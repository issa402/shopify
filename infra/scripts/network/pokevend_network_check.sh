#!/usr/bin/env bash
# =============================================================================
# SCRIPT: pokevend_network_check.sh
# MODULE: Networking — Week 3
# TIES TO: docker-compose.yml (all ports), main.go CORS config, rate_limit.go
#
# HOW TO RUN:
#   bash infra/scripts/network/pokevend_network_check.sh
#   bash infra/scripts/network/pokevend_network_check.sh --cors-test
#   bash infra/scripts/network/pokevend_network_check.sh --rate-limit-test
# =============================================================================
set -euo pipefail

readonly API_PORT="${PORT:-3001}"

# EXACT ports from docker-compose.yml ports: sections
declare -A EXPECTED_PORTS=(
    ["PostgreSQL (nexusos-postgres)"]="5432"
    ["Redis (nexusos-redis)"]="6379"
    ["Qdrant HTTP (nexusos-qdrant)"]="6333"
    ["Qdrant gRPC (nexusos-qdrant)"]="6334"
    ["Zookeeper"]="2181"
    ["Kafka (nexusos-kafka)"]="9092"
    ["Temporal gRPC"]="7233"
    ["Temporal UI"]="8088"
    ["Ollama (nexusos-ollama)"]="11434"
    ["Go API"]="${API_PORT}"
)

# These should NEVER be reachable from the public internet
INTERNAL_ONLY_PORTS=(5432 6379 6333 6334 2181 9092 7233 11434)

section() { echo ""; echo "━━━ $* ━━━"; }

# =============================================================================
# SECTION 1: Port Check — mirrors docker-compose.yml ports
# =============================================================================
check_all_ports() {
    section "1. PORT AVAILABILITY (from docker-compose.yml)"
    printf "  %-38s %-8s %-10s\n" "SERVICE" "PORT" "STATUS"
    printf "  %-38s %-8s %-10s\n" "────────────────────────────────────" "──────" "────────"

    local open=0 closed=0

    for service in "${!EXPECTED_PORTS[@]}"; do
        local port="${EXPECTED_PORTS[$service]}"

        # TODO: Check if port is open using nc -zw1 localhost "${port}"
        # Set   is_open=true if returns 0, is_open=false if returns 1
        # Print ✓ OPEN or ✗ CLOSED with the service and port
        # YOUR CODE HERE
        printf "  ? %-36s %-8s %s\n" "${service}" "${port}" "NOT IMPLEMENTED"
    done

    echo "  Result: ${open} open, ${closed} closed"
}

# =============================================================================
# SECTION 2: Docker DNS
# docker-compose.yml line 146: name: nexusos-network
# Services reach each other by service name (postgres, redis, kafka)
# =============================================================================
check_docker_dns() {
    section "2. DOCKER INTERNAL DNS (nexusos-network)"
    echo "  Services communicate by name inside Docker — verifying..."

    # Service names from docker-compose.yml (the YAML key, not container_name)
    local services=("postgres" "redis" "qdrant" "kafka" "temporal" "ollama")

    for svc in "${services[@]}"; do
        # TODO: From INSIDE the postgres container, resolve each service by name
        # COMMAND: docker exec nexusos-postgres getent hosts "${svc}" 2>/dev/null
        # If it returns an IP → DNS is working
        # If it fails → network is broken
        # YOUR CODE HERE
        echo "  ? ${svc}: NOT IMPLEMENTED"
    done

    # TODO: Show all containers attached to nexusos-network
    # COMMAND: docker network inspect nexusos-network \
    #   --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}'
    # YOUR CODE HERE
}

# =============================================================================
# SECTION 3: CORS Headers
# main.go lines 165-170: AllowedOrigins = [cfg.ClientURL, "http://localhost:5173"]
# The React frontend (Vite at :5173) REQUIRES these CORS headers to talk to the API
# =============================================================================
check_cors() {
    section "3. CORS VALIDATION (main.go lines 165-170)"
    echo "  AllowedOrigins: [CLIENT_URL, http://localhost:5173]"
    echo ""

    # TODO: Send a CORS preflight request from the allowed origin
    # A preflight is an OPTIONS request with Origin and Access-Control-Request-Method headers
    # curl -s -D - -o /dev/null -X OPTIONS \
    #   -H "Origin: http://localhost:5173" \
    #   -H "Access-Control-Request-Method: POST" \
    #   "http://localhost:${API_PORT}/api/v1/auth/login"
    #
    # Look for in response headers:
    # Access-Control-Allow-Origin: http://localhost:5173  ← must match
    # Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
    # Access-Control-Allow-Headers: Accept, Authorization, Content-Type
    # YOUR CODE HERE
    echo "  CORS check not implemented — add curl command above"

    # TODO: Test that an attacker origin is REJECTED
    # Send Origin: http://evil.attacker.com
    # The response should NOT contain Access-Control-Allow-Origin with that domain
    # YOUR CODE HERE
}

# =============================================================================
# SECTION 4: Rate Limit Test
# main.go line 175: r.Use(middleware.RateLimit(rdb, 100))
# Fire 110 requests, expect ~10 to return 429 Too Many Requests
# =============================================================================
check_rate_limit() {
    section "4. RATE LIMIT TEST (middleware.RateLimit(rdb, 100))"
    echo "  Firing 110 rapid requests to /health..."
    echo "  Expect: ~100 return 200, ~10 return 429"
    echo ""

    declare -A counts=([200]=0 [429]=0 [other]=0)

    # TODO: Fire 110 requests as fast as possible and count status codes
    # Use curl -s -o /dev/null -w "%{http_code}" for each
    # Count how many are 200, how many are 429
    # HINT: for i in $(seq 1 110); do
    #   code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${API_PORT}/health")
    #   case "${code}" in 200) ...; ;; 429) ...; ;; *) ...; ;; esac
    # done
    # YOUR CODE HERE

    echo "  200 OK:             ${counts[200]}"
    echo "  429 Rate Limited:   ${counts[429]}"
    echo "  Other:              ${counts[other]}"

    if [[ ${counts[429]} -gt 0 ]]; then
        echo "  ✓ Rate limiter is WORKING (Redis is handling the counters)"
    else
        echo "  ✗ No 429s seen — rate limiter may be disabled or Redis is down"
    fi
}

# =============================================================================
# SECTION 5: Endpoint Smoke Test
# routes/routes.go registers all URL → handler mappings
# =============================================================================
smoke_test_endpoints() {
    section "5. ENDPOINT SMOKE TEST (from routes/routes.go)"
    echo ""

    # These endpoints exist based on what handlers are registered in main.go
    # and wired up in routes/routes.go
    local -A ENDPOINTS=(
        ["GET /health"]="200"
        ["GET /api/v1/cards/trending"]="200 401"
        ["GET /api/v1/cards/search?q=charizard"]="200 401"
    )

    for endpoint in "${!ENDPOINTS[@]}"; do
        local method; method=$(echo "${endpoint}" | awk '{print $1}')
        local path;   path=$(echo "${endpoint}" | awk '{print $2}')
        local expected="${ENDPOINTS[$endpoint]}"

        # TODO: Make the request and capture status code
        # COMMAND: status=$(curl -s -o /dev/null -w "%{http_code}" \
        #                  -X "${method}" "http://localhost:${API_PORT}${path}")
        # Print: ✓ if status in expected, ✗ if not
        # YOUR CODE HERE
        echo "  ? ${method} ${path} → NOT IMPLEMENTED (expected: ${expected})"
    done
}

main() {
    echo ""
    echo "╔═══════════════════════════════════════════╗"
    echo "║    POKEVEND NETWORK AUDIT                 ║"
    echo "║    $(date '+%Y-%m-%d %H:%M:%S')           ║"
    echo "╚═══════════════════════════════════════════╝"

    case "${1:-all}" in
        --cors-test)       check_cors ;;
        --rate-limit-test) check_rate_limit ;;
        --docker-dns)      check_docker_dns ;;
        all)
            check_all_ports
            check_docker_dns
            check_cors
            check_rate_limit
            smoke_test_endpoints
            ;;
        *) echo "Usage: $0 [--cors-test|--rate-limit-test|--docker-dns|all]"; exit 1 ;;
    esac

    echo ""
    echo "Audit complete: $(date --iso-8601=seconds)"
}

main "$@"
