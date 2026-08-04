# 01 Identity Check Worksheet

## Why This Is The First AWS File

The most important AWS starter file is:

```text
infra/scripts/aws/01_identity_check.py
```

Reason:

> Before you inventory, audit, scan, or automate anything in AWS, you must know which AWS account, role/user, profile, and region your script is using.

At Future Standard, this matters because using the wrong AWS account could mean:

- reading the wrong environment
- reporting bad inventory
- misunderstanding production vs dev
- accidentally building confidence from the wrong data
- eventually making a dangerous change in the wrong place

So the first AWS/boto3 muscle is:

```text
Can I safely prove who I am in AWS before doing anything else?
```

This script should be read-only. It should only call AWS STS `get_caller_identity`.

## How To Use This Worksheet

Do not copy the reference answer first.

For each section:

1. Read the plan.
2. Try to write that part in `01_identity_check.py` yourself.
3. Then compare against the reference lines below it.
4. If yours is different but works and is readable, that is fine.

The goal is not memorizing code. The goal is learning the infra thought process.

---

## Step 1: Define The Question

Think first:

```text
Question:
Which AWS identity is this script using?

Source of truth:
AWS STS

Read-only API:
get_caller_identity

Output:
account, ARN, user_id, profile, region, checked_at

Risk reduced:
prevents running inventory/audit logic in the wrong AWS account or role
```

Do not code until you can say that out loud.

Reference mental model:

```text
AWS profile + region -> boto3 Session -> STS client -> get_caller_identity -> structured report
```

---

## Step 2: Imports

Your plan:

You need imports for:

- CLI arguments
- JSON output
- structured result object
- timestamp
- stderr/error handling
- optional types
- boto3
- botocore exceptions

Try to write the imports yourself first.



Reference imports:

```python
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, ProfileNotFound
```

Why these matter:

- `argparse`: lets you pass `--profile`, `--region`, `--format`
- `json`: lets scripts output machine-readable data
- `sys`: lets errors go to `stderr`
- `dataclass`: gives you a clean report object
- `datetime/timezone`: records when the check ran
- `Any`: types AWS responses without overcomplicating first version
- `boto3`: AWS SDK
- `botocore.exceptions`: clear errors for missing profile/credentials/API failures

---

## Step 3: Result Shape

Your plan:

Before calling AWS, define what a successful answer looks like.

Fields you need:

```text
account
arn
user_id
region
profile
checked_at
```

Make it immutable with `frozen=True` because this is a report, not a thing you mutate.



Reference code:

```python
@dataclass(frozen=True)
class AwsIdentity:
    account: str
    arn: str
    user_id: str
    region: str
    profile: str
    checked_at: str
```

Infra intuition:

> Good infra scripts turn messy API responses into clear structured reports.

---

## Step 4: CLI Arguments

Your plan:

The script should let you choose:

```text
--profile   which AWS CLI profile to use
--region    AWS region, default us-east-1
--format    text or json
```

The script should be runnable like:

```bash
python3 infra/scripts/aws/01_identity_check.py --profile future-standard-dev --region us-east-1
```

Try to write `parse_args()` yourself.



Reference code:

```python
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
```

Common mistake to avoid:

```text
argparse uses choices=, not choice=
```

---

## Step 5: Build The boto3 Session

Your plan:

A boto3 Session represents:

```text
profile + region + credentials/config source
```

Keep this in its own function because every future AWS script will reuse the same pattern.



Reference code:

```python
def build_session(profile: str | None, region: str) -> boto3.Session:
    return boto3.Session(profile_name=profile, region_name=region)
```

Infra intuition:

> Every AWS script should make account/profile/region explicit. Hidden defaults create confusion.

---

## Step 6: Call STS Safely

Your plan:

Use the session to create an STS client.

Call:

```text
get_caller_identity()
```

Extract:

```text
Account
Arn
UserId
```

Validate they exist. If AWS returns something unexpected, fail clearly.



Reference code:

```python
def get_identity(session: boto3.Session, profile: str | None, region: str) -> AwsIdentity:
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
```

Infra intuition:

> Do not just print raw AWS responses. Convert them into a small report that answers the operational question.

---

## Step 7: Print Text Or JSON

Your plan:

Humans like text.

Automation likes JSON.

Support both.

Text should be readable. JSON should use `asdict(identity)`.



Reference code:

```python
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
```

Infra intuition:

> Markdown/text is good for humans. JSON is good when one script feeds another script.

---

## Step 8: Main Function And Error Handling

Your plan:

`main()` should:

1. Parse args.
2. Build session.
3. Get identity.
4. Print identity.
5. Return `0` on success.
6. Return `1` on known failure.

Handle these separately:

```text
ProfileNotFound -> wrong/missing AWS profile
NoCredentialsError -> no credentials configured
ClientError/BotoCoreError -> AWS/API/config failure
RuntimeError -> our own validation failure
```



Reference code:

```python
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
```

Infra intuition:

> A good infra script fails clearly. Silent failure or messy stack traces are bad operator experience.

---

## Step 9: Entrypoint

Your plan:

Make the script executable as a normal Python CLI.



Reference code:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

Why this matters:

```text
main() returns an exit code
SystemExit uses that code for shell/CI behavior
```

---

## Step 10: How To Test Without Real AWS Access

Run help first:

```bash
python3 infra/scripts/aws/01_identity_check.py --help
```

Expected:

```text
usage message shows --profile, --region, --format
```

Run syntax check:

```bash
python3 -m py_compile infra/scripts/aws/01_identity_check.py
```

If you do not have credentials, run:

```bash
python3 infra/scripts/aws/01_identity_check.py
```

Expected:

```text
ERROR: No AWS credentials found. Configure AWS CLI credentials first.
```

That is still a useful result because the script failed clearly.

---

## Step 11: How To Test With AWS Access Later

When AWS CLI is configured:

```bash
python3 infra/scripts/aws/01_identity_check.py --profile <profile-name> --region us-east-1
```

JSON output:

```bash
python3 infra/scripts/aws/01_identity_check.py --profile <profile-name> --region us-east-1 --format json
```

Never continue to inventory/security audit until the identity output makes sense.

Ask yourself:

```text
Is this the right AWS account?
Is this the right role/user?
Is this dev, staging, or production?
Is this read-only?
Is this the region I meant to inspect?
```

---

## Step 12: What Comes After This File

After `01_identity_check.py`, build in this order:

```text
02_vpc_network_inventory.py
03_security_group_audit.py
04_s3_public_access_audit.py
05_inventory.py
06_cloudwatch_observability_audit.py
07_tag_hygiene_report.py
```

But do not skip identity.

The professional habit is:

```text
Prove identity -> inventory -> security -> observability -> IaC
```

