#!/usr/bin/env python3
"""Export active external/resource access findings from IAM Access Analyzer.

Use this for the resource analyzer, not the UnusedAccess analyzer.
Outputs grouped account/resource/principal reports for external/public access.
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
    ensure_output_dir,
    get_caller,
    json_dumps,
    list_analyzers,
    select_analyzer,
    write_csv,
)


@dataclass(frozen=True)
class ExternalFinding:
    account: str
    resource: str
    resource_type: str
    finding_id: str
    status: str
    is_public: bool
    principal: str
    condition: str
    action: str
    created_at: str
    updated_at: str

    def to_csv_row(self) -> dict[str, Any]:
        return asdict(self)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report active external/resource access findings.")
    parser.add_argument("--profile", help="Optional AWS named profile. Omit this when using pasted AWS env tokens.")
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--analyzer-name", help="Exact resource/external analyzer name.")
    parser.add_argument("--analyzer-arn", help="Exact resource/external analyzer ARN.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--include-archived", action="store_true", help="Include non-ACTIVE findings.")
    parser.add_argument("--yes", action="store_true", help="Confirm the selected analyzer without interactive prompt.")
    return parser.parse_args()


def collect_external_findings(client: Any, analyzer_arn: str, active_only: bool) -> list[ExternalFinding]:
    """Collect findings using list_findings for resource/external analyzer results."""
    findings: list[ExternalFinding] = []
    kwargs: dict[str, Any] = {"analyzerArn": analyzer_arn}
    if active_only:
        kwargs["filter"] = {"status": {"eq": ["ACTIVE"]}}

    paginator = client.get_paginator("list_findings")
    for page in paginator.paginate(**kwargs):
        for item in page.get("findings", []):
            findings.append(
                ExternalFinding(
                    account=item.get("resourceOwnerAccount", "UNKNOWN"),
                    resource=item.get("resource", ""),
                    resource_type=item.get("resourceType", ""),
                    finding_id=item.get("id", ""),
                    status=item.get("status", ""),
                    is_public=bool(item.get("isPublic", False)),
                    principal=json_dumps(item.get("principal", {})),
                    condition=json_dumps(item.get("condition", {})),
                    action=json_dumps(item.get("action", [])),
                    created_at=str(item.get("createdAt", "")),
                    updated_at=str(item.get("updatedAt", "")),
                )
            )
    return findings


def counter_rows(counter: Counter[str], key_name: str) -> list[dict[str, Any]]:
    return [{key_name: key, "count": count} for key, count in counter.most_common()]


def grouped_account_resource_rows(findings: list[ExternalFinding]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str]] = Counter((f.account, f.resource_type) for f in findings)
    return [
        {"account": account, "resource_type": resource_type, "count": count}
        for (account, resource_type), count in counts.most_common()
    ]


def write_summary(output_dir: Path, caller: Any, analyzer: Any, findings: list[ExternalFinding]) -> None:
    account_counts = Counter(f.account for f in findings)
    resource_counts = Counter(f.resource_type for f in findings)
    principal_counts = Counter(f.principal for f in findings)
    public_count = sum(1 for f in findings if f.is_public)

    lines = [
        "# External Access Findings Summary",
        "",
        "## Analyzer Check",
        "",
        f"- Caller account: `{caller.account}`",
        f"- Caller ARN: `{caller.arn}`",
        f"- Analyzer name: `{analyzer.name}`",
        f"- Analyzer ARN: `{analyzer.arn}`",
        "- API used: `accessanalyzer.list_findings`",
        "- Intended analyzer: resource/external access analyzer",
        "",
        "## Totals",
        "",
        f"- Active findings exported: `{len(findings)}`",
        f"- Public findings: `{public_count}`",
        "",
        "## Top Accounts",
        "",
    ]
    lines += [f"- `{account}`: `{count}`" for account, count in account_counts.most_common(10)]
    lines += ["", "## Top Resource Types", ""]
    lines += [f"- `{resource}`: `{count}`" for resource, count in resource_counts.most_common(10)]
    lines += ["", "## Top External Principals", ""]
    lines += [f"- `{principal}`: `{count}`" for principal, count in principal_counts.most_common(10)]
    lines += ["", "## Next Action", "", "Group by account owner and validate whether each principal is approved, public, vendor, cross-account internal, or unknown."]
    (output_dir / "external_access_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = ensure_output_dir(args.output_dir)
    session = build_session(args.profile, args.region)
    caller = get_caller(session, args.profile, args.region)
    client = access_analyzer_client(session)
    analyzer = select_analyzer(list_analyzers(client), args.analyzer_name, args.analyzer_arn, expected="external")
    confirm_analyzer(analyzer, expected="external", assume_yes=args.yes)

    findings = collect_external_findings(client, analyzer.arn, active_only=not args.include_archived)
    write_csv(output_dir / "external_access_findings.csv", [f.to_csv_row() for f in findings], list(ExternalFinding.__dataclass_fields__.keys()))
    write_csv(output_dir / "external_top_accounts.csv", counter_rows(Counter(f.account for f in findings), "account"), ["account", "count"])
    write_csv(output_dir / "external_top_resource_types.csv", counter_rows(Counter(f.resource_type for f in findings), "resource_type"), ["resource_type", "count"])
    write_csv(output_dir / "external_top_external_principals.csv", counter_rows(Counter(f.principal for f in findings), "principal"), ["principal", "count"])
    write_csv(output_dir / "external_grouped_account_resource_types.csv", grouped_account_resource_rows(findings), ["account", "resource_type", "count"])
    write_summary(output_dir, caller, analyzer, findings)

    print(f"Exported {len(findings)} external/resource findings to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
