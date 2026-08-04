#!/usr/bin/env python3
"""
SCRIPT: 05_load_tester.py
MODULE: Week 5 CAPSTONE — Cloud & Observability
READ FIRST: lessons/05_cloud_mastery.md — ALL of it

WHAT THIS SCRIPT DOES (when complete):
    The ultimate capstone. Runs a realistic load test against the entire
    NexusOS API, finds the breaking point, captures metrics during the test,
    and generates a professional Incident Report documenting the failure
    mode and remediation steps.

    This is what Google's SRE team does during "DiRT" (Disaster Recovery Tests).
    You are going to break your own system on purpose and document it.

KEY CONCEPTS YOU WILL MASTER:
    - Async/concurrent HTTP in Python (asyncio + aiohttp)
    - Load testing methodology (ramp up, steady state, ramp down)
    - Latency percentiles (p50, p95, p99 — what they mean and why p99 matters)
    - The G/L/E curve — how systems fail under load
    - Writing professional Root Cause Analysis documents

HOW TO RUN:
    python3 05_load_tester.py --users 50 --duration 60   # 50 concurrent, 60 seconds
    python3 05_load_tester.py --users 200 --ramp-up 30   # Ramp to 200 users over 30s
    python3 05_load_tester.py --scenario search           # Run specific test scenario
    python3 05_load_tester.py --find-breaking-point       # Binary search for max capacity

PREREQUISITES:
    pip3 install aiohttp    # async HTTP client
    (or: sudo apt install python3-aiohttp)

WHEN YOU KNOW YOU'RE DONE:
    1. Run the load test
    2. Find at what request rate errors start appearing
    3. Look at Grafana/Prometheus during the test (if you've done Task 5.3)
    4. Write the Incident Report (the write_incident_report() function)
    5. Implement at least ONE fix and re-run to verify improvement
"""

import asyncio
import sys
import time
import json
import math
import argparse
import statistics
import datetime
from pathlib import Path
from typing import NamedTuple
from collections import defaultdict

# Requires: pip install aiohttp
try:
    import aiohttp
except ImportError:
    print("ERROR: aiohttp not installed. Run: pip3 install aiohttp")
    sys.exit(1)

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8080/api/v1"
RESULTS_DIR = Path("/var/log/pokevend/load_tests")

# ── Test Scenarios ────────────────────────────────────────────────────────────
# Real-world user behavior patterns for a Pokémon card marketplace
SCENARIOS = {
    "browse": {
        "description": "User browses trending cards",
        "requests": [
            {"method": "GET", "path": "/cards/trending", "weight": 30},
            {"method": "GET", "path": "/cards/search?q=charizard&limit=20", "weight": 40},
            {"method": "GET", "path": "/cards/search?q=pikachu&limit=20", "weight": 20},
            {"method": "GET", "path": "/health", "weight": 10},
        ]
    },
    "search": {
        "description": "Heavy search load",
        "requests": [
            {"method": "GET", "path": "/cards/search?q=charizard", "weight": 25},
            {"method": "GET", "path": "/cards/search?q=mewtwo", "weight": 25},
            {"method": "GET", "path": "/cards/search?q=blastoise", "weight": 25},
            {"method": "GET", "path": "/cards/search?q=venusaur", "weight": 25},
        ]
    },
    "auth": {
        "description": "Authentication load (login flow)",
        "requests": [
            {"method": "POST", "path": "/auth/login",
             "body": {"email": "test@test.com", "password": "testpass"}, "weight": 100},
        ]
    }
}


# ── Data Structures ───────────────────────────────────────────────────────────
class RequestResult(NamedTuple):
    url:          str
    method:       str
    status_code:  int
    latency_ms:   float
    error:        str         # Empty string if no error
    timestamp:    float       # Unix timestamp when request was made


class LoadTestMetrics:
    """Collects and analyzes load test results."""
    
    def __init__(self):
        self.results: list[RequestResult] = []
        self.start_time: float = 0
        self.end_time: float = 0
    
    def add(self, result: RequestResult) -> None:
        self.results.append(result)
    
    def total_requests(self) -> int:
        # TODO: Return count of all results
        pass
    
    def error_rate(self) -> float:
        """
        TODO: Return percentage of requests that failed (status >= 400 OR error != "")
        """
        pass
    
    def throughput_rps(self) -> float:
        """
        TODO: Return requests per second = total_requests / duration
        """
        pass
    
    def latency_percentile(self, percentile: float) -> float:
        """
        Return the Nth percentile of latency.
        
        This is the MOST IMPORTANT metric in load testing.
        - p50 (median): half of requests are faster than this
        - p95: 95% of requests are faster — represents a "bad experience" 
        - p99: only 1% are slower — represents your WORST users
        
        A service with p50=50ms and p99=5000ms has a SERIOUS problem —
        1% of users wait 5 seconds. At 10,000 RPS, that's 100 users/second
        having a terrible experience.
        
        TODO: Sort latencies and return the value at the given percentile index
        HINT:
            latencies = sorted([r.latency_ms for r in self.results if not r.error])
            if not latencies: return 0
            idx = int(len(latencies) * percentile / 100)
            return latencies[min(idx, len(latencies) - 1)]
        """
        pass
    
    def status_code_distribution(self) -> dict[int, int]:
        """
        TODO: Return dict mapping status_code → count
        Example: {200: 9800, 429: 150, 500: 50}
        """
        pass
    
    def requests_per_second_over_time(self) -> list[dict]:
        """
        TODO: Group requests by second and return time-series data
        Return: [{"second": 1, "rps": 47, "errors": 0}, ...]
        This lets you visualize the ramp-up curve
        """
        pass


# ── Worker (Single Virtual User) ─────────────────────────────────────────────

async def virtual_user(
    session: aiohttp.ClientSession,
    scenario: dict,
    metrics: LoadTestMetrics,
    duration_secs: float,
    user_id: int
) -> None:
    """
    Simulates a single concurrent user making requests for `duration_secs`.
    
    TODO:
    1. Record start time
    2. While (time.time() - start) < duration_secs:
       a. Pick a random request from scenario["requests"] weighted by "weight"
          HINT: random.choices([r["path"] for r in requests], weights=[r["weight"] for r in requests])
       b. Make the HTTP request with aiohttp
       c. Record the result in metrics
       d. Add a small random delay between requests (0.1-0.5 seconds)
          This simulates realistic think time between user actions
    
    HINT for making requests:
        start = time.time()
        try:
            async with session.get(f"{BASE_URL}{path}") as response:
                latency = (time.time() - start) * 1000
                metrics.add(RequestResult(
                    url=path, method="GET", status_code=response.status,
                    latency_ms=latency, error="", timestamp=time.time()
                ))
        except Exception as e:
            metrics.add(RequestResult(..., error=str(e)))
    """
    # YOUR CODE HERE
    pass


# ── Load Test Runner ──────────────────────────────────────────────────────────

async def run_load_test(
    scenario_name: str,
    concurrent_users: int,
    duration_secs: float,
    ramp_up_secs: float = 0
) -> LoadTestMetrics:
    """
    Run the full load test with the requested concurrency level.
    
    TODO:
    1. Create aiohttp ClientSession with a connector pool large enough for concurrent_users
       HINT: aiohttp.TCPConnector(limit=concurrent_users)
    
    2. If ramp_up_secs > 0, implement gradual ramp-up:
       - Start 1 user, add more until we reach concurrent_users over ramp_up_secs
       - This finds the breaking point more precisely
    
    3. Create concurrent_users coroutines running virtual_user()
    
    4. Use asyncio.gather() to run them all concurrently
    
    5. Print live progress every second: "t=10s | RPS: 47 | Errors: 0 | p99: 120ms"
    
    HINT for live progress (run as a separate task):
        async def print_progress():
            while True:
                await asyncio.sleep(1)
                print(f"RPS: {metrics.throughput_rps():.0f} | Error%: {metrics.error_rate():.1f}%")
    """
    # YOUR CODE HERE
    pass


# ── Breaking Point Finder ─────────────────────────────────────────────────────

async def find_breaking_point(scenario_name: str) -> dict:
    """
    Binary search for the maximum sustainable request rate.
    
    Algorithm:
    1. Start with 10 users
    2. If error rate < 1%: double the users
    3. If error rate >= 5%: halve the users
    4. Converge on the maximum users where error rate stays < 1%
    
    This is called a "binary search" on concurrency levels.
    
    TODO: Implement the binary search loop
    Each test run should be 30 seconds to get stable measurements.
    Return: {"max_users": N, "max_rps": X, "breaking_point_users": Y}
    """
    # YOUR CODE HERE
    pass


# ── Incident Report Generator ─────────────────────────────────────────────────

def write_incident_report(metrics: LoadTestMetrics, args: argparse.Namespace) -> str:
    """
    Generate a professional Incident Report based on the load test findings.
    
    This is the most important skill for a Future Standard Global Engineering Interview:
    Communicating technical findings clearly to both engineers AND business stakeholders.
    
    The report MUST contain:
    1. Executive Summary (2-3 sentences, non-technical, for business)
    2. Technical Summary (for engineers)
    3. Timeline of the test
    4. Key Metrics Table
    5. Failure Mode Analysis (what broke and why)
    6. Root Cause Analysis
    7. Remediation Steps (ranked by impact vs effort)
    8. Verification Plan (how to confirm the fix worked)
    
    TODO: Write this function. It should generate a Markdown document.
    
    TEMPLATE TO FOLLOW:
    ---
    # Load Test Incident Report
    **Date**: 2026-04-01
    **Tester**: iscjmz
    **Environment**: Local NexusOS stack
    
    ## Executive Summary
    The Pokevend API showed [healthy/degraded] performance under load testing.
    At [N] concurrent users, error rates exceeded 1% threshold, indicating
    the system can sustain approximately [X] requests per second before degradation.
    
    ## Key Metrics
    | Metric          | Value   |
    |-----------------|---------|
    | Total Requests  | 45,231  |
    | Error Rate      | 2.3%    |
    | Throughput      | 452 RPS |
    | Latency p50     | 45ms    |
    | Latency p95     | 230ms   |
    | Latency p99     | 850ms   |
    
    ## Failure Mode
    [What actually broke? Did the database run out of connections?
     Did Redis start rejecting connections? Did Go run OOM?]
    
    ## Root Cause
    [The exact technical reason. Be specific.]
    
    ## Remediation Steps
    1. [Most impactful fix, lowest effort]
    2. [Second fix]
    ...
    ---
    """
    # YOUR CODE HERE
    pass


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """
    TODO: Add arguments:
      --users INT            (concurrent virtual users, default: 50)
      --duration INT         (test duration in seconds, default: 60)
      --ramp-up INT          (ramp-up duration in seconds, default: 0)
      --scenario NAME        (choices: browse, search, auth — default: browse)
      --find-breaking-point  (flag — run binary search for max capacity)
      --report-dir PATH      (where to write results, default: RESULTS_DIR)
    """
    # YOUR CODE HERE
    pass


async def main_async(args: argparse.Namespace) -> None:
    """
    TODO:
    1. If --find-breaking-point: call find_breaking_point()
    2. Else: call run_load_test()
    3. Print summary report to console
    4. Write detailed report to file with write_incident_report()
    5. Save raw metrics as JSON for future analysis
    """
    # YOUR CODE HERE
    pass


def main() -> None:
    args = parse_args()
    # asyncio.run() is how you run async code from synchronous Python
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
