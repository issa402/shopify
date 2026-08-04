# Odoo Pokemon Inventory Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Odoo the sellable inventory, CRM, stock, and order backend while PokemonTool supplies exact-card identity, market value, and seller intelligence.

**Architecture:** Extend Odoo `product.template` with Pokemon card metadata that maps directly to PokemonTool inventory rows. Add a local XML-RPC sync script that reads Pokemon Postgres inventory and upserts Odoo products by Pokemon inventory ID or external card ID. Keep Odoo core untouched under `vendor/odoo`; all project behavior stays in `odoo/custom_addons/pokecard_storefront`.

**Tech Stack:** Odoo 19 Community, Python 3, XML-RPC, PostgreSQL/PokemonTool schema, Docker Compose.

---

## File Map

- `odoo/custom_addons/pokecard_storefront/models/product_template.py`: Pokemon-specific fields on Odoo products.
- `odoo/custom_addons/pokecard_storefront/models/__init__.py`: model import surface.
- `odoo/custom_addons/pokecard_storefront/__init__.py`: load controllers and models.
- `odoo/custom_addons/pokecard_storefront/views/product_template_views.xml`: product backend tab for Pokemon inventory metadata.
- `odoo/custom_addons/pokecard_storefront/scripts/sync_pokemon_inventory_to_odoo.py`: one-way sync from PokemonTool inventory to Odoo products.
- `odoo/README.md`: runbook for installed backend apps and sync command.
- `docs/PROJECT_HANDOFF.md`: handoff state after verification.

## Tasks

### Task 1: Add Pokemon fields to Odoo products

- [x] Add a model extension for `product.template` with card ID, set, number, condition, grade, market value, acquisition cost, margin, sync source, and last sync timestamp.
- [x] Add a backend product form tab so the fields are visible in Odoo.
- [x] Update the addon manifest to load the view and depend on sale/stock/CRM modules needed by the store backend.

### Task 2: Add Pokemon inventory sync script

- [x] Add a Python XML-RPC script that reads Pokemon Postgres inventory rows and upserts Odoo products.
- [x] Map Pokemon fields to Odoo product fields and publish products to the website.
- [x] Support dry-run mode so the sync can be previewed safely.

### Task 3: Verify locally

- [x] Compile Python files.
- [x] Validate Odoo compose/scaffold.
- [ ] Upgrade the running Odoo addon and install CRM/stock/sales support.
- [ ] Verify `/pokecard-store` still returns HTTP 200.
- [ ] Document final state in `docs/PROJECT_HANDOFF.md`.
