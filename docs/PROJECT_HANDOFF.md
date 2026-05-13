# Project Handoff

This repo has two related product tracks:

1. NexusOS / Shopify platform at the repo root.
2. Pokemon card market-intelligence app under `Pokemon/`.

Read this before changing architecture. Do not assume old chat context is available.

## Product Concept

The Pokemon app started as a watchlist alert product:

- A user watches Pokemon cards.
- The user sets a buy target price.
- The system scans marketplaces.
- When a listing is at or below the user's target, the system creates an alert.
- The user can use those alerts to buy undervalued cards, flip cards, or track collection opportunities.

The product is moving from "watch a card by name" toward "watch a specific card variant using real market price context." PokeTCG/PokeAi was added so the system can fetch real PokemonTCG market data before setting the user's target price. Example:

- User searches `Radiant Charizard`.
- PokeTCG returns exact card variants like `pgo-11` and `swsh12pt5-20`.
- User selects the exact set/card.
- System reads market price, for example `$23.33`.
- User can set a buy target manually, or as a percentage below market, for example 20% below market = `$18.66`.
- Watchlist alerts should fire for listings at or below that target.

## Current Architecture

Root repo:

- `docker-compose.yml`: NexusOS infrastructure services.
- `docker-compose.dev.yml`: local development stack for web, gateway, AI, and infra.
- `apps/web`: React/Vite frontend for NexusOS.
- `services/gateway`: Go gateway for NexusOS.
- `services/ai`: Python AI/FastAPI service for NexusOS.

Pokemon subsystem:

- `Pokemon/docker-compose.yml`: main Pokemon app stack.
- `Pokemon/server`: Go API server using chi, Postgres, Redis, RabbitMQ, SSE, and auth middleware.
- `Pokemon/client`: React/Vite dashboard for cards, watchlist, alerts, trends, inventory, settings.
- `Pokemon/services/api-consumer`: Python service that scans watched card names and publishes listing events to RabbitMQ.
- `Pokemon/services/analytics-engine`: Python analytics jobs for trends/deals.
- `Pokemon/services/scraping-service`: Go scraping service for marketplace listings.
- `Pokemon/database/migrations`: Postgres schema.
- `PokeTCG/pokeai-service/pokeai`: local PokemonTCG/PokeAi API extracted from `PokeTCG/pokeai-service.zip`.

Runtime data flow for Pokemon alerts:

```text
React client
  -> Go API /api/watchlist
  -> Postgres watchlists table
  -> Python api-consumer reads /api/internal/watchlist-names
  -> marketplace/TCG scanning
  -> RabbitMQ listings queue
  -> Go notification worker
  -> Postgres alerts table + SSE notification
  -> React alerts/dashboard
```

PokeTCG integration target:

```text
React card search
  -> Go Pokemon API
  -> PokeTCG container at http://poketcg:8765
  -> PokemonTCG API market price data
  -> Go API response
  -> watchlist target calculation
```

## Important Docker Networking Rule

Containers can resolve each other by service name only when they share a Docker network.

Because `poketcg` is now in `Pokemon/docker-compose.yml`, other services in that compose project can call:

```text
http://poketcg:8765
```

Do not use `127.0.0.1` from one container to reach another container. Inside a container, `127.0.0.1` means that same container.

If services are split across different compose files, either:

- put them on a shared external Docker network, or
- publish ports on the host and call through the host address.

## What Works Now

- `infra_future_standard` tracks `origin/infra_future_standard`.
- `PokeTCG/pokeai-service.zip` was extracted to `PokeTCG/pokeai-service/pokeai`.
- PokeTCG API works locally with:

```bash
python -B api_server.py --host 0.0.0.0 --port 8765
```

- PokeTCG was dockerized with `PokeTCG/pokeai-service/pokeai/Dockerfile`.
- `Pokemon/docker-compose.yml` includes a `poketcg` service.
- `Pokemon/docker-compose.yml` sets `POKETCG_BASE_URL=http://poketcg:8765` on the Go server container.
- `docker compose build poketcg` passed from `Pokemon/`.
- `docker compose up -d poketcg` started the container.
- `pokemontool_poketcg` reached healthy status.
- A temporary container on `pokemon_default` successfully called `http://poketcg:8765/health`.
- A temporary container on `pokemon_default` successfully called `http://poketcg:8765/search?q=Radiant%20Charizard&limit=1` and received market data.

## Watchlist Behavior

Schema:

- `Pokemon/database/migrations/001_init.sql`
- `watchlists.target_buy_price`: alert when listing price drops below or equals this price.
- `watchlists.target_sell_price`: alert when listing price rises above or equals this price.

Current matching logic:

- `Pokemon/server/store/watchlist_store.go`
- `GetAlertCandidates(ctx, cardName, maxPrice)` uses:

```sql
WHERE card_name = $1 AND target_buy_price >= $2
```

That means if a listing price is `$18.00` and a user's target is `$20.00`, the user is a match.

Current weakness:

- Matching is by exact `card_name`.
- This is fragile because many Pokemon cards share the same name across sets.
- Long-term, watchlists should store external card IDs like `pgo-11`, set name, card number, and chosen variant.

## What Needs Fixing Next

High priority:

- Add a Go client for PokeTCG in `Pokemon/server`.
- Add an authenticated API route such as `GET /api/cards/tcg-search?q=...&limit=...`.
- Update the React watchlist flow so the user searches PokeTCG, selects the exact card/set, sees market price, and chooses a target strategy.
- Store PokeTCG card metadata with watchlist rows: external card ID, set, number, image, market price at add time, market updated date, and target percentage if used.
- Change matching away from exact card name when upstream listings can provide a stable card ID.
- Add tests for target-price calculation and watchlist matching.

Medium priority:

- Make eBay/listing scanning reliable and observable.
- Confirm whether TCG scanning currently works or only eBay works.
- Add rate limiting/cache around PokeTCG calls.
- Decide whether PokeTCG should replace or supplement the existing `services/api-consumer` TCG logic.
- Add a data freshness signal so stale market data is clearly marked.
- Keep Postgres, Redis, RabbitMQ, Grafana, Loki, and Prometheus private unless intentionally exposed.

NexusOS / Shopify uncertainty:

- The root Shopify/NexusOS app is a separate business platform for Shopify merchant workflows: dashboard, orders, customers, AI decisions, approvals, workflows, fraud/SEO/cart recovery/marketing/inventory services.
- It does not yet clearly monetize or operate the Pokemon product.
- The likely connection is commercial: use Shopify as the storefront/operator layer for vendors, inventory, subscriptions, checkout, or card-selling workflows, while Pokemon is the market-intelligence product.
- Do not force the two systems together until a specific business workflow is chosen.

## Business Direction Notes

The strongest product wedge is not "generic Pokemon price search." Many tools can show prices. The stronger wedge is workflow:

- detect underpriced cards,
- alert fast,
- help a seller decide whether to buy,
- track inventory and acquisition cost,
- suggest listing/repricing,
- connect to a Shopify storefront or seller operation.

Potential customer paths:

- Solo collectors/flippers: simple watchlist and alerts.
- Card vendors/local shops: inventory, buy targets, repricing, margin tracking, alerts, and storefront integration.
- Shopify sellers: market-aware product pricing and inventory actions.

Most realistic near-term product:

- B2B/SaaS for card sellers and small shops.
- Charge monthly for market intelligence, alerts, inventory valuation, repricing assistance, and deal detection.
- Shopify becomes useful when the seller actually uses Shopify to sell cards or manage store operations.

Do not pitch billion-dollar scale before proving:

- alerts are accurate,
- market data is fresh,
- users can act faster than manual searching,
- sellers make or save money,
- retention exists,
- acquisition cost is lower than customer lifetime value.

## Suggested Next Session

Use this order:

1. Read `AGENTS.md`.
2. Read this file.
3. Inspect `git status --short`.
4. Inspect `Pokemon/docker-compose.yml`.
5. Inspect `PokeTCG/pokeai-service/pokeai/api_server.py`.
6. Inspect `Pokemon/server/routes/routes.go`, `Pokemon/server/handlers/card_handler.go`, and `Pokemon/server/services/card_service.go`.
7. Implement the Go PokeTCG client and route.
8. Only then update the React watchlist UI.

Suggested skills:

- `handoff` when preparing continuation notes.
- `ui-ux-pro-max` when redesigning the watchlist/search flow.

