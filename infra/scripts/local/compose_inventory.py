#!/usr/bin/env python3
"""Guided Docker Compose inventory script.

WHY THIS SCRIPT IS THE RIGHT NEXT CODING TASK
============================================
You already have Docker Compose, Odoo, PokemonTool, infra docs, and some scripts.
The next useful thing is not another vague architecture note. The next useful
thing is a script that turns compose files into operational evidence.

This script answers:

    What services exist?
    What ports are exposed?
    What services depend on other services?
    What data is persisted in volumes?
    What services have healthchecks?
    What networks are used?
    What risks are visible before deploying anywhere?

HOW TO PLAN ANY FUTURE INFRA SCRIPT
===================================
Use this exact thinking pattern before coding any AWS/security/observability/IaC
script:

1. Question
   What operational question am I answering?

2. Source Of Truth
   Which file, API, command, or system has the truth?

3. Read-Only Method
   How can I inspect safely without changing state?

4. Output Shape
   Should the output be text, Markdown, JSON, or all of those?

5. Risk Lens
   What could be exposed, fragile, missing, stale, expensive, or unowned?

6. Next Action
   What should a human do after reading the report?

For this script:

    Question: What does the local runtime expose and depend on?
    Source: docker-compose.yml, docker-compose.odoo.yml, Pokemon/docker-compose.yml
    Method: parse YAML read-only
    Output: Markdown or JSON
    Risk: public ports, missing healthchecks, persistent data, default-heavy config
    Next: decide what needs hardening before cloud deployment

HOW TO USE THIS FILE
====================
Each section has:

    PLAN / QUESTIONS
    YOUR TURN space
    REFERENCE CODE

Try writing each function yourself in a scratch file or by covering the reference.
Then compare your code to the reference implementation below each section.
"""

# =============================================================================
# PART 1: IMPORTS
# =============================================================================
# PLAN / QUESTIONS:
# What does this script need?
# - argparse: CLI flags like --format and --compose-file
# - json: machine-readable output
# - sys: clean stderr and exit behavior
# - dataclass/asdict: structured report objects
# - pathlib: safe path handling
# - typing Any: YAML returns nested mixed data
# - yaml: parse Docker Compose YAML
#
# Why not regex the compose files?
# Because YAML is structured data. Infra scripts should use structured parsers
# when possible.
#
# YOUR TURN:
# Write the imports yourself before reading the reference.
#
#
#
# REFERENCE CODE:
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # keep --help and error messages clean if PyYAML is missing
    yaml = None


# =============================================================================
# PART 2: CONSTANTS AND DEFAULT FILES
# =============================================================================
# PLAN / QUESTIONS:
# What compose files represent the current local runtime?
# - root docker-compose.yml: older/shared/root infra surface
# - docker-compose.odoo.yml: active Odoo storefront/ERP stack
# - Pokemon/docker-compose.yml: active PokemonTool stack
#
# Why include root compose if Nexus is not active?
# Because the repo still has it and future sessions may confuse it with active
# Odoo/Pokemon work. Inventory should label what exists, then reports can mark
# active vs legacy.
#
# YOUR TURN:
# Define REPO_ROOT and DEFAULT_COMPOSE_FILES.
#
#
#
# REFERENCE CODE:
REPO_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_COMPOSE_FILES = [
    REPO_ROOT / "docker-compose.yml",
    REPO_ROOT / "docker-compose.odoo.yml",
    REPO_ROOT / "Pokemon" / "docker-compose.yml",
]


# =============================================================================
# PART 3: DATA MODELS
# =============================================================================
# PLAN / QUESTIONS:
# What should one service inventory record contain?
# Think like an infra engineer:
# - where did this service come from?
# - what image/build runs it?
# - what ports does it expose?
# - what data does it mount/persist?
# - what does it depend on?
# - does it have a healthcheck?
# - what network boundary does it use?
# - what risk notes jump out?
#
# YOUR TURN:
# Create dataclasses for ServiceInventory and ComposeInventoryReport.
#
#
#
# REFERENCE CODE:
@dataclass(frozen=True)
class ServiceInventory:
    compose_file: str
    service: str
    image: str | None
    build: str | None
    ports: list[str] = field(default_factory=list)
    expose: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    volumes: list[str] = field(default_factory=list)
    networks: list[str] = field(default_factory=list)
    environment_keys: list[str] = field(default_factory=list)
    has_healthcheck: bool = False
    risk_notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ComposeInventoryReport:
    repo_root: str
    compose_files: list[str]
    services: list[ServiceInventory]
    missing_files: list[str]


# =============================================================================
# PART 4: CLI ARGUMENTS
# =============================================================================
# PLAN / QUESTIONS:
# What choices should the operator have?
# - Choose output format: markdown/json
# - Add extra compose files if needed
# - Fail with useful help
#
# Why support JSON?
# Because later one script can feed another script, CI job, or report generator.
#
# YOUR TURN:
# Write parse_args().
#
#
#
# REFERENCE CODE:
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a read-only infrastructure inventory from Docker Compose files."
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format. Default: markdown.",
    )
    parser.add_argument(
        "--compose-file",
        action="append",
        default=[],
        help="Additional compose file to include. Can be passed multiple times.",
    )
    return parser.parse_args()


# =============================================================================
# PART 5: YAML LOADING
# =============================================================================
# PLAN / QUESTIONS:
# What can go wrong when loading YAML?
# - PyYAML might not be installed
# - file may not exist
# - YAML may be invalid
# - YAML may parse to something other than a dict
#
# Good infra scripts fail clearly. They do not produce confusing tracebacks for
# normal operator mistakes.
#
# YOUR TURN:
# Write require_yaml() and load_compose(path).
#
#
#
# REFERENCE CODE:
def require_yaml() -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is not installed. Install it with: python3 -m pip install PyYAML")


def load_compose(path: Path) -> dict[str, Any]:
    require_yaml()
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
    except yaml.YAMLError as error:
        raise RuntimeError(f"invalid YAML in {path}: {error}") from error

    if not isinstance(loaded, dict):
        raise RuntimeError(f"compose file did not parse to a mapping: {path}")
    return loaded


# =============================================================================
# PART 6: NORMALIZATION HELPERS
# =============================================================================
# PLAN / QUESTIONS:
# Docker Compose fields can be strings, lists, or dictionaries.
# You need helpers that turn messy YAML shapes into stable lists of strings.
#
# Example shapes:
#   ports:
#     - "127.0.0.1:8069:8069"
#
#   depends_on:
#     postgres:
#       condition: service_healthy
#
#   environment:
#     POSTGRES_USER: odoo
#
# The report should not care about every YAML shape. It should normalize.
#
# YOUR TURN:
# Write stringify_list(), depends_on_names(), environment_keys(), and build_value().
#
#
#
# REFERENCE CODE:
def stringify_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, dict):
        return [str(key) for key in value.keys()]
    return [str(value)]


def depends_on_names(value: Any) -> list[str]:
    if isinstance(value, dict):
        return sorted(str(key) for key in value.keys())
    return stringify_list(value)


def environment_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return sorted(str(key) for key in value.keys())
    if isinstance(value, list):
        keys = []
        for item in value:
            text = str(item)
            keys.append(text.split("=", 1)[0])
        return sorted(keys)
    return []


def build_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        context = value.get("context")
        dockerfile = value.get("dockerfile")
        if context and dockerfile:
            return f"{context} ({dockerfile})"
        if context:
            return str(context)
    return str(value)


# =============================================================================
# PART 7: RISK NOTES
# =============================================================================
# PLAN / QUESTIONS:
# Inventory is not enough. Add judgment.
#
# Risk questions:
# - Is a database/cache/admin UI bound to all interfaces?
# - Is the service missing a healthcheck?
# - Does it have persistent volumes, meaning backups matter?
# - Does it expose ports but lack obvious healthcheck?
# - Does env config include password/secret/token keys?
#
# Keep this simple. This is not a full security scanner. It is an operator
# first-pass report.
#
# YOUR TURN:
# Write risk_notes_for_service(...).
#
#
#
# REFERENCE CODE:
def is_localhost_port(port: str) -> bool:
    return port.startswith("127.0.0.1:") or port.startswith("localhost:")


def risk_notes_for_service(
    service_name: str,
    ports: list[str],
    volumes: list[str],
    env_keys: list[str],
    has_healthcheck: bool,
) -> list[str]:
    notes: list[str] = []
    lower_name = service_name.lower()
    sensitive_port_words = ("postgres", "redis", "rabbit", "grafana", "prometheus", "odoo", "db")

    for port in ports:
        if not is_localhost_port(port) and any(word in lower_name for word in sensitive_port_words):
            notes.append(f"review exposure: sensitive service publishes non-localhost port {port}")
        elif is_localhost_port(port):
            notes.append(f"localhost-only port binding: {port}")

    if ports and not has_healthcheck:
        notes.append("published port but no healthcheck in compose")

    if volumes:
        notes.append("persistent/mounted data exists; backup/restore ownership matters")

    secret_like_keys = [key for key in env_keys if any(word in key.upper() for word in ("SECRET", "PASSWORD", "TOKEN", "KEY"))]
    if secret_like_keys:
        notes.append(f"secret-like env keys present: {', '.join(secret_like_keys)}")

    if not notes:
        notes.append("no obvious first-pass risk from compose fields")

    return notes


# =============================================================================
# PART 8: EXTRACT ONE SERVICE
# =============================================================================
# PLAN / QUESTIONS:
# Given one compose service block, extract normalized fields and risk notes.
#
# This function is the heart of the script.
# It converts raw YAML into the ServiceInventory dataclass.
#
# YOUR TURN:
# Write extract_service(compose_file, service_name, service_config).
#
#
#
# REFERENCE CODE:
def extract_service(compose_file: Path, service_name: str, service_config: dict[str, Any]) -> ServiceInventory:
    ports = stringify_list(service_config.get("ports"))
    expose = stringify_list(service_config.get("expose"))
    depends = depends_on_names(service_config.get("depends_on"))
    volumes = stringify_list(service_config.get("volumes"))
    networks = stringify_list(service_config.get("networks"))
    env_keys = environment_keys(service_config.get("environment"))
    has_healthcheck = "healthcheck" in service_config

    risks = risk_notes_for_service(
        service_name=service_name,
        ports=ports,
        volumes=volumes,
        env_keys=env_keys,
        has_healthcheck=has_healthcheck,
    )

    return ServiceInventory(
        compose_file=str(compose_file.relative_to(REPO_ROOT)),
        service=service_name,
        image=service_config.get("image"),
        build=build_value(service_config.get("build")),
        ports=ports,
        expose=expose,
        depends_on=depends,
        volumes=volumes,
        networks=networks,
        environment_keys=env_keys,
        has_healthcheck=has_healthcheck,
        risk_notes=risks,
    )


# =============================================================================
# PART 9: BUILD THE FULL REPORT
# =============================================================================
# PLAN / QUESTIONS:
# The report builder should:
# - collect default compose files
# - include any extra files from CLI
# - track missing files instead of crashing
# - parse each compose file
# - extract each service
#
# Why track missing files?
# Because operational reports should show gaps. Missing files are evidence.
#
# YOUR TURN:
# Write build_report(extra_compose_files).
#
#
#
# REFERENCE CODE:
def build_report(extra_compose_files: list[str]) -> ComposeInventoryReport:
    compose_files = [*DEFAULT_COMPOSE_FILES]
    compose_files.extend((REPO_ROOT / file_path).resolve() for file_path in extra_compose_files)

    services: list[ServiceInventory] = []
    missing_files: list[str] = []

    for compose_file in compose_files:
        if not compose_file.exists():
            missing_files.append(str(compose_file))
            continue

        compose = load_compose(compose_file)
        raw_services = compose.get("services", {})
        if not isinstance(raw_services, dict):
            continue

        for service_name, service_config in sorted(raw_services.items()):
            if isinstance(service_config, dict):
                services.append(extract_service(compose_file, str(service_name), service_config))

    return ComposeInventoryReport(
        repo_root=str(REPO_ROOT),
        compose_files=[str(path) for path in compose_files],
        services=services,
        missing_files=missing_files,
    )


# =============================================================================
# PART 10: MARKDOWN OUTPUT
# =============================================================================
# PLAN / QUESTIONS:
# Markdown is the report format you can paste into Confluence or commit under
# infra/reports/.
#
# Good Markdown output should include:
# - summary counts
# - missing files
# - service table
# - risk notes by service
#
# YOUR TURN:
# Write markdown_report(report).
#
#
#
# REFERENCE CODE:
def markdown_report(report: ComposeInventoryReport) -> str:
    lines: list[str] = []
    lines.append("# Docker Compose Infrastructure Inventory")
    lines.append("")
    lines.append(f"Repo: `{report.repo_root}`")
    lines.append(f"Services found: `{len(report.services)}`")
    lines.append("")

    lines.append("## Compose Files")
    lines.append("")
    for file_path in report.compose_files:
        status = "missing" if file_path in report.missing_files else "checked"
        lines.append(f"- `{file_path}` - {status}")
    lines.append("")

    lines.append("## Service Inventory")
    lines.append("")
    lines.append("| Compose | Service | Runtime | Ports | Depends On | Volumes | Healthcheck |")
    lines.append("|---|---|---|---|---|---|---|")
    for service in report.services:
        runtime = service.image or service.build or "unknown"
        ports = "<br>".join(service.ports) if service.ports else ""
        depends = "<br>".join(service.depends_on) if service.depends_on else ""
        volumes = "<br>".join(service.volumes) if service.volumes else ""
        health = "yes" if service.has_healthcheck else "no"
        lines.append(
            f"| `{service.compose_file}` | `{service.service}` | `{runtime}` | {ports} | {depends} | {volumes} | {health} |"
        )
    lines.append("")

    lines.append("## Risk Notes")
    lines.append("")
    for service in report.services:
        lines.append(f"### `{service.service}` from `{service.compose_file}`")
        lines.append("")
        for note in service.risk_notes:
            lines.append(f"- {note}")
        if service.environment_keys:
            lines.append(f"- env keys: `{', '.join(service.environment_keys)}`")
        if service.networks:
            lines.append(f"- networks: `{', '.join(service.networks)}`")
        if service.expose:
            lines.append(f"- internal expose: `{', '.join(service.expose)}`")
        lines.append("")

    lines.append("## How To Use This Report")
    lines.append("")
    lines.append("Use this report to decide what needs hardening before cloud deployment:")
    lines.append("")
    lines.append("- Services with persistent volumes need backup/restore proof.")
    lines.append("- Services with published ports need exposure review.")
    lines.append("- Services without healthchecks need observability decisions.")
    lines.append("- Secret-like env keys need production secret management.")
    lines.append("- Localhost bindings map to private/internal exposure thinking in AWS.")
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# PART 11: PRINT OUTPUT
# =============================================================================
# PLAN / QUESTIONS:
# One function should decide output format.
# Keep this boring. Boring output functions are easy to test and reuse.
#
# YOUR TURN:
# Write print_report(report, output_format).
#
#
#
# REFERENCE CODE:
def print_report(report: ComposeInventoryReport, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(asdict(report), indent=2))
        return
    print(markdown_report(report))


# =============================================================================
# PART 12: MAIN FLOW
# =============================================================================
# PLAN / QUESTIONS:
# main() should be the operator workflow:
# - parse args
# - build report
# - print report
# - return 0 on success
# - return 1 on clean, understandable failure
#
# YOUR TURN:
# Write main().
#
#
#
# REFERENCE CODE:
def main() -> int:
    args = parse_args()
    try:
        report = build_report(args.compose_file)
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print_report(report, args.format)
    return 0


# =============================================================================
# PART 13: ENTRYPOINT
# =============================================================================
# PLAN / QUESTIONS:
# Use SystemExit(main()) so the return code becomes the process exit code.
# This matters later for CI.
#
# YOUR TURN:
# Write the entrypoint.
#
#
#
# REFERENCE CODE:
if __name__ == "__main__":
    raise SystemExit(main())


# =============================================================================
# PRACTICE COMMANDS
# =============================================================================
# Run help:
#   python3 infra/scripts/local/compose_inventory.py --help
#
# Generate Markdown:
#   python3 infra/scripts/local/compose_inventory.py
#
# Save report:
#   mkdir -p infra/reports
#   python3 infra/scripts/local/compose_inventory.py > infra/reports/current-runtime-state-jul2026.md
#
# Generate JSON:
#   python3 infra/scripts/local/compose_inventory.py --format json
#
# Add another compose file:
#   python3 infra/scripts/local/compose_inventory.py --compose-file Pokemon/docker-compose.prod.yml
#
# WHAT TO LEARN FROM THE OUTPUT
# =============================
# For every service ask:
# - Is this active, legacy, local-only, or future/cloud-only?
# - Is the port localhost-only or exposed broadly?
# - Does it persist data?
# - Does it have a healthcheck?
# - What would be the AWS equivalent?
# - What would break if this died?
#
# NEXT SCRIPT AFTER THIS
# ======================
# Once you understand this report, build:
#
#   infra/scripts/aws/02_vpc_network_inventory.py
#
# Same planning style:
#   Question -> Source -> Read-only method -> Output -> Risk -> Next action
