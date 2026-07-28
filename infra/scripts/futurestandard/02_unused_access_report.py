#!/usr/bin/env python3
"""Export unused-access findings from IAM Access Analyzer.

Use this for the UnusedAccess analyzer. It reports unused IAM roles, unused
access keys, unused passwords, and unused permissions. Detail collection calls
get_finding_v2 so the script can try to extract last-used signals where AWS
returns them.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from access_analyzer_common import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REGION,
    access_analyzer_client,
    build_session,
    confirm_analyzer,
    days_since,
    deep_find_first,
    ensure_output_dir,
    get_caller,
    json_dumps,
    list_analyzers,
    resource_name_from_arn,
    select_analyzer,
    write_csv,
)

NEVER_USED_OLD_DAYS = 150
UNUSED_PERMISSION_FLAG_DAYS = 130
WARNING_DAYS = 90
CRITICAL_DAYS = 180


@dataclass(frozen=True)
class UnusedFinding:
    account: str
    resource: str
    resource_name: str
    resource_type: str
    finding_id: str
    finding_type: str
    status: str
    created_at: str
    updated_at: str
    age_days: int | None
    last_used_at: str
    days_unused: int | None
    criticality: str
    recommendation: str
    raw_detail_hint: str

    def to_csv_row(self) -> dict[str, Any]:
        return asdict(self)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report unused IAM access findings.")
    parser.add_argument("--profile", help="Optional AWS named profile. Omit this when using pasted AWS env tokens.")
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--analyzer-name", help="Exact UnusedAccess analyzer name.")
    parser.add_argument("--analyzer-arn", help="Exact UnusedAccess analyzer ARN.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--include-archived", action="store_true", help="Include non-ACTIVE findings.")
    parser.add_argument("--max-findings", type=int, help="Limit findings for test runs.")
    parser.add_argument("--no-details", action="store_true", help="Skip get_finding_v2 detail calls.")
    parser.add_argument("--yes", action="store_true", help="Confirm the selected analyzer without interactive prompt.")
    return parser.parse_args()


def list_unused_finding_summaries(client: Any, analyzer_arn: str, active_only: bool, max_findings: int | None) -> list[dict[str, Any]]:
    """Collect raw finding summaries with list_findings_v2."""
    summaries: list[dict[str, Any]] = []
    kwargs: dict[str, Any] = {"analyzerArn": analyzer_arn}
    if active_only:
        kwargs["filter"] = {"status": {"eq": ["ACTIVE"]}}

    paginator = client.get_paginator("list_findings_v2")
    for page in paginator.paginate(**kwargs):
        for item in page.get("findings", []):
            summaries.append(item)
            if max_findings and len(summaries) >= max_findings:
                return summaries
    return summaries


def get_detail(client: Any, analyzer_arn: str, finding_id: str, include_details: bool) -> dict[str, Any]:
    """Fetch finding details when allowed/requested.

    If the role lacks get_finding_v2 or AWS throttles/fails, return a compact
    error object instead of killing the whole report.
    """
    if not include_details:
        return {}
    try:
        return client.get_finding_v2(analyzerArn=analyzer_arn, id=finding_id)
    except Exception as error:  # report should survive detail failures
        return {"detail_error": str(error)}


def infer_last_used(summary: dict[str, Any], detail: dict[str, Any]) -> Any:
    """Try multiple field names because finding details vary by type."""
    return (
        deep_find_first(detail, {"lastAccessed", "lastAccessedTime", "lastUsed", "lastUsedDate", "lastUsedAt"})
        or deep_find_first(summary, {"lastAccessed", "lastUsed", "lastUsedDate", "lastUsedAt"})
    )


def criticality_for(finding_type: str, age_days: int | None, days_unused: int | None, last_used_at: str) -> str:
    """Classify urgency using the Future Standard task thresholds."""
    never_used = not last_used_at
    old_enough = age_days is not None and age_days >= NEVER_USED_OLD_DAYS

    if never_used and old_enough:
        return "MUST_FLAG_NEVER_USED"
    if days_unused is not None and days_unused >= CRITICAL_DAYS:
        return "CRITICAL_180_DAYS"
    if finding_type == "UnusedPermission" and days_unused is not None and days_unused >= UNUSED_PERMISSION_FLAG_DAYS:
        return "FLAG_130_DAYS"
    if days_unused is not None and days_unused >= WARNING_DAYS:
        return "WARNING_90_DAYS"
    if never_used:
        return "WATCH_NEVER_USED_BUT_NEWER_THAN_5_MONTHS"
    return "OK_RECENT_OR_UNKNOWN"


def recommendation_for(finding_type: str, criticality: str) -> str:
    """Convert criticality into a human next step."""
    if finding_type == "UnusedIAMUserAccessKey":
        if criticality.startswith("MUST_FLAG") or criticality.startswith("CRITICAL"):
            return "Validate owner, disable key, monitor breakage window, then delete/rotate per policy."
        return "Review owner and rotate/disable if no approved use exists."
    if finding_type == "UnusedIAMRole":
        if criticality.startswith("MUST_FLAG") or criticality.startswith("CRITICAL"):
            return "Validate workload owner; remove role or reduce trust/policies after approval."
        return "Ask account owner whether role is still needed."
    if finding_type == "UnusedPermission":
        return "Review policy action list; remove unused permissions after owner approval."
    return "Review with account owner and document exception or cleanup action."


def normalize_unused_finding(summary: dict[str, Any], detail: dict[str, Any]) -> UnusedFinding:
    """Convert one AWS finding into a stable CSV/report row."""
    created_at = summary.get("createdAt")
    last_used = infer_last_used(summary, detail)
    age = days_since(created_at)
    unused_days = days_since(last_used)
    last_used_text = str(last_used or "")
    finding_type = summary.get("findingType", "")
    criticality = criticality_for(finding_type, age, unused_days, last_used_text)

    return UnusedFinding(
        account=summary.get("resourceOwnerAccount", "UNKNOWN"),
        resource=summary.get("resource", ""),
        resource_name=resource_name_from_arn(summary.get("resource", "")),
        resource_type=summary.get("resourceType", ""),
        finding_id=summary.get("id", ""),
        finding_type=finding_type,
        status=summary.get("status", ""),
        created_at=str(created_at or ""),
        updated_at=str(summary.get("updatedAt", "")),
        age_days=age,
        last_used_at=last_used_text,
        days_unused=unused_days,
        criticality=criticality,
        recommendation=recommendation_for(finding_type, criticality),
        raw_detail_hint=json_dumps(detail.get("findingDetails", detail))[:2000],
    )


def collect_unused_findings(client: Any, analyzer_arn: str, active_only: bool, include_details: bool, max_findings: int | None) -> list[UnusedFinding]:
    summaries = list_unused_finding_summaries(client, analyzer_arn, active_only, max_findings)
    findings: list[UnusedFinding] = []
    for summary in summaries:
        detail = get_detail(client, analyzer_arn, summary.get("id", ""), include_details)
        findings.append(normalize_unused_finding(summary, detail))
    return findings


def counter_rows(counter: Counter[str], key_name: str) -> list[dict[str, Any]]:
    return [{key_name: key, "count": count} for key, count in counter.most_common()]


def write_summary(output_dir: Path, caller: Any, analyzer: Any, findings: list[UnusedFinding]) -> None:
    account_counts = Counter(f.account for f in findings)
    type_counts = Counter(f.finding_type for f in findings)
    criticality_counts = Counter(f.criticality for f in findings)

    lines = [
        "# Unused Access Findings Summary",
        "",
        "## Analyzer Check",
        "",
        f"- Caller account: `{caller.account}`",
        f"- Caller ARN: `{caller.arn}`",
        f"- Analyzer name: `{analyzer.name}`",
        f"- Analyzer ARN: `{analyzer.arn}`",
        "- API used: `accessanalyzer.list_findings_v2` plus optional `get_finding_v2`",
        "- Intended analyzer: unused-access analyzer",
        "",
        "## Totals",
        "",
        f"- Findings exported: `{len(findings)}`",
        "",
        "## Criticality Counts",
        "",
    ]
    lines += [f"- `{key}`: `{count}`" for key, count in criticality_counts.most_common()]
    lines += ["", "## Top Accounts", ""]
    lines += [f"- `{account}`: `{count}`" for account, count in account_counts.most_common(10)]
    lines += ["", "## Finding Types", ""]
    lines += [f"- `{finding_type}`: `{count}`" for finding_type, count in type_counts.most_common()]
    lines += ["", "## Next Action", "", "Start with MUST_FLAG_NEVER_USED and CRITICAL_180_DAYS. Validate owners before disabling or deleting anything."]
    (output_dir / "unused_access_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = ensure_output_dir(args.output_dir)
    session = build_session(args.profile, args.region)
    caller = get_caller(session, args.profile, args.region)
    client = access_analyzer_client(session)
    analyzer = select_analyzer(list_analyzers(client), args.analyzer_name, args.analyzer_arn, expected="unused")
    confirm_analyzer(analyzer, expected="unused", assume_yes=args.yes)

    findings = collect_unused_findings(
        client,
        analyzer.arn,
        active_only=not args.include_archived,
        include_details=not args.no_details,
        max_findings=args.max_findings,
    )

    fieldnames = list(UnusedFinding.__dataclass_fields__.keys())
    rows = [f.to_csv_row() for f in findings]
    write_csv(output_dir / "unused_access_findings.csv", rows, fieldnames)
    write_csv(output_dir / "unused_top_accounts.csv", counter_rows(Counter(f.account for f in findings), "account"), ["account", "count"])
    write_csv(output_dir / "unused_top_finding_types.csv", counter_rows(Counter(f.finding_type for f in findings), "finding_type"), ["finding_type", "count"])
    write_csv(output_dir / "unused_roles.csv", [r for r in rows if r["finding_type"] == "UnusedIAMRole"], fieldnames)
    write_csv(output_dir / "unused_access_keys.csv", [r for r in rows if r["finding_type"] == "UnusedIAMUserAccessKey"], fieldnames)
    write_csv(output_dir / "unused_permissions.csv", [r for r in rows if r["finding_type"] == "UnusedPermission"], fieldnames)
    write_summary(output_dir, caller, analyzer, findings)

    print(f"Exported {len(findings)} unused-access findings to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
