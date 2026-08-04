# Wholesale Slab AI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a PokemonTool feature that finds graded slab wholesale opportunities, estimates resale value, ranks flips by profit/risk/liquidity, and sends approved buys into Odoo inventory/products.

**Architecture:** Keep PokemonTool as the intelligence engine and Odoo as the commerce backend. Marketplace ingestion writes active and sold listing evidence into Postgres, the slab valuation engine computes comps and confidence, the opportunity scorer ranks potential flips, and approved opportunities sync into Odoo products/inventory.

**Tech Stack:** Go API, Python analytics engine, PostgreSQL, RabbitMQ, Odoo 19 XML-RPC bridge, React dashboard.

---

## Product Lens

**Specific user:** A Pokemon card seller/vendor who buys slabs below market and resells through their own Odoo storefront or at shows.

**Pain:** Manual slab sourcing is slow and error-prone. Sellers check active listings, sold comps, grade tiers, cert/title mismatches, fees, shipping, and liquidity by hand. Missing one cheap PSA 10 or buying one stale slab can cost real money.

**MVP proof:** For a tracked card/slab tier, show 10 candidate slab deals with estimated market value, all-in cost, expected profit, margin, confidence, and reason. Let the seller approve one candidate into Odoo inventory.

**Anti-goals:** Do not auto-buy. Do not rely on LLM vibes for valuation. Do not scrape marketplaces in ways that violate credentials, rate limits, or account safety. Do not push products into Odoo without human approval.

**Success metric:** A seller can find at least one credible buy candidate in under 5 minutes, with enough evidence to decide whether to buy.

## Existing Foundation

Already present:

- `Pokemon/services/api-consumer/services/slab_parser.py` parses graders, grades, tiers, and cert-like text.
- `watchlists` supports `RAW`, `SLAB`, and `ALL_SLABS` lanes.
- `card_listings` stores slab snapshot fields.
- `GET /api/cards/{id}/slab-summary` returns observed slab listings.
- `deals` table and `/api/deals/today` exist for simple below-market opportunities.
- Odoo now has Pokemon product metadata fields and a PokemonTool-to-Odoo sync script.

Missing:

- sold-comps table and ingestion path
- valuation engine by card/set/grader/grade/language
- liquidity and confidence scoring
- wholesale deal opportunity schema
- approval workflow
- Odoo handoff for approved opportunities
- UI for slab sourcing pipeline
- evals/regression tests for false positives

## Target Data Model

Create a new migration after current Pokemon migrations:

```sql
CREATE TABLE IF NOT EXISTS slab_comps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_card_id TEXT,
    card_name VARCHAR(255) NOT NULL,
    set_name VARCHAR(255),
    language_preference VARCHAR(20) DEFAULT 'ANY',
    grader VARCHAR(20) NOT NULL,
    grade VARCHAR(10) NOT NULL,
    slab_tier VARCHAR(50) NOT NULL,
    cert_number VARCHAR(100),
    marketplace VARCHAR(50) NOT NULL,
    sold_price DECIMAL(10, 2) NOT NULL,
    shipping_price DECIMAL(10, 2) DEFAULT 0,
    sold_at TIMESTAMPTZ NOT NULL,
    listing_url TEXT,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_slab_comps_identity
    ON slab_comps(external_card_id, slab_tier, language_preference, sold_at DESC);

CREATE TABLE IF NOT EXISTS slab_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_card_id TEXT,
    card_name VARCHAR(255) NOT NULL,
    set_name VARCHAR(255),
    grader VARCHAR(20),
    grade VARCHAR(10),
    slab_tier VARCHAR(50),
    marketplace VARCHAR(50),
    listing_id VARCHAR(255),
    listing_url TEXT,
    title TEXT,
    asking_price DECIMAL(10, 2) NOT NULL,
    shipping_price DECIMAL(10, 2) DEFAULT 0,
    estimated_fees DECIMAL(10, 2) DEFAULT 0,
    all_in_cost DECIMAL(10, 2) NOT NULL,
    estimated_market_value DECIMAL(10, 2) NOT NULL,
    expected_profit DECIMAL(10, 2) NOT NULL,
    expected_margin_pct DECIMAL(6, 2) NOT NULL,
    liquidity_score INTEGER NOT NULL,
    confidence_score INTEGER NOT NULL,
    risk_score INTEGER NOT NULL,
    deal_score INTEGER NOT NULL,
    decision VARCHAR(30) NOT NULL DEFAULT 'candidate',
    reason TEXT,
    evidence JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_slab_opportunities_listing
    ON slab_opportunities(marketplace, listing_id)
    WHERE listing_id IS NOT NULL;
```

## Scoring Model

```text
all_in_cost = asking_price + shipping_price + estimated_fees
expected_profit = estimated_market_value - all_in_cost
expected_margin_pct = expected_profit / all_in_cost * 100

deal_score =
  margin_score
+ liquidity_score
+ confidence_score
- risk_score
```

MVP thresholds:

- only show candidates with `expected_profit >= 25`
- only show candidates with `expected_margin_pct >= 20`
- require at least 3 sold comps for high confidence
- lower confidence when listing title/card identity is ambiguous
- lower confidence when slab tier is unknown
- lower confidence when comps are older than 90 days

## Task 1: Migration

**Files:**
- Create: `Pokemon/database/migrations/011_slab_wholesale_opportunities.sql`

- [x] Add `slab_comps` and `slab_opportunities` tables exactly as above.
- [x] Run migration against local Pokemon Postgres.
- [x] Verify slab tables and indexes exist in local Pokemon Postgres.

## Task 2: Valuation Engine

**Files:**
- Create: `Pokemon/services/analytics-engine/slab_valuation.py`
- Test: `Pokemon/services/analytics-engine/tests/test_slab_valuation.py`

- [x] Implement median sold comp value for same `external_card_id + slab_tier + language`.
- [x] Drop outlier comps outside 40%-250% of median.
- [x] Return market value, comp count, liquidity score, and confidence score.

## Task 3: Opportunity Scorer

**Files:**
- Create: `Pokemon/services/analytics-engine/slab_opportunity_scorer.py`
- Test: `Pokemon/services/analytics-engine/tests/test_slab_opportunity_scorer.py`

- [x] Convert active `card_listings` slab rows into opportunity candidates.
- [x] Compute all-in cost, expected profit, margin, risk, confidence, and deal score.
- [x] Reject obvious false positives: raw listings, unknown slab tier, no external card ID, missing price.

## Task 4: Go API

**Files:**
- Create: `Pokemon/server/models/slab_opportunity.go`
- Create: `Pokemon/server/store/slab_opportunity_store.go`
- Create: `Pokemon/server/services/slab_opportunity_service.go`
- Create: `Pokemon/server/handlers/slab_opportunity_handler.go`
- Modify: `Pokemon/server/routes/routes.go`

- [x] Add `GET /api/slab-opportunities` with filters: min margin, grader, grade, card name, decision.
- [x] Add `POST /api/slab-opportunities/{id}/approve` to mark an opportunity approved.
- [x] Add `POST /api/slab-opportunities/{id}/reject` to mark an opportunity rejected.

## Task 5: Odoo Handoff

**Files:**
- Modify: `odoo/custom_addons/pokecard_storefront/scripts/sync_pokemon_inventory_to_odoo.py`
- Create: `Pokemon/scripts/approved_slab_to_inventory.py`

- [x] Convert approved slab opportunity into PokemonTool inventory row.
- [x] Include grader, grade, cert, acquisition cost, market value, and target price.
- [x] Reuse the Odoo sync bridge to create/update the sellable Odoo product.

## Task 6: UI

**Files:**
- Create: `Pokemon/client/src/pages/SlabOpportunitiesPage.jsx`
- Modify: `Pokemon/client/src/App.jsx`

- [x] Show ranked slab opportunities with profit, margin, confidence, risk, and evidence.
- [x] Add approve/reject buttons.
- [x] Add filters for PSA 10, PSA 9, CGC 9.5, BGS 10, minimum margin, and marketplace.

## Task 7: Eval And Safety

**Files:**
- Create: `Pokemon/services/analytics-engine/tests/fixtures/slab_opportunities.json`
- Create: `Pokemon/services/analytics-engine/tests/test_slab_opportunity_regression.py`

- [x] Add known good deals and known bad false positives.
- [x] Verify scorer ranks true deals higher than false positives.
- [x] Verify no candidate is auto-approved.
- [x] Verify missing comp data lowers confidence instead of inventing a price.

## Production Notes

- Keep marketplace credentials in env vars only.
- Respect marketplace API terms and rate limits.
- Prefer official APIs and sold listing sources over brittle scraping.
- Log every AI/LLM-assisted interpretation with original title/listing evidence.
- LLM use is allowed for messy title interpretation and explanation, not as the source of price truth.
- Human approval is required before buying or pushing a product to Odoo sale inventory.
