#!/usr/bin/env python3
"""Read-only AWS inventory starter template.

This script is intentionally safe: it only reads metadata, prints the caller
identity first, and does not create/update/delete AWS resources.
"""

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
except ImportError:  # lets --help still show useful info in bare environments
    boto3 = None
    BotoCoreError = ClientError = NoCredentialsError = ProfileNotFound = Exception


@dataclass(frozen=True)
class AwsCaller:
    account: str
    arn: str
    user_id: str


@dataclass(frozen=True)
class AwsInventoryReport:
    checked_at: str
    profile: str
    region: str
    caller: AwsCaller
    ec2_instances: list[dict[str, Any]]
    rds_instances: list[dict[str, Any]]
    s3_buckets: list[dict[str, Any]]
    cloudwatch_log_groups: list[dict[str, Any]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only AWS inventory starter.")
    parser.add_argument("--profile", help="AWS profile name.")
    parser.add_argument("--region", default="us-east-1", help="AWS region. Default: us-east-1.")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    return parser.parse_args()


def require_boto3() -> None:
    if boto3 is None:
        raise RuntimeError("boto3 is not installed. Install it before running AWS inventory scripts.")


def get_caller(session: Any) -> AwsCaller:
    response = session.client("sts").get_caller_identity()
    return AwsCaller(
        account=response.get("Account", "unknown"),
        arn=response.get("Arn", "unknown"),
        user_id=response.get("UserId", "unknown"),
    )


def list_ec2_instances(session: Any) -> list[dict[str, Any]]:
    ec2 = session.client("ec2")
    instances = []
    for page in ec2.get_paginator("describe_instances").paginate():
        for reservation in page.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instances.append({
                    "instance_id": instance.get("InstanceId"),
                    "state": instance.get("State", {}).get("Name"),
                    "type": instance.get("InstanceType"),
                    "private_ip": instance.get("PrivateIpAddress"),
                    "public_ip": instance.get("PublicIpAddress"),
                    "tags": instance.get("Tags", []),
                })
    return instances


def list_rds_instances(session: Any) -> list[dict[str, Any]]:
    rds = session.client("rds")
    instances = []
    for page in rds.get_paginator("describe_db_instances").paginate():
        for db in page.get("DBInstances", []):
            instances.append({
                "db_instance_identifier": db.get("DBInstanceIdentifier"),
                "engine": db.get("Engine"),
                "status": db.get("DBInstanceStatus"),
                "publicly_accessible": db.get("PubliclyAccessible"),
                "multi_az": db.get("MultiAZ"),
            })
    return instances


def list_s3_buckets(session: Any) -> list[dict[str, Any]]:
    s3 = session.client("s3")
    return [
        {"name": bucket.get("Name"), "created": str(bucket.get("CreationDate"))}
        for bucket in s3.list_buckets().get("Buckets", [])
    ]


def list_log_groups(session: Any) -> list[dict[str, Any]]:
    logs = session.client("logs")
    groups = []
    for page in logs.get_paginator("describe_log_groups").paginate():
        for group in page.get("logGroups", []):
            groups.append({
                "log_group_name": group.get("logGroupName"),
                "retention_in_days": group.get("retentionInDays"),
                "stored_bytes": group.get("storedBytes"),
            })
    return groups


def build_report(profile: str | None, region: str) -> AwsInventoryReport:
    require_boto3()
    session = boto3.Session(profile_name=profile, region_name=region)
    caller = get_caller(session)
    return AwsInventoryReport(
        checked_at=datetime.now(timezone.utc).isoformat(),
        profile=profile or "default",
        region=region,
        caller=caller,
        ec2_instances=list_ec2_instances(session),
        rds_instances=list_rds_instances(session),
        s3_buckets=list_s3_buckets(session),
        cloudwatch_log_groups=list_log_groups(session),
    )


def print_markdown(report: AwsInventoryReport) -> None:
    print("# AWS Inventory Report\n")
    print(f"Checked at: `{report.checked_at}`")
    print(f"Profile: `{report.profile}`")
    print(f"Region: `{report.region}`")
    print(f"Account: `{report.caller.account}`")
    print(f"ARN: `{report.caller.arn}`\n")
    sections = [
        ("EC2 Instances", report.ec2_instances),
        ("RDS Instances", report.rds_instances),
        ("S3 Buckets", report.s3_buckets),
        ("CloudWatch Log Groups", report.cloudwatch_log_groups),
    ]
    for title, items in sections:
        print(f"## {title}\n")
        if not items:
            print("No items found.\n")
            continue
        for item in items:
            print(f"- `{json.dumps(item, default=str)}`")
        print()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args.profile, args.region)
    except ProfileNotFound as error:
        print(f"ERROR: AWS profile not found: {error}", file=sys.stderr)
        return 1
    except NoCredentialsError:
        print("ERROR: No AWS credentials found. Configure AWS CLI credentials first.", file=sys.stderr)
        return 1
    except (ClientError, BotoCoreError, RuntimeError) as error:
        print(f"ERROR: AWS inventory failed: {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, default=str))
    else:
        print_markdown(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
