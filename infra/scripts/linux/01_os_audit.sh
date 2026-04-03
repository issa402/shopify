#!/usr/bin/env bash
# ==============================================================================
# SCRIPT: 01_os_audit.sh
# MODULE: Week 1 — Linux System Administration
# READ FIRST: infra/lessons/01_linux_mastery.md → PART 1 & 2
#
# WHAT THIS SCRIPT DOES (when complete):
#   Performs a comprehensive audit of the host OS and produces a structured
#   report showing users, running services, disk usage, open ports, and
#   the current Docker container state. This is the exact report an
#   Infrastructure Engineer produces when onboarding to a new system.
#
# WHY THIS MATTERS:
#   Before you can secure or improve anything, you must KNOW what's there.
#   "Know your terrain." — Every battle plan starts with recon.
#
# HOW TO RUN:
#   bash infra/scripts/linux/01_os_audit.sh
#   bash infra/scripts/linux/01_os_audit.sh 2>&1 | tee /tmp/audit_report.txt
#
# WHEN YOU KNOW YOU'RE DONE:
#   The script produces a clean, readable report covering all sections below
#   without any errors. You can explain what every single command does.
# ==============================================================================

set -euo pipefail  # NEVER remove these. See lesson §Bash Safety

# ── Color output helpers (make the report readable) ──────────────────────────
# ANSI escape codes — \033[...m sets terminal color
# 0m = reset, 1m = bold, 32m = green, 33m = yellow, 34m = blue, 31m = red
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'  # NC = No Color (reset)

print_header() {
    # Print a section header. Called like: print_header "Section Name"
    # TODO: Echo the section name with BOLD+BLUE formatting and a line of dashes
    # HINT: echo -e "${BOLD}${BLUE}=== $1 ===${NC}"
    # YOUR CODE HERE
    echo -e "${BOLD}${BLUE}=== $1 ===${NC}"
}

print_ok() {
    echo -e "  ${GREEN}[OK]${NC} $1"
}

print_warn() {
    echo -e "  ${YELLOW}[WARN]${NC} $1"
}

print_critical() {
    echo -e "  ${RED}[CRITICAL]${NC} $1"
}

# ── SECTION 1: System Identity ────────────────────────────────────────────────
# Goal: Know what machine you're looking at, who's running this script, and uptime
# Lesson reference: lessons/01_linux_mastery.md § "Practice Commands"
audit_system_identity() {
    print_header "SYSTEM IDENTITY"
    
    # WHY: Before you can fix a system, you MUST know what it is
    # - Different OSes, kernel versions, architectures require different approaches
    # - Load average tells you at a glance if the system is stressed
    
    echo "  Kernel & Architecture:"
    uname -a | sed 's/^/    /'
    
    echo ""
    echo "  OS Distribution:"
    if [ -f /etc/os-release ]; then
        grep PRETTY_NAME /etc/os-release | cut -d'=' -f2 | tr -d '"' | sed 's/^/    /'
    else
        echo "    [Unknown — /etc/os-release not found]"
    fi
    
    echo ""
    echo "  System Uptime & Load Average:"
    uptime | sed 's/^/    /'
    # EXPLANATION: Load average of 2.5 on a 4-core CPU = 62% utilized
    # Load > number_of_cores = system is overloaded
    
    echo ""
    echo "  Current Timestamp (UTC):"
    date --iso-8601=seconds | sed 's/^/    /'
    
    echo ""
    echo "  Currently Logged In Users:"
    who 2>/dev/null | while read user; do echo "    $user"; done
    if ! who &>/dev/null; then
        echo "    [No tty users currently logged in]"
    fi
}

# ── SECTION 2: User & Permission Audit ───────────────────────────────────────
# Goal: Find all human users, check for dangerous sudo access, find world-writable files
# Lesson reference: lessons/01_linux_mastery.md § PART 2 (Users, Groups & Permissions)
audit_users() {
    print_header "USER & PERMISSION AUDIT"

    # TODO 1: List all users who have an actual login shell (not /bin/false or /usr/sbin/nologin)
    # HINT: grep -v "nologin\|/bin/false" /etc/passwd | cut -d: -f1
    # These are the users who can actually log in — you want to know all of them
    # YOUR CODE HERE

    # TODO 2: List all sudoers (users who can become root)
    # HINT: The sudoers file is at /etc/sudoers. But also check /etc/sudoers.d/
    # WARNING: Use `sudo cat` — this requires root. What happens if you run without root?
    # YOUR CODE HERE

    # TODO 3: Check if the UID 0 user account is ONLY root (there should only be one)
    # HINT: awk -F: '($3 == "0") {print $1}' /etc/passwd
    # If you see ANYTHING other than "root" here, that's a CRITICAL security finding
    # YOUR CODE HERE

    # TODO 4: Find files that are world-writable (anyone can modify them — security risk)
    # HINT: find / -maxdepth 5 -perm -002 -type f 2>/dev/null | grep -v /proc
    # -perm -002 means "world-writable bit is set"
    # YOUR CODE HERE

    # TODO 5: Check if the pokevend-svc user exists (should from provisioning)
    # HINT: id pokevend-svc returns 0 if user exists, 1 if not
    # Use an if statement to print_ok or print_warn
    # YOUR CODE HERE
}

# ── SECTION 3: Services & Process Audit ──────────────────────────────────────
# Goal: Know what is running, and what is LISTENING for network connections
# Lesson reference: lessons/01_linux_mastery.md § PART 3 (Processes & Systemd)
audit_processes() {
    print_header "SERVICES & PROCESS AUDIT"

    # TODO 1: List all systemd services that are currently ACTIVE and RUNNING
    # HINT: systemctl list-units --type=service --state=running --no-pager --no-legend
    # The output has columns: UNIT, LOAD, ACTIVE, SUB, DESCRIPTION
    # YOUR CODE HERE

    # TODO 2: Show the top 10 processes by memory consumption
    # HINT: ps aux --sort=-%mem | head -11
    # Column meanings: PID, %CPU, %MEM, COMMAND
    # YOUR CODE HERE

    # TODO 3: List all TCP ports that are actively LISTENING for connections
    # HINT: ss -tlnp
    # -t = TCP only, -l = listening only, -n = show port numbers (not service names), -p = process
    # YOUR CODE HERE

    # TODO 4: Check if the pokevend service is running via systemctl
    # If it's not running, this should print a warning
    # HINT: systemctl is-active pokevend returns "active" or "inactive" or "failed"
    # YOUR CODE HERE
}

# ── SECTION 4: Storage & Disk Audit ──────────────────────────────────────────
# Goal: Know if you're about to run out of disk space (which crashes everything)
# Lesson reference: lessons/01_linux_mastery.md § PART 4 (Storage)
audit_storage() {
    print_header "STORAGE AUDIT"

    # TODO 1: Show disk usage for all mounted filesystems in human-readable format
    # HINT: df -h
    # Pay attention to the "Use%" column — anything > 85% is a WARNING
    # Anything > 95% is CRITICAL (databases will start failing)
    # YOUR CODE HERE

    # TODO 2: Find any filesystem over 80% full and print a WARNING
    # HINT: df -h | awk 'NR>1 {gsub(/%/,""); if ($5+0 > 80) print "WARN: " $6 " is " $5 "% full"}'
    # NR>1 skips the header line. gsub removes the % sign. +0 converts string to number.
    # YOUR CODE HERE

    # TODO 3: Show the top 5 largest directories in /var/log (logs love to fill disks)
    # HINT: du -sh /var/log/* 2>/dev/null | sort -rh | head -5
    # YOUR CODE HERE

    # TODO 4: Check if /var/backups/pokevend exists and show its size
    # This is where our database backups should live
    # YOUR CODE HERE
}

# ── SECTION 5: Docker Infrastructure Audit ───────────────────────────────────
# Goal: Know the state of all containers and their resource usage
# Lesson reference: lessons/01_linux_mastery.md + docker compose inspection
audit_docker() {
    print_header "DOCKER INFRASTRUCTURE AUDIT"

    # TODO 1: Check if Docker is running (if not, print CRITICAL and return early)
    # HINT: command -v docker returns 0 if docker exists
    # Or: docker info &>/dev/null — returns non-zero if Docker daemon is not running
    # YOUR CODE HERE

    # TODO 2: List all running containers with their CPU and Memory usage
    # HINT: docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
    # --no-stream = print once and exit (don't follow)
    # YOUR CODE HERE

    # TODO 3: Check for any containers with status "Exited" (crashed containers)
    # HINT: docker ps -a --filter "status=exited" --format "{{.Names}} exited"
    # -a = show ALL containers (not just running ones)
    # If you find any, print a WARNING — they shouldn't be stopped
    # YOUR CODE HERE

    # TODO 4: Show the NexusOS network configuration
    # HINT: docker network inspect nexusos-network --format '{{json .IPAM.Config}}' 2>/dev/null
    # YOUR CODE HERE
}

# ── MAIN: Run all audit sections ──────────────────────────────────────────────
main() {
    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║     NEXUSOS INFRASTRUCTURE AUDIT REPORT     ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
    echo -e "Generated: $(date --iso-8601=seconds)"
    echo ""

    # TODO: Call each audit function in order
    # audit_system_identity
    # audit_users
    # audit_processes
    # audit_storage
    # audit_docker
    # YOUR CODE HERE (uncomment the above lines to enable each section)

    echo ""
    echo -e "${GREEN}${BOLD}Audit complete. Review any [WARN] or [CRITICAL] findings above.${NC}"
}

# Call main to kick off the script
main "$@"
