# Whole System Architecture

This file explains the full runtime architecture of the current codebase:
- outer repo: `shopify/` = NexusOS
- nested submodule: `Pokemon/` = PokemonTool

Most important answer first:

## Do Pokemon and Shopify talk?

Yes, but in two different ways:

### 1. Clearly implemented right now: NexusOS calls PokemonTool

This path is visible in code now:
- `services/gateway/internal/pokemon/client.go`
- `services/ai/integrations/pokemon_client.py`

Meaning:
- NexusOS pulls live Pokemon card market data from PokemonTool over HTTP
- NexusOS uses that data for:
- A2A negotiation
- cart recovery
- SEO generation
- AI decision-making around cards

### 2. Documented/intended, but not fully visible as wired today: PokemonTool pushes events into NexusOS

This path is described in comments and handlers:
- `services/gateway/internal/pokemon/handler.go`
- `services/ai/consumers/pokemon_events.py`
- root `README.md`

Meaning:
- PokemonTool is supposed to push deal/trend/price-alert events into NexusOS
- NexusOS Gateway is supposed to receive them on internal routes
- Gateway is supposed to publish them to Kafka
- Python AI service is supposed to consume them

But in the current visible code:
- `services/gateway/main.go` does not currently register `/internal/pokemon/*` routes
- I also do not see the Pokemon-side bridge file in the current workspace snapshot

So the honest answer is:
- **NexusOS -> PokemonTool is clearly implemented**
- **PokemonTool -> NexusOS is architecturally planned and documented, but not fully visible as active wiring from the current files**

That distinction matters.

## The Big Picture

You have **two systems**:

### A. PokemonTool
A standalone distributed card-market intelligence system.

Responsibilities:
- ingest card listing data
- compute trends/deals
- manage user watchlists and inventory
- send alerts
- expose card market data over API

Main components:
- React frontend
- Go API server
- PostgreSQL
- Redis
- RabbitMQ
- Python ingestion/analytics services
- Go scraping service

### B. NexusOS
A Shopify-focused AI operations platform.

Responsibilities:
- receive Shopify events
- support AI workflows
- run agents
- manage merchant operations
- use Pokemon market data as intelligence input

Main components:
- React dashboard
- Go gateway
- Python AI service
- PostgreSQL
- Redis
- Kafka
- Qdrant
- Temporal
- Ollama

## Repo Relationship

`Pokemon/` is a Git submodule inside the outer `shopify/` repo.

That means:
- PokemonTool is its own project
- NexusOS depends on it
- the parent repo tracks a specific commit of PokemonTool

Think of it like this:

```text
shopify/
  ├── services/gateway       NexusOS Go API
  ├── services/ai            NexusOS Python AI service
  ├── apps/web               NexusOS frontend
  ├── docker-compose.yml     NexusOS infra
  └── Pokemon/               separate market-intelligence product
```

## Runtime Topology

```text
                           ┌────────────────────────────┐
                           │        Shopify SaaS        │
                           │   webhooks / merchant data │
                           └──────────────┬─────────────┘
                                          │ HTTP webhooks
                                          ▼
                    ┌─────────────────────────────────────────┐
                    │        NexusOS Go Gateway :8080         │
                    │ auth, webhooks, approvals, A2A, API     │
                    └──────────────┬───────────────┬──────────┘
                                   │               │
                                   │               │ HTTP
                                   │               ▼
                                   │    ┌──────────────────────┐
                                   │    │   PokemonTool API    │
                                   │    │       Go :3001       │
                                   │    └──────────┬───────────┘
                                   │               │
                                   │               │ uses
                                   ▼               ▼
                     ┌────────────────────┐   ┌───────────────┐
                     │ Kafka / topics     │   │ Redis / PG    │
                     │ shopify + pokemon* │   │ Pokemon state  │
                     └──────────┬─────────┘   └───────────────┘
                                │
                                ▼
                    ┌─────────────────────────────────────────┐
                    │       NexusOS AI Service :8000          │
                    │ agents, consumers, forecasting, RAG     │
                    └──────────────┬───────────────┬──────────┘
                                   │               │
                                   │               ▼
                                   │    ┌──────────────────────┐
                                   │    │ Qdrant / Ollama /    │
                                   │    │ Postgres / Redis     │
                                   │    └──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────────┐
                    │         NexusOS Frontend :3000          │
                    └─────────────────────────────────────────┘


PokemonTool internals:

  Python API Consumer + Analytics + Scraper
                  │
                  ▼
              RabbitMQ
                  │
                  ▼
        PokemonTool Go Worker / Alerts / SSE
```

`pokemon*` Kafka topics are documented/intended in current code comments and consumers.

## PokemonTool Internal Architecture

PokemonTool is a layered Go API plus asynchronous worker system.

### Main request path

```text
Browser / client
  -> chi routes
  -> middleware
  -> handlers
  -> services
  -> stores
  -> PostgreSQL / Redis
```

The main composition root is:
- `Pokemon/server/main.go`

That file builds:
- config
- DB connection
- Redis client
- RabbitMQ connection
- stores
- services
- handlers
- SSE manager
- background notification worker
- router and middleware

### PokemonTool async/event path

```text
Python producer / scraper / consumer
  -> RabbitMQ queue "listings"
  -> Go notification worker
  -> watchlist + price alert checks
  -> PostgreSQL alert inserts
  -> SSE push to connected user browsers
```

Key files:
- `Pokemon/server/worker/notification_worker.go`
- `Pokemon/server/config/rabbitmq.go`
- `Pokemon/server/handlers/sse_handler.go`

### What PokemonTool exposes outward

PokemonTool acts like a market-data service for NexusOS.

NexusOS reads:
- card prices
- trends
- deals
- possibly inventory or other card intelligence

Key outward-facing access points:
- `Pokemon/server/routes/routes.go`
- `Pokemon/server/handlers/card_handler.go`
- `Pokemon/server/handlers/deal_handler.go`

## NexusOS Internal Architecture

NexusOS is a platform with two main runtime services:
- Go Gateway
- Python AI Service

### Go Gateway

The gateway in `services/gateway/main.go` is the primary operational entrypoint for:
- Shopify webhooks
- auth
- API endpoints
- approvals
- A2A negotiation endpoints

Its main job is:
- receive external traffic safely
- authenticate and validate
- push events into Kafka
- expose application-facing routes

### Python AI Service

The AI service in `services/ai/main.py` is the intelligence layer.

Its main job is:
- run FastAPI routes
- start background consumers
- call PokemonTool when live market data is needed
- run agent workflows
- use Qdrant/RAG and model integrations

## The Real Direction Of Data Flow

There are **two separate integration patterns** between the systems.

## Pattern 1: Request/Response Pull

This is the clearest currently implemented integration.

### Flow

```text
NexusOS component
  -> HTTP GET to PokemonTool API
  -> PokemonTool returns live card data
  -> NexusOS uses that data in an AI/business workflow
```

### Where it happens

Go side:
- `services/gateway/internal/pokemon/client.go`

Python side:
- `services/ai/integrations/pokemon_client.py`

### What it is used for

#### A2A negotiation

Flow:

```text
Buyer / external agent
  -> NexusOS Gateway A2A endpoint
  -> negotiation logic
  -> PokemonTool card price lookup
  -> offer logic uses real market data
  -> response returned to caller
```

Meaning:
- PokemonTool is the pricing intelligence source
- NexusOS is the decision and workflow layer

#### Cart recovery

Flow:

```text
AI service cart-recovery route
  -> call PokemonTool for live card trend/price
  -> build better email content
  -> return generated recovery content
```

#### SEO generation

Flow:

```text
AI service SEO route
  -> call PokemonTool for market value/trend
  -> enrich generated product copy
  -> return result
```

## Pattern 2: Event Push Into NexusOS

This is the planned reverse-direction integration.

### Intended flow

```text
PokemonTool detects market event
  -> HTTP POST to NexusOS internal route
  -> Go Gateway validates internal secret
  -> Gateway publishes event to Kafka
  -> Python AI consumer processes event
  -> AI workflow / approval / repricing logic runs
```

### Documented event types

In `services/gateway/internal/pokemon/handler.go`, the intended inbound events are:
- `pokemon.deals`
- `pokemon.trends`
- `pokemon.price-alerts`

### Intended meaning of each topic

`pokemon.deals`
- card found below market
- should trigger buy/restock or approval-style logic

`pokemon.trends`
- card significantly rising/falling
- should influence repricing or inventory posture

`pokemon.price-alerts`
- threshold crossing event
- should refresh negotiation state or trigger downstream actions

### Current architecture honesty check

The handlers exist:
- `services/gateway/internal/pokemon/handler.go`

The Python consumer exists:
- `services/ai/consumers/pokemon_events.py`

The README describes the bridge.

But current visible wiring is incomplete because:
- `services/gateway/main.go` does not register the `/internal/pokemon/*` routes right now
- the Pokemon-side bridge sender is not present in the current visible workspace snapshot

So treat this as:
- **architectural intent present**
- **full runtime wiring not yet confirmed from visible code**

## End-To-End Workflows

## Workflow 1: Pokemon user checks card trends

```text
Pokemon frontend
  -> Pokemon Go API /api/cards/trending
  -> card service
  -> store / cache
  -> PostgreSQL / Redis
  -> response to frontend
```

This never needs NexusOS.

## Workflow 2: Pokemon user receives watchlist alert

```text
external listing data
  -> Python producer / scraper
  -> RabbitMQ
  -> Pokemon notification worker
  -> alert inserted into PostgreSQL
  -> SSE push to Pokemon frontend
```

This is entirely inside PokemonTool unless the reverse bridge is added.

## Workflow 3: NexusOS negotiates using Pokemon price data

```text
client / buyer agent
  -> NexusOS A2A route
  -> negotiation engine
  -> PokemonTool API lookup
  -> live market price comes back
  -> NexusOS generates price-aware offer
```

This is one of the clearest live integrations.

## Workflow 4: NexusOS cart-recovery email enriched by Pokemon market data

```text
cart recovery request
  -> NexusOS AI route
  -> pokemon_client.py
  -> PokemonTool API
  -> price/trend data returned
  -> email generation uses real market context
```

## Workflow 5: Intended market event push from Pokemon into NexusOS

```text
Pokemon analytics / worker
  -> internal POST to NexusOS Gateway
  -> gateway validates X-Internal-Secret
  -> publish to Kafka topic
  -> Python AI consumer handles event
  -> approval / repricing / action pipeline
```

Again: this is the planned system path, not fully confirmed as active from the current entrypoint wiring.

## Protocol Map

Use this to build intuition.

### HTTP
Used for:
- browser to frontend/backend
- Shopify webhooks to gateway
- NexusOS to PokemonTool API
- intended PokemonTool to NexusOS internal event bridge

### PostgreSQL
Used for:
- durable relational application data
- both systems use their own Postgres-backed state

### Redis
Used for:
- caching
- rate limiting / fast state
- quick operational data

### RabbitMQ
Used inside PokemonTool for:
- decoupling producers from alert-processing worker

### Kafka
Used inside NexusOS for:
- event streaming
- decoupling gateway ingestion from AI processing

### SSE
Used inside PokemonTool for:
- pushing real-time alerts to the browser

## Data Ownership

This is a key architecture concept.

### PokemonTool owns
- card market data
- watchlists
- inventory for PokemonTool users
- price alerts
- trend/deal computations
- real-time alerting around card listings

### NexusOS owns
- Shopify-related merchant workflows
- AI decisions
- approvals
- support / fraud / SEO / negotiation workflows
- merchant operational intelligence

### Shared boundary

PokemonTool is the source of truth for Pokemon market intelligence.

NexusOS consumes that intelligence and turns it into operational or commercial action.

## Security Boundary

### External/public-ish traffic
- Shopify webhooks to gateway
- frontend traffic to gateway / AI / Pokemon API

### Internal service-to-service traffic
- NexusOS to PokemonTool HTTP calls
- intended PokemonTool to NexusOS event posts
- Kafka internal traffic
- RabbitMQ internal traffic

### Shared secret model

The documented service-to-service auth boundary is:
- `X-Internal-Secret`

Meaning:
- internal routes are supposed to reject callers without the shared secret
- this is the trust boundary between PokemonTool and NexusOS for private integration routes

## Failure Domains

This is the infra-engineer view of the system.

### If PokemonTool is down

Effects:
- Pokemon frontend breaks
- NexusOS features that depend on card pricing lose live market enrichment
- A2A negotiation may need fallback prices
- cart recovery / SEO lose Pokemon-aware intelligence

### If RabbitMQ is down

Effects:
- Pokemon HTTP API may still run
- real-time listing/event processing degrades
- alert generation path weakens or stops

### If Kafka is down

Effects:
- NexusOS gateway can still serve some routes
- event-driven AI workflows degrade
- intended Pokemon inbound events cannot flow into AI processing

### If AI service is down

Effects:
- Gateway may still accept some traffic
- AI workflows and asynchronous decisioning fail
- Pokemon pull-based market lookup remains available if PokemonTool is healthy

### If Redis is down

Effects:
- performance degradation
- some rate-limiting or cache-backed behavior may change
- should not always mean total outage

### If Postgres is down

Effects:
- core application functionality is broken
- most critical durable operations fail

## Current Architecture Summary

If you want the simplest correct model, use this:

```text
PokemonTool = market intelligence system
NexusOS    = AI operations system

NexusOS currently reads from PokemonTool over HTTP.
PokemonTool is designed to also push market events back into NexusOS,
but that reverse path is only partially visible in the current code wiring.
```

## What To Look At Next

If you want to trace this manually, inspect these in order:

### PokemonTool
- `Pokemon/server/main.go`
- `Pokemon/server/routes/routes.go`
- `Pokemon/server/worker/notification_worker.go`
- `Pokemon/docker-compose.yml`

### NexusOS
- `services/gateway/main.go`
- `services/gateway/internal/pokemon/client.go`
- `services/gateway/internal/pokemon/handler.go`
- `services/ai/main.py`
- `services/ai/integrations/pokemon_client.py`
- `services/ai/consumers/pokemon_events.py`
- root `docker-compose.yml`

## Final Plain-English Explanation

If I explain it super simply:

- `Pokemon` is the card-market brain
- `shopify` is the merchant AI brain
- right now `shopify` clearly asks `Pokemon` for live card intelligence
- `Pokemon` is also supposed to send important market events back into `shopify`
- that reverse pipeline is described in the codebase, but the visible runtime wiring is not fully completed in the current snapshot

So you were not crazy for being confused. The architecture is split between:
- what already runs
- what is designed
- what is documented

That is exactly the kind of thing an infrastructure engineer needs to learn to spot.
