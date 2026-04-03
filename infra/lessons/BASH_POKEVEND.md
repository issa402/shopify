# 🔥 BASH SCRIPTING — POKEVEND PROJECT EDITION
## Every single example runs against YOUR actual stack
### File: infra/lessons/BASH_POKEVEND.md

---

> **YOUR ACTUAL STACK — memorise these before reading further:**
> - Go API (pokemontool) → port **3001** — the main backend
> - PostgreSQL (nexusos-postgres) → port **5432** — cards, users, alerts, watchlists
> - Redis (nexusos-redis) → port **6379** — cache for card search, trending, deals
> - Qdrant (nexusos-qdrant) → port **6333** — vector DB for AI semantic search
> - Kafka (nexusos-kafka) → port **9092** — event streaming
> - Temporal (nexusos-temporal) → port **7233** — long-running agent workflows
> - Ollama (nexusos-ollama) → port **11434** — local LLM (Llama 3 8B)
> - DB name: `pokemontool` | DB user: `pokemontool_user`

---

## PART 1: Variables — Using YOUR Project's Actual Values

The first thing any infrastructure script does is define constants for the project.
Here's how you'd define them for THIS project:

```bash
#!/usr/bin/env bash
set -euo pipefail

# ── Project constants — copied DIRECTLY from config/config.go defaults ─────
# Compare with: Pokemon/server/config/config.go lines 69-93
# getEnv("PORT", "3001")              → API_PORT
# getEnv("POSTGRES_HOST", "localhost") → DB_HOST
# getEnv("POSTGRES_DB", "pokemontool") → DB_NAME

API_PORT="${PORT:-3001}"
API_URL="http://localhost:${API_PORT}"

DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-pokemontool}"
DB_USER="${POSTGRES_USER:-pokemontool_user}"
DB_PASS="${POSTGRES_PASSWORD:-pokemontool_pass}"

REDIS_ADDR="${REDIS_URL:-redis:6379}"
REDIS_HOST="${REDIS_ADDR%%:*}"   # Strip everything after : → "redis"
REDIS_PORT="${REDIS_ADDR##*:}"   # Strip everything before : → "6379"

# ── Parameter expansion in action ──────────────────────────────────────────
# These come from your REDIS_URL="redis:6379" env var.
# ${REDIS_ADDR%%:*}  = remove longest suffix starting with : → "redis"
# ${REDIS_ADDR##*:}  = remove longest prefix ending  with : → "6379"

echo "API:   ${API_URL}"
echo "DB:    postgresql://${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo "Redis: ${REDIS_HOST}:${REDIS_PORT}"

# ── Path construction using YOUR actual project layout ─────────────────────
PROJECT_ROOT="/home/iscjmz/shopify/shopify"
GO_SERVER="${PROJECT_ROOT}/Pokemon/server"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
MAIN_GO="${GO_SERVER}/main.go"
CONFIG_GO="${GO_SERVER}/config/config.go"
CARD_STORE="${GO_SERVER}/store/card_store.go"

# Verify they exist using -f test
[[ -f "${MAIN_GO}" ]]    && echo "✓ main.go found" || echo "✗ main.go MISSING"
[[ -f "${CONFIG_GO}" ]]  && echo "✓ config.go found" || echo "✗ config.go MISSING"
[[ -f "${COMPOSE_FILE}" ]] && echo "✓ docker-compose.yml found"

# ── Extracting info from YOUR project using parameter expansion ────────────
# Get the binary name from the Go module name in go.mod
# go.mod line: "module pokemontool"
MODULE_NAME=$(grep "^module" "${GO_SERVER}/go.mod" | awk '{print $2}')
echo "Go module: ${MODULE_NAME}"    # pokemontool

# Get the number of handlers in your project (one per file)
HANDLER_COUNT=$(ls "${GO_SERVER}/handlers/"*_handler.go 2>/dev/null | wc -l)
echo "Handlers: ${HANDLER_COUNT}"

# Get the number of store files (one per domain: card, user, alert, etc.)
STORE_COUNT=$(ls "${GO_SERVER}/store/"*_store.go 2>/dev/null | wc -l)
echo "Stores: ${STORE_COUNT}"
```

**TRY IT NOW:**
```bash
# Run this to see YOUR project's real values
grep "^module" /home/iscjmz/shopify/shopify/Pokemon/server/go.mod
ls /home/iscjmz/shopify/shopify/Pokemon/server/handlers/
ls /home/iscjmz/shopify/shopify/Pokemon/server/store/
```

---

## PART 2: Control Flow — Health Checking YOUR Stack

In `main.go` lines 77-97, the Go server checks each dependency at startup
and fails fast if any are unavailable. Here's the bash equivalent —
you'll use this in your `01_os_audit.sh` and `02_process_manager.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# ── The same "fail fast" logic from main.go, but in bash ───────────────────
# main.go: if err != nil { log.Fatalf("❌ PostgreSQL: %v", err) }
# Bash equivalent: check each service, fail immediately if critical one is down

check_postgres() {
    # docker-compose.yml line 19: healthcheck uses "pg_isready -U nexusos"
    # We replicate that exact check here
    if docker exec nexusos-postgres pg_isready -U "${DB_USER:-pokemontool_user}" -d "${DB_NAME:-pokemontool}" \
        &>/dev/null; then
        echo "  ✓ PostgreSQL: ready"
        return 0
    else
        echo "  ✗ PostgreSQL: NOT READY"
        return 1
    fi
}

check_redis() {
    # docker-compose.yml line 34: healthcheck uses "redis-cli ping"
    if docker exec nexusos-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo "  ✓ Redis: PONG received"
        return 0
    else
        echo "  ✗ Redis: no PONG"
        return 1
    fi
}

check_api() {
    # health_handler.go line 36: returns {"status":"ok","service":"pokemontool-go"}
    # The Go server is on port 3001 (config.go line 69: getEnv("PORT", "3001"))
    local response
    response=$(curl -sf "http://localhost:3001/health" 2>/dev/null)
    if [[ $? -eq 0 ]]; then
        # Parse the status field from the JSON response
        local status
        status=$(echo "${response}" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo "  ✓ Pokevend API: ${status}"
        return 0
    else
        echo "  ✗ Pokevend API: not responding on port 3001"
        return 1
    fi
}

check_qdrant() {
    # docker-compose.yml line 50: healthcheck: "curl -sf http://localhost:6333/readyz"
    if curl -sf http://localhost:6333/readyz &>/dev/null; then
        echo "  ✓ Qdrant: ready"
        return 0
    else
        echo "  ✗ Qdrant: not ready"
        return 1
    fi
}

check_temporal() {
    # Temporal gRPC is on port 7233 (docker-compose.yml line 121)
    # We can check if it's listening with nc (netcat)
    if nc -zw2 localhost 7233 2>/dev/null; then
        echo "  ✓ Temporal: port 7233 open"
        return 0
    else
        echo "  ✗ Temporal: port 7233 not listening"
        return 1
    fi
}

check_ollama() {
    # Ollama HTTP API on port 11434 (docker-compose.yml line 99)
    # GET /api/tags returns list of loaded models
    if curl -sf http://localhost:11434/api/tags &>/dev/null; then
        local models
        models=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | wc -l)
        echo "  ✓ Ollama: ${models} model(s) loaded"
        return 0
    else
        echo "  ✗ Ollama: not responding on port 11434"
        return 1
    fi
}

# ── Run all checks — same order as main.go dependency injection ─────────────
main() {
    echo "Pokevend Stack Health Check"
    echo "==========================="
    
    local failed=0
    
    # Critical services — if these fail, the API doesn't work
    check_postgres  || ((failed++))
    check_redis     || ((failed++))
    check_api       || ((failed++))
    
    # Supporting services — API works without these but features degrade
    check_qdrant    || true   # AI search degrades, but cards still work
    check_temporal  || true   # Long-running workflows fail, but syncs still work
    check_ollama    || true   # AI features fail, but core search still works
    
    echo ""
    if [[ $failed -gt 0 ]]; then
        echo "RESULT: ✗ ${failed} critical service(s) down — API will not function"
        exit 1
    else
        echo "RESULT: ✓ All critical services healthy"
    fi
}

main "$@"
```

**WHY THIS MATTERS:** When you deploy to production, this exact script runs
before the deployment to confirm the environment is sane. If postgres is down,
you DON'T deploy. You fix postgres first.

---

## PART 3: Loops — Working WITH Your Actual Services

```bash
#!/usr/bin/env bash
set -euo pipefail

# ── YOUR actual containers from docker-compose.yml ─────────────────────────
# Map: container_name → expected_port (from docker-compose.yml)

declare -A CONTAINERS
CONTAINERS["nexusos-postgres"]="5432"
CONTAINERS["nexusos-redis"]="6379"
CONTAINERS["nexusos-qdrant"]="6333"
CONTAINERS["nexusos-kafka"]="9092"
CONTAINERS["nexusos-temporal"]="7233"
CONTAINERS["nexusos-ollama"]="11434"

# ── Iterate over all YOUR containers and check their status ────────────────
echo "Container Status Report"
echo "────────────────────────────────────────────────────"
printf "%-30s %-12s %-15s %-10s\n" "CONTAINER" "PORT" "DOCKER STATUS" "PORT OPEN?"

for container in "${!CONTAINERS[@]}"; do
    port="${CONTAINERS[$container]}"
    
    # Get Docker's reported status
    docker_status=$(docker inspect --format='{{.State.Status}}' "${container}" 2>/dev/null || echo "not found")
    
    # Get Docker's healthcheck result (from docker-compose.yml healthcheck blocks)
    health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no-check{{end}}' \
        "${container}" 2>/dev/null || echo "n/a")
    
    # Independently verify the port is reachable (don't just trust Docker)
    if nc -zw1 localhost "${port}" 2>/dev/null; then
        port_status="open"
    else
        port_status="CLOSED"
    fi
    
    printf "%-30s %-12s %-15s %-10s\n" "${container}" "${port}" "${docker_status}(${health})" "${port_status}"
done

echo ""

# ── Practical loop: find which containers have exited ──────────────────────
# This is the first thing you run when the API returns errors
echo "Exited Containers (should be empty if stack is healthy):"
while IFS= read -r line; do
    if [[ -n "${line}" ]]; then
        echo "  ⚠ EXITED: ${line}"
    fi
done < <(docker ps -a --filter "status=exited" --format "{{.Names}} (exited {{.Status}})")

[[ -z "$(docker ps -a --filter "status=exited" --format "{{.Names}}" 2>/dev/null)" ]] && \
    echo "  ✓ No exited containers"

# ── Loop over YOUR Go source files and count lines of code ─────────────────
SERVER_DIR="/home/iscjmz/shopify/shopify/Pokemon/server"
echo ""
echo "Codebase Size by Layer:"
printf "%-20s %8s %8s\n" "LAYER" "FILES" "LINES"
printf "%-20s %8s %8s\n" "─────────────────" "────────" "────────"

for layer in handlers services store middleware models config routes worker; do
    dir="${SERVER_DIR}/${layer}"
    if [[ -d "${dir}" ]]; then
        file_count=$(find "${dir}" -name "*.go" | wc -l)
        line_count=$(find "${dir}" -name "*.go" -exec cat {} \; | wc -l)
        printf "%-20s %8d %8d\n" "${layer}" "${file_count}" "${line_count}"
    fi
done
```

**TRY IT NOW:**
```bash
# Run just the docker container check
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"

# And the codebase count manually
find /home/iscjmz/shopify/shopify/Pokemon/server/handlers -name "*.go" | wc -l
find /home/iscjmz/shopify/shopify/Pokemon/server/store    -name "*.go" | wc -l
```

---

## PART 4: grep + awk + sed — Analysing YOUR Actual Code & Logs

This is where knowledge becomes POWER. You're not running generic examples —
you're extracting real, useful information from your actual codebase.

### grep — Searching Your Source Code

```bash
SERVER_DIR="/home/iscjmz/shopify/shopify/Pokemon/server"
COMPOSE="./docker-compose.yml"

# ── Find every TODO in your codebase that YOU need to implement ───────────
echo "=== YOUR TODOs ==="
grep -rn "^// TODO" "${SERVER_DIR}" --include="*.go" | \
    sed 's|'"${SERVER_DIR}"'/||'   # Strip the long path prefix for readability
# You'll see: store/card_store.go:272: // TODO #2 (Practice): ...

# ── Find every place your config values are actually used ─────────────────
# config.go defines JWT_SECRET — where is it consumed in the handlers?
echo ""
echo "=== JWT Secret Usage ==="
grep -rn "JWTSecret\|JWT_SECRET" "${SERVER_DIR}" --include="*.go" | \
    grep -v "^${SERVER_DIR}/config/"  # Exclude where it's defined, show where it's USED

# ── Find potential SQL injection risks (fmt.Sprintf in SQL context) ────────
# card_store.go shows safe use of Sprintf (line 152) — let's verify all uses
echo ""
echo "=== fmt.Sprintf in SQL queries (audit) ==="
grep -n "fmt.Sprintf" "${SERVER_DIR}/store/"*.go | head -20
# You'll see: store/card_store.go with controlled input (marketplace allowlist)

# ── Find all your API endpoints ───────────────────────────────────────────
echo ""
echo "=== All API Routes ==="
grep -n 'r\.Get\|r\.Post\|r\.Put\|r\.Delete\|r\.Patch' \
    "${SERVER_DIR}/routes/routes.go" 2>/dev/null | \
    awk '{print NR".", $0}' | \
    sed 's/[[:space:]]*r\.\(Get\|Post\|Put\|Delete\|Patch\)("\([^"]*\)".*/\1 \2/'

# ── Find every hardcoded port number (should match docker-compose.yml) ─────
echo ""
echo "=== Hardcoded Port Numbers in Source ==="
grep -rn ':[0-9]\{4,5\}' "${SERVER_DIR}" --include="*.go" | \
    grep -v "^Binary\|_test.go\|go.sum" | \
    grep -oE ':[0-9]{4,5}' | \
    sort | uniq -c | sort -rn
# This tells you: are these consistent with docker-compose.yml?
# Port 3001 should appear (API), 5432 (DB), 6379 (Redis)
```

### awk — Extracting Real Metrics From YOUR Logs

```bash
# ── Parse the chi middleware logger output from YOUR API ──────────────────
# chi's Logger middleware (main.go line 157) produces lines like:
# "GET /api/v1/cards/search?q=charizard HTTP/1.1\" from 127.0.0.1 - 200 124B in 45.231ms"

# Get the last 200 log lines from your running API
API_LOGS=$(docker logs nexusos-temp 2>&1 2>/dev/null | tail -200 || \
           journalctl -u pokevend --no-pager -n 200 2>/dev/null || \
           echo "")   # Graceful fallback if neither exists

if [[ -n "${API_LOGS}" ]]; then
    echo "=== Request Rate by Endpoint ==="
    echo "${API_LOGS}" | \
        grep -oE '"(GET|POST|PUT|DELETE) [^"]+' | \
        awk '{print $1, $2}' | \
        grep -oE '/(api|health|auth)[^ ]*' | \
        sort | uniq -c | sort -rn | head -10
    
    echo ""
    echo "=== Slow Requests (> 100ms) ==="
    echo "${API_LOGS}" | \
        grep -oE 'in [0-9]+\.[0-9]+ms' | \
        awk '{gsub(/ms/,""); gsub(/in /,""); if ($1+0 > 100) print int($1)"ms"}' | \
        sort -rn | head -10
fi

# ── Parse docker-compose.yml with awk to extract all image names ──────────
echo ""
echo "=== Images Used in docker-compose.yml ==="
awk '/image:/ {print $2}' \
    /home/iscjmz/shopify/shopify/docker-compose.yml
# Output: pgvector/pgvector:pg16, redis:7-alpine, qdrant/qdrant:latest, etc.

# ── Check which docker-compose services have healthchecks defined ──────────
echo ""  
echo "=== Services WITH and WITHOUT healthchecks ==="
# Services with healthcheck
awk '/  [a-z]/{svc=$1} /healthcheck:/{print svc, "✓ has healthcheck"}' \
    /home/iscjmz/shopify/shopify/docker-compose.yml | sed 's/://'

# ── Analyse config.go to list all env vars YOUR project uses ──────────────
echo ""
echo "=== All env vars Pokevend reads (from config.go) ==="
grep 'getEnv\|getEnvInt' \
    /home/iscjmz/shopify/shopify/Pokemon/server/config/config.go | \
    grep -oE '"[A-Z_]+"' | \
    tr -d '"' | sort
# Output: CLIENT_URL, ENCRYPTION_KEY, JWT_SECRET, NODE_ENV, PORT, POSTGRES_DB, etc.
```

### sed — Generating Configs FOR YOUR Project

```bash
# ── Generate a .env file for YOUR project from the config.go defaults ──────
# config.go shows us exactly what variables and defaults the app needs.
# This script generates the .env template automatically from the source code.

SERVER_DIR="/home/iscjmz/shopify/shopify/Pokemon/server"

echo "Generating .env template from config/config.go..."

# Extract getEnv("KEY", "default") calls and format as KEY=default
grep 'getEnv\|getEnvInt' "${SERVER_DIR}/config/config.go" | \
    sed 's/.*getEnvInt\?("\([^"]*\)", "\([^"]*\)").*/\1=\2/' | \
    sed 's/.*getEnvInt("\([^"]*\)", \([0-9]*\)).*/\1=\2/' | \
    grep -E '^[A-Z_]+=.*' | \
    sort > /tmp/pokevend_env_template.txt

echo "# Pokevend .env Template — Generated from config/config.go" > /tmp/pokevend.env.template
echo "# Generated: $(date --iso-8601=seconds)" >> /tmp/pokevend.env.template
echo "" >> /tmp/pokevend.env.template
cat /tmp/pokevend_env_template.txt >> /tmp/pokevend.env.template

echo "Template written to: /tmp/pokevend.env.template"
cat /tmp/pokevend.env.template

# ── NOW produce the SECURITY-HARDENED version of the .env ─────────────────
echo ""
echo "Generating production-hardened secrets..."

# config.go line 89: JWT_SECRET needs openssl rand -hex 32
JWT_SECRET=$(openssl rand -hex 32)  # 64 hex chars = 32 bytes = very strong

# config.go line 90: ENCRYPTION_KEY must be exactly 64 hex chars
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Show what would go in .env (never actually write the passwords here)
cat <<EOF

# PRODUCTION VALUES (never commit to git!):
JWT_SECRET=${JWT_SECRET}
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Validate JWT_SECRET length (config.go line 141 requires >= 32 chars):
echo "JWT_SECRET length: \${#JWT_SECRET} chars"
[[ \${#JWT_SECRET} -ge 32 ]] && echo "✓ Long enough" || echo "✗ TOO SHORT"
EOF
```

**RUN THIS NOW and see your own project's env vars listed:**
```bash
grep 'getEnv' /home/iscjmz/shopify/shopify/Pokemon/server/config/config.go | \
    grep -oE '"[A-Z_]+"' | tr -d '"'
```

---

## PART 5: Functions — Real Automation for YOUR Workflow

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/iscjmz/shopify/shopify"
GO_SERVER="${PROJECT_ROOT}/Pokemon/server"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

# ── Function: build the Pokevend binary ────────────────────────────────────
# This is what you run before every deployment.
# Replicates what you'd do by hand: cd Pokemon/server && go build ./...

build_pokevend() {
    local output="${1:-/tmp/pokevend}"  # Where to put the built binary
    local start_time; start_time=$(date +%s)
    
    echo "Building Pokevend Go binary..."
    echo "  Source: ${GO_SERVER}"
    echo "  Output: ${output}"
    
    # Build with version info embedded in the binary
    # This lets you run: ./pokevend --version and see exactly what was built
    local version; version=$(cd "${PROJECT_ROOT}" && git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    local build_time; build_time=$(date --iso-8601=seconds)
    
    if go build \
        -o "${output}" \
        -ldflags "-X main.Version=${version} -X main.BuildTime=${build_time}" \
        ./... 2>&1; then
        
        local elapsed=$(( $(date +%s) - start_time ))
        local size; size=$(du -sh "${output}" | cut -f1)
        echo "  ✓ Build successful: ${size} in ${elapsed}s (version: ${version})"
        return 0
    else
        echo "  ✗ Build FAILED — check errors above"
        return 1
    fi
}

# ── Function: run the Go tests ─────────────────────────────────────────────
# In main.go comments: "Run: go test ./..." is the standard
# You should ALWAYS run tests before deploying

run_pokevend_tests() {
    echo "Running test suite..."
    
    if go test ./... -timeout 60s 2>&1; then
        echo "  ✓ All tests passed"
        return 0
    else
        echo "  ✗ Tests FAILED — do NOT deploy"
        return 1
    fi
}

# ── Function: dump the database ────────────────────────────────────────────
# docker-compose.yml: the postgres container is named nexusos-postgres
# config.go: DB name is pokemontool, user is pokemontool_user

dump_pokevend_db() {
    local output_file="${1:-/tmp/pokevend_db_$(date +%Y%m%d_%H%M%S).sql}"
    
    echo "Dumping database: ${DB_NAME:-pokemontool} → ${output_file}"
    
    # The DB runs INSIDE the docker container (nexusos-postgres)
    # docker exec runs the command INSIDE the container
    # pg_dump exports the entire schema + data as SQL
    if docker exec nexusos-postgres \
        pg_dump -U "${POSTGRES_USER:-pokemontool_user}" \
                -d "${POSTGRES_DB:-pokemontool}" \
                --no-password \
        > "${output_file}" 2>/dev/null; then
        
        local size; size=$(du -sh "${output_file}" | cut -f1)
        echo "  ✓ Database dumped: ${size}"
        
        # Compress immediately
        gzip "${output_file}"
        echo "  ✓ Compressed: ${output_file}.gz"
        return 0
    else
        echo "  ✗ pg_dump FAILED — is nexusos-postgres running?"
        return 1
    fi
}

# ── Function: check your card count (sanity check after migrations) ────────
check_card_count() {
    local count
    count=$(docker exec nexusos-postgres \
        psql -U "${POSTGRES_USER:-pokemontool_user}" \
             -d "${POSTGRES_DB:-pokemontool}" \
             -t -c "SELECT COUNT(*) FROM cards;" 2>/dev/null | tr -d ' ')
    
    if [[ -n "${count}" && "${count}" -gt 0 ]]; then
        echo "  ✓ Cards in database: ${count}"
    elif [[ "${count}" == "0" ]]; then
        echo "  ⚠ Cards table is EMPTY — scraper may not have run yet"
    else
        echo "  ✗ Could not query cards table — is DB running?"
    fi
}

# ── Function: query Redis cache stats ─────────────────────────────────────
# card_service.go uses Redis to cache trending cards and search results
# config.go line 81: RedisAddr = getEnv("REDIS_URL", "redis:6379")

check_redis_cache() {
    echo "Redis cache stats:"
    
    # INFO keyspace shows which databases have keys and how many
    docker exec nexusos-redis redis-cli INFO keyspace 2>/dev/null | \
        grep "^db" | while IFS= read -r line; do
            echo "  ${line}"
        done
    
    # Show keys that look like Pokevend cache entries
    # card_service.go caches by card ID and search term
    local cache_keys
    cache_keys=$(docker exec nexusos-redis redis-cli KEYS "*card*" 2>/dev/null | wc -l)
    echo "  Card-related cache keys: ${cache_keys}"
    
    # Memory usage
    docker exec nexusos-redis redis-cli INFO memory 2>/dev/null | \
        grep "used_memory_human\|maxmemory_human" | \
        awk -F: '{printf "  %s: %s\n", $1, $2}'
}

# ── Main Workflow: Pre-deployment checklist ─────────────────────────────────
pre_deploy_check() {
    local env="${1:-staging}"
    local passed=0
    local failed=0
    
    run_check() {
        local name="$1"
        shift
        if "$@"; then
            ((passed++))
        else
            ((failed++))
            if [[ "${name}" == *"CRITICAL"* ]]; then
                echo "CRITICAL check failed — aborting"
                exit 1
            fi
        fi
    }
    
    echo "=== Pre-deployment Checklist: ${env} ==="
    echo ""
    
    (cd "${GO_SERVER}" && run_check "CRITICAL: Tests" run_pokevend_tests)
    (cd "${GO_SERVER}" && run_check "CRITICAL: Build" build_pokevend "/tmp/pokevend_predeploy")
    run_check "Database backup" dump_pokevend_db
    run_check "DB sanity (row count)" check_card_count
    run_check "Redis health" check_redis_cache
    
    echo ""
    echo "=== Result: ${passed} passed, ${failed} failed ==="
    [[ $failed -eq 0 ]]
}
```

**RUN IT:**
```bash
# Run just the card count check right now
docker exec nexusos-postgres \
    psql -U pokemontool_user -d pokemontool \
    -t -c "SELECT COUNT(*) FROM cards;" 2>/dev/null || echo "DB not running"

# Check Redis keys
docker exec nexusos-redis redis-cli INFO keyspace 2>/dev/null || echo "Redis not running"
```

---

## PART 6: The Holy Trinity on YOUR Log Format

Your Go app uses `slog` (main.go lines 179-186).
In **production** (`cfg.Env == "production"`), it outputs **JSON**.
In **development**, it outputs **text**.

```bash
# ── What YOUR logs look like in development (text format) ─────────────────
# time=2026-04-01T14:23:01.000Z level=INFO msg="Server started" port=3001 env=development
# time=2026-04-01T14:23:02.100Z level=ERROR msg="DB connection failed" error="..."

# Chi's Logger middleware (main.go line 157) adds lines like:
# "GET /api/v1/cards/search HTTP/1.1" from ::1 - 200 1234B in 45.231ms

# ── What YOUR logs look like in production (JSON format) ──────────────────
# {"time":"2026-04-01T14:23:01Z","level":"ERROR","msg":"DB connection failed","error":"..."}
# {"time":"2026-04-01T14:23:01Z","level":"INFO","msg":"Health check","status":"ok"}

# ── grep: find errors in your RUNNING API ─────────────────────────────────
docker logs nexusos-temp 2>/dev/null | grep -i "error\|fatal\|panic" | tail -20

# ── awk: count requests per endpoint from chi logs ────────────────────────
# chi Logger format: "METHOD /path HTTP/1.1" from IP - STATUS SIZEb in TIMEms
docker logs nexusos-temp 2>/dev/null | \
    grep '"GET\|"POST\|"PUT\|"DELETE' | \
    awk '{print $1}' | \
    grep -oE '/(api|health|auth|cards|alerts|watchlist|inventory|deals|shows)[^ "]*' | \
    sort | uniq -c | sort -rn | head -10

# ── awk: find slow database queries ───────────────────────────────────────
# PostgreSQL logs slow queries. In your postgres container:
docker logs nexusos-postgres 2>/dev/null | \
    grep "duration:" | \
    awk '{
        for(i=1;i<=NF;i++) {
            if ($i == "duration:") {
                ms = $(i+1)+0
                if (ms > 50) printf "SLOW(%.0fms): %s\n", ms, $0
            }
        }
    }' | head -10

# ── sed: redact passwords in logs before sharing ───────────────────────────
# If you need to share logs with someone, strip sensitive values first
docker logs nexusos-postgres 2>/dev/null | \
    sed 's/password=[^[:space:]]*/password=REDACTED/gi' | \
    sed 's/JWT_SECRET=[^[:space:]]*/JWT_SECRET=REDACTED/gi' | \
    head -50

# ── Pipeline: Top 5 cards being searched RIGHT NOW ────────────────────────
# card_store.go line 80: searchPattern = fmt.Sprintf("%%%s%%", query)
# Postgres logs the actual query — extract the search patterns
docker logs nexusos-postgres 2>/dev/null | \
    grep "ILIKE" | \
    grep -oE "'%[^%]*%'" | \
    tr -d "'" | \
    sed 's/%//g' | \
    sort | uniq -c | sort -rn | head -5
```

---

## PART 7: The Complete Workflow — Your Daily Dev Loop

This is the exact sequence you should run every morning when you start working:

```bash
#!/usr/bin/env bash
# morning_startup.sh — Run this when you sit down to work
set -euo pipefail

PROJECT_ROOT="/home/iscjmz/shopify/shopify"
GO_SERVER="${PROJECT_ROOT}/Pokemon/server"

echo "=============================="
echo " POKEVEND MORNING STARTUP"
echo " $(date '+%A, %B %d at %H:%M')"
echo "=============================="

# 1. Start the full stack (docker-compose.yml)
echo ""
echo "Starting Docker stack..."
docker-compose -f "${PROJECT_ROOT}/docker-compose.yml" up -d 2>/dev/null
echo "  Waiting 5s for containers to initialize..."
sleep 5

# 2. Quick port scan of all expected services
echo ""
echo "Port availability:"
declare -A PORTS=(
    ["Pokevend API"]=3001
    ["PostgreSQL"]=5432
    ["Redis"]=6379
    ["Qdrant"]=6333
    ["Kafka"]=9092
    ["Temporal"]=7233
    ["Ollama"]=11434
)

for service in "${!PORTS[@]}"; do
    port="${PORTS[$service]}"
    nc -zw1 localhost "${port}" 2>/dev/null && printf "  ✓ %-20s :%d\n" "${service}" "${port}" \
                                             || printf "  ✗ %-20s :%d NOT LISTENING\n" "${service}" "${port}"
done

# 3. Verify API health endpoint (health_handler.go)
echo ""
echo "API health check:"
response=$(curl -sf http://localhost:3001/health 2>/dev/null || echo '{"status":"unreachable"}')
echo "  Response: ${response}"

# 4. How many cards in the DB today vs yesterday
echo ""
echo "Database sanity:"
card_count=$(docker exec nexusos-postgres \
    psql -U pokemontool_user -d pokemontool -t -c "SELECT COUNT(*) FROM cards;" 2>/dev/null | \
    tr -d ' \n' || echo "unavailable")
echo "  Total cards: ${card_count}"

# 5. Show any failed containers
failed=$(docker ps -a --filter "status=exited" --format "{{.Names}}" 2>/dev/null)
if [[ -n "${failed}" ]]; then
    echo ""
    echo "⚠ FAILED CONTAINERS:"
    echo "${failed}" | while read -r container; do
        echo "  - ${container}"
        echo "    Last log: $(docker logs --tail 1 "${container}" 2>&1)"
    done
fi

# 6. Any recent git changes (what did you leave off working on?)
echo ""
echo "Recent changes:"
cd "${PROJECT_ROOT}" && git log --oneline -5 2>/dev/null || echo "  (no git history)"

echo ""
echo "=============================="
echo " Ready to develop. Good luck."
echo "=============================="
```

**SAVE AND RUN:**
```bash
chmod +x /home/iscjmz/shopify/shopify/infra/practice/morning_startup.sh
bash /home/iscjmz/shopify/shopify/infra/practice/morning_startup.sh
```

---

## CHEAT SHEET — Commands You'll Type Every Day for THIS Project

```bash
# ── Stack management ───────────────────────────────────────────────
docker-compose -f shopify/docker-compose.yml up -d          # Start all
docker-compose -f shopify/docker-compose.yml down           # Stop all
docker-compose -f shopify/docker-compose.yml restart postgres # Restart one
docker-compose -f shopify/docker-compose.yml logs -f        # Follow all logs

# ── Database (pokemontool DB, pokemontool_user) ────────────────────
docker exec -it nexusos-postgres psql -U pokemontool_user -d pokemontool
docker exec nexusos-postgres psql -U pokemontool_user -d pokemontool -c "SELECT COUNT(*) FROM cards;"
docker exec nexusos-postgres psql -U pokemontool_user -d pokemontool -c "\dt"  # list tables
docker exec nexusos-postgres pg_dump -U pokemontool_user pokemontool > backup.sql

# ── Redis (caching layer from card_service.go) ─────────────────────
docker exec -it nexusos-redis redis-cli
docker exec nexusos-redis redis-cli KEYS "*"                # All keys
docker exec nexusos-redis redis-cli INFO memory             # Memory stats
docker exec nexusos-redis redis-cli FLUSHALL                # Clear all cache ⚠

# ── Go API ────────────────────────────────────────────────────────
cd Pokemon/server
go build ./...                    # Build (check errors)
go test ./...                     # Run all tests
go vet ./...                      # Static analysis (catches bugs)
curl -s localhost:3001/health | python3 -m json.tool  # Pretty health check

# ── Kafka (event streaming) ────────────────────────────────────────
docker exec nexusos-kafka kafka-topics --list --bootstrap-server localhost:9092
docker exec nexusos-kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 --topic <topic> --from-beginning

# ── Logs: what's happening RIGHT NOW ──────────────────────────────
docker logs nexusos-postgres --tail 50
docker logs nexusos-redis    --tail 50
docker logs nexusos-kafka    --tail 50 2>&1

# ── Spot the bottleneck ───────────────────────────────────────────
docker stats --no-stream    # CPU/memory for all containers right now
```
