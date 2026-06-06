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



### Local Market Search Reliability

Watchlist and Inventory card search require the PokeTCG/PokeAi market-data service.

For local Vite + host-run Go development:

```text
POKETCG_BASE_URL=http://127.0.0.1:8765
```

`Pokemon/docker-compose.yml` must publish the PokeTCG service on the host:

```text
127.0.0.1:8765:8765
```

For Docker-run Go server, Compose overrides the URL to:

```text
http://poketcg:8765
```

If Watchlist or Inventory shows `market data search failed`, first check:

```bash
curl http://127.0.0.1:8765/health
```

Verified on 2026-06-01:

- `pokemontool_poketcg` was restarted with host port `8765` published.
- `GET /api/cards/tcg-search?q=radiant charizard&limit=5` returned real PokeTCG market rows.
- Browser QA on `http://127.0.0.1:5173/watchlist` showed `Radiant Charizard` search results with `$24.81` and `$14.19`, no `market data search failed`, and selecting the `$24.81` result calculated a 15% below-market buy alert of `$21.09`.
- Watchlist and Inventory frontend calculations now use TCGPlayer `market` first, then Cardmarket `cardmarketTrend` if TCGPlayer market is missing.

### Watchlist Live Slab Lookup Reliability

Watchlist `Slabs` cannot rely only on old `card_listings` rows. The UI now refreshes live eBay observations for the watched card before reading `/api/cards/{id}/slab-summary`.

Important behavior as of 2026-06-01:

- `GET /api/cards/ebay-listings` accepts `publish=true`; when set, api-consumer publishes matched live listings to RabbitMQ and the Go worker persists them into `card_listings`.
- Watchlist `Slabs` calls live eBay lookups for supported slab tiers, then reloads the persisted summary.
- PokeTCG search has a backend fallback for collector-style queries where the set and number are part of the search text, for example `lucario 12/16 pokemon rumble`. It now tries official PokemonTCG `name + number` candidates first, ranks by set tokens and printed set total denominator, then falls back to bounded broad name search. This protects cases like `charizard 4/102 base set` from incorrectly choosing Base Set 2.
- eBay slab lookup uses Browse API first, then Scrapling public-search fallback when the strict API query returns zero raw rows or when Browse rows all filter out as wrong card/set/grade. This catches vault/public-search rows that Browse can miss and prevents irrelevant Browse rows from blocking the fallback.
- eBay slab matching now requires set tokens when `setName` is available, so unrelated same-character slabs are not persisted under the watched card.
- Supported summary/search tiers include PSA 10/9/8/7, CGC 10/9.5/9/8.5/8/7.5/7, and BGS 10/9.5/9/8.5/8/7.5/7.

Verified locally on 2026-06-01 for `ru1-12 Lucario Pokemon Rumble #12`:

- `lucario rumble`, `lucario 12/16 pokemon rumble`, and `lucario 12 pokemon rumble` all returned `ru1-12`.
- Broader live matrix also passed: `charizard 4/102 base set -> base1-4`, `pikachu 58/102 base set -> base1-58`, `mewtwo 10/102 base set -> base1-10`, `umbreon 17/17 pop series 5 -> pop5-17`, `rayquaza 128/124 dragons exalted -> bw6-128`, `lugia 9/111 neo genesis -> neo1-9`, `gengar 5/62 fossil -> base3-5`, and `blastoise 2/102 base set -> base1-2`.
- Live slab refresh found PSA 8 `$499.99`, PSA 9 `$580` and `$3,499.99`, and BGS 7.5 `$1,000`.
- Live Azumarill proof after fallback-on-filter-empty fix: `azumarill 1/109 team rocket returns -> ex7-1`; `CGC_10` lookup returned `2004 POKEMON EX TEAM ROCKET RETURNS, REVERSE HOLO AZUMARILL CGC 10 GEM MINT` at `$999.99` and `Azumarill Holo 1/109 Team Rocket Returns - CGC 10` at `$1,572.90`; `/api/cards/ex7-1/slab-summary` persisted both under `CGC_10`.
- Follow-up fix on 2026-06-02: summaries now include `BOTH` language observations when the watchlist is filtered to `ENGLISH` or `JAPANESE`, and Watchlist `Slabs` no longer keeps a stale empty in-memory cache. Verified `/api/cards/ex7-1/slab-summary?languagePreference=ENGLISH` returns the raw English rows and the CGC 10 rows saved as `BOTH`.
- Follow-up hardening on 2026-06-02: Watchlist refresh now calls raw, generic any-slab, and fixed slab-tier lookups; passes `cardNumber` through frontend -> Go -> api-consumer; appends dynamic summary tiers returned by the backend instead of hiding tiers outside the fixed lane list; backend summary no longer filters out unlisted parsed slab tiers. Slab parser now recognizes lower grades down to 1 and `GSG`. Card-number matching rejects conflicting fractions like `025/084` for an English `1/109` card but accepts exact slab titles that omit the card number.
- Important eBay limitation observed on 2026-06-02: eBay public HTML search and Playwright browser fetches returned 403/error pages from this environment for `Azumarill 1/109 Team Rocket Returns`, while a human browser can show more rows. eBay Browse API initially missed visible public rows when `English` was injected into the query. After removing language terms from the query and keeping language as a post-filter, live refresh returned raw rows, `PSA_8`, `CGC_9`, `CGC_10`, and `GRADED_UNKNOWN` for Azumarill. eBay Browse API still returned zero for the visible `PSA_3 James Theme Deck` row even with broader wording, so full parity with a human eBay session still requires a browser/session/proxy-backed collector or a user-authorized eBay/Terapeak data source.
- `/api/cards/ru1-12/slab-summary?languagePreference=BOTH` returned only the relevant Rumble rows after removing bad rows from an earlier broad test.

## Current PokemonTool -> Odoo Store State

The Odoo storefront is now connected to real PokemonTool inventory instead of being only a static marketing page.

Local URLs:

```text
Pokemon app: http://127.0.0.1:5173
Pokemon API: http://127.0.0.1:3001
Odoo store:  http://127.0.0.1:8069/pokecard-store
Odoo login:  http://127.0.0.1:8069/web/login?db=pokecard_store
```

Current account sync behavior:

- Successful Pokemon register/login calls the Odoo syncer.
- The Odoo user login is the same email as Pokemon.
- The Odoo password is updated from the successful Pokemon login password.
- Verified locally on 2026-06-01 with the configured test account: Pokemon login succeeded, Odoo JSON auth succeeded, and Odoo web login redirected away from `/web/login`.

Current inventory-to-store behavior:

- `POST /api/inventory/{id}/store-listing` marks the Pokemon inventory row `READY` and calls Odoo JSON-RPC to create/update `product.template` using `pokemon_inventory_id` as the stable key.
- On successful Odoo product sync, Pokemon now records `inventory.store_synced_at` so the backend can prove the row reached Odoo.
- Odoo products are created with `sale_ok=true`, `is_published=true`, Pokemon metadata fields, image URL, and storefront price.
- `/pokecard-store` now queries Odoo `product.template` rows where `pokemon_inventory_id` exists and renders live synced products directly on the storefront.

Verified local product state on 2026-06-01:

- Pokemon inventory row `b92ab149-b9d9-4be2-9091-ca63e31a611e` for `Blastoise - Platinum - #2 - NM` is `READY` with store price `$36.42` and a non-null `store_synced_at`.
- Odoo product `Blastoise - Platinum - #2 - NM` exists, is published, has `pokemon_inventory_id=b92ab149-b9d9-4be2-9091-ca63e31a611e`, and list price `$36.42`.
- Browser QA for `http://127.0.0.1:8069/pokecard-store` found the product visible, the price visible, the `Synced from PokemonTool` section visible, no console errors, no failed network responses, and the product detail link `/shop/product/6` returned HTTP 200.

Important caveat:

- Odoo only knows about Pokemon users after they successfully register/login through Pokemon after the Odoo syncer is configured. Existing Pokemon users should log into Pokemon once to push/update their Odoo account.
- Odoo only shows inventory rows that were explicitly sent through Add to Store. It does not auto-publish every inventory item.

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

NexusOS / Shopify / Odoo commerce direction:

- The root Shopify/NexusOS app remains a separate business platform for Shopify merchant workflows.
- Odoo is now the local free storefront/ERP path for the Pokemon seller workflow.
- PokemonTool is the market-intelligence and inventory source of truth; Odoo is the commerce surface for products, storefront pages, customers, sales, inventory operations, and orders.
- Do not treat `/pokecard-store` as static marketing. It must continue rendering real `pokemon_inventory_id` products from Odoo.
- The chosen Shopify direction is documented in `docs/SHOPIFY_POKEMON_STRATEGY.md`: PokemonTool is the market-intelligence engine, Shopify/Odoo are commerce/storefront options.

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

## Session Update - 2026-05-27

Read this before restarting Pokemon infra or touching global Codex setup.

What happened this session:

- User asked to understand the Pokemon project with understand-anything. A fallback graph was generated because the full understand-anything flow needed plugin dependencies and agent workflow support.
- Generated files in Pokemon:
  - `Pokemon/.understand-anything/knowledge-graph.json`
  - `Pokemon/.understand-anything/meta.json`
  - `Pokemon/scripts/ua_fallback_graph_builder.js`
- The Understand Anything dashboard was started on `127.0.0.1:5173` and then stopped. It is no longer running.
- Docker infra issue was diagnosed:
  - Initial failure was `127.0.0.1:5432` already in use when Docker tried to publish Postgres.
  - Postgres data was not wiped; logs showed the existing database directory was reused.
  - After ports were cleared, Postgres recreated cleanly and published `127.0.0.1:5432->5432`.
- A scraper container startup bug was fixed in `Pokemon/services/scraping-service/Dockerfile`:
  - The image contained `/app/main`, while the container command expected `./scraper`.
  - Dockerfile was changed to build/copy/run `main` consistently.
- After the fix, the Pokemon compose stack reached running state and `http://127.0.0.1:3001/health` returned `200`.
- User then explicitly requested all containers be stopped. All running Docker containers were stopped and `docker ps` showed no running containers.
- ECC was installed globally for Codex:
  - Repo cloned to `/home/iscjmz/.codex/ECC`.
  - Local Codex marketplace wrapper created at `/home/iscjmz/.codex/ecc-marketplace`.
  - Plugin installed/enabled as `ecc@ecc` version `2.0.0-rc.1`.
  - ECC AGENTS guidance merged into `/home/iscjmz/.codex/AGENTS.md` with markers.
  - ECC Codex role files copied to `/home/iscjmz/.codex/agents`.
  - ECC prompts generated under `/home/iscjmz/.codex/prompts`.
  - ECC MCP config entries were merged additively into `/home/iscjmz/.codex/config.toml`.
  - Backup was saved at `/home/iscjmz/.codex/backups/ecc-manual-20260527-1135`.
  - ECC global Git hooks were intentionally not enabled because they would set global `core.hooksPath` for every repo.

Current known dirty state after this session:

```text
Pokemon/services/scraping-service/Dockerfile  # modified; actual infra fix
Pokemon/.understand-anything/                 # untracked generated graph
Pokemon/scripts/ua_fallback_graph_builder.js  # untracked fallback graph builder
```

Important next-session instructions:

1. Start by reading `/home/iscjmz/shopify/shopify/AGENTS.md` and this handoff file before taking action.
2. Do not assume Pokemon containers are running; the user asked for all containers to be stopped.
3. If restarting Pokemon infra, inspect `Pokemon/docker-compose.yml` first and check host ports `5432` and `5173` before `docker compose up -d`.
4. Do not restart the Understand Anything dashboard unless the user asks for it; it competes with Pokemon client port `5173`.
5. Treat `Pokemon/services/scraping-service/Dockerfile` as an intentional local fix unless the user asks to revert it.
6. Decide with the user whether to keep or delete the generated `.understand-anything` graph files and fallback builder.


## Session Update - 2026-05-30 Odoo Storefront Starter

Read this before editing Odoo, Shopify, or Pokemon commerce boundaries.

What changed:

- Official Odoo Community source was shallow-cloned into `vendor/odoo` on branch `19.0`.
- Parent repo ignores `/vendor/odoo/` so the 47k-file upstream source checkout is available locally but not accidentally committed.
- Project-owned Odoo work now lives under `odoo/`, not inside Odoo core.
- Added `docker-compose.odoo.yml` for a local Odoo 19 Community + Postgres stack.
- Added `odoo/config/odoo.conf` with `/mnt/extra-addons` in `addons_path` so project custom addons load.
- Added `odoo/.env.example` for local Odoo ports and development DB credentials.
- Added `odoo/custom_addons/pokecard_storefront`, a starter Odoo addon for a Pokemon card seller storefront.
- Added `odoo/scripts/validate_odoo_scaffold.sh` for cheap validation without starting services.
- Added `odoo/README.md` with first-run, install, and production-hardening notes.

Current intended Odoo shape:

```text
vendor/odoo                       # ignored upstream Odoo source reference
odoo/config/odoo.conf             # tracked project Odoo config
odoo/custom_addons/               # tracked custom Odoo modules
odoo/custom_addons/pokecard_storefront
odoo/scripts/validate_odoo_scaffold.sh
docker-compose.odoo.yml           # local Odoo runtime stack
```

Local validation command:

```bash
bash odoo/scripts/validate_odoo_scaffold.sh
```

Local startup command:

```bash
cp odoo/.env.example odoo/.env
docker compose -f docker-compose.odoo.yml --env-file odoo/.env up -d
```

Then open:

```text
http://127.0.0.1:8069
```

Install addon in Odoo Apps:

```text
PokeCard Storefront
```

Storefront route after addon install:

```text
/pokecard-store
```

Important product boundary:

- Odoo is now a free ERP/eCommerce storefront candidate for card seller operations.
- Shopify remains a separate commerce/storefront direction already documented in `docs/SHOPIFY_POKEMON_STRATEGY.md`.
- PokemonTool remains the market-intelligence engine.
- Do not force Odoo, Shopify, and PokemonTool together until a concrete workflow is chosen.
- The clean likely integration is: PokemonTool inventory/market intelligence -> Odoo products/pricing/inventory -> Odoo storefront/orders.

What remains:

- Run the Odoo stack and create the first local database.
- Install `PokeCard Storefront` in Odoo Apps and verify `/pokecard-store` in a browser.
- Add real Odoo product categories: Raw Singles, Graded Slabs, Sealed Product, Concierge Sourcing.
- Design a sync path from PokemonTool inventory to Odoo products.
- Add custom Odoo fields for card metadata: external card ID, set, number, grade, grader, cert number, market value, acquisition cost, and target margin.
- Add production hardening before public exposure: HTTPS proxy, strong secrets, backups, restore test, email, payment provider, logs, and alerts.

Verified runtime state - 2026-05-30:

- Local Odoo Docker stack is running with containers `shopify-odoo` and `shopify-odoo-db`.
- Database `pokecard_store` was initialized with `website_sale` and `pokecard_storefront`.
- `odoo/config/odoo.conf` now pins `dbfilter = ^pokecard_store$` so localhost routes bind to the initialized database.
- Verified `http://127.0.0.1:8069/pokecard-store` returns HTTP 200 and renders the custom PokeCard storefront content.
- `bash odoo/scripts/validate_odoo_scaffold.sh` passes after the config change.

## Session Update - 2026-05-30 Odoo Pokemon Inventory Bridge

Read this before editing Pokemon inventory, Odoo products, or store/backend boundaries.

Direction clarified by user:

- The Pokemon card store should use Odoo as the sellable backend.
- PokemonTool should not be a separate disconnected app for this workflow.
- PokemonTool remains the card intelligence/inventory source, while Odoo owns products, stock, CRM, sales, customers, checkout, and orders.

Implemented local slice:

- Upgraded `odoo/custom_addons/pokecard_storefront` from storefront-only to storefront + Pokemon product metadata.
- Added `odoo/custom_addons/pokecard_storefront/models/product_template.py` extending Odoo `product.template` with Pokemon fields.
- Added backend product tab `views/product_template_views.xml` named `Pokemon Inventory`.
- Added `odoo/custom_addons/pokecard_storefront/scripts/sync_pokemon_inventory_to_odoo.py` for one-way sync from PokemonTool Postgres inventory rows to Odoo products through XML-RPC.
- Updated `odoo/README.md` with bridge runbook and dry-run command.
- Updated plan at `docs/superpowers/plans/2026-05-30-odoo-pokemon-inventory-bridge.md`.

Installed in the running `pokecard_store` Odoo database:

- `crm`
- `stock`
- `sale_management`
- `website_sale_stock`
- `pokecard_storefront`

Verified:

- `python3 -m py_compile` passed for the manifest, model extension, and sync script.
- `bash odoo/scripts/validate_odoo_scaffold.sh` passed.
- Odoo module upgrade completed successfully and loaded 94 modules.
- Database shows all five target modules installed.
- `product_template` has 18 `pokemon_*` columns.
- `http://127.0.0.1:8069/pokecard-store` still returns HTTP 200 after the upgrade.

Important next step:

- Run the sync script against a running PokemonTool Postgres database after creating/confirming Odoo admin credentials. Use `--dry-run` first. The current script creates/updates Odoo products, but deeper stock quantity synchronization via `stock.quant` should be added as a separate safe step after product upsert is verified.

## Session Update - 2026-05-30 Wholesale Slab AI Direction

User clarified the next product wedge:

- PokemonTool should help find graded slabs at wholesale/underpriced prices.
- The system should identify bigger slab flips, estimate resale value, score risk/confidence/liquidity, and then connect approved opportunities to Odoo inventory/products.

Current state:

- Not fully implemented yet.
- Existing foundation already includes slab parsing, slab watchlists, slab listing snapshots, slab summary endpoint, and basic deal-of-day infrastructure.
- Odoo is already prepared to receive Pokemon card products and metadata through `pokecard_storefront` fields and the XML-RPC sync bridge.

Plan created:

- `docs/superpowers/plans/2026-05-30-wholesale-slab-ai.md`

Planned architecture:

```text
marketplace active listings + sold comps
  -> slab parser
  -> sold-comp valuation engine
  -> wholesale opportunity scorer
  -> human approval queue
  -> PokemonTool inventory row
  -> Odoo product/inventory sync
  -> Odoo storefront/orders/CRM
```

Important product/security decisions:

- Do not auto-buy.
- Do not let an LLM be the price source of truth.
- Use sold comps and deterministic valuation first.
- Use AI/LLM only for messy title interpretation, confidence explanation, and evidence summarization.
- Require human approval before pushing candidates into sellable Odoo inventory.

## Session Update - 2026-05-30 Wholesale Slab AI Implementation

Implemented the first full vertical slice of the wholesale slab sourcing feature.

Pokemon database:

- Added `Pokemon/database/migrations/011_slab_wholesale_opportunities.sql`.
- Adds `slab_comps` for sold-comparable slab sales.
- Adds `slab_opportunities` for ranked active buy candidates.
- Adds nullable slab metadata to `inventory`: `asset_type`, `grader`, `grade`, `slab_tier`, `cert_number`, `target_sale_price`.
- Applied the migration to local Pokemon Postgres and verified tables/indexes exist.

Analytics engine:

- Added `slab_valuation.py` for median sold-comp valuation with outlier filtering.
- Added `slab_opportunity_scorer.py` for all-in cost, expected profit, margin, liquidity/confidence/risk, and deal score.
- Added `analyzers/slab_opportunity_finder.py` to score recent active slab listings and upsert opportunities.
- Extended `repositories/listing_repo.py` with slab listing, sold comp, and opportunity persistence methods.
- Wired the finder into `services/analytics-engine/main.py` on `SLAB_OPPORTUNITY_INTERVAL_HOURS`.
- Added unittest regression coverage under `services/analytics-engine/tests/`.

Go API:

- Added `SlabOpportunity` model, store, service, and handler.
- Added protected endpoints:
  - `GET /api/slab-opportunities`
  - `POST /api/slab-opportunities/{id}/approve`
  - `POST /api/slab-opportunities/{id}/reject`
- Approval creates a PokemonTool inventory row for the authenticated user with slab metadata and acquisition/market values.
- Rejection marks the opportunity rejected.

React UI:

- Added `client/src/pages/SlabOpportunitiesPage.jsx`.
- Added `/slab-opportunities` route and `Slab Finder` navigation item.
- UI shows score, profit, margin, confidence, risk, evidence reason, filters, listing link, approve, and reject.

Odoo bridge:

- Extended `odoo/custom_addons/pokecard_storefront/scripts/sync_pokemon_inventory_to_odoo.py` to read slab metadata from Pokemon inventory and map it into Odoo Pokemon product fields.

Verification:

- `python3 -m unittest discover -s Pokemon/services/analytics-engine/tests -p 'test_*.py'` passed.
- `python3 -m py_compile` passed for new analytics and Odoo sync files.
- `go test ./...` passed in `Pokemon/server`.
- `npm install` was run in `Pokemon/client` because `vite` was missing locally.
- `npm run build` passed in `Pokemon/client`.
- `npm audit --audit-level=moderate` reports 2 moderate Vite/esbuild dev-server vulnerabilities; fix requires a breaking Vite major upgrade and was not forced in this session.

Operational notes:

- Odoo containers are still running.
- Pokemon Postgres was started to apply/verify the migration.
- Full production behavior still needs real sold-comp ingestion data. The scoring engine is implemented, but it can only produce good opportunities when `slab_comps` and active `card_listings` are populated.

## Session Update - 2026-05-31 Product/Infra/Money Model Doc

Created `docs/PRODUCT_INFRA_MONEY_MODEL.md` as the single high-level orientation file for:

- what PokemonTool is
- who it serves
- how PokemonTool, Odoo, and Shopify/NexusOS fit together
- how the product can make money
- where Scrapling fits in the data-ingestion pipeline
- what is built now vs what is still missing

Future agents should read it after this handoff before making architecture or product-direction changes.

## Session Update - 2026-05-31 Scrapling Integration

Integrated Scrapling into the Pokemon ingestion layer.

Verified source details before integration:

- Repo: `D4Vinci/Scrapling`
- PyPI package: `scrapling`
- License: BSD-3-Clause
- Installed version: `0.4.7`

Implemented:

- Added `scrapling[fetchers]==0.4.7` and `psycopg2-binary==2.9.9` to `Pokemon/services/api-consumer/requirements.txt`.
- Installed dependencies into `Pokemon/services/api-consumer/venv`.
- Added `Pokemon/services/api-consumer/services/scrapling_sold_comps.py`.
- Added `Pokemon/services/api-consumer/repositories/slab_comp_repo.py`.
- Added `Pokemon/services/api-consumer/scrapling_sold_comps_ingest.py`.
- Added `docs/SCRAPLING_INTEGRATION.md`.
- Updated `docs/PRODUCT_INFRA_MONEY_MODEL.md` with Scrapling integration status.

Verification:

- `import scrapling` reports `0.4.7` in the api-consumer venv.
- Python compile check passed for the new Scrapling modules and CLI.
- CLI help works.
- Harmless dry-run against `https://quotes.toscrape.com/` fetched HTTP 200 and parsed one test row without writing to Postgres.

Important guardrail:

- Scrapling is a scraping tool, not permission to scrape every site. Use official APIs where available, respect terms/robots/rate limits, and use dry-run before inserting comps.

## Session Update - 2026-05-31 Sold-Comp Batch Loop And Trend-Aware Slab Ranking

Implemented the next bridge toward real-time slab buy/sell alerts.

What changed:

- Added `Pokemon/services/api-consumer/services/scrapling_sold_comps_batch.py` for JSON-configured, approved sold-comp source batches.
- Added `Pokemon/services/api-consumer/scrapling_sold_comps_batch.py` CLI.
- Added `Pokemon/services/api-consumer/config/sold_comps.sources.example.json` as a disabled source template.
- Added `SOLD_COMP_SOURCES_CONFIG`, `SOLD_COMP_INTERVAL_MINUTES`, and `SOLD_COMP_DRY_RUN` support to the api-consumer background service.
- Added minute-level slab scoring with `SLAB_OPPORTUNITY_INTERVAL_MINUTES` while preserving the old `SLAB_OPPORTUNITY_INTERVAL_HOURS` fallback.
- Extended slab valuation with trend scoring from recent sold comps versus older comps.
- Added regression tests for the sold-comp batch runner and trend-aware valuation.

Important state:

- The local database had active slab listing snapshots, but no real `slab_comps`, so real candidate alerts still require approved sold-comp source configs.
- The pipeline now exists for real source data: source config -> Scrapling batch -> `slab_comps` -> analytics scorer -> `slab_opportunities` -> Slab Finder UI.
- Do not enable broad scraping without verifying source terms, selectors, and dry-run output.

## Session Update - 2026-05-31 Live Slab Research Connector

Implemented a real live slab source connector after verifying the project eBay credentials live in `Pokemon/.env`.

Added:

- `Pokemon/services/api-consumer/services/pricecharting_market.py` for PriceCharting big movers and grade-price parsing via Scrapling.
- `Pokemon/services/api-consumer/services/live_slab_research.py` for strict PriceCharting + eBay active-ask research.
- `Pokemon/services/api-consumer/live_slab_research.py` CLI.
- `Pokemon/services/api-consumer/config/live_slab_targets.example.json` with an Armored Mewtwo SM228 PSA 10 curated target.
- Tests for PriceCharting parsing, eBay numeric price parsing, curated target loading, buy/sell signal classification, and rejecting wrong-variant Charizard false positives.

Live verification:

- `PYTHONPATH=. python3 live_slab_research.py --mover-limit 8 --target-config config/live_slab_targets.example.json` ran against live PriceCharting + eBay and returned zero production buy candidates.
- Relaxed thresholds returned three exact Armored Mewtwo SM228 PSA 10 active eBay listings, all as `SELL_RESEARCH` because asking prices were above the PriceCharting PSA 10 reference.

Important product note:

- This is now real internet research, not mock data.
- It intentionally refuses false buy alerts when identity or economics do not clear strict filters.
- Next integration step is persisting live research output into `slab_opportunities` or a dedicated research signal table and exposing it in the Slab Finder UI.

## Session Update - 2026-05-31 Inventory Add-to-Store Gate

Read this before editing Pokemon inventory, Odoo sync, or slab flipping workflows.

Implemented the missing user-controlled commerce action between PokemonTool inventory and Odoo products:

- Added `Pokemon/database/migrations/012_inventory_store_listing_status.sql`.
- Inventory rows now support `store_listing_status`, `store_price`, `store_listing_notes`, `store_listed_at`, and `store_synced_at`.
- Added protected endpoint `POST /api/inventory/{id}/store-listing`. It marks a user-owned inventory row `READY` for store sync with an explicit store price.
- Updated `Pokemon/client/src/pages/InventoryPage.jsx` with an Add to Store action and store status/price display.
- Updated `odoo/custom_addons/pokecard_storefront/scripts/sync_pokemon_inventory_to_odoo.py` so normal sync only reads inventory rows marked `READY`. Use `--include-all-inventory` only for old broad sync behavior. Successful non-dry-run sync marks rows `SYNCED`.

Verified locally:

- `go test ./services` passed after a RED test proved the method/model did not exist.
- `go test ./...` passed in `Pokemon/server`.
- `npm run build` passed in `Pokemon/client`.
- Applied migration 012 to local Pokemon Postgres.
- Created a temporary user and slab inventory row through the real API, then called `POST /api/inventory/{id}/store-listing`; response returned `storeListingStatus: READY` and `storePrice: 10800`.
- Ran Odoo bridge dry-run with `POKEMON_POSTGRES_DSN=...`; it selected exactly the `READY` row and built an Odoo `product.template` payload. Temporary user was deleted afterward.

Product boundary is now clearer:

```text
Live slab research -> slab_opportunities
Seller approves/owns item -> inventory
Seller presses Add to Store -> inventory.store_listing_status = READY
Odoo sync script -> creates/updates Odoo product -> marks inventory SYNCED
```

This is helpful because the scanner can be aggressive about finding/valuing slabs, while store publishing stays under explicit seller control.

## Session Update - 2026-06-02 Watchlist Slab Summary No-Truncation Fix

Fixed a generic Watchlist slab display issue that made real eBay observations look missing even after scans found them.

What changed:

- `Pokemon/server/store/card_store.go` no longer limits slab summary rows to `rn <= 5` per lane. The summary now returns every listing stored for the card/tier/language window, ordered by lane and lowest active price.
- Dynamic lower grades are labeled generically (`PSA_3` -> `PSA 3`, `CGC_6` -> `CGC 6`, `BGS_2` -> `BGS 2`) instead of falling back to raw tier codes.
- `Pokemon/client/src/pages/WatchlistPage.jsx` now includes full PSA/CGC/BGS 1-10 slab options, so Watchlist live refresh deliberately scans lower grades like PSA 3 instead of only PSA/CGC/BGS 7-10.
- The Watchlist table header changed from `Top Matches` to `Matches` because the backend is no longer intentionally returning a five-row preview.
- Added `Pokemon/server/store/card_store_test.go` to lock down lower-grade slab labels.

Verified locally:

- `go test ./...` passed in `Pokemon/server`.
- `venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` passed in `Pokemon/services/api-consumer`.
- `npm run build` passed in `Pokemon/client`.
- Restarted the local Go API on port `3001`.
- Authenticated local check of `/api/cards/ex7-1/slab-summary?languagePreference=ENGLISH` returned all six RAW rows instead of the previous five-row cap, plus PSA 8, CGC 9, CGC 10, and GRADED_UNKNOWN rows for Azumarill.

Known limitation:

- eBay public browser search can show rows that the eBay Browse API and unauthenticated Scrapling/browser automation do not return. The app now shows all rows it can retrieve and persist, but full parity with a human eBay page still needs an authenticated/session-backed source, proxy-backed collector, Terapeak/export ingestion, or a manual paste/import workflow.

## Session Update - 2026-06-02 eBay Copied-Text Import Fallback

Implemented a generic fallback for eBay rows that are visible in the user's browser but not returned by the eBay Browse API or unauthenticated Scrapling/browser automation.

What changed:

- Added `EbayService.import_listing_text(...)` in `Pokemon/services/api-consumer/services/ebay_service.py`.
- Added copied eBay search text parsing with deterministic `manual:<hash>` listing IDs, generated eBay search URLs, and the existing strict card filters.
- Added `POST /ebay/import-text` in the API-consumer.
- Added protected Go proxy `POST /api/cards/ebay-import-text` in `Pokemon/server`.
- Added a Watchlist expanded-panel paste box and `Import eBay Text` action in `Pokemon/client/src/pages/WatchlistPage.jsx`.
- Expanded scheduled `ALL_SLABS` scanning in `Pokemon/services/api-consumer/main.py` to PSA/CGC/BGS 1-10 instead of only high grades.
- Adjusted set matching to treat `EX` as a generic Pokemon set prefix, so `EX Team Rocket Returns` watch targets match eBay titles that say only `Team Rocket Returns`.
- Adjusted the blocklist so `deck` terms can pass only when slab parsing confirms the row is actually a graded slab. This allows rows like `James Theme Deck PSA 3` without opening raw deck false positives.

Verified locally:

- `go test ./...` passed in `Pokemon/server`.
- `venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` passed in `Pokemon/services/api-consumer` with 28 tests.
- `npm run build` passed in `Pokemon/client`.
- Restarted API-consumer on `8001` and Go API on `3001`.
- Protected live import call for Azumarill copied text returned two imported slabs: PSA 8 at `$74.01` and PSA 3 at `$35`.
- Protected slab summary for `ex7-1` then included the imported `PSA_3` lane with listing id `manual:e6d70b828cdf7e6345dc2704`.

How to use:

1. Open Watchlist.
2. Click `Slabs` on the exact card.
3. Copy visible eBay search result text from the browser.
4. Paste into the new import box and click `Import eBay Text`.
5. The app filters by card name, set, card number, language, and slab parser before saving rows.

Important limitation:

- This is a fallback for browser-visible rows; it does not replace real API/Scrapling scans. If a source blocks automation but the user can see rows manually, paste/import brings those rows into the same `card_listings` pipeline without weakening global filters.

## Session Update - 2026-06-02 Generic eBay Slab Query Fix For Sparse Slabs

Fixed the generic missing-slab issue reproduced with Spinda 26/92 EX Legend Maker.

Root cause:

- The frontend already sent `cardNumber`, but `EbayService.scan_card` did not include card number query variants in eBay slab searches.
- `EbayRepo.search_listings` always appended `pokemon card` to every query. This helped raw searches but broke some sparse exact slab searches. Example: eBay Browse API found `Spinda 26/92 EX Legend Maker CGC 9`, but the repo-mutated query could return zero.
- This caused the Watchlist slab table to show many RAW rows but zero slab rows even when eBay human search showed slabs in the title/image.

What changed:

- Added `_search_queries(...)` in `Pokemon/services/api-consumer/services/ebay_service.py`.
- Slab searches now try multiple generic query variants when a card number exists: base set + grade, `card number + set + grade`, `#number + set + grade`, and grade-first variants.
- Raw searches keep the cheaper existing path.
- Added `_marketplace_query(...)` in `Pokemon/services/api-consumer/repositories/ebay_repo.py` so rich slab/card-number queries are not mutated with an extra `pokemon card` suffix.
- Added regression tests proving number-specific fallback queries find sparse slab rows and rich slab queries are not mutated.

Verified locally:

- Direct fixed service scan for Spinda `ex12-26` found live eBay slabs:
  - `CGC_9` at `$15.99`: `Spinda Pokemon 2006 EX Legend Maker 26/92 Rare - CGC 9 MINT`
  - `CGC_10` at `$679.99`: `CGC 10 Gem Mint Spinda EX Legend Maker 26/92 Reverse Holo Stamp Pokemon Low Pop`
  - `PSA_7` at `$125`: `2006 POKEMON EX LEGEND MAKER #26 SPINDA-REVERSE FOIL PSA 7`
- Restarted API-consumer on `8001`.
- Published those three Spinda slab rows through the fixed live endpoint.
- Protected Go slab summary for `/api/cards/ex12-26/slab-summary?languagePreference=ENGLISH` now returns RAW rows plus `PSA_7`, `CGC_10`, and `CGC_9` lanes.
- `venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` passed with 30 tests.
- `go test ./...` passed in `Pokemon/server`.
- `npm run build` passed in `Pokemon/client`.

## Session Update - 2026-06-02 Authenticated eBay Seller Hub Research Connector

Implemented the first authenticated Seller Hub Product Research connector. This is the bridge for combining Scrapling/Playwright-style browser automation with eBay Research metrics such as active/sold counts, listing averages, bids, watchers, shipping, and promoted listing share.

What changed:

- Added migration `Pokemon/database/migrations/014_seller_hub_research_metrics.sql` and applied it locally.
- Added `seller_hub_research_metrics` table for per-card/per-grade/per-tab Product Research snapshots.
- Added `Pokemon/services/api-consumer/services/seller_hub_research.py`:
  - Builds grade-specific Seller Hub keywords, for example `Gengar & Mimikyu GX 165 Team Up PSA 10`.
  - Builds `/sh/research` URLs for `ACTIVE` and `SOLD` tabs.
  - Parses Seller Hub text for average listing price, price range, average shipping, free shipping %, total listings, promoted %, bids, watchers, top rows, and slab tiers.
  - Supports a persistent local Playwright profile at `Pokemon/.local/ebay-seller-hub-profile` by default.
- Added `Pokemon/services/api-consumer/repositories/seller_hub_research_repo.py` for upserting metrics.
- Added `Pokemon/services/api-consumer/seller_hub_research.py` CLI:
  - `venv/bin/python seller_hub_research.py login`
  - `venv/bin/python seller_hub_research.py run --card-name ... --set-name ... --card-number ... --slab-tier PSA_10 --persist`
- Added API-consumer endpoints:
  - `POST /seller-hub/login`
  - `POST /seller-hub/research/run`
- Added opt-in background loop controlled by `EBAY_SELLER_HUB_RESEARCH_ENABLED=true`. When enabled, it reads Go watchlist targets and researches configured grade tiers/tabs on an interval.
- Added `playwright==1.54.0` to api-consumer requirements and ignored `Pokemon/.local/` in git.

Important operating model:

- Do not paste eBay passwords or cookies into chat/docs/code.
- First run the login command locally and log into eBay in the opened browser. The browser profile stays local under `.local/` and is ignored by git.
- After login, run one-off research or enable the loop with env vars.
- Default loop is disabled so normal scans do not fail if Seller Hub login is not set up.

Useful env vars:

- `EBAY_SELLER_HUB_PROFILE_DIR` defaults to `Pokemon/.local/ebay-seller-hub-profile`.
- `EBAY_SELLER_HUB_RESEARCH_ENABLED=false` by default.
- `EBAY_SELLER_HUB_RESEARCH_INTERVAL_MINUTES=240`.
- `EBAY_SELLER_HUB_GRADE_LIMIT=6` for a conservative first pass.
- `EBAY_SELLER_HUB_DAY_RANGE=30`.
- `EBAY_SELLER_HUB_TABS=ACTIVE,SOLD`.
- `EBAY_SELLER_HUB_BROWSER_CHANNEL=chrome` uses a system Chrome install when available.
- `EBAY_SELLER_HUB_BROWSER_EXECUTABLE=/path/to/browser` can point at a trusted local browser binary.

Login caveat:

- If eBay/Google shows `This browser or app may not be secure`, do not use Google/social sign-in inside the automated browser. Use direct eBay email/username login, or install system Chrome and run with `EBAY_SELLER_HUB_BROWSER_CHANNEL=chrome`.

Verified locally:

- `venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` passed with 33 tests.
- `go test ./...` passed in `Pokemon/server`.
- `npm run build` passed in `Pokemon/client`.
- Seller Hub metrics migration applied successfully.
- Synthetic Seller Hub metric upsert succeeded and was removed afterward.
- API-consumer restarted on `8001`; logs show Seller Hub loop installed and disabled until env flag is enabled.

Remaining work:

- User must complete one local eBay Seller Hub login in the persistent browser profile.
- After that, run one one-off Seller Hub research command against a known card and inspect the saved metrics.
- Then wire the saved metrics into Slab Finder scoring/UI so opportunities use Seller Hub active/sold/watchers/bids instead of only Browse API active asks and PriceCharting references.

## Session Update - 2026-06-03 Seller Hub Metrics In Finder + Headroom Codex Setup

Authenticated eBay Seller Hub Product Research is now proven and connected to Finder output.

What changed:

- Installed user-local Chrome-for-Testing at `/home/iscjmz/.cache/chrome-for-testing/chrome/linux-149.0.7827.54/chrome-linux64/chrome` because eBay rejected Playwright's bundled Chromium during login/verification.
- Added ignored local api-consumer `.env` setting `EBAY_SELLER_HUB_BROWSER_EXECUTABLE=.../chrome` so the Seller Hub CLI uses the local Chrome binary without storing credentials.
- Updated `Pokemon/services/api-consumer/seller_hub_research.py` to load `.env` and use configurable browser executable/channel options.
- Hardened Seller Hub auth detection so eBay verification/checkpoint pages (`Please verify yourself`, blocked browser warnings, access denied pages) fail loudly instead of being parsed as zero listings.
- Added migration `Pokemon/database/migrations/015_seller_hub_metric_helpers.sql` with reusable helpers:
  - `latest_seller_hub_metric(...)`
  - `seller_hub_snapshot(...)`
- Updated `Pokemon/server/store/slab_opportunity_store.go` so `GET /api/slab-opportunities` includes latest Seller Hub `ACTIVE` and `SOLD` snapshots as `sellerHubMetrics`.
- Updated `Pokemon/client/src/pages/SlabOpportunitiesPage.jsx` so Finder cards display eBay Research active/sold metrics when available: listing count, average listing price, watchers, bids, research date, and source link.

Live proof:

- Seller Hub Product Research for `Pikachu PSA 10` returned real active-listing metrics from the authenticated browser profile, including total listings, average listing price, shipping, promoted share, watchers, bids, and parsed top rows.
- Persisted real Seller Hub Product Research rows for current watchlist card `Spinda ex12-26`:
  - `PSA_7`: 1 active listing, avg `$125.00`, 3 watchers.
  - `CGC_9`: 1 active listing, avg `$15.99`, 9 watchers.
  - `CGC_10`: 1 active listing, avg `$679.99`, 13 watchers.
- Persisted a Seller Hub Product Research row for existing Finder card `Charizard [1st Edition] #4 PSA_10`; protected `GET /api/slab-opportunities?q=Charizard&limit=5` returned 5 opportunities with `sellerHubMetrics.active` attached. Sample metric: 191 active listings, `$47,506.63` average listing price, 96.7 average watchers, 3,320 max watchers.

Verified:

- `go test ./...` passed in `Pokemon/server`.
- `npm run build` passed in `Pokemon/client`.
- API-consumer health returned `{"status":"ok","service":"api-consumer","rabbitmq":"connected"}`.
- Host-run Go API restarted on `3001` with host-local Postgres, Redis, RabbitMQ, PokeTCG, and api-consumer URLs.

Important caveat:

- Seller Hub broad keyword searches can include mixed rows if keywords are broad, for example other Charizard/1st-edition items. The connector now gets the real data, but the next scoring improvement should make Seller Hub keywords stricter using exact set/card number and row-level identity filtering before using the metrics for BUY/SELL ranking.

Headroom/Codex setup:

- Installed `headroom-ai` in user-level venv `/home/iscjmz/.local/share/headroom-venv`.
- Symlinked CLI at `/home/iscjmz/.local/bin/headroom`; version `0.22.4`.
- Ran `headroom init --global --memory codex`; `codex mcp list` now shows `headroom` enabled.
- Headroom can reduce future Codex token usage only after Codex is restarted or launched through the Headroom integration. It cannot retroactively lower the current weekly usage already spent in this running session.

## Session Update - 2026-06-03 Seller Hub Strict Identity Filtering + Finder Score

Improved Seller Hub Product Research so broad eBay Research pages do not poison Finder metrics.

What changed:

- `Pokemon/services/api-consumer/services/seller_hub_research.py` now filters parsed Seller Hub rows by strict identity before computing metrics.
- Seller Hub metrics are now derived from matched rows first, not page-level averages, when row prices exist.
- The parser enforces:
  - meaningful card-name tokens,
  - set-name tokens when available,
  - exact card number or compatible fraction matching,
  - slab tier matching.
- If `card_number` is not passed separately, the parser infers it from card names like `Charizard [1st Edition] #4`.
- `build_keywords(...)` no longer duplicates a card number that already appears in the card name.
- Added Seller Hub regression tests for conflicting fractions and inferred card numbers.
- `Pokemon/server/store/slab_opportunity_store.go` now adjusts Finder response scores using Seller Hub metrics:
  - active/sold metrics can raise `liquidityScore`, `confidenceScore`, and `dealScore`,
  - active/sold metrics reduce `riskScore` when present.

Live proof:

- Exact authenticated Seller Hub research for `Charizard [1st Edition] #4`, set `Base`, card number `4`, tier `PSA_10` persisted 4 strict rows instead of the earlier broad 21-row mixed result.
- The strict row set produced: 4 active listings, `$1,342,500.00` average listing price, 1,052 average watchers, and 3,319 max watchers.
- Protected Finder API returned the strict Seller Hub metrics and adjusted scores: liquidity `72`, confidence `82`, risk `3`, deal score `300`.

Verified:

- `venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` passed with 36 api-consumer tests.
- `go test ./...` passed in `Pokemon/server`.
- `npm run build` passed in `Pokemon/client`.
- Go API health passed.
- api-consumer health passed and RabbitMQ connected.

Operational note:

- Seller Hub browser research is working with authenticated Product Research.
- Regular eBay Browse API is currently reaching production `https://api.ebay.com/...` but returns OAuth `401 Unauthorized` with the credentials available to the local api-consumer process. Fixing that requires valid production eBay Browse API client credentials or reverting to a valid sandbox app for sandbox-only tests. Do not commit credentials.

## Session Update - 2026-06-03 eBay Browse 401 Fallback Hardening

- Fixed a slab scanning reliability bug in `Pokemon/services/api-consumer/services/ebay_service.py`: when eBay Browse API auth/network fails, slab scans now still call the public eBay/Scrapling active-listing fallback instead of returning zero listings.
- Added regression coverage in `Pokemon/services/api-consumer/tests/test_ebay_service_matching.py` for a Browse API `401 Unauthorized` path returning a real slab from the fallback scraper.
- Fixed local env resolution in `Pokemon/services/api-consumer/repositories/ebay_repo.py`: service-local commands now load both `services/api-consumer/.env` and the parent `Pokemon/.env` with `override=False`, so app-level `EBAY_SANDBOX_MODE=false` applies when no service-local override exists.
- Live proof after the fix: a production-mode `Spinda` / `EX Legend Maker` / `#26` / `PSA_7` scan returned `2006 POKEMON EX LEGEND MAKER #26 SPINDA-REVERSE FOIL PSA 7` at `$125.00`.
- Current meaning of the eBay caveat: invalid/revoked Browse API credentials can still prevent official Browse API calls, but slab scans no longer go blank because the free public eBay fallback remains active. Seller Hub Product Research remains the richer source for watchers/bids/active-sold metrics.
- Headroom status: `codex mcp list` shows `headroom` enabled, and `headroom memory stats` works. It has zero current memories because this Codex session is not running through `headroom wrap codex`; restart/wrap Codex for future token savings.
- Root workspace verification note: root `package.json` declares `pnpm@10` and Node `>=20`, but this shell currently has Node `18.20.8` and no `pnpm`, so root `pnpm` verification is environment-blocked until Node/pnpm are installed or enabled.

Verification run:

```text
cd Pokemon/services/api-consumer && venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v  # 37 tests passed
cd Pokemon/server && go test ./...                                                               # passed
cd Pokemon/client && npm run build                                                               # passed
```

## 2026-06-05 Agent Ops And Commerce Direction Update

- Added `docs/PROJECT_INFRASTRUCTURE.md` as the current infrastructure map for PokemonTool, Odoo, Seller Hub automation, vendor insight scoring, alerts, and run commands.
- Added `docs/AGENT_OPS_HERMES_LAST30DAYS.md` to document how Hermes Agent and `last30days` should be used for this project.
- Installed `last30days` globally for this user at `~/.agents/skills/last30days` and added `Pokemon/scripts/run_last30days_vendor_pulse.sh` as the project wrapper.
- The `last30days` wrapper is an intelligence/reporting input only. It saves market-pulse reports under `Pokemon/reports/last30days/` and should feed suggested watchlist additions, demand/risk explanations, listing copy, and vendor product strategy. It must not override eBay sold evidence, Seller Hub metrics, exact card/slab matching, or margin math.
- Current no-key `last30days` sources are Reddit, Hacker News, and Polymarket. YouTube requires `yt-dlp`; GitHub requires `gh` auth or `GITHUB_TOKEN`; broader web/social sources require optional API keys such as `BRAVE_API_KEY`, `EXA_API_KEY`, `SCRAPECREATORS_API_KEY`, or `XAI_API_KEY`.
- Hermes Agent is recommended as a future ops copilot for scheduled reports, Telegram/Slack access, market-pulse automation, and incident triage. It should not be installed into the production request path or granted broad write access to eBay, Odoo, Shopify, or production data without scoped approvals.
- Odoo currently receives PokemonTool output through the product/inventory sync path. Odoo shows synced products and Pokemon metadata, but it does not yet expose a native live Go-backend intelligence dashboard. A future Odoo product tab could show Finder action, Seller Hub snapshot age, sold evidence, watcher/bid metrics, margin, and a link back to PokemonTool.
- The Pokemon engine can be generalized beyond cards as: product catalog -> marketplace comps -> demand signals -> margin math -> sourcing alerts -> storefront sync. Pokemon remains the strongest current niche because collectibles have exact identity, sold comps, and emotional demand, but the same infrastructure can support other resale, affiliate, or dropshipping categories after replacing Pokemon-specific schemas and sources.

## 2026-06-06 Repo Optimization And Directory Ownership Update

- Added `docs/DIRECTORY_INFRASTRUCTURE.md` as the directory-by-directory ownership map for root NexusOS/Shopify, PokemonTool, Odoo, generated artifacts, and vendor/reference areas.
- Confirmed `apps/web` is not part of the active Pokemon/Odoo runtime, but it is still wired to `docker-compose.dev.yml` as the NexusOS/Shopify frontend. Do not delete it unless the whole NexusOS/Shopify track is intentionally retired.
- Confirmed root `docker-compose.yml` is the NexusOS infrastructure stack, while `docker-compose.dev.yml` adds root `web`, `gateway`, and `ai` app services. The active Pokemon/Odoo work uses `Pokemon/docker-compose.yml` plus `docker-compose.odoo.yml`.
- Reviewed the root `Makefile`; the current checked-in version is scoped to the NexusOS/Shopify stack and no longer carries the stale Pokemon alias block that earlier local notes referenced.

