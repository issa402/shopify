
from __future__ import annotations
import os 
import argparse 
import json 
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, ProfileNotFound

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
        description="Show the AWS identity used by boto3 before running AWS automation"
    )
    parser.add_argument("--profile", help="AWS profile name, for example future-standard-dev.")
    parser.add_argument("--region", default="us-east-1", help="AWS region. Default: us-east-1.")
    parser.add_argument(
        "--format", 
        choice=("text", "json"),
        default="text",
        help="Output format. default: text",

        
    )
    return parser.parse_args()

def build_session(profile: str | None, region: str) -> boto3.Session:
    return boto3.Session(profile_name=profile, region_name=region)

def get_identity(session: boto3.Session, profile: str | None, region:str) -> AwsIdentity:
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

def print_identity(identity: AwsIdentity, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(asdict(identity), indent=2))
        return 

    print("AWS identity check")
    print(f"  account: {identity.account}")
    print(f"  arn: {identity.arn}")
    print(f"  user_id: {identity.user_id}")
    print(f"  region:   {identity.region}")
    print(f"  profile:  {identity.profile}")
    print(f"  checked_at:   {identity.checked_at}")


def main() -> int:
    args = parse_args()

    try:
        session = build_session(args.profile, args.region)
        identity = get_identity(session, args.profile, args.region)
    except ProfileNotFound as error:
        print(f"ERROR: AWS profile not found: {error}", file = sys.stderr)
        return 1
    except NoCredentialsError:
        print("ERROR: No AWS credentials found. Configure AWS CLI credentila first.", file=sys.stderr)
        return 1
    except (ClientError, BotoCoreError, RuntimeError) as error:
        print(f"ERROR: AWS identity check failed: {error}",
        file=sys.stderr)
        return 1
    print_identity(identity, args.format)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
    


###python infra/scripts/aws/01_identity_check.py --help

###  Later, when AWS is configured:

  ###python infra/scripts/aws/01_identity_check.py --profile future-
  #standard-dev --region us-east-1

 # or JSON:
#
  #python infra/scripts/aws/01_identity_check.py --profile future-
  #standard-dev --region us-east-1 --format json

# Done. I added a Future Standard field kit under the AWS folder and
#   wired it into the main AWS practice plan.

#   What changed:

#   - shopify/shopify/infra/AWS_SECURITY_OBSERVABILITY_PRACTICE_PLAN.md
#       - Added Future Standard Field Kit links.
#       - Keeps the ordered AWS/security/observability learning path, but
#         now points to concrete templates and scripts.

#   - shopify/shopify/infra/scripts/aws/
#     FUTURE_STANDARD_INFRA_IDEA_PLAYBOOK.md
#       - Plausible Future Standard infra needs.
#       - High-value ideas you can bring.
#       - What to inspect in company repos.
#       - What to do about GitHub teams/projects.
#       - AI-for-infra ideas.
#       - Enterprise/hybrid-cloud strategy notes with sources.

#   - shopify/shopify/infra/scripts/aws/company_repo_discovery.py
#       - Read-only scanner for any company repo checkout.
#       - Finds CI, Docker, Terraform, Kubernetes, scripts, docs,
#         runbooks, monitoring surfaces.

#       - Run it like:

#         python infra/scripts/aws/company_repo_discovery.py /path/to/
#         company/repo --format markdown

#   - shopify/shopify/infra/scripts/aws/01_identity_check.py
#       - Safe AWS identity check.
#       - Prints account, ARN, user ID, profile, region.
#       - No mutation.

#   - shopify/shopify/infra/scripts/aws/05_inventory.py
#       - Read-only AWS inventory starter.
#       - Later can list EC2, RDS, S3, CloudWatch log groups.
#       - Prints identity first.

#   Templates added:

#   - shopify/shopify/infra/scripts/aws/templates/
#     infra_idea_proposal_template.md

#   - shopify/shopify/infra/scripts/aws/templates/
#     github_access_request_template.md

#   - shopify/shopify/infra/scripts/aws/templates/
#     ai_infra_use_case_template.md

#   - shopify/shopify/infra/scripts/aws/templates/
#     company_repo_review_template.md

#   I also verified:

#   python3 -m py_compile ...
#   python3 infra/scripts/aws/05_inventory.py --help
#   python3 infra/scripts/aws/company_repo_discovery.py shopify/shopify
#   --format markdown

#   For your GitHub situation: don’t assume missing teams means something
#   is wrong. Use the access-request template and ask your manager/
#   onboarding buddy which repos, teams, project boards, docs, and
#   runbooks are the official Infrastructure work surfaces. Ask for read-
#   only first.

#   Sources I used for the strategy framing:

#   - AWS Well-Architected:
#     https://aws.amazon.com/architecture/well-architected/

#   - AWS GenAI Lens:

#     https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-le
# ns/generative-ai-lens.html

#   - Google SRE incident guide:

#     https://sre.google/resources/practices-and-processes/incident-manag
# ement-guide/

#   - McKinsey GenAI in operations:

#     https://www.mckinsey.com/capabilities/operations/our-insights/gener
# ative-ai-in-operations-capturing-the-value

# ─ Worked for 9m 37s ───────────────────────
