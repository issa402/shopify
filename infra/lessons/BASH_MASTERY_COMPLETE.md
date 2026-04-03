# 🔥 BASH MASTERY — COMPLETE REFERENCE
## From Zero to Infrastructure Automation Expert
### Every concept tied to the NexusOS/Pokevend stack

---

> **HOW TO USE THIS DOCUMENT**
> Don't just read. Every code block has a "TRY IT NOW" marker.
> Open a terminal alongside this. Run every example. Break it. Fix it.
> The intuition comes from doing, not reading.

---

## CHAPTER 1: How Bash Actually Works — The Mental Model

Most people think of Bash as "a way to run commands." That's wrong.

**Bash is a programming language whose primitive type is a string of text.**

Every command in Bash is fundamentally this:
```
program_name arg1 arg2 arg3
```
Where everything is text. `ls -la /tmp` is: program=`ls`, arg1=`-la`, arg2=`/tmp`.

### The Two Phases: Expansion → Execution

Before Bash runs a command, it **expands** it. This is why Bash behaves the way it does.

```bash
# Phase 1: Expansion (Bash transforms your text BEFORE running anything)
echo "Today is $(date +%A)"
# Bash sees: echo "Today is $(date +%A)"
# Expansion: runs date +%A → "Tuesday"
# Becomes:   echo "Today is Tuesday"
# Phase 2: Execution: runs echo with "Today is Tuesday"

# Multiple expansions happen in this order:
# 1. Brace expansion:        {a,b,c} → a b c
# 2. Tilde expansion:        ~ → /home/iscjmz
# 3. Parameter expansion:    $VAR or ${VAR}
# 4. Command substitution:   $(command)
# 5. Arithmetic expansion:   $((5 + 3))
# 6. Word splitting:         split by IFS
# 7. Filename expansion:     *.go → file1.go file2.go
```

**TRY IT NOW — See expansion in action:**
```bash
set -x           # Debug mode — shows EXACTLY what bash runs after expansion
echo "Host: $(hostname)"
ls *.md 2>/dev/null
COUNT=5; echo $((COUNT * 2))
set +x           # Turn off debug mode
```

Understanding expansion is WHY:
- `echo $VAR` is dangerous but `echo "${VAR}"` is safe
- `*.go` works without quotes but breaks in directories with spaces
- Scripts that work interactively sometimes fail in cron (different expansion)

---

## CHAPTER 2: Variables — The Complete Truth

### Basic Variables

```bash
# Assignment — NO spaces around = (critical!)
NAME="nexusos"
PORT=8080               # Numbers are still strings in bash
EMPTY=""

# BAD (fails because bash thinks = is an argument to NAME):
# NAME = "nexusos"

# Reading variables
echo $NAME              # Works but risky
echo "${NAME}"          # ALWAYS use this form — braces prevent ambiguity
echo "${NAME}_backup"   # nexusos_backup (without braces: $NAME_backup → empty!)
```

### The Full Power of Parameter Expansion

This is where Bash becomes genuinely powerful. These transforms happen WITHOUT spawning a subprocess.

```bash
URL="https://api.nexusos.com/v1/cards"

# Default values — critical for infrastructure scripts
DB_HOST="${DB_HOST:-localhost}"         # Use $DB_HOST if set, else "localhost"
DB_PORT="${DB_PORT:-5432}"              # Use env var or default

# Fail if variable is unset (crash with message)
DB_PASSWORD="${DB_PASSWORD:?'ERROR: DB_PASSWORD must be set'}"
# If DB_PASSWORD is not set, script exits with that error message

# Assign default AND save it
LOGDIR="${LOGDIR:=/var/log/nexusos}"   # If unset, set it AND use the value

# String length
echo "${#URL}"          # 36 (length of the URL string)

# Substring extraction
echo "${URL:8}"         # api.nexusos.com/v1/cards (skip first 8 chars)
echo "${URL:8:11}"      # api.nexusos (8 chars in, 11 chars long)

# Remove prefix (shortest match)
echo "${URL#https://}"  # api.nexusos.com/v1/cards

# Remove prefix (longest match — greedy)
FILEPATH="/var/log/nexusos/app.log"
echo "${FILEPATH##*/}"  # app.log (remove everything up to last /)
                        # This is basename WITHOUT calling basename!

# Remove suffix
echo "${FILEPATH%/*}"   # /var/log/nexusos (remove everything after last /)
                        # This is dirname WITHOUT calling dirname!
echo "${FILEPATH%.log}" # /var/log/nexusos/app (remove .log extension)

# Replace
VERSION="v1.2.3-beta"
echo "${VERSION/beta/stable}"   # v1.2.3-stable (replace first match)
echo "${VERSION//-/_}"         # v1.2.3_beta (replace ALL dashes with underscores)

# Case transformation (bash 4+)
SERVICE="NexusOS"
echo "${SERVICE,,}"     # nexusos (lowercase all)
echo "${SERVICE^^}"     # NEXUSOS (uppercase all)
echo "${SERVICE,}"      # nEXusOS (lowercase first char only)
```

**PROJECT EXERCISE — use this RIGHT NOW in 01_os_audit.sh:**
```bash
# In your audit script, extract just the service name from a full path
SERVICE_FILE="/etc/systemd/system/pokevend.service"
SERVICE_NAME="${SERVICE_FILE##*/}"        # pokevend.service
SERVICE_NAME="${SERVICE_NAME%.service}"   # pokevend
echo "Service name: ${SERVICE_NAME}"
```

---

## CHAPTER 3: Control Flow — Making Decisions

### The Exit Code — The Grammar of Success/Failure

Every single command in Linux returns a number 0-255 when it finishes.
- **0** = success (true)
- **1-255** = failure (false)

This is the opposite of most programming languages where 0 = false!

```bash
ls /tmp              # Returns 0 (success)
ls /nonexistent      # Returns 2 (failure)

echo $?              # $? = exit code of the LAST command

# Bash evaluates exit codes for if statements
if ls /tmp; then
    echo "directory exists"     # This runs if ls returned 0
fi

# The [ ] and [[ ]] are actually commands that return 0 or 1
[ -d "/tmp" ]        # Returns 0 if /tmp is a directory
[[ -f "/etc/passwd" ]]  # Returns 0 if file exists

# Common test operators
[[ -f file ]]       # Is it a file?
[[ -d dir ]]        # Is it a directory?
[[ -r file ]]       # Is it readable?
[[ -w file ]]       # Is it writable?
[[ -x file ]]       # Is it executable?
[[ -z "$var" ]]     # Is the variable empty? (zero length)
[[ -n "$var" ]]     # Is the variable non-empty? (non-zero length)
[[ -s file ]]       # Does the file exist AND is it non-empty (has size)?
[[ "$a" == "$b" ]]  # String equality
[[ "$a" != "$b" ]]  # String inequality
[[ $n -eq 5 ]]      # Numeric equality (-eq -ne -lt -le -gt -ge)
[[ $n -gt 5 && $n -lt 10 ]]  # Compound: 5 < n < 10
```

### The && and || Operators — The Infrastructure Pattern

```bash
# && = "and then" — run second command only if first SUCCEEDS
mkdir /opt/nexusos && echo "Created directory"
systemctl start pokevend && echo "Service started"

# || = "or else" — run second command only if first FAILS
mkdir /opt/nexusos || echo "ERROR: Could not create directory"

# POWER PATTERN — try something, fall back on failure:
docker start nexusos-postgres || {
    echo "Container not found, starting from compose"
    docker-compose up -d postgres
}

# SAFEGUARD PATTERN — stop if something fails:
go build -o /opt/pokevend/pokevend ./... || exit 1
# Script stops here if build fails — NEVER deploys a broken binary
```

### If/Elif/Else — Full Syntax

```bash
# Check environment and set appropriate DB host
ENV="${1:-dev}"

if [[ "${ENV}" == "prod" ]]; then
    DB_HOST="prod-db.nexusos.internal"
    LOG_LEVEL="warn"
elif [[ "${ENV}" == "staging" ]]; then
    DB_HOST="staging-db.nexusos.internal"
    LOG_LEVEL="info"
elif [[ "${ENV}" == "dev" ]]; then
    DB_HOST="localhost"
    LOG_LEVEL="debug"
else
    echo "ERROR: Unknown environment '${ENV}'. Use: prod, staging, dev" >&2
    exit 1
fi

echo "Connecting to ${DB_HOST} with log level ${LOG_LEVEL}"
```

### Case Statements — The Router

Case is cleaner than if/elif when routing on a single variable:

```bash
# Service management router — from your 02_process_manager.sh
handle_command() {
    local cmd="$1"
    shift  # Remove first argument, $@ now contains remaining args

    case "${cmd}" in
        start)
            start_service "$@"
            ;;
        stop|kill)         # Multiple patterns in one branch
            stop_service "$@"
            ;;
        restart)
            stop_service "$@" && start_service "$@"
            ;;
        status|info)
            show_status "$@"
            ;;
        logs)
            show_logs "$@"
            ;;
        --help|-h|help)
            show_usage
            ;;
        *)                 # Default — catches everything else
            echo "Unknown command: ${cmd}" >&2
            show_usage
            exit 1
            ;;
    esac
}
```

---

## CHAPTER 4: Loops — Repeating Operations at Scale

### For Loops — Iterate Over Everything

```bash
# ─── Over a list ──────────────────────────────────────────────────────
SERVICES=("pokevend" "nginx" "postgresql@14")
for service in "${SERVICES[@]}"; do
    status=$(systemctl is-active "${service}" 2>/dev/null || echo "not-found")
    printf "%-20s %s\n" "${service}" "${status}"
done

# ─── Over files matching a pattern ────────────────────────────────────
for config_file in /etc/nexusos/*.conf; do
    [[ -f "${config_file}" ]] || continue   # skip if no files match
    echo "Validating: ${config_file}"
    # validate the config
done

# ─── Over command output ───────────────────────────────────────────────
# Get all running docker containers and check their health
while IFS= read -r container; do
    health=$(docker inspect --format='{{.State.Health.Status}}' "${container}" 2>/dev/null)
    echo "${container}: ${health:-no healthcheck}"
done < <(docker ps --format='{{.Names}}')
# < <(command) = "process substitution" — reads command output as a file

# ─── C-style loop (counter) ───────────────────────────────────────────
# Retry a service check 5 times
for ((i=1; i<=5; i++)); do
    if curl -sf http://localhost:8080/health > /dev/null; then
        echo "Service healthy after ${i} attempt(s)"
        break
    fi
    echo "Attempt ${i}/5 failed, waiting 2s..."
    sleep 2
done

# ─── Over lines in a file ──────────────────────────────────────────────
while IFS='=' read -r key value; do  # IFS='=' splits on = sign
    # Skip comments and empty lines
    [[ "${key}" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${key}" ]] && continue
    echo "Config: ${key} = ${value}"
done < /etc/nexusos/config.env

# ─── Infinite loop with break (polling pattern) ───────────────────────
echo "Waiting for Pokevend API to start..."
while true; do
    if curl -sf http://localhost:8080/health &>/dev/null; then
        echo "API is ready!"
        break
    fi
    sleep 1
done
```

---

## CHAPTER 5: Functions — The Architecture of Scripts

Functions are what separate a script from a PROGRAM.

```bash
# ─── Function Definition ──────────────────────────────────────────────
# Two equivalent syntaxes (function keyword is optional in Bash 4+)
function my_function { echo "hello"; }
my_function() { echo "hello"; }

# ─── Local Variables — CRITICAL ───────────────────────────────────────
# Without local: variables are GLOBAL and bleed between functions
# This causes the most mysterious bugs in bash scripts

check_service() {
    local service_name="$1"   # LOCAL — only exists in this function
    local timeout="${2:-30}"  # Default 30 seconds
    local status
    
    status=$(systemctl is-active "${service_name}" 2>/dev/null)
    
    if [[ "${status}" == "active" ]]; then
        return 0   # Return 0 = success
    else
        return 1   # Return non-zero = failure
    fi
}

# Call and check return value
if check_service "pokevend"; then
    echo "Pokevend is running"
else
    echo "Pokevend is DOWN"
fi

# ─── Return Values — Bash can only return numbers (0-255) ─────────────
# To return strings, use echo and command substitution

get_service_pid() {
    local service="$1"
    local pid
    pid=$(systemctl show "${service}" --property=MainPID --value 2>/dev/null)
    echo "${pid}"   # "Return" the PID by printing it
}

POKEVEND_PID=$(get_service_pid "pokevend")
echo "Pokevend PID: ${POKEVEND_PID}"

# ─── Functions as Commands — The Composition Pattern ──────────────────
# Functions can be piped, redirected, and used like any other command

get_all_container_ips() {
    docker network inspect nexusos-network \
        --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}' \
        2>/dev/null
}

# Pipe the function output to grep — exact same as piping a command
get_all_container_ips | grep "postgres"

# ─── The Trap Pattern — Guaranteed Cleanup ────────────────────────────
# This is one of the most important bash patterns for production scripts

safe_deploy() {
    local backup_file=""
    local service_was_running=false
    
    # Set up cleanup that runs NO MATTER HOW the function exits
    cleanup() {
        echo "Running cleanup..."
        if [[ -n "${backup_file}" && -f "${backup_file}" ]]; then
            rm -f "${backup_file}"
        fi
        if [[ "${service_was_running}" == "true" ]]; then
            systemctl start pokevend 2>/dev/null || true
        fi
    }
    trap cleanup EXIT   # Run cleanup when this script exits (success OR failure)
    trap 'echo "INTERRUPTED"; exit 130' INT TERM   # Handle Ctrl+C cleanly
    
    # Now do the risky operations
    service_was_running=$(systemctl is-active pokevend 2>/dev/null || true)
    backup_file=$(mktemp /tmp/pokevend_deploy.XXXXXX)
    
    # ... do things ...
    # If anything fails with set -e, cleanup() STILL runs
}
```

---

## CHAPTER 6: Text Processing Mastery — grep, awk, sed

This is the section that makes Infrastructure Engineers irreplaceable.
If you can work with text pipelines fluently, you can analyze any log,
parse any config, extract any metric.

### grep — Pattern Finder

```bash
# ─── Basic grep ───────────────────────────────────────────────────────
grep "ERROR" /var/log/nexusos/app.log           # Lines WITH "ERROR"
grep -v "ERROR" /var/log/nexusos/app.log        # Lines WITHOUT "ERROR"
grep -i "error" /var/log/nexusos/app.log        # Case insensitive
grep -n "FATAL" /var/log/nexusos/app.log        # With line numbers
grep -c "ERROR" /var/log/nexusos/app.log        # Count of matching lines
grep -l "ERROR" /var/log/nexusos/*.log          # List FILES that match

# ─── Extended Regex (-E) ──────────────────────────────────────────────
grep -E "(ERROR|FATAL|PANIC)" app.log           # Multiple patterns (OR)
grep -E "^[0-9]{4}-"          app.log           # Line starting with 4 digits + dash
grep -E "took [0-9]+ms"       app.log           # "took Nms" pattern
grep -E '"status":\s*[45][0-9]{2}' app.log     # HTTP 4xx or 5xx in JSON logs

# ─── Context lines ────────────────────────────────────────────────────
grep -A 5 "PANIC" app.log    # 5 lines AFTER each match (After)
grep -B 3 "FATAL" app.log    # 3 lines BEFORE each match (Before)
grep -C 2 "ERROR" app.log    # 2 lines AROUND each match (Context)

# ─── Real-world pipelines ────────────────────────────────────────────
# Find all ERROR lines in the last 500 lines AND show their context
tail -500 /var/log/nexusos/app.log | grep -B1 -A1 "ERROR"

# Count errors per minute for the last hour (structured JSON logs)
journalctl -u pokevend --since "1 hour ago" --no-pager -o cat | \
    grep '"level":"error"' | \
    grep -oE '"time":"[^"]*"' | \
    grep -oE '"[0-9]{2}:[0-9]{2}' | \
    sort | uniq -c

# Find which Go source files have hardcoded database URLs
grep -rn "postgres://" Pokemon/server/ --include="*.go" | grep -v "_test.go"
```

### awk — The Column Engine

awk processes each line as "fields" separated by a delimiter (default: whitespace).
Think of it as a mini-programming language for rows and columns.

```bash
# ─── Field extraction ─────────────────────────────────────────────────
# $1=first field, $2=second, ..., $NF=last field, $0=entire line

# Nginx access log:
# 192.168.1.1 - - [01/Apr/2026:14:30:00] "GET /api/v1/cards HTTP/1.1" 200 1234
awk '{print $1}'    access.log   # All client IPs
awk '{print $9}'    access.log   # All HTTP status codes
awk '{print $7}'    access.log   # All request URLs (the path)
awk '{print $1, $9, $7}' access.log  # IP, status, URL — space separated

# ─── Filtering with awk ────────────────────────────────────────────────
awk '$9 >= 400'         access.log   # Only errors (status >= 400)
awk '$9 == "500"'       access.log   # Only 500s
awk '/api\/v1\/cards/'  access.log   # Lines matching a regex
awk '$9 >= 400 && $1 != "127.0.0.1"' access.log  # Errors not from localhost

# ─── Custom delimiters ────────────────────────────────────────────────
awk -F: '{print $1}' /etc/passwd       # Use : as delimiter → prints usernames
awk -F= '{print $2}' /etc/nexusos/config.env  # Print values from KEY=VALUE pairs

# ─── awk as a calculator ──────────────────────────────────────────────
# Calculate total bytes served from Nginx logs (column 10 = bytes)
awk '{total += $10} END {print "Total bytes:", total}' access.log

# Calculate average response time from Go JSON logs
# Log format: {"time":"...","duration_ms":145,"path":"/api/v1/cards"}
awk -F'"duration_ms":' '{split($2,a,","); sum+=a[1]; count++} \
    END {printf "Avg duration: %.2f ms\n", sum/count}' app.log

# ─── NR, NF, FNR special variables ────────────────────────────────────
# NR  = current line number (across ALL files)
# FNR = current line number within current file
# NF  = number of fields in current line

awk 'NR > 1'    file.txt      # Skip header line (process from line 2)
awk 'NR % 10 == 0' file.txt   # Every 10th line (sampling)
awk 'NF > 5'    file.txt      # Lines with more than 5 fields

# ─── BEGIN and END blocks ─────────────────────────────────────────────
# BEGIN: runs BEFORE any lines are processed (good for printing headers)
# END: runs AFTER all lines are processed (good for totals/summaries)

awk '
BEGIN {
    print "=== Error Report ==="
    print "IP Address       | Count | Last URL"
    print "-----------------|-------|----------"
    FS="\t"   # Set field separator for input
    OFS=" | " # Set field separator for output
}
$9 >= 400 {
    errors[$1]++
    last_url[$1] = $7
}
END {
    for (ip in errors) {
        print ip, errors[ip], last_url[ip]
    }
    print "Total unique IPs with errors:", length(errors)
}
' access.log

# ─── Project-relevant awk: parse docker stats ────────────────────────
# docker stats --no-stream output:
# CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT   MEM %
# abc123         nexusos-postgres     2.5%      150MiB / 8GiB      1.8%

docker stats --no-stream | awk '
NR > 1 {
    name = $2
    cpu  = $3
    mem  = $4
    # gsub removes the % sign for numeric comparisons
    gsub(/%/, "", cpu)
    if (cpu+0 > 80) print "HIGH CPU:", name, cpu "%"
    if (cpu+0 > 2)  print "Service:", name, "CPU:", cpu "%", "Mem:", mem
}
'
```

### sed — The Stream Transformer

sed makes transformations to text as it flows through. Think of it as
a find-and-replace that understands patterns and works on streams.

```bash
# ─── Basic substitution ───────────────────────────────────────────────
# s/pattern/replacement/flags
sed 's/localhost/prod-db.nexusos.internal/' config.env   # First match per line
sed 's/localhost/prod-db.nexusos.internal/g' config.env  # ALL matches (g=global)
sed 's/localhost/prod-db.nexusos.internal/gi' config.env # Case-insensitive

# ─── In-place editing (-i) ────────────────────────────────────────────
sed -i 's/DEBUG/WARN/' /etc/nexusos/config.env   # Edit file directly
sed -i.bak 's/DEBUG/WARN/' config.env  # Edit and save backup as config.env.bak

# ─── Line selection ────────────────────────────────────────────────────
sed -n '10,20p'  file.txt    # Print only lines 10-20
sed '10,20d'     file.txt    # Delete lines 10-20
sed '/^#/d'      config.env  # Delete comment lines
sed '/^$/d'      file.txt    # Delete blank lines
sed '1d'         file.txt    # Delete first line (skip header)

# ─── Real-world patterns ──────────────────────────────────────────────

# Redact passwords in log output (for sharing reports safely)
docker logs nexusos-postgres 2>&1 | sed 's/password=[^&]*/password=REDACTED/gi'

# Extract just values from a .env file (strip KEY=)
cat /etc/nexusos/config.env | grep -v '^#' | sed 's/^[^=]*=//'

# Update a version number in a config file
sed -i "s/^VERSION=.*/VERSION=${NEW_VERSION}/" /etc/nexusos/config.env

# Apply a nginx config template for a new environment
sed -e "s|{{DOMAIN}}|pokevend.com|g" \
    -e "s|{{UPSTREAM}}|127.0.0.1:8080|g" \
    -e "s|{{ENV}}|prod|g" \
    nginx.conf.template > /etc/nginx/sites-available/pokevend

# ─── THE PIPELINE COMBINATION ─────────────────────────────────────────
# Extract top 10 client IPs hitting 500 errors in the last hour
journalctl -u nginx --since "1 hour ago" --no-pager |
    grep '" 5[0-9][0-9] ' |            # Only 5xx lines
    awk '{print $1}' |                  # Extract IP (first field)
    sort |                              # Sort for uniq
    uniq -c |                           # Count per IP
    sort -rn |                          # Highest count first
    head -10 |                          # Top 10
    sed 's/^[[:space:]]*//' |           # Trim leading spaces
    awk '{print "IP:", $2, "| Requests:", $1}'  # Format nicely
```

---

## CHAPTER 7: Input, Output, and Redirection

Understanding how data flows is what makes you a pipeline master.

```bash
# The three standard file descriptors every process has:
# 0 = stdin  (reads FROM here — keyboard by default)
# 1 = stdout (writes TO here — terminal by default)
# 2 = stderr (errors go TO here — terminal by default)

# ─── Redirection ─────────────────────────────────────────────────────
command > file.txt      # Redirect stdout to file (overwrites)
command >> file.txt     # Redirect stdout to file (appends)
command < file.txt      # Read stdin from file
command 2> errors.txt   # Redirect stderr to file
command 2>&1            # Merge stderr INTO stdout (both go to stdout)
command &> file.txt     # Redirect both stdout AND stderr to file
command > /dev/null     # Throw away stdout (silence success output)
command 2>/dev/null     # Throw away stderr (silence errors)
command &>/dev/null     # Throw away ALL output (run silently)

# ─── Pipes ───────────────────────────────────────────────────────────
# A pipe connects stdout of left to stdin of right
ps aux | grep pokevend | grep -v grep

# ─── Process Substitution — Advanced ─────────────────────────────────
# <(command) creates a temporary file that contains command's output
# You can use it wherever a filename is expected

# Compare current config with the known-good backup
diff <(cat /etc/nexusos/config.env) <(cat /etc/nexusos/config.env.bak)

# Read from MULTIPLE sources as if they were one file
cat <(journalctl -u pokevend --no-pager) \
    <(docker logs nexusos-postgres 2>&1) | grep -i error

# ─── Heredocs — Writing multi-line content ────────────────────────────
cat <<EOF > /etc/nexusos/config.env
# NexusOS Configuration
# Generated: $(date --iso-8601=seconds)
APP_PORT=8080
DB_HOST=${DB_HOST:-localhost}
DB_PORT=5432
DB_NAME=nexusos
REDIS_ADDR=localhost:6379
LOG_LEVEL=${LOG_LEVEL:-info}
EOF
# Note: Variables ARE expanded in heredocs (use <<'EOF' to prevent expansion)

# Here-string — pass a string as stdin to a command
read -r db_version <<< "$(docker exec nexusos-postgres psql -U nexusos -t -c 'SELECT version();' 2>/dev/null)"
echo "DB version: ${db_version}"

# ─── tee — Write to file AND stdout simultaneously ─────────────────────
# Critical for scripts that need to log AND show output live
./deploy.sh | tee /var/log/nexusos/deployments.log
# Output goes to terminal AND to the log file at the same time
```

---

## CHAPTER 8: Arrays — Data Structures in Bash

```bash
# ─── Indexed Arrays ──────────────────────────────────────────────────
SERVICES=("pokevend" "nexusos-postgres" "nexusos-redis" "nexusos-kafka")
PORTS=(8080 5432 6379 9092)

# Access
echo "${SERVICES[0]}"       # pokevend (0-indexed)
echo "${SERVICES[-1]}"      # nexusos-kafka (last element)
echo "${#SERVICES[@]}"      # 4 (count of elements)
echo "${SERVICES[@]}"       # All elements (space-separated)
echo "${!SERVICES[@]}"      # All indices (0 1 2 3)

# Iteration — ALWAYS use "${array[@]}" (not $array which only gives first element)
for service in "${SERVICES[@]}"; do
    systemctl status "${service}" --no-pager -l 2>/dev/null | head -3
done

# Iteration with index  
for i in "${!SERVICES[@]}"; do
    printf "Port %d → %s\n" "${PORTS[$i]}" "${SERVICES[$i]}"
done

# Append
SERVICES+=("nexusos-qdrant")     # Add one element
SERVICES+=("temporal" "ollama")  # Add multiple

# Slice
echo "${SERVICES[@]:1:2}"    # Elements 1 and 2 (skip first)
echo "${SERVICES[@]:0:2}"    # First 2 elements

# ─── Associative Arrays (Maps/Dictionaries) ────────────────────────────
declare -A SERVICE_PORTS      # Must declare -A for associative arrays!
SERVICE_PORTS["pokevend"]=8080
SERVICE_PORTS["postgres"]=5432
SERVICE_PORTS["redis"]=6379
SERVICE_PORTS["kafka"]=9092

# Access
echo "${SERVICE_PORTS["pokevend"]}"    # 8080
echo "${!SERVICE_PORTS[@]}"           # All keys
echo "${SERVICE_PORTS[@]}"            # All values

# Iteration over key:value pairs
for service in "${!SERVICE_PORTS[@]}"; do
    port="${SERVICE_PORTS[$service]}"
    if nc -zv "localhost" "${port}" &>/dev/null; then
        echo "✓ ${service} is listening on ${port}"
    else
        echo "✗ ${service} is NOT listening on ${port}"
    fi
done

# ─── mapfile / readarray — Load file into array ───────────────────────
# Load all config lines into an array
mapfile -t CONFIG_LINES < /etc/nexusos/config.env   # -t strips newlines
for line in "${CONFIG_LINES[@]}"; do
    [[ "${line}" =~ ^[[:space:]]*# ]] && continue   # Skip comments
    echo "Config: ${line}"
done
```

---

## CHAPTER 9: Error Handling — Production-Grade Scripts

```bash
# ─── The strict mode trinity (you already know this!) ─────────────────
set -euo pipefail

# ─── Fail with context ────────────────────────────────────────────────
die() {
    # Print error and exit — the standard pattern
    echo "[$(date '+%H:%M:%S')] ERROR: $*" >&2
    exit 1
}

[[ -f "/etc/nexusos/config.env" ]] || die "Config file not found. Run provisioner first."

# ─── Retry pattern — for flaky operations ─────────────────────────────
retry() {
    local max_attempts="$1"
    local delay="$2"
    shift 2
    local cmd=("$@")
    local attempt=1
    
    while (( attempt <= max_attempts )); do
        if "${cmd[@]}"; then
            return 0
        fi
        echo "Attempt ${attempt}/${max_attempts} failed. Retrying in ${delay}s..." >&2
        sleep "${delay}"
        (( attempt++ ))
    done
    
    echo "All ${max_attempts} attempts failed for: ${cmd[*]}" >&2
    return 1
}

# Usage:
retry 5 2 curl -sf http://localhost:8080/health   # Try 5 times, 2s between each

# ─── The || { } fail block ────────────────────────────────────────────
# Execute a whole block if a command fails

go build -o /opt/pokevend/pokevend ./... || {
    echo "Build failed!" >&2
    systemctl start pokevend  # Roll back — restart old version
    exit 1
}

# ─── Trap for cleanup (full pattern) ──────────────────────────────────
TMPDIR_WORK=$(mktemp -d)
trap 'rm -rf "${TMPDIR_WORK}"; echo "Cleaned up temp files"' EXIT
trap 'echo "Script interrupted by user"; exit 130' INT TERM

# Everything in TMPDIR_WORK will be automatically cleaned up
# even if the script crashes or is Ctrl+C'd
```

---

## CHAPTER 10: Practical Projects — Apply Everything

### PROJECT A: The NexusOS Daily Health Report
Combine ALL the above to build this. It should:
1. Audit all services (systemd + docker)
2. Parse the last hour of Pokevend logs for errors
3. Check disk and memory
4. Output a structured markdown report
5. Be schedulable via cron

### PROJECT B: The Config Drift Detector
Build a script that:
1. Records the "known good" state of all config files (checksums)
2. On subsequent runs, detect if any config has changed unexpectedly
3. Report the exact diff if something has changed
4. Alert if critical configs (nginx, sshd) were modified

### PROJECT C: The Deployment Lock
Build a script that:
1. Creates a "lock file" at the start of deployment (`/tmp/nexusos.lock`)
2. Detects if another deployment is already running (lock file exists)
3. Refuses to start if locked
4. Cleans up the lock file even if it crashes (via trap)

---

## ⚡ BASH CHEAT SHEET — COMMIT TO MEMORY

```bash
# Variables
${VAR:-default}      # Use default if VAR unset
${VAR:?error_msg}    # Exit if VAR unset
${#VAR}              # String length
${VAR##*/}           # basename (strip leading path)
${VAR%/*}            # dirname (strip trailing component)
${VAR/old/new}       # Replace first match
${VAR//old/new}      # Replace all matches
${VAR,,}             # Lowercase
${VAR^^}             # Uppercase

# Tests (inside [[ ]])
-f    file exists and is regular file
-d    is directory
-z    string is empty
-n    string is non-empty
-r    is readable
-x    is executable
-s    file exists and has size > 0

# Process control
command &            # Run in background
wait $!              # Wait for background job
jobs                 # List background jobs
$(command)           # Command substitution (capture output)
$((expr))            # Arithmetic

# Redirection
> file    stdout to file (overwrite)
>> file   stdout to file (append)  
2>&1      stderr → stdout
&>        both to file
/dev/null discard output

# Arrays
declare -A MAP       # Associative array
${arr[@]}            # All elements
${!arr[@]}           # All indices/keys
${#arr[@]}           # Count

# Loops
for x in "${arr[@]}"; do ... done
while IFS= read -r line; do ... done < file
for ((i=0; i<N; i++)); do ... done
```
