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
  -> Python api-consumer reads /api/internal/watchlist-targets
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
- `Pokemon/server` now has a PokeTCG-backed card search path through `GET /api/cards/tcg-search?q=...&limit=...`.
- `Pokemon/database/migrations/003_watchlist_market_metadata.sql` adds PokeTCG market metadata fields to `watchlists`.
- `Pokemon/client/src/pages/WatchlistPage.jsx` now supports market-first watchlist creation: search PokeTCG, select exact card/set, calculate a below-market target, then save.
- Watchlist UI was simplified after feedback: the normal flow no longer exposes separate `Market Search` plus editable `Card Name` fields. It is now `Find Card` -> select result -> choose below-market percentage/target -> save.
- `Pokemon/client/nginx.conf` proxies `/api/` to `http://server:3001/api/` so the built client container can call the Go API.
- PokeTCG search now has a fallback for lowercase/partial/slightly misspelled input. Example verified: `radiant charzard` returns `Radiant Charizard` results.
- Inventory is now also market-data-backed. `Pokemon/client/src/pages/InventoryPage.jsx` uses the PokeTCG search/select flow, stores the selected card's market value as `current_value`, and shows cost basis, market value, position value, and unrealized P&L.
- `Pokemon/database/migrations/004_inventory_market_metadata.sql` adds exact-card market metadata to `inventory`.
- `Pokemon/server` now exposes `GET /api/internal/watchlist-targets` so api-consumer receives card name, set name, and `externalCardId` instead of only bare names.
- `Pokemon/docker-compose.yml` pins api-consumer `GO_INTERNAL_URL=http://server:3001/api/internal/watchlist-targets`.
- eBay listing messages now include `external_card_id` when the watchlist row has a PokeTCG card ID.
- Go notification matching now prefers `external_card_id` and falls back to case-insensitive card name for legacy/manual rows.
- The React SSE client now handles `WATCHLIST_HIT`, so watchlist alerts can appear live in the frontend bell/store instead of only after opening/reloading the Alerts page.
- Saving a selected PokeTCG card to watchlist or inventory writes a card-specific daily `price_history` snapshot keyed by the PokeTCG card ID. Search clicks alone do not write snapshots; saving does.
- Slab watchlist MVP is implemented as an explicit asset lane. Raw is the default. Users can choose `Graded Slab` and a lane such as `PSA_10`, `PSA_9`, `CGC_9_5`, `BGS_10`, or `BGS_BLACK_LABEL`.
- `Pokemon/database/migrations/005_watchlist_slab_metadata.sql` adds `asset_type`, `grader`, `grade`, and `slab_tier` to watchlists.
- `Pokemon/services/api-consumer/services/slab_parser.py` parses active eBay listing titles/conditions into slab metadata.
- eBay scans add slab keywords only for slab targets, for example `Armored Mewtwo SM Black Star Promos PSA 10`.
- Raw watchlist rows do not alert on parsed slab listings, and slab watchlist rows do not alert on raw listings.
- Watchlist UI now has `Track All Major Slabs`, which stores one `asset_type='ALL_SLABS'` target for the selected PokeTCG card.
- api-consumer fans out `ALL_SLABS` targets into searches for: PSA 10/9/8/7, CGC 10/9.5/9, and BGS 10/9.5/9.
- `Pokemon/database/migrations/007_card_listing_slab_snapshots.sql` adds listing snapshot fields to `card_listings`: `external_card_id`, `is_slab`, `grader`, `grade`, and `slab_tier`.
- The Go worker now upserts every listing message into `card_listings` so the app can show latest active eBay observations by slab tier.
- `GET /api/cards/{id}/slab-summary` returns the lowest observed active listing per slab tier from the last 7 days.
- `Pokemon/database/migrations/006_alert_listing_dedupe.sql` adds `alerts.listing_id` and a unique partial index on `(user_id, marketplace, listing_id)`.
- eBay `itemId` now flows through api-consumer -> RabbitMQ -> Go worker -> alerts table as `listing_id`.
- Duplicate eBay listing alerts are suppressed at the database layer, so repeated 30-minute scans or service restarts should not create another alert for the same user/listing.
- `docker compose build poketcg` passed from `Pokemon/`.
- `docker compose up -d poketcg` started the container.
- `pokemontool_poketcg` reached healthy status.
- A temporary container on `pokemon_default` successfully called `http://poketcg:8765/health`.
- A temporary container on `pokemon_default` successfully called `http://poketcg:8765/search?q=Radiant%20Charizard&limit=1` and received market data.
- Live smoke test on the Go API passed: authenticated `GET /api/cards/tcg-search?q=Radiant%20Charizard&limit=1` returned PokeTCG market data.
- Live smoke test on `POST /api/watchlist` passed with PokeTCG metadata and a calculated target buy price. The temporary smoke-test user was deleted afterward.
- Built client container responds on `http://localhost:5173`, and `/api/health/freshness` proxies through Nginx to the Go API.
- Live smoke test on `POST /api/inventory` passed with PokeTCG metadata/current value, and `GET /api/inventory` returned the metadata correctly. The temporary smoke-test user was deleted afterward.
- Live smoke test for card-ID alert matching passed: a temporary watchlist with `external_card_id='smp-SM228'` received a `WATCHLIST_HIT` even when the RabbitMQ listing name was not an exact watchlist name. The temporary user was deleted afterward.
- Live smoke test for snapshots passed: adding selected PokeTCG card `smp-SM228` to watchlist wrote today's `price_history` row with `price_tcgplayer=123.45`. The temporary user was deleted afterward.
- Live smoke test for raw-vs-slab separation passed: a PSA 10 listing alerted only the PSA 10 watchlist row, while a raw listing alerted only the raw watchlist row. Temporary users were deleted afterward.
- Live smoke test for listing dedupe passed: publishing the same RabbitMQ listing twice with `listing_id='dedupe-smoke-item-1'` created exactly one alert. Temporary user was deleted afterward.
- Live smoke test for slab summary passed: publishing sample Raw, PSA 10, PSA 9, CGC 9.5, and BGS 10 listing messages for `smp-SM228` returned those rows from `/api/cards/smp-SM228/slab-summary`.

## Watchlist Behavior

Schema:

- `Pokemon/database/migrations/001_init.sql`
- `watchlists.target_buy_price`: alert when listing price drops below or equals this price.
- `watchlists.target_sell_price`: alert when listing price rises above or equals this price.

Current matching logic:

- `Pokemon/server/store/watchlist_store.go`
- `GetAlertCandidates(ctx, cardName, externalCardID, assetType, slabTier, maxPrice)` prefers exact `external_card_id` when present, separates raw and slab lanes, and falls back to case-insensitive card name for legacy/manual rows.

```sql
WHERE target_buy_price >= maxPrice
  AND asset_type = assetType
  AND (assetType = 'RAW' OR slab_tier = slabTier)
  AND (
    external_card_id = externalCardID
    OR legacy/manual name fallback
  )
```

That means if a listing price is `$18.00` and a user's target is `$20.00`, the user is a match.

Current weakness:

- New PokeTCG-backed rows can match by exact card ID.
- Old/manual rows still rely on card-name fallback.
- eBay itself does not know PokeTCG IDs; api-consumer tags results with the ID of the watchlist target it is scanning. This is much cleaner than bare names, but listing title quality still matters.

## What Needs Fixing Next

High priority:

- Verify the updated watchlist UI in a browser across desktop/mobile widths.
- Verify the updated inventory UI in a browser across desktop/mobile widths.
- Decide whether to keep manual card entry visible, hide it behind an advanced fallback, or require PokeTCG selection for all new watchlist rows.
- Add tests for the PokeTCG Go client, target-price calculation, watchlist metadata persistence, and inventory metadata persistence.
- Apply `003_watchlist_market_metadata.sql` and `004_inventory_market_metadata.sql` in every existing environment because Docker init scripts only auto-run on a fresh Postgres volume.
- Apply `005_watchlist_slab_metadata.sql` in every existing environment for the same reason.
- Apply `006_alert_listing_dedupe.sql` in every existing environment for the same reason.
- Apply `007_card_listing_slab_snapshots.sql` in every existing environment for the same reason.

Medium priority:

- Make eBay/listing scanning reliable and observable.
- Confirm whether the older api-consumer TCGdex path should be fixed or removed. Current logs show SSL certificate failures there; the newer PokeTCG container search path works separately.
- Add rate limiting/cache around PokeTCG calls.
- Decide whether PokeTCG should replace or supplement the existing `services/api-consumer` TCG logic.
- Add a data freshness signal so stale market data is clearly marked.
- Keep Postgres, Redis, RabbitMQ, Grafana, Loki, and Prometheus private unless intentionally exposed.

NexusOS / Shopify uncertainty:

- The root Shopify/NexusOS app is a separate business platform for Shopify merchant workflows: dashboard, orders, customers, AI decisions, approvals, workflows, fraud/SEO/cart recovery/marketing/inventory services.
- It does not yet clearly monetize or operate the Pokemon product.
- The likely connection is commercial: use Shopify as the storefront/operator layer for vendors, inventory, subscriptions, checkout, or card-selling workflows, while Pokemon is the market-intelligence product.
- Do not force the two systems together until a specific business workflow is chosen.
- The chosen Shopify direction is documented in `docs/SHOPIFY_POKEMON_STRATEGY.md`: PokemonTool is the market-intelligence engine, Shopify is the commerce/storefront engine.

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
