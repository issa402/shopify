# Directory Infrastructure Map

Last updated: 2026-06-18

This repo has three product tracks. The active customer-facing work is PokemonTool plus Odoo. The root NexusOS/Shopify stack is also runnable in the full local universe and should not be deleted piecemeal.

## Decision Summary

- Keep `Pokemon/`: active PokemonTool product and main app stack.
- Keep `odoo/` and `docker-compose.odoo.yml`: active Odoo storefront/ERP bridge.
- Keep `apps/web`, `services/gateway`, `services/ai`, `docker-compose.yml`, `docker-compose.dev.yml`, and `docker-compose.universe.yml`: NexusOS/Shopify track. It now runs beside PokemonTool and Odoo through `scripts/dev-universe.sh`. Delete only if we intentionally retire that entire track.
- Do not commit generated/browser/cache directories such as `.codex-browser-use/`, `.codex-venvs/`, `Pokemon/.local/`, `Pokemon/reports/`, `Pokemon/client/dist/`, or `__pycache__/`.

## Root Directories

| Directory | Status | Purpose | Keep/Delete | Notes |
|---|---|---|---|---|
| `apps/web` | Dormant but wired | NexusOS/Shopify React/Vite frontend | Keep | Used by `docker-compose.dev.yml` as service `web`. Do not delete unless retiring NexusOS/Shopify. |
| `services/gateway` | Dormant but wired | NexusOS Go gateway, dashboard APIs, Shopify webhooks, Pokemon event intake | Keep | Backend paired with `apps/web`. |
| `services/ai` | Dormant but wired | NexusOS Python AI/FastAPI service, agent workflows, Shopify AI tools | Keep | Used by `docker-compose.dev.yml` as service `ai`. |
| `Pokemon` | Active | PokemonTool app submodule | Keep | Main Go API, React dashboard, Postgres schema, marketplace services. |
| `odoo` | Active | Project-owned Odoo config, custom addon, sync scripts | Keep | Odoo core stays in `vendor/odoo`; custom behavior lives here. |
| `PokeTCG` | Active support | Local Pokemon card identity/market-data service source | Keep | Supports exact PokemonTCG card lookup. |
| `docs` | Active documentation | Handoffs, infrastructure, strategy, runbooks | Keep | Update after architectural changes. |
| `config` | Dormant support | Temporal dynamic config for NexusOS root stack | Keep while NexusOS remains. |
| `schemas` | Support | Shared protocol/schema definitions | Keep | Review before deleting. |
| `scripts` | Support | Root-level orchestration, test, and agent scripts | Keep | `scripts/dev-cardstore.sh` is the default runner for Odoo + PokemonTool + PokeTCG. `scripts/dev-universe.sh` is the full Odoo + NexusOS + PokemonTool runner. |
| `infra` | Learning/reference | Infra lessons and practice scripts | Keep or archive later | Not runtime-critical. |
| `future_standard_mastery` | Learning/reference | Training docs and artifacts | Keep or archive later | Not runtime-critical. |
| `vendor/odoo` | Vendor/reference | Local ignored upstream Odoo source reference | Keep local, do not commit | Heavy third-party source, not project-owned. |
| `.agents`, `.codex-browser-use`, `.codex-venvs` | Local agent/tooling | Agent skills/browser-use/venvs | Do not commit | Local-only operational state. |
| `.github` | Active CI metadata | GitHub workflow/config surface | Keep | Check before branch/CI changes. |
| `.githooks` | Support | Git hook scripts | Keep | Local enforcement support. |

## Compose Files

| File | Status | Purpose | Notes |
|---|---|---|---|
| `docker-compose.yml` | NexusOS infra | Postgres, Redis, Qdrant, Kafka, Ollama, Temporal | Used underneath the NexusOS local universe path. Keep while NexusOS remains. |
| `docker-compose.dev.yml` | Active in full local universe | Adds NexusOS `web`, `gateway`, and `ai` app services | Used with `docker-compose.universe.yml` by `scripts/dev-universe.sh`. |
| `docker-compose.universe.yml` | Active local override | Assigns non-conflicting NexusOS host ports | Keeps NexusOS beside Pokemon/Odoo without port collisions. |
| `docker-compose.odoo.yml` | Active Odoo stack | Odoo Community plus Odoo Postgres | Shares `pokemon-odoo-bridge` with PokemonTool. |
| `Pokemon/docker-compose.yml` | Active Pokemon stack | PokemonTool Postgres, Redis, RabbitMQ, Go API, React client, consumers, analytics, scraping, PokeTCG, observability | Main product runtime. |
| `Pokemon/docker-compose.universe.yml` | Active local override | Assigns non-conflicting Pokemon host ports | Use this with full universe orchestration. |
| `Pokemon/docker-compose.local-no-postgres-port.yml` | Legacy/isolated local override | Keeps local Postgres host access for host-side tools | Prefer `Pokemon/docker-compose.universe.yml` when running all stacks together. |
| `Pokemon/docker-compose.selfhost.yml` | Support | Self-host/friend access deployment variant | Keep. |
| `Pokemon/docker-compose.prod.yml` | Support | Production deployment variant | Keep and verify before use. |

## Pokemon Submodule Directories

| Directory | Status | Purpose | Keep/Delete |
|---|---|---|---|
| `Pokemon/server` | Active | Go API, auth, routes, services, stores, workers | Keep |
| `Pokemon/client` | Active | React/Vite Pokemon dashboard. `dist/` is generated. | Keep |
| `Pokemon/database` | Active | Postgres migrations and seeds | Keep |
| `Pokemon/services/api-consumer` | Active | Python marketplace ingestion, eBay, Seller Hub, live slab research | Keep |
| `Pokemon/services/analytics-engine` | Active/support | Python trend/deal/valuation jobs | Keep |
| `Pokemon/services/scraping-service` | Active/support | Go scraping worker | Keep |
| `Pokemon/scripts` | Active ops | Health checks, Seller Hub runners, audits, market-pulse wrapper | Keep |
| `Pokemon/deploy/systemd` | Active ops | User-level Seller Hub automation service | Keep |
| `Pokemon/grafana` | Support | Observability provisioning | Keep |
| `Pokemon/.github` | Active CI | Pokemon submodule workflows | Keep |
| `Pokemon/backups` | Local data | Backup outputs | Do not commit new generated backups |
| `Pokemon/reports` | Generated reports | `last30days` market-pulse output | Do not commit generated reports |
| `Pokemon/.local` | Local browser/session state | eBay Seller Hub browser profile | Never commit |
| `Pokemon/.understand-anything` | Generated analysis graph | Understand Anything output | Do not commit unless intentionally publishing graph artifacts |

## Odoo Directories

| Directory | Status | Purpose | Keep/Delete |
|---|---|---|---|
| `odoo/config` | Active | Odoo config with custom addon path and DB filter | Keep |
| `odoo/custom_addons/pokecard_storefront` | Active | Custom Pokemon storefront/product metadata addon | Keep |
| `odoo/custom_addons/pokecard_storefront/controllers` | Active | `/pokecard-store` storefront routes | Keep |
| `odoo/custom_addons/pokecard_storefront/models` | Active | Odoo product metadata extensions | Keep |
| `odoo/custom_addons/pokecard_storefront/scripts` | Active | Pokemon inventory to Odoo sync bridge | Keep |
| `odoo/custom_addons/pokecard_storefront/static` | Active | Storefront CSS/assets | Keep |
| `odoo/custom_addons/pokecard_storefront/views` | Active | Odoo XML views/templates | Keep |
| `odoo/scripts` | Active ops | Odoo scaffold validation | Keep |

## Operating Rule

If the goal is Pokemon/Odoo only, archive the NexusOS/Shopify track as a coordinated removal: `apps/web`, `services/gateway`, `services/ai`, root NexusOS compose files, root Makefile targets, and corresponding docs. Do not delete only `apps/web`, because it is wired to the root gateway and dev compose stack.
