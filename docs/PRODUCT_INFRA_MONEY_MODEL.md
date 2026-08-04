# Product, Infrastructure, And Money Model

This is the short master explanation of what this project is, how the infrastructure fits together, and how it can make money.

## One-Sentence Product

PokemonTool helps card sellers find underpriced Pokemon cards and slabs, decide what to buy or sell, track inventory profit, and push approved inventory into a real store backend.

## The Customer

The strongest customer is not a casual collector. The strongest customer is:

- a local card shop
- a card show vendor
- an eBay/Whatnot/Shopify/Odoo seller
- a serious flipper buying raw cards, graded slabs, and sealed product

They care about speed, profit, and not buying bad inventory.

## The Pain

A card seller has to manually answer these questions every day:

- Is this exact card variant worth buying?
- Is this PSA 10 / CGC 9.5 / BGS 10 slab actually below market?
- Are recent sold comps strong enough or is the market stale?
- What is my all-in cost after shipping, tax, fees, and platform spread?
- What price should I list at to hit my target margin?
- What inventory do I own, what did I pay, and what is it worth now?
- Which cards should I sell, hold, reprice, or source?

The software makes money if it helps sellers make or save more money than the subscription costs.

## Product Loop

```text
market data + marketplace listings
  -> exact card/slab matching
  -> valuation and opportunity scoring
  -> seller approves buy/sell decision
  -> inventory row is created
  -> product syncs to store backend
  -> order/sale updates inventory and margin history
```

## Main Systems

### PokemonTool

PokemonTool is the intelligence engine.

It handles:

- exact Pokemon card search
- market price context
- watchlists
- alerts
- slab parsing
- sold-comp valuation
- wholesale slab opportunity scoring
- inventory cost basis and P&L
- buy/sell/reprice recommendations

Important local paths:

- `Pokemon/server`: Go API
- `Pokemon/client`: React dashboard
- `Pokemon/services/api-consumer`: marketplace/listing ingestion
- `Pokemon/services/analytics-engine`: valuation, trends, deals, slab scoring
- `Pokemon/database/migrations`: Postgres schema

### Odoo

Odoo is the free ERP/store backend.

It handles:

- products
- inventory/stock
- CRM
- sales orders
- eCommerce storefront
- customers
- invoicing/back office

Important local paths:

- `odoo/custom_addons/pokecard_storefront`: custom Odoo addon
- `odoo/custom_addons/pokecard_storefront/scripts/sync_pokemon_inventory_to_odoo.py`: Pokemon inventory to Odoo product sync
- `docker-compose.odoo.yml`: local Odoo runtime

### Shopify / NexusOS

Shopify/NexusOS is another possible commerce/backend track.

The documented strategy is:

```text
PokemonTool = market intelligence
Shopify/Odoo = commerce backend
```

Do not mix all systems randomly. Pick one selling backend per workflow.

## How It Makes Money

### 1. Seller SaaS Subscription

Charge card sellers monthly for:

- market-backed inventory
- under-market alerts
- wholesale slab finder
- sell/hold/reprice suggestions
- inventory P&L
- Odoo/Shopify product sync
- stale-data warnings

Possible pricing:

- Starter: $29-$49/month for solo sellers
- Pro: $99-$199/month for serious vendors
- Shop: $299+/month for local shops with team/workflows

### 2. Deal Finder / Sourcing Product

The highest-value wedge is the wholesale slab finder.

It ranks slabs by:

- all-in cost
- estimated market value from sold comps
- expected profit
- expected margin percent
- liquidity
- confidence
- risk

If the tool helps a seller find one extra profitable slab flip per month, it can justify the subscription.

### 3. Store Backend / Managed Commerce

Use Odoo or Shopify to run the seller's actual inventory and storefront.

Money paths:

- setup fee for sellers
- monthly managed store fee
- optional percentage of sales if you become a managed service
- premium automation for listing/repricing

### 4. Data / Intelligence Reports

Once data quality is strong:

- weekly slab market report
- underpriced card report
- local shop buying guide
- show/vendor sourcing report

This only works after data is reliable.

## Where Scrapling Fits

Scrapling is not the product. Scrapling is a data acquisition tool.

It can help with:

- crawling public marketplace pages
- extracting active listings
- extracting sold comps where allowed
- handling dynamic pages
- surviving minor page layout changes with adaptive selectors
- running long crawls with pause/resume
- streaming scraped items into pipelines

Best fit in this repo:

```text
Scrapling spider
  -> active listings / sold comps
  -> Pokemon card/slab parser
  -> Postgres card_listings or slab_comps
  -> analytics scorer
  -> Slab Finder UI
```

Do not treat Scrapling as permission to scrape everything. Use official APIs when available, respect terms/rate limits, and keep credentials in environment variables.

## Current Infra Shape

PokemonTool local stack includes:

- Postgres: source of truth
- Redis: cache
- RabbitMQ: listing/alert event queue
- Go API: user-facing backend
- React client: dashboard
- Python api-consumer: marketplace ingestion
- Python analytics-engine: trends/deals/slab scoring
- PokeTCG service: exact card/market search
- Grafana/Loki/Prometheus: observability

Odoo local stack includes:

- Odoo 19 Community
- Odoo Postgres
- custom Pokemon storefront addon
- product fields for Pokemon metadata
- sync script from Pokemon inventory to Odoo products

## What Is Built Now

Built/started:

- exact-card watchlists
- PokeTCG-backed card search
- inventory with market metadata
- raw/slab watchlist lanes
- slab parser
- card listing snapshots
- slab summary endpoint
- alert dedupe
- Odoo storefront starter
- Odoo CRM/Sales/Inventory/eCommerce install
- Pokemon product fields in Odoo
- Pokemon inventory to Odoo product sync bridge
- wholesale slab opportunity schema
- slab valuation/scoring engine
- Slab Finder API and UI

## What Is Not Done Yet

Still needed before this is money-ready:

- reliable sold-comp ingestion into `slab_comps`
- reliable active listing ingestion into `card_listings`
- browser/UI QA for the new Slab Finder page
- real seller onboarding and auth hardening
- production deployment plan
- backups and restore drills
- payment/subscription billing
- real store checkout/payment/shipping configuration
- legal/rate-limit review for scraping/data sources
- real users testing whether alerts/opportunities make money

## The Best Next Build

Build a Scrapling-backed sold-comps ingestion service.

MVP:

```text
input: list of cards/slab tiers to monitor
crawl: public sold-comps source or allowed marketplace endpoint
parse: card, set, grader, grade, sold price, sold date, URL
store: slab_comps
score: run slab_opportunity_finder
show: Slab Finder page
approve: create inventory row
sync: Odoo product
```

That is the bridge between infrastructure and revenue.

## Rule For Future Agents

Before changing architecture, read:

1. `AGENTS.md`
2. `docs/PROJECT_HANDOFF.md`
3. `docs/PRODUCT_INFRA_MONEY_MODEL.md`
4. `docs/SHOPIFY_POKEMON_STRATEGY.md`
5. `odoo/README.md`
6. `docs/superpowers/plans/2026-05-30-wholesale-slab-ai.md`

## Scrapling Integration Status

Scrapling is now installed/included in the Python ingestion layer, not vendored as a full source checkout.

Why dependency instead of cloning the whole repo:

- smaller project surface
- easier upgrades through `requirements.txt`
- avoids committing third-party source into this repo
- keeps our code focused on Pokemon-specific ingestion and scoring

Installed path/use:

```text
Pokemon/services/api-consumer/requirements.txt
Pokemon/services/api-consumer/services/scrapling_sold_comps.py
Pokemon/services/api-consumer/repositories/slab_comp_repo.py
Pokemon/services/api-consumer/scrapling_sold_comps_ingest.py
```

The current integration is operator-run and source-configurable:

```text
approved source URL + CSS selectors
  -> Scrapling fetch
  -> parse sold comp title/price/date/link
  -> write `slab_comps`
  -> slab opportunity scorer ranks flips
```

This is the first practical bridge from web data to the money feature.
