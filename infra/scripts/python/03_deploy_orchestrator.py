#!/usr/bin/env python3
"""
SCRIPT: 03_deploy_orchestrator.py
MODULE: Week 2 CAPSTONE — Scripting Mastery
READ FIRST: lessons/02_scripting_mastery.md — ALL of it
PREREQUISITE: Complete ALL of 2.1 through 2.5 first

WHAT THIS SCRIPT DOES (when complete):
    A full production-grade deployment pipeline in Python. This is what
    CI/CD systems like GitHub Actions, Jenkins, and ArgoCD do under the hood.
    It handles: build, test, backup, deploy, verify, and rollback.

    THIS IS THE MOST IMPORTANT SCRIPT IN THE CURRICULUM.
    When you can build, understand, and explain every line of this —
    you can talk about it in a Future Standard interview and they will
    be genuinely impressed.

PIPELINE STAGES:
    Stage 0: Pre-flight  — check all dependencies and services are up
    Stage 1: Build       — compile the Go binary with go build
    Stage 2: Test        — run go test ./... and fail if tests fail
    Stage 3: Backup      — snapshot the database before changing anything
    Stage 4: Deploy      — atomic binary swap (zero-downtime)
    Stage 5: Verify      — hit /health endpoint, check database connection
    Stage 6: Rollback    — automatic rollback if verify fails

HOW TO RUN:
    python3 03_deploy_orchestrator.py --env staging --version $(git rev-parse --short HEAD)
    python3 03_deploy_orchestrator.py --env prod --version v1.2.3 --force
    python3 03_deploy_orchestrator.py --rollback --version v1.1.0

WHEN YOU KNOW YOU'RE DONE:
    - Deploying a bad binary (that won't start) triggers automatic rollback
    - Every stage is logged to /var/log/pokevend/deployments.log
    - Running it twice with the same version catches the duplicate
"""

import subprocess
import argparse
import sys
import os
import json
import time
import shutil
import logging
import urllib.request
import urllib.error
import datetime
from pathlib import Path
from typing import Optional

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path("/home/iscjmz/shopify/shopify")
GO_SERVER_DIR = PROJECT_ROOT / "Pokemon" / "server"
BINARY_DEST  = Path("/opt/pokevend/pokevend")
BACKUP_DIR   = Path("/var/backups/pokevend")
LOG_DIR      = Path("/var/log/pokevend")
DEPLOY_LOG   = LOG_DIR / "deployments.log"
ROLLBACK_DIR = Path("/opt/pokevend/rollback")

HEALTH_URL   = "http://localhost:8080/health"
HEALTH_TIMEOUT_SECS = 30   # How long to wait for health check to pass after restart

VALID_ENVS = ["dev", "staging", "prod"]

# ── Logging Setup ─────────────────────────────────────────────────────────────
# TODO: Set up Python's logging module with TWO handlers:
#   1. StreamHandler → formats to: "2026-04-01 14:23:01 [INFO ] message"
#   2. FileHandler → writes same format to DEPLOY_LOG
# HINT: Use logging.Formatter with datefmt
# READ: lessons/02_scripting_mastery.md "Logging — The Professional Way"
# YOUR CODE HERE
logger = logging.getLogger(__name__)  # Keep this line, add setup above it


# ── Custom Exceptions ─────────────────────────────────────────────────────────
class DeploymentError(Exception):
    """Raised when any deployment stage fails unrecoverably."""
    pass

class RollbackError(Exception):
    """Raised when rollback itself fails — this is a critical situation."""
    pass


# ── CLI Arguments ─────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    """
    Create the CLI argument parser.
    
    TODO: Add these arguments:
      --env ENVIRONMENT      (required, choices=VALID_ENVS)
      --version VERSION      (required unless --rollback is set)
      --rollback             (flag — rolls back to previous version)
      --force                (flag — skip confirmation prompts for prod)
      --skip-tests           (flag — skip go test, DANGEROUS but sometimes needed)
      --skip-backup          (flag — skip DB backup, only for non-prod)
      --dry-run              (flag — show what would happen without doing it)
    
    READ: lessons/02_scripting_mastery.md "argparse — Professional CLI Scripts"
    """
    # YOUR CODE HERE
    pass


# ── Stage 0: Preflight Checks ────────────────────────────────────────────────
def preflight(args: argparse.Namespace) -> None:
    """
    Verify all prerequisites before starting the pipeline.
    If ANY check fails, raise DeploymentError immediately.
    
    TODO: Check ALL of the following:
    
    1. Go is installed (go version)
       HINT: subprocess.run(["go", "version"], check=True, capture_output=True)
    
    2. The Go server directory exists
       HINT: if not GO_SERVER_DIR.exists(): raise DeploymentError(...)
    
    3. Docker is running and NexusOS containers are healthy
       HINT: docker ps | grep nexusos-postgres
    
    4. Binary destination parent directory exists (/opt/pokevend)
       If not: log a warning but do NOT fail (provisioner should have created it)
    
    5. Disk space check — need at least 500MB free
       HINT: shutil.disk_usage("/opt").free / (1024**3) > 0.5
    
    6. If env == "prod" and --force is not set, require interactive confirmation
       HINT: input("Deploy to PRODUCTION? Type 'yes' to confirm: ")
    """
    logger.info("Stage 0: Preflight checks")
    # YOUR CODE HERE
    pass


# ── Stage 1: Build ────────────────────────────────────────────────────────────
def build(version: str, dry_run: bool = False) -> Path:
    """
    Compile the Go binary.
    
    Returns the path to the compiled binary (in a temp location).
    
    TODO:
    1. Create a temp build directory: Path(f"/tmp/pokevend_build_{version}")
    
    2. Run go build with these flags:
       - -o <output_path>       (where to put the binary)
       - -ldflags "-X main.Version=<version>"  (embed version in binary)
       - ./...                  (build all packages)
    
    3. Verify the binary was actually created (path.exists())
    
    4. Print the binary size for auditing
    
    IMPORTANT: If go build returns non-zero exit code, raise DeploymentError
    with the stderr output included in the error message.
    
    HINT:
        result = subprocess.run(
            ["go", "build", "-o", str(output_path), 
             "-ldflags", f"-X main.Version={version}", "./..."],
            cwd=str(GO_SERVER_DIR),
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise DeploymentError(f"Build failed:\n{result.stderr}")
    """
    logger.info("Stage 1: Building binary (version=%s)", version)
    # YOUR CODE HERE
    pass


# ── Stage 2: Test ─────────────────────────────────────────────────────────────
def run_tests(dry_run: bool = False) -> None:
    """
    Run the Go test suite.
    
    TODO:
    1. Run: go test ./... -v -timeout 120s
    2. Stream output in real-time (don't capture it — show it as it runs)
       HINT: subprocess.run(...) without capture_output shows output directly
    3. If tests fail, raise DeploymentError with the test output
    
    LEARNING POINT: Why do tests before deploying and NOT after?
    Because deploying a broken binary to production and THEN finding out
    via customer complaints is the worst possible outcome. Tests are your
    safety harness.
    """
    logger.info("Stage 2: Running test suite")
    # YOUR CODE HERE
    pass


# ── Stage 3: Database Backup ──────────────────────────────────────────────────
def backup_database(version: str, dry_run: bool = False) -> Optional[Path]:
    """
    Snapshot the database before deploying. 
    If the deployment breaks the schema, this is how you recover.
    
    TODO:
    1. Create BACKUP_DIR if it doesn't exist: BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    2. Build backup filename: pokevend_pre_deploy_{version}_{timestamp}.sql
    
    3. Run pg_dump inside the Docker container:
       docker exec nexusos-postgres pg_dump -U nexusos nexusos > backup_file.sql
       HINT: You need to redirect stdout to the file using open() + stdout=file
    
    4. Compress with gzip: subprocess.run(["gzip", str(backup_path)])
    
    5. Log the backup size
    
    6. Return the path to the .sql.gz file
    
    CRITICAL: If pg_dump fails, raise DeploymentError BEFORE deploying anything.
    A deployment without a backup is a firing offense.
    """
    logger.info("Stage 3: Creating pre-deployment database backup")
    # YOUR CODE HERE
    pass


# ── Stage 4: Deploy ───────────────────────────────────────────────────────────
def deploy(new_binary: Path, dry_run: bool = False) -> Path:
    """
    Atomically swap the binary. This is the deployment itself.
    
    Returns the path to the backed-up OLD binary (for rollback).
    
    THE ATOMIC SWAP STRATEGY:
        old_binary = /opt/pokevend/pokevend  (currently running)
        new_binary = /tmp/pokevend_build_v1.2.3/pokevend  (just compiled)
        
        Step 1: Copy old → rollback dir (save it in case we need to roll back)
        Step 2: Copy new → /opt/pokevend/pokevend.new  (don't overwrite live binary yet)
        Step 3: mv /opt/pokevend/pokevend.new → /opt/pokevend/pokevend
                (mv is atomic on same filesystem — either it works or it doesn't)
        Step 4: systemctl restart pokevend
    
    WHY NOT just `cp new_binary /opt/pokevend/pokevend`?
    Because if the server crashes mid-copy, you have a corrupt binary.
    The mv (rename) is atomic at the kernel level.
    
    TODO: Implement the above strategy.
    Remember to set correct permissions on the new binary (chmod 755).
    """
    logger.info("Stage 4: Deploying new binary")
    # YOUR CODE HERE
    pass


# ── Stage 5: Verify ───────────────────────────────────────────────────────────
def verify_deployment() -> bool:
    """
    Verify the new deployment is actually healthy.
    
    Returns True if healthy, False if not.
    
    TODO:
    1. Wait for the service to start (it takes a few seconds after systemctl restart)
       Use a retry loop — try every 2 seconds for up to HEALTH_TIMEOUT_SECS
    
    2. Make an HTTP request to HEALTH_URL
       Expected: 200 OK with JSON containing "status": "ok" (or similar)
    
    3. Parse the JSON response and check:
       - database status is "up" or "healthy"
       - redis status is "up" or "healthy"
    
    4. Return True only if ALL checks pass
    
    HINT for retry loop:
        deadline = time.time() + HEALTH_TIMEOUT_SECS
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(HEALTH_URL, timeout=5) as resp:
                    if resp.status == 200:
                        data = json.load(resp)
                        ...
            except Exception as e:
                logger.debug("Health check failed: %s, retrying...", e)
                time.sleep(2)
        return False  # Timed out
    """
    logger.info("Stage 5: Verifying deployment health")
    # YOUR CODE HERE
    pass


# ── Stage 6: Rollback ─────────────────────────────────────────────────────────
def rollback(old_binary: Path, dry_run: bool = False) -> None:
    """
    Restore the previously working binary.
    This runs AUTOMATICALLY if Stage 5 (verify) returns False.
    
    TODO:
    1. Copy old_binary back to BINARY_DEST
    2. Restart the service: systemctl restart pokevend
    3. Run verify_deployment() again to confirm rollback worked
    4. If rollback also fails → raise RollbackError (this is a P0 incident)
    
    The pattern here is critical:
    - Never panic
    - Execute the rollback procedure methodically  
    - Log EVERYTHING (so you can write the incident report later)
    - Escalate (RollbackError) if you can't recover automatically
    """
    logger.critical("Stage 6: ROLLBACK INITIATED — previous deploy failed health check")
    # YOUR CODE HERE
    pass


# ── Deployment Record ─────────────────────────────────────────────────────────
def record_deployment(version: str, env: str, success: bool, details: dict) -> None:
    """
    Write a JSON record of this deployment to a deployments history file.
    This is your audit trail — every deploy, who ran it, when, if it succeeded.
    
    Format:
    {
        "timestamp": "2026-04-01T14:23:01",
        "version": "v1.2.3",
        "environment": "prod",
        "success": true,
        "deployed_by": "iscjmz",
        "duration_seconds": 47,
        "details": { ... }
    }
    
    TODO: Build the record dict and append it as a JSON line to DEPLOY_LOG.json
    (One JSON object per line — this is called JSONL format)
    """
    # YOUR CODE HERE
    pass


# ── Main Pipeline ─────────────────────────────────────────────────────────────
def main() -> None:
    """
    Orchestrate the full deployment pipeline.
    
    TODO: Wire up all stages in order:
    
    1. parse_args()
    2. preflight(args)
    
    If args.rollback:
        - Find the old binary in ROLLBACK_DIR
        - deploy(old_binary)
        - verify_deployment()
        - Exit
    
    Else (normal deploy):
    3. build(args.version, args.dry_run)
    4. run_tests(args.dry_run) — unless args.skip_tests
    5. backup_database(args.version, args.dry_run) — unless args.skip_backup
    6. old_binary = deploy(new_binary, args.dry_run)
    7. if not verify_deployment():
           rollback(old_binary)
           exit with non-zero status
    8. record_deployment(...)
    9. Print success banner
    
    TIME IT: Use time.time() at start and end to calculate total pipeline duration.
    """
    start_time = time.time()
    # YOUR CODE HERE
    pass


if __name__ == "__main__":
    main()
