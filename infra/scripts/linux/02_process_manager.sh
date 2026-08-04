#!/usr/bin/env bash
# ==============================================================================
# SCRIPT: 02_process_manager.sh
# MODULE: Week 1 — Linux System Administration
# READ FIRST: lessons/01_linux_mastery.md § PART 3 (Processes & Systemd)
#
# WHAT THIS SCRIPT DOES (when complete):
#   A complete service lifecycle manager for the NexusOS/Pokevend stack.
#   Supports start, stop, restart, status, and log-viewing operations.
#   Handles both systemd services AND docker-compose services in one tool.
#
# WHY THIS MATTERS:
#   This is EXACTLY what an on-call engineer runs at 3 AM when their phone
#   rings. Having a single, reliable tool to manage all services means less
#   time panicking and more time fixing.
#
# HOW TO RUN:
#   bash 02_process_manager.sh status
#   bash 02_process_manager.sh restart pokevend
#   bash 02_process_manager.sh logs pokevend 100
#   bash 02_process_manager.sh docker-status
#
# WHEN YOU KNOW YOU'RE DONE:
#   Each subcommand works correctly. You understand the difference between
#   `systemctl restart` and `docker-compose restart` and why they exist.
# ==============================================================================

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
# These are the systemd services this script manages
# If pokevend.service doesn't exist yet, it will skip it gracefully
MANAGED_SERVICES=("pokevend" "nginx" "postgresql" "redis")

# The location of your docker-compose file
COMPOSE_FILE="/home/iscjmz/shopify/shopify/docker-compose.yml"

# ── Helper Functions ────────────────────────────────────────────────────────────

usage() {
    # TODO: Print a helpful usage message showing all valid subcommands
    # Make it look professional — use echo statements showing examples
    # Pattern:
    #   Usage: $0 <command> [arguments]
    #   Commands:
    #     status              - Show status of all services
    #     start <service>     - Start a specific service
    #     ...
    # YOUR CODE HERE
    exit 1
}

log_info()  { echo "[$(date '+%H:%M:%S')] [INFO]  $*"; }
log_error() { echo "[$(date '+%H:%M:%S')] [ERROR] $*" >&2; }
log_warn()  { echo "[$(date '+%H:%M:%S')] [WARN]  $*"; }

# ── Command: status ────────────────────────────────────────────────────────────
# Show the status of all managed systemd services in a clean table
cmd_status() {
    log_info "=== SYSTEMD SERVICE STATUS ==="
    
    # TODO 1: Loop over MANAGED_SERVICES array and for each service:
    #   - Get its status with: systemctl is-active <service>
    #   - Print whether it's active (print [OK]) or not (print [WARN])
    # HINT: 
    #   for service in "${MANAGED_SERVICES[@]}"; do
    #     status=$(systemctl is-active "${service}" 2>/dev/null || echo "not-found")
    #     ...
    #   done
    # YOUR CODE HERE

    # TODO 2: Add a blank line then show Docker container states too
    # Use: docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    # YOUR CODE HERE
}

# ── Command: start <service> ────────────────────────────────────────────────────
cmd_start() {
    local service="${1:-}"
    
    # TODO 1: Validate that a service name was provided
    # If service is empty, call usage and exit
    # HINT: if [[ -z "${service}" ]]; then ... fi
    # YOUR CODE HERE

    log_info "Starting service: ${service}"
    
    # TODO 2: Check if this is a systemd service or a docker service
    # Strategy: if systemctl list-units --type=service "${service}.service" has output → systemd
    # Otherwise → try docker-compose start
    # HINT: 
    #   if systemctl list-unit-files "${service}.service" &>/dev/null; then
    #     sudo systemctl start "${service}"
    #   else
    #     docker-compose -f "${COMPOSE_FILE}" start "${service}"
    #   fi
    # YOUR CODE HERE

    # TODO 3: After starting, wait 2 seconds then check the status to confirm it started
    # HINT: sleep 2 && systemctl is-active "${service}"
    # YOUR CODE HERE
}

# ── Command: restart <service> ─────────────────────────────────────────────────
cmd_restart() {
    local service="${1:-}"
    
    # TODO 1: Validate service name was provided
    # YOUR CODE HERE

    log_info "Restarting service: ${service}"
    
    # TODO 2: Implement restart (similar to start but using systemctl restart)
    # IMPORTANT: For production systems, some services need special handling.
    # For nginx: use `nginx -t` first to TEST the config before restarting
    # If the test fails, DO NOT restart (it would bring down the live server!)
    # HINT:
    #   if [[ "${service}" == "nginx" ]]; then
    #     if sudo nginx -t; then
    #       sudo systemctl restart nginx
    #     else
    #       log_error "nginx config test failed! Not restarting."
    #       exit 1
    #     fi
    #   fi
    # YOUR CODE HERE

    # TODO 3: Check status after restart
    # YOUR CODE HERE
}

# ── Command: logs <service> [lines] ────────────────────────────────────────────
cmd_logs() {
    local service="${1:-}"
    local lines="${2:-50}"    # Default to 50 lines if not specified
    
    # TODO 1: Validate service name
    # YOUR CODE HERE

    log_info "Showing last ${lines} lines for: ${service}"
    
    # TODO 2: Determine if this is a systemd or docker service
    # For systemd: use journalctl -u "${service}" -n "${lines}" --no-pager
    # For docker: use docker logs "${service}" --tail "${lines}"
    # YOUR CODE HERE
}

# ── Command: docker-status ─────────────────────────────────────────────────────
cmd_docker_status() {
    log_info "=== DOCKER CONTAINER HEALTH ==="
    
    # TODO 1: Show all containers (running AND stopped)
    # HINT: docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    # YOUR CODE HERE

    # TODO 2: Show resource usage for running containers
    # HINT: docker stats --no-stream
    # YOUR CODE HERE

    # TODO 3: Check health of specific critical containers by calling their healthcheck
    # For each container, run: docker inspect --format='{{.State.Health.Status}}' <name>
    # If health is not "healthy", print a WARNING
    critical_containers=("nexusos-postgres" "nexusos-redis" "nexusos-qdrant")
    
    # HINT:
    # for container in "${critical_containers[@]}"; do
    #   health=$(docker inspect --format='{{.State.Health.Status}}' "${container}" 2>/dev/null || echo "not-found")
    #   case "${health}" in
    #     "healthy")   log_info "${container}: healthy" ;;
    #     "unhealthy") log_error "${container}: UNHEALTHY!" ;;
    #     *)           log_warn "${container}: ${health}" ;;
    #   esac
    # done
    # YOUR CODE HERE
}

# ── Main: Route to the right subcommand ────────────────────────────────────────
main() {
    # TODO: Parse the first argument as the command and route to the right function
    # If no command is given, call usage
    # HINT: Use a case statement:
    #   local command="${1:-}"
    #   shift || true   # Remove the first arg from $@
    #   case "${command}" in
    #     status)        cmd_status ;;
    #     start)         cmd_start "$@" ;;
    #     restart)       cmd_restart "$@" ;;
    #     logs)          cmd_logs "$@" ;;
    #     docker-status) cmd_docker_status ;;
    #     *)             usage ;;
    #   esac
    # YOUR CODE HERE
    usage
}

main "$@"
