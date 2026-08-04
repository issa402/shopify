#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POKEMON_DIR="$ROOT_DIR/Pokemon"

ODOO_COMPOSE=(-f "$ROOT_DIR/docker-compose.odoo.yml" --env-file "$ROOT_DIR/odoo/.env")
NEXUS_COMPOSE=(-f "$ROOT_DIR/docker-compose.dev.yml" -f "$ROOT_DIR/docker-compose.universe.yml")
POKEMON_COMPOSE=(-f "$POKEMON_DIR/docker-compose.yml" -f "$POKEMON_DIR/docker-compose.universe.yml")

ensure_bridge() {
  if ! docker network inspect pokemon-odoo-bridge >/dev/null 2>&1; then
    docker network create pokemon-odoo-bridge >/dev/null
  fi
}

compose_odoo() {
  COMPOSE_IGNORE_ORPHANS=true docker compose "${ODOO_COMPOSE[@]}" "$@"
}

compose_nexus() {
  COMPOSE_IGNORE_ORPHANS=true docker compose "${NEXUS_COMPOSE[@]}" "$@"
}

compose_pokemon() {
  cd "$POKEMON_DIR"
  docker compose "${POKEMON_COMPOSE[@]}" "$@"
}

wait_for_container_health() {
  local container="$1"
  local timeout_seconds="${2:-120}"
  local waited=0

  while (( waited < timeout_seconds )); do
    local status
    status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container" 2>/dev/null || true)"
    if [[ "$status" == "healthy" || "$status" == "running" ]]; then
      return 0
    fi
    sleep 2
    waited=$((waited + 2))
  done

  echo "Timed out waiting for $container health" >&2
  return 1
}

start_nexus() {
  if compose_nexus up -d; then
    return 0
  fi

  echo "Nexus startup did not complete on first attempt; waiting for Kafka and retrying..." >&2
  wait_for_container_health nexusos-kafka 120
  compose_nexus up -d
}

up() {
  ensure_bridge
  compose_odoo up -d
  start_nexus
  compose_pokemon up -d
}

down() {
  compose_pokemon down
  compose_nexus down
  compose_odoo down
}

ps_all() {
  echo "== Odoo =="
  compose_odoo ps odoo-db odoo
  echo
  echo "== NexusOS =="
  compose_nexus ps postgres redis qdrant zookeeper kafka ollama temporal temporal-ui gateway ai web
  echo
  echo "== PokemonTool =="
  compose_pokemon ps
}

config() {
  compose_odoo config --quiet
  compose_nexus config --quiet
  compose_pokemon config --quiet
}

health() {
  curl -fsS http://127.0.0.1:8069/pokecard-store >/dev/null
  echo "ok odoo storefront"
  curl -fsS http://127.0.0.1:8080/health
  curl -fsS http://127.0.0.1:8000/health
  curl -fsS http://127.0.0.1:3000 >/dev/null
  echo "ok nexusos web"
  curl -fsS http://127.0.0.1:3001/health
  curl -fsS http://127.0.0.1:5173 >/dev/null
  echo "ok pokemon web"
  curl -fsS "http://127.0.0.1:8765/search?q=Radiant%20Charizard&limit=1" >/dev/null
  echo "ok poketcg search"
}

usage() {
  cat <<'USAGE'
Usage: scripts/dev-universe.sh <command>

Commands:
  up       Start Odoo, NexusOS, and PokemonTool with non-conflicting local ports
  down     Stop all three local stacks
  ps       Show all stack service states
  config   Validate all compose files
  health   Run HTTP smoke checks for the local universe

Ports:
  NexusOS web/gateway/AI:      3000, 8080, 8000
  NexusOS Postgres/Redis:      55434, 6380
  Pokemon API/web/PokeTCG:     3001, 5173, 8765
  Pokemon Postgres/Redis:      55433, 6381
  Pokemon RabbitMQ/Grafana:    5673, 15673, 3002
  Odoo storefront/Postgres:    8069, 55432
USAGE
}

case "${1:-}" in
  up) up ;;
  down) down ;;
  ps) ps_all ;;
  config) config ;;
  health) health ;;
  ""|help|--help|-h) usage ;;
  *)
    usage >&2
    exit 2
    ;;
esac
