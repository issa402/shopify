#!/usr/bin/env python3
"""
SCRIPT: 03_storage_audit.py
MODULE: Week 1 — Linux System Administration (Python edition)
READ FIRST: lessons/01_linux_mastery.md § PART 4 (Storage)
           lessons/02_scripting_mastery.md § PART 2 (Python)

WHAT THIS SCRIPT DOES (when complete):
    Monitors disk usage, finds large files/directories, checks PostgreSQL
    database size, and performs automated database backups with compression.
    Generates an alert if disk space falls below safe thresholds.

WHY THIS MATTERS:
    Disk-full events are one of the most common production incidents.
    They crash databases (PostgreSQL stops writing), logs disappear,
    and apps start failing in bizarre ways. Your job is to PREVENT this.
    This script is what you'd run as a hourly cron job.

HOW TO RUN:
    python3 infra/scripts/linux/03_storage_audit.py
    python3 infra/scripts/linux/03_storage_audit.py --backup
    python3 infra/scripts/linux/03_storage_audit.py --threshold 90

WHEN YOU KNOW YOU'RE DONE:
    Without --backup: prints a full storage report
    With --backup: creates and compresses a PostgreSQL dump
    All alerts write to /var/log/pokevend/storage_alerts.log
"""

import subprocess
import argparse
import sys
import os
import shutil
import datetime
import json
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────
# These are environment-specific. In production, read from /etc/pokevend/config.env
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "nexusos")
DB_NAME = os.getenv("DB_NAME", "nexusos")

BACKUP_DIR = Path("/var/backups/pokevend")
LOG_DIR    = Path("/var/log/pokevend")
ALERT_LOG  = LOG_DIR / "storage_alerts.log"

# Thresholds (percentage used — alert if exceeded)
WARNING_THRESHOLD  = 80  # 80% full = warning
CRITICAL_THRESHOLD = 90  # 90% full = critical


# ── Logging ─────────────────────────────────────────────────────────────────
# TODO: Set up Python's logging module so messages go to both stdout AND a log file
# READ: lessons/02_scripting_mastery.md "Logging — The Professional Way"
# Requirements:
#   - Format: "2026-04-01 14:23:01 [INFO] message"
#   - Handlers: StreamHandler (console) + FileHandler (ALERT_LOG)
#
# HINT: Import logging, create handlers, set level, attach formatters
# YOUR CODE HERE
# import logging
# logging.basicConfig(...)
# logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    TODO: Create an argument parser with these arguments:
      --backup         (flag, action="store_true") — triggers DB backup creation
      --threshold INT  (optional, default=80) — warning threshold percentage
      --output FORMAT  (optional, choices=["text","json"], default="text") — report format
    
    READ: lessons/02_scripting_mastery.md "argparse — Professional CLI Scripts"
    """
    # YOUR CODE HERE
    pass


def get_disk_usage() -> list[dict]:
    """
    Returns a list of filesystem disk usage stats.
    
    Each dict should look like:
    {
        "filesystem": "/dev/sda1",
        "size_human": "50G",
        "used_human": "12G",
        "available_human": "38G",
        "percent_used": 24,
        "mount_point": "/"
    }
    
    TODO 1: Run `df -h` using subprocess.run()
            READ: lessons/02_scripting_mastery.md "subprocess.run()"
    
    TODO 2: Parse each output line. The columns are:
            Filesystem  Size  Used  Avail  Use%  Mounted-on
            Skip the first line (header)
    
    HINT: 
        result = subprocess.run(["df", "-h"], capture_output=True, text=True, check=True)
        for line in result.stdout.strip().split('\n')[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 6:
                percent = int(parts[4].rstrip('%'))
                ...
    """
    # YOUR CODE HERE
    pass


def get_largest_directories(path: str, top_n: int = 10) -> list[tuple[str, int]]:
    """
    Find the largest subdirectories under `path`.
    Returns list of (path, size_bytes) tuples, sorted by size descending.
    
    TODO 1: Use subprocess to run: du -sb <path>/* 2>/dev/null
            -s = summary (don't recurse), -b = bytes
    
    TODO 2: Parse the output (each line is "SIZE\tDIRECTORY")
    
    TODO 3: Return sorted list, largest first, limited to top_n items
    
    HINT: 
        result = subprocess.run(
            f"du -sb {path}/* 2>/dev/null || true",
            shell=True, capture_output=True, text=True
        )
        # Parse each line: line.split('\t') gives [size_str, path_str]
    """
    # YOUR CODE HERE
    pass


def get_postgres_db_size() -> dict:
    """
    Connect to PostgreSQL and get the size of each database.
    Uses psql command-line tool (no Python postgres driver needed).
    
    Returns:
    {
        "databases": [
            {"name": "nexusos", "size": "234 MB"},
            {"name": "postgres", "size": "8.2 MB"}
        ]
    }
    
    TODO 1: Run this SQL via psql:
            SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
            FROM pg_database ORDER BY pg_database_size(datname) DESC;
    
    TODO 2: Parse the output. psql -t (tuple-only) returns clean rows: "nexusos | 234 MB"
    
    HINT:
        sql = "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database ORDER BY 2 DESC;"
        result = subprocess.run(
            ["psql", "-h", DB_HOST, "-p", DB_PORT, "-U", DB_USER, "-t", "-c", sql],
            capture_output=True, text=True
        )
        # Note: if psql is not available or postgres is down, handle the exception!
        # In docker: docker exec nexusos-postgres psql -U nexusos -t -c "..."
    """
    # YOUR CODE HERE
    pass


def backup_database() -> Path:
    """
    Creates a compressed, timestamped backup of the PostgreSQL database.
    
    TODO 1: Create the backup directory if it doesn't exist
            READ: lessons/02_scripting_mastery.md "pathlib"
            HINT: BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    TODO 2: Build a backup filename with current timestamp
            HINT: timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                  backup_path = BACKUP_DIR / f"pokevend_{timestamp}.sql"
    
    TODO 3: Run pg_dump in a Docker container (since postgres runs in docker here)
            Database is in the nexusos-postgres container.
            HINT: docker exec nexusos-postgres pg_dump -U nexusos nexusos > /tmp/db.sql
            Then copy from container to host with docker cp
    
    TODO 4: Compress the backup with gzip
            HINT: subprocess.run(["gzip", str(backup_path)])
                  This creates backup_path.gz and DELETES the original
    
    TODO 5: Calculate and print the compressed file size
    
    TODO 6: Return the path to the compressed file
    
    IMPORTANT: If pg_dump fails, the function must raise an exception.
               Never silently create an empty backup file!
    """
    # YOUR CODE HERE
    pass


def check_thresholds(disk_stats: list[dict], threshold: int) -> list[str]:
    """
    Compare disk usage against the threshold and return a list of alert strings.
    
    TODO: Iterate over disk_stats. For any filesystem where percent_used > threshold,
          add an alert string like:
          "WARN: /dev/sda1 mounted at / is 87% full (threshold: 80%)"
    
    If percent_used > 95, use "CRITICAL:" prefix instead of "WARN:"
    """
    alerts = []
    # YOUR CODE HERE
    return alerts


def write_alert(message: str) -> None:
    """
    Write a critical alert to the alert log with timestamp.
    
    TODO: Append to ALERT_LOG (create directory/file if they don't exist)
          Format: "[2026-04-01T14:23:01] ALERT: your message here"
    """
    # YOUR CODE HERE
    pass


def generate_report(disk_stats: list[dict], alerts: list[str], db_info: dict, output_format: str) -> None:
    """
    Print the full storage audit report.
    
    TODO: If output_format is "json", print everything as JSON (json.dumps with indent=2)
          If output_format is "text", print a nicely formatted human-readable report
    
    The report should show:
    1. Overall disk usage table (filesystem, size, used, free, %)
    2. Any alerts (highlighted)
    3. Database sizes
    4. Top 5 largest directories under /var and /opt
    """
    # YOUR CODE HERE
    pass


def main() -> None:
    """
    Main entry point — orchestrates the full audit.
    
    TODO: 
    1. Parse args
    2. Gather all data (disk_stats, alerts, db_info)
    3. Write any alerts to the log file
    4. If --backup flag is set, run backup_database()
    5. Generate and print the report
    6. Exit with code 1 if there are CRITICAL alerts (so cron jobs can detect failure)
    """
    # YOUR CODE HERE
    pass


if __name__ == "__main__":
    main()
