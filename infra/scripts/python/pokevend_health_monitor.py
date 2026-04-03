#!/usr/bin/env python3
"""
SCRIPT: pokevend_health_monitor.py
MODULE: Python + Linux — Week 2
TIES TO THESE REAL PROJECT FILES:
    handlers/health_handler.go  — what the /health endpoint does
    config/config.go            — env vars and defaults
    docker-compose.yml          — all service definitions

WHAT IT DOES (when complete):
    Polls every Pokevend service every N seconds.
    Tracks uptime history. Fires alerts when services go down.
    Generates a markdown status page at /tmp/pokevend_status.md
    This is exactly what StatusPage.io / Uptime Robot does — you're building
    a mini version tailored to your exact stack.

REAL ENDPOINTS IT HITS:
    http://localhost:3001/health  → Go API (health_handler.go)
    http://localhost:6333/readyz  → Qdrant
    http://localhost:11434/api/tags → Ollama
    tcp://localhost:5432          → PostgreSQL
    tcp://localhost:6379          → Redis
    tcp://localhost:9092          → Kafka
    tcp://localhost:7233          → Temporal

HOW TO RUN:
    python3 infra/scripts/python/pokevend_health_monitor.py
    python3 infra/scripts/python/pokevend_health_monitor.py --interval 10
    python3 infra/scripts/python/pokevend_health_monitor.py --once     (single check)
    python3 infra/scripts/python/pokevend_health_monitor.py --output /tmp/status.md

WHAT YOU LEARN:
    - subprocess for running docker commands
    - socket for TCP port checking (without HTTP libraries)
    - urllib.request for HTTP health checks
    - datetime and time for tracking check history
    - pathlib for writing reports
    - argparse for CLI flags
    - The while True loop pattern for monitoring daemons
"""

import socket
import subprocess
import urllib.request
import urllib.error
import json
import time
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# =============================================================================
# REAL SERVICE DEFINITIONS
# Every entry maps EXACTLY to a service in docker-compose.yml
# =============================================================================
SERVICES = [
    # name, check_type, host, port, path (for HTTP only)
    # Source: config.go line 69: getEnv("PORT", "3001")
    # Source: health_handler.go: returns {"status":"ok","service":"pokemontool-go"}
    {
        "name":       "Pokevend Go API",
        "container":  None,   # runs outside docker in dev
        "type":       "http",
        "host":       "localhost",
        "port":       int(os.getenv("PORT", "3001")),
        "path":       "/health",
        "critical":   True,   # API down = product is down
        "expected_json_key": "status",
        "expected_json_val": "ok",
    },
    # Source: docker-compose.yml line 19: pg_isready -U nexusos
    # Source: config.go line 74: getEnv("POSTGRES_HOST", "localhost")
    {
        "name":       "PostgreSQL",
        "container":  "nexusos-postgres",
        "type":       "tcp",
        "host":       "localhost",
        "port":       int(os.getenv("POSTGRES_PORT", "5432")),
        "path":       None,
        "critical":   True,   # health_handler.go fails if DB is down
    },
    # Source: docker-compose.yml line 34: redis-cli ping
    # Source: config.go line 81: getEnv("REDIS_URL", "redis:6379")
    {
        "name":       "Redis Cache",
        "container":  "nexusos-redis",
        "type":       "tcp",
        "host":       "localhost",
        "port":       6379,
        "path":       None,
        "critical":   True,   # health_handler.go checks Redis
    },
    # Source: docker-compose.yml line 50: curl -sf http://localhost:6333/readyz
    {
        "name":       "Qdrant Vector DB",
        "container":  "nexusos-qdrant",
        "type":       "http",
        "host":       "localhost",
        "port":       6333,
        "path":       "/readyz",
        "critical":   False,  # AI search degrades, core API still works
    },
    # Source: docker-compose.yml line 88: kafka-broker-api-versions
    {
        "name":       "Kafka",
        "container":  "nexusos-kafka",
        "type":       "tcp",
        "host":       "localhost",
        "port":       9092,
        "path":       None,
        "critical":   False,  # Event streaming; API works without it
    },
    # Source: docker-compose.yml line 121: port 7233
    {
        "name":       "Temporal Workflows",
        "container":  "nexusos-temporal",
        "type":       "tcp",
        "host":       "localhost",
        "port":       7233,
        "path":       None,
        "critical":   False,
    },
    # Source: docker-compose.yml line 99: port 11434
    {
        "name":       "Ollama LLM",
        "container":  "nexusos-ollama",
        "type":       "http",
        "host":       "localhost",
        "port":       11434,
        "path":       "/api/tags",
        "critical":   False,
    },
]

# =============================================================================
# DATA STRUCTURES
# =============================================================================

class CheckResult:
    """Result of a single health check on a single service."""
    def __init__(self, service_name: str, is_healthy: bool,
                 latency_ms: float, detail: str, timestamp: datetime):
        self.service_name = service_name
        self.is_healthy   = is_healthy
        self.latency_ms   = round(latency_ms, 2)
        self.detail       = detail
        self.timestamp    = timestamp

    def __str__(self):
        status = "✓" if self.is_healthy else "✗"
        return f"{status} {self.service_name:<25} {self.latency_ms:>8.1f}ms  {self.detail}"


class ServiceHistory:
    """
    Tracks the last N check results for a service.
    Used to calculate uptime percentage.
    """
    def __init__(self, service_name: str, max_history: int = 100):
        self.service_name = service_name
        self.results: list[CheckResult] = []
        self.max_history  = max_history

    def add(self, result: CheckResult) -> None:
        """Add a check result, trim if over max."""
        self.results.append(result)
        if len(self.results) > self.max_history:
            self.results = self.results[-self.max_history:]

    def uptime_pct(self) -> float:
        """
        Calculate uptime percentage from stored history.

        TODO: Return the percentage of checks that were healthy.
              If no history yet, return 100.0 (assume up until proven otherwise)

        HINT:
            if not self.results: return 100.0
            healthy = sum(1 for r in self.results if r.is_healthy)
            return (healthy / len(self.results)) * 100
        """
        # YOUR CODE HERE
        return 100.0  # placeholder

    def last_result(self) -> Optional[CheckResult]:
        """Return the most recent check result, or None."""
        # TODO: Return last element of self.results, or None if empty
        # YOUR CODE HERE
        return None  # placeholder

    def consecutive_failures(self) -> int:
        """
        Count how many consecutive failures are at the end of history.
        Used to determine when to fire an alert.

        TODO:
        1. Start from the LAST result and count backwards
        2. Stop when you hit a healthy result
        3. Return the count

        WHY: 1 failure = noise. 3 in a row = real problem.
        """
        # YOUR CODE HERE
        return 0  # placeholder


# =============================================================================
# HEALTH CHECK FUNCTIONS
# =============================================================================

def check_tcp(host: str, port: int, timeout: float = 3.0) -> tuple[bool, float, str]:
    """
    Try to open a TCP connection to host:port.
    Returns (is_open, latency_ms, detail_message).

    This is how we check PostgreSQL, Redis, Kafka, Temporal —
    services that don't have HTTP health endpoints.

    TODO:
    1. Create socket: socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       AF_INET = IPv4, SOCK_STREAM = TCP (not UDP)
    2. Set timeout: sock.settimeout(timeout)
    3. Record start time: time.time()
    4. Try connect: result = sock.connect_ex((host, port))
       connect_ex returns 0 = success, non-zero = failure (don't raise)
    5. Calculate latency: (time.time() - start) * 1000
    6. Close socket in a finally block (ALWAYS close connections)
    7. Return (result == 0, latency_ms, "port open" or "connection refused")

    HINT:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start = time.time()
        try:
            code = sock.connect_ex((host, port))
            latency = (time.time() - start) * 1000
            return code == 0, latency, "open" if code == 0 else f"error {code}"
        finally:
            sock.close()
    """
    # YOUR CODE HERE
    return False, 0.0, "not implemented"  # placeholder


def check_http(host: str, port: int, path: str = "/",
               expected_key: str = None, expected_val: str = None,
               timeout: float = 5.0) -> tuple[bool, float, str]:
    """
    Make an HTTP GET request and check the response.
    Returns (is_healthy, latency_ms, detail_message).

    This is how we check the Go API (/health endpoint from health_handler.go),
    Qdrant (/readyz), and Ollama (/api/tags).

    TODO:
    1. Build URL: f"http://{host}:{port}{path}"
    2. Record start time
    3. Use urllib.request.urlopen(url, timeout=timeout) with a context manager
    4. Calculate latency
    5. Read and parse JSON response body (json.load(response))
    6. If expected_key is provided, check data[expected_key] == expected_val
    7. Return (True, latency, f"HTTP {status}") on success
    8. Handle exceptions:
       - urllib.error.HTTPError  → server responded with 4xx/5xx
       - urllib.error.URLError   → connection refused, DNS failure
       - json.JSONDecodeError    → server responded but not with JSON
       - Exception               → anything else

    REMEMBER:
    - health_handler.go returns: {"status":"ok","service":"pokemontool-go"}
    - We check: data["status"] == "ok"

    HINT:
        url = f"http://{host}:{port}{path}"
        start = time.time()
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                latency = (time.time() - start) * 1000
                data = json.load(resp)
                if expected_key and data.get(expected_key) != expected_val:
                    return False, latency, f"unexpected value: {data.get(expected_key)}"
                return True, latency, f"HTTP {resp.status}"
        except urllib.error.URLError as e:
            return False, (time.time()-start)*1000, str(e.reason)
    """
    # YOUR CODE HERE
    return False, 0.0, "not implemented"  # placeholder


def check_docker_container(container_name: str) -> tuple[str, str]:
    """
    Get the Docker status and health of a container.
    Returns (status, health) e.g. ("running", "healthy") or ("exited", "n/a")

    TODO:
    1. Run: docker inspect --format '{{.State.Status}}' <container>
       Use subprocess.run() with capture_output=True, text=True
    2. Also get health: --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}}'
    3. If the container doesn't exist, return ("not found", "n/a")
    4. Handle subprocess.CalledProcessError

    IMPORTANT: docker inspect returns non-zero if the container doesn't exist.
    Set check=False and check returncode manually.

    HINT:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", container_name],
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return "not found", "n/a"
        return result.stdout.strip(), health_str
    """
    # YOUR CODE HERE
    return "not implemented", "n/a"  # placeholder


def run_single_check(service: dict) -> CheckResult:
    """
    Run one health check for one service.

    TODO:
    1. If service["type"] == "http": call check_http()
    2. If service["type"] == "tcp":  call check_tcp()
    3. Wrap in try/except — a crash in one check must NOT stop others
    4. Return a CheckResult with the results

    The CheckResult needs: service_name, is_healthy, latency_ms, detail, timestamp
    """
    # YOUR CODE HERE
    return CheckResult(service["name"], False, 0.0, "not implemented", datetime.now())


# =============================================================================
# REPORTING
# =============================================================================

def print_console_report(histories: dict[str, ServiceHistory]) -> None:
    """
    Print a live console status table.

    TODO: Print a table like this:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    SERVICE                   LATENCY    STATUS    UPTIME
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ✓ Pokevend Go API          12.3ms    healthy    100.0%
    ✓ PostgreSQL                0.8ms    healthy    100.0%
    ✓ Redis Cache               0.4ms    healthy    100.0%
    ✗ Qdrant Vector DB          ---      down        73.0%
    ✓ Kafka                     1.2ms    healthy    100.0%

    Use: f"{'SERVICE':<28} {'LATENCY':>10} {'STATUS':<12} {'UPTIME':>8}"
    for alignment. Print ✓ green (healthy) and ✗ red (down).
    """
    # YOUR CODE HERE
    pass


def write_markdown_report(histories: dict[str, ServiceHistory], output_path: Path) -> None:
    """
    Write a markdown status page to output_path.

    TODO: Generate this format:
    # Pokevend Status Page
    _Last updated: 2026-04-01T14:23:01_

    ## Services

    | Service            | Status  | Latency | Uptime |
    |--------------------|---------|---------|--------|
    | Pokevend Go API    | ✅ UP   | 12.3ms  | 100%   |
    | PostgreSQL         | ✅ UP   | 0.8ms   | 100%   |
    | Qdrant Vector DB   | ❌ DOWN | ---     | 73%    |

    ## Recent Incidents
    [List any service that had downtime in the last 10 checks]

    Use output_path.write_text(markdown_string) to write it.
    """
    # YOUR CODE HERE
    pass


# =============================================================================
# ALERT SYSTEM
# =============================================================================

def should_alert(history: ServiceHistory, service: dict) -> bool:
    """
    Decide if we should fire an alert for this service.

    TODO:
    Alert if:
    1. Service is critical (service["critical"] == True) AND
       consecutive_failures >= 1 (went down immediately)
    OR
    2. Service is non-critical AND
       consecutive_failures >= 3 (give it a few chances)

    This avoids alert spam for transient failures.
    """
    # YOUR CODE HERE
    return False  # placeholder


def fire_alert(service: dict, history: ServiceHistory) -> None:
    """
    Fire an alert when a service goes down.

    TODO:
    Log a CRITICAL message to:
    1. stdout (print it prominently with red color)
    2. /var/log/pokevend/alerts.log (append)
    3. (Optional bonus) Write to a file that a Discord webhook script could pick up

    Format:
    [2026-04-01T14:23:01] ALERT: PostgreSQL has been down for 3 consecutive checks
    Action: docker-compose up -d postgres
    """
    # YOUR CODE HERE
    pass


# =============================================================================
# MAIN LOOP
# =============================================================================

def parse_args() -> argparse.Namespace:
    """
    TODO: Create argument parser with:
      --interval INT   (seconds between checks, default: 30)
      --once           (flag: run once and exit, default: False)
      --output PATH    (where to write markdown report, default: /tmp/pokevend_status.md)
      --quiet          (flag: suppress console output, only write file)
    """
    # YOUR CODE HERE
    # Temporary fallback so script runs while you implement
    class FakeArgs:
        interval = 30
        once = True
        output = "/tmp/pokevend_status.md"
        quiet = False
    return FakeArgs()


def main() -> None:
    """
    Main monitoring loop.

    TODO:
    1. Parse args
    2. Initialize a ServiceHistory for each service in SERVICES
    3. Run loop:
       a. For each service, run run_single_check()
       b. Add result to its ServiceHistory
       c. If should_alert(): call fire_alert()
       d. Print console report
       e. Write markdown report
       f. If --once: break
       g. Else: sleep(args.interval)
    4. Handle KeyboardInterrupt gracefully (print "Monitoring stopped" and exit 0)
    """
    args = parse_args()

    # Initialize history tracker for each service
    histories: dict[str, ServiceHistory] = {
        svc["name"]: ServiceHistory(svc["name"])
        for svc in SERVICES
    }

    print("Pokevend Health Monitor")
    print(f"Checking {len(SERVICES)} services...")
    print("")

    try:
        while True:
            # TODO: Run all checks, update histories, print report
            # YOUR CODE HERE

            # For now, run a single check to demonstrate the structure
            for service in SERVICES:
                result = run_single_check(service)
                histories[service["name"]].add(result)
                print(result)

            if args.once:
                break

            print(f"\nNext check in {args.interval}s (Ctrl+C to stop)")
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        sys.exit(0)

    # Write final report
    write_markdown_report(histories, Path(args.output))
    print(f"\nReport written to: {args.output}")


if __name__ == "__main__":
    main()
