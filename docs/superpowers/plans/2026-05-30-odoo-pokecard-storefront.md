# Odoo PokeCard Storefront Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a free Odoo Community storefront starter inside the Shopify workspace for a high-value Pokemon card seller workflow.

**Architecture:** Keep upstream Odoo isolated in `vendor/odoo` and build project-owned Odoo config/custom addons under `odoo/`. Run Odoo with Docker Compose using the official Odoo 19 image, a private Postgres service, a custom addon mount, and local-only ports.

**Tech Stack:** Odoo 19 Community, PostgreSQL 15, Docker Compose, Odoo custom addon XML/Python/CSS, project documentation.

---

### Task 1: Project-Owned Runtime Scaffold

**Files:**
- Create: `docker-compose.odoo.yml`
- Create: `odoo/config/odoo.conf`
- Create: `odoo/.env.example`
- Create: `odoo/README.md`

- [x] **Step 1: Create Odoo compose file**

Use local-only Odoo/Postgres ports and mount custom addons from this repo.

- [x] **Step 2: Create Odoo config**

Define `addons_path` so `/mnt/extra-addons` loads project-owned modules.

- [x] **Step 3: Document startup path**

Write exact commands and explain that the first database is created through Odoo's web setup.

### Task 2: Storefront Addon

**Files:**
- Create: `odoo/custom_addons/pokecard_storefront/__manifest__.py`
- Create: `odoo/custom_addons/pokecard_storefront/__init__.py`
- Create: `odoo/custom_addons/pokecard_storefront/controllers/__init__.py`
- Create: `odoo/custom_addons/pokecard_storefront/controllers/main.py`
- Create: `odoo/custom_addons/pokecard_storefront/views/website_pages.xml`
- Create: `odoo/custom_addons/pokecard_storefront/static/src/css/pokecard_storefront.css`

- [x] **Step 1: Define module metadata**

Depend on Odoo website/eCommerce modules so the store can sell products.

- [x] **Step 2: Add high-value landing page**

Create a storefront page focused on graded cards, sealed product, live market intelligence, seller trust, and concierge sourcing.

- [x] **Step 3: Add route redirect**

Expose `/pokecard-store` as a clean storefront URL.

### Task 3: Validation And Handoff

**Files:**
- Create: `odoo/scripts/validate_odoo_scaffold.sh`
- Modify: `docs/PROJECT_HANDOFF.md`

- [x] **Step 1: Add local scaffold validation**

Check compose syntax and required addon files without starting services.

- [x] **Step 2: Update project handoff**

Record where Odoo lives, how to start it, and what remains.
