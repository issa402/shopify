# 🗺️ START HERE — COMPLETE NAVIGATION MAP
## NexusOS Infrastructure Engineering Mastery Program
### Everything you need to go from zero to cracked in 5 weeks

---

> **THIS IS YOUR DAILY DRIVER. Bookmark it. Open it first every single session.**
> Every file, every lesson, every task — listed here in exact execution order.
> When you sit down to work, open this file, find where you left off, go.

---

## 📁 EVERYTHING THAT EXISTS — FULL INVENTORY

```
shopify/shopify/infra/
│
├── START_HERE.md                    ← YOU ARE HERE (this file)
├── MASTER_INDEX.md                  ← Weekly schedule overview
│
├── lessons/                         ← READ BEFORE EACH WEEK'S SCRIPTS
│   ├── 01_linux_mastery.md          ← Week 1 reference (12,977 bytes of pure knowledge)
│   ├── 02_scripting_mastery.md      ← Week 2 reference (Python + Bash deep dive)
│   ├── 03_networking_mastery.md     ← Week 3 reference (OSI, TCP, DNS, Nginx)
│   ├── 04_cybersecurity_mastery.md  ← Week 4 reference (Zero Trust, Firewalls, IDS)
│   └── 05_cloud_mastery.md          ← Week 5 reference (AWS, Terraform, Observability)
│
└── scripts/
    ├── linux/                        ← Week 1 Tasks (ACTIVE — START HERE)
    │   ├── 01_os_audit.sh           ← Task 1.1: Audit the whole OS
    │   ├── 02_process_manager.sh    ← Task 1.2: Manage services (systemd + docker)
    │   ├── 03_storage_audit.py      ← Task 1.3: Disk usage + DB backup tool
    │   ├── 04_ssh_hardener.sh       ← Task 1.4: Harden SSH config
    │   └── 05_pokevend_provisioner.sh ← Task 1.5: CAPSTONE — Full server setup
    │
    ├── bash/                         ← Week 2a Tasks (Bash)
    │   ├── 01_bash_fundamentals.sh  ← Task 2.1: Bash strict mode, variables, functions
    │   ├── 02_log_parser.sh         ← Task 2.2: grep+awk+sed log analysis pipeline
    │   └── 03_cron_scheduler.sh     ← Task 2.3: Automate everything with cron
    │
    ├── python/                       ← Week 2b Tasks (Python)
    │   ├── 01_system_probe.py       ← Task 2.4: Python OS system introspection
    │   ├── 02_config_manager.py     ← Task 2.5: YAML/JSON config parser + validator
    │   └── 03_deploy_orchestrator.py ← Task 2.6: CAPSTONE — Full CI/CD pipeline
    │
    ├── network/                      ← Week 3 Tasks
    │   ├── 01_port_scanner.py       ← Task 3.1: Scan all NexusOS service ports
    │   ├── 02_firewall_hardener.sh  ← Task 3.2: UFW zero-trust setup
    │   ├── 03_nginx_configurator.sh ← Task 3.3: Nginx reverse proxy + TLS
    │   ├── 04_dns_resolver.py       ← Task 3.4: Docker service DNS + health
    │   └── 05_network_validator.py  ← Task 3.5: CAPSTONE — Full stack network test
    │
    ├── security/                     ← Week 4 Tasks
    │   ├── 01_secrets_auditor.py    ← Task 4.1: Scan for exposed credentials
    │   ├── 02_ids_monitor.py        ← Task 4.2: Build an IDS — watch logs for attacks
    │   ├── 03_docker_hardener.sh    ← Task 4.3: Harden all docker-compose services
    │   ├── 04_vuln_scanner.py       ← Task 4.4: Dependency + image vulnerability scan
    │   └── 05_security_audit.py     ← Task 4.5: CAPSTONE — Full security policy report
    │
    └── cloud/                        ← Week 5 Tasks
        ├── 01_terraform_plan/        ← Task 5.1: Write AWS VPC + EC2 Terraform
        │   ├── main.tf
        │   ├── variables.tf
        │   ├── outputs.tf
        │   └── README.md
        ├── 02_prometheus_metrics.go  ← Task 5.2: Add Prometheus metrics to Go API
        ├── 03_grafana_dashboard.json ← Task 5.3: Build Grafana dashboard as code
        ├── 04_log_aggregator.py      ← Task 5.4: Structured log parser + analyzer
        └── 05_load_tester.py         ← Task 5.5: CAPSTONE — Load test + Incident Report
```

---

## 🚀 EXACT EXECUTION ORDER — DO THIS IN ORDER, NO SKIPPING

### 📌 WEEK 1: Linux System Administration

#### Before you write a single line of code:
```bash
# Run these right now in your terminal and READ every output
uname -a                                          # What OS/kernel are you on?
cat /etc/os-release                               # What distro?
uptime                                            # Load average (is machine stressed?)
free -h                                           # How much RAM is free?
df -h                                             # How full is the disk?
id                                                # Who are you?
ss -tlnp                                          # What's already listening?
docker ps                                         # What containers are running?
docker-compose -f shopify/docker-compose.yml ps   # NexusOS stack state?
```
**If you can explain every output line = you're ready. If not, re-read lesson 01.**

---

#### ✅ TASK 1.1 — `scripts/linux/01_os_audit.sh`
**What it does:** Comprehensive OS audit — users, services, disk, processes, docker state
**What you learn:** Linux filesystem, user model, ps/ss/df commands, bash control flow
**Prerequisite reading:** `lessons/01_linux_mastery.md` PART 1 + PART 2 + PART 3
**Time estimate:** 2-3 hours
**How to run when done:**
```bash
bash infra/scripts/linux/01_os_audit.sh
bash infra/scripts/linux/01_os_audit.sh 2>&1 | tee /tmp/audit_$(date +%Y%m%d).txt
```
**You pass when:** Script runs clean, produces a structured report, you can explain every command

---

#### ✅ TASK 1.2 — `scripts/linux/02_process_manager.sh`
**What it does:** Full service lifecycle manager for systemd services + docker containers
**What you learn:** systemctl commands, case statements in bash, docker ps/logs, argument routing
**Prerequisite reading:** `lessons/01_linux_mastery.md` PART 3 (Processes & Systemd)
**Time estimate:** 2-3 hours
**How to run when done:**
```bash
bash infra/scripts/linux/02_process_manager.sh status
bash infra/scripts/linux/02_process_manager.sh logs nexusos-postgres 100
bash infra/scripts/linux/02_process_manager.sh docker-status
```
**You pass when:** Every subcommand works and you haven't hardcoded anything

---

#### ✅ TASK 1.3 — `scripts/linux/03_storage_audit.py`
**What it does:** Disk monitoring + automated PostgreSQL backup with compression
**What you learn:** Python subprocess module, pathlib, argparse, error handling, database backups
**Prerequisite reading:** `lessons/01_linux_mastery.md` PART 4 + `lessons/02_scripting_mastery.md` PART 2
**Time estimate:** 3-4 hours
**How to run when done:**
```bash
python3 infra/scripts/linux/03_storage_audit.py
python3 infra/scripts/linux/03_storage_audit.py --output json
python3 infra/scripts/linux/03_storage_audit.py --backup
```
**You pass when:** JSON output works, backup creates a `.sql.gz` file, disk alerts fire correctly

---

#### ✅ TASK 1.4 — `scripts/linux/04_ssh_hardener.sh`
**What it does:** Audits SSH config, applies hardening settings, generates service account keys
**What you learn:** sshd_config settings, sed in-place editing, key pair generation, dry-run pattern
**Prerequisite reading:** `lessons/01_linux_mastery.md` PART 5 (SSH)
**⚠️ WARNING:** Run `--dry-run` first ALWAYS
**Time estimate:** 2-3 hours
**How to run when done:**
```bash
bash infra/scripts/linux/04_ssh_hardener.sh --dry-run   # ALWAYS first
sudo bash infra/scripts/linux/04_ssh_hardener.sh        # Apply if dry-run looks good
```
**You pass when:** Dry-run shows all 10 settings, config test passes, keys generated

---

#### 🏆 TASK 1.5 (CAPSTONE) — `scripts/linux/05_pokevend_provisioner.sh`
**What it does:** Turns a bare Ubuntu machine into a production-ready Pokevend host. One script.
**What you learn:** Everything from Week 1 combined. This is a real-world provisioning script.
**Prerequisite:** Complete ALL of 1.1 through 1.4 first
**Time estimate:** 4-6 hours
**How to run when done:**
```bash
bash infra/scripts/linux/05_pokevend_provisioner.sh --dry-run
sudo bash infra/scripts/linux/05_pokevend_provisioner.sh
```
**You pass when:** A fresh directory + this script = running Pokevend service, locked-down user, backups scheduled

---

### 📌 WEEK 2: Python & Bash Scripting

#### Before you write a single line of code:
```bash
# Verify your environment
python3 --version && python3 -c "import subprocess,os,json,pathlib,argparse,logging; print('ALL GOOD')"
bash --version
shellcheck --version   # Install: sudo apt install shellcheck
# Run ShellCheck on your Week 1 scripts!
shellcheck infra/scripts/linux/01_os_audit.sh
```

---

#### ✅ TASK 2.1 — `scripts/bash/01_bash_fundamentals.sh`
**What it does:** A library of bash utility functions used by ALL other scripts in this project
**What you learn:** Functions, arrays, string manipulation, error handling, heredocs, traps
**Key concept:** The `trap` command — run cleanup code even when script fails/is killed
**Prerequisite reading:** `lessons/02_scripting_mastery.md` PART 1
**Time estimate:** 2-3 hours
**How to run when done:**
```bash
bash infra/scripts/bash/01_bash_fundamentals.sh test   # Runs self-test suite
source infra/scripts/bash/01_bash_fundamentals.sh      # Makes functions available to other scripts
```

---

#### ✅ TASK 2.2 — `scripts/bash/02_log_parser.sh`
**What it does:** Real-time NexusOS log analyzer — finds errors, extracts slow queries, builds report
**What you learn:** grep -E, awk column extraction, sed substitution, sort | uniq -c pipelines, process substitution
**Key concept:** Piping programs together vs reading files — why pipelines are more powerful
**Prerequisite reading:** `lessons/02_scripting_mastery.md` PART 1 "The Holy Trinity"
**Time estimate:** 3-4 hours
**Challenge:** Find the top 10 IP addresses hitting your API and the exact endpoints they hit

---

#### ✅ TASK 2.3 — `scripts/bash/03_cron_scheduler.sh`
**What it does:** Installs all your scripts as cron jobs — automates the entire monitoring suite
**What you learn:** crontab syntax, cron timing expressions, environment in crone, stderr redirect
**Key concept:** Cron jobs run with minimal environment. Your scripts must be self-contained.
**Prerequisite reading:** `lessons/02_scripting_mastery.md` PART 1
**Time estimate:** 1-2 hours
**Cron expression practice:**
```
# ┌────── minute (0-59)
# │ ┌──── hour (0-23)
# │ │ ┌── day of month (1-31)
# │ │ │ ┌ month (1-12)
# │ │ │ │ ┌ day of week (0-6, 0=Sun)
# * * * * *  command

*/5 * * * *    # Every 5 minutes
0 */4 * * *    # Every 4 hours
0 2 * * *      # Daily at 2:00 AM
0 2 * * 0      # Every Sunday at 2:00 AM
0 0 1 * *      # First day of every month at midnight
```

---

#### ✅ TASK 2.4 — `scripts/python/01_system_probe.py`
**What it does:** Deep system profiler — reads /proc files directly, no external deps
**What you learn:** Reading virtual filesystems (/proc/meminfo, /proc/stat, /proc/net/tcp), parsing raw system data
**Key concept:** /proc is not real files — it's the kernel talking to you
**Prerequisite reading:** `lessons/02_scripting_mastery.md` PART 2
**Time estimate:** 3-4 hours
**Challenge:** Calculate actual CPU usage % by reading /proc/stat twice and calculating the delta

---

#### ✅ TASK 2.5 — `scripts/python/02_config_manager.py`
**What it does:** Validates and manages configuration for all NexusOS services
**What you learn:** YAML parsing (PyYAML), JSON Schema validation, environment variable injection, config diffing
**Key concepts:** What happens when a service starts with the WRONG config? Config validation prevents production disasters
**Prerequisite reading:** `lessons/02_scripting_mastery.md` PART 2 + PART 3
**Time estimate:** 3-4 hours

---

#### 🏆 TASK 2.6 (CAPSTONE) — `scripts/python/03_deploy_orchestrator.py`
**What it does:** A full CI/CD pipeline in Python — build, test, deploy, verify, rollback
**What you learn:** Everything from Week 2 combined. Pipeline design, rollback logic, deployment strategies
**This is what GitHub Actions, Jenkins, and ArgoCD do — you're building one from scratch**
**Time estimate:** 5-8 hours
**Stages it implements:**
```
Stage 1: Pre-flight checks (DB connection, Redis, disk space)
Stage 2: Build Go binary (go build)
Stage 3: Run tests (go test ./...)
Stage 4: Backup database before deploying
Stage 5: Deploy binary (stop → replace → start)
Stage 6: Health check verification
Stage 7: Rollback if health check fails
```

---

### 📌 WEEK 3: Networking & Protocols

#### Before you write a single line of code:
```bash
# Understand what's on your network RIGHT NOW
ss -tlnp                                  # All listening ports
docker network ls                         # Docker networks
docker network inspect nexusos-network    # NexusOS container IPs
dig google.com                           # DNS working?
curl -v http://localhost:8080/health     # Is Pokevend API up?
```

---

#### ✅ TASK 3.1 — `scripts/network/01_port_scanner.py`
**What it does:** Scans all expected NexusOS service ports, tests TCP connectivity, reports state
**What you learn:** Python socket module, TCP connection testing, concurrent scanning with threading
**Key concept:** The difference between "port is open" and "service is healthy"
**Time estimate:** 3-4 hours

---

#### ✅ TASK 3.2 — `scripts/network/02_firewall_hardener.sh`
**What it does:** Implements zero-trust UFW rules for the NexusOS stack
**What you learn:** UFW commands, iptables concepts, deny-by-default policy, allowlist rules
**Key concept:** Every port NOT in the allowlist must be provably unreachable
**⚠️ WARNING:** Test with `--dry-run` first. Lock yourself out = bad day.
**Time estimate:** 2-3 hours

---

#### ✅ TASK 3.3 — `scripts/network/03_nginx_configurator.sh`
**What it does:** Generates and deploys Nginx config as reverse proxy for Pokevend with TLS
**What you learn:** Nginx config syntax, self-signed cert generation, upstream proxy, rate limiting
**Time estimate:** 3-4 hours

---

#### ✅ TASK 3.4 — `scripts/network/04_dns_resolver.py`
**What it does:** Validates Docker service DNS resolution and inter-container connectivity
**What you learn:** How Docker DNS works, Python socket.getaddrinfo(), container networking
**Time estimate:** 2-3 hours

---

#### 🏆 TASK 3.5 (CAPSTONE) — `scripts/network/05_network_validator.py`
**What it does:** End-to-end network validation — port scan, DNS, HTTP, TLS, latency measurement
**What you learn:** Full network stack testing from the outside in
**Time estimate:** 4-5 hours
**It validates:**
```
✅ All expected ports are listening
✅ All Docker services can see each other by name (DNS)
✅ Nginx is correctly forwarding to Go API
✅ TLS certificate is valid and not expiring soon
✅ Response times are under thresholds (< 100ms for health endpoint)
✅ Rate limiting is working (fire 200 requests, check 429s appear)
```

---

### 📌 WEEK 4: Cybersecurity

#### ✅ TASK 4.1 — `scripts/security/01_secrets_auditor.py`
**What it does:** Scans the ENTIRE repository for accidentally exposed credentials
**What you learn:** Regex patterns for credential detection, git history scanning, risk scoring
**Time estimate:** 3-4 hours
**It detects:**
```
- Hardcoded passwords (password = "something")
- AWS keys (AKIA...)
- Private keys (BEGIN PRIVATE KEY)
- JWT secrets hardcoded in source
- Database connection strings with passwords
- OpenAI / Stripe API keys
```

---

#### ✅ TASK 4.2 — `scripts/security/02_ids_monitor.py`
**What it does:** Real-time log monitor that detects intrusion patterns and fires alerts
**What you learn:** Pattern matching in Python, file tail (like `tail -f`), alert throttling
**This IS what Fail2Ban does internally — you're building a mini version**
**Time estimate:** 4-5 hours
**Detects:**
```
- SSH brute force (> 5 failures from same IP in 60 seconds)
- API auth brute force (> 20 401s from same IP in 60 seconds)  
- Port scanning (connection attempts to multiple closed ports)
- SQL injection attempts in API logs
```

---

#### ✅ TASK 4.3 — `scripts/security/03_docker_hardener.sh`
**What it does:** Audits docker-compose.yml against security best practices and outputs a report
**What you learn:** Docker security flags, read-only containers, capability dropping, resource limits
**Time estimate:** 2-3 hours

---

#### ✅ TASK 4.4 — `scripts/security/04_vuln_scanner.py`
**What it does:** Scans Go + Python dependencies for known CVEs, scans Docker images
**What you learn:** govulncheck, pip-audit, Trivy, CVE scoring, remediation prioritization
**Time estimate:** 2-3 hours

---

#### 🏆 TASK 4.5 (CAPSTONE) — `scripts/security/05_security_audit.py`
**What it does:** Generates a full ISO-27001-style security audit report for NexusOS
**What you learn:** Security reporting, risk scoring, remediation planning, executive summaries
**Time estimate:** 6-8 hours
**Report covers:**
```
SECTION 1: Access Control (users, passwords, SSH keys)
SECTION 2: Network Security (firewall, exposed ports, TLS)
SECTION 3: Application Security (dependency CVEs, secrets, auth)
SECTION 4: Container Security (docker hardening score)
SECTION 5: Data Security (backup status, encryption)
SECTION 6: Monitoring & Incident Response (logging, alerting)
OVERALL RISK SCORE: 0-100
```

---

### 📌 WEEK 5: Cloud & Observability

#### ✅ TASK 5.1 — `scripts/cloud/01_terraform_plan/`
**What it does:** Full AWS VPC architecture for NexusOS in production (Terraform IaC)
**What you learn:** Terraform HCL syntax, AWS VPC/subnets/EC2/RDS, state management
**Time estimate:** 5-6 hours

---

#### ✅ TASK 5.2 — `scripts/cloud/02_prometheus_metrics.go`
**What it does:** Adds production-grade Prometheus metrics to the Pokevend Go API
**What you learn:** Counter vs Gauge vs Histogram, labeling, middleware instrumentation
**Time estimate:** 3-4 hours

---

#### ✅ TASK 5.3 — `scripts/cloud/03_grafana_dashboard.json`
**What it does:** A pre-built Grafana dashboard for NexusOS (import directly into Grafana)
**What you learn:** Dashboard-as-code, PromQL queries, visualization types, alerting rules
**Time estimate:** 3-4 hours

---

#### ✅ TASK 5.4 — `scripts/cloud/04_log_aggregator.py`
**What it does:** Collects, parses, and indexes structured logs from all NexusOS services
**What you learn:** Structured logging, log parsing, time-series analysis, Python generators
**Time estimate:** 3-4 hours

---

#### 🏆 TASK 5.5 (CAPSTONE) — `scripts/cloud/05_load_tester.py`
**What it does:** Load tests the full NexusOS stack, finds breaking points, generates Incident Report
**What you learn:** Load testing methodology, concurrent HTTP (asyncio), percentile analysis, RCA writing
**Time estimate:** 5-6 hours
**The loop:**
```
1. Run load test (100 concurrent users, ramp up slowly)
2. Watch Prometheus metrics live during the test
3. Find the exact request rate where errors start appearing
4. Identify the bottleneck (DB? Redis? CPU? Memory?)
5. Write a full Incident Report with root cause and fix
```

---

## 🧠 MENTAL FRAMEWORK — HOW TO THINK LIKE AN INFRA ENGINEER

### When ANYTHING breaks, ask in this order:

```
1. IS IT UP?       → ping, curl /health, systemctl status
2. IS IT LISTENING? → ss -tlnp | grep <port>
3. IS IT CRASHING?  → journalctl -u service -n 50
4. IS IT FULL?      → df -h, free -h
5. IS IT SLOW?      → top, iostat, pg_stat_activity
6. IS IT BLOCKED?   → ufw status, iptables -L, tcpdump
7. IS IT WRONG?     → diff current_config known_good_config
```

### Layers of the Stack (Debug Bottom-Up):

```
6. Application (Pokevend API, Python AI service)
5. Containers  (Docker, docker-compose)
4. Process     (systemd, PID, user)
3. Network     (TCP ports, firewall, DNS)
2. OS          (Linux users, filesystem, memory)
1. Hardware    (CPU, RAM, disk, NIC)

If Layer 2 is broken, Layer 6 will ALWAYS fail.
Always fix from the bottom up.
```

---

## 📊 HOW TO TRACK YOUR PROGRESS

Copy this block into a scratch file and update it daily:

```
WEEK 1 — Linux
[x] Read 01_linux_mastery.md (all 5 parts)
[ ] 01_os_audit.sh — working
[ ] 02_process_manager.sh — working
[ ] 03_storage_audit.py — working
[ ] 04_ssh_hardener.sh — working (dry-run first!)
[ ] 05_pokevend_provisioner.sh — CAPSTONE complete

WEEK 2 — Scripting  
[ ] Read 02_scripting_mastery.md (all 3 parts)
[ ] 01_bash_fundamentals.sh — working + self-tests pass
[ ] 02_log_parser.sh — found real errors in NexusOS logs
[ ] 03_cron_scheduler.sh — all scripts scheduled
[ ] 01_system_probe.py — /proc readings working
[ ] 02_config_manager.py — validates .env correctly
[ ] 03_deploy_orchestrator.py — CAPSTONE complete

WEEK 3 — Networking
[ ] Read 03_networking_mastery.md (all 7 parts)
[ ] 01_port_scanner.py — all NexusOS ports scanned
[ ] 02_firewall_hardener.sh — UFW active, tested
[ ] 03_nginx_configurator.sh — Nginx running + proxying
[ ] 04_dns_resolver.py — Docker DNS validated
[ ] 05_network_validator.py — CAPSTONE complete

WEEK 4 — Security
[ ] Read 04_cybersecurity_mastery.md (all 6 parts)
[ ] 01_secrets_auditor.py — no leaked secrets found
[ ] 02_ids_monitor.py — running, detecting test attacks
[ ] 03_docker_hardener.sh — docker-compose secured
[ ] 04_vuln_scanner.py — zero critical CVEs
[ ] 05_security_audit.py — CAPSTONE + full report

WEEK 5 — Cloud
[ ] Read 05_cloud_mastery.md (all 4 parts)
[ ] 01_terraform_plan/ — terraform plan passes
[ ] 02_prometheus_metrics.go — /metrics endpoint live
[ ] 03_grafana_dashboard.json — dashboard imported
[ ] 04_log_aggregator.py — parsing all service logs
[ ] 05_load_tester.py — CAPSTONE + incident report written
```

---

## 🔥 BONUS ADVANCED CHALLENGES (After Week 5)

These are things that separate senior engineers from juniors:

1. **Zero-Downtime Deploy**: Modify `03_deploy_orchestrator.py` so Pokevend has 0ms downtime during deploys using a blue-green swap
2. **Distributed Tracing**: Add OpenTelemetry to the Go API so you can trace requests from Nginx → Go → PostgreSQL
3. **Chaos Engineering**: Write a script that randomly kills containers and verifies the system recovers automatically
4. **GitOps**: Set up a local Gitea server, create a webhook that auto-runs your deploy script on every push to main
5. **Container Registry**: Set up a local Docker registry, push/pull your Pokevend image through it

---

## ⚡ QUICK REFERENCE — COMMANDS YOU'LL USE EVERY DAY

```bash
# System health snapshot (run this first every morning)
echo "=== UPTIME ===" && uptime
echo "=== MEMORY ===" && free -h
echo "=== DISK ===" && df -h | grep -v tmpfs
echo "=== SERVICES ===" && systemctl list-units --type=service --state=failed
echo "=== DOCKER ===" && docker ps --format "table {{.Names}}\t{{.Status}}"

# Find what's using a port
ss -tlnp | grep :8080
lsof -i :8080               # Alternative

# Follow service logs in real-time
journalctl -u pokevend -f
docker logs nexusos-postgres -f

# Quick firewall check
sudo ufw status verbose

# Check if you locked yourself out (DO THIS before changing SSH!)
sudo sshd -t                # Test SSH config without restarting

# Database quick check
docker exec nexusos-postgres psql -U nexusos -c "SELECT count(*) FROM pg_stat_activity;"

# Nuclear option: full system restart of NexusOS stack
docker-compose -f shopify/docker-compose.yml down && docker-compose -f shopify/docker-compose.yml up -d
```

---

**START WITH: `lessons/01_linux_mastery.md` → then `scripts/linux/01_os_audit.sh`**
**Do not rush. Mastery is understanding, not completion speed.**
