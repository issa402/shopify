# Bash For Infrastructure Engineering And Automation

This is not a tiny command cheat sheet. This is a practical Bash field manual for becoming dangerous in infrastructure engineering, scripting, automation, Linux operations, log analysis, Docker operations, and troubleshooting.

The goal is simple:

You should be able to sit at a Linux terminal, look at a broken system, write a script, collect facts, check health, parse logs, explain what is happening, and automate the fix safely.

If you feel like you know nothing, perfect. Bash is confusing because it mixes:

- Linux commands
- shell syntax
- process control
- text processing
- filesystems
- permissions
- networking
- environment variables
- exit codes
- quoting rules
- automation habits

This guide starts from the ground and builds the intuition.

## The Big Mental Model

Bash is the control room for Linux.

Python is great when you need data structures, APIs, bigger applications, or maintainable business logic.

Bash is great when you need to glue operating-system tools together:

- Start services
- Stop services
- Check ports
- Inspect files
- Parse logs
- Run Docker commands
- Call health endpoints
- Move backups around
- Validate environment variables
- Run deployment steps
- Create reports
- Fail fast when something is unsafe
- Automate the exact commands you would type manually

For infrastructure engineering, Bash is not just "programming." It is operational muscle.

You use Bash when the problem sounds like:

- "Check if all services are healthy."
- "Find what is listening on port 3001."
- "Show the top errors in the last 30 minutes."
- "Restart this container only if it is stopped."
- "Back up this config before editing it."
- "Fail the deployment if the database is not ready."
- "Scan these logs and tell me if auth failures are spiking."
- "Make this repeated manual workflow one command."

## What Actually Happens When You Type A Command

When you type:

```bash
ls -la /var/log
```

Bash does roughly this:

1. Reads your text.
2. Splits it into words.
3. Expands variables, globs, command substitutions, and quotes.
4. Finds the executable named `ls`.
5. Starts a process.
6. Passes arguments `-la` and `/var/log` to that process.
7. Waits for it to finish.
8. Stores the exit code in `$?`.

The command is not "Bash" itself. Bash is the shell that launches the command.

This distinction matters:

- `cd`, `export`, `alias`, `set`, `source` are shell builtins.
- `ls`, `grep`, `awk`, `sed`, `curl`, `docker`, `systemctl` are external programs.

Check with:

```bash
type cd
type grep
type docker
```

## The First Commands An Infra Engineer Must Own

### Navigation

```bash
pwd
ls
ls -la
cd /path/to/dir
cd ..
cd -
```

Meaning:

- `pwd` prints your current directory.
- `ls` lists files.
- `ls -la` lists hidden files, permissions, owners, sizes, and dates.
- `cd ..` moves up one directory.
- `cd -` jumps back to the previous directory.

### Files And Directories

```bash
touch file.txt
mkdir logs
mkdir -p scripts/logs
cp source target
cp -r dir backup-dir
mv old new
rm file
rm -r dir
```

Be careful with `rm -r`. It removes directories recursively. In real infrastructure work, destructive commands need caution.

Safer habits:

```bash
ls -la target
du -sh target
rm -i file
```

`-i` asks before deleting.

### Reading Files

```bash
cat file
less file
head file
tail file
tail -f file
sed -n '1,120p' file
```

Use:

- `cat` for short files.
- `less` for long files.
- `head` for beginning.
- `tail` for end.
- `tail -f` for live logs.
- `sed -n '1,120p'` to print specific line ranges.

### Searching

Prefer `rg` when available:

```bash
rg "DATABASE_URL"
rg -n "error|fatal|panic"
rg --files
```

Classic tools:

```bash
grep "error" app.log
grep -i "error" app.log
grep -r "redis" services/
grep -n "TODO" file
```

Meaning:

- `-i` means case-insensitive.
- `-r` means recursive.
- `-n` means show line numbers.

## Command Anatomy

Command:

```bash
docker compose up -d --build
```

Parts:

- `docker` is the program.
- `compose` is a subcommand.
- `up` is another subcommand/action.
- `-d` is a short flag.
- `--build` is a long flag.

Command:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/health
```

Meaning:

- `curl` makes an HTTP request.
- `-s` means silent.
- `-o /dev/null` throws away the response body.
- `-w "%{http_code}"` prints only the HTTP status code.
- The URL is the target.

This is the foundation of health checks.

## Exit Codes

Every command returns an exit code.

- `0` means success.
- Non-zero means failure.

Example:

```bash
ls /tmp
echo $?

ls /does/not/exist
echo $?
```

`$?` stores the exit code of the last command.

Infra scripts use exit codes constantly:

```bash
if curl -fsS http://localhost:3001/health >/dev/null; then
  echo "API is healthy"
else
  echo "API is down"
  exit 1
fi
```

Why this matters:

- CI/CD checks exit codes.
- Cron jobs check exit codes.
- Git hooks check exit codes.
- Deploy scripts check exit codes.
- Health scripts check exit codes.

If your script exits `0`, automation thinks everything is fine.

If your script exits `1`, automation knows something failed.

## Standard Streams

Every process has three default streams:

- `stdin` = input = file descriptor `0`
- `stdout` = normal output = file descriptor `1`
- `stderr` = error output = file descriptor `2`

Example:

```bash
echo "normal output"
echo "error output" >&2
```

`>&2` means send this message to stderr.

Why infra engineers care:

- Normal output can be parsed by another tool.
- Error output can be logged separately.
- Scripts should print machine-readable results to stdout and human errors to stderr.

Redirect examples:

```bash
command > output.txt
command >> output.txt
command 2> errors.txt
command > all.log 2>&1
command >/dev/null 2>&1
```

Meaning:

- `>` overwrites stdout.
- `>>` appends stdout.
- `2>` redirects stderr.
- `2>&1` sends stderr to wherever stdout is going.
- `/dev/null` is the Linux black hole.

Common infra pattern:

```bash
docker exec pokemontool_postgres pg_isready -U pokemontool_user >/dev/null 2>&1
```

This means:

"Run the database readiness check, but do not print noise. I only care if it succeeds or fails."

## Pipes

A pipe sends stdout from one command into stdin of another command.

```bash
cat app.log | grep ERROR
```

Better:

```bash
grep ERROR app.log
```

But pipes become powerful when chaining:

```bash
docker compose logs --tail=500 |
  grep -i "error" |
  sort |
  uniq -c |
  sort -rn
```

Meaning:

1. Get recent Docker logs.
2. Keep only error lines.
3. Sort them.
4. Count duplicates.
5. Sort highest count first.

This is infrastructure analysis.

## Variables

Basic variable:

```bash
name="postgres"
echo "$name"
```

No spaces around `=`.

Correct:

```bash
PORT="3001"
```

Wrong:

```bash
PORT = "3001"
```

Why wrong? Bash thinks `PORT` is a command and `=` and `"3001"` are arguments.

Always quote variable usage:

```bash
echo "$PORT"
```

Why?

If a variable has spaces, unquoted usage splits it apart.

Bad:

```bash
file="my config.txt"
cat $file
```

Good:

```bash
cat "$file"
```

## Environment Variables

Shell variables exist inside the current shell.

Environment variables are inherited by child processes.

```bash
DATABASE_URL="postgres://local"
echo "$DATABASE_URL"
```

Only Bash sees that variable unless you export it:

```bash
export DATABASE_URL="postgres://local"
python app.py
```

Infra scripts often read env vars:

```bash
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
```

`${DB_HOST:-localhost}` means:

"Use `$DB_HOST` if it exists and is not empty. Otherwise use `localhost`."

This is how scripts get safe defaults.

## Important Parameter Expansion Syntax

```bash
${VAR:-default}
```

Use default if VAR is empty or unset.

```bash
${VAR-default}
```

Use default only if VAR is unset.

```bash
${VAR:?message}
```

Fail if VAR is empty or unset.

Example:

```bash
DATABASE_URL="${DATABASE_URL:?DATABASE_URL must be set}"
```

This is great for deployment scripts.

```bash
${file%.log}
```

Remove suffix `.log`.

```bash
${path##*/}
```

Get basename-like value.

Example:

```bash
path="/var/log/nginx/access.log"
echo "${path##*/}"
```

Prints:

```text
access.log
```

## Quoting Rules

Single quotes preserve text literally:

```bash
echo '$HOME'
```

Prints:

```text
$HOME
```

Double quotes allow variables:

```bash
echo "$HOME"
```

Prints your home directory.

No quotes means Bash can split words and expand globs:

```bash
echo *.md
```

This expands to matching Markdown files.

Infra rule:

Quote variables unless you intentionally want splitting or glob expansion.

## Command Substitution

Command substitution runs a command and stores its output.

```bash
today="$(date +%F)"
echo "$today"
```

Common repo-root pattern:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
```

Meaning:

- `${BASH_SOURCE[0]}` is the script file path.
- `dirname` gets its directory.
- `cd ... && pwd` gives the absolute path.

Why use this?

So your script works no matter where you run it from.

Example:

```bash
cd /tmp
bash /home/you/project/scripts/health-check.sh
```

The script can still find the project root.

## Tests: `[ ]` And `[[ ]]`

Old style:

```bash
if [ -f "$file" ]; then
  echo "file exists"
fi
```

Better Bash style:

```bash
if [[ -f "$file" ]]; then
  echo "file exists"
fi
```

Common file tests:

```bash
[[ -f "$path" ]]  # regular file
[[ -d "$path" ]]  # directory
[[ -r "$path" ]]  # readable
[[ -w "$path" ]]  # writable
[[ -x "$path" ]]  # executable
[[ -s "$path" ]]  # exists and not empty
```

String tests:

```bash
[[ -z "$value" ]]  # empty
[[ -n "$value" ]]  # not empty
[[ "$a" == "$b" ]]
[[ "$line" == *ERROR* ]]
```

Regex:

```bash
if [[ "$status" =~ ^2[0-9][0-9]$ ]]; then
  echo "success status"
fi
```

## Math

Bash math uses `(( ))`.

```bash
count=0
((count++))
((count += 5))

if (( count > 10 )); then
  echo "high count"
fi
```

Do not use Bash for serious decimal math. Use `awk`, `bc`, Python, or another tool.

Example with `awk`:

```bash
awk 'BEGIN { print 10 / 3 }'
```

## If Statements

Basic:

```bash
if command; then
  echo "command succeeded"
else
  echo "command failed"
fi
```

Real infra example:

```bash
if docker ps --format '{{.Names}}' | grep -qx "pokemontool_postgres"; then
  echo "postgres container is running"
else
  echo "postgres container is not running"
fi
```

HTTP example:

```bash
status="$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/health || echo 000)"

if [[ "$status" == "200" ]]; then
  echo "API healthy"
else
  echo "API unhealthy: HTTP $status"
  exit 1
fi
```

## Case Statements

Use `case` for command-line options or known choices.

```bash
case "${1:-}" in
  start)
    echo "starting"
    ;;
  stop)
    echo "stopping"
    ;;
  *)
    echo "usage: $0 start|stop"
    exit 2
    ;;
esac
```

Important syntax:

- `case value in` starts.
- `pattern)` matches.
- `;;` ends a case block.
- `*)` is default.
- `esac` ends the case statement.

## Loops

For loop:

```bash
for service in postgres redis rabbitmq; do
  echo "checking $service"
done
```

While loop reading lines:

```bash
while IFS= read -r line; do
  echo "line: $line"
done < file.txt
```

Why `IFS= read -r`?

- `IFS=` preserves leading/trailing spaces.
- `-r` prevents backslash escaping.

This is the safe way to read lines.

Loop over command output carefully:

Bad for paths with spaces:

```bash
for file in $(find . -type f); do
  echo "$file"
done
```

Better:

```bash
find . -type f -print0 |
  while IFS= read -r -d '' file; do
    echo "$file"
  done
```

`-print0` and `-d ''` handle spaces safely.

## Functions

Functions let you turn repeated logic into a named operation.

```bash
log_info() {
  local message="$1"
  echo "[INFO] $message" >&2
}

log_info "starting health check"
```

Use `local` inside functions:

```bash
check_endpoint() {
  local name="$1"
  local url="$2"
  local expected="$3"
  local status

  status="$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo 000)"

  if [[ "$status" == "$expected" ]]; then
    echo "OK $name HTTP $status"
  else
    echo "FAIL $name HTTP $status expected $expected" >&2
    return 1
  fi
}
```

Why `return 1` instead of `exit 1`?

- `return` fails the function but lets the caller decide what to do.
- `exit` kills the whole script immediately.

Use `exit` at the top-level when the whole script should stop.

## Arguments

Inside a script:

```bash
$0  # script name
$1  # first argument
$2  # second argument
$@  # all arguments, preserved separately when quoted
$#  # number of arguments
```

Example:

```bash
#!/usr/bin/env bash
set -euo pipefail

name="${1:-world}"
echo "hello $name"
```

Run:

```bash
bash hello.sh Issa
```

## `shift`

`shift` moves arguments left.

Before:

```text
$1=--since
$2=1h
$3=--service
$4=api
```

After one `shift`:

```text
$1=1h
$2=--service
$3=api
```

Argument parser:

```bash
since="1h"
service=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)
      since="${2:?--since requires a value}"
      shift 2
      ;;
    --service)
      service="${2:?--service requires a value}"
      shift 2
      ;;
    --help)
      echo "usage: $0 [--since 1h] [--service name]"
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done
```

This pattern is everywhere in real scripts.

## Arrays

Arrays hold lists.

```bash
services=(postgres redis rabbitmq)

for service in "${services[@]}"; do
  echo "$service"
done
```

Important:

Use `"${array[@]}"`, not `${array[*]}` most of the time.

`"${array[@]}"` preserves each item separately.

Associative arrays:

```bash
declare -A ports=(
  [api]=3001
  [web]=5173
  [postgres]=5432
)

echo "${ports[api]}"
```

Associative arrays are useful for service maps.

## Strict Mode

Most production-ish scripts should start with:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

Meaning:

- `-e`: exit if a command fails.
- `-u`: fail if using an unset variable.
- `-o pipefail`: fail a pipeline if any command inside it fails.

Example without pipefail:

```bash
grep "ERROR" missing.log | wc -l
```

`grep` fails because the file is missing, but `wc -l` may still succeed. Without `pipefail`, the script might think the whole pipeline succeeded.

With `pipefail`, the failure is caught.

Important warning:

`set -e` has edge cases. Commands inside `if command; then` can fail without killing the script, because the failure is being tested.

This is good:

```bash
if grep -q "ERROR" app.log; then
  echo "errors found"
else
  echo "no errors"
fi
```

## `trap`

`trap` runs cleanup code when something happens.

Common use:

```bash
tmpfile="$(mktemp)"
trap 'rm -f "$tmpfile"' EXIT
```

Meaning:

"No matter how the script exits, remove the temp file."

Signal cleanup:

```bash
cleanup() {
  echo "stopping background processes"
  kill "$api_pid" "$worker_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM
```

Meaning:

- `EXIT` runs when script exits.
- `INT` is usually Ctrl-C.
- `TERM` is a polite termination signal.

This is critical for scripts that start background processes.

## Background Processes And `$!`

Run in background:

```bash
python -m http.server 8000 &
server_pid=$!
```

`$!` is the PID of the most recent background process.

Wait for it:

```bash
wait "$server_pid"
```

Kill it:

```bash
kill "$server_pid"
```

Infra startup scripts use this when they start a Go API, Python API, worker, or watcher.

## Permissions And Executable Scripts

Make a script executable:

```bash
chmod +x scripts/health-check.sh
```

Run it:

```bash
./scripts/health-check.sh
```

Or without executable bit:

```bash
bash scripts/health-check.sh
```

Read permissions:

```bash
ls -la scripts/health-check.sh
```

Example:

```text
-rwxrwxr-x
```

Meaning:

- First char `-` means regular file.
- Owner has `rwx`.
- Group has `rwx`.
- Others have `r-x`.

Numbers:

- `r = 4`
- `w = 2`
- `x = 1`
- `7 = 4+2+1 = rwx`
- `5 = 4+1 = r-x`

`chmod 755 script.sh` means owner can read/write/execute, everyone else can read/execute.

## Grep

`grep` finds lines.

```bash
grep "ERROR" app.log
grep -i "error" app.log
grep -E "ERROR|FATAL|PANIC" app.log
grep -v "health" app.log
grep -c "ERROR" app.log
grep -q "ready" app.log
```

Meaning:

- `-i`: ignore case.
- `-E`: extended regex.
- `-v`: invert match.
- `-c`: count matches.
- `-q`: quiet mode, only exit code matters.

Health check pattern:

```bash
if docker exec pokemontool_redis redis-cli ping | grep -q PONG; then
  echo "redis ok"
else
  echo "redis failed"
fi
```

## Awk

`awk` is for columns, records, counters, math, and reports.

Print first column:

```bash
awk '{print $1}' access.log
```

Print first and ninth columns:

```bash
awk '{print $1, $9}' access.log
```

Count status code families:

```bash
awk '{
  if ($9 ~ /^2/) ok++
  else if ($9 ~ /^4/) client_errors++
  else if ($9 ~ /^5/) server_errors++
}
END {
  print "2xx:", ok+0
  print "4xx:", client_errors+0
  print "5xx:", server_errors+0
}' access.log
```

Important awk ideas:

- `$1`, `$2`, `$3` are fields.
- `$0` is the whole line.
- `NF` is number of fields.
- `NR` is current line number.
- `BEGIN` runs before input.
- `END` runs after input.
- `~` means regex match.

Pass Bash variable into awk:

```bash
threshold=100
awk -v threshold="$threshold" '$1 > threshold { print }' numbers.txt
```

## Sed

`sed` transforms text.

Print lines:

```bash
sed -n '1,20p' file
```

Replace text:

```bash
sed 's/old/new/' file
```

Replace globally on each line:

```bash
sed 's/error/ERROR/g' file
```

Delete blank lines:

```bash
sed '/^$/d' file
```

Infrastructure use:

- Clean logs.
- Normalize output.
- Extract parts of config.
- Preview replacements before editing.

Be careful with in-place editing:

```bash
sed -i.bak 's/old/new/g' config.conf
```

This creates a backup file.

## Sort, Uniq, Head

Top repeated errors:

```bash
grep -i "error" app.log |
  sort |
  uniq -c |
  sort -rn |
  head
```

Top IPs from Nginx:

```bash
awk '{print $1}' /var/log/nginx/access.log |
  sort |
  uniq -c |
  sort -rn |
  head -10
```

Mental model:

- `sort` groups equal lines together.
- `uniq -c` counts repeated adjacent lines.
- `sort -rn` sorts numeric reverse.
- `head` takes the top.

## Find

Find files:

```bash
find . -type f -name "*.log"
find . -type f -size +50M
find . -type d -name "node_modules"
```

Case-insensitive:

```bash
find . -type f -iname "*readme*"
```

Delete carefully:

```bash
find . -type f -name "*.tmp" -print
```

Only after reviewing:

```bash
find . -type f -name "*.tmp" -delete
```

Large-file check:

```bash
find . -path './.git' -prune -o -type f -size +50M -print
```

Meaning:

- `-path './.git' -prune` skips `.git`.
- `-o` means OR.
- `-type f` means files only.
- `-size +50M` means bigger than 50 MB.
- `-print` prints matches.

## Xargs

`xargs` turns input lines into command arguments.

Example:

```bash
find . -name "*.log" -print0 | xargs -0 du -h
```

Use `-print0` and `xargs -0` to handle spaces safely.

Parallel-ish example:

```bash
printf '%s\0' postgres redis rabbitmq | xargs -0 -n1 docker compose logs --tail=20
```

Use with caution. `xargs rm` can be destructive.

## Networking Commands

Check listening ports:

```bash
ss -tulpn
sudo ss -tulpn
```

Meaning:

- `-t`: TCP
- `-u`: UDP
- `-l`: listening
- `-p`: process
- `-n`: numeric ports

Check one port:

```bash
ss -tulpn | grep ':3001'
```

Check TCP connection:

```bash
nc -vz localhost 3001
```

Curl endpoint:

```bash
curl -i http://localhost:3001/health
```

Only status code:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3001/health
```

DNS:

```bash
getent hosts github.com
dig github.com
```

Route:

```bash
ip route
```

Interfaces:

```bash
ip addr
```

## Processes

List processes:

```bash
ps aux
ps aux --sort=-%cpu | head
ps aux --sort=-%mem | head
```

Find process:

```bash
pgrep -a redis
pgrep -af "go run"
```

Kill process:

```bash
kill PID
kill -TERM PID
kill -9 PID
```

Use `kill -9` only when normal termination fails. `-9` does not let the process clean up.

Find process using a port:

```bash
lsof -t -i :3001
```

Kill process on port:

```bash
pid="$(lsof -t -i :3001 || true)"
if [[ -n "$pid" ]]; then
  kill "$pid"
fi
```

## Systemd And Logs

Check service:

```bash
systemctl status nginx
systemctl is-active nginx
systemctl is-enabled nginx
```

Start/stop/reload:

```bash
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl reload nginx
```

Logs:

```bash
journalctl -u nginx --since "30 minutes ago"
journalctl -u nginx -f
journalctl -xe
```

Meaning:

- `-u nginx`: service unit.
- `--since`: time window.
- `-f`: follow live.
- `-xe`: jump to recent logs with extra explanation.

## Docker And Bash

Docker is where Bash becomes very infra-heavy.

List containers:

```bash
docker ps
docker ps -a
```

Get only IDs:

```bash
docker ps -q
docker ps -aq
```

Filter by exact name:

```bash
docker ps -q -f "name=^pokemontool_postgres$"
```

Meaning:

- `-q` quiet: only IDs.
- `-f` filter.
- `^` start of string.
- `$` end of string.

Check logs:

```bash
docker compose logs --tail=50
docker compose logs --since "30m" rabbitmq
docker logs container_name --tail=100
```

Run command inside container:

```bash
docker exec pokemontool_redis redis-cli ping
docker exec pokemontool_postgres pg_isready -U pokemontool_user
```

Compose:

```bash
docker compose up -d
docker compose down
docker compose ps
docker compose config --services
docker compose restart api
```

Common container ensure function:

```bash
ensure_container() {
  local service_name="$1"
  local container_name="$2"

  local running_id
  local existing_id

  running_id="$(docker ps -q -f "name=^${container_name}$")"
  existing_id="$(docker ps -aq -f "name=^${container_name}$")"

  if [[ -n "$running_id" ]]; then
    echo "$container_name is already running"
  elif [[ -n "$existing_id" ]]; then
    echo "$container_name exists but is stopped; starting"
    docker start "$container_name"
  else
    echo "$container_name does not exist; creating with compose"
    docker compose up -d "$service_name"
  fi
}
```

This is the kind of function infrastructure engineers write all the time.

## Writing A Professional Script Skeleton

Use this starting point:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log_info() {
  printf '[INFO] %s\n' "$*" >&2
}

log_error() {
  printf '[ERROR] %s\n' "$*" >&2
}

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log_error "required command not found: $cmd"
    exit 1
  fi
}

main() {
  require_command docker
  require_command curl

  log_info "project root: $PROJECT_ROOT"
}

main "$@"
```

Why this is professional:

- Strict mode catches mistakes.
- Script paths are stable.
- Logging goes to stderr.
- Dependency checks fail early.
- `main "$@"` makes flow clear.

## Health Check Script Pattern

Health checks answer:

"Can the system do what it is supposed to do right now?"

Example:

```bash
#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

check_endpoint() {
  local name="$1"
  local url="$2"
  local expected="$3"
  local status

  status="$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo 000)"

  if [[ "$status" == "$expected" ]]; then
    echo -e "${GREEN}OK${NC} $name HTTP $status"
  else
    echo -e "${RED}FAIL${NC} $name HTTP $status expected $expected" >&2
    return 1
  fi
}

failed=0

check_endpoint "Go API" "http://localhost:3001/health" 200 || failed=1
check_endpoint "Web App" "http://localhost:5173" 200 || failed=1

if (( failed > 0 )); then
  echo "one or more checks failed" >&2
  exit 1
fi

echo "all checks passed"
```

Important idea:

This script checks all endpoints before failing. That gives you a full report instead of stopping after the first failure.

## Log Analysis Script Pattern

Logs are just text. Bash is incredible at text.

Count error lines:

```bash
docker compose logs --since "1h" |
  grep -iE "error|fatal|panic" |
  wc -l
```

Show top repeated errors:

```bash
docker compose logs --since "1h" |
  grep -iE "error|fatal|panic" |
  sed 's/[0-9]\{4\}-[0-9:-]\{8,\}//g' |
  sort |
  uniq -c |
  sort -rn |
  head
```

Find RabbitMQ auth today:

```bash
today="$(date +%F)"
docker compose logs --since "${today}T00:00:00" rabbitmq |
  grep "authenticated and granted access"
```

## Report Script Pattern

Infrastructure engineers often need scripts that print reports.

Example:

```bash
#!/usr/bin/env bash
set -euo pipefail

section() {
  echo
  echo "===== $1 ====="
}

section "Disk"
df -h

section "Memory"
free -h

section "Top CPU"
ps aux --sort=-%cpu | head -n 6

section "Listening Ports"
ss -tulpn
```

This is simple, but useful.

The value is not fancy syntax. The value is repeatable evidence.

## Safe File Editing Pattern

Never casually overwrite important config.

Backup first:

```bash
backup_file() {
  local file="$1"
  local backup="${file}.bak.$(date +%Y%m%d_%H%M%S)"

  if [[ ! -f "$file" ]]; then
    echo "file not found: $file" >&2
    return 1
  fi

  cp "$file" "$backup"
  echo "$backup"
}
```

Atomic write:

```bash
atomic_write() {
  local target="$1"
  local content="$2"
  local tmp

  tmp="$(mktemp "${target}.tmp.XXXXXX")"
  trap 'rm -f "$tmp"' RETURN

  printf '%s\n' "$content" > "$tmp"
  mv "$tmp" "$target"
}
```

Atomic write means:

1. Write to temp file.
2. Move temp file into place.

This avoids half-written config files.

## Debugging Bash

Print commands as they run:

```bash
bash -x script.sh
```

Inside script:

```bash
set -x
# debug area
set +x
```

Check syntax without running:

```bash
bash -n script.sh
```

Use ShellCheck if installed:

```bash
shellcheck script.sh
```

Debug variables:

```bash
printf 'DEBUG: var=%q\n' "$var" >&2
```

`%q` prints safely escaped shell text.

## Common Bash Mistakes

### Spaces Around Assignment

Wrong:

```bash
name = "api"
```

Right:

```bash
name="api"
```

### Forgetting Quotes

Wrong:

```bash
rm $file
```

Right:

```bash
rm "$file"
```

### Parsing `ls`

Wrong:

```bash
for file in $(ls); do
  echo "$file"
done
```

Right:

```bash
for file in *; do
  [[ -e "$file" ]] || continue
  echo "$file"
done
```

### Using `exit` Inside Helper Functions Too Early

This stops the whole script:

```bash
check() {
  exit 1
}
```

Often better:

```bash
check() {
  return 1
}
```

### Assuming Grep Match Means Success

With `set -e`, this can kill your script:

```bash
count="$(grep -c ERROR app.log)"
```

If no match, grep may return non-zero.

Safer:

```bash
count="$(grep -c ERROR app.log || true)"
```

## Hands-On Master Path

You are going to build skill by making real scripts in this repo. Do these in order.

Do not just read. Type the commands. Break things safely. Rerun. Explain the output out loud.

### Lab 1: Navigation And Evidence Collection

Goal: Learn to inspect a repo like an infra engineer.

Commands:

```bash
cd /home/iscjmz/shopify/shopify
pwd
ls -la
find . -maxdepth 2 -type f | sort | head -50
find . -path './.git' -prune -o -type f -size +10M -print
git status --short
```

What you should understand:

- Where the repo root is.
- Which files changed.
- Whether large files exist.
- How to gather facts before making changes.

What it looks like:

```text
## infra_future_standard
 m Pokemon
```

That means the parent repo is on branch `infra_future_standard`, and the `Pokemon` submodule has changes inside it.

### Lab 2: Write Your First Infra Script

Create:

```bash
nano /tmp/infra_report.sh
```

Put:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "===== HOST ====="
hostname

echo
echo "===== DATE ====="
date

echo
echo "===== DISK ====="
df -h

echo
echo "===== MEMORY ====="
free -h

echo
echo "===== TOP CPU ====="
ps aux --sort=-%cpu | head -n 6
```

Run:

```bash
bash /tmp/infra_report.sh
```

Expected shape:

```text
===== HOST =====
your-hostname

===== DATE =====
Mon May  4 ...

===== DISK =====
Filesystem      Size  Used Avail Use% Mounted on
...
```

Upgrade it:

```bash
chmod +x /tmp/infra_report.sh
/tmp/infra_report.sh
```

What you learned:

- Script file.
- Shebang.
- Strict mode.
- Reports.
- System commands.

### Lab 3: Health Check Function

Create:

```bash
nano /tmp/health_lab.sh
```

Put:

```bash
#!/usr/bin/env bash
set -euo pipefail

check_endpoint() {
  local name="$1"
  local url="$2"
  local expected="$3"
  local status

  status="$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo 000)"

  if [[ "$status" == "$expected" ]]; then
    echo "OK $name HTTP $status"
  else
    echo "FAIL $name HTTP $status expected $expected" >&2
    return 1
  fi
}

failed=0
check_endpoint "Example" "https://example.com" 200 || failed=1
check_endpoint "Bad Local Port" "http://localhost:9999" 200 || failed=1

if (( failed > 0 )); then
  echo "health check failed" >&2
  exit 1
fi

echo "all checks passed"
```

Run:

```bash
bash /tmp/health_lab.sh
echo $?
```

Expected shape:

```text
OK Example HTTP 200
FAIL Bad Local Port HTTP 000 expected 200
health check failed
```

What you learned:

- Functions.
- Local variables.
- Curl status checks.
- `return 1`.
- `failed=1`.
- Script exit codes.

### Lab 4: Docker Service Checks

From the Pokemon app folder:

```bash
cd /home/iscjmz/shopify/shopify/Pokemon
docker compose ps
docker compose config --services
docker compose logs --tail=20
```

Now test Redis if containers are running:

```bash
docker exec pokemontool_redis redis-cli ping
```

Expected:

```text
PONG
```

Test Postgres:

```bash
docker exec pokemontool_postgres pg_isready -U pokemontool_user
```

Expected shape:

```text
/var/run/postgresql:5432 - accepting connections
```

What you learned:

- `docker exec`.
- Service-specific health checks.
- How Bash can wrap container checks.

### Lab 5: Rebuild A Real Health Script

Read:

```bash
sed -n '1,180p' /home/iscjmz/shopify/shopify/Pokemon/scripts/health-check.sh
```

Then write your own from scratch:

```bash
nano /tmp/pokemon_health_rebuild.sh
```

Requirements:

- Use `set -euo pipefail`.
- Create `check_endpoint`.
- Check Go API.
- Check FastAPI.
- Check Redis.
- Check Postgres.
- Exit `1` if anything fails.
- Print a final success only if all checks passed.

Starter:

```bash
#!/usr/bin/env bash
set -euo pipefail

check_endpoint() {
  local name="$1"
  local url="$2"
  local expected="$3"
  local status

  status="$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo 000)"

  if [[ "$status" == "$expected" ]]; then
    echo "OK $name HTTP $status"
  else
    echo "FAIL $name HTTP $status expected $expected" >&2
    return 1
  fi
}

main() {
  local failed=0

  check_endpoint "Go API" "http://localhost:3001/health" 200 || failed=1
  check_endpoint "FastAPI" "http://localhost:8001/health" 200 || failed=1

  if docker exec pokemontool_redis redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "OK Redis PONG"
  else
    echo "FAIL Redis" >&2
    failed=1
  fi

  if docker exec pokemontool_postgres pg_isready -U pokemontool_user >/dev/null 2>&1; then
    echo "OK Postgres ready"
  else
    echo "FAIL Postgres" >&2
    failed=1
  fi

  if (( failed > 0 )); then
    echo "one or more checks failed" >&2
    exit 1
  fi

  echo "all services healthy"
}

main "$@"
```

Expected shape:

```text
OK Go API HTTP 200
OK FastAPI HTTP 200
OK Redis PONG
OK Postgres ready
all services healthy
```

If services are down, expected shape:

```text
FAIL Go API HTTP 000 expected 200
FAIL FastAPI HTTP 000 expected 200
FAIL Redis
FAIL Postgres
one or more checks failed
```

That failure output is not bad. It is useful evidence.

### Lab 6: Log Counting

Generate a sample log:

```bash
cat > /tmp/sample.log <<'EOF'
2026-05-04T10:00:00 INFO started api
2026-05-04T10:01:00 WARN slow request
2026-05-04T10:02:00 ERROR database timeout
2026-05-04T10:03:00 ERROR database timeout
2026-05-04T10:04:00 ERROR redis unavailable
2026-05-04T10:05:00 INFO recovered
EOF
```

Run:

```bash
grep -i "error" /tmp/sample.log
grep -ic "error" /tmp/sample.log
grep -i "error" /tmp/sample.log | sort | uniq -c | sort -rn
```

Expected:

```text
2 2026-05-04T10:02:00 ERROR database timeout
1 2026-05-04T10:04:00 ERROR redis unavailable
```

Problem:

The timestamps make identical errors look different if the timestamps differ.

Normalize:

```bash
grep -i "error" /tmp/sample.log |
  sed 's/^[^ ]* //' |
  sort |
  uniq -c |
  sort -rn
```

Expected:

```text
2 ERROR database timeout
1 ERROR redis unavailable
```

What you learned:

- Logs often need normalization.
- `sed` can remove noisy timestamp fields.
- `sort | uniq -c | sort -rn` is a core incident-response move.

### Lab 7: Access Log Analysis With Awk

Create:

```bash
cat > /tmp/access.log <<'EOF'
10.0.0.1 - - [04/May/2026] "GET /health HTTP/1.1" 200 12
10.0.0.2 - - [04/May/2026] "GET /login HTTP/1.1" 401 44
10.0.0.2 - - [04/May/2026] "GET /login HTTP/1.1" 401 44
10.0.0.3 - - [04/May/2026] "GET /bad HTTP/1.1" 404 19
10.0.0.4 - - [04/May/2026] "POST /api HTTP/1.1" 500 99
EOF
```

Top IPs:

```bash
awk '{print $1}' /tmp/access.log | sort | uniq -c | sort -rn
```

Status counts:

```bash
awk '{print $9}' /tmp/access.log | sort | uniq -c | sort -rn
```

Status families:

```bash
awk '{
  if ($9 ~ /^2/) ok++
  else if ($9 ~ /^4/) client++
  else if ($9 ~ /^5/) server++
}
END {
  print "2xx:", ok+0
  print "4xx:", client+0
  print "5xx:", server+0
}' /tmp/access.log
```

Expected:

```text
2xx: 1
4xx: 3
5xx: 1
```

What you learned:

- `$1` is IP.
- `$9` is status code in default access logs.
- `awk` can count and bucket events.

### Lab 8: Build A Log Report Script

Create:

```bash
nano /tmp/log_report.sh
```

Put:

```bash
#!/usr/bin/env bash
set -euo pipefail

log_file="${1:?usage: bash log_report.sh /path/to/log}"

section() {
  echo
  echo "===== $1 ====="
}

section "Error Count"
grep -icE "error|fatal|panic" "$log_file" || true

section "Top Error Messages"
grep -iE "error|fatal|panic" "$log_file" |
  sed 's/^[^ ]* //' |
  sort |
  uniq -c |
  sort -rn |
  head -10 || true

section "Warning Count"
grep -ic "warn" "$log_file" || true
```

Run:

```bash
bash /tmp/log_report.sh /tmp/sample.log
```

Expected shape:

```text
===== Error Count =====
3

===== Top Error Messages =====
2 ERROR database timeout
1 ERROR redis unavailable

===== Warning Count =====
1
```

### Lab 9: Argument Parser

Create:

```bash
nano /tmp/args_lab.sh
```

Put:

```bash
#!/usr/bin/env bash
set -euo pipefail

since="1h"
service="all"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)
      since="${2:?--since requires a value}"
      shift 2
      ;;
    --service)
      service="${2:?--service requires a value}"
      shift 2
      ;;
    --help)
      echo "usage: $0 [--since 1h] [--service api]"
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

echo "since=$since"
echo "service=$service"
```

Run:

```bash
bash /tmp/args_lab.sh
bash /tmp/args_lab.sh --since 24h --service postgres
bash /tmp/args_lab.sh --bad
```

Expected:

```text
since=24h
service=postgres
```

For bad argument:

```text
unknown argument: --bad
```

What you learned:

- `while [[ $# -gt 0 ]]`
- `case`
- `shift 2`
- usage errors

### Lab 10: Service Inventory Script

Goal:

Print every Docker Compose service and whether its container appears to be running.

Create:

```bash
nano /tmp/service_inventory.sh
```

Put:

```bash
#!/usr/bin/env bash
set -euo pipefail

compose_file="${1:-docker-compose.yml}"

if [[ ! -f "$compose_file" ]]; then
  echo "compose file not found: $compose_file" >&2
  exit 1
fi

echo "SERVICE INVENTORY"
echo "compose_file=$compose_file"
echo

while IFS= read -r service; do
  if docker compose -f "$compose_file" ps "$service" 2>/dev/null | grep -q "$service"; then
    echo "SEEN $service"
  else
    echo "UNKNOWN $service"
  fi
done < <(docker compose -f "$compose_file" config --services)
```

Run:

```bash
cd /home/iscjmz/shopify/shopify/Pokemon
bash /tmp/service_inventory.sh docker-compose.yml
```

Expected shape:

```text
SERVICE INVENTORY
compose_file=docker-compose.yml

SEEN postgres
SEEN redis
SEEN rabbitmq
...
```

What you learned:

- Process substitution: `< <(command)`
- Reading command output line by line.
- Docker Compose service discovery.

### Lab 11: Large File Guard

This connects directly to the Git hook work.

Run:

```bash
cd /home/iscjmz/shopify/shopify
find . -path './.git' -prune -o -type f -size +50M -print
```

Run the script:

```bash
scripts/check-large-files.sh --staged
```

Expected:

```text
# no output means no staged oversized files
```

Create a fake 51 MB file in `/tmp`, not the repo:

```bash
dd if=/dev/zero of=/tmp/big-test.bin bs=1M count=51
ls -lh /tmp/big-test.bin
```

Do not add it to Git. Just understand the size.

What you learned:

- Infrastructure scripts often prevent humans from making expensive mistakes.
- A good guardrail is quiet when things are good and loud when things are bad.

### Lab 12: Build Your Own `doctor.sh`

This is the graduation project.

Create this in the repo:

```bash
mkdir -p /home/iscjmz/shopify/shopify/scripts
nano /home/iscjmz/shopify/shopify/scripts/doctor.sh
```

Requirements:

- Strict mode.
- Stable project root detection.
- Check required commands: `git`, `docker`, `curl`.
- Print branch and git status.
- Check files over 50 MB.
- Check Docker availability.
- If in `Pokemon`, list compose services.
- Print disk, memory, top CPU.
- Exit non-zero if critical checks fail.

Starter:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

failed=0

section() {
  echo
  echo "===== $1 ====="
}

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "MISSING command: $cmd" >&2
    failed=1
  else
    echo "OK command: $cmd"
  fi
}

section "Required Commands"
require_command git
require_command docker
require_command curl

section "Git"
cd "$PROJECT_ROOT"
git branch --show-current || failed=1
git status --short || failed=1

section "Large Files Over 50 MB"
large_files="$(find . -path './.git' -prune -o -type f -size +50M -print)"
if [[ -n "$large_files" ]]; then
  echo "$large_files"
  failed=1
else
  echo "OK no large files found"
fi

section "Docker"
if docker info >/dev/null 2>&1; then
  echo "OK docker daemon reachable"
else
  echo "FAIL docker daemon not reachable" >&2
  failed=1
fi

section "System"
df -h
free -h
ps aux --sort=-%cpu | head -n 6

if (( failed > 0 )); then
  echo
  echo "doctor found problems" >&2
  exit 1
fi

echo
echo "doctor passed"
```

Run:

```bash
chmod +x scripts/doctor.sh
scripts/doctor.sh
```

Expected shape:

```text
===== Required Commands =====
OK command: git
OK command: docker
OK command: curl

===== Git =====
infra_future_standard
 m Pokemon

===== Large Files Over 50 MB =====
OK no large files found

===== Docker =====
OK docker daemon reachable

doctor passed
```

## What Mastery Looks Like

You are getting good when you can do these without freezing:

- Read a Bash script and explain every line.
- Write a health check with functions.
- Use `curl` to check endpoints.
- Use `docker exec` to check service internals.
- Use `grep`, `awk`, `sed`, `sort`, `uniq`, and `head` to analyze logs.
- Use `find` to locate large files, old files, config files, and generated junk.
- Use `ss`, `lsof`, `ps`, and `pgrep` to inspect ports and processes.
- Use `journalctl` and `docker logs` during incidents.
- Use `set -euo pipefail` without being confused by it.
- Quote variables correctly.
- Handle script arguments with `case` and `shift`.
- Use exit codes intentionally.
- Create reports that help other people make decisions.
- Write scripts that are boring, clear, repeatable, and safe.

## Your Daily Bash Training Plan

Do this every day for two weeks.

Day 1:

- Run Lab 1.
- Explain every command in your own words.
- Read `Pokemon/scripts/health-check.sh`.

Day 2:

- Build Lab 2 and Lab 3.
- Modify the health check to test a different URL.

Day 3:

- Do Lab 6 and Lab 7.
- Make your own fake logs with 20 lines.

Day 4:

- Build Lab 8.
- Add a `--top 5` argument.

Day 5:

- Do Lab 9.
- Add `--json` that prints a simple JSON-ish output.

Day 6:

- Do Lab 10.
- Run it inside the Pokemon app.

Day 7:

- Build `scripts/doctor.sh`.
- Commit it only after you understand every line.

Week 2:

- Take one repeated manual thing you do in this repo and automate it.
- Examples:
  - Start Pokemon services.
  - Check ports.
  - Print Docker health.
  - Scan logs.
  - Check for large files.
  - Create a deploy preflight report.

## Final Intuition

Bash mastery is not memorizing every flag.

Bash mastery is knowing how to think:

1. What fact do I need?
2. Which command exposes that fact?
3. Is the output text, JSON, status code, file metadata, or an exit code?
4. How do I filter it?
5. How do I turn it into a decision?
6. How do I make the script fail safely?
7. How do I make the output useful to another engineer?

That is infrastructure scripting.

When you can turn manual troubleshooting into repeatable scripts, you stop being someone who "knows commands" and start becoming someone who can operate systems.
