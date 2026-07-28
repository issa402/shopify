#!/usr/bin/env python3
"""Shared helpers for Future Standard IAM Access Analyzer reports.

These helpers are intentionally read-only. They do not create, update, delete,
archive, or remediate findings. They only help scripts select the right analyzer,
normalize identity context, and write report files.
"""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, ProfileNotFound
except ImportError:
    boto3 = None
    BotoCoreError = ClientError = NoCredentialsError = ProfileNotFound = Exception

DEFAULT_REGION = "us-east-1"
DEFAULT_OUTPUT_DIR = Path("infra/reports/futurestandard/access-analyzer")


@dataclass(frozen=True)
class AwsCaller:
    account: str
    arn: str
    user_id: str
    region: str
    profile: str
    checked_at: str


@dataclass(frozen=True)
class AnalyzerSummary:
    name: str
    arn: str
    type: str
    status: str


def require_boto3() -> None:
    """Fail clearly if boto3 is missing."""
    if boto3 is None:
        raise RuntimeError("boto3 is not installed. Install boto3 or run inside an AWS-ready Python env.")


def build_session(profile: str | None, region: str) -> Any:
    """Create one boto3 session for the selected profile and region."""
    require_boto3()
    return boto3.Session(profile_name=profile, region_name=region)


def get_caller(session: Any, profile: str | None, region: str) -> AwsCaller:
    """Call STS so every report proves which identity collected the data."""
    response = session.client("sts").get_caller_identity()
    return AwsCaller(
        account=response.get("Account", "unknown"),
        arn=response.get("Arn", "unknown"),
        user_id=response.get("UserId", "unknown"),
        region=region,
        profile=profile or "default",
        checked_at=datetime.now(timezone.utc).isoformat(),
    )


def access_analyzer_client(session: Any) -> Any:
    """Return the IAM Access Analyzer client."""
    return session.client("accessanalyzer")


def list_analyzers(client: Any) -> list[AnalyzerSummary]:
    """List analyzers and normalize the fields we care about."""
    analyzers: list[AnalyzerSummary] = []
    token: str | None = None

    while True:
        kwargs: dict[str, Any] = {}
        if token:
            kwargs["nextToken"] = token
        response = client.list_analyzers(**kwargs)
        for item in response.get("analyzers", []):
            analyzers.append(
                AnalyzerSummary(
                    name=item.get("name", ""),
                    arn=item.get("arn", ""),
                    type=item.get("type", ""),
                    status=item.get("status", ""),
                )
            )
        token = response.get("nextToken")
        if not token:
            return analyzers


def print_analyzers(analyzers: list[AnalyzerSummary]) -> None:
    """Print analyzers in a shape that makes choosing safer."""
    print("Analyzers")
    print("-" * 80)
    for index, analyzer in enumerate(analyzers):
        print(f"{index}: name={analyzer.name} type={analyzer.type} status={analyzer.status}")
        print(f"   arn={analyzer.arn}")


def select_analyzer(
    analyzers: list[AnalyzerSummary],
    analyzer_name: str | None,
    analyzer_arn: str | None,
    expected: str,
) -> AnalyzerSummary:
    """Select analyzer by exact name/ARN and warn when intent looks mismatched.

    expected should be "external" or "unused". This function does not guess from
    index 0 because AWS can return analyzers in an order that does not match the
    dashboard you are looking at.
    """
    if analyzer_arn:
        matches = [item for item in analyzers if item.arn == analyzer_arn]
    elif analyzer_name:
        matches = [item for item in analyzers if item.name == analyzer_name]
    else:
        raise RuntimeError("Pass --analyzer-name or --analyzer-arn. Do not rely on analyzer index 0.")

    if not matches:
        raise RuntimeError("No analyzer matched the provided name/ARN. Run 00_discover_analyzers.py first.")
    if len(matches) > 1:
        raise RuntimeError("Multiple analyzers matched. Use --analyzer-arn for an exact selection.")

    selected = matches[0]
    name_lower = selected.name.lower()
    if expected == "unused" and "unused" not in name_lower:
        print("WARNING: selected analyzer name does not look like an unused-access analyzer.", file=sys.stderr)
    if expected == "external" and "unused" in name_lower:
        print("WARNING: selected analyzer looks like unused access, not external/resource access.", file=sys.stderr)
    return selected


def confirm_analyzer(selected: AnalyzerSummary, expected: str, assume_yes: bool) -> None:
    """Force an intentional analyzer confirmation before collection."""
    print("Selected analyzer")
    print("-" * 80)
    print(f"expected_pipeline: {expected}")
    print(f"name: {selected.name}")
    print(f"arn:  {selected.arn}")
    print(f"type: {selected.type}")
    print(f"status: {selected.status}")
    print()

    if assume_yes:
        return
    if not sys.stdin.isatty():
        raise RuntimeError("Non-interactive run requires --yes after you confirm the analyzer is correct.")

    answer = input(f"Type the analyzer name to confirm {expected} pipeline: ").strip()
    if answer != selected.name:
        raise RuntimeError("Analyzer confirmation failed. Refusing to run against the wrong analyzer.")


def ensure_output_dir(path: Path) -> Path:
    """Create report output directory if needed."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def json_dumps(value: Any) -> str:
    """Stable JSON string for nested AWS fields in CSV."""
    return json.dumps(value, sort_keys=True, default=str)


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    """Write dictionaries to CSV with consistent columns."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def days_since(value: Any) -> int | None:
    """Return whole days since a datetime-like value, or None if missing."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    elif isinstance(value, datetime):
        parsed = value
    else:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).days


def resource_name_from_arn(resource: str) -> str:
    """Extract a readable resource name from an ARN or return the original string."""
    if not resource:
        return ""
    if ":" not in resource:
        return resource
    tail = resource.split(":", 5)[-1]
    for marker in ("role/", "user/", "policy/", "key/", "bucket/", "queue/"):
        if marker in tail:
            return tail.split(marker, 1)[-1]
    return tail.split("/")[-1]


def deep_find_first(value: Any, target_keys: set[str]) -> Any:
    """Search nested AWS JSON for the first matching key.

    Access Analyzer detail responses can vary by finding type. This lets report
    scripts extract fields like lastAccessed or lastUsed without hardcoding one
    shape too early.
    """
    if isinstance(value, dict):
        for key, item in value.items():
            if key in target_keys:
                return item
        for item in value.values():
            found = deep_find_first(item, target_keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = deep_find_first(item, target_keys)
            if found is not None:
                return found
    return None
