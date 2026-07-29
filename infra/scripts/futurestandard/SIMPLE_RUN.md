# Simple Access Analyzer Run

Paste AWS temp credentials into the terminal, then run one command:

```bash
python3 infra/scripts/futurestandard/quick_access_analyzer_report.py
```

This creates CSVs in:

```text
infra/reports/futurestandard/access-analyzer/
```

## What The File Does

`quick_access_analyzer_report.py`

- Finds `ConsoleAnalyzer-*` automatically.
- Finds `UnusedAccess-ConsoleAnalyzer-*` automatically.
- Uses `list_findings` for external/resource access.
- Uses `list_findings_v2` for unused access.
- Exports simple CSVs.
- Does not modify AWS.

## CSVs Created

External/resource access:

- `external_access_findings.csv`
- `external_top_accounts.csv`
- `external_top_resource_types.csv`
- `external_top_principals.csv`
- `external_group_by_account_and_type.csv`
- `external_group_by_account_type_resource.csv`

Unused access:

- `unused_access_findings.csv`
- `unused_roles.csv`
- `unused_access_keys.csv`
- `unused_permissions.csv`
- `unused_top_accounts.csv`
- `unused_top_finding_types.csv`
- `unused_group_by_account_and_finding_type.csv`
- `unused_candidates_over_5_months.csv`
- `unused_permissions_candidates.csv`

## Future Remediation Use

Yes, these CSVs are meant to feed a future approval/remediation workflow. Start with the `must_flag` CSVs, get manager/account-owner approval, then a later script can disable keys, reduce policies, or delete unused roles. Do not remediate directly from this export script.

## If The Script Looked Frozen

If it prints `External/resource findings: ...` and then seems stuck, the old version was doing one `get_finding_v2` call for every unused finding. With thousands of unused findings, that is slow. The current version skips those detail calls by default and should finish much faster.

Only use deep detail mode for smaller runs:

```bash
ACCESS_ANALYZER_FETCH_DETAILS=1 python3 infra/scripts/futurestandard/quick_access_analyzer_report.py
```
