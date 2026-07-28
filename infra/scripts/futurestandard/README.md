# Future Standard Access Analyzer Task

Purpose: build a read-only reporting workflow for IAM Access Analyzer findings in `us-east-1`.

## The Problem

There are many AWS accounts with access that may be too broad, stale, or outside the organization. The work is not to delete anything first. The work is:

1. Confirm the correct analyzer.
2. Export raw evidence.
3. Group findings by account, resource type, finding type, and principal.
4. Rank the accounts/resources that need human review first.
5. Produce a report that can be given back to the security/shared-services team.

## Two Analyzer Pipelines

Do not mix these up.

| Pipeline | Analyzer | API | Main Question |
|---|---|---|---|
| External/resource access | Resource analyzer / organization analyzer | `list_findings` | Who outside the org or public internet can access resources? |
| Unused access | UnusedAccess analyzer | `list_findings_v2` + optional `get_finding_v2` | Which roles, access keys, users, or permissions are stale/unused? |

Before running reports, always ask:

```text
Am I using the resource/external analyzer or the unused-access analyzer?
Does the selected analyzer name/ARN match the dashboard I am reporting from?
```

## Files

- `00_discover_analyzers.py` - prints identity and all analyzers so you can choose the right one.
- `01_external_access_report.py` - exports active external/resource access findings.
- `02_unused_access_report.py` - exports unused roles, unused keys, and unused permissions.
- `access_analyzer_common.py` - shared boto3/session/analyzer/report helpers.
- `run_access_analyzer_reports.sh` - wrapper once analyzer names are known.

## Recommended Workflow

1. Discover analyzers.

```bash
python3 infra/scripts/futurestandard/00_discover_analyzers.py   --profile future-standard-readonly   --region us-east-1
```

2. Pick the resource/external analyzer by exact name or ARN.

```bash
python3 infra/scripts/futurestandard/01_external_access_report.py   --profile future-standard-readonly   --region us-east-1   --analyzer-name "ConsoleAnalyzer-EXACT-NAME"   --yes
```

3. Pick the unused-access analyzer by exact name or ARN.

```bash
python3 infra/scripts/futurestandard/02_unused_access_report.py   --profile future-standard-readonly   --region us-east-1   --analyzer-name "UnusedAccess-ConsoleAnalyzer-EXACT-NAME"   --yes
```

## Report Outputs

By default reports go to:

```text
infra/reports/futurestandard/access-analyzer/
```

External/resource report produces:

- `external_access_findings.csv`
- `external_top_accounts.csv`
- `external_top_resource_types.csv`
- `external_top_external_principals.csv`
- `external_grouped_account_resource_types.csv`
- `external_access_summary.md`

Unused access report produces:

- `unused_access_findings.csv`
- `unused_top_accounts.csv`
- `unused_top_finding_types.csv`
- `unused_roles.csv`
- `unused_access_keys.csv`
- `unused_permissions.csv`
- `unused_access_summary.md`

## What To Report Back

For external/resource access:

```text
Top accounts by active findings
Top resource types: S3, IAM Role, KMS key, SQS, SNS, etc.
Top external principals
Grouped count by account + resource type
Example rows with account, resource, type, principal, finding ID
```

For unused access:

```text
Unused roles by account
Unused access keys by user/account/key age/last used
Unused permissions by account/resource
Criticality: MUST_FLAG, CRITICAL, WARNING, OK
Recommendation: review, disable, rotate, remove permissions, or validate exception
```

## Criticality Rules Used

Access keys:

- `MUST_FLAG_NEVER_USED`: never used and created more than 150 days ago.
- `CRITICAL_180_DAYS`: last used more than 180 days ago.
- `WARNING_90_DAYS`: last used 90-179 days ago.
- `OK_RECENT`: last used less than 90 days ago.

Unused roles / permissions:

- `MUST_FLAG_NEVER_USED`: never used and created more than 150 days ago.
- `FLAG_130_DAYS`: unused for 130+ days.
- `WARNING_90_DAYS`: unused for 90+ days.
- `OK_RECENT_OR_NEW`: not old enough to be urgent.

## Coding Mindset

Every script follows this pattern:

```text
identity -> select analyzer -> confirm analyzer -> collect findings -> normalize rows -> group/rank -> export evidence
```

Do not skip normalization. AWS responses are nested and service-specific. Dataclasses make the report rows predictable.
