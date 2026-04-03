#!/usr/bin/env python3
"""
SCRIPT: 01_port_scanner.py
MODULE: Week 3 — Networking & Protocol Fundamentals
READ FIRST: lessons/03_networking_mastery.md — ALL of it

WHAT THIS SCRIPT DOES (when complete):
    Scans every expected service port for the NexusOS stack, tests TCP
    connectivity, measures response latency, and flags any port that is
    either unexpectedly OPEN (security risk!) or unexpectedly CLOSED
    (service is down). Also performs application-level checks beyond
    simple TCP connection.

KEY CONCEPTS YOU WILL MASTER:
    - Python's `socket` module — raw TCP connection testing
    - Concurrent scanning with `concurrent.futures.ThreadPoolExecutor`
    - The difference between "port open" and "service responding"
    - Why you should scan from OUTSIDE your network, not just inside
    - Port scanning as a security tool (and as an attacker tool)

HOW TO RUN:
    python3 01_port_scanner.py
    python3 01_port_scanner.py --target localhost
    python3 01_port_scanner.py --target 10.0.0.5 --range 1-65535   # Full scan
    python3 01_port_scanner.py --report json > ports.json

WHEN YOU KNOW YOU'RE DONE:
    Run it against your local NexusOS stack — every expected port should
    show as OPEN. Then: `docker stop nexusos-redis` and re-run — Redis port
    should now show as CLOSED with a warning.
"""

import socket
import concurrent.futures
import json
import sys
import argparse
import time
from typing import NamedTuple
from datetime import datetime

# ── Expected NexusOS Service Ports ────────────────────────────────────────────
# This is the "contract" — these ports SHOULD be open on the NexusOS host
# Anything NOT in this list that IS open = security finding!
EXPECTED_SERVICES = {
    22:    {"name": "SSH",            "proto": "TCP", "public": False},
    80:    {"name": "HTTP (Nginx)",   "proto": "TCP", "public": True},
    443:   {"name": "HTTPS (Nginx)",  "proto": "TCP", "public": True},
    5432:  {"name": "PostgreSQL",     "proto": "TCP", "public": False},
    6333:  {"name": "Qdrant HTTP",    "proto": "TCP", "public": False},
    6334:  {"name": "Qdrant gRPC",    "proto": "TCP", "public": False},
    6379:  {"name": "Redis",          "proto": "TCP", "public": False},
    7233:  {"name": "Temporal gRPC",  "proto": "TCP", "public": False},
    8080:  {"name": "Pokevend API",   "proto": "TCP", "public": False},
    8088:  {"name": "Temporal UI",    "proto": "TCP", "public": False},
    9092:  {"name": "Kafka",          "proto": "TCP", "public": False},
    2181:  {"name": "Zookeeper",      "proto": "TCP", "public": False},
    11434: {"name": "Ollama AI",      "proto": "TCP", "public": False},
}

# Ports that should ONLY be accessible internally, never from the internet
INTERNAL_ONLY_PORTS = {5432, 6379, 6333, 6334, 7233, 9092, 2181, 11434}


# ── Data Structures ───────────────────────────────────────────────────────────
class PortResult(NamedTuple):
    port:         int
    is_open:      bool
    latency_ms:   float
    service_name: str
    expected:     bool    # Was this port expected to be open?
    public:       bool    # Should this be publicly accessible?
    error:        str     # Error message if connection failed


# ── Core Scanning Functions ───────────────────────────────────────────────────

def scan_port(host: str, port: int, timeout: float = 2.0) -> PortResult:
    """
    Test if a TCP port is open on the given host.
    
    Returns a PortResult with the connection state and latency.
    
    TODO:
    1. Create a TCP socket: socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       AF_INET = IPv4, SOCK_STREAM = TCP (vs SOCK_DGRAM = UDP)
    
    2. Set the timeout: sock.settimeout(timeout)
       WHY: Without a timeout, a closed port waits forever for a RST packet
    
    3. Record the start time with time.time()
    
    4. Attempt connection: sock.connect_ex((host, port))
       connect_ex returns 0 if successful, error code if not
       (unlike connect() which RAISES an exception — we want to handle this gracefully)
    
    5. Calculate latency = (time.time() - start) * 1000
    
    6. Close the socket: sock.close() (always! use try/finally)
    
    7. Look up the port in EXPECTED_SERVICES and build the PortResult
    
    HINT:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start = time.time()
        try:
            result_code = sock.connect_ex((host, port))
            latency = (time.time() - start) * 1000
            is_open = (result_code == 0)
        finally:
            sock.close()
    """
    # YOUR CODE HERE
    pass


def scan_range(host: str, port_range: tuple[int, int], 
               max_workers: int = 100) -> list[PortResult]:
    """
    Scan a RANGE of ports concurrently using a thread pool.
    
    This is much faster than scanning ports one by one.
    Scanning 65535 ports sequentially at 2s timeout = 36 hours.
    With 100 threads: 36 hours / 100 = ~22 minutes.
    
    TODO:
    1. Create a list of ports to scan: range(port_range[0], port_range[1] + 1)
    
    2. Use concurrent.futures.ThreadPoolExecutor with max_workers threads
    
    3. Submit scan_port(host, port) for each port
    
    4. Collect results as they complete (use as_completed for live progress)
    
    HINT:
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(scan_port, host, port): port 
                      for port in range(port_range[0], port_range[1] + 1)}
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        return sorted(results, key=lambda r: r.port)
    """
    # YOUR CODE HERE
    pass


def scan_expected_only(host: str) -> list[PortResult]:
    """
    Only scan the ports that we EXPECT to be open (faster, more targeted).
    This is the default mode — we care about our specific services.
    
    TODO: Scan only the ports in EXPECTED_SERVICES using scan_range or individual calls.
    Return a list of PortResult objects.
    """
    # YOUR CODE HERE
    pass


# ── Application-Level Checks ──────────────────────────────────────────────────

def check_http_endpoint(host: str, port: int, path: str = "/") -> dict:
    """
    Beyond just "is the port open?", check if the HTTP service responds correctly.
    
    TODO:
    1. Make an HTTP GET request to http://host:port/path
    2. Return dict with: status_code, response_time_ms, content_type, body_preview
    3. Handle connection refused, timeout, etc.
    
    HINT: Use urllib.request.urlopen with timeout
    """
    # YOUR CODE HERE
    pass


def check_postgres_auth(host: str, port: int = 5432) -> dict:
    """
    Beyond open port — can we actually reach the PostgreSQL protocol?
    
    TODO:
    1. Connect to the port
    2. PostgreSQL sends a challenge on connection — read the first 4 bytes
    3. If you get a response, the service is truly alive
    
    WHY: A port can be "open" (TCP accepts connection) but the service
    behind it might be crashed and just accepting connections without responding.
    This is rare but happens during certain crash states.
    """
    # YOUR CODE HERE
    pass


# ── Analysis & Findings ───────────────────────────────────────────────────────

def analyze_results(results: list[PortResult]) -> dict:
    """
    Analyze scan results and generate security findings.
    
    TODO: Build a findings dict containing:
    
    1. "expected_open_but_closed": ports we expect to be open but aren't
       → Service is DOWN (operational issue)
    
    2. "unexpected_open": ports that are open but NOT in EXPECTED_SERVICES  
       → Unknown service — SECURITY FINDING
    
    3. "internal_ports_exposed": INTERNAL_ONLY_PORTS that are somehow open
       → Database/Redis exposed to network — CRITICAL SECURITY FINDING
    
    4. "high_latency": services with latency > 500ms
       → Performance issue
    
    5. "summary": overall health score (0-100)
    """
    # YOUR CODE HERE
    pass


# ── Report Generation ─────────────────────────────────────────────────────────

def print_text_report(results: list[PortResult], findings: dict) -> None:
    """
    Print a human-readable table showing all port scan results.
    
    TODO: Print a formatted table like:
    
    PORT    SERVICE          STATUS    LATENCY   FINDING
    ───────────────────────────────────────────────────
    22      SSH              ✅ OPEN   1.2ms
    80      HTTP (Nginx)     ✅ OPEN   0.8ms
    443     HTTPS (Nginx)    ❌ CLOSED          ⚠ SERVICE DOWN
    5432    PostgreSQL       ✅ OPEN   0.5ms
    8888    ???              ✅ OPEN             🚨 UNEXPECTED PORT
    
    For the security findings section, highlight CRITICAL ones in red.
    """
    # YOUR CODE HERE
    pass


def print_json_report(results: list[PortResult], findings: dict) -> None:
    """
    TODO: Convert results to a JSON-serializable dict and print with json.dumps(indent=2)
    PortResult is a NamedTuple so use result._asdict() to convert to dict
    """
    # YOUR CODE HERE
    pass


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """
    TODO: Add arguments:
      --target HOST      (default: localhost)
      --range START-END  (e.g. "1-1024", default: only expected ports)
      --report FORMAT    (choices: ["text", "json"], default: "text")
      --timeout SECS     (connection timeout, default: 2.0)
      --workers INT      (concurrent threads, default: 50)
    """
    # YOUR CODE HERE
    pass


def main() -> None:
    """
    TODO:
    1. Parse args
    2. If --range given: call scan_range()
       If not: call scan_expected_only()
    3. Run application-level checks on HTTP ports
    4. analyze_results()
    5. Print report in requested format
    6. Exit with code 1 if any CRITICAL findings exist
    """
    # YOUR CODE HERE
    pass


if __name__ == "__main__":
    main()
