# ✅ EXERCISE REFERENCE: What Each TODO Means
## How to Know You're Done

This file explains EVERY TODO you'll encounter. Use it as your verification checklist.

---

## WEEK 1: Linux Foundation

### scripts/linux/01_os_audit.sh

#### TODO: Implement `audit_system_identity()`
**What it should do**: Get hostname, kernel version, OS info
```bash
# Commands you need:
hostname
uname -a
cat /etc/os-release
hostnamectl status

# Your function output should look like:
# ✓ System: Ubuntu 22.04
# ✓ Hostname: mycomputer
# ✓ Kernel: 5.10.0-1234
# ✓ Uptime: 45 days
```

**✅ Test**: After implementing, run: `audit_system_identity` and verify it doesn't error

---

#### TODO: Implement `audit_users()`
**What it should do**: List users with shell access, show their UIDs
```bash
# Commands you need:
cat /etc/passwd
grep -v "/nologin\|/false" /etc/passwd
cut -d: -f1,3 /etc/passwd

# Your function output should show:
# Active users with shell access:
# root: 0
# user: 1000
# Important: Verify no unexpected users have UID 0!
```

**✅ Test**: Run `audit_users` and look for any UID 0 users besides root

---

#### TODO: Implement `audit_processes()`
**What it should do**: List running systemd services, show resource usage
```bash
# Commands you need:
systemctl list-units --type=service --state=running
ps aux | sort -rn -k3 | head -10  # CPU usage
ps aux | sort -rn -k4 | head -10  # Memory usage

# Your function output should show:
# Top processes by memory:
# PID  %MEM  VSZ  COMMAND
# 1234  5.2  234M  docker
```

**✅ Test**: Run `audit_processes` and verify it shows the heaviest processes

---

#### TODO: Implement `audit_storage()`
**What it should do**: Check disk usage, inode usage, partition health
```bash
# Commands you need:
df -h
df -i
du -sh /*
ls -lS /* | head -20  # Largest directories

# Your function output should show:
# ⚠️  Partition / is 78% full
# ✓ Partition /home is 23% full
# ✓ Inodes usage is healthy (< 90%)
```

**✅ Test**: Run `audit_storage` and verify each mount point is checked

---

#### TODO: Implement `audit_docker()`
**What it should do**: List Docker containers, check health, show resource usage
```bash
# Commands you need:
docker ps -a
docker stats --no-stream
docker images
docker volume ls

# Your function output should show:
# Running containers: 3
# Stopped containers: 0
# Docker images: 12
# Volumes: 5
```

**✅ Test**: Run `audit_docker` (if Docker is running)

---

## WEEK 2: Bash Scripting

### scripts/bash/01_bash_fundamentals.sh

#### TODO: Implement `log::step()`
**What it should do**: Print a divider line, then the message
```bash
# Requirements:
# - Print a line of ━ characters (40-50 chars wide)
# - Print the message
# - Print another divider
# - Output to stderr (like other log functions)

# Example output:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Installing Python packages...
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Hints:
# printf '━%.0s' {1..40}  # Print 40 ━ characters
# Send to stderr with: >&2
```

**✅ Test**: `log::step "Test message"` and verify dividers print

---

#### TODO: Implement `require::command()`
**What it should do**: Check if a command exists, fail if not
```bash
# Requirements:
# - Take command name as argument
# - Check if it exists with 'command -v'
# - If not found, call log::error()
# - Return 1 if not found, 0 if found

# Example usage:
# require::command git    # Passes
# require::command foobar # Fails with error message

# Hints:
# Use: if ! command -v "$1" &>/dev/null; then
# Then call: log::error "Required command not found: $1"
```

**✅ Test**: 
```bash
require::command bash      # Should succeed (no error)
require::command notareal  # Should fail and print error
```

---

#### TODO: Implement `require::root()`
**What it should do**: Check if running as root, fail if not
```bash
# Requirements:
# - Check if EUID (effective UID) is 0
# - If not 0, call log::error()
# - Return 1 if not root, 0 if root

# Example usage:
# require::root  # Passes if you're root, fails otherwise

# Hints:
# Check: if (( EUID != 0 ))
# Call: log::error "This script must run as root"
```

**✅ Test**: 
```bash
require::root  # Will fail (probably not running as root)
sudo bash scripts/bash/01_bash_fundamentals.sh  # Then it passes
```

---

#### TODO: Implement `require::env()`
**What it should do**: Check if environment variable is set, fail if not
```bash
# Requirements:
# - Take variable name as argument (e.g., "POKEVEND_API_KEY")
# - Check if it's set and non-empty
# - If not set, call log::error()
# - Return 1 if not set, 0 if set

# Example usage:
# require::env POKEVEND_API_KEY
# require::env PATH

# Hints:
# Check using parameter expansion: ${variable:-}
# Or check $PARAM in: [[ -z ${PARAM:-} ]]
# Call: log::error "Required environment variable not set: $1"
```

**✅ Test**: 
```bash
require::env PATH          # Should pass (PATH is always set)
require::env NOTAREALVAR   # Should fail (not set)
```

---

#### TODO: Implement `require::file()`
**What it should do**: Check if file exists and is readable
```bash
# Requirements:
# - Take file path as argument
# - Check if file exists and is readable
# - If not, call log::error()
# - Return 1 if not readable, 0 if readable

# Example usage:
# require::file /etc/passwd
# require::file ~/.ssh/id_ed25519

# Hints:
# Check: [[ -r "$1" ]]
# Call: log::error "Required file not readable: $1"
```

**✅ Test**: 
```bash
require::file /etc/passwd      # Should pass
require::file /nonexistent     # Should fail (file not found)
require::file /root/.ssh/id_*  # Might fail (permission denied)
```

---

### practice/bash_practice.sh

#### Exercise 1: Variable Expansion (5 min)
**TODO**: Extract the base name from a filepath
```bash
# Given:
filepath="/var/log/pokevend/api.log"

# You need to extract:
basename_only="api.log"

# Hint: Use parameter expansion ${var##*/}
# Also try: basename "$filepath"
```

**✅ Test**: Run `bash practice/bash_practice.sh 1` and verify output

---

#### Exercise 2: Loops + Arrays (5-10 min)
**TODO**: Count how many Pokevend services are accessible
```bash
# Given service ports:
# 8080 = API server
# 5432 = Postgres database  
# 6379 = Redis cache

# You need to:
# 1. Check if each port is open
# 2. Count how many are open
# 3. Print summary:
#    "3/3 services are accessible"

# Hint: Use netcat with -zw1:
#   nc -zw1 localhost 8080 && echo "8080 OPEN" || echo "8080 CLOSED"
```

**✅ Test**: Run `bash practice/bash_practice.sh 2` and verify the count

---

#### Exercise 3: Text Processing (5-10 min)
**TODO**: Find disk partitions that are > 50% full
```bash
# Given:
# Run `df -h` and get output like:
# Filesystem     Size  Used Avail Use% Mounted on
# /dev/sda1      100G   78G   20G  78% /

# You need to:
# 1. Parse df output
# 2. Find rows where usage % > 50
# 3. Print them:
#    "⚠️  / is 78% full (20GB free)"

# Hint: Use awk with NR > 1 to skip header
# Extract the Use% column and compare as number
```

**✅ Test**: Run `bash practice/bash_practice.sh 3` and verify high-usage partitions

---

#### Exercise 4: Functions + Error Handling (10 min)
**TODO**: Implement `check_disk_space()` function
```bash
# Requirements:
# - Function takes a directory path as argument
# - Checks how much space is available
# - Returns 1 if less than 5GB available
# - Returns 0 if >= 5GB available
# - Prints a status message

# Example usage:
# check_disk_space /
# check_disk_space /home

# Hint: Use 'df -B1' to get bytes, then convert to GB
# Or use 'df' with human-readable and do math
```

**✅ Test**: Run `bash practice/bash_practice.sh 4` and test with different directories

---

#### Exercise 5: Mini Deployment Script (15 min)
**TODO**: Complete the build and deployment logic
```bash
# Requirements:
# - Check required commands exist (go, docker)
# - Build the Go binary
# - Create Docker image
# - Print success message or fail gracefully

# Template:
# 1. require::command go
# 2. require::command docker
# 3. cd /path/to/Pokemon/server
# 4. go build -o pokevend,
# 5. docker build -t pokevend:latest .
# 6. echo "✅ Deployment complete"
```

**✅ Test**: Run `bash practice/bash_practice.sh 5` and verify it builds (or shows what's missing)

---

## WEEK 3: Python Scripting

### practice/python_practice.py

#### Exercise 1: Data Types + Comprehensions (10 min)
**TODOs**:
1. Count "DB connection failed" occurrences
2. Find the maximum `duration_ms` value
3. Build a dict of `{message → count}`

```python
# Given a log file with JSON lines like:
# {"message": "DB connection failed", "duration_ms": 234}
# {"message": "API response OK", "duration_ms": 45}

# You need to:
# COUNT occurrences of each message
# FIND max duration
# CREATE dict: {"DB connection failed": 3, "API response OK": 15}

# Hints:
# - Use Counter from collections
# - Use max(list of numbers)
# - Use dict comprehension or Counter
```

**✅ Test**: Run `python3 practice/python_practice.py 1` and verify counts make sense

---

#### Exercise 2: subprocess Module (10 min)
**TODOs**:
1. Extract listening ports from `ss -tlnp`
2. Parse `/proc/loadavg`
3. Check if port 8080 is in the list

```python
# Commands to run:
# ss -tlnp           # Show listening TCP ports
# cat /proc/loadavg  # Show 1/5/15 min load average

# You need to:
# EXTRACT ports like 8080, 5432, 6379 from ss output
# PARSE first line of /proc/loadavg (1-min average)
# CHECK if 8080 is listening
# PRINT results

# Hints:
# subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
# Split output by newlines and parse each line
# Use regex to extract port numbers
```

**✅ Test**: Run `python3 practice/python_practice.py 2` and verify port detection

---

#### Exercise 3: File Operations + pathlib (10 min)
**TODOs**:
1. Count lines of code in all `.go` files
2. Find the Go file with most functions
3. Scan for TODO comments in `.go` files

```python
# You need to:
# USE pathlib to find all *.go files in Pokemon/server
# COUNT lines in each file
# COUNT "func " occurrences (Go functions)
# FIND TODOs in files
# PRINT results:
#   "main.go: 234 lines, 12 functions"
#   "handlers.go: 567 lines, 34 functions"
#   "File with most functions: handlers.go (34 functions)"
#   "TODOs found: 3 in main.go, 5 in handlers.go"

# Hints:
# from pathlib import Path
# for file in Path(".").rglob("*.go"):
# file.read_text().count("\n")
```

**✅ Test**: Run `python3 practice/python_practice.py 3` and verify file analysis

---

#### Exercise 4: Error Handling + Retry Logic (10 min)
**TODOs**:
1. Add retry logic (try 3 times per endpoint)
2. Calculate average latency
3. Exit with code 1 if any service unhealthy

```python
# You need to:
# TEST these endpoints:
#   http://localhost:8080/health
#   http://localhost:5432 (just check connectivity)
#   http://localhost:6379 (just check connectivity)
# RETRY 3 times if first attempt fails
# MEASURE response time for each
# CALCULATE average latency
# PRINT results:
#   "✓ API (8080): 45ms healthy"
#   "✗ Redis (6379): connection refused (unhealthy)"
# EXIT with code 1 if ANY service unhealthy

# Hints:
# import requests
# for attempt in range(3): try / except
# Use time.time() before/after request
# sys.exit(1) for failure
```

**✅ Test**: Run `python3 practice/python_practice.py 4` and check return code

---

#### Exercise 5: Build a Complete Status Reporter (20-30 min)
**TODO**: Implement all functions to build a status reporting tool
```python
# Functions you need to implement:

def collect_system_metrics():
    # Return: {"memory_used": "23%", "disk_used": "45%", "cpu_count": 4}
    # Commands: free, df, nproc

def collect_container_statuses():
    # Return: {"running": 3, "stopped": 0, "images": 12}
    # Command: docker ps, docker images

def check_api_health():
    # Return: {"8080": "healthy", "5432": "connection_failed"}
    # Retry 3 times per endpoint

def generate_report():
    # Create markdown file with all metrics
    # Write to /tmp/nexusos_status.md
    # Include timestamp, all metrics, any warnings

# Main:
metrics = collect_system_metrics()
containers = collect_container_statuses()
api_health = check_api_health()
generate_report()
print("Report written to /tmp/nexusos_status.md")
```

**✅ Test**: 
```bash
python3 practice/python_practice.py 5
cat /tmp/nexusos_status.md  # Verify the report exists and looks good
```

---

## WEEK 4: Networking

### YOUR STATUS REPORT
When you complete Weeks 1-3, you should be able to describe:

✅ **Linux Foundation**
- Can you explain what `/var/log` is used for?
- Can you list all users with shell access?
- Can you identify which process is using the most memory?
- Can you explain what systemd RestartSec does?

✅ **Bash Scripting**
- Do you understand why `set -euo pipefail` is important?
- Can you write a function that takes arguments?
- Can you use grep/awk to filter a text file?
- Can you write a loop that checks multiple services?

✅ **Python Scripting**
- Can you run shell commands from Python?
- Can you parse JSON data?
- Can you handle errors with try/except?
- Can you use pathlib to find files?

If you can't answer ANY of these, **GO BACK and re-do that exercise.**

---

## VERIFICATION CHECKLIST

After each exercise, verify:

- [ ] Script runs without errors
- [ ] Output makes sense (numbers reasonable)
- [ ] No sensitive data in output
- [ ] You can explain every line of code
- [ ] You tested both success and failure cases
- [ ] Code follows the pattern in bash_fundamentals.sh (for bash)
- [ ] Error handling is in place

---

## IF A TODO CONFUSES YOU

1. **Read the hint** — It's there for a reason
2. **Google the command** — `man grep`, `man awk`, etc.
3. **Try it manually first** — Run the command by hand
4. **Write pseudo-code** — Plan before coding
5. **Test one piece at a time** — Don't write 20 lines at once

---

**YOU'VE GOT THIS** 💪
