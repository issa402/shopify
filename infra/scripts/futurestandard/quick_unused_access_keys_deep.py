#!/usr/bin/env python3
"""Deep export only unused IAM access key findings.

How to run:
1. Paste AWS temp credentials into your terminal.
2. Run: python3 infra/scripts/futurestandard/quick_unused_access_keys_deep.py

This is read-only. It does not disable/delete keys.
It only deep-fetches UnusedIAMUserAccessKey findings, which should be a small set.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import boto3

REGION = "us-east-1"
OUT_DIR = Path("infra/reports/futurestandard/access-analyzer")
OUT_FILE = OUT_DIR / "unused_access_keys_deep.csv"


def write_csv(path, rows, headers):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_dt(value):
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
    dt = parse_dt(value)
    if not dt:
        return ""
    return (datetime.now(timezone.utc) - dt).days


def deep_find_all(value, wanted_keys):
    """Return every matching key/value found in nested AWS response JSON."""
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in wanted_keys:
                found.append((key, item))
            found.extend(deep_find_all(item, wanted_keys))
    elif isinstance(value, list):
        for item in value:
            found.extend(deep_find_all(item, wanted_keys))
    return found


def deep_find_first(value, wanted_keys):
    matches = deep_find_all(value, wanted_keys)
    return matches[0][1] if matches else ""


def username_from_resource(resource):
    text = str(resource or "")
    if ":user/" in text:
        return text.split(":user/", 1)[-1]
    if "/" in text:
        return text.split("/")[-1]
    return text


def criticality(created_at, last_used_at):
    age = days_since(created_at)
    unused = days_since(last_used_at)
    never_used = not last_used_at

    if never_used and isinstance(age, int) and age >= 150:
        return "MUST_FLAG_NEVER_USED_OVER_5_MONTHS"
    if isinstance(unused, int) and unused >= 180:
        return "HIGH_180_DAYS_UNUSED"
    if isinstance(unused, int) and unused >= 90:
        return "WARNING_90_DAYS_UNUSED"
    if never_used:
        return "REVIEW_NEVER_USED_BUT_NEWER"
    return "REVIEW"


def get_unused_analyzer(aa):
    analyzers = aa.list_analyzers()["analyzers"]
    for analyzer in analyzers:
        if analyzer["name"].startswith("UnusedAccess-ConsoleAnalyzer"):
            return analyzer
    raise RuntimeError("Could not find UnusedAccess-ConsoleAnalyzer")


def list_access_key_findings(aa, analyzer):
    findings = []
    paginator = aa.get_paginator("list_findings_v2")
    for page in paginator.paginate(
        analyzerArn=analyzer["arn"],
        filter={"status": {"eq": ["ACTIVE"]}},
    ):
        for finding in page.get("findings", []):
            if finding.get("findingType") == "UnusedIAMUserAccessKey":
                findings.append(finding)
    return findings


def main():
    sts = boto3.client("sts", region_name=REGION)
    aa = boto3.client("accessanalyzer", region_name=REGION)

    identity = sts.get_caller_identity()
    print("Account:", identity["Account"])
    print("Arn:", identity["Arn"])

    analyzer = get_unused_analyzer(aa)
    print("Unused analyzer:", analyzer["name"])

    findings = list_access_key_findings(aa, analyzer)
    print("Unused access key findings:", len(findings))

    rows = []
    for finding in findings:
        finding_id = finding.get("id", "")
        detail = aa.get_finding_v2(analyzerArn=analyzer["arn"], id=finding_id)

        resource = finding.get("resource", "")
        created_at = finding.get("createdAt", "")
        access_key_id = deep_find_first(detail, {"accessKeyId", "accessKey"})
        last_used_at = deep_find_first(detail, {"lastAccessed", "lastAccessedTime", "lastUsed", "lastUsedDate", "lastUsedAt"})

        # If AWS changes nested fields, keep a compact JSON hint for debugging.
        matching_detail_keys = deep_find_all(detail, {"accessKeyId", "accessKey", "lastAccessed", "lastUsed", "lastUsedDate", "lastUsedAt"})

        rows.append({
            "account": finding.get("resourceOwnerAccount", ""),
            "user_name": username_from_resource(resource),
            "resource": resource,
            "access_key_id": access_key_id,
            "finding_id": finding_id,
            "status": finding.get("status", ""),
            "created_at": str(created_at),
            "age_days": days_since(created_at),
            "last_used_at": str(last_used_at or ""),
            "days_unused": days_since(last_used_at),
            "criticality": criticality(created_at, last_used_at),
            "updated_at": str(finding.get("updatedAt", "")),
            "analyzed_at": str(finding.get("analyzedAt", "")),
            "detail_key_hints": json.dumps(matching_detail_keys, default=str),
        })

    headers = [
        "account", "user_name", "resource", "access_key_id", "finding_id", "status",
        "created_at", "age_days", "last_used_at", "days_unused", "criticality",
        "updated_at", "analyzed_at", "detail_key_hints",
    ]
    write_csv(OUT_FILE, rows, headers)
    print("CSV output:", OUT_FILE)


if __name__ == "__main__":
    main()
