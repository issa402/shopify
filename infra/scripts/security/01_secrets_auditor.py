#!/usr/bin/env python3
"""
SCRIPT: 01_secrets_auditor.py
MODULE: Week 4 — Cybersecurity
READ FIRST: lessons/04_cybersecurity_mastery.md § PART 2 (Secrets Management)

WHAT THIS SCRIPT DOES (when complete):
    Scans the ENTIRE NexusOS repository for accidentally exposed credentials,
    API keys, passwords, and other secrets. This is a professional secrets
    audit tool. Run it before every code review and before every deployment.

    If you find a secret in your repo history — it is ALREADY compromised.
    The attacker bots that scan GitHub find secrets within minutes of pushing.
    This script runs LOCALLY to catch them BEFORE you push.

KEY CONCEPTS YOU WILL MASTER:
    - Regex for pattern matching (the attacker's tool repurposed for defense)
    - Git history scanning (secrets in old commits are still dangerous)
    - Risk scoring — not all findings are equal
    - Entropy analysis — high-entropy strings are likely secrets

HOW TO RUN:
    python3 01_secrets_auditor.py                    # Scan current directory
    python3 01_secrets_auditor.py --path /some/dir   # Scan specific path
    python3 01_secrets_auditor.py --git-history      # Also scan git commits
    python3 01_secrets_auditor.py --report json      # JSON output for CI/CD

WHEN YOU KNOW YOU'RE DONE:
    Create a test_secrets.py file with fake hardcoded secrets.
    Run the auditor — it must detect ALL of them.
    Delete test_secrets.py. Re-run — clean report.
"""

import re
import os
import sys
import json
import math
import argparse
import subprocess
from pathlib import Path
from typing import NamedTuple
from datetime import datetime

# ── Secret Detection Patterns ────────────────────────────────────────────────
# Each pattern has: name, regex, severity (1-10), description
# Severity 10 = immediate breach risk. Severity 1 = low risk.
#
# LEARNING POINT: These are the EXACT patterns that GitHub's secret scanning
# and tools like TruffleHog, GitGuardian use.

SECRET_PATTERNS = [
    {
        "name": "AWS Access Key",
        "pattern": r"AKIA[0-9A-Z]{16}",
        "severity": 10,
        "description": "AWS Access Key ID — can be used to access your entire AWS account"
    },
    {
        "name": "AWS Secret Key",
        "pattern": r"(?i)aws.{0,20}secret.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]",
        "severity": 10,
        "description": "AWS Secret Access Key"
    },
    {
        "name": "PostgreSQL Connection String",
        "pattern": r"postgres(?:ql)?://[^:]+:[^@]+@[^/\s]+/\w+",
        "severity": 9,
        "description": "Database URL with embedded credentials"
    },
    {
        "name": "JWT Secret Hardcoded",
        "pattern": r"(?i)jwt.{0,10}secret.{0,10}[=:]['\"][^'\"]{8,}['\"]",
        "severity": 8,
        "description": "JWT signing secret — allows forging any token"
    },
    {
        "name": "Private Key",
        "pattern": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "severity": 10,
        "description": "Private cryptographic key — never commit these"
    },
    {
        "name": "Generic Password Assignment",
        "pattern": r"(?i)password\s*[=:]\s*['\"][^'\"]{4,}['\"]",
        "severity": 6,
        "description": "Hardcoded password — may be real or test value"
    },
    {
        "name": "OpenAI API Key",
        "pattern": r"sk-[a-zA-Z0-9]{48}",
        "severity": 9,
        "description": "OpenAI API key — charges to your account"
    },
    {
        "name": "Stripe Secret Key",
        "pattern": r"sk_(?:live|test)_[0-9a-zA-Z]{24}",
        "severity": 10,
        "description": "Stripe secret key — financial access"
    },
    {
        "name": "Generic API Key",
        "pattern": r"(?i)api[_-]?key\s*[=:]\s*['\"][^'\"]{8,}['\"]",
        "severity": 5,
        "description": "Generic API key — severity depends on the service"
    },
    {
        "name": "Environment Variable with Secret",
        "pattern": r"(?i)(?:secret|password|token|key)\s*=\s*(?![<$])[^\s'\"#]{8,}",
        "severity": 4,
        "description": "Unquoted secret value in config or shell script"
    },
]

# File extensions to scan
SCAN_EXTENSIONS = {
    ".go", ".py", ".js", ".ts", ".json", ".yaml", ".yml",
    ".env", ".sh", ".bash", ".toml", ".conf", ".config",
    ".properties", ".ini", ".md", ".txt"
}

# Files/directories to always skip
SKIP_PATHS = {
    ".git", "node_modules", "__pycache__", ".venv", "vendor",
    "*.min.js", "go.sum",  # go.sum has hashes that look like secrets
}


# ── Data Structures ───────────────────────────────────────────────────────────
class Finding(NamedTuple):
    file_path:   str
    line_number: int
    line_content: str    # Redacted version (never print full secret)
    pattern_name: str
    severity:    int
    in_git_history: bool = False
    commit_hash: str = ""


# ── Scanning Functions ────────────────────────────────────────────────────────

def should_skip(path: Path) -> bool:
    """
    Determine if a file or directory should be skipped.
    
    TODO: Return True if:
    1. Any part of the path is in SKIP_PATHS
    2. The path is a symlink (avoid following symlinks)
    3. The file extension is not in SCAN_EXTENSIONS (for files)
    4. The file is larger than 1MB (likely binary data, not source)
    
    HINT: Use path.suffix for extension and path.stat().st_size for size
    """
    # YOUR CODE HERE
    pass


def redact_line(line: str, pattern: str) -> str:
    """
    Replace the matched secret value with [REDACTED] in the output.
    
    We NEVER print the actual secret value — even in the report.
    The report goes into logs, which might be stored somewhere less secure.
    
    TODO: Use re.sub to replace the matched portion with "[REDACTED]"
    HINT: re.sub(pattern, "[REDACTED]", line)
    """
    # YOUR CODE HERE
    pass


def calculate_entropy(text: str) -> float:
    """
    Calculate the Shannon entropy of a string.
    
    High entropy = random-looking = likely a secret (key, token, hash).
    Low entropy = human-readable text = likely not a secret.
    
    Entropy formula: H = -sum(p(x) * log2(p(x))) for each unique character
    
    Real API keys have entropy > 4.5
    English text has entropy ~ 4.0
    Repeated characters have entropy ~ 0
    
    TODO: Implement the Shannon entropy calculation
    HINT:
        if not text: return 0
        char_counts = {}
        for c in text:
            char_counts[c] = char_counts.get(c, 0) + 1
        entropy = 0
        for count in char_counts.values():
            p = count / len(text)
            entropy -= p * math.log2(p)
        return entropy
    """
    # YOUR CODE HERE
    pass


def scan_file(filepath: Path) -> list[Finding]:
    """
    Scan a single file for all secret patterns.
    
    TODO:
    1. Open the file and read it line by line
    2. For each line, test against EVERY pattern in SECRET_PATTERNS
    3. If a pattern matches, create a Finding with the redacted line
    4. Also run entropy check — if a string in the line has entropy > 4.8,
       flag it as a potential secret even if no pattern matched
    5. Return list of all findings
    
    IMPORTANT: Handle encoding errors gracefully (binary files, etc.)
    HINT: open(filepath, 'r', errors='ignore')
    """
    # YOUR CODE HERE
    pass


def scan_directory(root: Path) -> list[Finding]:
    """
    Recursively scan all files in a directory.
    
    TODO:
    1. Walk the directory tree with Path.rglob('*')
    2. For each file, check should_skip()
    3. If not skipping, call scan_file()
    4. Collect and return all findings
    
    Show progress as you scan (print dots or file count)
    """
    # YOUR CODE HERE
    pass


def scan_git_history(repo_path: Path) -> list[Finding]:
    """
    Scan the git commit history for secrets.
    
    WHY THIS IS CRITICAL:
    If you commit a secret and then "delete" it in the next commit,
    the secret is STILL in git history. Anyone who clones your repo
    can see it with: git log -p
    
    TODO:
    1. Run: git log --all -p --no-merges --since="90 days ago"
       This outputs the full patch (diff) for every commit in the last 90 days
    
    2. Parse the output — track current commit hash (lines starting with "commit ")
    
    3. For "+" lines (additions), scan with SECRET_PATTERNS
    
    4. Return findings with in_git_history=True and the commit_hash
    
    LEARNING: This is exactly what TruffleHog and git-secrets do.
    """
    # YOUR CODE HERE
    pass


# ── Risk Scoring ──────────────────────────────────────────────────────────────

def calculate_risk_score(findings: list[Finding]) -> int:
    """
    Calculate an overall risk score 0-100.
    
    TODO: 
    - Start at 0
    - Add severity * weight for each finding
    - Findings in git history are 2x weight (can't be un-exposed)
    - Cap at 100
    
    Score interpretation:
    0     = Clean
    1-25  = Low risk (likely false positives or test values)
    26-50 = Medium risk (investigate)
    51-75 = High risk (immediate action needed)
    76-100= Critical (treat all credentials as compromised NOW)
    """
    # YOUR CODE HERE
    pass


# ── Report Generation ─────────────────────────────────────────────────────────

def print_text_report(findings: list[Finding], risk_score: int) -> None:
    """
    TODO: Print a professional security report:
    
    ╔══════════════════════════════════════════╗
    ║     NEXUSOS SECRETS AUDIT REPORT        ║
    ╚══════════════════════════════════════════╝
    Scanned: 2026-04-01T14:23:01
    
    RISK SCORE: 35/100 (MEDIUM)
    
    CRITICAL FINDINGS (Severity 8-10):
    ────────────────────────────────────
    [CRITICAL] AWS Access Key
    File: services/ai/config.py:43
    Line: api_key = "[REDACTED]"
    Action: Rotate this key NOW. Assume it's already been used by attackers.
    
    LOW FINDINGS (Severity 1-4):
    ────────────────────────────────────
    ...
    
    RECOMMENDATIONS:
    ────────────────────────────────────
    • Use environment variables or a secrets manager (AWS Secrets Manager, Vault)
    • Add pre-commit hooks to prevent future secret commits
    • Rotate all credentials found in git history
    """
    # YOUR CODE HERE
    pass


def parse_args() -> argparse.Namespace:
    """
    TODO: Add arguments:
      --path PATH         (default: current directory)
      --git-history       (also scan git commits)
      --report FORMAT     (choices: ["text", "json"], default: "text")
      --severity-min INT  (only report findings >= this severity, default: 1)
      --output FILE       (write report to file instead of stdout)
    """
    # YOUR CODE HERE
    pass


def main() -> None:
    """
    TODO:
    1. Parse args
    2. Scan directory
    3. Optionally scan git history
    4. Calculate risk score
    5. Generate report
    6. Exit with code 1 if any findings with severity >= 7
       (Makes this useful in CI/CD pipelines — fails the build if secrets found)
    """
    # YOUR CODE HERE
    pass


if __name__ == "__main__":
    main()
