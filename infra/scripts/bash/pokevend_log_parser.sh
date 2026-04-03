#!/usr/bin/env bash
# =============================================================================
# SCRIPT: pokevend_log_parser.sh
# MODULE: Bash — Week 2 (grep + awk + sed on REAL logs)
# TIES TO THESE REAL PROJECT FILES:
#   main.go lines 179-186: slog setup (JSON in prod, text in dev)
#   main.go line 157:      chimiddleware.Logger logs every request
#   main.go line 159:      chimiddleware.Timeout(30s) — 30s requests = problem
#
# WHAT IT DOES:
#   Parses actual logs from your running Pokevend containers.
#   Extracts: error rates, slow requests, top endpoints, search terms,
#             DB query patterns, Redis cache hit/miss hints.
#
# THE REAL LOG FORMATS THIS PARSES:
#
#   CHI LOGGER (main.go line 157) — text format from the router:
#   "GET /api/v1/cards/search?q=charizard HTTP/1.1" from 127.0.0.1 - 200 1234B in 45.231ms
#   "POST /api/v1/auth/login HTTP/1.1" from ::1 - 401 89B in 3.1ms
#
#   SLOG (main.go line 207) — text format in dev:
#   time=2026-04-01T14:23:01.000Z level=INFO msg="Server started" port=3001
#   time=2026-04-01T14:23:02.100Z level=ERROR msg="DB connection failed" error="..."
#
#   SLOG — JSON format in prod (NODE_ENV=production):
#   {"time":"2026-04-01T14:23:01Z","level":"ERROR","msg":"DB connection","error":"..."}
#
#   POSTGRES (from nexusos-postgres container):
#   2026-04-01 14:23:01.123 UTC [42] LOG:  duration: 145.321 ms  statement: SELECT ...
#
# HOW TO RUN:
#   bash infra/scripts/bash/pokevend_log_parser.sh
#   bash infra/scripts/bash/pokevend_log_parser.sh --since 1h
#   bash infra/scripts/bash/pokevend_log_parser.sh --container nexusos-postgres
#   bash infra/scripts/bash/pokevend_log_parser.sh --follow   (live tail mode)
#
# WHEN COMPLETE: Run during normal operation (see clean baseline).
#   Then: curl localhost:3001/nonexistent 50 times → re-run → see 404 spike.
#   Then: stop nexusos-redis → re-run → see Redis errors appear.
# =============================================================================

set -euo pipefail

# ── Config ─────────────────────────────────────────────────────────────────────
readonly API_PORT="${PORT:-3001}"
SINCE="1h"
TARGET_CONTAINER=""
FOLLOW_MODE=false

# =============================================================================
# ARGUMENT PARSING
# =============================================================================
# TODO: Parse these arguments:
#   --since DURATION   (e.g. "1h", "30m", "24h") → set SINCE
#   --container NAME   → set TARGET_CONTAINER (only parse that one container)
#   --follow           → set FOLLOW_MODE=true (live tail mode)
# Use: while [[ $# -gt 0 ]]; do case "$1" in --since) SINCE="$2"; shift 2 ;; ... done
# YOUR CODE HERE

# =============================================================================
# LOG COLLECTION
# =============================================================================

get_api_logs() {
    # Get logs from the Go API (the chi Logger output)
    # The API runs outside docker in dev, so we try journalctl first,
    # then fall back to looking for a running Go process

    if systemctl is-active pokevend &>/dev/null; then
        journalctl -u pokevend --since "${SINCE} ago" --no-pager -o cat 2>/dev/null
    else
        # Dev mode: Go process logs to stdout, try to grab from tmux/screen or a log file
        # If you're running it with: go run . > /tmp/pokevend.log 2>&1
        # then: cat /tmp/pokevend.log
        cat /tmp/pokevend.log 2>/dev/null || echo ""
    fi
}

get_container_logs() {
    local container="$1"
    docker logs "${container}" --since "${SINCE}" --timestamps 2>&1 2>/dev/null || true
}

get_postgres_logs() {
    # PostgreSQL logs ALL queries when log_min_duration_statement is set
    # This shows slow queries (>0ms = all queries, >100 = only slow ones)
    get_container_logs "nexusos-postgres"
}

# =============================================================================
# ANALYSIS FUNCTIONS
# Each one uses grep/awk/sed on the REAL log format
# =============================================================================

analyze_error_rate() {
    local logs="$1"
    echo ""
    echo "━━━ ERROR ANALYSIS ━━━"

    # TODO: Count total log lines
    # HINT: echo "${logs}" | wc -l
    # YOUR CODE HERE

    # TODO: Count lines containing "ERROR" or "error" (case-insensitive)
    # chi Logger format: the status code is in the line as a number after " - "
    # slog format: level=ERROR or "level":"ERROR"
    # COMMAND: echo "${logs}" | grep -ciE "level=ERROR|\"level\":\"ERROR\"|\" 5[0-9]{2} "
    # YOUR CODE HERE

    # TODO: Count 4xx errors (client errors — bad requests, auth failures)
    # chi Logger lines with status 4xx: '" from ... - 4XX '
    # COMMAND: grep -cE '" - 4[0-9]{2} ' <<< "${logs}" || echo 0
    # YOUR CODE HERE

    # TODO: Count 5xx errors (server errors — these are YOUR bugs)
    # COMMAND: grep -cE '" - 5[0-9]{2} ' <<< "${logs}" || echo 0
    # YOUR CODE HERE

    # TODO: Show the actual error messages (not just counts)
    # chi format: the path before the status code
    # slog format: msg="..." field
    # Show last 10 unique error messages
    # YOUR CODE HERE
}

analyze_request_breakdown() {
    local logs="$1"
    echo ""
    echo "━━━ REQUEST BREAKDOWN BY ENDPOINT ━━━"

    # chi Logger format: "METHOD /path HTTP/1.1" from IP - STATUS SIZEb in TIMEms
    # We want: count per endpoint, grouped

    # TODO: Extract all endpoints and count them
    # Step 1: grep lines that look like HTTP logs (contain " HTTP/1.1")
    # Step 2: awk to extract the URL path (field 2 after the opening quote)
    # Step 3: strip query strings (everything after ?)
    # Step 4: sort | uniq -c | sort -rn | head 15

    # HINT (full pipeline):
    # echo "${logs}" | \
    #   grep '"[A-Z]\+ /' | \              ← Only HTTP log lines
    #   awk '{print $2}' | \               ← Extract "GET" or "POST" etc.
    #   ... need to think about the format more carefully ...

    # BETTER HINT: chi Logger wraps the request in quotes:
    # "GET /api/v1/cards/search?q=charizard HTTP/1.1"
    # So: grep -oE '"(GET|POST|PUT|DELETE|PATCH) [^[:space:]]+'
    # Then: awk '{print $1, $2}' to get "GET /api/v1/cards/search"
    # Then: sed 's/?.*$//' to strip query params

    # YOUR CODE HERE
}

analyze_response_times() {
    local logs="$1"
    echo ""
    echo "━━━ RESPONSE TIME ANALYSIS ━━━"

    # chi Logger ends with: in 45.231ms
    # We want: list of all times, then find min/max/average/p95

    # TODO:
    # Step 1: Extract all millisecond values
    #   HINT: grep -oE 'in [0-9]+\.[0-9]+ms' | grep -oE '[0-9]+\.[0-9]+'
    # Step 2: Find the slow ones (> 1000ms = 1 second — over the 30s timeout warning)
    #   Any request > 100ms should be investigated (card_store uses indices, should be fast)
    # Step 3: Print the slowest 5 requests with their full line for context

    # HINT for slow request detection:
    # echo "${logs}" | \
    #   grep -E 'in [0-9]{4,}\.' | \   ← 4+ digits before decimal = ≥ 1000ms
    #   tail -10

    # YOUR CODE HERE

    # TODO: Calculate average response time using awk arithmetic
    # HINT:
    # echo "${logs}" | \
    #   grep -oE 'in [0-9]+\.[0-9]+ms' | \
    #   grep -oE '[0-9]+\.[0-9]+' | \
    #   awk '{sum+=$1; count++} END {if(count>0) printf "Average: %.1fms over %d requests\n", sum/count, count}'
    # YOUR CODE HERE
}

analyze_search_terms() {
    local logs="$1"
    echo ""
    echo "━━━ TOP SEARCH TERMS ━━━"

    # chi Logger logs: "GET /api/v1/cards/search?q=charizard HTTP/1.1"
    # card_store.go Search() is called with: query = URL-decoded value of ?q=

    # TODO:
    # Step 1: Find all lines containing /cards/search
    # Step 2: Extract the query parameter value (after q= and before space or &)
    # Step 3: URL decode spaces (%20 → ' ')
    # Step 4: Count by search term

    # HINT:
    # echo "${logs}" | \
    #   grep '/cards/search' | \
    #   grep -oE 'q=[^[:space:]&"]*' | \
    #   sed 's/q=//' | \
    #   sed 's/%20/ /g' | \             ← Basic URL decode
    #   sort | uniq -c | sort -rn | head 10
    # YOUR CODE HERE
}

analyze_auth_failures() {
    local logs="$1"
    echo ""
    echo "━━━ AUTH FAILURE ANALYSIS ━━━"

    # auth_handler.go returns 401 for bad credentials
    # main.go line 175: RateLimit(rdb, 100) — 429 means rate limited

    # TODO: Find all 401 responses (failed logins)
    # chi Logger: "POST /api/v1/auth/login HTTP/1.1" from IP - 401 ...

    # TODO: Count 401s and 429s (rate limit hits)
    # YOUR CODE HERE

    # TODO: If more than 10 401s from the same IP in this time window → flag as brute force
    # Step 1: Extract IP from 401 lines
    # chi Logger format: from IP - 401
    # HINT: grep "401" | grep -oE 'from [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | awk '{print $2}'
    # Step 2: count per IP, flag any > 10
    # YOUR CODE HERE
}

analyze_postgres_slow_queries() {
    echo ""
    echo "━━━ POSTGRESQL SLOW QUERIES ━━━"
    echo "(Threshold: > 100ms — same as what you'd set in postgresql.conf)"

    # Postgres slow query log format:
    # 2026-04-01 14:23:01.123 UTC [42] LOG:  duration: 145.321 ms  statement: SELECT ...

    local pg_logs
    pg_logs=$(get_postgres_logs)

    if [[ -z "${pg_logs}" ]]; then
        echo "  (No postgres logs available — container may not be running)"
        return
    fi

    # TODO: Find slow query lines (duration > 100ms)
    # HINT: grep "duration:" | awk to extract ms value and filter > 100
    # YOUR CODE HERE

    # TODO: Extract the actual SQL from slow query lines
    # Postgres logs: duration: 145.321 ms  statement: SELECT ...
    # Extract everything after "statement: "
    # Truncate to first 80 chars to avoid huge output
    # YOUR CODE HERE

    # TODO: Which tables are being queried the most?
    # grep "statement:" | grep -oE "(FROM|UPDATE|INSERT INTO|DELETE FROM) [a-z_]+" | sort | uniq -c | sort -rn
    # YOUR CODE HERE
}

# =============================================================================
# LIVE FOLLOW MODE
# =============================================================================

follow_all_logs() {
    echo "Following ALL Pokevend service logs (Ctrl+C to stop)"
    echo "Errors highlighted in red"
    echo ""

    # TODO: Use `docker logs -f` and `journalctl -f` to tail logs from multiple sources
    # Combine them with process substitution: cat <(cmd1) <(cmd2) <(cmd3)
    # Pipe through grep with color highlighting for errors

    # HINT:
    # cat <(docker logs nexusos-postgres -f 2>&1) \
    #     <(docker logs nexusos-redis -f 2>&1) \
    #     <(docker logs nexusos-kafka -f 2>&1 | head -1) \
    # | grep --line-buffered --color=always -E "ERROR|FATAL|PANIC|error|$"
    # YOUR CODE HERE

    echo "Follow mode not implemented yet — complete the TODO above"
}

# =============================================================================
# MAIN REPORT GENERATOR
# =============================================================================

generate_report() {
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║      POKEVEND LOG ANALYSIS REPORT                    ║"
    echo "║      Since: ${SINCE} ago                             ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo "  Generated: $(date --iso-8601=seconds)"

    # Collect logs once (so we don't run docker multiple times)
    local api_logs
    api_logs=$(get_api_logs 2>/dev/null || echo "")

    # TODO: Call each analysis function with the logs
    # YOUR CODE HERE:
    # analyze_error_rate "${api_logs}"
    # analyze_request_breakdown "${api_logs}"
    # analyze_response_times "${api_logs}"
    # analyze_search_terms "${api_logs}"
    # analyze_auth_failures "${api_logs}"
    # analyze_postgres_slow_queries    ← this fetches its own logs

    echo ""
    echo "━━━ TRY THESE COMMANDS TO GENERATE TEST DATA ━━━"
    echo "  # Generate some search traffic:"
    echo "  for term in charizard pikachu mewtwo blastoise; do"
    echo "    curl -s \"http://localhost:${API_PORT}/api/v1/cards/search?q=\${term}\" > /dev/null"
    echo "  done"
    echo ""
    echo "  # Generate some 404s:"
    echo "  for i in {1..5}; do curl -s http://localhost:${API_PORT}/nonexistent; done"
    echo ""
    echo "  # Then re-run this script to see them appear in the report"
}

main() {
    if [[ "${FOLLOW_MODE}" == "true" ]]; then
        follow_all_logs
    else
        generate_report
    fi
}

main "$@"
