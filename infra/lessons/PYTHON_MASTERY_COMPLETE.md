# 🐍 PYTHON MASTERY — COMPLETE REFERENCE
## From Zero to Infrastructure Automation Expert
### Every concept tied to the NexusOS/Pokevend stack

---

> **HOW TO USE THIS DOCUMENT**
> Every section has runnable examples. Open `python3` in a terminal.
> The REPL is your laboratory. Test everything. Break things. Read errors carefully.
> Errors in Python are GOOD — they tell you exactly what's wrong.

---

## WHY PYTHON FOR INFRASTRUCTURE?

Python is the language of infrastructure because:
1. **AWS CLI, Boto3, Ansible** — all Python
2. **Readable** — you can read it 6 months later and understand it
3. **Batteries included** — handles JSON, YAML, HTTP, OS, processes out of the box
4. **Error handling is explicit** — try/except forces you to think about failure
5. **Cross-platform** — the same script runs on Linux, Mac, Windows

Infrastructure Python is NOT like web development Python.
You will use: `subprocess`, `os`, `pathlib`, `json`, `argparse`, `logging`.
You will rarely use: `numpy`, `pandas`, `Flask`.

---

## CHAPTER 1: The Python Mental Model

### Everything is an Object

```python
# In Python, EVERYTHING is an object with attributes and methods
"hello".upper()         # "HELLO" — strings are objects
[1,2,3].append(4)       # Lists are objects
(42).__class__          # <class 'int'> — even numbers are objects

# This matters because:
path = "/var/log/nexusos/app.log"
parts = path.split("/")          # ['', 'var', 'log', 'nexusos', 'app.log']
filename = path.split("/")[-1]   # 'app.log'
ext = filename.split(".")[-1]    # 'log'
```

### The Indentation Contract

Indentation IS the code structure. Not style — structure.
```python
# This is ONE function with ONE if statement:
def check_service(name):          # Function starts here
    if name == "pokevend":        # if block
        return True               # Inside if
    return False                  # Back to function level (not in if)

# This CRASHES (IndentationError):
def broken():
    x = 1
  y = 2  # Wrong indentation — Python will reject this
```

### Truthiness — What's "True" in Python

```python
# Falsy values (evaluate to False in boolean context):
False, None, 0, 0.0, "", [], {}, set()

# Everything else is truthy

# This is useful for checking if something exists:
containers = get_running_containers()  # returns a list
if containers:                          # True if list is non-empty
    print(f"Found {len(containers)} containers")

# For infrastructure, you often do:
db_password = os.getenv("DB_PASSWORD")  # Returns None if not set
if not db_password:
    raise ValueError("DB_PASSWORD environment variable must be set")
```

---

## CHAPTER 2: Data Types — The Building Blocks

### Strings — Text Manipulation for Log Parsing

```python
# String creation
single = 'hello'
double = "world"
multi  = """Multi
line
string"""

# f-strings — THE modern way to format strings (Python 3.6+)
service = "pokevend"
port    = 8080
url     = f"http://localhost:{port}/health"     # "http://localhost:8080/health"
msg     = f"Service {service!r} on port {port}" # Service 'pokevend' on port 8080
# !r uses repr() — adds quotes around strings, good for logging

# String methods for infrastructure
log_line = "  2026-04-01T14:23:01 [ERROR] Database connection failed  "
log_line.strip()            # Remove whitespace from both ends
log_line.lstrip()           # Remove ONLY leading whitespace
log_line.rstrip()           # Remove ONLY trailing whitespace
log_line.lower()            # Lowercase (for case-insensitive comparison)
log_line.upper()            # Uppercase
log_line.startswith("[")    # False
log_line.endswith("  ")     # True
log_line.contains("ERROR")  # AttributeError! Use "ERROR" in log_line

# The `in` operator for substring check
if "ERROR" in log_line:
    print("Error found!")

# Splitting and joining — critical for log parsing
line = "192.168.1.1 - - [01/Apr/2026] GET /api/v1/cards 200 1234"
fields = line.split()          # Split on whitespace → list of fields
ip     = fields[0]             # "192.168.1.1"
status = fields[-2]            # "200" (second to last)
url    = fields[5]             # "/api/v1/cards"

# Join a list back into a string
csv_line = ",".join(["192.168.1.1", "200", "/api/v1/cards"])

# Splitting on a specific character
key, value = "DB_HOST=localhost".split("=", 1)  # maxsplit=1 prevents splitting value
# key   = "DB_HOST"
# value = "localhost"

# String formatting for reports
print(f"{'Service':<20} {'Port':>6} {'Status':^10}")  # Aligned columns
print(f"{'pokevend':<20} {8080:>6} {'active':^10}")
# Output:
# Service                Port   Status
# pokevend              8080    active

# Multiline strings for generating configs
nginx_config = f"""
server {{
    listen 443 ssl;
    server_name {domain};
    
    location /api/ {{
        proxy_pass http://localhost:{port};
    }}
}}
"""
```

### Lists — Ordered Collections

```python
# Creation
services = ["pokevend", "nginx", "postgres", "redis"]
ports    = [8080, 80, 5432, 6379]
empty    = []

# Access
services[0]      # "pokevend"
services[-1]     # "redis" (last element)
services[1:3]    # ["nginx", "postgres"] (slice: indices 1 and 2)
services[:2]     # ["pokevend", "nginx"] (first 2)
services[2:]     # ["postgres", "redis"] (from index 2 to end)

# Modification
services.append("kafka")           # Add to end
services.insert(0, "temporal")     # Insert at index 0
services.extend(["ollama", "qdrant"])  # Add multiple
services.remove("nginx")           # Remove by value (first occurrence)
popped = services.pop()            # Remove and return last element
popped = services.pop(0)           # Remove and return index 0

# List comprehensions — the most important Python pattern for data transformation
# [expression for item in iterable if condition]

# Get all ports above 1024
user_ports = [p for p in ports if p > 1024]   # [8080, 5432, 6379]

# Map a function over a list
upper_services = [s.upper() for s in services]  # ["POKEVEND", "NGINX", ...]

# Extract IPs from log lines
log_lines = ["192.168.1.1 - GET /cards 200", "10.0.0.1 - POST /auth 401"]
ips = [line.split()[0] for line in log_lines]   # ["192.168.1.1", "10.0.0.1"]

# Flatten a list of lists
nested = [[1, 2], [3, 4], [5, 6]]
flat = [x for sublist in nested for x in sublist]  # [1, 2, 3, 4, 5, 6]

# Sorting
services.sort()                      # Sort in place
sorted_services = sorted(services)   # Return new sorted list
# Sort by custom key:
containers = [{"name": "redis", "mem": 150}, {"name": "postgres", "mem": 512}]
containers.sort(key=lambda c: c["mem"], reverse=True)  # By memory, descending
```

### Dictionaries — The Data Structure of Infrastructure

Dicts are EVERYWHERE in infrastructure Python: JSON responses, config files, metrics.

```python
# Creation
service_info = {
    "name": "pokevend",
    "port": 8080,
    "status": "healthy",
    "containers": ["nexusos-postgres", "nexusos-redis"]
}

# Access
service_info["name"]                    # "pokevend"
service_info.get("port")                # 8080
service_info.get("missing_key", 0)      # 0 (default — never KeyError)
service_info.get("missing_key")         # None (no error if missing)

# Modification
service_info["status"] = "degraded"     # Update existing
service_info["replicas"] = 3            # Add new key
del service_info["replicas"]            # Delete key

# Checking existence
"name" in service_info          # True
"missing" in service_info       # False
"missing" not in service_info   # True

# Iteration
for key, value in service_info.items():    # Both key and value
    print(f"  {key}: {value}")

for key in service_info:                   # Just keys
    print(key)

for value in service_info.values():        # Just values
    print(value)

# Dict comprehensions
# Build port→service map from a list
services_list = [
    {"name": "pokevend", "port": 8080},
    {"name": "postgres", "port": 5432},
]
port_map = {svc["port"]: svc["name"] for svc in services_list}
# {8080: "pokevend", 5432: "postgres"}

# Merge dicts (Python 3.9+)
defaults = {"log_level": "info", "timeout": 30}
overrides = {"log_level": "debug", "port": 8080}
merged = defaults | overrides
# {"log_level": "debug", "timeout": 30, "port": 8080}

# Nested dict access (safe pattern)
response = {"data": {"service": {"status": "healthy"}}}
status = response.get("data", {}).get("service", {}).get("status", "unknown")
# "healthy" — no KeyError even if any level is missing
```

---

## CHAPTER 3: Functions — Code Organization

```python
# ─── Basic function ────────────────────────────────────────────────────
def check_service_health(url: str, timeout: int = 5) -> dict:
    """
    Check the health of a service endpoint.
    
    Args:
        url: The health check URL
        timeout: Request timeout in seconds (default: 5)
    
    Returns:
        dict with keys: "status", "latency_ms", "details"
    """
    # Implementation here
    pass

# Type hints are NOT enforced, but they document intent and enable IDE help
# str → this parameter should be a string
# int → should be an integer
# dict → returns a dictionary
# Optional[str] → can be str or None
# list[dict] → list of dicts
# → None means function returns nothing

# ─── *args and **kwargs — Variable Arguments ───────────────────────────
def log_event(level: str, *messages: str, **context) -> None:
    """
    log_event("ERROR", "Connection failed", "Retrying...", service="pokevend", port=5432)
    """
    import datetime
    timestamp = datetime.datetime.now().isoformat()
    all_messages = " ".join(messages)
    context_str  = " ".join(f"{k}={v}" for k, v in context.items())
    print(f"[{timestamp}] [{level}] {all_messages} {context_str}")

log_event("ERROR", "DB connection lost", service="pokevend", attempt=3)
# [2026-04-01T14:23:01] [ERROR] DB connection lost service=pokevend attempt=3

# ─── Returning Multiple Values (actually returns a tuple) ──────────────
def get_service_status(name: str) -> tuple[bool, str, float]:
    """Returns (is_healthy, status_text, latency_ms)"""
    # ... implementation ...
    return True, "healthy", 12.5

is_healthy, status, latency = get_service_status("pokevend")
# Tuple unpacking — cleaner than returning a dict for simple cases

# ─── Lambda — Inline Functions ────────────────────────────────────────
# lambdas are single-expression functions, good for use with sort/filter/map

containers = [
    {"name": "redis", "cpu": 2.1, "mem": 150},
    {"name": "postgres", "cpu": 15.3, "mem": 512},
    {"name": "kafka", "cpu": 8.7, "mem": 350},
]

# Sort by CPU usage descending
containers.sort(key=lambda c: c["cpu"], reverse=True)

# Filter to high-memory containers
high_mem = list(filter(lambda c: c["mem"] > 300, containers))

# Map: extract just names
names = list(map(lambda c: c["name"], containers))
# Better as a list comprehension: names = [c["name"] for c in containers]
```

---

## CHAPTER 4: Error Handling — The Most Critical Chapter

In infrastructure automation, YOU MUST handle errors explicitly.
A script that crashes halfway through a deployment is worse than one that doesn't run at all.

```python
# ─── The try/except Pattern ────────────────────────────────────────────
import subprocess

def run_command(cmd: list[str], fail_message: str = "") -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True          # Raises CalledProcessError if exit code != 0
        )
        return result
    except subprocess.CalledProcessError as e:
        # e.returncode = exit code
        # e.stdout     = what the program printed to stdout
        # e.stderr     = what it printed to stderr
        message = fail_message or f"Command failed: {' '.join(cmd)}"
        raise RuntimeError(f"{message}\nStderr: {e.stderr}") from e
    except FileNotFoundError:
        # The program itself doesn't exist
        raise RuntimeError(f"Command not found: {cmd[0]}")

# ─── Multiple Exception Types ──────────────────────────────────────────
import urllib.request
import urllib.error
import json

def check_api_health(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        # Server responded with a 4xx or 5xx status
        return {"status": "error", "code": e.code, "reason": e.reason}
    except urllib.error.URLError as e:
        # Connection refused, DNS failure, timeout
        return {"status": "unreachable", "reason": str(e.reason)}
    except json.JSONDecodeError as e:
        # Server responded but with invalid JSON
        return {"status": "invalid_response", "error": str(e)}
    except Exception as e:
        # Catch-all for unexpected errors — log but don't suppress
        print(f"[WARN] Unexpected error checking {url}: {type(e).__name__}: {e}")
        return {"status": "unknown", "error": str(e)}

# ─── Context Managers — Automatic Resource Cleanup ─────────────────────
# The `with` statement ensures cleanup happens even if an exception occurs

# File handling with automatic close:
with open("/var/log/nexusos/app.log", "r", errors="ignore") as f:
    for line in f:
        process_log_line(line)
# File is GUARANTEED to be closed here, even if an exception was raised inside

# Writing with atomic rename (the safe way):
import os
import tempfile
from pathlib import Path

def write_config_atomically(path: Path, content: str) -> None:
    """Write content to path atomically — no partial writes on crash."""
    # Write to temp file first
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, 'w') as f:
            f.write(content)
        # Atomic rename — either it works fully or nothing changes
        os.replace(tmp_path, path)
    except Exception:
        # Clean up temp file if anything went wrong
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

# ─── Custom Exceptions — Clear Error Communication ─────────────────────
class DeploymentError(Exception):
    """Raised when a deployment stage fails. Non-recoverable."""
    def __init__(self, stage: str, message: str, details: dict = None):
        self.stage   = stage
        self.details = details or {}
        super().__init__(f"Stage '{stage}' failed: {message}")

class HealthCheckError(Exception):
    """Raised when a service fails its health check."""
    pass

class ConfigurationError(ValueError):
    """Raised when configuration is invalid or missing."""
    pass

# Usage:
try:
    result = subprocess.run(["go", "build", "./..."], check=True, capture_output=True)
except subprocess.CalledProcessError as e:
    raise DeploymentError("build", "Go compilation failed", {
        "stderr": e.stderr.decode(),
        "command": e.cmd,
    }) from e
```

---

## CHAPTER 5: The subprocess Module — Making Python Talk to Linux

This is THE most important module for infrastructure Python.

```python
import subprocess
import shlex

# ─── RULE 1: NEVER use os.system() or shell=True with user input ──────
# These are dangerous because of shell injection:
# os.system(f"rm {user_input}")  ← if user_input = "/ -rf # ": game over

# ─── subprocess.run() — The Modern Standard ───────────────────────────
# Always pass commands as a LIST, never as a string
result = subprocess.run(
    ["docker", "ps", "--format", "{{.Names}}"],
    capture_output=True,    # Capture stdout AND stderr
    text=True,              # Decode bytes → str automatically (UTF-8)
    check=False,            # Don't raise on non-zero exit (handle manually)
    timeout=30,             # Kill if it takes more than 30 seconds
)

# The CompletedProcess result object
result.returncode          # 0 = success, anything else = failure
result.stdout              # What the command printed to stdout (str)
result.stderr              # What it printed to stderr (str)

# Check manually
if result.returncode != 0:
    print(f"Error: {result.stderr.strip()}")
else:
    containers = result.stdout.strip().split('\n')  # List of container names

# ─── check=True — Auto-raise on failure ────────────────────────────────
# Use this when you want to crash if the command fails (most of the time)
try:
    result = subprocess.run(
        ["systemctl", "restart", "pokevend"],
        capture_output=True,
        text=True,
        check=True          # Raises subprocess.CalledProcessError if exit != 0
    )
    print("Service restarted successfully")
except subprocess.CalledProcessError as e:
    print(f"Failed to restart: {e.stderr}")

# ─── Streaming output — Show progress in real-time ────────────────────
# When you DON'T use capture_output, output goes directly to terminal
# Great for long-running commands where you want live progress

print("Running tests...")
result = subprocess.run(
    ["go", "test", "-v", "./..."],
    cwd="/home/iscjmz/shopify/shopify/Pokemon/server",  # Working directory
    check=False
)
# Test output printed live to terminal as tests run

# ─── Environment Variables ────────────────────────────────────────────
import os

# Run command with ADDITIONAL env vars (don't replace the whole environment)
env = os.environ.copy()          # Copy current environment
env["GOFLAGS"] = "-mod=vendor"   # Add or override one variable
env["CGO_ENABLED"] = "0"         # Disable CGO for static linking

result = subprocess.run(
    ["go", "build", "-o", "/opt/pokevend/pokevend", "./..."],
    env=env,
    cwd="/home/iscjmz/shopify/shopify/Pokemon/server",
    capture_output=True, text=True, check=True
)

# ─── Piping between commands in Python ────────────────────────────────
# Instead of: ps aux | grep pokevend | awk '{print $2}'
# Do it properly in Python (safer, more readable, no shell=True needed):

ps_result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
pokevend_lines = [
    line for line in ps_result.stdout.split('\n')
    if "pokevend" in line and "grep" not in line
]
pids = [line.split()[1] for line in pokevend_lines]
print("Pokevend PIDs:", pids)

# ─── When you DO need a shell pipeline ────────────────────────────────
# Use shell=True ONLY when you need shell features (pipes, redirection)
# and ONLY with static strings (never with user input)

result = subprocess.run(
    "journalctl -u pokevend --no-pager | grep ERROR | wc -l",
    shell=True,
    capture_output=True,
    text=True
)
error_count = int(result.stdout.strip())
```

---

## CHAPTER 6: Files, Paths, and the OS

### pathlib — The Modern Way

```python
from pathlib import Path

# ─── Path Creation ────────────────────────────────────────────────────
log_dir    = Path("/var/log/nexusos")
config     = Path("/etc/nexusos/config.env")
binary     = Path("/opt/pokevend/pokevend")
home       = Path.home()                  # /home/iscjmz
here       = Path(__file__).parent       # directory containing this script

# ─── Path Components ──────────────────────────────────────────────────
config.name          # "config.env"
config.stem          # "config" (name without extension)
config.suffix        # ".env"
config.suffixes      # [".env"]
config.parent        # Path("/etc/nexusos")
config.parents[0]    # Path("/etc/nexusos")
config.parents[1]    # Path("/etc")
config.parts         # ('/', 'etc', 'nexusos', 'config.env')

# ─── Path Joining ─────────────────────────────────────────────────────
log_file = log_dir / "app.log"             # /var/log/nexusos/app.log
backup   = config.parent / "backups" / "config.bak"
# This is better than os.path.join() — reads left to right, elegant

# ─── Existence Checks ─────────────────────────────────────────────────
config.exists()      # Does it exist at all?
config.is_file()     # Is it a file?
log_dir.is_dir()     # Is it a directory?
binary.is_symlink()  # Is it a symlink?

# ─── Directory Operations ─────────────────────────────────────────────
log_dir.mkdir(parents=True, exist_ok=True)  # Create /var/log/nexusos
# parents=True  → create any missing parent directories  
# exist_ok=True → don't fail if it already exists (idempotent!)

# ─── File Operations ──────────────────────────────────────────────────
# Read entire file
content = config.read_text(encoding="utf-8", errors="ignore")

# Read lines as a list
lines = config.read_text().splitlines()

# Write
config.write_text("DB_HOST=localhost\nDB_PORT=5432\n")

# ─── Listing Directory Contents ───────────────────────────────────────
# All files in a directory
for f in log_dir.iterdir():
    print(f.name, f.stat().st_size)

# Only .log files
for log_file in log_dir.glob("*.log"):
    print(log_file)

# Recursive search — all .go files in the entire project
go_files = list(Path("Pokemon/server").rglob("*.go"))

# ─── File Metadata ────────────────────────────────────────────────────
stat = config.stat()
stat.st_size     # File size in bytes
stat.st_mtime    # Last modified timestamp (Unix time)
stat.st_mode     # Permission mode (numeric)

import datetime
modified = datetime.datetime.fromtimestamp(stat.st_mtime)
print(f"Config last modified: {modified.isoformat()}")

# ─── Permissions (os module for chmod/chown) ──────────────────────────
import os
import stat

os.chmod(str(binary), 0o755)       # rwxr-xr-x (note: octal literal with 0o prefix)
os.chmod(str(config), 0o640)       # rw-r----- 

# Check if a file has the right permissions
current_mode = config.stat().st_mode
is_world_readable = bool(current_mode & stat.S_IROTH)   # Others read bit
if is_world_readable:
    print(f"SECURITY: {config} is world-readable! Fixing...")
    os.chmod(str(config), 0o640)
```

---

## CHAPTER 7: JSON and Data Formats

```python
import json

# ─── Reading JSON ──────────────────────────────────────────────────────
# From a string
json_str = '{"status": "ok", "services": {"db": "up", "redis": "up"}}'
data = json.loads(json_str)                # string → dict/list
status = data["status"]                    # "ok"
db_status = data["services"]["db"]         # "up"

# From a file
with open("/var/log/nexusos/status.json") as f:
    status_data = json.load(f)             # file → dict/list (no .loads())

# From an HTTP response
import urllib.request
with urllib.request.urlopen("http://localhost:8080/health") as response:
    health = json.load(response)           # Parse response directly

# ─── Writing JSON ──────────────────────────────────────────────────────
report = {
    "timestamp": "2026-04-01T14:23:01",
    "services": {
        "pokevend": {"status": "healthy", "uptime_hours": 72},
        "postgres": {"status": "healthy", "connections": 15},
    },
    "disk_usage_pct": 43.2
}

# To string
json_str = json.dumps(report)              # Compact (one line)
json_str = json.dumps(report, indent=2)    # Pretty with 2-space indent
json_str = json.dumps(report, indent=2, sort_keys=True)  # Also sort keys

# To file
with open("/var/log/nexusos/report.json", "w") as f:
    json.dump(report, f, indent=2)

# ─── JSONL — JSON Lines (One JSON Object Per Line) ─────────────────────
# Used for deployment logs, event streams, structured logging
# MUCH better than a single huge JSON array for large files

# Writing JSONL
with open("/var/log/nexusos/deployments.jsonl", "a") as f:
    event = {"time": "2026-04-01T14:00:00", "version": "v1.2.3", "success": True}
    f.write(json.dumps(event) + "\n")   # One JSON object per line

# Reading JSONL (read line by line — memory efficient for huge files)
with open("/var/log/nexusos/deployments.jsonl") as f:
    deployments = [json.loads(line) for line in f if line.strip()]
    
# ─── Real-world: Parse Pokevend structured logs ────────────────────────
# Your Go app emits JSON logs like:
# {"time":"2026-04-01T14:23:01","level":"error","msg":"DB connection failed","service":"pokevend"}

def parse_structured_logs(log_file: str) -> list[dict]:
    """Parse JSON-structured log lines from the Go API."""
    logs = []
    with open(log_file, errors="ignore") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                log_entry = json.loads(line)
                logs.append(log_entry)
            except json.JSONDecodeError:
                # Not every line is JSON (startup messages, etc.)
                pass
    return logs

# Analyze: count errors by level
all_logs = parse_structured_logs("/var/log/nexusos/app.log")
by_level = {}
for entry in all_logs:
    level = entry.get("level", "unknown")
    by_level[level] = by_level.get(level, 0) + 1

print("Log breakdown:", by_level)
# {'info': 14532, 'error': 12, 'warn': 47}
```

---

## CHAPTER 8: Classes — Object-Oriented Infrastructure Tools

```python
# ─── When to Use Classes ───────────────────────────────────────────────
# Create a class when:
# 1. You have state (data) that functions need to share
# 2. You have multiple related operations on the same concept
# 3. You want a clean API for complex behavior

# A class that represents the NexusOS stack
class NexusOSStack:
    """Manages the NexusOS infrastructure stack."""
    
    COMPOSE_FILE = "/home/iscjmz/shopify/shopify/docker-compose.yml"
    
    # Expected services and their health check URLs
    SERVICES = {
        "nexusos-postgres": {"port": 5432, "type": "postgres"},
        "nexusos-redis":    {"port": 6379, "type": "redis"},
        "nexusos-kafka":    {"port": 9092, "type": "kafka"},
        "nexusos-qdrant":   {"port": 6333, "type": "http", "path": "/readyz"},
        "nexusos-temporal": {"port": 7233, "type": "grpc"},
        "nexusos-ollama":   {"port": 11434, "type": "http", "path": "/api/tags"},
    }
    
    def __init__(self):
        """Initialize: discover current stack state."""
        self._running_containers: dict[str, str] = {}
        self._refresh_state()
    
    def _refresh_state(self) -> None:
        """Update internal state from docker ps."""
        import subprocess
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True
        )
        self._running_containers = {}
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('\t', 1)
            if len(parts) == 2:
                name, status = parts
                self._running_containers[name] = status
    
    def is_running(self, service_name: str) -> bool:
        """Check if a service container is running."""
        return service_name in self._running_containers
    
    def start_all(self) -> bool:
        """Start the entire stack with docker-compose."""
        import subprocess
        try:
            subprocess.run(
                ["docker-compose", "-f", self.COMPOSE_FILE, "up", "-d"],
                check=True
            )
            self._refresh_state()
            return True
        except subprocess.CalledProcessError as e:
            return False
    
    def health_report(self) -> dict:
        """Generate a health report for all services."""
        self._refresh_state()
        report = {"timestamp": __import__("datetime").datetime.now().isoformat(), "services": {}}
        
        for service, config in self.SERVICES.items():
            is_up = self.is_running(service)
            report["services"][service] = {
                "running": is_up,
                "port": config["port"],
                "status": self._running_containers.get(service, "stopped")
            }
        return report
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        running = sum(1 for s in self.SERVICES if self.is_running(s))
        total   = len(self.SERVICES)
        return f"NexusOSStack({running}/{total} running)"


# ─── Usage ────────────────────────────────────────────────────────────
stack = NexusOSStack()
print(stack)                          # NexusOSStack(5/6 running)

report = stack.health_report()
print(json.dumps(report, indent=2))

if not stack.is_running("nexusos-postgres"):
    print("WARNING: Database is not running!")
    stack.start_all()
```

---

## CHAPTER 9: The logging Module — Production-Quality Output

```python
import logging
import sys
from pathlib import Path

def setup_logging(log_file: Path = None, level: str = "INFO") -> logging.Logger:
    """
    Configure logging for an infrastructure script.
    
    Sets up structured output going to BOTH console and optionally a file.
    """
    # The numeric level (INFO=20, DEBUG=10, WARNING=30, ERROR=40, CRITICAL=50)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter — defines how log lines look
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)   # Capture everything; handlers filter individually
    
    # Console handler — shows INFO and above
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(numeric_level)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # File handler — if log_file specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_file))
        file_handler.setLevel(logging.DEBUG)   # File captures everything
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Return module-specific logger
    return logging.getLogger(__name__)

# Usage in your scripts:
logger = setup_logging(
    log_file=Path("/var/log/nexusos/deploy.log"),
    level="INFO"
)

logger.debug("Debug detail (only in file)")
logger.info("Starting deployment of v1.2.3")
logger.warning("Skip backup was set — proceed with caution")
logger.error("Health check failed after restart")
logger.critical("ROLLBACK INITIATED: service failed to start")

# Log with extra context (structured)
logger.info("Deployed service %s to %s in %.1fs", "pokevend", "staging", 12.3)
# [2026-04-01T14:23:01] [INFO    ] Deployed service pokevend to staging in 12.3s
```

---

## CHAPTER 10: argparse — CLI Superpowers

```python
import argparse
import sys

def build_parser() -> argparse.ArgumentParser:
    """Build a comprehensive CLI parser for a deployment tool."""
    
    parser = argparse.ArgumentParser(
        prog="nexusos-deploy",
        description="NexusOS Deployment & Infrastructure Management Tool",
        epilog="""
Examples:
  %(prog)s deploy --env staging --version v1.2.3
  %(prog)s status
  %(prog)s rollback --version v1.1.0
  %(prog)s audit --output report.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Subcommands (like git commit, git push, git status)
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True
    
    # ── deploy subcommand ──────────────────────────────────────────────
    deploy = subparsers.add_parser("deploy", help="Deploy a new version")
    deploy.add_argument(
        "--env", "-e",
        required=True,
        choices=["dev", "staging", "prod"],
        help="Target environment"
    )
    deploy.add_argument(
        "--version", "-v",
        required=True,
        metavar="VERSION",
        help="Version to deploy (e.g. v1.2.3 or git sha)"
    )
    deploy.add_argument(
        "--force",
        action="store_true",               # Flag: present=True, absent=False
        help="Skip confirmation prompts (required for CI/CD)"
    )
    deploy.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip test suite (DANGEROUS — only for emergency deploys)"
    )
    deploy.add_argument(
        "--timeout",
        type=int,                          # Convert string arg to int
        default=300,
        metavar="SECONDS",
        help="Deployment timeout in seconds (default: 300)"
    )
    
    # ── status subcommand ──────────────────────────────────────────────
    status = subparsers.add_parser("status", help="Show stack status")
    status.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    # ── audit subcommand ───────────────────────────────────────────────
    audit = subparsers.add_parser("audit", help="Run security/health audit")
    audit.add_argument("--output", metavar="FILE", help="Write report to file")
    audit.add_argument("--severity-min", type=int, default=1, choices=range(1, 11),
                       metavar="1-10", help="Minimum severity level to report")
    
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    
    # Route to the right handler
    if args.command == "deploy":
        if args.env == "prod" and not args.force:
            confirm = input(f"Deploy {args.version} to PRODUCTION? [type 'yes']: ")
            if confirm.strip().lower() != "yes":
                print("Aborted.")
                sys.exit(1)
        run_deploy(args.env, args.version, args.timeout)
    
    elif args.command == "status":
        show_status(output_format=args.format)
    
    elif args.command == "audit":
        run_audit(output_file=args.output, severity_min=args.severity_min)

if __name__ == "__main__":
    main()
```

---

## ⚡ PYTHON CHEAT SHEET — MEMORIZE THIS

```python
# ── String Operations ──────────────────
f"text {variable}"          # f-string formatting
"text".split(",")           # ['text'] (split into list)
",".join(["a","b"])         # "a,b" (list to string)
"text".strip()              # Remove whitespace
"TEXT".lower()              # "text"
"text" in other_str         # Substring check
f"{val:<20}"                # Left-align in 20 chars
f"{val:>10.2f}"             # Right-align, 2 decimal places

# ── List Operations ──────────────────
[x for x in lst if cond]    # List comprehension with filter
sorted(lst, key=lambda x: x["field"])  # Sort by key
any(condition for x in lst) # True if ANY match
all(condition for x in lst) # True if ALL match
lst[0], lst[-1], lst[1:3]   # First, last, slice

# ── Dict Operations ────────────────────
d.get("key", default)       # Safe access with default
d.items()                   # Key-value pairs
{k: v for k,v in d.items() if condition}  # Dict comprehension

# ── File I/O ────────────────────────────
Path("/path/to").mkdir(parents=True, exist_ok=True)
Path("/path").read_text()   # Read entire file
Path("/path").write_text(s) # Write entire file
for line in open("/path"):  # Line by line

# ── subprocess ─────────────────────────
subprocess.run(["cmd", "arg"], capture_output=True, text=True, check=True)
result.stdout / result.stderr / result.returncode

# ── Error Handling ──────────────────────
try:
    risky_operation()
except SpecificError as e:
    handle(e)
finally:
    cleanup()  # ALWAYS runs

# ── Environment / OS ────────────────────
os.getenv("VAR", "default")  # Read env var
os.environ["VAR"]            # Read (raises KeyError if missing)
os.path.exists("/path")      # File/dir exists
```

---

## 🔥 PROJECT CHALLENGES — Build These, Become a Master

### CHALLENGE 1: NexusOS Log Aggregator (Beginner)
Write a Python script that:
- Reads logs from `journalctl -u pokevend` AND `docker logs nexusos-postgres`
- Parses each JSON log line
- Groups errors by type
- Prints: "Top 5 errors in the last hour"

### CHALLENGE 2: Service Health Dashboard (Intermediate)
Write a Python class `HealthDashboard` that:
- Checks every service in NexusOS every 30 seconds
- Tracks historical uptime (stores in a JSON file)
- Generates a markdown report on request
- Calculates "uptime %" for each service over the last 24 hours

### CHALLENGE 3: Automated DB Backup with Verification (Advanced)
Write a Python script that:
- Runs `pg_dump` via Docker exec
- Compresses and encrypts the output with `openssl`
- Verifies the backup by restoring to a temp DB and checking row counts
- Uploads to a local "offsite" directory with checksums
- Prunes old backups (keep last 7 daily, 4 weekly, 12 monthly — the Grandfather-Father-Son strategy)

### CHALLENGE 4: Config Drift Detector (Expert)
Write a Python script that:
- Takes a "snapshot" of all config file checksums and OS settings
- On subsequent runs, compares to the snapshot
- Reports any changes as a diff
- Integrates with the Pokevend API: if nginx config changes, check if the /health endpoint still responds
