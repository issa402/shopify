# Card-Store Product Strategy

Last updated: 2026-06-18

## Product Boundary

The active product is not NexusOS. The active product is a Pokemon card vendor operating system connected to an Odoo storefront.

```text
PokemonTool = card intelligence, sourcing, pricing, watchlists, alerts, inventory decisions
PokeTCG     = exact Pokemon card identity and market lookup support
Odoo        = storefront, product catalog, orders, customers, inventory ops, invoicing, ERP
Hermes      = optional read-only ops copilot and scheduled reporting
NexusOS     = optional broader Shopify automation platform, not required for the card store
```


## Operating Rule

Default to the smallest stack that proves the feature:

```text
Card pricing, sourcing, alerts, inventory, storefront sync -> scripts/dev-cardstore.sh
Cross-shop Shopify automation, Nexus AI routes, Kafka/Temporal workflows -> scripts/dev-universe.sh
Browser marketplace scraping experiments -> scripts/dev-cardstore.sh scraping-up
```

A new service should not be default-on unless the card-store product fails without it. Heavy or brittle systems such as browser scraping, local LLM serving, and workflow engines should stay opt-in until they are required for a specific workflow.

## What Belongs In PokemonTool

- Exact card/set/number/grade/language matching.
- eBay Browse API active listing ingestion.
- Seller Hub Product Research snapshots.
- Watchlists, alerts, vendor opportunity scoring, and Finder decisions.
- Inventory source of truth before a product is approved for sale.
- Data freshness metrics for listings, alerts, deals, price history, cards, and research snapshots.
- Odoo sync decisions: `READY`, `SYNCED`, `NEEDS_REPRICE`, `NEEDS_RESEARCH`, `DO_NOT_LIST`.

## What Belongs In Odoo

- Public storefront and product pages.
- Cart, checkout, customers, orders, invoices, refunds, and fulfillment.
- Published sellable product catalog.
- ERP back-office views for product metadata, margins, stock, and accounting.
- Storefront search/filter UX over already-approved inventory.

## What Not To Do

- Do not put NexusOS in the required path for the card store.
- Do not make Facebook/Mercari browser scraping required for local startup or core pricing evidence.
- Do not let social buzz override sold comps, Seller Hub evidence, exact matching, or margin math.
- Do not grant Hermes write access to Odoo/eBay/Shopify until read-only reports are stable.

## Highest-Leverage Roadmap

### P0: Make The Store Trustworthy

1. Fix data freshness for `price_history` and `deals` so `/metrics` is not critical.
2. Add a visible freshness state in the dashboard: fresh, stale, critical.
3. Add an Odoo sync report: ready, synced, failed, stale, needs reprice.
4. Make Odoo product sync idempotent and observable: every sync should produce a count and error report.
5. Keep browser scraping opt-in; rely on eBay Browse API and Seller Hub evidence first.

### P1: Make The Vendor Workflow Excellent

1. One-click path: watchlist target -> evidence -> alert -> approve -> inventory -> Odoo product.
2. Repricing lane: products where current market is below/above store price by threshold.
3. Margin guardrails: acquisition cost, marketplace fees, shipping, target margin, recommended list price.
4. Slab workflow: grader, grade, cert, sold comps, active comps, liquidity signal.
5. Storefront filters: raw/slab/sealed, set, grade, condition, price range.

### P2: Make It Defensible

1. Seller Hub ACTIVE/SOLD snapshots as primary evidence layer.
2. Historical opportunity ledger: why the system recommended source/watch/avoid at the time.
3. Vendor intelligence brief: weekly demand shifts from last30days + eBay/Seller Hub data.
4. Competitor price monitoring for matching products.
5. Hermes read-only daily ops report for health, freshness, sync failures, and new opportunities.

## Security And Ops Requirements

- Keep Odoo, eBay, Shopify, and database credentials in env files only.
- Do not store browser cookies or Seller Hub session data in Postgres.
- Move JWT persistence away from `localStorage` before real production; use httpOnly cookies or short-lived access tokens with refresh protection.
- Replace URL-query SSE JWTs with short-lived stream tokens before public launch.
- Keep frontend security headers enabled in `Pokemon/client/nginx.conf`.
- Add E2E coverage once local Playwright/Chrome is installed.

## Current Verified Local Command

```bash
cd /home/iscjmz/shopify/shopify
scripts/dev-cardstore.sh up
scripts/dev-cardstore.sh health
```

Current default local URLs:

```text
Odoo storefront:   http://127.0.0.1:8069/pokecard-store
Pokemon dashboard: http://127.0.0.1:5173
Pokemon API:       http://127.0.0.1:3001
PokeTCG:           http://127.0.0.1:8765
```
