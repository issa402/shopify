# 🎯 YOUR COMPLETE LEARNING ROADMAP
## Infrastructure Mastery Through Hands-On Practice

Your practice files are waiting. This is your step-by-step workout guide.

---

## WEEK 1: Linux Foundation
**Goal**: Understand your system + build diagnostic intuition  
**Time**: ~15 hours total  
**Deliverables**: System audit complete + 5 diagnostic scripts working

### Daily Tasks

#### Day 1: System Baseline (2-3 hours)
- [ ] **Read**: `lessons/01_linux_mastery.md` **PART 1** (Filesystem)
- [ ] **Read**: `lessons/01_linux_mastery.md` **PART 2** (Users & Permissions)
- [ ] **Hands-on**: Run ALL commands in "HANDS-ON EXERCISE: Map Your System"
- [ ] **Hands-on**: Run ALL commands in "HANDS-ON: PROVE WHY SECURITY MATTERS"
- [ ] **Document**: Screenshot your outputs, save to `/tmp/week1_day1.txt`

```bash
# After completing Day 1, you should be able to answer:
# 1. What's the current load average on your system?
# 2. How many users have actual shell access?
# 3. What happens if a file is 644 vs 755 vs 777?
# 4. Why shouldn't we run Pokevend as root?
```

#### Day 2: Processes & Systemd (2-3 hours)
- [ ] **Read**: `lessons/01_linux_mastery.md` **PART 3** (Processes & Systemd)
- [ ] **Hands-on**: Run ALL "HANDS-ON: UNDERSTAND SYSTEMD" exercises
- [ ] **Hands-on**: Check 3 systemd services: `systemctl status docker`, `systemctl status ssh`, etc.
- [ ] **Exercise**: Write down what `RestartSec=5s` means and why it matters

```bash
# Command practice:
systemctl list-units --type=service --state=running
systemctl show docker -p Restart
journalctl -u docker -n 20 --no-pager
```

#### Day 3: Storage & Backups (2-3 hours)
- [ ] **Read**: `lessons/01_linux_mastery.md` **PART 4** (Storage & Backups)
- [ ] **Hands-on**: Run ALL "HANDS-ON: DISK CRISIS DIAGNOSIS" exercises
- [ ] **Exercise**: Find the largest directories on your system
- [ ] **Exercise**: Check inode usage: `df -i`

```bash
# Critical challenge:
# If /var is 95% full, what breaks first? Why?
# How would you recover?
```

#### Day 4: SSH & Week 1 Review (2-3 hours)
- [ ] **Read**: `lessons/01_linux_mastery.md` **PART 5** (SSH)
- [ ] **Hands-on**: Generate SSH key: Run ALL "HANDS-ON: GENERATE YOUR SSH KEY" exercises
- [ ] **Exercise**: Check your SSH config: `cat ~/.ssh/authorized_keys`, `ssh-keygen -l -f ~/.ssh/id_ed25519.pub`
- [ ] **Quiz yourself**:
  - What's the difference between chmod 755 and chmod 750?
  - Why use `/bin/false` as a shell for service accounts?
  - What does `RestartSec` do in a systemd service?
  - Draw the filesystem hierarchy from memory

#### Day 5: Week 1 Scripts (3-4 hours)
- [ ] **Run**: `bash infra/scripts/linux/01_os_audit.sh`
- [ ] **Read**: The entire script, understand every line
- [ ] **Complete TODOs** in the script (audit_system_identity, audit_users, audit_processes, audit_storage, audit_docker)
- [ ] **Test**: Run the script with all functions working
- [ ] **Challenge**: Add a new audit function for SSH configuration

---

## WEEK 2: Bash Scripting & Automation
**Goal**: Build reusable scripts from scratch + understand log analysis  
**Time**: ~15 hours total  
**Deliverables**: bash_fundamentals library + 5 bash practice exercises complete

### Daily Tasks

#### Day 1: Bash Foundations (2-3 hours)
- [ ] **Read**: `lessons/02_scripting_mastery.md` **PART 1** (Bash Safety)
- [ ] **Hands-on**: Run "HANDS-ON: PROVE WHY THESE MATTER" — all 4 tests
- [ ] **Exercise**: Write a simple script that fails gracefully without `set -e`, then with `set -e`
- [ ] **Script**: Edit a copy of your script to add `set -euo pipefail` and prove it prevents bugs

```bash
# Review questions:
# 1. What does set -u catch that set -e doesn't?
# 2. Why is pipefail dangerous to omit?
# 3. What's the difference between $VAR and ${VAR}?
```

#### Day 2: Logging Functions (2-3 hours)
- [ ] **Read**: `lessons/02_scripting_mastery.md` (Functions section)
- [ ] **TODO**: Complete `scripts/bash/01_bash_fundamentals.sh`:
  - [ ] Implement `log::info()` with timestamp
  - [ ] Implement `log::warn()` with yellow color
  - [ ] Implement `log::error()` (write to stderr!)
  - [ ] Implement `log::success()`
  - [ ] Implement `log::step()` (with ━ dividers)
- [ ] **Test**: `bash scripts/bash/01_bash_fundamentals.sh test`

#### Day 3: Validation Functions (2-3 hours)
- [ ] **TODO**: Complete `scripts/bash/01_bash_fundamentals.sh`:
  - [ ] Implement `require::command()` (check if command exists)
  - [ ] Implement `require::root()` (check EUID)
  - [ ] Implement `require::env()` (check environment variable set)
  - [ ] Implement `require::file()` (check file exists and readable)
- [ ] **Test**: Write a test script that calls all 4 functions
- [ ] **Challenge**: Add `require::dir()` for checking directories

#### Day 4: Text Processing (2-3 hours)
- [ ] **Read**: `lessons/02_scripting_mastery.md` (Holy Trinity: grep, awk, sed)
- [ ] **Hands-on**: Run "HANDS-ON: ANALYZE LOGS LIKE A SRE" exercises
- [ ] **Practice**: `bash infra/practice/bash_practice.sh 3` (Exercise 3: Text Processing)
- [ ] **TODO**: Complete the disk usage filtering exercise in bash_practice.sh

```bash
# Challenge:
# Write a one-liner that finds all *.log files > 100MB
# and prints: "file.log: 145MB (too large!)"
```

#### Day 5: Bash Practice Exercises (2-3 hours)
- [ ] **Run**: `bash infra/practice/bash_practice.sh all`
- [ ] **Complete TODOs** in each exercise:
  - [ ] Exercise 1: Variable expansion (find the base name)
  - [ ] Exercise 2: Loops (count how many services are open)
  - [ ] Exercise 3: Text processing (disk usage > 50%)
  - [ ] Exercise 4: Functions (implement check_disk_space())
  - [ ] Exercise 5: Deployment (implement build step)
- [ ] **Final test**: All exercises run without errors

---

## WEEK 3: Python Scripting & System Automation
**Goal**: Use Python to manage infrastructure + parse system data  
**Time**: ~15 hours total  
**Deliverables**: python_practice.py exercises all complete

### Daily Tasks

#### Day 1: Python Foundation (2-3 hours)
- [ ] **Read**: `lessons/02_scripting_mastery.md` **PART 2** (Python)
- [ ] **Read**: `lessons/02_scripting_mastery.md` **PART 3** (subprocess module)
- [ ] **Run**: `python3 infra/practice/python_practice.py 1`
- [ ] **TODO**: Complete Exercise 1 challenges:
  - [ ] Count "DB connection failed" occurrences
  - [ ] Find max duration_ms
  - [ ] Build {message → count} dict
- [ ] **Test**: All comprehensions work correctly

#### Day 2: subprocess & System Commands (2-3 hours)
- [ ] **Run**: `python3 infra/practice/python_practice.py 2`
- [ ] **TODO**: Complete Exercise 2 challenges:
  - [ ] Extract listening ports from `ss -tlnp`
  - [ ] Parse /proc/loadavg
  - [ ] Check if port 8080 is in the list
- [ ] **Enhancement**: Add retry logic (try 3 times before failing)

#### Day 3: File Operations & pathlib (2-3 hours)
- [ ] **Run**: `python3 infra/practice/python_practice.py 3`
- [ ] **TODO**: Complete Exercise 3 challenges:
  - [ ] Count lines of code in all .go files
  - [ ] Find the Go file with MOST functions
  - [ ] Scan for TODO comments in .go files
- [ ] **Output**: Write findings to a JSON report

#### Day 4: Error Handling & Robustness (2-3 hours)
- [ ] **Run**: `python3 infra/practice/python_practice.py 4`
- [ ] **TODO**: Complete Exercise 4 challenges:
  - [ ] Add retry logic (try 3 times per endpoint)
  - [ ] Calculate average latency
  - [ ] Exit with code 1 if any service unhealthy
- [ ] **Test**: Health check works across multiple services

#### Day 5: Build a Real Tool — Status Reporter (3-4 hours)
- [ ] **Run**: `python3 infra/practice/python_practice.py 5`
- [ ] **TODO**: Build Exercise 5 — Status Reporter:
  - [ ] `collect_system_metrics()` — get memory, disk stats
  - [ ] `collect_container_statuses()` — Docker container health
  - [ ] `check_api_health()` — test Pokevend API
  - [ ] `generate_report()` — create markdown report
  - [ ] Main function that ties it all together
- [ ] **Output**: Report written to `/tmp/nexusos_status.md`
- [ ] **Final**: Schedule with cron: `*/5 * * * * python3 /path/to/reporter.py`

---

## WEEK 4: Networking & Troubleshooting
**Goal**: Master network diagnostics + Docker networking  
**Time**: ~12 hours total  
**Deliverables**: Port scanner working + network validation complete

### Daily Tasks

#### Day 1-2: Network Fundamentals (4 hours)
- [ ] **Read**: `lessons/03_networking_mastery.md` **PART 1-3** (OSI, TCP, Ports)
- [ ] **Hands-on**: "HANDS-ON: POKEVEND NETWORK TROUBLESHOOTING"
- [ ] **Practice**: Test all 5 scenarios manually:
  - [ ] Check if 8080 is available
  - [ ] Verify if Go API is listening
  - [ ] Test Redis connectivity
  - [ ] Count TCP connections
  - [ ] List all listening ports

#### Day 3-4: Docker & DNS Networking (4 hours)
- [ ] **Read**: `lessons/03_networking_mastery.md` **PART 4-5** (Docker, DNS)
- [ ] **Hands-on**: "HANDS-ON: DOCKER CONTAINER NETWORKING"
- [ ] **Hands-on**: "HANDS-ON: DNS DEBUGGING FOR POKEVEND"
- [ ] **Exercise**: Test DNS resolution of Docker services (when available)

#### Day 5: Network Scripts (3-4 hours)
- [ ] **Complete**: `scripts/network/01_port_scanner.py` (if it has TODOs)
  - [ ] Scan all expected Pokevend ports
  - [ ] Report listening state
  - [ ] Generate connectivity report
- [ ] **Test**: Run full port scan, verify output makes sense

---

## WEEK 5: Security & Hardening
**Goal**: Understand security principles + audit your project  
**Time**: ~12 hours total  
**Deliverables**: Secrets audit complete + firewall plan designed

### Daily Tasks

#### Day 1-2: Secrets & Access Control (4 hours)
- [ ] **Read**: `lessons/04_cybersecurity_mastery.md` **PART 1-2**
- [ ] **Hands-on**: "HANDS-ON: AUDIT POKEVEND REPO FOR LEAKED SECRETS"
- [ ] **Exercise**: Run ALL 6 secret scanning tests
- [ ] **Action**: If secrets found, add them to .gitignore and remove from git history
- [ ] **Verify**: No credentials in git log

#### Day 3-4: Firewalls & Network Security (4 hours)
- [ ] **Read**: `lessons/04_cybersecurity_mastery.md` **PART 3** (Firewalls)
- [ ] **Hands-on**: "HANDS-ON: POKEVEND FIREWALL SECURITY PLANNING"
- [ ] **Design**: Complete the firewall design exercise
- [ ] **Document**: Write a firewall ruleset for Pokevend deployment
- [ ] **Lab**: (If safe to do) Test UFW rules on a test VM

#### Day 5: Security Scripts (3-4 hours)
- [ ] **Complete**: `scripts/security/01_secrets_auditor.py` (if it has TODOs)
  - [ ] Scan entire repo for credential patterns
  - [ ] Generate a report of findings
  - [ ] Flag high-risk patterns
- [ ] **Run**: `python3 scripts/security/01_secrets_auditor.py`
- [ ] **Action**: Fix any findings in the repo

---

## WEEK 6: Cloud & Observability
**Goal**: Understand AWS design + monitoring architecture  
**Time**: ~12 hours total  
**Deliverables**: AWS design document + monitoring strategy

### Daily Tasks

#### Day 1-2: AWS & Terraform (4 hours)
- [ ] **Read**: `lessons/05_cloud_mastery.md` **PART 1-2** (AWS, Terraform)
- [ ] **Hands-on**: "HANDS-ON: DESIGN POKEVEND AWS INFRASTRUCTURE"
- [ ] **Exercises**: Complete ALL 4 exercises in the hands-on section
- [ ] **Document**: Write a design doc for deploying Pokevend to AWS
- [ ] **Cost**: Calculate approximate monthly AWS expenses

#### Day 3-4: Monitoring & Metrics (4 hours)
- [ ] **Read**: `lessons/05_cloud_mastery.md` **PART 3** (Observability)
- [ ] **Hands-on**: "HANDS-ON: MONITORING POKEVEND"
- [ ] **Exercise**: Complete the monitoring questions
- [ ] **Exercise**: Write PromQL queries for all 5 scenarios
- [ ] **Exercise**: Design alert rules for Pokevend

#### Day 5: Cloud Scripts (3-4 hours)
- [ ] **Complete**: `scripts/cloud/05_load_tester.py` (if it has TODOs)
  - [ ] Load test the Pokevend API
  - [ ] Measure response times
  - [ ] Generate load report
  - [ ] Write an incident report template
- [ ] **Run**: Load test, capture metrics
- [ ] **Report**: Document findings

---

## 🏁 FINAL CAPSTONE: Build a Production Monitoring Suite
**Time**: 1-2 weeks  
**Goal**: Combine EVERYTHING into one deployable monitoring system

### Components to Build:
1. **System Health Script** (Linux + Bash)
   - CPU, memory, disk, network monitoring
   - Background process health checking
   - Log aggregation

2. **Container Health Script** (Python + Docker)
   - Docker container status monitoring
   - Performance metrics per container
   - Alert on unhealthy containers

3. **API Health Dashboard** (Python + HTTP)
   - Test all microservice health endpoints
   - Track latency trends
   - Generate HTML report

4. **Alerting System** (Bash + Email/Slack)
   - Watch for critical conditions
   - Send alerts when thresholds exceeded
   - Track alert history

5. **Infrastructure-as-Code** (Terraform)
   - Deploy monitoring to AWS
   - Set up alerts in CloudWatch
   - Create RDS for metrics storage

---

## 📊 PROGRESS TRACKER

Copy this into a file and update it daily:

```
WEEK 1: Linux Foundation
[x] Day 1: System Baseline
[x] Day 2: Processes & Systemd
[x] Day 3: Storage & Backups
[x] Day 4: SSH & Review
[x] Day 5: Scripts
Status: 5/5 complete, scripts fully functional

WEEK 2: Bash Scripting
[ ] Day 1: Bash Foundations
[ ] Day 2: Logging Functions
[ ] Day 3: Validation Functions
[ ] Day 4: Text Processing
[ ] Day 5: Practice Exercises
Status: 0/5 complete

WEEK 3: Python Scripting
[ ] Day 1: Python Foundation
[ ] Day 2: subprocess
[ ] Day 3: File Operations
[ ] Day 4: Error Handling
[ ] Day 5: Status Reporter
Status: 0/5 complete

WEEK 4: Networking
[ ] Day 1-2: Fundamentals
[ ] Day 3-4: Docker & DNS
[ ] Day 5: Scripts
Status: 0/3 complete

WEEK 5: Security
[ ] Day 1-2: Secrets & Access
[ ] Day 3-4: Firewalls
[ ] Day 5: Scripts
Status: 0/3 complete

WEEK 6: Cloud & Observability
[ ] Day 1-2: AWS & Terraform
[ ] Day 3-4: Monitoring
[ ] Day 5: Scripts
Status: 0/3 complete

CAPSTONE: Production System
Status: Not started
```

---

## 🎓 HOW TO USE THIS ROADMAP

1. **Print it** — Put it on your wall
2. **Daily standup** — Each morning: "What am I doing today?"
3. **Execute exercises** — Run the commands, type the code, break things, fix them
4. **Test often** — After each exercise, verify it works
5. **Document** — Keep notes of what you learned
6. **Ask questions** — If something doesn't make sense, look it up and document the answer

---

## ✅ SUCCESS CRITERIA

You know you're mastering this when:

- [ ] You can diagnose ANY system health issue by running 5 commands
- [ ] You can write a bash script that doesn't break silently on errors
- [ ] You can extract meaningful data from logs using grep/awk/sed in one line
- [ ] You understand why a service runs as a non-root user
- [ ] You can design a firewall rule set that's both secure AND allows legitimate traffic
- [ ] You can parse Docker network topology and debug connectivity issues
- [ ] You can write Python code that talks to the OS and parses its responses
- [ ] You can explain what happens when disk fills to 100%
- [ ] You can design a monitoring architecture for a real service
- [ ] You understand the tradeoffs between different AWS deployment options
