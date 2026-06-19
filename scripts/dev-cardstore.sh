#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POKEMON_DIR="$ROOT_DIR/Pokemon"

ODOO_COMPOSE=(-f "$ROOT_DIR/docker-compose.odoo.yml" --env-file "$ROOT_DIR/odoo/.env")
POKEMON_COMPOSE=(-f "$POKEMON_DIR/docker-compose.yml" -f "$POKEMON_DIR/docker-compose.universe.yml")

ensure_bridge() {
  if ! docker network inspect pokemon-odoo-bridge >/dev/null 2>&1; then
    docker network create pokemon-odoo-bridge >/dev/null
  fi
}

compose_odoo() {
  COMPOSE_IGNORE_ORPHANS=true docker compose "${ODOO_COMPOSE[@]}" "$@"
}

compose_pokemon() {
  cd "$POKEMON_DIR"
  docker compose "${POKEMON_COMPOSE[@]}" "$@"
}

up() {
  ensure_bridge
  compose_odoo up -d
  compose_pokemon up -d
  compose_pokemon stop scraping-service >/dev/null 2>&1 || true
}

up_with_scraping() {
  ensure_bridge
  compose_odoo up -d
  COMPOSE_PROFILES=browser-scraping compose_pokemon up -d
}

down() {
  compose_pokemon down
  compose_odoo down
}

ps_all() {
  echo "== Odoo =="
  compose_odoo ps odoo-db odoo
  echo
  echo "== PokemonTool =="
  compose_pokemon ps
}

health() {
  curl -fsS http://127.0.0.1:8069/pokecard-store >/dev/null
  echo "ok odoo storefront"
  curl -fsS http://127.0.0.1:3001/health
  curl -fsS http://127.0.0.1:5173 >/dev/null
  echo "ok pokemon web"
  curl -fsS "http://127.0.0.1:8765/search?q=Radiant%20Charizard&limit=1" >/dev/null
  echo "ok poketcg search"
}

config() {
  compose_odoo config --quiet
  compose_pokemon config --quiet
}

scraping_up() {
  COMPOSE_PROFILES=browser-scraping compose_pokemon up -d scraping-service
}

scraping_down() {
  compose_pokemon stop scraping-service >/dev/null 2>&1 || true
}

usage() {
  cat <<'USAGE'
Usage: scripts/dev-cardstore.sh <command>

Commands:
  up                 Start Odoo + PokemonTool + PokeTCG without heavy browser scraping
  up-with-scraping   Start Odoo + PokemonTool + PokeTCG + browser scraping
  scraping-up        Start only the optional Facebook/Mercari browser scraper
  scraping-down      Stop only the optional browser scraper
  down               Stop Odoo + PokemonTool
  ps                 Show card-store service states
  config             Validate card-store compose files
  health             Run card-store HTTP smoke checks

Default product surface:
  Odoo storefront:    http://127.0.0.1:8069/pokecard-store
  Pokemon dashboard:  http://127.0.0.1:5173
  Pokemon API:        http://127.0.0.1:3001
  PokeTCG:            http://127.0.0.1:8765

NexusOS is intentionally not started by this script. Use scripts/dev-universe.sh
only when you are working on the broader Shopify/NexusOS platform.
USAGE
}

case "${1:-}" in
  up) up ;;
  up-with-scraping) up_with_scraping ;;
  scraping-up) scraping_up ;;
  scraping-down) scraping_down ;;
  down) down ;;
  ps) ps_all ;;
  config) config ;;
  health) health ;;
  ""|help|--help|-h) usage ;;
  *) usage >&2; exit 2 ;;
esac
