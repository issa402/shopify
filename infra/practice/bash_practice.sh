#!/usr/bin/env bash
# ==============================================================================
# BASH PRACTICE: 5 Progressive Exercises - NOW WITH ACTUAL WORKING CODE
# PURPOSE: Learn bash by DOING — each exercise teaches one concept
# HOW TO USE:
#   bash infra/practice/bash_practice_fixed.sh 1    # Exercise 1
#   bash infra/practice/bash_practice_fixed.sh 2    # Exercise 2
#   bash infra/practice/bash_practice_fixed.sh all  # All exercises
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ============================================================
# EXERCISE 1: Variable Expansion — NOW WITH SOLUTIONS + CHALLENGES
# ============================================================
exercise_1_variables() {
    echo ""
    echo -e "${YELLOW}=== EXERCISE 1: Variable Expansion ===${NC}"
    echo ""
    
    local BINARY_PATH="/opt/pokevend/pokevend"
    local CONFIG_FILE="/etc/nexusos/config.env.bak.20260401"
    local VERSION="v1.2.3-beta"
    
    echo "SOLUTION: Extract filename from path"
    echo "  ${BINARY_PATH##*/}"
    echo ""
    echo "SOLUTION: Extract directory"
    echo "  ${BINARY_PATH%/*}"
    echo ""
    echo "SOLUTION: Extract extension"
    echo "  ${CONFIG_FILE##*.}"
    echo ""
    
    echo -e "${GREEN}CHALLENGES TO COMPLETE:${NC}"
    echo "  1. Extract 'pokevend' (binary name) from ${BINARY_PATH}"
    echo "  2. Extract 'config' from ${CONFIG_FILE} (no path, no ext)"
    echo "  3. Convert VERSION to lowercase"
    echo ""
}

# ============================================================
# EXERCISE 2: Loops + Associative Arrays
# ============================================================
exercise_2_loops() {
    echo ""
    echo -e "${YELLOW}=== EXERCISE 2: Loops + Arrays ===${NC}"
    echo ""
    
    declare -A SERVICE_PORTS
    SERVICE_PORTS["API"]=8080
    SERVICE_PORTS["Postgres"]=5432
    SERVICE_PORTS["Redis"]=6379
    SERVICE_PORTS["Qdrant"]=6333
    
    echo "Checking service connectivity..."
    printf "  %-15s %-8s %-10s\n" "SERVICE" "PORT" "STATUS"
    printf "  %-15s %-8s %-10s\n" "───────────────" "────────" "──────────"
    
    local open_count=0
    local total=${#SERVICE_PORTS[@]}
    
    for service in "${!SERVICE_PORTS[@]}"; do
        local port="${SERVICE_PORTS[$service]}"
        
        if nc -zw1 localhost "${port}" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} ${service:<13} ${port:<8} OPEN"
            ((open_count++))
        else
            echo -e "  ${RED}✗${NC} ${service:<13} ${port:<8} CLOSED"
        fi
    done
    
    echo ""
    echo "Summary: ${open_count}/${total} services responding"
    echo ""
    
    echo -e "${GREEN}CHALLENGE:${NC}"
    echo "  Add code to print health status:"
    echo "  - 'CRITICAL' if < 50% open"
    echo "  - 'WARNING' if < 80% open"
    echo "  - 'HEALTHY' if >= 80% open"
    echo ""
}

# ============================================================
# EXERCISE 3: grep, awk, sed (Text Processing)
# ============================================================
exercise_3_text_processing() {
    echo ""
    echo -e "${YELLOW}=== EXERCISE 3: Text Processing ===${NC}"
    echo ""
    
    echo "SOLUTION: Parse system memory"
    total_kb=$(grep "^MemTotal:" /proc/meminfo | awk '{print $2}')
    avail_kb=$(grep "^MemAvailable:" /proc/meminfo | awk '{print $2}')
    echo "  Total: $((total_kb / 1024)) MB"
    echo "  Available: $((avail_kb / 1024)) MB"
    echo ""
    
    echo "SOLUTION: Parse load average"
    read -r load1 load5 load15 _ < /proc/loadavg
    echo "  1-min: ${load1}  5-min: ${load5}  15-min: ${load15}"
    echo ""
    
    echo "SOLUTION: Find high-usage partitions"
    df -h | awk 'NR > 1 {
        usage = $5
        gsub(/%/, "", usage)
        if (usage + 0 > 50) {
            printf "  %-12s: %3s%% full\n", $6, usage
        }
    }' || echo "  (No partitions > 50% full)"
    echo ""
    
    echo -e "${GREEN}CHALLENGE:${NC}"
    echo "  Extend the disk check to alert on:"
    echo "  - CRITICAL if > 90% full"
    echo "  - WARNING if > 75% full"
    echo ""
}

# ============================================================
# EXERCISE 4: Functions — Reusable Code
# ============================================================
exercise_4_functions() {
    echo ""
    echo -e "${YELLOW}=== EXERCISE 4: Functions ===${NC}"
    echo ""
    
    # This function works NOW
    check_disk_space() {
        local path="$1"
        local min_gb="$2"
        
        local avail_gb
        avail_gb=$(df -BG "${path}" 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/G//')
        
        if (( avail_gb >= min_gb )); then
            echo -e "  ${GREEN}✓${NC} ${path}: ${avail_gb}GB available (need ${min_gb}GB)"
            return 0
        else
            echo -e "  ${RED}✗${NC} ${path}: only ${avail_gb}GB (need ${min_gb}GB)"
            return 1
        fi
    }
    
    echo "SOLUTION: Check disk space function"
    check_disk_space "/" 1 || true
    check_disk_space "/var" 1 || true
    echo ""
    
    echo -e "${GREEN}CHALLENGE:${NC}"
    echo "  Write function: validate_pokevend_deployment()"
    echo "  Must check:"
    echo "    1. Go compiler exists"
    echo "    2. Docker exists"
    echo "    3. At least 2GB free on /"
    echo "    4. Return 0 only if ALL pass"
    echo ""
}

# ============================================================
# EXERCISE 5: Real Deployment Script
# ============================================================
exercise_5_deployment() {
    echo ""
    echo -e "${YELLOW}=== EXERCISE 5: Real Deployment ===${NC}"
    echo ""
    
    local PROJECT_DIR="/home/iscjmz/shopify/shopify/Pokemon/server"
    
    echo "Phase 1: Pre-flight checks"
    
    if ! command -v go &>/dev/null; then
        echo -e "  ${RED}✗${NC} Go not installed"
        return 1
    fi
    echo -e "  ${GREEN}✓${NC} Go $(go version | awk '{print $3}')"
    
    if [[ ! -d "${PROJECT_DIR}" ]]; then
        echo -e "  ${RED}✗${NC} Project not found at ${PROJECT_DIR}"
        return 1
    fi
    echo -e "  ${GREEN}✓${NC} Project directory found"
    
    local avail_gb; avail_gb=$(df -BG / 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/G//')
    if (( avail_gb < 2 )); then
        echo -e "  ${RED}✗${NC} Insufficient space: ${avail_gb}GB (need 2GB)"
        return 1
    fi
    echo -e "  ${GREEN}✓${NC} Disk: ${avail_gb}GB available"
    echo ""
    
    echo "Phase 2: Build"
    local output_bin="/tmp/pokevend_test_build"
    
    if (cd "${PROJECT_DIR}" && go build -o "${output_bin}" >/dev/null 2>&1); then
        local size_kb; size_kb=$(stat -c%s "${output_bin}" 2>/dev/null | awk '{print int($1/1024)}')
        echo -e "  ${GREEN}✓${NC} Build successful (${size_kb}KB)"
    else
        echo -e "  ${RED}✗${NC} Build failed"
        return 1
    fi
    echo ""
    
    echo "✅ Deployment validation passed!"
    echo ""
    echo -e "${GREEN}CHALLENGE:${NC}"
    echo "  1. Create Docker image from binary"
    echo "  2. Generate /tmp/deployment_summary.txt"
    echo "  3. Add colored timestamp logging"
    echo ""
}

# ── Main ───────────────────────────────────────────────────────────────
main() {
    local ex="${1:-all}"
    case "${ex}" in
        1) exercise_1_variables ;;
        2) exercise_2_loops ;;
        3) exercise_3_text_processing ;;
        4) exercise_4_functions ;;
        5) exercise_5_deployment ;;
        all)
            exercise_1_variables
            exercise_2_loops
            exercise_3_text_processing
            exercise_4_functions
            exercise_5_deployment
            ;;
        *)
            echo "Usage: $0 [1|2|3|4|5|all]"
            exit 1
            ;;
    esac
}

main "$@"
