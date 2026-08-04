#!/usr/bin/env python3
"""Guided AWS identity check practice script.

This file is intentionally written as a learning file:
1. Each section starts with how to think about the infra problem.
2. You try writing that section yourself.
3. The working reference code appears a few lines later.

The script is still runnable. It is read-only and only calls AWS STS
get_caller_identity.
"""

# =============================================================================
# STEP 1: IMPORTS
# =============================================================================
# PLAN:
# You are writing a CLI infrastructure script.
# Ask: what do I need this script to do?
# - parse command-line options: argparse
# - print JSON for automation: json
# - print clean errors to stderr: sys
# - model the output cleanly: dataclass/asdict
# - timestamp the report: datetime/timezone
# - type AWS responses without overcomplicating: Any
# - talk to AWS: boto3
# - fail clearly for AWS config/API problems: botocore exceptions
#
# TRY IT YOURSELF:
# Write the imports before looking below.
#
#
#
# REFERENCE IMPORTS:
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, ProfileNotFound
except ImportError:
    boto3 = None

    class BotoCoreError(Exception):
        pass

    class ClientError(Exception):
        pass

    class NoCredentialsError(Exception):
        pass

    class ProfileNotFound(Exception):
        pass


# =============================================================================
# STEP 2: DEFINE THE REPORT SHAPE
# =============================================================================
# PLAN:
# Before calling AWS, decide what a successful answer looks like.
# The operational question is:
# "Which AWS identity, profile, and region is this script using?"
#
# The report should include:
# - account: AWS account ID
# - arn: exact IAM user/role ARN
# - user_id: AWS user/role session ID
# - region: region the session was built with
# - profile: AWS CLI profile used, or default
# - checked_at: timestamp for evidence
#
# Use frozen=True because this is a report object. Do not mutate it.
#
# TRY IT YOURSELF:
# Write the dataclass before looking below.
#
#
#
# REFERENCE CODE:
@dataclass(frozen=True)
class AwsIdentity:
    account: str
    arn: str
    user_id: str
    region: str
    profile: str
    checked_at: str


# =============================================================================
# STEP 3: PARSE CLI ARGUMENTS
# =============================================================================
# PLAN:
# This script should not hide AWS defaults from you.
# Make account context explicit by accepting:
# - --profile: which AWS CLI profile to use
# - --region: which region to build the boto3 session with
# - --format: text for humans, json for automation
#
# Infra intuition:
# Hidden defaults cause mistakes. Explicit profile/region builds discipline.
#
# TRY IT YOURSELF:
# Write parse_args() before looking below.
#
#
#
# REFERENCE CODE:
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show the AWS identity used by boto3 before running AWS automation."
    )
    parser.add_argument("--profile", help="AWS profile name, for example future-standard-dev.")
    parser.add_argument("--region", default="us-east-1", help="AWS region. Default: us-east-1.")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Default: text.",
    )
    return parser.parse_args()


# =============================================================================
# STEP 4: BUILD THE BOTO3 SESSION
# =============================================================================
# PLAN:
# A boto3 Session represents the AWS config context:
# profile + region + credentials provider chain.
#
# Keep it in its own function because every future AWS script will reuse this.
# Later scripts can call build_session() before inventory/security/observability.
#
# TRY IT YOURSELF:
# Write build_session(profile, region) before looking below.
#
#
#
# REFERENCE CODE:
def require_boto3() -> None:
    if boto3 is None:
        raise RuntimeError("boto3 is not installed. Install boto3 before running AWS identity checks.")


def build_session(profile: str | None, region: str) -> Any:
    require_boto3()
    return boto3.Session(profile_name=profile, region_name=region)


# =============================================================================
# STEP 5: CALL STS AND VALIDATE THE RESPONSE
# =============================================================================
# PLAN:
# AWS STS get_caller_identity is the safest first API call.
# It answers:
# - what account am I in?
# - what role/user am I using?
# - what identity did AWS resolve from my local config?
#
# Do not print raw AWS responses directly.
# Convert the response into AwsIdentity so the script has a clean contract.
#
# Also validate required keys. If Account/Arn/UserId are missing, fail clearly.
#
# TRY IT YOURSELF:
# Write get_identity(session, profile, region) before looking below.
#
#
#
# REFERENCE CODE:
def get_identity(session: Any, profile: str | None, region: str) -> AwsIdentity:
    sts = session.client("sts")
    response: dict[str, Any] = sts.get_caller_identity()

    account = response.get("Account")
    arn = response.get("Arn")
    user_id = response.get("UserId")

    if not account or not arn or not user_id:
        raise RuntimeError("AWS STS response was missing Account, Arn, or UserId.")

    return AwsIdentity(
        account=account,
        arn=arn,
        user_id=user_id,
        region=region,
        profile=profile or "default",
        checked_at=datetime.now(timezone.utc).isoformat(),
    )


# =============================================================================
# STEP 6: PRINT HUMAN OR MACHINE OUTPUT
# =============================================================================
# PLAN:
# Infra scripts should support two common audiences:
# - humans reading terminal output
# - other tools reading JSON
#
# If --format json, use dataclasses.asdict() and json.dumps().
# Otherwise print aligned human-readable text.
#
# TRY IT YOURSELF:
# Write print_identity(identity, output_format) before looking below.
#
#
#
# REFERENCE CODE:
def print_identity(identity: AwsIdentity, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(asdict(identity), indent=2))
        return

    print("AWS identity check")
    print(f"  account:    {identity.account}")
    print(f"  arn:        {identity.arn}")
    print(f"  user_id:    {identity.user_id}")
    print(f"  region:     {identity.region}")
    print(f"  profile:    {identity.profile}")
    print(f"  checked_at: {identity.checked_at}")


# =============================================================================
# STEP 7: MAIN FLOW AND ERROR HANDLING
# =============================================================================
# PLAN:
# main() is the operator workflow:
# 1. parse CLI args
# 2. build session
# 3. call STS
# 4. print report
# 5. return a shell-friendly exit code
#
# Catch specific exceptions:
# - ProfileNotFound: the profile name is wrong/missing
# - NoCredentialsError: credentials are not configured
# - ClientError/BotoCoreError: AWS or botocore failed
# - RuntimeError: our own validation failed
#
# Infra intuition:
# A good infrastructure script should fail clearly. The person running it
# should know what to fix next.
#
# TRY IT YOURSELF:
# Write main() before looking below.
#
#
#
# REFERENCE CODE:
def main() -> int:
    args = parse_args()

    try:
        session = build_session(args.profile, args.region)
        identity = get_identity(session, args.profile, args.region)
    except ProfileNotFound as error:
        print(f"ERROR: AWS profile not found: {error}", file=sys.stderr)
        return 1
    except NoCredentialsError:
        print("ERROR: No AWS credentials found. Configure AWS CLI credentials first.", file=sys.stderr)
        return 1
    except (ClientError, BotoCoreError, RuntimeError) as error:
        print(f"ERROR: AWS identity check failed: {error}", file=sys.stderr)
        return 1

    print_identity(identity, args.format)
    return 0


# =============================================================================
# STEP 8: SCRIPT ENTRYPOINT
# =============================================================================
# PLAN:
# Make the file runnable from the shell.
# main() returns an int, and SystemExit turns that into the process exit code.
# This matters for CI and future automation.
#
# TRY IT YOURSELF:
# Write the entrypoint before looking below.
#
#
#
# REFERENCE CODE:
if __name__ == "__main__":
    raise SystemExit(main())


# =============================================================================
# PRACTICE COMMANDS
# =============================================================================
# 1. Check help output:
#
#    python3 infra/scripts/aws/01_identity_check.py --help
#
# 2. Check syntax:
#
#    python3 -m py_compile infra/scripts/aws/01_identity_check.py
#
# 3. Run later when AWS is configured:
#
#    python3 infra/scripts/aws/01_identity_check.py --profile <profile-name> --region us-east-1
#
# 4. JSON output for automation:
#
#    python3 infra/scripts/aws/01_identity_check.py --profile <profile-name> --region us-east-1 --format json
#
# DO NOT move to inventory/security/observability until this identity output
# makes sense. Professional habit:
#
#    prove identity -> inventory -> security -> observability -> IaC
