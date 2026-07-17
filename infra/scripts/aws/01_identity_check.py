#!/usr/bin/env python3
"""Print the AWS identity, account, region, and profile for the active session."""

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
    BotoCoreError = ClientError = NoCredentialsError = ProfileNotFound = Exception


@dataclass(frozen=True)
class AwsIdentity:
    account: str
    arn: str
    user_id: str
    region: str
    profile: str
    checked_at: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show the AWS identity used by boto3 before running AWS automation."
    )
    parser.add_argument("--profile", help="AWS profile name, for example future-standard-dev.")
    parser.add_argument("--region", default="us-east-1", help="AWS region. Default: us-east-1.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args()


def require_boto3() -> None:
    if boto3 is None:
        raise RuntimeError("boto3 is not installed. Install boto3 before running AWS scripts.")


def build_session(profile: str | None, region: str) -> Any:
    require_boto3()
    return boto3.Session(profile_name=profile, region_name=region)


def get_identity(session: Any, profile: str | None, region: str) -> AwsIdentity:
    response: dict[str, Any] = session.client("sts").get_caller_identity()
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


if __name__ == "__main__":
    raise SystemExit(main())
