#!/usr/bin/env bash
set -euo pipefail

# Future Standard Access Analyzer report runner.
# Default credential flow: paste temporary AWS credentials into the terminal.
# Optional named profile flow: set AWS_PROFILE_NAME if you actually use profiles.

REGION="${AWS_REGION:-us-east-1}"
EXTERNAL_ANALYZER_NAME="${EXTERNAL_ANALYZER_NAME:-}"
UNUSED_ANALYZER_NAME="${UNUSED_ANALYZER_NAME:-}"
PROFILE_ARGS=()

if [[ -n "${AWS_PROFILE_NAME:-}" ]]; then
  PROFILE_ARGS=(--profile "$AWS_PROFILE_NAME")
fi

if [[ -z "$EXTERNAL_ANALYZER_NAME" || -z "$UNUSED_ANALYZER_NAME" ]]; then
  echo "Set EXTERNAL_ANALYZER_NAME and UNUSED_ANALYZER_NAME first." >&2
  echo "First run:" >&2
  echo "  python3 infra/scripts/futurestandard/00_discover_analyzers.py --region $REGION" >&2
  exit 2
fi

python3 infra/scripts/futurestandard/01_external_access_report.py   "${PROFILE_ARGS[@]}"   --region "$REGION"   --analyzer-name "$EXTERNAL_ANALYZER_NAME"   --yes

python3 infra/scripts/futurestandard/02_unused_access_report.py   "${PROFILE_ARGS[@]}"   --region "$REGION"   --analyzer-name "$UNUSED_ANALYZER_NAME"   --yes
