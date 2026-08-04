#!/usr/bin/env python3
"""
SANDBOX: python_practice.py
PURPOSE: Your personal Python training ground
READ:    lessons/PYTHON_MASTERY_COMPLETE.md

HOW TO USE:
    python3 infra/practice/python_practice.py           # All exercises
    python3 infra/practice/python_practice.py 1         # Only exercise 1
    python3 infra/practice/python_practice.py 3         # Only exercise 3

Modify, break, fix, re-run. That's the loop.
"""

import subprocess
import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent  # shopify/shopify/


# ============================================================
# EXERCISE 1: Data Types & Comprehensions
# Master: strings, lists, dicts, and comprehensions
# ============================================================
def exercise_1_data_types():
    print("=" * 60)
    print("EXERCISE 1: Data Types & Comprehensions")
    print("=" * 60)

    # ── Part A: String parsing ─────────────────────────────────
    # Parse a real docker stats output line
    docker_stats_line = "nexusos-postgres    2.56%     150MiB / 8GiB    1.83%"
    parts = docker_stats_line.split()

    name   = parts[0]
    cpu    = float(parts[1].rstrip('%'))   # "2.56%" → 2.56
    mem    = parts[2]
    # mem_limit = parts[4]

    print(f"\nParsed docker stats:")
    print(f"  Container: {name}")
    print(f"  CPU: {cpu:.1f}%")
    print(f"  Memory: {mem}")
    print(f"  High CPU: {cpu > 80}")

    # ── Part B: List comprehensions ────────────────────────────
    log_lines = [
        '{"level":"info","msg":"Server started","port":8080}',
        '{"level":"error","msg":"DB connection failed","retry":1}',
        '{"level":"info","msg":"Health check passed"}',
        '{"level":"error","msg":"Redis timeout","duration_ms":5001}',
        '{"level":"warn","msg":"High memory usage","pct":87}',
        '{"level":"error","msg":"DB connection failed","retry":2}',
    ]

    # Parse the JSON lines
    parsed = [json.loads(line) for line in log_lines]

    # Get only error lines
    errors = [e for e in parsed if e["level"] == "error"]
    print(f"\nError lines: {len(errors)}/{len(parsed)} total")

    # Extract all unique messages
    unique_msgs = list({e["msg"] for e in parsed})  # set comprehension for unique
    print(f"Unique messages: {unique_msgs}")

    # Count by level
    level_counts = {}
    for entry in parsed:
        level = entry["level"]
        level_counts[level] = level_counts.get(level, 0) + 1
    print(f"By level: {level_counts}")

    # ── YOUR CHALLENGE ─────────────────────────────────────────
    print("\nCHALLENGE:")
    print("  1. Find how many times 'DB connection failed' occurred")
    print("  2. Get the max duration_ms across ALL log entries (use .get())")
    print("  3. Build a dict: {message → count_of_occurrences}")
    # YOUR CODE HERE


# ============================================================
# EXERCISE 2: subprocess — Making Python Control the System
# ============================================================
def exercise_2_subprocess():
    print("\n" + "=" * 60)
    print("EXERCISE 2: subprocess")
    print("=" * 60)

    # ── Part A: Run a command and parse output ─────────────────
    result = subprocess.run(
        ["df", "-h", "/"],
        capture_output=True,
        text=True,
        check=True
    )

    # Parse the output (second line = / filesystem)
    lines = result.stdout.strip().split('\n')
    header  = lines[0].split()
    values  = lines[1].split()
    disk_info = dict(zip(header, values))
    print(f"\nRoot filesystem: {disk_info}")
    print(f"  Used: {disk_info.get('Used', 'N/A')}")
    print(f"  Available: {disk_info.get('Avail', 'N/A')}")

    # ── Part B: Get running Docker containers ──────────────────
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"],
            capture_output=True, text=True, check=True
        )
        
        containers = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                containers.append({
                    "name":   parts[0],
                    "status": parts[1],
                    "image":  parts[2],
                })
        
        print(f"\nRunning containers: {len(containers)}")
        for c in containers:
            print(f"  {c['name']:<30} {c['status']}")
            
    except subprocess.CalledProcessError:
        print("\nDocker not running or no containers")

    # ── Part C: Read /proc/meminfo ─────────────────────────────
    # LEARNING: /proc/meminfo is a virtual file that exposes kernel memory stats
    # No subprocess needed — just read the file!
    mem_info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, value = line.split(":", 1)
            mem_info[key.strip()] = value.strip()

    total_kb = int(mem_info["MemTotal"].split()[0])
    avail_kb = int(mem_info["MemAvailable"].split()[0])
    used_pct = ((total_kb - avail_kb) / total_kb) * 100

    print(f"\nMemory usage: {used_pct:.1f}%")
    print(f"  Total: {total_kb // 1024} MB")
    print(f"  Available: {avail_kb // 1024} MB")

    # ── YOUR CHALLENGE ─────────────────────────────────────────
    print("\nCHALLENGE:")
    print("  1. Run 'ss -tlnp' and extract all listening ports as a list of ints")
    print("  2. Read /proc/loadavg and parse the 1-min, 5-min, 15-min load averages")
    print("  3. Check if port 8080 is in the list from challenge 1")
    # YOUR CODE HERE


# ============================================================
# EXERCISE 3: File & Config Operations
# ============================================================
def exercise_3_files():
    print("\n" + "=" * 60)
    print("EXERCISE 3: Files & Paths")
    print("=" * 60)

    # ── Part A: Find all Go files in the Pokevend server ──────
    go_server = PROJECT_ROOT / "Pokemon" / "server"
    
    if go_server.exists():
        go_files = list(go_server.rglob("*.go"))
        print(f"\nGo files in Pokemon/server: {len(go_files)}")
        
        # Find the largest files
        go_files.sort(key=lambda f: f.stat().st_size, reverse=True)
        print("Largest Go files:")
        for f in go_files[:5]:
            size_kb = f.stat().st_size / 1024
            print(f"  {size_kb:6.1f} KB  {f.relative_to(go_server)}")
    else:
        print(f"\n(Project not found at {go_server})")

    # ── Part B: Parse the .env.example file ────────────────────
    env_example = PROJECT_ROOT / ".env.example"
    
    if env_example.exists():
        config = {}
        with open(env_example) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, _, value = line.partition('=')
                    config[key.strip()] = value.strip()
        
        print(f"\n.env.example has {len(config)} settings:")
        for key, value in list(config.items())[:5]:
            # Redact anything that looks like a password/secret
            if any(word in key.lower() for word in ['pass', 'secret', 'key', 'token']):
                print(f"  {key} = [REDACTED]")
            else:
                print(f"  {key} = {value}")
    
    # ── Part C: Generate a config report ───────────────────────
    report = {
        "generated_at": datetime.now().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "go_files": len(go_files) if go_server.exists() else 0,
    }
    
    # Write to /tmp (temporary)
    report_path = Path("/tmp/nexusos_file_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nReport written to: {report_path}")

    # ── YOUR CHALLENGE ─────────────────────────────────────────
    print("\nCHALLENGE:")
    print("  1. Count lines of code in all .go files (grep 'package' is not enough!)")
    print("     HINT: open each file, count non-empty lines")
    print("  2. Find the go file with the MOST functions (grep 'func ')")
    print("  3. Scan all .go files for 'TODO' comments and print them")
    # YOUR CODE HERE


# ============================================================
# EXERCISE 4: Error Handling — Build It Right
# ============================================================
def exercise_4_error_handling():
    print("\n" + "=" * 60)
    print("EXERCISE 4: Error Handling")
    print("=" * 60)

    # ── Part A: Robust health checker ────────────────────────
    import urllib.request
    import urllib.error
    
    def check_service_health(url: str, name: str) -> dict:
        """
        Checks a service's health endpoint.
        NEVER raises — always returns a status dict.
        """
        try:
            start = datetime.now()
            with urllib.request.urlopen(url, timeout=3) as response:
                elapsed = (datetime.now() - start).total_seconds() * 1000
                body = response.read()
                
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    data = {"raw": body.decode(errors='ignore')[:100]}
                
                return {
                    "name":       name,
                    "url":        url,
                    "status":     "healthy",
                    "http_code":  response.status,
                    "latency_ms": round(elapsed, 1),
                    "data":       data,
                }
        
        except urllib.error.HTTPError as e:
            return {"name": name, "status": "error", "http_code": e.code}
        except urllib.error.URLError as e:
            return {"name": name, "status": "unreachable", "reason": str(e.reason)}
        except Exception as e:
            return {"name": name, "status": "unknown", "error": str(e)}
    
    # Health check all services
    endpoints = [
        ("http://localhost:8080/health",   "Pokevend API"),
        ("http://localhost:6333/readyz",   "Qdrant Vector DB"),
        ("http://localhost:11434/api/tags", "Ollama AI"),
        ("http://localhost:8088",          "Temporal UI"),
    ]
    
    print("\nService Health Checks:")
    all_results = []
    for url, name in endpoints:
        result = check_service_health(url, name)
        status = result["status"]
        latency = result.get("latency_ms", "-")
        indicator = "✓" if status == "healthy" else "✗"
        print(f"  {indicator} {name:<25} {status:<12} {latency}ms" if latency != "-"
              else f"  {indicator} {name:<25} {status}")
        all_results.append(result)
    
    healthy = sum(1 for r in all_results if r["status"] == "healthy")
    print(f"\n  {healthy}/{len(all_results)} services healthy")

    # ── YOUR CHALLENGE ─────────────────────────────────────────
    print("\nCHALLENGE:")
    print("  1. Add a retry mechanism — try each URL up to 3 times before marking unhealthy")
    print("  2. Calculate the average latency across all healthy services")
    print("  3. If ANY service is unhealthy, exit with code 1 (non-zero)")
    # YOUR CODE HERE


# ============================================================
# EXERCISE 5: Build a Real Tool — NexusOS Status Reporter
# This is the capstone. When done, this should be genuinely useful.
# ============================================================
def exercise_5_status_reporter():
    print("\n" + "=" * 60)
    print("EXERCISE 5: NexusOS Status Reporter")
    print("=" * 60)

    # TODO: Build a complete status reporter that:
    # 1. Checks memory and disk usage (from /proc/meminfo and df)
    # 2. Gets all Docker container statuses
    # 3. Checks the Pokevend API /health endpoint
    # 4. Generates a formatted markdown report to /tmp/nexusos_status.md
    # 5. Prints a text summary to stdout

    # STRUCTURE your code:
    # - collect_system_metrics() → dict with memory, disk stats
    # - collect_container_statuses() → list of container dicts
    # - check_api_health() → dict with health check result
    # - generate_report(metrics, containers, health) → markdown string
    # - main → calls all above, writes report, prints summary

    # HINT: Start with collect_system_metrics() — you know how to do this
    # from exercises 2 and 3. Then build up from there.
    
    print("STATUS REPORTER NOT IMPLEMENTED YET")
    print("Complete this exercise by building all 5 components above.")
    print("When done, you will have a real tool you can schedule with cron.")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    exercise_map = {
        "1": exercise_1_data_types,
        "2": exercise_2_subprocess,
        "3": exercise_3_files,
        "4": exercise_4_error_handling,
        "5": exercise_5_status_reporter,
    }

    if len(sys.argv) > 1:
        key = sys.argv[1]
        if key in exercise_map:
            exercise_map[key]()
        else:
            print(f"Unknown exercise: {key}. Choose 1-5")
            sys.exit(1)
    else:
        # Run all
        for func in exercise_map.values():
            func()


if __name__ == "__main__":
    main()
