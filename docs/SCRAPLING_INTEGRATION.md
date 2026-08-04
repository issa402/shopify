# Scrapling Integration

Scrapling is integrated as a dependency of `Pokemon/services/api-consumer`, not vendored as a full source checkout.

Verified source:

- GitHub: `D4Vinci/Scrapling`
- PyPI package: `scrapling`
- License: BSD-3-Clause
- Requires Python 3.10+

## Current Status

Scrapling is available and wired as a selector-based sold-comps extractor, but it is not the only eBay research path and should not be treated as the default live eBay integration.

Current marketplace research paths:

- eBay Browse API active listings: implemented in `services/api-consumer/services/ebay_service.py`; used by watchlist scans, live eBay lookups, and RabbitMQ alert publishing.
- Seller Hub Product Research: implemented in `services/api-consumer/services/seller_hub_research.py`; uses a local Playwright browser profile for authenticated ACTIVE/SOLD research metrics.
- Scrapling sold-comps ingestion: implemented in `services/api-consumer/services/scrapling_sold_comps.py`; useful for approved HTML pages with explicit selectors.

## Why We Use It

Scrapling is a data acquisition tool for the PokemonTool money loop:

```text
operator-approved sold-comps/listing pages
  -> Scrapling extractor
  -> slab_comps / card_listings
  -> slab valuation and opportunity scoring
  -> Slab Finder UI
  -> approved inventory
  -> Odoo product/store backend
```

It is useful because card-selling profit depends on fresh active listings and sold comps. Without data flowing into `slab_comps`, the Slab Finder has scoring logic but no price truth.

## What Was Added

Dependency:

```text
Pokemon/services/api-consumer/requirements.txt
scrapling[fetchers]==0.4.7
psycopg2-binary==2.9.9
```

Files:

```text
Pokemon/services/api-consumer/services/scrapling_sold_comps.py
Pokemon/services/api-consumer/repositories/slab_comp_repo.py
Pokemon/services/api-consumer/scrapling_sold_comps_ingest.py
```

## Run A Dry-Run

Use dry-run first. This prints parsed comps and does not write to Postgres.

```bash
cd Pokemon/services/api-consumer

python3 scrapling_sold_comps_ingest.py \
  --dry-run \
  --url 'https://example.com/sold-comps-page' \
  --marketplace 'example_sold' \
  --card-name 'Armored Mewtwo' \
  --set-name 'SM Promos' \
  --external-card-id 'smp-SM228' \
  --grader PSA \
  --grade 10 \
  --slab-tier PSA_10 \
  --row-selector '.sold-row' \
  --title-selector '.title::text' \
  --price-selector '.price::text' \
  --sold-at-selector '.sold-date::text' \
  --link-selector 'a'
```

Selectors are source-specific. For each source, inspect the page and tune:

- row selector
- title selector
- price selector
- sold date selector
- link selector

## Write To Postgres

Only after dry-run output looks correct:

```bash
POSTGRES_HOST=127.0.0.1 \
POSTGRES_PORT=5432 \
POSTGRES_DB=pokemontool \
POSTGRES_USER=pokemontool_user \
POSTGRES_PASSWORD=pokemontool_pass \
python3 scrapling_sold_comps_ingest.py \
  --url 'https://example.com/sold-comps-page' \
  --marketplace 'example_sold' \
  --card-name 'Armored Mewtwo' \
  --set-name 'SM Promos' \
  --external-card-id 'smp-SM228' \
  --grader PSA \
  --grade 10 \
  --slab-tier PSA_10 \
  --row-selector '.sold-row' \
  --title-selector '.title::text' \
  --price-selector '.price::text'
```

## What Scrapling Is And Is Not

Scrapling is a Python HTML extraction/fetching library. In this repo it takes an approved page URL plus CSS selectors and returns structured sold-comp rows. It is not an auto-browser shopping bot, not an auto-buy system, and not where eBay API credentials live.

For eBay specifically:

- Active listing search should use the eBay Browse API path first.
- Authenticated Seller Hub research should use the Playwright profile path.
- Scrapling should be used when an operator has approved a source page and selector config for sold comps.

## Guardrails

- Prefer official APIs when available.
- Respect site terms, robots.txt, and rate limits.
- Do not store marketplace credentials in git.
- Do not use Scrapling to auto-buy anything.
- Treat scraped data as evidence requiring validation, not guaranteed truth.
- LLMs may summarize messy listing titles, but sold-comp prices must come from parsed evidence.

## Next Build

Create source-specific selector configs for the first real sold-comp source and add a regression fixture so layout changes are caught before bad comps hit `slab_comps`.

## Batch Sold-Comp Loop

The app now supports a repeatable sold-comp ingestion loop. Keep source configs explicit and disabled until a source is approved and selectors are verified.

Example config:

```text
Pokemon/services/api-consumer/config/sold_comps.sources.example.json
```

Dry-run one batch locally:

```bash
cd Pokemon/services/api-consumer
PYTHONPATH=. python3 scrapling_sold_comps_batch.py \
  --dry-run \
  --config config/sold_comps.sources.example.json
```

Enable the background loop in `api-consumer` by setting environment variables:

```bash
SOLD_COMP_SOURCES_CONFIG=/app/config/sold_comps.sources.json
SOLD_COMP_INTERVAL_MINUTES=15
SOLD_COMP_DRY_RUN=false
```

After sold comps are inserted, the analytics engine re-scores active slab listings into `slab_opportunities`. For faster slab alerts in development or production, set:

```bash
SLAB_OPPORTUNITY_INTERVAL_MINUTES=5
```

The ranking now includes a trend score from recent sold comps when there is enough history. Recent comps stronger than older comps raise candidate ranking; weaker recent comps reduce it.

Operational loop:

```text
approved sold-comp source config
  -> Scrapling batch ingestion
  -> slab_comps
  -> analytics slab opportunity finder
  -> slab_opportunities
  -> Slab Finder UI / approve to inventory
```

Do not enable a source globally until its dry-run output has been checked and a regression fixture exists for that page shape.

## Live Slab Research Connector

The live research connector combines:

```text
PriceCharting big movers / grade prices
+ curated target configs
+ eBay Browse API active asks from Pokemon/.env credentials
+ strict identity matching
-> BUY_CANDIDATE or SELL_RESEARCH output
```

Files:

```text
Pokemon/services/api-consumer/services/pricecharting_market.py
Pokemon/services/api-consumer/services/live_slab_research.py
Pokemon/services/api-consumer/live_slab_research.py
Pokemon/services/api-consumer/config/live_slab_targets.example.json
```

Run with production buy thresholds:

```bash
cd Pokemon/services/api-consumer
PYTHONPATH=. python3 live_slab_research.py \
  --mover-limit 8 \
  --target-config config/live_slab_targets.example.json
```

Run with relaxed thresholds to inspect exact active listings even when they are not buys:

```bash
PYTHONPATH=. python3 live_slab_research.py \
  --mover-limit 8 \
  --min-profit -100000 \
  --min-margin-pct -100 \
  --target-config config/live_slab_targets.example.json
```

Current behavior verified on 2026-05-31:

- PriceCharting live fetch returned HTTP 200 for big movers and target card pages.
- eBay Browse API credentials loaded from `Pokemon/.env`.
- Strict matching rejects wrong-variant false positives such as Skyridge Charizard value matched to VMax Climax Charizard listings.
- Armored Mewtwo SM228 PSA 10 produced exact active eBay listings, but all were above the PriceCharting PSA 10 reference, so production buy thresholds returned zero `BUY_CANDIDATE` rows.
- Relaxed thresholds returned `SELL_RESEARCH` rows for those active asks.

This connector is useful for live research now. To turn it into automatic user alerts, persist its output into `slab_opportunities` or a dedicated research signal table after adding source/rate-limit controls.
