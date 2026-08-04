# 📚 LESSON 02: Python & Bash Scripting Mastery
## MASTER REFERENCE — Read before touching any Week 2 scripts

---

## 🧠 The Mental Model: Scripts Are Force Multipliers

An Infrastructure Engineer who can't script is like a surgeon who uses their hands instead of instruments. Scripting lets you:
- Do in 1 second what takes a human 10 minutes
- Do it CORRECTLY every single time (no fat-finger mistakes)
- Do it CONSISTENTLY across 100 servers at once
- PROVE you did it (via logs)

**Rule**: If you do something manually more than twice, you script it.

**Job Qualification Link**: *"Proficiency in scripting or programming (e.g., PowerShell, Python, Bash, etc) to automate tasks, analyze data, and support infrastructure operations."*

This lesson teaches you to build the **exact infrastructure scripts** that SREs and DevOps engineers use at major companies. By the end, you'll be able to write **production-grade** automation code.

---

## 🔨 PART 1: Bash — The OS Glue

### The #1 Bash Safety Rule

**Always start your scripts with:**
```bash
#!/usr/bin/env bash
set -euo pipefail
```

Let's break this down:
```bash
#!/usr/bin/env bash    # The "shebang" — tells Linux what interpreter to use
                       # /usr/bin/env bash is better than #!/bin/bash because
                       # it finds bash wherever it is on the system

set -e                 # Exit Immediately on error
                       # Without this: a failed command is silently ignored
                       # With this: if ANY command fails, the script STOPS
                       # This prevents "half-deployed" disasters

set -u                 # Treat Unset Variables as errors
                       # Without: $UNDEFINED_VAR becomes empty string ""
                       # With: using an unset variable = immediate error
                       # This prevents typos from silently doing the wrong thing

set -o pipefail        # Pipeline fails if ANY step fails
                       # Without: false | true returns 0 (success!) — DANGEROUS
                       # With: any failure in a pipe = entire pipe fails
```

This triplet `set -euo pipefail` is NON-NEGOTIABLE. Use it in every script. 

**HANDS-ON: PROVE WHY THESE MATTER (10 minutes)**

```bash
# Test 1: set -e in action
cat > /tmp/test_set_e.sh <<'EOF'
#!/bin/bash
# WITHOUT set -e — DANGEROUS
mkdir /root/forbidden 2>/dev/null || true
echo "This runs anyway"  # Problem: script continues after failure
EOF
bash /tmp/test_set_e.sh

echo "The script completed even though mkdir failed!"

# Test 2: WITH set -e — CORRECT
cat > /tmp/test_set_e_safe.sh <<'EOF'
#!/bin/bash
set -euo pipefail
mkdir /root/forbidden 2>/dev/null || true    # This WILL fail
echo "THIS NEVER PRINTS"  # Script stops at the error
EOF
bash /tmp/test_set_e_safe.sh 2>&1 || echo "Script correctly stopped on error"

# Test 3: set -u catches typos
cat > /tmp/test_set_u.sh <<'EOF'
#!/bin/bash
set -euo pipefail
BACKUP_DIR="/backups"
echo "Backing up to: $BAKUP_DIR"  # Typo: BAKUP_DIR instead of BACKUP_DIR
EOF
bash /tmp/test_set_u.sh 2>&1 || echo "Typo caught by set -u!"

# Test 4: pipefail saves you
echo "Testing | grep impossible" | grep nonexistent ; echo "Result without pipefail: $?"
# Piping to a failed grep normally returns 0 (success) — VERY BAD
```

---

### Variables in Bash

```bash
# Basic variable
NAME="pokevend"
echo $NAME              # pokevend
echo "${NAME}"          # Better — always use braces
echo "${NAME}_backup"   # pokevend_backup (without braces: $NAME_backup = empty)

# Command substitution — capture output of a command
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Backup created at: ${TIMESTAMP}"
# Output: Backup created at: 20260401_143022

# Arithmetic
COUNT=5
echo $((COUNT + 1))     # 6
echo $((COUNT * 2))     # 10

# Default values (critical for defensive scripting)
DB_HOST="${DB_HOST:-localhost}"   # Use $DB_HOST if set, else "localhost"
DB_PORT="${DB_PORT:-5432}"        # This is how you handle missing env vars safely
```

### The Exit Code — The Language of Failure

Every command returns an exit code. `0` = success. `1-255` = failure.
This is how scripts communicate "did it work?"

```bash
ls /tmp/myfile          # Returns 0 if file exists, 2 if not
echo $?                 # Print the exit code of the LAST command

# Checking exit codes
if ! mkdir /root/secret 2>/dev/null; then
    echo "ERROR: Could not create directory"
    exit 1              # Exit with failure code
fi

# The && and || operators
mkdir /opt/pokevend && echo "Success"  # Run second only if first SUCCEEDS
mkdir /root/secret || echo "Failed"   # Run second only if first FAILS
```


### The Holy Trinity: grep, awk, sed

These three tools parse text. Since EVERYTHING in Linux is text (logs, config files, command output), these are your most powerful analysis weapons.

**Job Qualification**: *"Develop expertise in key areas... improve that area's ability to make critical business decisions"* — Data analysis from logs is HOW you make critical decisions.

```bash
# ─────────────────── GREP — Find lines matching a pattern ──────────────────
# FIRST: Generate sample logs (you'll run this ONCE)
bash infra/scripts/bash/generate_sample_logs.sh

# NOW these examples actually work:
grep "ERROR" /tmp/pokevend_logs/app.log           # Find ERROR lines in Go API logs
grep -i "error" /tmp/pokevend_logs/app.log        # Case-insensitive search
grep -n "FATAL" /tmp/pokevend_logs/app.log        # Show line numbers with matches
grep -c "200" /tmp/pokevend_logs/access.log       # Count successful HTTP responses
grep -v "200" /tmp/pokevend_logs/access.log       # Invert — show failed requests (4xx, 5xx)
grep -E "(ERROR|FATAL)" /tmp/pokevend_logs/app.log  # Find multiple patterns
grep -A 2 "ERROR" /tmp/pokevend_logs/app.log      # Show ERROR line + 2 lines after                        # 3 lines AFTER each match (context)

# Real-world usage: Find all failed auth attempts in the last hour
journalctl -u pokevend --since "1 hour ago" | grep -i "unauthorized"

# ─────────────────── AWK — Column extraction and transformation ────────────
# awk processes each line as "fields" split by whitespace
# $1 = first field, $2 = second, $NF = last field

# Nginx access log format example:
# 192.168.1.1 - - [01/Apr/2026:14:30:00 +0000] "GET /api/v1/cards HTTP/1.1" 200 1234

awk '{print $1}' /var/log/nginx/access.log       # Extract all IP addresses
awk '{print $9}' /var/log/nginx/access.log       # Extract status codes
awk '$9 == "500"' /var/log/nginx/access.log      # Only 500 error lines
awk '$9 >= "400" {print $1, $7}' access.log      # IP and URL for 4xx+ errors
awk 'END {print NR}' access.log                  # Count total lines (NR = line number)

# Count requests per IP (find top abusers):
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -20
# Breakdown:
# awk '{print $1}'  — extract IPs
# sort              — sort alphabetically (needed before uniq)
# uniq -c           — count duplicates
# sort -rn          — sort by count, reversed (highest first)
# head -20          — show top 20

# ─────────────────── SED — Find and Replace in streams ────────────────────
# sed is a "stream editor" — it modifies text as it flows through

sed 's/old/new/' file.txt           # Replace first occurrence per line
sed 's/old/new/g' file.txt          # Replace ALL occurrences (g = global)
sed 's/password=.*/password=REDACTED/g' config.txt  # Redact passwords in logs
sed -n '10,20p' file.txt            # Print only lines 10-20
sed '/^#/d' file.txt                # Delete comment lines (starting with #)
sed -i 's/localhost/prod-db.internal/g' config.env  # Edit file IN-PLACE (-i)

# Real-world: Extract the DB URL from an env file and redact the password
grep "DATABASE_URL" .env | sed 's/:.*@/:REDACTED@/'
```

**HANDS-ON: ANALYZE LOGS LIKE A SRE (20 minutes)**

First, generate realistic sample logs matching your actual Pokemon project infrastructure:

```bash
# Step 1: Generate sample logs (creates /tmp/pokevend_logs/ with 4 realistic log files)
bash infra/scripts/bash/generate_sample_logs.sh

# Step 2: List what was created
ls -lah /tmp/pokevend_logs/
```

Now analyze them with grep/awk/sed (these are REAL logs, not made up):

```bash
# GREP EXERCISES
# 1. How many ERROR messages are in the app.log?
grep "ERROR" /tmp/pokevend_logs/app.log | wc -l

# 2. Show all ERROR messages with timestamps (first 3)
grep "\[ERROR\]" /tmp/pokevend_logs/app.log | head -3

# 3. Find all database connection errors
grep "database\|connection\|conn" /tmp/pokevend_logs/app.log | head -5

# AWK EXERCISES
# 4. Extract all status codes from Nginx (column 9)
awk '{print $9}' /tmp/pokevend_logs/access.log

# 5. What's the top IP making requests to Nginx?
awk '{print $1}' /tmp/pokevend_logs/access.log | sort | uniq -c | sort -rn | head -5

# 6. Count all requests by status code (200s, 500s, etc.)
awk '{print $9}' /tmp/pokevend_logs/access.log | sort | uniq -c | sort -rn

# SED EXERCISES
# 7. Show only ERROR lines from app.log, but redact any IPs
sed -n '/ERROR/p' /tmp/pokevend_logs/app.log | sed 's/[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+/<IP>/g'

# 8. Replace all ERROR with CRITICAL (doesn't modify file, just shows output)
sed 's/ERROR/CRITICAL/g' /tmp/pokevend_logs/app.log | head -5

# ADVANCED COMBINATION
# 9. Get top 3 IPs with 500+ errors (find abuse patterns)
grep " 5[0-9][0-9] " /tmp/pokevend_logs/access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -3

# 10. Count 404 Not Found vs 500 Server Error (which is worse?)
echo "404s: $(grep ' 404 ' /tmp/pokevend_logs/access.log | wc -l)"
echo "500s: $(grep ' 500 ' /tmp/pokevend_logs/access.log | wc -l)"
```

## CHALLENGE: Analyze the Docker Logs File

```bash
# Read the docker.log file
cat /tmp/pokevend_logs/docker.log

# Your challenge:
# 1. How many ERROR lines are there?
# 2. Which service had the most errors? (hint: use grep + awk)
# 3. Find the most recent error (last one in the file)
# 4. Search for "timeout" or "failed" across all 4 log files (which file has the worst issues?)

# SOLUTION (don't peek until you try):
grep "ERROR" /tmp/pokevend_logs/docker.log | wc -l   # Q1
grep "\[ERROR\]" /tmp/pokevend_logs/*.log | awk -F: '{print $1}' | sort | uniq -c | sort -rn  # Q2/4
tail -1 /tmp/pokevend_logs/docker.log  # Q3
```

### Functions in Bash

```bash
# Functions make bash scripts readable and reusable
log_info() {
    echo "[$(date +%Y-%m-%dT%H:%M:%S)] [INFO]  $*"
}

log_error() {
    echo "[$(date +%Y-%m-%dT%H:%M:%S)] [ERROR] $*" >&2  # >&2 = write to stderr
}

check_command() {
    if ! command -v "$1" &>/dev/null; then
        log_error "Required command not found: $1"
        exit 1
    fi
}

# Usage
check_command docker
check_command psql
log_info "Starting deployment..."
```

### Heredocs — Writing Multi-Line Strings

```bash
# A heredoc writes multi-line text. Critical for generating config files.
cat <<EOF > /etc/pokevend/config.env
# Pokevend Production Config
# Generated by deploy script on $(date)
APP_PORT=8080
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pokevend
REDIS_ADDR=localhost:6379
EOF
# Everything between <<EOF and EOF is written to the file literally
# Notice $(date) IS expanded inside a heredoc
```

---

## 🐍 PART 2: Python — The Precision Scalpel

### The subprocess Module — Python's OS Interface

**Never use `os.system()`.** It's old, insecure, and useless. Always use `subprocess`.

```python
import subprocess

# ─────────────────── subprocess.run() — The modern way ──────────────────────

# Basic execution
result = subprocess.run(["ls", "-la", "/tmp"])
# Always pass commands as LISTS, not strings. Never:
# subprocess.run("ls -la /tmp")  ← shell injection vulnerability

# Capture output
result = subprocess.run(
    ["docker", "ps", "--format", "{{.Names}}"],
    capture_output=True,     # Capture stdout AND stderr
    text=True,               # Decode bytes to string automatically
    check=True               # Raise CalledProcessError if exit code != 0
)
running_containers = result.stdout.strip().split('\n')

# Handle failure explicitly

try:
    result = subprocess.run(
        ["systemctl", "restart", "pokevend"],
        capture_output=True,
        text=True,
        check=True           # This raises an exception on failure
    )
except subprocess.CalledProcessError as e:
    print(f"FAILED: {e.stderr}")
    raise  # Re-raise so the caller knows

# Run a shell pipeline (use shell=True ONLY when you need pipes — never with user input)
result = subprocess.run(
    "journalctl -u pokevend --since '5 minutes ago' | grep ERROR | wc -l",
    shell=True, capture_output=True, text=True
)
error_count = int(result.stdout.strip())
```

### The os and pathlib Modules — File System Operations

```python
import os
from pathlib import Path

# ─────────────────── os module ─────────────────────────────────────────────
os.getenv("DB_HOST", "localhost")   # Read env var with default
os.getenv("DB_PASSWORD")            # Returns None if not set
os.environ["SECRET_KEY"]            # Raises KeyError if not set (good for required vars)

os.path.exists("/opt/pokevend")     # Does this path exist?
os.path.isfile("/opt/pokevend/bin") # Is it a file?
os.path.isdir("/opt/pokevend")      # Is it a directory?

os.makedirs("/var/log/pokevend", exist_ok=True)  # Create dir (and parents)
os.chown("/opt/pokevend", uid=1001, gid=1001)    # Change owner (needs root)
os.chmod("/opt/pokevend/bin", 0o750)             # Change permissions (octal!)

# ─────────────────── pathlib — The modern, elegant way ─────────────────────
# pathlib.Path is MUCH better than os.path for most cases

log_dir = Path("/var/log/pokevend")
log_dir.mkdir(parents=True, exist_ok=True)

binary_path = Path("/opt/pokevend/pokevend")
if binary_path.exists():
    print(f"Binary exists: {binary_path}")
    print(f"Size: {binary_path.stat().st_size / 1024:.1f} KB")

# Iterate over all log files
for log_file in Path("/var/log/pokevend").glob("*.log"):
    print(f"Log: {log_file.name}, Size: {log_file.stat().st_size}")
```

### argparse — Professional CLI Scripts

Infrastructure scripts MUST accept command-line arguments. No hardcoded values.

```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        description="Pokevend deployment and management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy.py --env prod --force
  python deploy.py --env staging --skip-backup
  python deploy.py --rollback v1.2.3
        """
    )
    
    # Required argument
    parser.add_argument(
        "--env",
        required=True,
        choices=["dev", "staging", "prod"],  # Enforces valid values
        help="Target environment"
    )
    
    # Optional flags
    parser.add_argument("--force", action="store_true", help="Skip confirmation")
    parser.add_argument("--skip-backup", action="store_true")
    parser.add_argument("--rollback", metavar="VERSION", help="Roll back to VERSION")
    
    return parser.parse_args()

# Usage:
# args = parse_args()
# if args.env == "prod" and not args.force:
#     confirm = input("Deploy to PRODUCTION? (yes/no): ")
```

### JSON Parsing — Config and API Responses

```python
import json
import urllib.request

# Read a JSON config file

with open("config.json", "r") as f:
    config = json.load(f)
    db_url = config["database"]["url"]

# Write a JSON file
status = {"service": "pokevend", "status": "healthy", "version": "1.2.3"}
with open("status.json", "w") as f:
    json.dump(status, f, indent=2)

# HTTP request (no external libraries needed)
def check_health(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.load(response)
    except Exception as e:
        return {"status": "down", "error": str(e)}

health = check_health("http://localhost:8080/health")
print(f"DB status: {health.get('database', 'unknown')}")
```

### Logging — The Professional Way

```python
import logging
import sys

# Configure logging early in your script

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),                          # Console
        logging.FileHandler("/var/log/pokevend/deploy.log")        # File
    ]
)
logger = logging.getLogger(__name__)

# Usage
logger.info("Starting deployment of version %s", "1.2.3")
logger.warning("Skipping backup as requested")
logger.error("Failed to connect to database: %s", err)
logger.critical("PRODUCTION IS DOWN — initiating rollback")
```

---

## 🔗 PART 3: Mixing Bash and Python

Real infrastructure uses both. The pattern is:
- **Bash** for: simple OS tasks, calling other programs, writing files
- **Python** for: complex logic, error handling, parsing JSON/YAML, HTTP calls

```bash
#!/usr/bin/env bash
# deploy.sh — Bash wrapper that calls Python for complex logic

set -euo pipefail

# Bash handles: checking prerequisites, env vars, calling python
if [[ ! -f ".env" ]]; then
    echo "ERROR: .env file not found"
    exit 1
fi

source .env  # Load env vars from .env file into current shell

# Call Python for the heavy lifting
python3 scripts/python/03_deploy_orchestrator.py \
    --env "${DEPLOY_ENV:-staging}" \
    --version "${GIT_SHA:-latest}"
```

---

## 📋 PRE-REQUISITES FOR WEEK 2

Before starting scripting tasks, verify:

```bash
# Python is installed
python3 --version          # Should be 3.10+
python3 -c "import subprocess, os, json, argparse; print('OK')"

# Key bash tools are available  
command -v grep awk sed sort uniq wc

# You understand exit codes
false; echo "exit: $?"     # Should print: exit: 1
true; echo "exit: $?"      # Should print: exit: 0
```

---

## 🔗 Resources

- **Bash Cheat Sheet**: https://devhints.io/bash
- **Python subprocess docs**: https://docs.python.org/3/library/subprocess.html
- **explainshell.com**: Paste any bash command and get it explained
- **ShellCheck**: https://www.shellcheck.net/ — Linter for bash scripts (use this!)
- **Real Python — subprocess**: https://realpython.com/python-subprocess/
