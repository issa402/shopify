# PokemonTool Project Infrastructure

Last updated: 2026-06-05

## Scope

This document describes the infrastructure for the PokemonTool app under `Pokemon/` and its connected Odoo storefront. The root repo also contains NexusOS/Shopify work, but the active card-vendor product is the PokemonTool stack.

## Product Loop

```text
Exact Pokemon card identity
  -> market data and active marketplace observations
  -> recent social and seller demand signals
  -> card/slab matching and valuation
  -> Finder vendor decision engine
  -> alerts and human approval
  -> inventory
  -> Odoo storefront product sync
```

The app should not behave like a generic card search page. It should identify exact card + set + grade opportunities and explain whether a vendor should source, watch, reprice, refresh research, or avoid.

## Agent Ops And Market Pulse

The repo now has an agent-ops runbook at `docs/AGENT_OPS_HERMES_LAST30DAYS.md`.

`last30days` is installed globally for this user at `~/.agents/skills/last30days` and is integrated as a market-intelligence input, not as an automatic pricing authority. The project wrapper is:

```bash
cd /home/iscjmz/shopify/shopify/Pokemon
scripts/run_last30days_vendor_pulse.sh
```

It writes reports under `Pokemon/reports/last30days/`. Current no-key sources are Reddit, Hacker News, and Polymarket. YouTube can be added with `yt-dlp`; GitHub can be added with `gh auth login` or `GITHUB_TOKEN`; broader web/social sources need optional API keys such as `BRAVE_API_KEY`, `EXA_API_KEY`, `SCRAPECREATORS_API_KEY`, or `XAI_API_KEY`.

Use the pulse output to propose watchlist additions, explain demand/risk, and improve vendor-facing copy. Do not let social buzz override sold comps, Seller Hub evidence, margin math, or exact card/slab matching.

Hermes Agent is recommended only as an ops copilot layer for scheduled reports, Telegram/Slack operator access, and incident triage. Do not put Hermes in the app request path or give it broad write access to Odoo, eBay, Shopify, or production data without narrow approval boundaries.

## Runtime Stacks

### PokemonTool Docker Stack

Main file: `Pokemon/docker-compose.yml`
Local override: `Pokemon/docker-compose.local-no-postgres-port.yml`

Services:

- `postgres`: primary PokemonTool database. Host access is bound to `127.0.0.1:55433` for local tools.
- `redis`: cache and supporting runtime state.
- `rabbitmq`: listing and alert event queue.
- `server`: Go API on `http://127.0.0.1:3001`.
- `client`: React/Vite dashboard served on `http://127.0.0.1:5173`.
- `api-consumer`: Python marketplace ingestion, eBay Browse API, Seller Hub tooling, live slab research.
- `scraping-service`: Go scraping worker for marketplace collection paths.
- `analytics-engine`: Python trend/deal analytics.
- `poketcg`: local exact Pokemon card and market search service on `http://127.0.0.1:8765`.
- `prometheus`, `grafana`, `loki`, `promtail`: observability.

Key local URLs:

```text
Pokemon dashboard: http://127.0.0.1:5173
Pokemon API:       http://127.0.0.1:3001
PokeTCG:           http://127.0.0.1:8765
RabbitMQ UI:       http://127.0.0.1:15672
Grafana:           http://127.0.0.1:3000
Prometheus:        http://127.0.0.1:9090
```

### Odoo Stack

Main file: `docker-compose.odoo.yml`

Services:

- `shopify-odoo`: Odoo Community storefront and ERP.
- Odoo Postgres service from the Odoo compose stack.
- Custom addon: `odoo/custom_addons/pokecard_storefront`.

Key local URLs:

```text
Odoo storefront: http://127.0.0.1:8069/pokecard-store
Odoo login:      http://127.0.0.1:8069/web/login?db=pokecard_store
```

PokemonTool and Odoo share the external Docker network `pokemon-odoo-bridge`. The Pokemon Go API calls Odoo at `http://shopify-odoo:8069` from inside Docker.

## Database Ownership

PokemonTool Postgres is the source of truth for:

- users
- watchlists
- alerts
- inventory
- price history
- card listings
- slab opportunities
- Seller Hub research snapshots

Important migrations:

- `001_init.sql`: users, watchlists, alerts, inventory, base schema.
- `003_watchlist_market_metadata.sql`: exact card market metadata.
- `005_watchlist_slab_metadata.sql`: raw/slab watchlist lanes.
- `006_alert_listing_dedupe.sql`: alert dedupe by user, marketplace, and listing id.
- `007_card_listing_slab_snapshots.sql`: active listing observations with slab metadata.
- `011_slab_wholesale_opportunities.sql`: slab opportunity table and inventory slab fields.
- `014_seller_hub_research_metrics.sql`: authenticated Seller Hub Product Research snapshots.
- `015_seller_hub_metric_helpers.sql`: latest Seller Hub snapshot helper functions.
- `016_expand_card_listing_condition.sql`: expands listing condition storage for long eBay condition strings.

## Data Flow

### Watchlist Alerts

```text
React Watchlist UI
  -> Go API /api/watchlist
  -> Postgres watchlists
  -> api-consumer reads /api/internal/watchlist-targets
  -> eBay/PokeTCG scanning
  -> RabbitMQ listing messages
  -> Go notification worker
  -> Postgres alerts
  -> SSE + Alerts UI
```

The worker deduplicates alerts by `(user_id, marketplace, listing_id)`.

### Finder / Slab Opportunities

```text
PriceCharting movers + configured targets
  -> live slab research
  -> exact eBay active listing scan
  -> strict card/set/grade filtering
  -> slab_opportunities rows
  -> Go API attaches Seller Hub snapshots
  -> vendor insight scoring
  -> Finder UI
```

Finder is card-and-grade-specific. Generic research targets are kept as research rows, but they cannot be approved as exact buys until an exact listing exists.

### Seller Hub Product Research

Authenticated Seller Hub research is host-side because the login session belongs to the local browser profile, not a Docker container.

Files:

- `services/api-consumer/services/seller_hub_research.py`: browser research collector.
- `services/api-consumer/seller_hub_research.py`: one-card CLI.
- `services/api-consumer/seller_hub_research_batch.py`: automated batch collector for Finder targets.
- `scripts/run_seller_hub_research.sh`: manual one-card runner.
- `scripts/run_seller_hub_automation.sh`: batch runner.
- `deploy/systemd/pokemon-seller-hub-research.service`: persistent user-level automation.

Persistent service:

```bash
systemctl --user status pokemon-seller-hub-research.service
```

Current service behavior:

```text
Every 240 minutes:
  -> load up to 100 exact eBay Finder card+grade targets
  -> research ACTIVE and SOLD tabs in Seller Hub
  -> persist Seller Hub snapshots
  -> create targeted vendor opportunity alerts when strict evidence gates pass
```

Target selection is generic. It is not hardcoded to Charizard. The SQL selects any row in `slab_opportunities` where:

- `marketplace = 'ebay'`
- `listing_id IS NOT NULL`
- `asking_price > 0`
- `decision IN ('candidate', 'watch')`
- `slab_tier IS NOT NULL`

Then it groups by `card_name` and `slab_tier`, orders by best current opportunity score/update time, and researches those exact card+grade targets.

This covers all current exact Finder targets up to the configured batch cap. It does not scan every Pokemon card in existence unless those cards first enter the app through watchlists, configured targets, PriceCharting movers, or live Finder ingestion.

## Vendor Decision Engine

Core file: `server/store/vendor_insight.go`

Each Finder row gets `vendorInsight`:

- `action`
- `actionReason`
- `opportunityScore`
- `demandScore`
- `priceScore`
- `evidenceScore`
- `sellThroughRate`
- `priceEdgePct`
- `targetListPrice`
- `benchmarkSource`
- `sellerHubStale`
- `hasExactListing`
- `hasActiveResearch`
- `hasSoldResearch`

Actions:

- `SOURCE_NOW`: exact listing, strong economics, fresh meaningful sold evidence.
- `CONSIDER_BUY`: exact listing with upside but not enough evidence for urgent sourcing.
- `FIND_EXACT_LISTING`: market research exists but no exact purchasable listing is attached.
- `REFRESH_RESEARCH`: economics look good but Seller Hub evidence is stale.
- `WATCH`: not actionable yet.
- `AVOID`: listing is overpriced or negative after costs.

Important guardrail: missing or empty SOLD research caps the score below the source-now tier. A blank sold snapshot cannot produce a `SOURCE_NOW` recommendation.

## Vendor Opportunity Alerts

Core file: `services/api-consumer/services/vendor_opportunity_alerts.py`

After each Seller Hub batch cycle, the automation creates `VENDOR_OPPORTUNITY` alerts only when:

- a user already watches the exact card name
- the opportunity is an exact eBay listing
- expected profit is positive
- expected margin is at least 20%
- Seller Hub SOLD evidence is meaningful

Alerts are deduped by the existing alert unique index on `(user_id, marketplace, listing_id)`.

## Odoo Integration

Pokemon register/login syncs user credentials into Odoo so the same email/password can access the store account.

Inventory-to-store flow:

```text
Pokemon inventory row
  -> POST /api/inventory/{id}/store-listing
  -> Go Odoo syncer
  -> Odoo product.template with pokemon_inventory_id
  -> /pokecard-store renders live synced products
```

Odoo product sync uses `pokemon_inventory_id` as the stable key.

## Operational Commands

Start Pokemon stack:

```bash
cd /home/iscjmz/shopify/shopify/Pokemon
docker compose -f docker-compose.yml -f docker-compose.local-no-postgres-port.yml up -d
```

Check services:

```bash
docker compose -f docker-compose.yml -f docker-compose.local-no-postgres-port.yml ps --all
curl http://127.0.0.1:3001/health
curl http://127.0.0.1:5173/finder
```

Check Odoo:

```bash
curl http://127.0.0.1:8069/pokecard-store
```

Run manual Seller Hub research:

```bash
cd /home/iscjmz/shopify/shopify/Pokemon
./scripts/run_seller_hub_research.sh login
./scripts/run_seller_hub_research.sh run --card-name "Radiant Charizard" --external-card-id pgo-11 --set-name "Pokemon GO" --card-number 11 --slab-tier PSA_10 --tab ACTIVE --persist
```

Run one batch manually:

```bash
./scripts/run_seller_hub_automation.sh --limit 100 --tabs ACTIVE,SOLD
```

Manage persistent Seller Hub automation:

```bash
systemctl --user status pokemon-seller-hub-research.service
systemctl --user restart pokemon-seller-hub-research.service
journalctl --user -u pokemon-seller-hub-research.service -f
```

Run verification:

```bash
cd /home/iscjmz/shopify/shopify/Pokemon/server
go test ./...

cd /home/iscjmz/shopify/shopify/Pokemon/client
npm run build

cd /home/iscjmz/shopify/shopify/Pokemon/services/api-consumer
venv/bin/python -m unittest tests.test_vendor_opportunity_alerts tests.test_seller_hub_batch tests.test_seller_hub_batch_retry tests.test_seller_hub_research tests.test_live_slab_research tests.test_live_slab_opportunity_repo -v
```

## Current Limits And Product Truth

- Seller Hub automation covers all exact Finder targets up to the service cap, currently 100 unique card+grade targets per cycle.
- It does not magically cover every Pokemon card ever printed. A card must enter the system through watchlist, target config, PriceCharting mover ingestion, or a live Finder row.
- eBay Seller Hub data requires the local authenticated browser profile. Passwords are not stored by the app.
- Public eBay Browse API and authenticated Seller Hub are separate data sources.
- Sold evidence is treated as stronger pricing evidence than active asks.
- Empty Seller Hub results lower confidence; they do not prove demand is zero.
- Human approval is still required before inventory is created or listed.
