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
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import boto3

REGION = "us-east-1"
OUT_DIR = Path("infra/reports/futurestandard/access-analyzer")
NEVER_USED_OLD_DAYS = 150
UNUSED_PERMISSION_FLAG_DAYS = 130
FETCH_DETAILS = os.getenv("ACCESS_ANALYZER_FETCH_DETAILS") == "1"


def write_csv(path, rows, headers):
    """Write rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def counter_csv(path, counter, key_name):
    """Write simple count CSV sorted by count descending."""
    rows = [{key_name: key, "count": count} for key, count in counter.most_common()]
    write_csv(path, rows, [key_name, "count"])
    return rows


def grouped_counter_csv(path, rows, keys):
    """Group rows by multiple keys and write count CSV."""
    counter = Counter(tuple(row.get(key, "") for key in keys) for row in rows)
    output = []
    for values, count in counter.most_common():
        item = {key: value for key, value in zip(keys, values)}
        item["count"] = count
        output.append(item)
    write_csv(path, output, [*keys, "count"])
    return output


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
    if FETCH_DETAILS and never_used and old_enough:
        return "MUST_FLAG_NEVER_USED_OVER_5_MONTHS"
    if finding_type == "UnusedPermission" and (days_unused == "" or days_unused >= UNUSED_PERMISSION_FLAG_DAYS):
        return "MUST_FLAG_UNUSED_PERMISSION_REVIEW"
    if old_enough:
        return "REVIEW_UNUSED_FINDING_OVER_5_MONTHS"
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
    rows = sorted(rows, key=lambda r: (r["account"], r["resource_type"], r["resource"]))
    write_csv(OUT_DIR / "external_access_findings.csv", rows, headers)
    top_accounts = counter_csv(OUT_DIR / "external_top_accounts.csv", Counter(r["account"] for r in rows), "account")
    top_resource_types = counter_csv(OUT_DIR / "external_top_resource_types.csv", Counter(r["resource_type"] for r in rows), "resource_type")
    top_principals = counter_csv(OUT_DIR / "external_top_principals.csv", Counter(r["principal"] for r in rows), "principal")
    account_type = grouped_counter_csv(OUT_DIR / "external_group_by_account_and_type.csv", rows, ["account", "resource_type"])
    account_type_resource = grouped_counter_csv(OUT_DIR / "external_group_by_account_type_resource.csv", rows, ["account", "resource_type", "resource"])

    print(f"External/resource findings: {len(rows)}")
    return {
        "rows": rows,
        "top_accounts": top_accounts,
        "top_resource_types": top_resource_types,
        "top_principals": top_principals,
        "account_type": account_type,
        "account_type_resource": account_type_resource,
    }


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
            if FETCH_DETAILS:
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
    severity_order = {
        "MUST_FLAG_NEVER_USED_OVER_5_MONTHS": 0,
        "MUST_FLAG_UNUSED_PERMISSION_REVIEW": 1,
        "REVIEW_UNUSED_FINDING_OVER_5_MONTHS": 2,
        "HIGH_180_DAYS_UNUSED": 3,
        "WARNING_90_DAYS_UNUSED": 4,
        "REVIEW": 5,
    }
    rows = sorted(rows, key=lambda r: (severity_order.get(r["criticality"], 99), r["account"], r["finding_type"], r["resource_name"]))
    roles = [r for r in rows if r["finding_type"] == "UnusedIAMRole"]
    keys = [r for r in rows if r["finding_type"] == "UnusedIAMUserAccessKey"]
    permissions = [r for r in rows if r["finding_type"] == "UnusedPermission"]
    over_5_months = [r for r in rows if r["criticality"] in {"MUST_FLAG_NEVER_USED_OVER_5_MONTHS", "REVIEW_UNUSED_FINDING_OVER_5_MONTHS"}]
    permission_candidates = [r for r in rows if r["finding_type"] == "UnusedPermission"]

    write_csv(OUT_DIR / "unused_access_findings.csv", rows, headers)
    write_csv(OUT_DIR / "unused_roles.csv", roles, headers)
    write_csv(OUT_DIR / "unused_access_keys.csv", keys, headers)
    write_csv(OUT_DIR / "unused_permissions.csv", permissions, headers)
    write_csv(OUT_DIR / "unused_candidates_over_5_months.csv", over_5_months, headers)
    write_csv(OUT_DIR / "unused_permissions_candidates.csv", permission_candidates, headers)
    top_accounts = counter_csv(OUT_DIR / "unused_top_accounts.csv", Counter(r["account"] for r in rows), "account")
    top_finding_types = counter_csv(OUT_DIR / "unused_top_finding_types.csv", Counter(r["finding_type"] for r in rows), "finding_type")
    account_finding_type = grouped_counter_csv(OUT_DIR / "unused_group_by_account_and_finding_type.csv", rows, ["account", "finding_type"])

    print(f"Unused access findings: {len(rows)}")
    if not FETCH_DETAILS:
        print("Skipped slow per-finding get_finding_v2 detail calls. Set ACCESS_ANALYZER_FETCH_DETAILS=1 only for smaller/deep runs.")
    return {
        "rows": rows,
        "roles": roles,
        "keys": keys,
        "permissions": permissions,
        "over_5_months": over_5_months,
        "permission_candidates": permission_candidates,
        "top_accounts": top_accounts,
        "top_finding_types": top_finding_types,
        "account_finding_type": account_finding_type,
    }


def top_lines(rows, label_key, count_key="count", limit=10):
    lines = []
    for row in rows[:limit]:
        label = row.get(label_key, "")
        count = row.get(count_key, "")
        lines.append(f"- `{label}`: `{count}`")
    return lines or ["- None"]


def write_report(identity, external_summary, unused_summary):
    """Write a manager/operator report explaining every CSV and next steps."""
    lines = [
        "# Future Standard Access Analyzer Report",
        "",
        "## What This Run Does",
        "",
        "This is a read-only export and triage report. It does not disable keys, delete roles, change policies, archive findings, or remediate anything.",
        "",
        f"- Security services account used: `{identity['Account']}`",
        f"- Caller ARN: `{identity['Arn']}`",
        f"- External/resource findings exported: `{len(external_summary['rows'])}`",
        f"- Unused access findings exported: `{len(unused_summary['rows'])}`",
        "",
        "## What To Look At First",
        "",
        "1. `external_group_by_account_and_type.csv` - tells which accounts have concentrated external/public access by resource type.",
        "2. `external_group_by_account_type_resource.csv` - gives exact account + resource + type counts for owner review.",
        "3. `unused_top_accounts.csv` - shows accounts with the most stale IAM findings.",
        "4. `unused_group_by_account_and_finding_type.csv` - splits each account by unused roles, keys, passwords, and permissions.",
        "5. `unused_access_keys_deep.csv` - run the separate deep key script for actual AccessKeyId values before any key disable plan.",
        "",
        "## CSV File Guide",
        "",
        "| CSV | Purpose | How It Helps |",
        "|---|---|---|",
        "| `external_access_findings.csv` | All active external/resource findings. | Raw evidence list for S3/SNS/SQS/IAM/KMS resource review. |",
        "| `external_top_accounts.csv` | Accounts ranked by external finding count. | Start with highest-volume accounts. |",
        "| `external_top_resource_types.csv` | Resource types ranked by finding count. | Shows whether the main issue is S3, SQS, IAM roles, KMS, etc. |",
        "| `external_top_principals.csv` | External principals ranked by count. | Helps spot repeated outside accounts/vendors/public principals. |",
        "| `external_group_by_account_and_type.csv` | Count by account and resource type. | Directly answers: account has 3 S3, 2 IAM role, 2 SQS findings. |",
        "| `external_group_by_account_type_resource.csv` | Count by account, resource type, and resource. | Exact resource-owner review list. |",
        "| `unused_access_findings.csv` | All active unused access findings. | Raw stale IAM evidence. |",
        "| `unused_roles.csv` | Only unused IAM role findings. | Role cleanup candidate list. |",
        "| `unused_access_keys.csv` | Only unused access key summary findings. | Account/user finding list; run deep key script for actual key IDs. |",
        "| `unused_permissions.csv` | Only unused permission findings. | Policy reduction candidate list. |",
        "| `unused_top_accounts.csv` | Accounts ranked by unused finding count. | Start stale-access review with highest-volume accounts. |",
        "| `unused_top_finding_types.csv` | Unused finding types ranked by count. | Shows whether stale roles, credentials, or permissions dominate. |",
        "| `unused_group_by_account_and_finding_type.csv` | Count by account and unused finding type. | Tells each account's stale access pattern. |",
        "| `unused_candidates_over_5_months.csv` | Old unused finding candidates. | Review list for older stale access. |",
        "| `unused_permissions_candidates.csv` | Unused permission candidates. | Policy right-sizing input. |",
        "",
        "## Top External Accounts",
        "",
        *top_lines(external_summary["top_accounts"], "account"),
        "",
        "## Top External Resource Types",
        "",
        *top_lines(external_summary["top_resource_types"], "resource_type"),
        "",
        "## Top Unused Access Accounts",
        "",
        *top_lines(unused_summary["top_accounts"], "account"),
        "",
        "## Top Unused Finding Types",
        "",
        *top_lines(unused_summary["top_finding_types"], "finding_type"),
        "",
        "## Fix Plan",
        "",
        "1. Review grouped CSVs first; do not start with raw findings.",
        "2. Assign account owners for the top accounts.",
        "3. For external access, classify each principal as approved vendor, internal cross-account, public, unknown, or remove candidate.",
        "4. For unused keys, run `quick_unused_access_keys_deep.py` to get `UserName` and `AccessKeyId` before any disable plan.",
        "5. For unused roles, validate owner/workload before delete or permission removal.",
        "6. For unused permissions, use the findings as input to policy right-sizing; do not blindly remove permissions without approval.",
        "7. Build a separate dry-run remediation script later that reads approved rows only.",
        "",
        "## Why This Helps",
        "",
        "The AWS dashboard shows the problem. These files turn it into an owner-review and remediation-prep workflow: account -> resource type -> exact resource -> finding -> approved next action.",
    ]
    (OUT_DIR / "ACCESS_ANALYZER_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    sts = boto3.client("sts", region_name=REGION)
    aa = boto3.client("accessanalyzer", region_name=REGION)

    identity = sts.get_caller_identity()
    print("Account:", identity["Account"])
    print("Arn:", identity["Arn"])

    external, unused = get_analyzers(aa)
    print("External analyzer:", external["name"])
    print("Unused analyzer:", unused["name"])

    external_summary = export_external_findings(aa, external)
    unused_summary = export_unused_findings(aa, unused)
    write_report(identity, external_summary, unused_summary)

    print("CSV output:", OUT_DIR)
    print("Report:", OUT_DIR / "ACCESS_ANALYZER_REPORT.md")


if __name__ == "__main__":
    main()
