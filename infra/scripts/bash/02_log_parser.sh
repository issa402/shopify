#!/usr/bin/env bash
# ==============================================================================
# SCRIPT: 02_log_parser.sh
# MODULE: Week 2a — Bash Scripting Mastery
# READ FIRST: lessons/02_scripting_mastery.md § "The Holy Trinity: grep, awk, sed"
#
# WHAT THIS SCRIPT DOES (when complete):
#   Analyzes ALL NexusOS service logs in real-time. Extracts errors, slow
#   queries, top IPs, 4xx/5xx rates, and suspicious patterns. Outputs 
#   a structured analysis report. This is what a real on-call engineer
#   runs during an incident to understand what's happening.
#
# KEY CONCEPTS YOU WILL MASTER:
#   - Multi-stage bash pipelines (command | command | command)
#   - awk for column extraction and math
#   - sed for text transformation
#   - sort | uniq -c for frequency counting
#   - Process substitution diff <(cmd1) <(cmd2)
#   - Reading from journalctl, docker logs, and text files
#
# HOW TO RUN:
#   bash 02_log_parser.sh                    # Full report (last 1 hour)
#   bash 02_log_parser.sh --since "1h"      # Last hour specifically
#   bash 02_log_parser.sh --since "24h"     # Last 24 hours
#   bash 02_log_parser.sh --service pokevend # Only one service
#   bash 02_log_parser.sh --follow           # Real-time mode (like tail -f)
#
# WHEN YOU KNOW YOU'RE DONE:
#   Run it during normal operation — it should show 0 errors and normal traffic.
#   Then: curl localhost:8080/nonexistent-endpoint 30 times and re-run — you should 
#   see those 404s appear in your report.
# ==============================================================================

set -euo pipefail

# Source the utility library from task 2.1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./01_bash_fundamentals.sh
source "${SCRIPT_DIR}/01_bash_fundamentals.sh" 2>/dev/null || true  # OK if not done yet

# ── Configuration ──────────────────────────────────────────────────────────────
SINCE_DURATION="${SINCE_DURATION:-1h}"      # Default: last 1 hour
TARGET_SERVICE="${TARGET_SERVICE:-}"        # Empty = all services
FOLLOW_MODE=false

DOCKER_LOG_CONTAINERS=(
    "nexusos-postgres"
    "nexusos-redis"
    "nexusos-kafka"
    "nexusos-temporal"
    "nexusos-qdrant"
)

# ── Argument Parsing ──────────────────────────────────────────────────────────
parse_args() {
    # TODO: Parse the following arguments:
    # --since <duration>   (e.g. "1h", "24h", "7d")
    # --service <name>     (filter to one service)
    # --follow             (real-time mode)
    # Use while/case/shift pattern from lessons/02_scripting_mastery.md
    # YOUR CODE HERE
    :
}

# ── Log Collection ────────────────────────────────────────────────────────────

collect_journald_logs() {
    # Collect logs from systemd journal for managed services
    # Returns logs on stdout (can be piped to analysis functions)
    local service="${1:-pokevend}"
    
    # TODO: Use journalctl to collect logs
    # journalctl -u "${service}" --since "${SINCE_DURATION} ago" --no-pager -o short-iso
    # -o short-iso = ISO timestamp format (easier to parse)
    # --no-pager = print all lines, don't use less
    # YOUR CODE HERE
    :
}

collect_docker_logs() {
    # Collect logs from a docker container
    # Usage: collect_docker_logs nexusos-postgres
    local container="$1"
    
    # TODO: Use `docker logs` with the since flag
    # HINT: docker logs "${container}" --since "${SINCE_DURATION}" --timestamps 2>&1
    # 2>&1 merges stderr into stdout (some docker logs go to stderr)
    # YOUR CODE HERE
    :
}

# ── Analysis Functions ────────────────────────────────────────────────────────

analyze::error_count() {
    # Count the number of ERROR, FATAL, and PANIC messages in log stream
    # Usage: collect_journald_logs pokevend | analyze::error_count
    # Output: "ERROR: 12   FATAL: 0   PANIC: 0"
    
    # TODO: Read from stdin. Use grep -ciE for case-insensitive count.
    # HINT: 
    #   local log_data; log_data=$(cat)    # Read all stdin into variable
    #   local errors; errors=$(echo "${log_data}" | grep -ciE "^.*error" || echo 0)
    #   local fatals; fatals=$(echo "${log_data}" | grep -ciE "^.*fatal" || echo 0)
    #   echo "ERROR: ${errors}   FATAL: ${fatals}"
    # YOUR CODE HERE
    :
}

analyze::top_ips() {
    # Extract the top N most frequent IP addresses from an Nginx access log stream
    # Usage: cat /var/log/nginx/access.log | analyze::top_ips 10
    local top_n="${1:-10}"
    
    # TODO: Extract IPs (column $1 in Nginx logs) and count occurrences
    # PIPELINE:
    #   awk '{print $1}'     ← Extract first column (the IP address)
    #   | sort               ← Sort IPs alphabetically (needed for uniq to work)
    #   | uniq -c            ← Count duplicates (-c adds count prefix)
    #   | sort -rn           ← Sort by count, largest first (-r=reverse, -n=numeric)
    #   | head -${top_n}     ← Take top N
    # YOUR CODE HERE
    :
}

analyze::http_status_counts() {
    # Count HTTP status codes from Nginx access log
    # Groups them into: 2xx (success), 3xx (redirect), 4xx (client error), 5xx (server error)
    # Usage: cat access.log | analyze::http_status_counts
    
    # Nginx log format: IP - - [date] "METHOD URL HTTP/1.1" STATUS SIZE
    # STATUS is column $9 in the default Nginx combined log format
    
    # TODO:
    # 1. Use awk '{print $9}' to extract status codes
    # 2. Use awk again to bucket them into 2xx/3xx/4xx/5xx
    # ADVANCED HINT with awk:
    #   awk '{
    #     if ($9 ~ /^2/) twxx++
    #     else if ($9 ~ /^3/) thxx++
    #     else if ($9 ~ /^4/) foxx++
    #     else if ($9 ~ /^5/) fixx++
    #   } END {
    #     print "2xx:", twxx+0, "3xx:", thxx+0, "4xx:", foxx+0, "5xx:", fixx+0
    #   }'
    # YOUR CODE HERE
    :
}

analyze::slow_postgres_queries() {
    # Find queries that took longer than a threshold from PostgreSQL logs
    # PostgreSQL logs slow queries with "duration: XXX.XXX ms"
    # Usage: collect_docker_logs nexusos-postgres | analyze::slow_postgres_queries 100
    # Shows all queries that took > 100ms
    local threshold_ms="${1:-100}"
    
    # TODO: 
    # 1. Use grep to find lines containing "duration:"
    # 2. Use awk to extract the duration number and filter > threshold
    # HINT: 
    #   grep "duration:" |
    #   awk -v thresh="${threshold_ms}" '{
    #     # Find the field after "duration:"
    #     for(i=1; i<=NF; i++) {
    #       if ($i == "duration:") {
    #         ms = $(i+1)
    #         if (ms+0 > thresh) print "SLOW (" ms "ms):", $0
    #       }
    #     }
    #   }'
    # YOUR CODE HERE
    :
}

analyze::kafka_lag() {
    # Check Kafka consumer group lag from kafka container logs
    # High lag = consumers are falling behind = data processing delay
    # Usage: collect_docker_logs nexusos-kafka | analyze::kafka_lag
    
    # TODO: Look for lag-related log lines in Kafka output
    # Kafka logs consumer group lag with "currentLag" or "lag="
    # Extract and show any lag > 1000 messages
    # YOUR CODE HERE
    :
}

analyze::auth_failures() {
    # Find authentication failure patterns — potential brute force attacks
    # Usage: collect_journald_logs pokevend | analyze::auth_failures
    
    # TODO:
    # 1. grep for "unauthorized" or "401" or "invalid token" patterns
    # 2. Extract IP addresses from those lines (if present)
    # 3. Count failures per IP
    # 4. Flag any IP with > 10 failures in the time window
    # YOUR CODE HERE
    :
}

# ── Report Generator ──────────────────────────────────────────────────────────

print_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

generate_report() {
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║        NEXUSOS LOG ANALYSIS REPORT                   ║"
    echo "║        Period: Last ${SINCE_DURATION}                            ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo "  Generated: $(date --iso-8601=seconds)"
    
    # TODO: For each section below, call the appropriate collect + analyze functions
    
    print_section "1. POKEVEND API — Error Summary"
    # TODO: Collect pokevend logs and pipe to analyze::error_count
    # YOUR CODE HERE
    
    print_section "2. POKEVEND API — Auth Failures (Brute Force Detection)"
    # TODO: Collect pokevend logs and pipe to analyze::auth_failures
    # YOUR CODE HERE
    
    print_section "3. POSTGRESQL — Slow Queries (> 100ms)"
    # TODO: Collect postgres logs and pipe to analyze::slow_postgres_queries 100
    # YOUR CODE HERE
    
    print_section "4. KAFKA — Consumer Lag"
    # TODO: Collect kafka logs and pipe to analyze::kafka_lag
    # YOUR CODE HERE
    
    print_section "5. ALL CONTAINERS — Error Summary"
    # TODO: Loop through DOCKER_LOG_CONTAINERS
    # For each: collect logs, count error lines, print summary row
    # YOUR CODE HERE
    
    print_section "6. RECOMMENDATIONS"
    # TODO: Based on findings:
    # If error count > 0 → "Review application logs immediately"
    # If slow queries found → "Add database indexes or optimize queries"
    # If auth failures found → "Consider enabling fail2ban"
    # YOUR CODE HERE
}

# ── Real-Time Follow Mode ─────────────────────────────────────────────────────
follow_logs() {
    # Follow ALL service logs in real-time, highlighting errors
    # This is `tail -f` on steroids — multiple sources, highlighted, filtered
    
    # TODO: Use `journalctl -f` and `docker logs -f` piped through grep with color
    # CHALLENGE: Use process substitution to merge multiple log streams:
    # cat <(journalctl -u pokevend -f -o short-iso) <(docker logs nexusos-postgres -f 2>&1) |
    #   grep --line-buffered -E "*(ERROR|FATAL|WARN)*" | 
    #   GREP_COLOR='01;31' grep --color=always -E "ERROR|FATAL|$"
    # YOUR CODE HERE
    :
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    parse_args "$@"
    
    if [[ "${FOLLOW_MODE}" == "true" ]]; then
        follow_logs
    else
        generate_report
    fi
}

main "$@"
