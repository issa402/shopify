# NexusOS — Complete Project Bible

> **Last updated:** April 2026  
> This document is the single source of truth for everything about this project.  
> Read this. Never ask "what does this do" again.

---

## What This Is

**NexusOS** is an autonomous AI operations layer for Shopify stores — built specifically for Pokemon TCG card sellers but architected to be product-agnostic.

It is **not** a dashboard. It is not a chatbot. It runs your store 24/7, making real decisions:
- Scoring every order for fraud before you ship
- Recovering abandoned carts with AI-written emails (not templates)
- Generating SEO descriptions for 50 products in 30 seconds
- Letting other AI agents buy from your store at market-rate prices automatically
- Repricing your Shopify listings when the TCG market moves

One human merchant. Zero ops team. This is the product.

---

## Two Separate Services in One Repo

```
shopify/
├── shopify/              ← NexusOS (THIS IS THE MAIN PROJECT)
│   ├── services/
│   │   ├── gateway/      ← Go API Gateway
│   │   └── ai/           ← Python AI Service
│   ├── apps/web/         ← React Merchant Dashboard
│   ├── Pokemon/          ← PokémonTool microservice (SEPARATE, git submodule)
│   ├── infra/            ← YOUR personal infra training lab (not part of app)
│   └── docker-compose.yml
```

**Pokemon/** is an entirely separate microservice that lives here as a git submodule. NexusOS calls it for live card prices. It has its own Docker stack, its own Postgres, its own RabbitMQ. If it's down, NexusOS degrades gracefully — fraud, SEO, and support still work, cart emails and repricing lose their live market data.

**infra/** is your personal infrastructure engineering training curriculum. Not part of the running application. Ignore it when thinking about the product.

---

## Full Runtime Architecture

```
INBOUND:
  Shopify (webhooks) ──► Go Gateway :8080
                              │
                     HMAC-SHA256 verify
                              │
                         Kafka publish
                              │
                    ──────────┴────────────
                    │                     │
                    ▼                     ▼
          Python AI :8000        Kafka Event Bus
          (main consumer)        (topic: shopify.events)
                    │
         ┌──────────┼──────────────────────────────┐
         │          │          │          │         │
         ▼          ▼          ▼          ▼         ▼
      Fraud      Cart       SEO      Agents      A2A
     Scoring   Recovery  Generator   Swarm    Negotiate
         │          │                  │
         │          └──► Claude 3.5    │
         │               (email write) │
         └──► GPT-4o                  └──► CrewAI
              (chargeback)                 ├── SupportAgent (Claude)
                                           ├── LogisticsAgent (Claude)
                                           └── FinanceAgent (GPT-4o)
                                                    │ manager
                                                    ▼
EXTERNAL ENRICHMENT:                         approval_queue
  PokémonTool :3001 ─────────────────────────────────┘
  (live card prices, trends, deals)    All big actions here → human approves

DATA LAYER (all in Docker):
  PostgreSQL + pgvector  :5432   ← all relational data + Row-Level Security multi-tenant
  Redis                  :6379   ← idempotency keys (24h TTL), session cache
  Qdrant (vector DB)     :6333   ← RAG embeddings (past tickets, product docs)
  Kafka + Zookeeper      :9092   ← event streaming between Go and Python
  Ollama (Llama3:8b)     :11434  ← free local LLM for cheap classification tasks
  Temporal               :7233   ← reliable long-running agent workflow execution
  Temporal UI            :8088   ← browser UI to watch/debug workflows
```

---

## Service 1: Go API Gateway (`services/gateway/`)

**Language:** Go 1.22  
**Framework:** Gin  
**Port:** 8080  
**Entry point:** `services/gateway/main.go`

### What It Does

The Go gateway is the front door of NexusOS. Everything from Shopify hits here first.

**On startup:**
1. Connects to PostgreSQL and runs migrations automatically
2. Initializes the Kafka producer
3. Initializes the MCP Hub (model context protocol — lets AI agents call tools)
4. Starts Gin router with graceful SIGTERM/SIGINT shutdown (30s drain)

**What it handles:**

| Route | What happens |
|---|---|
| `GET /health` | Returns `{status: "healthy", service: "nexusos-gateway", version: "2026.1.0"}` |
| `GET /auth/shopify` | Starts Shopify OAuth flow |
| `GET /auth/callback` | Handles OAuth callback, stores access token in DB |
| `POST /webhooks/shopify/orders/create` | Verifies HMAC, publishes to Kafka, triggers fraud score |
| `POST /webhooks/shopify/orders/paid` | Verify + publish |
| `POST /webhooks/shopify/orders/cancelled` | Verify + publish |
| `POST /webhooks/shopify/orders/updated` | Verify + publish |
| `POST /webhooks/shopify/products/create` | Verify + publish |
| `POST /webhooks/shopify/products/update` | Verify + publish |
| `POST /webhooks/shopify/inventory_levels/set` | Verify + publish |
| `POST /webhooks/shopify/customers/create/update/delete` | Verify + publish |
| `POST /webhooks/shopify/refunds/create` | Verify + publish |
| `POST /api/v1/agent/negotiate` | 🔐 JWT required — A2A negotiation endpoint |
| `GET /api/v1/agent/capabilities` | 🔐 JWT required — advertise what this agent can do |
| `GET /api/v1/orders` | 🔐 JWT + RBAC — merchant's orders |
| `GET /api/v1/approvals/pending` | 🔐 JWT + RBAC — pending AI actions awaiting approval |
| `POST /api/v1/approvals/:id/approve` | 🔐 Merchant approves an AI action |
| `POST /api/v1/approvals/:id/reject` | 🔐 Merchant rejects an AI action |
| `DELETE /api/v1/customers/:id` | 🔐 GDPR cascade delete across Postgres + Qdrant |

**Middleware stack (applied in order):**
1. `gin.Logger()` — request logging
2. `gin.Recovery()` — panic recovery (never crashes)
3. `middleware.CORS()` — cross-origin headers for React dashboard
4. `middleware.OpenTelemetry()` — distributed tracing
5. `middleware.AuthRequired(pool)` — JWT verification on `/api/v1/*`
6. `middleware.RBAC()` — role-based access control

### Internal Packages

```
internal/
├── auth/       Shopify OAuth — initiate + callback, stores access token in Postgres
├── webhook/    HMAC-SHA256 verification (constant-time comparison) + Kafka publish
├── kafka/      Kafka producer wrapper
├── a2a/        A2A commerce handler — receives ProductQuery from buyer agents
├── pokemon/    PokémonTool HTTP client + inbound event handler (market events)
├── middleware/ JWT auth, RBAC, CORS, OpenTelemetry
├── db/         PostgreSQL connection pool + migration runner + Row-Level Security
└── mcp/        MCP Hub — loads tool definitions from mcp-config.json
```

### Completion Status

| Feature | Status | What's Missing |
|---|---|---|
| Webhook ingestion (all 11 types) | ✅ Complete | Nothing |
| HMAC-SHA256 verification | ✅ Complete | Nothing |
| Kafka publish | ✅ Complete | Nothing |
| Shopify OAuth | ✅ Complete | Nothing |
| JWT/RBAC middleware | ✅ Complete | Nothing |
| Graceful shutdown | ✅ Complete | Nothing |
| A2A negotiate endpoint | ✅ Complete | Nothing |
| Orders/Customers/Approvals endpoints | 🟡 Shell | Returns empty arrays — needs real DB queries wired in |
| GDPR cascade delete | 🟡 Stub | Has TODO for Qdrant + MCP cascade |
| PokémonTool inbound handler | ✅ Complete | Nothing |

---

## Service 2: Python AI Service (`services/ai/`)

**Language:** Python 3.11  
**Framework:** FastAPI + uvicorn  
**Port:** 8000  
**Entry point:** `services/ai/main.py`  
**API docs:** `http://localhost:8000/docs` (auto-generated Swagger)

### What It Does

The Python AI service is the brain. It runs all AI agents, all ML models, all LLM calls, all business logic. The Go gateway handles HTTP/webhook ingestion; this service handles everything intelligent.

**On startup (lifespan hook):**
1. `await init_qdrant()` — creates vector collection in Qdrant if it doesn't exist
2. `asyncio.create_task(pokemon_event_consumer.run())` — starts Kafka consumer as background coroutine (won't block HTTP requests)

**All registered routes:**

| Router | Prefix | Endpoints |
|---|---|---|
| `health.py` | `/health` | `GET /health` — status of all dependencies |
| `agents.py` | `/agents` | `POST /agents/support/resolve`, `/agents/logistics/restock`, `/agents/finance/margin` |
| `fraud.py` | `/fraud` | `POST /fraud/score`, `POST /fraud/dispute/respond` |
| `cart_recovery.py` | `/cart-recovery` | `POST /cart-recovery/generate-email` |
| `seo.py` | `/seo` | `POST /seo/generate`, `POST /seo/bulk-generate` |
| `negotiate.py` | `/negotiate` | `POST /negotiate/offer`, `POST /negotiate/contract` |
| `inventory.py` | `/inventory` | `POST /inventory/forecast`, `POST /inventory/draft-po` |
| `marketing.py` | `/marketing` | `POST /marketing/segment` |

### Subdirectory Breakdown

#### `agents/crew.py` — CrewAI Multi-Agent Swarm ✅ FULLY IMPLEMENTED

Three agents working as a team:

| Agent | LLM | Tools | Role |
|---|---|---|---|
| `SupportAgent` | Claude 3.5 Sonnet | ShopifyRefundTool, SlackNotifyTool | Resolves customer tickets, issues refunds ≤$100 |
| `LogisticsAgent` | Claude 3.5 Sonnet | CheckInventoryTool, FindAlternativeSupplierTool, SlackNotifyTool | Monitors inventory, finds alternative suppliers |
| `FinanceAgent` | GPT-4o | ProfitCalculatorTool | **MANAGER** — approves anything >$100, never allows margin <15% |

**Process:** Hierarchical — FinanceAgent oversees all. Any action over $100 requires its approval before execution.

**Memory:** `memory=True` — shared embeddings via OpenAI `text-embedding-3-small` so agents remember context within a session.

**Tools (all need real API wiring):**

| Tool | Does Now | Needs |
|---|---|---|
| `ShopifyRefundTool` | Returns stub string, blocks >$100 | Shopify Admin API `POST /orders/{id}/refunds.json` |
| `CheckInventoryTool` | Returns hardcoded "145 units" | Postgres `SELECT current_quantity FROM inventory_levels` |
| `ProfitCalculatorTool` | Returns hardcoded "35% margin" | Postgres `SELECT subtotal_price FROM orders` |
| `SlackNotifyTool` | Returns stub string | Slack Incoming Webhook `POST` |
| `FindAlternativeSupplierTool` | Returns stub string | Supplier DB / ERP / Spocket API |

#### `agents/router.py` — HybridAIRouter ✅ FULLY IMPLEMENTED

Routes every AI call to the cheapest appropriate model:

| Tier | Model | Cost | Used for |
|---|---|---|---|
| CHEAP | Ollama Llama3:8b (local) | $0.00 | classify_email, tag_ticket, route_intent, sentiment_analysis, check_spam |
| NORMAL | Claude 3.5 Sonnet | ~$0.004/call | draft_customer_reply, logistics_analysis, marketing_copy, ticket_resolution, SEO copy, cart emails |
| COMPLEX | GPT-4o | ~$0.015/call | financial_analysis, risk_assessment, contract_negotiation, chargeback responses |

**Graceful degradation:** If Ollama is down → falls back to Claude automatically. Never crashes.

**Cost estimation:** `router.estimate_cost(task_type, input_tokens, output_tokens)` — exact USD cost per call. Used to show merchants "NexusOS cost $4.23 this month in AI calls."

**Adding a new task:** Add one line to `TASK_ROUTING_TABLE` in `router.py`. That's it.

#### `agents/negotiation.py` — A2A Negotiation Engine ✅ FULLY IMPLEMENTED

Handles automated B2B purchasing from other AI agents.

**Flow:**
1. Buyer AI sends `POST /api/v1/agent/negotiate` with a `ProductQuery`
2. Go gateway forwards to Python AI service
3. `NegotiationEngine.process_query()` calls PokémonTool live for real TCGplayer market price
4. **Trend-aware discounting:**
   - RISING market (score >50) → cuts discount by 50% (don't give away value on appreciating cards)
   - RISING market (score 20-50) → cuts discount by 25%
   - FALLING market (score <-50) → adds 5% extra discount (move inventory before price drops further)
   - FALLING market (score -20 to -50) → adds 2% extra
   - STABLE → standard B2B quantity tiers (5% / 10% / 20% for <10 / 10-49 / 50+ units)
5. Always caps at 25% max discount, never sells below 15% margin
6. Returns `Offer` with 15-minute expiry
7. `generate_contract()` converts accepted offer → `Contract` with payment URL

**Missing:** Qdrant semantic search for real Shopify product matching (currently returns stub product). Inventory count not queried from Postgres yet.

#### `routers/fraud.py` — Fraud Detection & Chargeback Defense ✅ THE MOST COMPLETE FEATURE

**Feature 1: Real-time order risk scoring**

Called the moment a `orders/create` webhook arrives. Five weighted risk factors:

| Signal | Weight | Logic |
|---|---|---|
| Billing ≠ shipping country | +30 pts | Stolen card fraud pattern |
| New customer + order >$200 | +25 pts | Fraudsters maximize single purchase |
| New customer + order >$500 | +40 pts total | Major red flag |
| 3+ payment attempts | +20 pts | Card cycling / carding attack |
| 5+ payment attempts | +30 pts total | Definitely suspicious |
| Disposable email domain | +35 pts | **Highest weight** — real customers never use throwaway emails |
| 5+ previous orders | -20 pts | Trusted returning customer |
| 2-4 previous orders | -10 pts | Known returning customer |

Score clamped 0-100 → three tiers:
- `0-34` → LOW → `approve` — fulfill immediately
- `35-69` → MEDIUM → `review` — hold 2h, send ID verification email
- `70-100` → HIGH → `cancel` — auto-cancel, don't ship, add to watchlist

14 disposable email domains hardcoded (guerrillamail, mailinator, 10minutemail, etc.)

**Feature 2: Automated chargeback response**

Called when `disputes/created` webhook arrives. Uses GPT-4o (not Claude — financial precision matters).

Different prompt strategy per dispute reason:
- `not_received` → focuses on tracking number + delivery confirmation + signature
- `fraudulent` → focuses on IP geolocation + purchase history + confirmed delivery address
- anything else → generic evidence collection

Returns a draft response for merchant 1-click approval. Missing: `stripe.Dispute.modify()` call to actually submit (code is there, commented out as TODO).

Win rate with automated response: industry ~35%. Win rate without response: 0%.

#### `routers/cart_recovery.py` — Cart Abandonment Recovery ✅ FULLY IMPLEMENTED

3-email sequence per abandoned checkout:

| Email | Timing | Tone | Special |
|---|---|---|---|
| #1 | 1h after abandonment | Friendly, no pressure | Standard reminder |
| #2 | 24h after | Informative | Includes live PokémonTool market data if item is a Pokemon card |
| #3 | 72h after | Mild urgency | Includes 5% discount code `COMEBACK5` |

**PokémonTool enrichment:** Detects Pokemon cards by keyword matching (charizard, pikachu, mewtwo, tcg, base set, psa, shadowless, first edition, booster) → calls `pokemon_client.get_card_price()` → if trending UP, includes "This card is up 15% this week" in email naturally.

**Claude 3.5 Sonnet** writes every email. Not a template — a unique email per customer.

**Fallback:** If Claude fails → uses basic template. Never returns 500 to the caller.

**Missing:** The actual email send call (SendGrid / Shopify Email API). Returns the generated email object; caller is responsible for sending.

#### `routers/seo.py` — AI SEO Engine ✅ FULLY IMPLEMENTED

**Single product** (`POST /seo/generate`):
- Generates: description (150-200 words), title tag (≤60 chars), meta description (≤160 chars), H1 heading, JSON-LD Product schema markup
- Section parser extracts each piece from Claude's structured output
- Fallback defaults if parsing fails — never errors out
- PokémonTool enrichment for card products: bakes live market price into description

**Bulk** (`POST /seo/bulk-generate`):
- Up to 50 products max
- Uses `asyncio.gather()` — all 50 run in parallel
- 50 products sequential = ~150s. 50 products parallel = ~3s
- `return_exceptions=True` — one failed product doesn't kill the batch
- Returns per-product `status: "success"` or `status: "failed"` with error

#### `inventory/` — Prophet ML Forecasting 🟡 STRUCTURE EXISTS

Facebook Prophet ML model for 30-day demand forecasting. Needs 90 days of real sales history from Postgres to generate meaningful forecasts. Router exposes `POST /inventory/forecast` and `POST /inventory/draft-po`. Works once you have real data.

#### `rag/pipeline.py` — RAG Support Pipeline 🟡 INITIALIZED, NEEDS DATA

Qdrant vector collection initialized on every startup. Semantic search over past support tickets. The infrastructure is ready. Feed it real ticket data and it enables SupportAgent to resolve "like we resolved order #1234 last month" using actual past context.

#### `consumers/pokemon_events.py` — Kafka Consumer ✅ WIRED, RUNS IN BACKGROUND

Reads Kafka events published by PokémonTool when card prices move significantly. When a trend event arrives → triggers `run_finance_agent()` or `run_logistics_agent()` from `crew.py`. This is how market intelligence becomes automatic Shopify pricing updates.

#### `integrations/pokemon_client.py` — PokémonTool HTTP Client ✅ COMPLETE

Async HTTP client (httpx) that calls PokémonTool's Go API at `:3001`. Used by cart recovery, SEO, fraud, and A2A negotiation. If PokémonTool is unavailable → returns `None` everywhere → callers handle gracefully.

---

## Service 3: React Merchant Dashboard (`apps/web/`)

**Language:** TypeScript + React  
**Framework:** Vite  
**UI library:** @shopify/polaris — Shopify's official design system (looks exactly like a real Shopify app)  
**Charts:** recharts  
**Port:** 3000

### Pages

| Page | File | Status | What It Does |
|---|---|---|---|
| Dashboard | `Dashboard.tsx` | 🟡 Shell | KPI cards (revenue, AI actions, approvals, LLM cost), revenue+AI actions chart, recent orders table, agent swarm status |
| Approvals | `Approvals.tsx` | 🟡 Shell | Lists pending AI actions waiting for merchant approval (big refunds, purchase orders, pricing changes) |
| Agent Logs | `AgentLogs.tsx` | 🟡 Shell | Real-time agent action history |
| Workflows | `Workflows.tsx` | 🟡 Shell | Temporal workflow status, agent configuration |
| Settings | `Settings.tsx` | 🟡 Shell | Store connection, API keys, notification preferences |

**All UI components are real and styled correctly. All data is hardcoded mock data.** No `fetch()` calls wired to the Go gateway yet. This is the biggest remaining gap in the frontend — every page needs to call `GET /api/v1/...` with a JWT token.

---

## Infrastructure (Docker Compose)

All services defined in `docker-compose.yml`. Run `docker compose up -d` and they all start with health checks.

| Service | Container | Port | Purpose | Data Persisted |
|---|---|---|---|---|
| PostgreSQL + pgvector | `nexusos-postgres` | 5432 | All relational data — orders, merchants, inventory, approvals. Multi-tenant via Row-Level Security. pgvector extension for optional embedding storage | Yes — `postgres_data` volume |
| Redis | `nexusos-redis` | 6379 | Idempotency keys (24h TTL) prevent duplicate webhook processing. Session cache | Yes — `redis_data` volume |
| Qdrant | `nexusos-qdrant` | 6333 | Vector database. Stores embeddings of past support tickets and product docs for RAG search | Yes — `qdrant_data` volume |
| Zookeeper | `nexusos-zookeeper` | 2181 | Required by Kafka (metadata management) | Yes — `zookeeper_data` volume |
| Kafka | `nexusos-kafka` | 9092 | Event streaming. Go gateway publishes webhooks here, Python AI consumes them | Yes — `kafka_data` volume |
| Ollama | `nexusos-ollama` | 11434 | Local LLM server. Auto-pulls `llama3:8b` on first start. Zero API cost for cheap AI tasks | Yes — `ollama_data` volume |
| Temporal | `nexusos-temporal` | 7233 | Reliable long-running workflow execution. If a 10-step agent workflow crashes at step 7, Temporal resumes from step 7 on restart | Uses Postgres |
| Temporal UI | `nexusos-temporal-ui` | 8088 | Browser dashboard to see all running/failed workflows | No |

**NexusOS network name:** `nexusos-network` — all containers communicate internally by service name.

**Migrations:** Postgres auto-runs SQL files from `services/gateway/internal/db/migrations/` on first start.

---

## Security Model

| Layer | Implementation |
|---|---|
| Shopify webhook verification | HMAC-SHA256, constant-time comparison — prevents webhook spoofing |
| Gateway → AI communication | Internal Docker network only — Python AI not exposed publicly |
| PokémonTool ↔ NexusOS | `X-Internal-Secret` shared header — must be identical in both `.env` files |
| Merchant API access | JWT Bearer tokens — issued by Go gateway on Shopify OAuth |
| Role-based access | RBAC middleware — different permissions per merchant role |
| Multi-tenant data isolation | PostgreSQL Row-Level Security — agents can never read another merchant's data |
| Webhook deduplication | Redis idempotency keys — prevents processing the same webhook twice |
| Human-in-the-loop | All actions >$100 go to `approval_queue` — merchant approves before execution |

---

## AI Model Strategy

Every AI call goes through `HybridAIRouter` in `agents/router.py`:

```
Task type → routing table → model tier → LLM client

CHEAP  → Ollama Llama3:8b  → $0.00  (classify_email, tag_ticket, route_intent, check_spam)
NORMAL → Claude 3.5 Sonnet → ~$0.004 (customer emails, SEO copy, logistics analysis)
COMPLEX → GPT-4o           → ~$0.015 (fraud risk, chargeback response, financial decisions)
```

Estimated monthly cost at moderate volume (~500 AI actions/day):
- Claude calls: ~$6-12/month
- GPT-4o calls: ~$2-5/month  
- Ollama: $0

**~70% cost reduction** vs using GPT-4o for everything.

---

## What's Fully Working vs What's Missing

### Ready Now (just needs `.env` keys)
| Feature | File |
|---|---|
| ✅ Fraud scoring (real algorithm, real thresholds) | `routers/fraud.py` |
| ✅ Chargeback response drafting (GPT-4o) | `routers/fraud.py` |
| ✅ Cart recovery email generation (Claude + PokémonTool) | `routers/cart_recovery.py` |
| ✅ SEO package generation, single and bulk 50x parallel | `routers/seo.py` |
| ✅ A2A negotiation with real market prices + trend discounts | `agents/negotiation.py` |
| ✅ CrewAI 3-agent swarm with hierarchical approval | `agents/crew.py` |
| ✅ HybridAIRouter — 3 model tiers, cost tracking, Ollama fallback | `agents/router.py` |
| ✅ All 11 Shopify webhook types ingested, verified, Kafka-published | `gateway/internal/webhook/` |
| ✅ Kafka event pipeline Go → Python | Both services |
| ✅ PokémonTool HTTP client with graceful degradation | `integrations/pokemon_client.py` |
| ✅ All Docker infrastructure (Postgres, Redis, Kafka, Qdrant, Ollama, Temporal) | `docker-compose.yml` |

### Needs Wiring (code exists, just needs real API calls)
| Gap | What's Needed | Files |
|---|---|---|
| 🔧 CrewAI tool `_run()` methods | Shopify Admin API calls in each Tool class | `agents/crew.py` |
| 🔧 Dashboard API calls | Replace mock data with `fetch()` to Go gateway | All `apps/web/src/pages/*.tsx` |
| 🔧 Cart recovery email sending | SendGrid or Shopify Email API call | `routers/cart_recovery.py` |
| 🔧 Chargeback auto-submit | Uncomment Stripe `Dispute.modify()` call | `routers/fraud.py` |
| 🔧 Order/Customer/Approval endpoints | Real DB queries in Go gateway | `services/gateway/main.go` |
| 🔧 Inventory forecasting | Real sales history from Postgres | `inventory/` |
| 🔧 RAG support pipeline | Feed real ticket data into Qdrant | `rag/pipeline.py` |
| 🔧 Qdrant product search | Product embeddings for A2A matching | `agents/negotiation.py` |

### Needs `.env` File Filled
```bash
# NexusOS (.env)
SHOPIFY_CLIENT_ID=
SHOPIFY_CLIENT_SECRET=
SHOPIFY_WEBHOOK_SECRET=
ANTHROPIC_API_KEY=          ← Claude 3.5 Sonnet
OPENAI_API_KEY=             ← GPT-4o
DATABASE_URL=               ← Postgres connection string
REDIS_URL=                  ← Redis connection
KAFKA_BROKERS=              ← Kafka broker address
JWT_SECRET=                 ← 64+ char random string (openssl rand -hex 32)
INTERNAL_SECRET=            ← Must match Pokemon/.env exactly
POKEMONTOOL_API_URL=        ← http://localhost:3001

# Pokemon microservice (Pokemon/.env)
NEXUSOS_GATEWAY_URL=        ← http://localhost:8080
INTERNAL_SECRET=            ← Must match NexusOS .env exactly
```

---

## How to Run

```bash
# 1. Fill .env files (see above)
cp .env.example .env
cd Pokemon && cp .env.example .env && cd ..

# 2. Start all infrastructure
docker compose up -d                        # NexusOS: Postgres, Redis, Kafka, Qdrant, Ollama, Temporal
cd Pokemon && docker compose up -d && cd .. # PokémonTool: its own Postgres, Redis, RabbitMQ

# 3. Three terminals
cd services/gateway && go run ./main.go                    # :8080
cd services/ai && pip install -r requirements.txt && \
  python -m uvicorn main:app --port 8000 --reload          # :8000
cd apps/web && npm install && npm run dev                   # :3000

# 4. Pokemon microservice (4th terminal)
cd Pokemon/server && go run ./main.go                       # :3001

# 5. Verify
curl http://localhost:8080/health   # {"status":"healthy","service":"nexusos-gateway"}
curl http://localhost:8000/health   # AI service status
curl http://localhost:3001/health   # PokémonTool status

# 6. Open
# Dashboard:     http://localhost:3000
# AI API docs:   http://localhost:8000/docs
# Temporal UI:   http://localhost:8088
```

---

## Planned: Three Major New Features

### Feature 1: Reverse Market Arbitrage Agent

**What it does:** Instead of just forecasting inventory, actively scans suppliers (AliExpress, liquidators, other Shopify stores) for your best-selling items at below-market prices. If COGS can be cut 40%, the agent auto-buys a test batch or negotiates a dropship deal via A2A.

**How to build:**
- New CrewAI tool: `SupplierScanTool` — hits AliExpress Dropshipping API or Spocket/Zendrop API
- New Kafka topic: `supply.arbitrage.opportunities`
- New Python consumer that runs every 6h: pulls best-sellers from Shopify, compares to supplier prices
- When opportunity found → LogisticsAgent evaluates → FinanceAgent approves → lands in `approval_queue`
- Fits exactly into the existing crew/tool/approval pattern — no new architecture needed

**Where it slots in:** `agents/crew.py` new tool + `consumers/` new consumer

---

### Feature 2: Hyper-Personalized Storefronts (Generative UI)

**What it does:** When a visitor lands, the AI re-renders the product page copy, headline, and price strategy based on their UTM source and behavioral history. User from "luxury tech" TikTok ad → premium high-contrast copy. User from "budget deals" search → bundle offer with urgency timer.

**How to build:**
- New endpoint: `POST /storefront/render` — takes `{visitor_id, utm_source, product_id, past_behavior[]}`
- Claude generates customized headline, description, CTA, and pricing display strategy
- Redis caches the personalized version per session (don't regenerate on every refresh)
- Frontend: either headless Next.js storefront (full control, right approach long-term) or a Shopify theme script injection that swaps content on page load

**Where it slots in:** New router in `services/ai/routers/storefront.py` + React storefront component

---

### Feature 3: Influencer Swarm Protocol

**What it does:** New agent scans Instagram/TikTok/YouTube for micro-influencers matching your niche → generates personalized outreach DMs → auto-creates unique Shopify discount codes per influencer → tracks their sales → auto-pays commission via Stripe.

**How to build:**
- New `services/influencer/` microservice (Python)
- Playwright scraper to discover influencers by hashtag/keyword
- New CrewAI agent: `OutreachAgent` (NORMAL tier — Claude writes personalized DMs)
- Shopify Discount API for unique codes
- Stripe Connect for commission payouts OR Coinbase Commerce for crypto
- Track conversions via existing `orders/create` webhook listener → attribute by discount code

**Platform reality:** Platform ToS makes automated DM sending risky. Practical v1: agent writes the DMs and queues them in a dashboard for the merchant to send manually. Full automation is possible via Instagram Graph API but requires Facebook Business approval.

---

## Planned: Hermes Agent Integration

**What Hermes is:** `nous-hermes-2-pro` or `hermes-3` — open-source LLM models fine-tuned specifically for agentic tool-calling and structured JSON output. Dramatically better than generic Llama3 for agent tasks. Runs locally via Ollama. Zero API cost.

**Why it matters for this project:** The CHEAP tier currently uses generic Llama3:8b. Replacing it with Hermes gives you:
- Reliable structured JSON output (critical for tool calls in CrewAI)
- Better function-calling with the right arguments
- More accurate intent classification in A2A negotiation
- Handles the Reverse Market Agent's bulk supplier evaluation ($0/call instead of Claude)

**How to integrate:**

Step 1 — Pull Hermes into Ollama (update `docker-compose.yml`):
```yaml
# In the ollama entrypoint:
entrypoint: ["/bin/sh", "-c", "ollama serve & sleep 10 && ollama pull llama3:8b && ollama pull hermes3 && wait"]
```

Step 2 — Add a HERMES tier to `HybridAIRouter` in `agents/router.py`:
```python
class TaskComplexity(str, Enum):
    CHEAP   = "cheap"    # Llama3:8b  — basic classification
    HERMES  = "hermes"   # Hermes3    # structured JSON, tool calls, agent reasoning (still free)
    NORMAL  = "normal"   # Claude 3.5 — human-quality writing
    COMPLEX = "complex"  # GPT-4o    — financial/legal reasoning

def _get_hermes(self) -> ChatOllama:
    if "hermes" not in self._llms:
        self._llms["hermes"] = ChatOllama(
            model="hermes3",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.1,
        )
    return self._llms["hermes"]
```

Step 3 — Route the right tasks to Hermes:
```python
# Move these from CHEAP to HERMES:
"route_intent":              TaskComplexity.HERMES,  # A2A: classify buyer query type
"logistics_analysis":        TaskComplexity.HERMES,  # Supply disruption evaluation
"supplier_comparison":       TaskComplexity.HERMES,  # Arbitrage agent — compare 500 suppliers
"inventory_summary":         TaskComplexity.HERMES,  # Structured inventory reports
```

**Result:** The Reverse Market Arbitrage Agent can evaluate thousands of supplier prices at zero API cost with reliable structured output. The A2A negotiation intent router gets better. CrewAI tool calls become more reliable. The saving goes entirely to your Anthropic/OpenAI bills.

---

## File Tree

```
shopify/shopify/
├── services/
│   ├── gateway/
│   │   ├── main.go                    ← Entry point, router setup, graceful shutdown
│   │   ├── webhook_test.go            ← HMAC verification tests
│   │   └── internal/
│   │       ├── auth/                  ← Shopify OAuth
│   │       ├── webhook/               ← HMAC verify + Kafka publish
│   │       ├── kafka/                 ← Kafka producer
│   │       ├── a2a/                   ← A2A commerce handler
│   │       ├── pokemon/               ← PokémonTool client + inbound handler
│   │       ├── middleware/            ← JWT, RBAC, CORS, OpenTelemetry
│   │       ├── db/                    ← Postgres pool + migrations + RLS
│   │       └── mcp/                   ← MCP Hub (tool definitions)
│   └── ai/
│       ├── main.py                    ← FastAPI app, startup hooks, router registration
│       ├── requirements.txt           ← All Python dependencies
│       ├── agents/
│       │   ├── crew.py                ← 3 CrewAI agents + 5 tools + task runners
│       │   ├── router.py              ← HybridAIRouter (Ollama/Claude/GPT-4o)
│       │   └── negotiation.py         ← A2A NegotiationEngine
│       ├── routers/
│       │   ├── fraud.py               ← Fraud scoring + chargeback response
│       │   ├── cart_recovery.py       ← 3-email abandonment recovery
│       │   ├── seo.py                 ← Single + bulk product SEO generation
│       │   ├── agents.py              ← Agent trigger endpoints
│       │   ├── inventory.py           ← Prophet forecasting endpoints
│       │   ├── marketing.py           ← Customer segmentation
│       │   ├── negotiate.py           ← Negotiate offer/contract endpoints
│       │   └── health.py              ← /health endpoint
│       ├── consumers/
│       │   └── pokemon_events.py      ← Kafka consumer for PokémonTool market events
│       ├── integrations/
│       │   └── pokemon_client.py      ← Async HTTP client for PokémonTool API
│       ├── inventory/                 ← Facebook Prophet ML forecasting
│       ├── rag/
│       │   └── pipeline.py            ← Qdrant init + RAG search pipeline
│       └── tests/                     ← Test suite
├── apps/
│   └── web/
│       ├── src/
│       │   ├── App.tsx                ← Routing setup (React Router)
│       │   ├── main.tsx               ← React entry point
│       │   └── pages/
│       │       ├── Dashboard.tsx      ← KPIs, revenue chart, agent status (mock data)
│       │       ├── Approvals.tsx      ← Pending AI action approvals (mock data)
│       │       ├── AgentLogs.tsx      ← Agent action history (mock data)
│       │       ├── Workflows.tsx      ← Temporal workflow status (mock data)
│       │       └── Settings.tsx       ← Store config (mock data)
│       ├── package.json               ← @shopify/polaris, recharts, react-router-dom
│       └── vite.config.ts
├── Pokemon/                           ← Git submodule — separate microservice
├── infra/                             ← Personal training lab — NOT part of the app
├── docker-compose.yml                 ← All NexusOS infrastructure
├── Makefile                           ← Developer shortcuts
├── mcp-config.json                    ← MCP tool hub config
├── .env.example                       ← All required env vars with descriptions
└── .gitmodules                        ← Points to Pokemon submodule
```

---

## Key Design Decisions Worth Understanding

**Why Go for the gateway and Python for AI?**  
Go handles thousands of concurrent webhook HTTP connections efficiently with minimal memory. Python has the entire ML/AI ecosystem (CrewAI, Prophet, LangChain, FastAPI). Use the right tool for each job.

**Why Kafka between them?**  
Decouples ingestion from processing. If the Python AI service is slow or restarts, Shopify webhooks are not lost — they sit in Kafka. Go gateway never waits on Python. The system is resilient by design.

**Why Temporal?**  
Some agent workflows take minutes (or longer). Standard HTTP requests time out. Temporal handles durable execution — if an agent crashes mid-workflow, Temporal resumes from the last checkpoint. Critical for multi-step operations like "write email → wait for PokémonTool data → send → wait 24h → send follow-up."

**Why Qdrant?**  
PostgreSQL with pgvector could handle basic vector search, but Qdrant is purpose-built for it — faster at scale, better similarity indexing, already in the stack for proper RAG.

**Why hierarchical CrewAI process?**  
Money decisions cannot be made by individual agents without oversight. The hierarchical process means FinanceAgent reviews every action over $100 before it executes. This is the human-in-the-loop enforcement mechanism built into the agent architecture itself.

**Why MCP Hub?**  
Model Context Protocol lets AI agents call tools (Postgres, Slack, Shopify) in a standardized way. The hub in the Go gateway acts as the single authorized tool execution point — agents request tool calls, the hub validates and executes them. Centralizes auth and audit logging for all AI-initiated actions.
