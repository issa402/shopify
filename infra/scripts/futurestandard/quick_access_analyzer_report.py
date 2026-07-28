#!/usr/bin/env python3
"""One-run IAM Access Analyzer CSV export.

How to run:
1. Paste AWS temp credentials into your terminal.
2. Run: python3 infra/scripts/futurestandard/quick_access_analyzer_report.py

What it does:
- Uses us-east-1.
- Finds the normal ConsoleAnalyzer for external/resource access.
- Finds the UnusedAccess-ConsoleAnalyzer for unused access.
- Exports simple CSV files into infra/reports/futurestandard/access-analyzer.
- Does not change AWS. Read-only only.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import boto3

REGION = "us-east-1"
OUT_DIR = Path("infra/reports/futurestandard/access-analyzer")
NEVER_USED_OLD_DAYS = 150
UNUSED_PERMISSION_FLAG_DAYS = 130


def write_csv(path, rows, headers):
    """Write rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def counter_csv(path, counter, key_name):
    """Write simple count CSV."""
    rows = [{key_name: key, "count": count} for key, count in counter.most_common()]
    write_csv(path, rows, [key_name, "count"])


def grouped_counter_csv(path, rows, keys):
    """Group rows by multiple keys and write count CSV."""
    counter = Counter(tuple(row.get(key, "") for key in keys) for row in rows)
    output = []
    for values, count in counter.most_common():
        item = {key: value for key, value in zip(keys, values)}
        item["count"] = count
        output.append(item)
    write_csv(path, output, [*keys, "count"])


def parse_dt(value):
    """Parse AWS datetime values."""
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def days_since(value):
    """Return days since datetime, or blank if unknown."""
    dt = parse_dt(value)
    if not dt:
        return ""
    return (datetime.now(timezone.utc) - dt).days


def deep_find_first(value, keys):
    """Find the first matching key inside nested AWS response JSON."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys:
                return item
        for item in value.values():
            found = deep_find_first(item, keys)
            if found is not None:
                return found
    if isinstance(value, list):
        for item in value:
            found = deep_find_first(item, keys)
            if found is not None:
                return found
    return None


def resource_name(resource):
    """Readable name from ARN-ish strings."""
    if not resource:
        return ""
    return str(resource).split("/")[-1]


def criticality(finding_type, age_days, days_unused, last_used):
    """Simple criticality for unused access cleanup candidates."""
    never_used = not last_used
    old_enough = isinstance(age_days, int) and age_days >= NEVER_USED_OLD_DAYS
    if never_used and old_enough:
        return "MUST_FLAG_NEVER_USED_OVER_5_MONTHS"
    if finding_type == "UnusedPermission" and (days_unused == "" or days_unused >= UNUSED_PERMISSION_FLAG_DAYS):
        return "MUST_FLAG_UNUSED_PERMISSION_130_DAYS_OR_NEVER"
    if isinstance(days_unused, int) and days_unused >= 180:
        return "HIGH_180_DAYS_UNUSED"
    if isinstance(days_unused, int) and days_unused >= 90:
        return "WARNING_90_DAYS_UNUSED"
    return "REVIEW"


def get_analyzers(aa):
    """Find both analyzers by name."""
    analyzers = aa.list_analyzers()["analyzers"]

    external = None
    unused = None

    for analyzer in analyzers:
        name = analyzer["name"]
        if name.startswith("UnusedAccess-ConsoleAnalyzer"):
            unused = analyzer
        elif name.startswith("ConsoleAnalyzer"):
            external = analyzer

    if external is None:
        raise RuntimeError("Could not find ConsoleAnalyzer external/resource analyzer")
    if unused is None:
        raise RuntimeError("Could not find UnusedAccess-ConsoleAnalyzer unused analyzer")

    return external, unused


def export_external_findings(aa, analyzer):
    """Export public/external access findings from ConsoleAnalyzer."""
    rows = []
    paginator = aa.get_paginator("list_findings")

    for page in paginator.paginate(
        analyzerArn=analyzer["arn"],
        filter={"status": {"eq": ["ACTIVE"]}},
    ):
        for f in page.get("findings", []):
            rows.append({
                "account": f.get("resourceOwnerAccount", ""),
                "resource": f.get("resource", ""),
                "resource_type": f.get("resourceType", ""),
                "finding_id": f.get("id", ""),
                "status": f.get("status", ""),
                "is_public": f.get("isPublic", False),
                "principal": json.dumps(f.get("principal", {}), default=str),
                "action": json.dumps(f.get("action", []), default=str),
                "condition": json.dumps(f.get("condition", {}), default=str),
                "created_at": str(f.get("createdAt", "")),
                "updated_at": str(f.get("updatedAt", "")),
            })

    headers = [
        "account", "resource", "resource_type", "finding_id", "status",
        "is_public", "principal", "action", "condition", "created_at", "updated_at",
    ]
    write_csv(OUT_DIR / "external_access_findings.csv", rows, headers)
    counter_csv(OUT_DIR / "external_top_accounts.csv", Counter(r["account"] for r in rows), "account")
    counter_csv(OUT_DIR / "external_top_resource_types.csv", Counter(r["resource_type"] for r in rows), "resource_type")
    counter_csv(OUT_DIR / "external_top_principals.csv", Counter(r["principal"] for r in rows), "principal")
    grouped_counter_csv(OUT_DIR / "external_group_by_account_and_type.csv", rows, ["account", "resource_type"])
    grouped_counter_csv(OUT_DIR / "external_group_by_account_type_resource.csv", rows, ["account", "resource_type", "resource"])

    print(f"External/resource findings: {len(rows)}")


def export_unused_findings(aa, analyzer):
    """Export unused roles, keys, passwords, and permissions from UnusedAccess analyzer."""
    rows = []
    paginator = aa.get_paginator("list_findings_v2")

    for page in paginator.paginate(
        analyzerArn=analyzer["arn"],
        filter={"status": {"eq": ["ACTIVE"]}},
    ):
        for f in page.get("findings", []):
            detail = {}
            try:
                detail = aa.get_finding_v2(analyzerArn=analyzer["arn"], id=f.get("id", ""))
            except Exception as error:
                detail = {"detail_error": str(error)}

            last_used = deep_find_first(detail, {"lastAccessed", "lastAccessedTime", "lastUsed", "lastUsedDate", "lastUsedAt"})
            access_key_id = deep_find_first(detail, {"accessKeyId", "accessKey"}) or ""
            created_at = f.get("createdAt", "")
            age_days = days_since(created_at)
            unused_days = days_since(last_used)
            finding_type = f.get("findingType", "")

            rows.append({
                "account": f.get("resourceOwnerAccount", ""),
                "resource": f.get("resource", ""),
                "resource_name": resource_name(f.get("resource", "")),
                "resource_type": f.get("resourceType", ""),
                "finding_type": finding_type,
                "finding_id": f.get("id", ""),
                "status": f.get("status", ""),
                "created_at": str(created_at),
                "age_days": age_days,
                "last_used_at": str(last_used or ""),
                "days_unused": unused_days,
                "access_key_id": access_key_id,
                "criticality": criticality(finding_type, age_days, unused_days, last_used),
                "updated_at": str(f.get("updatedAt", "")),
                "analyzed_at": str(f.get("analyzedAt", "")),
            })

    headers = [
        "account", "resource", "resource_name", "resource_type", "finding_type", "finding_id",
        "status", "created_at", "age_days", "last_used_at", "days_unused", "access_key_id",
        "criticality", "updated_at", "analyzed_at",
    ]
    write_csv(OUT_DIR / "unused_access_findings.csv", rows, headers)
    write_csv(OUT_DIR / "unused_roles.csv", [r for r in rows if r["finding_type"] == "UnusedIAMRole"], headers)
    write_csv(OUT_DIR / "unused_access_keys.csv", [r for r in rows if r["finding_type"] == "UnusedIAMUserAccessKey"], headers)
    write_csv(OUT_DIR / "unused_permissions.csv", [r for r in rows if r["finding_type"] == "UnusedPermission"], headers)
    write_csv(OUT_DIR / "unused_must_flag_never_used_over_5_months.csv", [r for r in rows if r["criticality"] == "MUST_FLAG_NEVER_USED_OVER_5_MONTHS"], headers)
    write_csv(OUT_DIR / "unused_permissions_must_flag_130_days_or_never.csv", [r for r in rows if r["criticality"] == "MUST_FLAG_UNUSED_PERMISSION_130_DAYS_OR_NEVER"], headers)
    counter_csv(OUT_DIR / "unused_top_accounts.csv", Counter(r["account"] for r in rows), "account")
    counter_csv(OUT_DIR / "unused_top_finding_types.csv", Counter(r["finding_type"] for r in rows), "finding_type")
    grouped_counter_csv(OUT_DIR / "unused_group_by_account_and_finding_type.csv", rows, ["account", "finding_type"])

    print(f"Unused access findings: {len(rows)}")


def main():
    sts = boto3.client("sts", region_name=REGION)
    aa = boto3.client("accessanalyzer", region_name=REGION)

    identity = sts.get_caller_identity()
    print("Account:", identity["Account"])
    print("Arn:", identity["Arn"])

    external, unused = get_analyzers(aa)
    print("External analyzer:", external["name"])
    print("Unused analyzer:", unused["name"])

    export_external_findings(aa, external)
    export_unused_findings(aa, unused)

    print("CSV output:", OUT_DIR)


if __name__ == "__main__":
    main()
