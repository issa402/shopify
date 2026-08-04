#!/usr/bin/env bash
# =============================================================================
# SCRIPT: pokevend_stack_audit.sh  [UPDATED — real container names]
# MODULE: Linux + Bash — Week 1
#
# THE REAL CONTAINER NAMES (from Pokemon/docker-compose.yml):
#   pokemontool_postgres       → port 5432
#   pokemontool_redis          → port 6379
#   pokemontool_rabbitmq       → port 5672 (AMQP) + 15672 (Management UI)
#   pokemontool_server         → port 3001 (Go API)
#   pokemontool_api_consumer   → port 8001 (FastAPI — api-consumer)
#   pokemontool_analytics      → no public port (batch — runs internally)
#   pokemontool_scraper        → no public port (Playwright headless)
#   pokemontool_client         → port 5173 (React → Nginx in prod)
#
# THE REAL DB:
#   Name: pokemontool  User: pokemontool_user  Pass: (from .env)
#   Tables: users, watchlists, alerts, price_alerts, inventory, deals,
#           shows, cards, card_listings, price_history, api_keys
#
# HOW TO RUN:
#   bash infra/scripts/linux/pokevend_stack_audit.sh
#   bash infra/scripts/linux/pokevend_stack_audit.sh --fix
#   bash infra/scripts/linux/pokevend_stack_audit.sh --json
#
# WHEN YOU'VE COMPLETED THIS:
#   Run with everything up → see clean baseline output
#   Stop postgres → see critical failure detected
#   Stop rabbitmq → see api-consumer and analytics show degraded
# =============================================================================

set -euo pipefail

readonly PROJECT_ROOT="/home/iscjmz/shopify/shopify/Pokemon"
readonly COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
readonly GO_SERVER="${PROJECT_ROOT}/server"

# Real credentials from .env.example — override via environment
readonly DB_NAME="${POSTGRES_DB:-pokemontool}"
readonly DB_USER="${POSTGRES_USER:-pokemontool_user}"
readonly API_PORT="${PORT:-3001}"
readonly CONSUMER_PORT="8001"

# Flags
FIX_MODE=false
JSON_MODE=false

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $*"; }
fail() { echo -e "  ${RED}✗${NC} $*"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $*"; }
hdr()  { echo -e "\n${BOLD}${BLUE}━━━ $* ━━━${NC}"; }

# =============================================================================
# ARGUMENT PARSING
# TODO: Parse --fix and --json flags
# Use: for arg in "$@"; do case "${arg}" in --fix) FIX_MODE=true ;; ... esac; done
# YOUR CODE HERE
:

# =============================================================================
# SECTION 1: System Identity
# =============================================================================
audit_system() {
    hdr "1. SYSTEM IDENTITY"

    # TODO: Kernel version (uname -r)
    # WHY: Docker requires Linux ≥ 4.x; some cgroup features need 5.x
    # YOUR CODE HERE

    # TODO: OS release (source /etc/os-release && echo "${PRETTY_NAME}")
    # YOUR CODE HERE

    # TODO: Uptime and load average (uptime)
    # WHY: Load avg > nproc means machine is overloaded — containers will lag
    # YOUR CODE HERE

    # TODO: RAM usage (free -h)
    # WHY: pokemontool_analytics uses numpy for trend calculations — needs RAM
    # YOUR CODE HERE

    # TODO: CPU count (nproc)
    # YOUR CODE HERE

    # TODO: Disk usage — warn if any mount is > 80% full
    # COMMAND: df -h | awk '$5+0 > 80 {print "DISK WARN:", $0}'
    # WHY: PostgreSQL data lives in /var/lib/docker/volumes/pokemontool_pgdata
    #      If disk fills up, postgres CRASHES and you lose all cards/users
    # YOUR CODE HERE
}

# =============================================================================
# SECTION 2: Docker Stack Status
# Checks ALL services from docker-compose.yml
# =============================================================================
audit_docker_stack() {
    hdr "2. DOCKER STACK (from Pokemon/docker-compose.yml)"

    # TODO: Check Docker daemon is running
    # docker info &>/dev/null 2>&1 || { fail "Docker not running!"; return 1; }
    # YOUR CODE HERE

    # These match docker-compose.yml EXACTLY:
    # container_name fields and their expected host ports
    declare -A CONTAINERS=(
        ["pokemontool_postgres"]="5432"
        ["pokemontool_redis"]="6379"
        ["pokemontool_rabbitmq"]="5672"
        ["pokemontool_server"]="3001"
        ["pokemontool_api_consumer"]="8001"
        ["pokemontool_analytics"]=""        # no public port
        ["pokemontool_scraper"]=""          # no public port
        ["pokemontool_client"]="5173"
    )

    printf "\n  %-30s %-12s %-14s %-12s\n" "CONTAINER" "DOCKER" "HEALTH" "PORT"
    printf "  %-30s %-12s %-14s %-12s\n" "──────────────────────────────" "──────────" "────────────" "──────────"

    local failed_critical=0

    for container in "${!CONTAINERS[@]}"; do
        local port="${CONTAINERS[$container]}"

        # TODO: Get docker status (running/exited/not found)
        # docker inspect --format='{{.State.Status}}' "${container}" 2>/dev/null || echo "not found"
        # YOUR CODE HERE
        local status="NOT IMPLEMENTED"

        # TODO: Get health status from docker healthcheck
        # docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no-check{{end}}'
        # YOUR CODE HERE
        local health="NOT IMPLEMENTED"

        # TODO: If port is not empty, check it with nc -zw1 localhost "${port}"
        # YOUR CODE HERE
        local port_display="${port:-internal}"

        printf "  %-30s %-12s %-14s %-12s\n" "${container}" "${status}" "${health}" "${port_display}"
    done

    # TODO: If FIX_MODE=true and any container is exited/missing:
    # Run: docker-compose -f "${COMPOSE_FILE}" up -d
    # YOUR CODE HERE
}

# =============================================================================
# SECTION 3: Go API Health
# Checks the /health endpoint from health_handler.go
# =============================================================================
audit_go_api() {
    hdr "3. GO API (pokemontool_server:${API_PORT})"

    # TODO: Hit http://localhost:3001/health
    # health_handler.go returns: {"status":"ok","service":"pokemontool-go"}
    # if curl -sf --max-time 5 "http://localhost:${API_PORT}/health"
    # Parse status field from JSON response
    # YOUR CODE HERE

    # TODO: Check which port the Go API is ACTUALLY listening on
    # ss -tlnp | grep ":${API_PORT}"
    # WHY: Sometimes the binary starts but binds to wrong port
    # YOUR CODE HERE

    # TODO: Check Go binary was built successfully (can it compile?)
    # cd "${GO_SERVER}" && go vet ./... 2>&1 | head -5
    # YOUR CODE HERE
}

# =============================================================================
# SECTION 4: FastAPI api-consumer
# Python service that scans eBay + TCGplayer
# main.py has /health endpoint (added in TODO #2 — now it's implemented)
# =============================================================================
audit_api_consumer() {
    hdr "4. PYTHON API-CONSUMER (pokemontool_api_consumer:${CONSUMER_PORT})"

    # TODO: Hit http://localhost:8001/health
    # main.py health endpoint returns: {"status":"ok/unhealthy","service":"api-consumer","rabbitmq":"connected/not connected"}
    # Check if rabbitmq field is "connected" — if not, eBay/TCGplayer data won't flow
    # YOUR CODE HERE

    # TODO: Check the scanner_loop is running
    # The scanner_loop (main.py line 131) runs as asyncio.create_task()
    # It polls the Go API at: GET http://localhost:3001/api/internal/watchlist-names
    # Verify that endpoint exists and returns a list
    # curl -sf "http://localhost:${API_PORT}/api/internal/watchlist-names"
    # YOUR CODE HERE

    # TODO: Check the api-consumer logs for the most recent scan cycle
    # docker logs pokemontool_api_consumer --tail 20 2>/dev/null
    # Look for: "Scan cycle complete. Sleeping Xs..."
    # YOUR CODE HERE
}

# =============================================================================
# SECTION 5: PostgreSQL Deep Check
# Tables from database/migrations/ — cards, watchlists, deals, etc.
# =============================================================================
audit_postgres() {
    hdr "5. POSTGRESQL (pokemontool_postgres:5432)"

    # TODO: Run the docker-compose.yml healthcheck manually
    # docker-compose.yml line 30: pg_isready -U pokemontool_user -d postgres
    # YOUR CODE HERE

    # TODO: List all tables (should have: cards, users, watchlists, alerts,
    #        price_alerts, inventory, deals, shows, card_listings, price_history, api_keys)
    # COMMAND: docker exec pokemontool_postgres psql -U "${DB_USER}" -d "${DB_NAME}" -c "\dt"
    # YOUR CODE HERE

    # TODO: Count rows in each key table
    # For each of: cards, watchlists, users, deals
    # Run: SELECT COUNT(*) FROM <table>;
    # Print as: "cards: N rows"
    # YOUR CODE HERE

    # TODO: Check for the price_history table — this is what trend_analyzer.py reads
    # analytics-engine/trend_analyzer.py line 41: self.history_col = db["price_history"]
    # (Note: the old version used MongoDB, new version uses PostgreSQL price_history table)
    # COMMAND: docker exec pokemontool_postgres psql -U "${DB_USER}" -d "${DB_NAME}" \
    #          -t -c "SELECT COUNT(*) FROM price_history;"
    # YOUR CODE HERE

    # TODO: Show the 3 most recently updated cards (scraper working?)
    # SELECT name, price_ebay, last_updated FROM cards ORDER BY last_updated DESC LIMIT 3;
    # YOUR CODE HERE
}

# =============================================================================
# SECTION 6: RabbitMQ Queue Health
# RabbitMQ is the backbone that connects:
#   api-consumer (producer) → [queue] → Go notification_worker (consumer)
#   analytics-engine (producer) → [queue] → (future: websocket push)
#
# If queue depth is growing, the consumer is falling behind.
# If queue is empty but no listings appear, producer isn't publishing.
# =============================================================================
audit_rabbitmq() {
    hdr "6. RABBITMQ (pokemontool_rabbitmq:5672)"
    echo "  (Management UI: http://localhost:15672 — user: guest / pass: guest)"

    # TODO: Check AMQP port is open (nc -zw1 localhost 5672)
    # YOUR CODE HERE

    # TODO: Use RabbitMQ HTTP API to list queues and their depths
    # The management plugin runs on port 15672
    # COMMAND: curl -s -u guest:guest http://localhost:15672/api/queues
    # Parse: name (queue name), messages (depth), consumers (how many are consuming)
    # HINT: Use python3 -m json.tool or grep/awk to parse
    # YOUR CODE HERE
    local rmq_response
    if rmq_response=$(curl -sf -u guest:guest "http://localhost:15672/api/queues" 2>/dev/null); then
        # TODO: Parse queue names and message counts from the JSON response
        # python3 -c "import json,sys; queues=json.load(sys.stdin); ..."
        # YOUR CODE HERE
        echo "  RabbitMQ API reachable — implement JSON parsing above"
    else
        fail "RabbitMQ management API not reachable"
        fail "  If api-consumer is running → it can't publish listings"
        fail "  If Go worker can't connect → real-time alerts won't fire"
    fi

    # TODO: Check docker logs for any connection errors
    # docker logs pokemontool_rabbitmq --tail 20 2>/dev/null | grep -i "error\|connection\|refused"
    # YOUR CODE HERE
}

# =============================================================================
# SECTION 7: Analytics Engine
# Runs trend analysis every 1 hour and deal finder daily at 6 AM
# analytics-engine/main.py uses schedule library
# =============================================================================
audit_analytics() {
    hdr "7. ANALYTICS ENGINE (pokemontool_analytics)"

    # TODO: Check if container is running
    # docker inspect --format='{{.State.Status}}' pokemontool_analytics 2>/dev/null
    # YOUR CODE HERE

    # TODO: Check most recent log output
    # docker logs pokemontool_analytics --tail 30 2>/dev/null
    # Look for lines containing:
    #   "✓ Trends computed for N cards"  ← trend_analyzer.py ran successfully
    #   "✓ N deals found today"          ← deal_finder.py ran successfully
    #   "Trend analysis failed"           ← something broke — needs fixing
    # YOUR CODE HERE

    # TODO: Check the deals table in PostgreSQL — did the deal finder write anything today?
    # SELECT COUNT(*) FROM deals WHERE created_at::date = CURRENT_DATE;
    # If 0 and it's past 6 AM → deal finder may have crashed
    # YOUR CODE HERE

    # TODO: Check trending card counts
    # SELECT trend_label, COUNT(*) FROM cards GROUP BY trend_label;
    # Expected: mix of RISING, FALLING, STABLE
    # If ALL cards are STABLE → trend analyzer hasn't run yet
    # YOUR CODE HERE
}

# =============================================================================
# SECTION 8: Security Audit
# Checks .env for dangerous defaults (same as config.go Validate())
# =============================================================================
audit_security() {
    hdr "8. SECURITY AUDIT"

    # Load .env if it exists
    local env_file="${PROJECT_ROOT}/.env"

    # TODO: Check JWT_SECRET is not the placeholder from .env.example
    # .env.example line 13: "replace_with_a_long_random_string_at_least_64_chars"
    # Also check it's >= 64 chars (config.go says >= 32, but 64 is better)
    # YOUR CODE HERE
    local jwt="${JWT_SECRET:-replace_with_a_long_random_string_at_least_64_chars}"
    if [[ "${jwt}" == *"replace_with"* ]]; then
        fail "JWT_SECRET is still the placeholder value from .env.example"
        fail "  Fix: export JWT_SECRET=\$(openssl rand -hex 32)"
    elif [[ ${#jwt} -lt 32 ]]; then
        warn "JWT_SECRET is only ${#jwt} chars — use at least 64"
    else
        ok "JWT_SECRET: set (${#jwt} chars)"
    fi

    # TODO: Check ENCRYPTION_KEY is set and 64 hex chars
    # .env.example line 14: "replace_with_32_char_hex_key_for_aes256"
    # YOUR CODE HERE

    # TODO: Check POSTGRES_PASSWORD is not the default "pokemontool_pass"
    # docker-compose.yml line 23: POSTGRES_PASSWORD:-pokemontool_pass
    # This default is in a PUBLIC repo — every attacker knows it
    # YOUR CODE HERE

    # TODO: Scan source code for hardcoded API keys or secrets
    # Look for: EBAY_CLIENT_SECRET, TCGPLAYER_PRIVATE_KEY, JWT_SECRET being hardcoded
    # COMMAND: grep -rn "ebay_client_secret\|private_key.*=.*['\"][a-zA-Z0-9]\{10,\}" \
    #          "${PROJECT_ROOT}" --include="*.py" --include="*.go" | grep -v ".env.example\|#"
    # YOUR CODE HERE

    # TODO: Check .gitignore has .env listed (prevent accidental commit of secrets)
    # COMMAND: grep "^\.env" "${PROJECT_ROOT}/.gitignore"
    # YOUR CODE HERE
}

# =============================================================================
# SECTION 9: Codebase Health
# Go + Python codebases
# =============================================================================
audit_codebase() {
    hdr "9. CODEBASE HEALTH"

    # ── Go Server ─────────────────────────────────────────────
    echo "  Go API (server/):"

    # TODO: Build check — does go build succeed?
    # cd "${GO_SERVER}" && go build -o /tmp/pokemontool_check ./... 2>&1
    # YOUR CODE HERE

    # TODO: Run go vet (static analysis — catches real bugs at compile time)
    # cd "${GO_SERVER}" && go vet ./... 2>&1
    # YOUR CODE HERE

    # TODO: Count all your TODOs in Go source (things still to implement)
    # grep -rn "^// TODO" "${GO_SERVER}" --include="*.go" | wc -l
    # YOUR CODE HERE

    # ── Python Services ────────────────────────────────────────
    echo ""
    echo "  Python services:"

    for service in "api-consumer" "analytics-engine"; do
        local svc_dir="${PROJECT_ROOT}/services/${service}"

        # TODO: Check requirements.txt exists and has content
        # YOUR CODE HERE

        # TODO: Check for syntax errors in all .py files
        # COMMAND: find "${svc_dir}" -name "*.py" -exec python3 -m py_compile {} \;
        # python3 -m py_compile <file> exits with 0 if syntax is OK, 1 if not
        # YOUR CODE HERE

        echo "  ${service}: (implement syntax check above)"
    done

    # TODO: Show TODO count in Python services
    # grep -rn "# TODO" "${PROJECT_ROOT}/services" --include="*.py" | wc -l
    # YOUR CODE HERE
}

# =============================================================================
# MAIN
# =============================================================================
main() {
    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║      POKEVEND STACK AUDIT REPORT                     ║${NC}"
    echo -e "${BOLD}║      $(date '+%Y-%m-%d %H:%M:%S %Z')                 ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════════════════════╝${NC}"

    audit_system
    audit_docker_stack
    audit_go_api
    audit_api_consumer
    audit_postgres
    audit_rabbitmq
    audit_analytics
    audit_security
    audit_codebase

    echo ""
    echo -e "${BOLD}Audit complete.${NC} $(date --iso-8601=seconds)"
    echo ""
    echo "Next steps:"
    echo "  1. Fix any ✗ CRITICAL items (postgres/redis/rabbitmq down = API broken)"
    echo "  2. Fix any ✗ SECURITY items before deploying to EC2"
    echo "  3. Track ⚠ WARN items — they degrade features but don't crash the app"
}

main "$@"
