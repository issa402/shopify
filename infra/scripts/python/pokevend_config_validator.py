#!/usr/bin/env python3
"""
SCRIPT: pokevend_config_validator.py
MODULE: Python + Security — Week 2/4
TIES TO THESE REAL PROJECT FILES:
    config/config.go           — ALL env vars and their validation rules
    config/config.go line 125  — Validate() method (we replicate this in Python)
    docker-compose.yml         — env var patterns for each container

WHAT IT DOES:
    Validates that your .env file (or environment variables) meet ALL the
    requirements defined in config/config.go BEFORE you start the server.

    config.go Validate() checks:
      ✓ PORT is 1-65535
      ✓ JWT_SECRET != "change-me-in-production" (in prod)
      ✓ JWT_SECRET length >= 32 (in prod)
      ✓ ENCRYPTION_KEY != all zeros (in prod)

    This script does ALL of that PLUS:
      ✓ Checks all required vars are present
      ✓ Validates DB connection string format
      ✓ Validates ENCRYPTION_KEY is exactly 64 hex chars
      ✓ Checks REDIS_URL format (host:port)
      ✓ Warns about default values (which are in your public GitHub repo)
      ✓ Generates a safe .env from scratch with proper random values
      ✓ Scans config.go to find ANY new env vars that were added

HOW TO RUN:
    python3 infra/scripts/python/pokevend_config_validator.py
    python3 infra/scripts/python/pokevend_config_validator.py --env .env
    python3 infra/scripts/python/pokevend_config_validator.py --generate  (create new .env)
    python3 infra/scripts/python/pokevend_config_validator.py --diff       (compare .env vs config.go)

WHAT YOU LEARN:
    - re module for regex-based validation
    - os.getenv / dotenv parsing
    - subprocess to read your own source code
    - generating cryptographically secure values (secrets module)
    - Custom exception hierarchy
    - Severity-graded findings (ERROR vs WARNING vs INFO)
"""

import re
import os
import sys
import json
import secrets
import argparse
import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

# =============================================================================
# PROJECT PATHS
# =============================================================================
PROJECT_ROOT = Path("/home/iscjmz/shopify/shopify")
GO_SERVER    = PROJECT_ROOT / "Pokemon" / "server"
CONFIG_GO    = GO_SERVER / "config" / "config.go"

# =============================================================================
# REAL RULES FROM config/config.go
# =============================================================================

# config.go line 136: "change-me-in-production" is the insecure default
INSECURE_JWT_DEFAULT = "change-me-in-production"

# config.go line 139: 64 zeros is the insecure encryption key default
INSECURE_ENC_DEFAULT = "0" * 64

# config.go line 141: JWT must be >= 32 chars in production
MIN_JWT_LENGTH = 32

# config.go line 128: PORT must be 1-65535
MIN_PORT = 1
MAX_PORT = 65535

# All env vars that config.go reads (from getEnv/getEnvInt calls)
# These were extracted by: grep 'getEnv' config/config.go
KNOWN_ENV_VARS = {
    "PORT":                      {"type": "int",    "default": "3001",        "required": False},
    "NODE_ENV":                  {"type": "string", "default": "development",  "required": False},
    "CLIENT_URL":                {"type": "string", "default": "http://localhost:5173", "required": False},
    "POSTGRES_HOST":             {"type": "string", "default": "localhost",   "required": False},
    "POSTGRES_PORT":             {"type": "int",    "default": "5432",        "required": False},
    "POSTGRES_DB":               {"type": "string", "default": "pokemontool", "required": False},
    "POSTGRES_USER":             {"type": "string", "default": "pokemontool_user", "required": False},
    "POSTGRES_PASSWORD":         {"type": "string", "default": "pokemontool_pass", "required": True},
    "REDIS_URL":                 {"type": "string", "default": "redis:6379",  "required": False},
    "RABBITMQ_URL":              {"type": "string", "default": "amqp://guest:guest@rabbitmq:5672", "required": False},
    "JWT_SECRET":                {"type": "string", "default": INSECURE_JWT_DEFAULT, "required": True},
    "ENCRYPTION_KEY":            {"type": "string", "default": INSECURE_ENC_DEFAULT, "required": True},
    "SCRAPING_INTERVAL_MINUTES": {"type": "int",    "default": "30",          "required": False},
}

# =============================================================================
# FINDINGS — Severity-graded results
# =============================================================================

@dataclass
class Finding:
    """
    A validation finding. Matches how config.go's Validate() reports errors.

    Severity:
      ERROR   = server WILL fail or is insecure (matches Validate() returns)
      WARNING = server WILL work but is using insecure defaults
      INFO    = suggestion for improvement
    """
    severity: str    # "ERROR", "WARNING", "INFO"
    var_name: str    # which env var
    message:  str    # what's wrong or notable
    fix:      str    # how to fix it


@dataclass
class ValidationResult:
    """Container for all findings from a validation run."""
    findings: list[Finding] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)

    def add(self, severity: str, var: str, message: str, fix: str = "") -> None:
        self.findings.append(Finding(severity, var, message, fix))

    def errors(self)   -> list[Finding]: return [f for f in self.findings if f.severity == "ERROR"]
    def warnings(self) -> list[Finding]: return [f for f in self.findings if f.severity == "WARNING"]
    def infos(self)    -> list[Finding]: return [f for f in self.findings if f.severity == "INFO"]

    def has_errors(self) -> bool: return len(self.errors()) > 0


# =============================================================================
# ENV FILE PARSER
# =============================================================================

def load_env_file(path: Path) -> dict[str, str]:
    """
    Parse a .env file (KEY=VALUE format) into a dict.
    Handles: comments (#), quoted values, empty lines.

    TODO:
    1. Open path with Path.read_text()
    2. For each line:
       a. Strip whitespace
       b. Skip empty lines and lines starting with #
       c. Split on first = only (partition = is safer than split)
          "KEY=value=with=equals" should give key="KEY", value="value=with=equals"
       d. Strip quotes from value ("value" → value, 'value' → value)
    3. Return dict of {KEY: value}

    HINT:
        result = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, _, value = line.partition('=')
            key   = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                result[key] = value
        return result
    """
    if not path.exists():
        return {}
    # YOUR CODE HERE
    return {}  # placeholder


def load_env_from_environment() -> dict[str, str]:
    """
    Read all KNOWN_ENV_VARS from the actual OS environment.
    Returns only the vars we care about (not the entire environment).

    TODO: For each key in KNOWN_ENV_VARS, get os.getenv(key) and include
    only if it's not None.
    """
    # YOUR CODE HERE
    return {}  # placeholder


# =============================================================================
# VALIDATION RULES
# These mirror config.go Validate() plus extra checks
# =============================================================================

def validate_port(result: ValidationResult, val: str) -> None:
    """
    Mirrors config.go lines 127-130:
        port, err := strconv.Atoi(c.Port)
        if err != nil || port < 1 || port > 65535 {...}

    TODO:
    1. Try int(val) — if ValueError: add ERROR "PORT must be a number"
    2. If out of range: add ERROR "PORT must be 1-65535"
    3. If in well-known system range (< 1024): add WARNING "Ports < 1024 require root"
    4. If == 3001: add INFO "Using default development port"
    """
    # YOUR CODE HERE
    pass


def validate_jwt_secret(result: ValidationResult, val: str, env: str) -> None:
    """
    Mirrors config.go lines 135-143:
        if c.JWTSecret == "change-me-in-production" → ERROR
        if len(c.JWTSecret) < 32 → ERROR

    TODO:
    1. If val == INSECURE_JWT_DEFAULT:
       - In production (env=="production"): add ERROR (blocks startup)
       - In development: add WARNING (should change before prod)
    2. If len(val) < MIN_JWT_LENGTH: add ERROR with fix showing openssl command
    3. If not high entropy (all lowercase, simple pattern): add WARNING
    4. If looks good: add INFO

    For step 3, check entropy: if all chars are letters and the string looks
    like a word (not random hex), it's probably too guessable.
    """
    # YOUR CODE HERE
    pass


def validate_encryption_key(result: ValidationResult, val: str, env: str) -> None:
    """
    Mirrors config.go lines 138-140:
        if c.EncryptionKey == "0000...0000" → ERROR

    ENCRYPTION_KEY must be exactly 64 hex characters (32 bytes = AES-256).

    TODO:
    1. If val == INSECURE_ENC_DEFAULT: add ERROR
    2. If len(val) != 64: add ERROR "Must be exactly 64 hex chars (got N)"
    3. If not all hex chars: add ERROR "Must be hexadecimal only (0-9, a-f)"
       HINT: re.match(r'^[0-9a-fA-F]{64}$', val)
    4. If correct: add INFO "Encryption key looks good"
    """
    # YOUR CODE HERE
    pass


def validate_postgres_connection(result: ValidationResult, env_vars: dict) -> None:
    """
    Validate all PostgreSQL-related config as a group.

    TODO:
    1. Check POSTGRES_HOST: if "localhost" in prod → WARNING (should use RDS endpoint)
    2. Check POSTGRES_PORT: must be 1-65535
    3. Check POSTGRES_PASSWORD: if == "pokemontool_pass" (the public default) → ERROR
       This password is in your PUBLIC repo so every hacker knows it
    4. Check POSTGRES_DB: must not be empty
    5. BONUS: Try to actually ping the DB:
       docker exec nexusos-postgres pg_isready -U pokemontool_user -d pokemontool
       Add INFO if successful, WARNING if failed (can't reach DB)
    """
    # YOUR CODE HERE
    pass


def validate_redis_url(result: ValidationResult, val: str) -> None:
    """
    REDIS_URL format: "host:port" (e.g. "redis:6379" or "localhost:6379")
    config.go line 81: getEnv("REDIS_URL", "redis:6379")

    TODO:
    1. Must contain exactly one ":"
    2. Extract port and validate it's numeric and in range
    3. If host is "redis" — this is the Docker container name
       It only works INSIDE Docker networking. In dev (outside Docker), use "localhost"
       Add an INFO explaining this.
    """
    # YOUR CODE HERE
    pass


# =============================================================================
# DRIFT DETECTOR
# Compare .env file with what config.go expects
# =============================================================================

def detect_drift_from_source(env_vars: dict[str, str]) -> ValidationResult:
    """
    Read config/config.go source code and find any getEnv() calls
    that we don't know about in KNOWN_ENV_VARS.

    This catches: a developer added a new env var to config.go
    but didn't document it in KNOWN_ENV_VARS or put it in .env

    TODO:
    1. Read CONFIG_GO with Path.read_text()
    2. Use re.findall(r'getEnv(?:Int)?\("([^"]+)"', content) to extract all var names
    3. For each found var not in KNOWN_ENV_VARS: add WARNING "Unknown env var found in config.go"
    4. For each var in KNOWN_ENV_VARS not found in config.go: add INFO "Env var in validator but not in config.go (may be removed)"

    HINT:
        content = CONFIG_GO.read_text()
        found_vars = set(re.findall(r'getEnv(?:Int)?\("([^"]+)"', content))
        known_vars = set(KNOWN_ENV_VARS.keys())
        for v in found_vars - known_vars:
            result.add("WARNING", v, "Found in config.go but not in validator — add to KNOWN_ENV_VARS")
    """
    result = ValidationResult()
    # YOUR CODE HERE
    return result


# =============================================================================
# .ENV GENERATOR
# =============================================================================

def generate_secure_env(env: str = "development") -> str:
    """
    Generate a secure .env file using cryptographically random values
    for secrets, and correct defaults for everything else.

    config.go line 89: JWT_SECRET — use secrets.token_hex(32) = 64 hex chars
    config.go line 90: ENCRYPTION_KEY — must be exactly 64 hex chars

    TODO:
    1. Use secrets.token_hex(32) for JWT_SECRET (64 hex chars → very secure)
    2. Use secrets.token_hex(32) for ENCRYPTION_KEY (64 hex chars = 32 bytes AES-256)
    3. Build the .env content as a string with all KNOWN_ENV_VARS
    4. For vars with secure defaults: use the default
    5. For JWT_SECRET and ENCRYPTION_KEY: use the generated values

    RETURN FORMAT:
    # Pokevend .env — Generated 2026-04-01T14:23:01
    # Environment: development
    # NEVER commit this file to git!

    PORT=3001
    NODE_ENV=development
    # ... etc

    # SECURITY — Change these in production!
    JWT_SECRET=<64-char-hex>
    ENCRYPTION_KEY=<64-char-hex>
    POSTGRES_PASSWORD=<random-strong-password>
    """
    jwt_secret      = secrets.token_hex(32)       # 64 hex chars
    encryption_key  = secrets.token_hex(32)       # 64 hex chars
    db_password     = secrets.token_urlsafe(24)   # strong random password

    # YOUR CODE HERE
    # Build and return the .env string
    return f"""# Pokevend .env — Generated {datetime.now().isoformat()}
# Environment: {env}
# NEVER commit this file to git!
# Add .env to your .gitignore NOW if not already there.

PORT=3001
NODE_ENV={env}
CLIENT_URL=http://localhost:5173

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=pokemontool
POSTGRES_USER=pokemontool_user
POSTGRES_PASSWORD={db_password}

REDIS_URL=localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672

# SECURITY — These were generated with cryptographically secure randomness
# They match config.go requirements: JWT >= 32 chars, ENCRYPTION_KEY = 64 hex chars
JWT_SECRET={jwt_secret}
ENCRYPTION_KEY={encryption_key}

SCRAPING_INTERVAL_MINUTES=30
"""


# =============================================================================
# REPORT PRINTER
# =============================================================================

def print_report(result: ValidationResult) -> None:
    """
    TODO: Print a formatted validation report like:

    ╔══════════════════════════════════════════════════════╗
    ║      POKEVEND CONFIG VALIDATION REPORT              ║
    ╚══════════════════════════════════════════════════════╝

    ❌ ERRORS (must fix before production):
    ──────────────────────────────────────
    JWT_SECRET: Still using default "change-me-in-production"
    Fix: export JWT_SECRET=$(openssl rand -hex 32)

    ⚠ WARNINGS (should fix):
    ...

    ℹ INFOS:
    ...

    OVERALL: PASS (0 errors, 2 warnings) or FAIL (3 errors)

    Color: errors in red, warnings in yellow, info in blue
    """
    # YOUR CODE HERE
    print("Report not implemented yet — implement print_report()")
    for f in result.findings:
        print(f"  [{f.severity}] {f.var_name}: {f.message}")
        if f.fix:
            print(f"    Fix: {f.fix}")


# =============================================================================
# CLI
# =============================================================================

def parse_args() -> argparse.Namespace:
    """
    TODO: Create argument parser with:
      --env PATH       (.env file to validate, default: PROJECT_ROOT/.env)
      --generate       (flag: generate a new secure .env and print it)
      --diff           (flag: compare .env against config.go source)
      --output PATH    (write report to this file as JSON)
    """
    # YOUR CODE HERE
    class FakeArgs:
        env = str(PROJECT_ROOT / ".env")
        generate = False
        diff = False
        output = None
    return FakeArgs()


def main() -> None:
    args = parse_args()

    if args.generate:
        env_type = "production" if "prod" in str(args.env) else "development"
        print(generate_secure_env(env_type))
        print("\n# Save this with: python3 pokevend_config_validator.py --generate > .env", file=sys.stderr)
        return

    # Load env vars from file or environment
    env_file = Path(args.env)
    if env_file.exists():
        env_vars = load_env_file(env_file)
        print(f"Validating: {env_file}")
    else:
        env_vars = load_env_from_environment()
        print(f"No .env file found at {env_file}, reading from environment")

    # Merge with defaults (anything not set uses config.go defaults)
    for key, info in KNOWN_ENV_VARS.items():
        if key not in env_vars:
            env_vars[key] = info["default"]

    result = ValidationResult(env_vars=env_vars)
    current_env = env_vars.get("NODE_ENV", "development")

    # Run all validations
    validate_port(result, env_vars.get("PORT", "3001"))
    validate_jwt_secret(result, env_vars.get("JWT_SECRET", INSECURE_JWT_DEFAULT), current_env)
    validate_encryption_key(result, env_vars.get("ENCRYPTION_KEY", INSECURE_ENC_DEFAULT), current_env)
    validate_postgres_connection(result, env_vars)
    validate_redis_url(result, env_vars.get("REDIS_URL", "redis:6379"))

    if args.diff:
        drift = detect_drift_from_source(env_vars)
        result.findings.extend(drift.findings)

    print_report(result)

    # Exit with error code if any errors found
    # This makes it work in CI/CD: if config is invalid, pipeline fails
    sys.exit(1 if result.has_errors() else 0)


if __name__ == "__main__":
    main()
