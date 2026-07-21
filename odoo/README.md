# Odoo Storefront Starter

This folder contains project-owned Odoo configuration and custom addons for a free Odoo Community storefront. The upstream Odoo source checkout is intentionally isolated at `vendor/odoo` and ignored by the parent repo.

## What This Builds

A local Odoo 19 Community stack for a Pokemon card seller storefront:

- Odoo eCommerce and website on `http://127.0.0.1:8069`
- private Odoo Postgres on host port `55432`
- project custom addons mounted from `odoo/custom_addons`
- starter addon: `pokecard_storefront`
- public storefront route after install: `/pokecard-store`

## Why Odoo Here

Odoo Community gives a free ERP/storefront base: products, website, cart, checkout, orders, customers, inventory, invoicing, and back-office workflows.

The long-term value is connecting that commerce base to PokemonTool intelligence:

```text
PokemonTool market data -> Odoo products/pricing/inventory -> seller storefront/orders
```

Do not edit Odoo core in `vendor/odoo` for app-specific work. Put custom behavior in `odoo/custom_addons`.

## First Run

Copy the local env file:

```bash
cp odoo/.env.example odoo/.env
```

Validate config without starting services:

```bash
bash odoo/scripts/validate_odoo_scaffold.sh
```

Start Odoo:

```bash
docker compose -f docker-compose.odoo.yml --env-file odoo/.env up -d
```

Open:

```text
http://127.0.0.1:8069
```

Create the first database in the Odoo web setup screen.

Development master password from `odoo/config/odoo.conf`:

```text
admin_dev_change_me
```

Change that before any shared or public deployment.

## Install The Storefront Addon

Inside Odoo:

1. Open Apps.
2. Enable developer mode if needed.
3. Update Apps List.
4. Search for `PokeCard Storefront`.
5. Install it.
6. Open `/pokecard-store`.

The addon depends on `website`, `website_sale`, and `product`, so Odoo installs the basic eCommerce foundation if those modules are not already installed.

## Useful Commands

Run the read-only infrastructure doctor:

```bash
python3 odoo/scripts/odoo_infra_doctor.py
# or
make odoo-doctor
```

Check compose syntax:

```bash
docker compose -f docker-compose.odoo.yml --env-file odoo/.env.example config --quiet
```

Start stack:

```bash
docker compose -f docker-compose.odoo.yml --env-file odoo/.env up -d
```

Tail logs:

```bash
docker compose -f docker-compose.odoo.yml --env-file odoo/.env logs -f --tail=80 odoo
```

Stop stack:

```bash
docker compose -f docker-compose.odoo.yml --env-file odoo/.env down
```

Keep data but recreate services:

```bash
docker compose -f docker-compose.odoo.yml --env-file odoo/.env up -d --force-recreate
```

Delete Odoo local data volumes only when you intentionally want a clean database:

```bash
docker compose -f docker-compose.odoo.yml --env-file odoo/.env down -v
```

## Next High-Value Work

1. Create real product categories: Raw Singles, Graded Slabs, Sealed Product, Concierge Sourcing.
2. Add a product template/import flow from PokemonTool inventory rows.
3. Add fields for external card ID, set name, grade, grader, cert number, market value, acquisition cost, and target margin.
4. Add a sync service from PokemonTool to Odoo products.
5. Add repricing workflow: market price changes -> suggested Odoo price update -> seller approves.
6. Add storefront trust elements: condition notes, slab cert, photos, returns, shipping promise.
7. Add backup/restore and production hardening before public exposure.

## Production Warnings

Do not expose this directly to the internet yet.

Before public use:

- change `admin_passwd`
- use strong DB password
- put Odoo behind HTTPS reverse proxy
- disable public DB listing if appropriate
- configure email
- configure payment provider
- configure backups
- configure logs and alerts
- test restore
- review Odoo module access rights
- use production-grade secrets, not `.env.example`

## PokemonTool Inventory Bridge

The store backend direction is now:

```text
PokemonTool inventory + market intelligence -> Odoo products + stock/sales/CRM/eCommerce
```

Installed Odoo backend apps in the local `pokecard_store` database:

- CRM
- Sales Management
- Inventory / Stock
- Website Sale Stock
- PokeCard Storefront custom addon

The custom addon extends Odoo products with Pokemon card metadata:

- PokemonTool inventory row ID
- external card ID
- set name
- card number
- rarity
- image URL
- raw/slab/sealed lane
- condition
- grader, grade, cert number
- acquisition cost
- market value
- target margin
- price source
- sync state

Preview a sync without writing products:

```bash
POKEMON_POSTGRES_DSN='postgresql://pokemontool_user:pokemontool_pass@127.0.0.1:5432/pokemontool' \
ODOO_URL='http://127.0.0.1:8069' \
ODOO_DB='pokecard_store' \
ODOO_USERNAME='admin' \
ODOO_PASSWORD='<your-odoo-password>' \
python3 odoo/custom_addons/pokecard_storefront/scripts/sync_pokemon_inventory_to_odoo.py --dry-run --limit 20
```

Run the sync for real only after confirming the dry-run output:

```bash
POKEMON_POSTGRES_DSN='postgresql://pokemontool_user:pokemontool_pass@127.0.0.1:5432/pokemontool' \
ODOO_URL='http://127.0.0.1:8069' \
ODOO_DB='pokecard_store' \
ODOO_USERNAME='admin' \
ODOO_PASSWORD='<your-odoo-password>' \
python3 odoo/custom_addons/pokecard_storefront/scripts/sync_pokemon_inventory_to_odoo.py --limit 100
```

The script creates or updates Odoo `product.template` records using `pokemon_inventory_id` as the stable key. Odoo then owns sellable products, sales orders, customer records, website publishing, and inventory operations. PokemonTool remains the intelligence engine for exact-card matching, market value, alerts, and repricing signals.
