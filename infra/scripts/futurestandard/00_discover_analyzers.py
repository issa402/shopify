#!/usr/bin/env python3
"""Discover IAM Access Analyzer analyzers before running reports.

Run this first. The purpose is to prevent the common mistake of using the
UnusedAccess analyzer when you meant to use the resource/external analyzer, or
using the resource analyzer when you meant to report unused roles/keys.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from access_analyzer_common import (
    DEFAULT_REGION,
    access_analyzer_client,
    build_session,
    get_caller,
    list_analyzers,
    print_analyzers,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List IAM Access Analyzer analyzers safely.")
    parser.add_argument("--profile", help="Optional AWS named profile. Omit this when using pasted AWS env tokens.")
    parser.add_argument("--region", default=DEFAULT_REGION, help="AWS region. Default: us-east-1.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    session = build_session(args.profile, args.region)
    caller = get_caller(session, args.profile, args.region)
    client = access_analyzer_client(session)
    analyzers = list_analyzers(client)

    if args.json:
        print(json.dumps({"caller": asdict(caller), "analyzers": [asdict(a) for a in analyzers]}, indent=2))
        return 0

    print("AWS caller")
    print("-" * 80)
    print(f"account={caller.account}")
    print(f"arn={caller.arn}")
    print(f"region={caller.region}")
    print(f"profile={caller.profile}")
    print()
    print_analyzers(analyzers)
    print()
    print("Question to answer before the next script:")
    print("- Which analyzer is the resource/external access analyzer?")
    print("- Which analyzer is the unused-access analyzer?")
    print("- Copy the exact name or ARN. Do not use analyzer index 0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
