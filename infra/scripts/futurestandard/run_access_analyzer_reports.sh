#!/usr/bin/env bash
set -euo pipefail

# Future Standard Access Analyzer report runner.
# Fill these in after running 00_discover_analyzers.py.

PROFILE="${AWS_PROFILE_NAME:-future-standard-readonly}"
REGION="${AWS_REGION:-us-east-1}"
EXTERNAL_ANALYZER_NAME="${EXTERNAL_ANALYZER_NAME:-}"
UNUSED_ANALYZER_NAME="${UNUSED_ANALYZER_NAME:-}"

if [[ -z "$EXTERNAL_ANALYZER_NAME" || -z "$UNUSED_ANALYZER_NAME" ]]; then
  echo "Set EXTERNAL_ANALYZER_NAME and UNUSED_ANALYZER_NAME first." >&2
  echo "Run: python3 infra/scripts/futurestandard/00_discover_analyzers.py --profile $PROFILE --region $REGION" >&2
  exit 2
fi

python3 infra/scripts/futurestandard/01_external_access_report.py   --profile "$PROFILE"   --region "$REGION"   --analyzer-name "$EXTERNAL_ANALYZER_NAME"   --yes

python3 infra/scripts/futurestandard/02_unused_access_report.py   --profile "$PROFILE"   --region "$REGION"   --analyzer-name "$UNUSED_ANALYZER_NAME"   --yes
