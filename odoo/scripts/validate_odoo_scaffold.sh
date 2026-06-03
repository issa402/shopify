#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

required_files=(
  "docker-compose.odoo.yml"
  "odoo/config/odoo.conf"
  "odoo/.env.example"
  "odoo/custom_addons/pokecard_storefront/__manifest__.py"
  "odoo/custom_addons/pokecard_storefront/__init__.py"
  "odoo/custom_addons/pokecard_storefront/controllers/__init__.py"
  "odoo/custom_addons/pokecard_storefront/controllers/main.py"
  "odoo/custom_addons/pokecard_storefront/views/website_pages.xml"
  "odoo/custom_addons/pokecard_storefront/static/src/css/pokecard_storefront.css"
)

for path in "${required_files[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "missing required file: $path" >&2
    exit 1
  fi
done

if [[ ! -f "vendor/odoo/odoo-bin" ]]; then
  echo "warning: vendor/odoo/odoo-bin not found; upstream Odoo source checkout is missing" >&2
fi

docker compose -f docker-compose.odoo.yml --env-file odoo/.env.example config --quiet

echo "Odoo scaffold validation passed."
