#!/usr/bin/env python3
"""Read-only Odoo infrastructure doctor for local development.

The goal is to build infrastructure intuition before changing application code:
files -> config -> runtime -> network -> health -> risk.
"""

from __future__ import annotations

import argparse
import re
import shutil
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str
    action: str = ""


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "docker-compose.odoo.yml"
ENV_EXAMPLE = REPO_ROOT / "odoo" / ".env.example"
ENV_FILE = REPO_ROOT / "odoo" / ".env"
ODOO_CONF = REPO_ROOT / "odoo" / "config" / "odoo.conf"
ADDON_ROOT = REPO_ROOT / "odoo" / "custom_addons" / "pokecard_storefront"
BRIDGE_NETWORK = "pokemon-odoo-bridge"

REQUIRED_FILES = [
    COMPOSE_FILE,
    ENV_EXAMPLE,
    ODOO_CONF,
    ADDON_ROOT / "__manifest__.py",
    ADDON_ROOT / "__init__.py",
    ADDON_ROOT / "controllers" / "__init__.py",
    ADDON_ROOT / "controllers" / "main.py",
    ADDON_ROOT / "models" / "__init__.py",
    ADDON_ROOT / "models" / "product_template.py",
    ADDON_ROOT / "views" / "website_pages.xml",
    ADDON_ROOT / "views" / "product_template_views.xml",
    ADDON_ROOT / "static" / "src" / "css" / "pokecard_storefront.css",
]

DEV_DEFAULT_WARNINGS = {
    "ODOO_POSTGRES_PASSWORD": "odoo_dev_password",
    "admin_passwd": "admin_dev_change_me",
    "db_password": "odoo_dev_password",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only Odoo infrastructure doctor.")
    parser.add_argument("--format", choices=("text", "markdown"), default="text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on WARN as well as FAIL. Useful for CI later.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def run_command(command: list[str], timeout: int = 15) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return 127, "", f"command not found: {command[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"command timed out: {' '.join(command)}"
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_required_files() -> list[Check]:
    checks = []
    for path in REQUIRED_FILES:
        relative = path.relative_to(REPO_ROOT)
        if path.is_file():
            checks.append(Check(str(relative), "PASS", "required file exists"))
        else:
            checks.append(Check(str(relative), "FAIL", "required file missing", "restore or create this file"))
    return checks


def check_env() -> list[Check]:
    checks = []
    env_values = load_env(ENV_FILE if ENV_FILE.exists() else ENV_EXAMPLE)
    source = ENV_FILE if ENV_FILE.exists() else ENV_EXAMPLE
    checks.append(Check("Odoo env source", "PASS", str(source.relative_to(REPO_ROOT))))

    for key in ["ODOO_HTTP_PORT", "ODOO_LONGPOLL_PORT", "ODOO_POSTGRES_PORT", "ODOO_POSTGRES_USER", "ODOO_POSTGRES_PASSWORD"]:
        if key in env_values:
            checks.append(Check(f"env {key}", "PASS", "set"))
        else:
            checks.append(Check(f"env {key}", "WARN", "not set", "add it to odoo/.env or .env.example"))

    for key, unsafe_value in DEV_DEFAULT_WARNINGS.items():
        if env_values.get(key) == unsafe_value:
            checks.append(Check(f"dev default {key}", "WARN", "development default is still present", "change before shared/public deployment"))

    return checks


def check_odoo_conf() -> list[Check]:
    checks = []
    config = read_text(ODOO_CONF)
    if not config:
        return [Check("odoo.conf", "FAIL", "missing or unreadable", "restore odoo/config/odoo.conf")]

    expected_pairs = {
        "db_host": "odoo-db",
        "db_port": "5432",
        "addons_path": "/mnt/extra-addons",
    }
    for key, expected in expected_pairs.items():
        pattern = rf"^\s*{re.escape(key)}\s*=\s*(.+)$"
        match = re.search(pattern, config, flags=re.MULTILINE)
        if not match:
            checks.append(Check(f"odoo.conf {key}", "WARN", "not configured", "confirm Odoo can find DB/addons"))
            continue
        value = match.group(1).strip()
        status = "PASS" if expected in value else "WARN"
        checks.append(Check(f"odoo.conf {key}", status, value, "confirm this is intentional" if status == "WARN" else ""))

    for key, unsafe_value in DEV_DEFAULT_WARNINGS.items():
        pattern = rf"^\s*{re.escape(key)}\s*=\s*{re.escape(unsafe_value)}\s*$"
        if re.search(pattern, config, flags=re.MULTILINE):
            checks.append(Check(f"dev default {key}", "WARN", "development default is still present", "change before shared/public deployment"))

    return checks


def check_compose_static() -> list[Check]:
    compose = read_text(COMPOSE_FILE)
    checks = []
    if not compose:
        return [Check("docker-compose.odoo.yml", "FAIL", "missing or unreadable")]

    expected_snippets = {
        "odoo-db service": "odoo-db:",
        "odoo service": "odoo:",
        "localhost Odoo port": '127.0.0.1:${ODOO_HTTP_PORT:-8069}:8069',
        "localhost DB port": '127.0.0.1:${ODOO_POSTGRES_PORT:-55432}:5432',
        "external bridge network": "external: true",
        "Pokemon bridge name": BRIDGE_NETWORK,
        "custom addons mount": "./odoo/custom_addons:/mnt/extra-addons:ro",
    }
    for name, snippet in expected_snippets.items():
        if snippet in compose:
            checks.append(Check(name, "PASS", "compose contains expected setting"))
        else:
            checks.append(Check(name, "WARN", "expected setting not found", "review docker-compose.odoo.yml"))
    return checks


def check_compose_command() -> list[Check]:
    if not shutil.which("docker"):
        return [Check("docker compose config", "WARN", "docker not found", "install/start Docker to validate runtime config")]

    env_file = ENV_FILE if ENV_FILE.exists() else ENV_EXAMPLE
    code, _stdout, stderr = run_command([
        "docker",
        "compose",
        "-f",
        str(COMPOSE_FILE),
        "--env-file",
        str(env_file),
        "config",
        "--quiet",
    ])
    if code == 0:
        return [Check("docker compose config", "PASS", "compose renders successfully")]
    return [Check("docker compose config", "FAIL", stderr or "compose config failed", "fix compose/env syntax")]


def check_docker_network() -> list[Check]:
    if not shutil.which("docker"):
        return [Check("Docker network", "WARN", "docker not found", "cannot inspect external bridge network")]
    code, stdout, stderr = run_command(["docker", "network", "inspect", BRIDGE_NETWORK])
    if code == 0 and stdout:
        return [Check("Docker network pokemon-odoo-bridge", "PASS", "external bridge network exists")]
    return [
        Check(
            "Docker network pokemon-odoo-bridge",
            "WARN",
            stderr or "network not found",
            f"create it with: docker network create {BRIDGE_NETWORK}",
        )
    ]


def check_live_ports() -> list[Check]:
    env = load_env(ENV_FILE if ENV_FILE.exists() else ENV_EXAMPLE)
    http_port = int(env.get("ODOO_HTTP_PORT", "8069"))
    db_port = int(env.get("ODOO_POSTGRES_PORT", "55432"))
    checks = []
    for name, port, action in [
        ("Odoo HTTP", http_port, "start with docker compose -f docker-compose.odoo.yml --env-file odoo/.env up -d"),
        ("Odoo Postgres", db_port, "wait for odoo-db health or start the Odoo stack"),
    ]:
        if port_open("127.0.0.1", port):
            checks.append(Check(f"live port {name}", "PASS", f"127.0.0.1:{port} is reachable"))
        else:
            checks.append(Check(f"live port {name}", "WARN", f"127.0.0.1:{port} is not reachable", action))
    return checks


def build_checks() -> list[Check]:
    checks: list[Check] = []
    checks.extend(check_required_files())
    checks.extend(check_env())
    checks.extend(check_odoo_conf())
    checks.extend(check_compose_static())
    checks.extend(check_compose_command())
    checks.extend(check_docker_network())
    checks.extend(check_live_ports())
    return checks


def print_text(checks: list[Check]) -> None:
    print("Odoo Infrastructure Doctor")
    print(f"Repo: {REPO_ROOT}")
    print()
    for check in checks:
        line = f"[{check.status}] {check.name}: {check.detail}"
        if check.action:
            line += f" | next: {check.action}"
        print(line)


def print_markdown(checks: list[Check]) -> None:
    print("# Odoo Infrastructure Doctor\n")
    print(f"Repo: `{REPO_ROOT}`\n")
    print("| Status | Check | Detail | Next action |")
    print("|---|---|---|---|")
    for check in checks:
        print(f"| {check.status} | `{check.name}` | {check.detail} | {check.action} |")


def exit_code(checks: list[Check], strict: bool) -> int:
    statuses = {check.status for check in checks}
    if "FAIL" in statuses:
        return 1
    if strict and "WARN" in statuses:
        return 2
    return 0


def main() -> int:
    args = parse_args()
    checks = build_checks()
    if args.format == "markdown":
        print_markdown(checks)
    else:
        print_text(checks)
    return exit_code(checks, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
