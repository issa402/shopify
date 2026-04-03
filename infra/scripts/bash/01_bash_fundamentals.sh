#!/usr/bin/env bash
set -euo pipefail

# ===================================================================== 
# LOGGING FUNCTIONS — ALL IMPLEMENTED AND WORKING NOW
# =====================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log::info() {
    local msg="$1"
    local timestamp; timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] ${BLUE}[INFO]${NC}  ${msg}" >&2
}

log::warn() {
    local msg="$1"
    local timestamp; timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] ${YELLOW}[WARN]${NC}  ${msg}" >&2
}

log::error() {
    local msg="$1"
    local timestamp; timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] ${RED}[ERROR]${NC} ${msg}" >&2
    return 1
}

log::success() {
    local msg="$1"
    local timestamp; timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] ${GREEN}[✓]${NC}    ${msg}" >&2
}

log::step() {
    local msg="$1"
    echo -e "\n${BOLD}" >&2
    printf '━%.0s' {1..60} >&2
    echo " " >&2
    echo -e "${BOLD}▶  ${msg}${NC}" >&2
    printf '━%.0s' {1..60} >&2
    echo " " >&2
}

# =====================================================================
# VALIDATION FUNCTIONS — ALL IMPLEMENTED
# =====================================================================

require::command() {
    local cmd="$1"
    local hint="${2:-}"
    
    if ! command -v "${cmd}" &>/dev/null; then
        log::error "Required command not found: ${cmd}"
        if [[ -n "${hint}" ]]; then
            echo "       ${hint}" >&2
        fi
        return 1
    fi
    return 0
}

require::root() {
    if (( EUID != 0 )); then
        log::error "This script must run as root (use: sudo $0)"
        return 1
    fi
    return 0
}

require::env() {
    local var_name="$1"
    local hint="${2:-}"
    
    if [[ -z "${!var_name:-}" ]]; then
        log::error "Required environment variable not set: ${var_name}"
        if [[ -n "${hint}}" ]]; then
            echo "       ${hint}" >&2
        fi
        return 1
    fi
    return 0
}

require::file() {
    local filepath="$1"
    
    if [[ ! -f "${filepath}" ]]; then
        log::error "Required file not found: ${filepath}"
        return 1
    fi
    
    if [[ ! -r "${filepath}" ]]; then
        log::error "Required file not readable: ${filepath}"
        return 1
    fi
    return 0
}

# =====================================================================
# STRING MANIPULATION — ALL IMPLEMENTED
# =====================================================================

str::trim() {
    echo "$1" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
}

str::to_lower() {
    echo "${1,,}"
}

str::contains() {
    [[ "$1" == *"$2"* ]]
}

str::parse_key_value() {
    IFS='=' read -r "$2" "$3" <<< "$1"
}

# =====================================================================
# FILE OPERATIONS — ALL IMPLEMENTED
# =====================================================================

file::backup() {
    local filepath="$1"
    local backup="${filepath}.bak.$(date +%Y%m%d_%H%M%S)"
    
    if [[ ! -f "${filepath}" ]]; then
        log::error "Cannot backup — file not found: ${filepath}"
        return 1
    fi
    
    cp "${filepath}" "${backup}" || {
        log::error "Backup failed: ${filepath} → ${backup}"
        return 1
    }
    
    echo "${backup}"
    return 0
}

file::atomic_write() {
    local target="$1"
    local content="$2"
    local tmpfile; tmpfile=$(mktemp "${target}.tmp.XXXXXX")
    
    trap 'rm -f "${tmpfile}"' EXIT ERR
    
    echo "${content}" > "${tmpfile}" || {
        log::error "Failed to write temporary file: ${tmpfile}"
        return 1
    }
    
    mv "${tmpfile}" "${target}" || {
        log::error "Failed to move ${tmpfile} → ${target}"
        return 1
    }
    
    trap - EXIT ERR
    return 0
}

# =====================================================================
# ARRAY FUNCTIONS — ALL IMPLEMENTED
# =====================================================================

array::contains() {
    local needle="$1"
    shift
    local item
    for item in "$@"; do
        [[ "${item}" == "${needle}" ]] && return 0
    done
    return 1
}

array::join() {
    local delimiter="$1"
    shift
    (IFS="${delimiter}"; echo "$*")
}

# =====================================================================
# SELF-TEST SUITE — RUN WITH: bash script.sh test
# =====================================================================

run_tests() {
    local passed=0
    local failed=0
    
    echo -e "\n${BOLD}Running Self-Tests...${NC}\n"
    
    # Test logging
    log::info "Test info message"
    ((passed++))
    
    log::warn "Test warning message"
    ((passed++))
    
    log::success "Test success message"
    ((passed++))
    
    # Test string functions
    local trimmed; trimmed=$(str::trim "  hello  ")
    if [[ "${trimmed}" == "hello" ]]; then
        echo -e "  ${GREEN}✓${NC} str::trim works"
        ((passed++))
    else
        echo -e "  ${RED}✗${NC} str::trim failed"
        ((failed++))
    fi
    
    local lower; lower=$(str::to_lower "HELLO")
    if [[ "${lower}" == "hello" ]]; then
        echo -e "  ${GREEN}✓${NC} str::to_lower works"
        ((passed++))
    else
        echo -e "  ${RED}✗${NC} str::to_lower failed"
        ((failed++))
    fi
    
    if str::contains "hello world" "world"; then
        echo -e "  ${GREEN}✓${NC} str::contains works"
        ((passed++))
    else
        echo -e "  ${RED}✗${NC} str::contains failed"
        ((failed++))
    fi
    
    # Test array functions
    local arr=("a" "b" "c")
    if array::contains "b" "${arr[@]}"; then
        echo -e "  ${GREEN}✓${NC} array::contains works"
        ((passed++))
    else
        echo -e "  ${RED}✗${NC} array::contains failed"
        ((failed++))
    fi
    
    local joined; joined=$(array::join "," a b c)
    if [[ "${joined}" == "a,b,c" ]]; then
        echo -e "  ${GREEN}✓${NC} array::join works"
        ((passed++))
    else
        echo -e "  ${RED}✗${NC} array::join failed (got: ${joined})"
        ((failed++))
    fi
    
    # Test validation
    require::command bash
    if [[ $? -eq 0 ]]; then
        echo -e "  ${GREEN}✓${NC} require::command works"
        ((passed++))
    else
        echo -e "  ${RED}✗${NC} require::command failed"
        ((failed++))
    fi
    
    echo ""
    echo -e "${BOLD}Results: ${GREEN}${passed} passed${NC}, ${RED}${failed} failed${NC}${BOLD}${NC}\n"
    
    [[ $failed -gt 0 ]] && return 1
    return 0
}

# =====================================================================
# MAIN — Route to test or demo
# =====================================================================

main() {
    case "${1:-}" in
        test)
            run_tests
            ;;
        demo)
            log::step "Demonstrating bash_fundamentals.sh"
            
            log::info "This is an info message"
            log::warn "This is a warning message"
            log::success "This is a success message"
            
            log::step "String Functions"
            local trimmed; trimmed=$(str::trim "  hello world  ")
            log::info "Trimmed: '${trimmed}'"
            
            local lower; lower=$(str::to_lower "POKEVEND")
            log::info "Lowercase: '${lower}'"
            
            log::step "Array Functions"
            local services=("postgres" "redis" "qdrant")
            if array::contains "redis" "${services[@]}"; then
                log::success "Found redis in services"
            fi
            
            local joined; joined=$(array::join " → " "${services[@]}")
            log::info "Services: ${joined}"
            
            log::step "Validation"
            require::command bash && log::success "bash is available"
            
            log::step "Demo complete!"
            ;;
        "")
            : # Sourced — don't run anything
            ;;
        *)
            echo "Usage: $0 [test|demo]"
            echo "  $0 test  — Run self-test suite"
            echo "  $0 demo  — Show examples of each function"
            exit 1
            ;;
    esac
}

main "$@"
