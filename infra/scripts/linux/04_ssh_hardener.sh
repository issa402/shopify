#!/usr/bin/env bash
# ==============================================================================
# SCRIPT: 04_ssh_hardener.sh
# MODULE: Week 1 — Linux System Administration
# READ FIRST: lessons/01_linux_mastery.md § PART 5 (SSH)
#
# WHAT THIS SCRIPT DOES (when complete):
#   Audits and hardens the SSH daemon configuration to industry-standard
#   security settings. Generates an SSH key pair for the pokevend-svc
#   service account. Creates a detailed report of changes made.
#
# WHY THIS IS CRITICAL:
#   SSH is usually the first thing attackers try. Bad SSH config =
#   password brute-force attacks succeed. Root access via SSH =
#   game over. This script applies the changes that prevent 99% of
#   automated SSH attacks.
#
# ⚠️  DANGER WARNING:
#   Misonfiguring SSH can lock you out of a remote server PERMANENTLY.
#   Always test with: "sshd -t" before restarting sshd.
#   Always have a backup connection open.
#   Run this on your LOCAL machine only (not a remote server) until
#   you understand exactly what every line does.
#
# HOW TO RUN (dry-run mode first!):
#   bash 04_ssh_hardener.sh --dry-run   # Just show what would change
#   sudo bash 04_ssh_hardener.sh        # Actually apply changes
#
# WHEN YOU KNOW YOU'RE DONE:
#   You can explain what every sshd_config setting does from memory.
#   The dry-run shows only secure settings being applied.
# ==============================================================================

set -euo pipefail

DRY_RUN=false
SSHD_CONFIG="/etc/ssh/sshd_config"
SSHD_CONFIG_BACKUP="/etc/ssh/sshd_config.bak.$(date +%Y%m%d_%H%M%S)"
LOG_FILE="/var/log/pokevend/ssh_hardening.log"

# ── Argument Parsing ──────────────────────────────────────────────────────────
# TODO: Check if "--dry-run" is in the arguments ($@)
# If so, set DRY_RUN=true and print a clear banner that we're in dry-run mode
# HINT: for arg in "$@"; do if [[ "${arg}" == "--dry-run" ]]; then DRY_RUN=true; fi; done
# YOUR CODE HERE

# ── Helpers ───────────────────────────────────────────────────────────────────
log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "${LOG_FILE}"; }

apply_setting() {
    # Apply or update a setting in sshd_config
    # Usage: apply_setting "PermitRootLogin" "no"
    # This function should:
    #   1. Check if the setting already exists (grep)
    #   2. If DRY_RUN=true, just print "Would set: KEY = VALUE"
    #   3. If DRY_RUN=false:
    #      - If key exists: use sed to replace the line
    #      - If key doesn't exist: append it
    
    local key="$1"
    local value="$2"
    
    # TODO: Implement this function
    # HINT for checking if key exists:
    #   if grep -qE "^#?${key}" "${SSHD_CONFIG}"; then
    #     # key exists (maybe commented out) — replace the line
    #     sed -i "s|^#\?${key}.*|${key} ${value}|" "${SSHD_CONFIG}"
    #   else
    #     # key doesn't exist — append it
    #     echo "${key} ${value}" >> "${SSHD_CONFIG}"
    #   fi
    # YOUR CODE HERE
    :
}

# ── Step 1: Backup the current SSH config ─────────────────────────────────────
backup_sshd_config() {
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "[DRY-RUN] Would backup ${SSHD_CONFIG} to ${SSHD_CONFIG_BACKUP}"
        return
    fi
    
    # TODO: Copy the current sshd_config to the backup path
    # This is your safety net — if something goes wrong, restore it with:
    # sudo cp BACKUP_PATH /etc/ssh/sshd_config
    # YOUR CODE HERE
    log "Config backed up to: ${SSHD_CONFIG_BACKUP}"
}

# ── Step 2: Apply hardened settings ───────────────────────────────────────────
harden_ssh_config() {
    log "=== Applying SSH hardening settings ==="
    
    # TODO: Use the apply_setting function to apply each of these settings.
    # For each one, read the comment explaining WHY this setting exists.
    
    # 1. Disable root login over SSH
    # WHY: Attackers always try root first. Disabling it eliminates the attack vector.
    # If you need root, SSH as your user then `sudo su`
    # YOUR CODE HERE: apply_setting "PermitRootLogin" "no"

    # 2. Disable password authentication
    # WHY: Passwords can be brute-forced. Keys cannot (mathematically impossible with strong keys).
    # Attackers run automated scripts trying millions of passwords per second.
    # YOUR CODE HERE: apply_setting "PasswordAuthentication" "no"

    # 3. Enable public key authentication
    # WHY: This is the ONLY authentication method we allow after disabling passwords
    # YOUR CODE HERE: apply_setting "PubkeyAuthentication" "yes"

    # 4. Disable empty passwords
    # WHY: A user with no password is a security catastrophe
    # YOUR CODE HERE: apply_setting "PermitEmptyPasswords" "no"

    # 5. Limit auth attempts
    # WHY: Limits brute force even if someone somehow tries passwords
    # YOUR CODE HERE: apply_setting "MaxAuthTries" "3"

    # 6. Disconnect idle sessions
    # WHY: A forgotten open SSH session = open door. Auto-close after 10 min idle.
    # ClientAliveInterval: send keepalive every 300 seconds
    # ClientAliveCountMax: if 2 keepalives ignored, disconnect (300*2 = 10 min total)
    # YOUR CODE HERE: apply_setting "ClientAliveInterval" "300"
    # YOUR CODE HERE: apply_setting "ClientAliveCountMax" "2"

    # 7. Only allow SSH Protocol 2
    # WHY: Protocol 1 has known cryptographic vulnerabilities. Always use 2.
    # YOUR CODE HERE: apply_setting "Protocol" "2"

    # 8. Disable X11 forwarding
    # WHY: X11 has known security issues. We're a server team, we don't need GUI forwarding.
    # YOUR CODE HERE: apply_setting "X11Forwarding" "no"

    # 9. Disable agent forwarding (unless you specifically need it)
    # WHY: Agent forwarding can be exploited by a compromised intermediate server
    # YOUR CODE HERE: apply_setting "AllowAgentForwarding" "no"

    # 10. Set log level to VERBOSE (so you can see WHO authenticated and when)
    # WHY: Forensics. If a breach happens, VERBOSE logs tell you exactly what happened.
    # YOUR CODE HERE: apply_setting "LogLevel" "VERBOSE"
}

# ── Step 3: Test the new config before applying ───────────────────────────────
test_sshd_config() {
    log "=== Testing sshd config syntax ==="
    
    # TODO: Run `sshd -t` to test the config file for syntax errors
    # This is like running `nginx -t` before restarting nginx — ALWAYS do this
    # If it fails, restore the backup and exit!
    # HINT:
    #   if ! sudo sshd -t; then
    #     log "ERROR: sshd config test FAILED. Restoring backup..."
    #     sudo cp "${SSHD_CONFIG_BACKUP}" "${SSHD_CONFIG}"
    #     exit 1
    #   fi
    # YOUR CODE HERE
    :
}

# ── Step 4: Generate SSH keys for the service account ─────────────────────────
generate_service_keys() {
    log "=== Generating SSH key for pokevend-svc ==="
    
    local key_dir="/home/pokevend-svc/.ssh"
    local key_file="${key_dir}/id_ed25519"
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "[DRY-RUN] Would generate ed25519 key at ${key_file}"
        return
    fi
    
    # TODO 1: Create the .ssh directory with correct permissions
    # CRITICAL: .ssh directories MUST be mode 700 (only owner can access)
    # HINT: sudo mkdir -p "${key_dir}" && sudo chmod 700 "${key_dir}"
    # YOUR CODE HERE

    # TODO 2: Generate an ed25519 key pair (better than RSA in 2024)
    # -t ed25519 = algorithm, -N "" = empty passphrase (for service accounts)
    # -C = comment (human-readable label for the key)
    # HINT: sudo ssh-keygen -t ed25519 -N "" -C "pokevend-svc@$(hostname)" -f "${key_file}"
    # YOUR CODE HERE

    # TODO 3: Set correct key permissions
    # Private key: 600 (only owner can read — NEVER share this)
    # Public key: 644 (anyone can read — it's meant to be distributed)
    # YOUR CODE HERE

    # TODO 4: Set ownership to pokevend-svc
    # HINT: sudo chown -R pokevend-svc:pokevend-svc "${key_dir}"
    # YOUR CODE HERE

    log "Public key: $(sudo cat ${key_file}.pub)"
}

# ── Step 5: Show a diff of changes ────────────────────────────────────────────
show_changes() {
    if [[ -f "${SSHD_CONFIG_BACKUP}" ]]; then
        log "=== Configuration Changes (diff) ==="
        # TODO: Show the diff between the backup and the new config
        # This lets you verify exactly what changed
        # HINT: diff "${SSHD_CONFIG_BACKUP}" "${SSHD_CONFIG}" || true
        # (|| true prevents set -e from exiting on diff's exit code 1)
        # YOUR CODE HERE
        :
    fi
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    log "Starting SSH hardening. DRY_RUN=${DRY_RUN}"
    
    # TODO: Call the functions in correct order:
    # 1. backup_sshd_config
    # 2. harden_ssh_config
    # 3. test_sshd_config (skip if DRY_RUN)
    # 4. generate_service_keys
    # 5. show_changes
    # YOUR CODE HERE

    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY-RUN complete. No changes were made."
        log "Review the output above, then run without --dry-run to apply."
    else
        log "SSH hardening complete."
        log "⚠️  IMPORTANT: Restart sshd to apply: sudo systemctl restart sshd"
        log "⚠️  Keep this terminal open and test SSH login in a NEW terminal first!"
    fi
}

main "$@"
