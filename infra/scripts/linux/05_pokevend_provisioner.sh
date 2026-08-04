#!/usr/bin/env bash
# ==============================================================================
# SCRIPT: 05_pokevend_provisioner.sh
# MODULE: Week 1 CAPSTONE — Linux System Administration
# READ FIRST: lessons/01_linux_mastery.md — ALL PARTS
# PREREQUISITE: Complete tasks 1.1 through 1.4 first
#
# WHAT THIS SCRIPT DOES (when complete):
#   Takes a BARE Ubuntu 22.04 machine and transforms it into a fully
#   production-ready Pokevend host in a single run. This is called
#   "server provisioning" and it is one of the core skills of an  
#   Infrastructure Engineer.
#
#   After running this script, the machine will have:
#     ✅ pokevend-svc system user (locked down, no shell)
#     ✅ /opt/pokevend/ directory owned by root, binary deployed there
#     ✅ /var/log/pokevend/ owned by pokevend-svc
#     ✅ /etc/pokevend/config.env with proper permissions (640)
#     ✅ pokevend.service registered with systemd and running
#     ✅ Nightly database backup cron job installed
#     ✅ SSH hardening applied
#     ✅ UFW firewall enabled with minimal allowed ports
#
# WHY THIS SCRIPT IS THE MOST IMPORTANT THING YOU'LL WRITE:
#   This is "Infrastructure as Code" at the OS level. Netflix, Google,
#   Amazon — they all have versions of this. It's called a "bootstrapper"
#   or "user-data script" in cloud environments. When AWS Auto-Scaling
#   spins up a new EC2 instance, it runs something exactly like this.
#
# HOW TO RUN:
#   # ALWAYS dry-run first
#   sudo bash 05_pokevend_provisioner.sh --dry-run
#   # Then apply for real
#   sudo bash 05_pokevend_provisioner.sh
#   # With custom binary path
#   sudo bash 05_pokevend_provisioner.sh --binary /path/to/pokevend
#
# WHEN YOU KNOW YOU'RE DONE:
#   Run the script on a clean system (or in a Docker container):
#     docker run -it --rm ubuntu:22.04 bash
#     # Copy script in, run it, verify all the above bullets are true
#   If you can run this script 10 times and get the same result every
#   time = IDEMPOTENCY. That's the gold standard.
# ==============================================================================

set -euo pipefail

# ── Constants — The Single Source of Truth ─────────────────────────────────────
# NEVER hardcode paths in multiple places. Define them ONCE here.
# If the path needs to change, change it HERE and only here.

SERVICE_USER="pokevend-svc"
SERVICE_GROUP="pokevend-svc"

APP_DIR="/opt/pokevend"           # Binary lives here
CONFIG_DIR="/etc/pokevend"        # Config/secrets live here
LOG_DIR="/var/log/pokevend"       # Log files go here
BACKUP_DIR="/var/backups/pokevend"# DB backups go here

BINARY_SRC="${BINARY_SRC:-}"      # Source binary path (set via --binary flag)
BINARY_DEST="${APP_DIR}/pokevend" # Where we install the binary
CONFIG_FILE="${CONFIG_DIR}/config.env"
SYSTEMD_SERVICE="/etc/systemd/system/pokevend.service"
CRON_FILE="/etc/cron.d/pokevend-backup"

DRY_RUN=false
APP_PORT=8080

# ── Logging & Helpers ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'

info()     { echo -e "${GREEN}[PROVISION]${NC} $*"; }
warn()     { echo -e "${YELLOW}[WARN]${NC}     $*"; }
error()    { echo -e "${RED}[ERROR]${NC}    $*" >&2; }
step()     { echo -e "\n${BOLD}━━━ STEP: $* ━━━${NC}"; }
dry_run()  { echo -e "${YELLOW}[DRY-RUN]${NC}  Would: $*"; }

run() {
    # Wrapper for all commands — in dry-run mode, print but don't execute
    # Usage: run sudo useradd -r pokevend-svc
    # This is the KEY pattern for safe infrastructure scripts
    if [[ "${DRY_RUN}" == "true" ]]; then
        dry_run "$*"
    else
        "$@"
    fi
}

# ── Argument Parsing ──────────────────────────────────────────────────────────
parse_args() {
    # TODO: Loop through all arguments ($@) and handle:
    #   --dry-run         → set DRY_RUN=true
    #   --binary <path>   → set BINARY_SRC to the next argument
    #   --port <number>   → set APP_PORT
    #   --help            → print usage and exit 0
    # HINT: Use a while loop with shift:
    #   while [[ $# -gt 0 ]]; do
    #     case "$1" in
    #       --dry-run)  DRY_RUN=true; shift ;;
    #       --binary)   BINARY_SRC="$2"; shift 2 ;;
    #       ...
    #     esac
    #   done
    # YOUR CODE HERE
    :
}

# ── Preflight Checks ──────────────────────────────────────────────────────────
preflight_checks() {
    step "Preflight Checks"
    
    # TODO 1: Verify the script is running as root
    # HINT: Check if EUID == 0. If not, print error and exit 1.
    # WHY: useradd, systemctl, and chmod to /etc all require root
    # YOUR CODE HERE

    # TODO 2: Verify we're on Ubuntu/Debian (use /etc/os-release)
    # HINT: source /etc/os-release && if [[ "${ID}" != "ubuntu" && "${ID}" != "debian" ]]
    # WHY: This script uses apt. On CentOS/RHEL you'd use dnf. Be explicit.
    # YOUR CODE HERE

    # TODO 3: Check if required commands exist (command -v for each)
    # Required: systemctl, useradd, chmod, chown, crontab
    # HINT: Create an array of required commands, loop and check each one
    # YOUR CODE HERE

    # TODO 4: If BINARY_SRC is set, verify the file exists and is executable
    # HINT: if [[ -n "${BINARY_SRC}" ]] && [[ ! -f "${BINARY_SRC}" ]]; then ...
    # YOUR CODE HERE

    info "Preflight checks passed"
}

# ── Step 1: Create the Service User ───────────────────────────────────────────
create_service_user() {
    step "Creating Service User: ${SERVICE_USER}"
    
    # TODO 1: Check if the user already exists (id command)
    # If it already exists, print "user already exists, skipping" and return
    # WHY: Idempotency — running the script twice shouldn't fail
    # HINT: if id "${SERVICE_USER}" &>/dev/null; then info "User exists"; return; fi
    # YOUR CODE HERE

    # TODO 2: Create the system user
    # Flags needed: --system, --no-create-home, --shell /bin/false, --comment "..."
    # LOOK UP: man useradd — understand what each flag does
    # run useradd ...
    # YOUR CODE HERE

    info "Created user: ${SERVICE_USER}"
}

# ── Step 2: Create Directories with Correct Permissions ───────────────────────
create_directories() {
    step "Creating Directories"
    
    # TODO: For EACH directory below, create it and set ownership + permissions
    # Think carefully about WHO should own each dir and what permissions make sense
    
    # /opt/pokevend/ — The binary lives here
    # Owner: root (so pokevend-svc can't replace its own binary — security!)
    # Permissions: 755 (root can rwx, others can r-x → can execute binary but not write)
    # YOUR CODE HERE

    # /etc/pokevend/ — Config and secrets live here
    # Owner: root, Group: pokevend-svc
    # Permissions: 750 (root rwx, group r-x, others nothing)
    # YOUR CODE HERE

    # /var/log/pokevend/ — Service writes logs here
    # Owner: pokevend-svc (the service must be able to write its own logs)
    # Permissions: 755
    # YOUR CODE HERE

    # /var/backups/pokevend/ — Encrypted DB backups go here
    # Owner: root (only root can access backups — security)
    # Permissions: 700
    # YOUR CODE HERE

    info "Directories created with correct permissions"
}

# ── Step 3: Deploy the Binary ──────────────────────────────────────────────────
deploy_binary() {
    step "Deploying Binary"
    
    if [[ -z "${BINARY_SRC}" ]]; then
        warn "No binary provided (--binary flag). Building from source..."
        
        # TODO: Build the Go binary from the project source
        # HINT: Navigate to the Go project directory and run go build
        # The project is at: /home/iscjmz/shopify/shopify/Pokemon/server/
        # Output the binary to: ${BINARY_DEST}
        # Command: go build -o "${BINARY_DEST}" ./...
        # YOUR CODE HERE
    else
        # Copy the provided binary
        run cp "${BINARY_SRC}" "${BINARY_DEST}"
    fi
    
    # TODO: Set correct permissions on the binary
    # Owner: root (pokevend-svc cannot modify its own binary)
    # Permissions: 755 (world-executable so pokevend-svc can RUN it)
    # YOUR CODE HERE

    info "Binary deployed to: ${BINARY_DEST}"
}

# ── Step 4: Write Configuration File ──────────────────────────────────────────
write_config() {
    step "Writing Configuration"
    
    # If config already exists in a real system, preserve it
    if [[ -f "${CONFIG_FILE}" ]]; then
        warn "Config file already exists at ${CONFIG_FILE}. Skipping."
        return
    fi
    
    # TODO: Use a heredoc to write the config.env file
    # IMPORTANT: The file should contain PLACEHOLDER VALUES only
    # Never write real secrets in a provisioning script!
    # The operator must fill in real values after provisioning.
    # HINT:
    # run bash -c "cat <<'EOF' > ${CONFIG_FILE}
    # # Pokevend Production Config — Fill in real values!
    # APP_PORT=8080
    # DB_HOST=localhost
    # DB_PORT=5432
    # DB_NAME=pokevend
    # DB_USER=CHANGE_ME
    # DB_PASSWORD=CHANGE_ME_USE_STRONG_PASSWORD
    # REDIS_ADDR=localhost:6379
    # JWT_SECRET=CHANGE_ME_USE_OPENSSL_RAND_BASE64_64
    # EOF"
    # YOUR CODE HERE

    # TODO: Set strict permissions on the config file
    # Owner: root, Group: pokevend-svc
    # Permissions: 640 (owner rw, group r, others NOTHING)
    # This means root can edit secrets, pokevend-svc can READ them, nobody else
    # YOUR CODE HERE

    info "Config template written to: ${CONFIG_FILE}"
    warn "ACTION REQUIRED: Edit ${CONFIG_FILE} and fill in real values before starting service"
}

# ── Step 5: Install Systemd Service ───────────────────────────────────────────
install_systemd_service() {
    step "Installing systemd Service"
    
    # TODO: Write the systemd service file using a heredoc
    # Review lessons/01_linux_mastery.md "Anatomy of a Systemd Service File"
    # Requirements for the service file:
    #   [Unit]
    #     - Description and After=network.target
    #   [Service]
    #     - Type=simple
    #     - User=${SERVICE_USER}
    #     - Group=${SERVICE_GROUP}
    #     - WorkingDirectory=${APP_DIR}
    #     - ExecStart=${BINARY_DEST}
    #     - EnvironmentFile=${CONFIG_FILE}
    #     - Restart=always
    #     - RestartSec=5s
    #     - LimitNOFILE=65536   (critical for high-concurrency Go servers)
    #     - StandardOutput=journal
    #   [Install]
    #     - WantedBy=multi-user.target
    # YOUR CODE HERE

    # TODO: Reload systemd, enable and start the service
    # After writing a .service file you MUST reload systemd daemon
    # Then enable (start on boot) and start (start now)
    # run systemctl daemon-reload
    # run systemctl enable pokevend
    # run systemctl start pokevend (skip if DRY_RUN since binary may not be real)
    # YOUR CODE HERE

    info "pokevend.service installed and enabled"
}

# ── Step 6: Install Backup Cron Job ───────────────────────────────────────────
install_backup_cron() {
    step "Installing Backup Cron Job"
    
    # TODO: Write a cron job file to /etc/cron.d/pokevend-backup
    # It should run the storage audit backup script nightly at 2:30 AM
    # Cron format: minute hour day month weekday user command
    # 30 2 * * * root python3 /path/to/03_storage_audit.py --backup >> /var/log/pokevend/backup.log 2>&1
    # YOUR CODE HERE

    info "Backup cron job installed: nightly at 02:30"
}

# ── Step 7: Verify the Installation ───────────────────────────────────────────
verify_installation() {
    step "Verifying Installation"
    
    local errors=0
    
    verify_item() {
        # Helper to check a condition and count failures
        # Usage: verify_item "description" <condition_command>
        if "$@" &>/dev/null; then
            echo -e "  ${GREEN}✓${NC} $1"
        else
            echo -e "  ${RED}✗${NC} $1"
            ((errors++))
        fi
    }
    
    # TODO: Verify each item that should have been created
    # Use verify_item with these checks:
    # 1. Service user exists: id "${SERVICE_USER}"
    # 2. App directory exists: test -d "${APP_DIR}"
    # 3. Config file exists: test -f "${CONFIG_FILE}"
    # 4. Config file is NOT world-readable: ! test -r /proc/1/root/.../config.env
    #    HINT: Use stat --format="%a" "${CONFIG_FILE}" and check it's "640"
    # 5. Systemd service file exists: test -f "${SYSTEMD_SERVICE}"
    # 6. Service is enabled: systemctl is-enabled pokevend
    # 7. Cron job file exists: test -f "${CRON_FILE}"
    # YOUR CODE HERE

    if [[ $errors -gt 0 ]]; then
        error "${errors} verification checks FAILED. Review output above."
        exit 1
    fi
    
    info "All verification checks passed ✓"
}

# ── Main Orchestrator ──────────────────────────────────────────────────────────
main() {
    echo -e "${BOLD}"
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║       POKEVEND PRODUCTION PROVISIONER                 ║"
    echo "║       Infrastructure as Code — OS Layer               ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    parse_args "$@"
    
    [[ "${DRY_RUN}" == "true" ]] && warn "DRY-RUN MODE — No changes will be made\n"
    
    # TODO: Call each step function in order
    # preflight_checks
    # create_service_user
    # create_directories
    # deploy_binary
    # write_config
    # install_systemd_service
    # install_backup_cron
    # verify_installation
    # YOUR CODE HERE (uncomment lines above)
    
    echo ""
    if [[ "${DRY_RUN}" == "true" ]]; then
        info "DRY-RUN complete. Re-run without --dry-run to provision for real."
    else
        info "Provisioning complete!"
        echo ""
        warn "NEXT STEPS:"
        warn "  1. Edit ${CONFIG_FILE} — fill in real DB password, JWT secret"
        warn "  2. Generate secrets: openssl rand -base64 64"
        warn "  3. Start the service: sudo systemctl start pokevend"
        warn "  4. Check status: sudo systemctl status pokevend"
        warn "  5. Watch logs: sudo journalctl -u pokevend -f"
    fi
}

main "$@"
