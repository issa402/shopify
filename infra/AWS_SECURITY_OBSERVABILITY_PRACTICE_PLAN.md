# AWS Security, Observability, and Infra Coding Practice Plan

This file is not another task tracker.

Use it as the AWS/security/observability lens for work that already exists in:

- [FUTURE_STANDARD_INFRA_TASKS.md](/home/iscjmz/shopify/shopify/infra/FUTURE_STANDARD_INFRA_TASKS.md)
- [LEARNING_ROADMAP.md](/home/iscjmz/shopify/shopify/infra/LEARNING_ROADMAP.md)
- [PRACTICE_READY.md](/home/iscjmz/shopify/shopify/infra/PRACTICE_READY.md)
- [practice/github_actions_practice.md](/home/iscjmz/shopify/shopify/infra/practice/github_actions_practice.md)

Those files tell you what to do and in what order. This file tells you how to make that work count for AWS security, observability, and infrastructure engineering.

## Purpose

The goal is to turn the Shopify/Pokemon/NexusOS repo into proof that you can operate software, not just write it.

When you finish an infra task, ask:

- What could fail in production?
- What would expose data, money, or credentials?
- What would I monitor?
- What would I log?
- What would I alert on?
- What would I automate so a human does not have to remember it?
- What evidence would convince a senior engineer this is safe?

## Existing Work Map

Use this mapping instead of creating duplicate assignments.

| Existing work | AWS/security/observability angle |
| --- | --- |
| Runtime architecture and dependency inventory | Identify blast radius, network boundaries, single points of failure, and AWS service equivalents. |
| Health checks and readiness | Define what CloudWatch alarms, load balancer health checks, and deploy gates would need. |
| Graceful shutdown | Practice deployment safety, ECS/Kubernetes termination behavior, and queue-consumer reliability. |
| Structured logging and request IDs | Make incidents traceable across Go, FastAPI, workers, queues, and future AWS logs. |
| RabbitMQ worker reliability | Think like SQS/SNS/EventBridge operations: retries, dead-letter paths, idempotency, and backpressure. |
| Config and secrets hardening | Practice IAM/Secrets Manager/SSM Parameter Store thinking even when running locally. |
| Docker Compose audit | Translate local exposure into security group, subnet, and container runtime risk. |
| Observability basics | Turn health, logs, metrics, and traces into operational evidence. |
| Incident runbook | Prove you can respond under pressure with a repeatable process. |
| Bash and Python operational scripts | Build the muscle for AWS CLI, boto3, CI gates, and repeatable admin work. |
| GitHub Actions practice | Treat CI as the first deployment safety boundary. |




## Future Standard Field Kit

For company-onboarding, idea generation, GitHub access confusion, AI-in-infra proposals, and reusable proposal templates, use:

- [scripts/aws/FUTURE_STANDARD_INFRA_IDEA_PLAYBOOK.md](/home/iscjmz/shopify/shopify/infra/scripts/aws/FUTURE_STANDARD_INFRA_IDEA_PLAYBOOK.md)
- [scripts/aws/company_repo_discovery.py](/home/iscjmz/shopify/shopify/infra/scripts/aws/company_repo_discovery.py)
- [scripts/aws/05_inventory.py](/home/iscjmz/shopify/shopify/infra/scripts/aws/05_inventory.py)
- [scripts/aws/templates/infra_idea_proposal_template.md](/home/iscjmz/shopify/shopify/infra/scripts/aws/templates/infra_idea_proposal_template.md)
- [scripts/aws/templates/github_access_request_template.md](/home/iscjmz/shopify/shopify/infra/scripts/aws/templates/github_access_request_template.md)
- [scripts/aws/templates/ai_infra_use_case_template.md](/home/iscjmz/shopify/shopify/infra/scripts/aws/templates/ai_infra_use_case_template.md)
- [scripts/aws/templates/company_repo_review_template.md](/home/iscjmz/shopify/shopify/infra/scripts/aws/templates/company_repo_review_template.md)

Use this kit when you open a Future Standard repo or project board and need to decide what to inspect, what access to request, what idea to bring, and how to frame it as infrastructure value.

## Start Here: Ordered Practice Path

This is the concrete order. Do not skip around unless the current task is blocked.

You do not need paid AWS on day one. Build the local version first, then build the AWS-ready script in read-only mode so it is ready when credentials exist.

### Session 0 - Set Up The Work Area

Purpose: create the folders where practice work and proof will live.

Work here:

```text
infra/scripts/aws/
infra/scripts/observability/
infra/scripts/security/
infra/scripts/bash/
infra/reports/
infra/runbooks/
```

Do this:

```bash
mkdir -p infra/scripts/aws infra/scripts/observability infra/scripts/security infra/scripts/bash infra/reports infra/runbooks
```

Proof to save:

```text
infra/reports/practice-session-00-setup.md
```

Write:

```text
Future Standard value: Organized operational workspace
Site improvement: Standard place for infra scripts, reports, and runbooks
AWS/security/observability concept learned: operational evidence structure
Evidence produced: folder tree exists
Next operational risk to reduce: no runtime architecture map yet
```

### Session 1 - Runtime Architecture And Dependency Map

Purpose: understand the actual stack before touching AWS.

Start by reading:

```text
Pokemon/docker-compose.yml
Pokemon/server/main.go
Pokemon/server/routes/routes.go
Pokemon/server/config/
Pokemon/services/api-consumer/
services/ai/
docker-compose.yml
```

Create or update:

```text
infra/reports/runtime-architecture-map.md
```

Do this locally:

```bash
docker compose ps
```

If the Pokemon stack uses its own compose file, also run from the right folder:

```bash
docker compose -f Pokemon/docker-compose.yml ps
```

Document:

```text
service name
container name
internal port
published host port
depends on
database/queue/cache dependency
what breaks if this service dies
AWS equivalent
```

AWS-ready script to prepare later:

```text
infra/scripts/aws/01_identity_check.py
```

What it should eventually do:

- call STS `get_caller_identity`
- print account, ARN, user/role, region, profile
- exit before doing anything else if identity is unclear

Run later when AWS exists:

```bash
python infra/scripts/aws/01_identity_check.py --profile future-standard-dev --region us-east-1
```

Official resources:

- AWS STS boto3 reference: https://docs.aws.amazon.com/boto3/latest/reference/services/sts.html
- AWS STS Python examples: https://docs.aws.amazon.com/code-library/latest/ug/python_3_sts_code_examples.html

### Session 2 - Health And Readiness Checks

Purpose: prove the stack is up and ready, not just running.

Create:

```text
infra/scripts/observability/service_health_report.py
infra/reports/health-readiness-report.md
```

Check these local targets if they exist:

```text
Go API health endpoint
FastAPI api-consumer health endpoint
AI FastAPI health endpoint
frontend port
Postgres container status
Redis container status
RabbitMQ container status
```

Expected local command:

```bash
python infra/scripts/observability/service_health_report.py --format markdown > infra/reports/health-readiness-report.md
```

The script should report:

```text
service
endpoint or container
status
latency_ms when HTTP
failure reason
ready/not-ready
```

AWS connection:

- Application Load Balancer health checks
- ECS service health
- CloudWatch alarms
- synthetic checks
- deploy gates

Official resources:

- Amazon CloudWatch documentation: https://docs.aws.amazon.com/cloudwatch/
- CloudWatch Logs getting started: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_GettingStarted.html

### Session 3 - Structured Logging And Request IDs

Purpose: make debugging possible across services.

Inspect:

```text
Pokemon/server/middleware/
Pokemon/server/main.go
Pokemon/services/api-consumer/main.py
services/ai/main.py
```

Create report:

```text
infra/reports/logging-request-id-audit.md
```

Look for:

```text
request_id
method
path
status
latency_ms
service_name
environment
error_code
```

If missing, add the smallest improvement in the app code or document the exact gap.

Expected proof:

```text
sample log line from Go API
sample log line from FastAPI service
what fields are missing
what CloudWatch query would search this later
```

AWS-ready script to prepare later:

```text
infra/scripts/aws/02_cloudwatch_log_groups.py
```

What it should eventually do:

- list CloudWatch log groups for the project prefix
- show retention settings
- flag groups with no retention policy
- output JSON or Markdown

Official resources:

- CloudWatch Logs overview: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html
- Amazon CloudWatch documentation: https://docs.aws.amazon.com/cloudwatch/

### Session 4 - Config And Secrets Hardening

Purpose: reduce credential and unsafe-config risk.

Create:

```text
infra/scripts/security/secret_scan_report.py
infra/reports/secrets-config-report.md
```

Scan:

```text
.env files
compose files
Go config
Python config
GitHub Actions workflows
README examples
```

Expected local command:

```bash
python infra/scripts/security/secret_scan_report.py --format markdown > infra/reports/secrets-config-report.md
```

Detect:

```text
AWS access key patterns
private keys
tokens
password-looking values
committed .env files
broad CORS defaults
default database passwords
missing required env var documentation
```

AWS connection:

- IAM least privilege
- Secrets Manager
- SSM Parameter Store
- environment-specific config

AWS-ready script to prepare later:

```text
infra/scripts/aws/03_secrets_inventory.py
```

What it should eventually do:

- list Secrets Manager secrets with project prefix
- show rotation enabled/disabled
- show last changed date
- never print secret values

Official resources:

- AWS Secrets Manager documentation: https://docs.aws.amazon.com/secretsmanager/
- AWS Well-Architected Security Pillar: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html

### Session 5 - Docker And Container Exposure Audit

Purpose: know what is private, what is public, and what should not be exposed.

Create:

```text
infra/scripts/security/docker_compose_security_audit.py
infra/reports/docker-exposure-audit.md
```

Inspect:

```text
docker-compose.yml
Pokemon/docker-compose.yml
docker-compose.dev.yml if present
```

Expected local command:

```bash
python infra/scripts/security/docker_compose_security_audit.py --format markdown docker-compose.yml Pokemon/docker-compose.yml > infra/reports/docker-exposure-audit.md
```

Check:

```text
published ports
privileged containers
host mounts
missing healthchecks
default passwords
services that should be internal only
restart policies
resource limits
```

AWS connection:

- VPC subnet design
- security groups
- private RDS/Redis
- public load balancer vs private service
- ECS task networking

AWS-ready script to prepare later:

```text
infra/scripts/aws/04_security_group_audit.py
```

What it should eventually do:

- list security groups
- flag 0.0.0.0/0 on SSH, Postgres, Redis, RabbitMQ, admin ports
- flag missing descriptions and missing tags
- output high/medium/low findings

Official resources:

- AWS Security Pillar security foundations: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/security.html
- AWS Well-Architected Security Pillar: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html

### Session 6 - Incident Runbook

Purpose: make troubleshooting repeatable.

Create:

```text
infra/runbooks/incident_response.md
infra/scripts/bash/incident_snapshot.sh
infra/reports/incident-snapshot-example.md
```

The snapshot script should collect:

```text
git commit
docker compose ps
docker compose logs --tail 200
disk usage
memory
listening ports
health report output
recent errors summary
```

Expected local command:

```bash
bash infra/scripts/bash/incident_snapshot.sh
```

AWS connection:

- CloudWatch alarms
- CloudWatch Logs queries
- rollback plan
- backup restore plan
- post-incident review

Official resources:

- Amazon CloudWatch documentation: https://docs.aws.amazon.com/cloudwatch/
- AWS Well-Architected Security Pillar: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html

### Session 7 - Bash And Python Ops Scripts

Purpose: build reusable operational tooling, not random scripts.

Create one small script at a time:

```text
infra/scripts/bash/env_doctor.sh
infra/scripts/bash/deploy_guard.sh
infra/scripts/observability/docker_log_audit.py
infra/scripts/aws/05_inventory.py
```

Rules:

```text
--help works
safe defaults
no secrets printed
clear exit codes
JSON or Markdown output
read-only unless --apply exists
```

Expected local commands:

```bash
bash infra/scripts/bash/env_doctor.sh
python infra/scripts/observability/docker_log_audit.py --tail 200 --format markdown
```

AWS-ready inventory script:

```text
infra/scripts/aws/05_inventory.py
```

What it should eventually list:

```text
EC2 instances
RDS instances
ECR repos
ECS clusters/services if used
S3 buckets
CloudWatch log groups
IAM roles matching project prefixes
```

Official resources:

- Boto3 documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- AWS STS boto3 reference: https://docs.aws.amazon.com/boto3/latest/reference/services/sts.html

### Session 8 - CI And Deploy Safety Checks

Purpose: stop risky changes before they ship.

Create or update:

```text
.github/workflows/infra-security.yml
infra/scripts/bash/deploy_guard.sh
infra/reports/deploy-safety-report.md
```

Local deploy guard should run available checks:

```text
secret scan
Docker exposure audit
health readiness report
log audit
migration safety check if present
unit tests if available
```

Expected local command:

```bash
bash infra/scripts/bash/deploy_guard.sh --dry-run
```

AWS connection:

- deployment gates
- policy-as-code thinking
- environment protection
- least-privilege CI credentials
- pre-production safety checks

Official resources:

- GitHub Actions docs: https://docs.github.com/actions
- AWS Well-Architected Security Pillar: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html

## AWS Script Rule

Every AWS script in this plan must be safe before you have a paid AWS account:

- it must support `--help`
- it must fail clearly if boto3 or credentials are missing
- it must never create, update, or delete resources by default
- it must print the AWS identity before reading account resources
- it must support `--profile` and `--region`
- it must have `--format json` and/or `--format markdown`
- any future mutation must require `--apply`

This lets you write the tooling now and run it later when AWS is available.

## Future Standard High-Value Workstream

This is the main point of the plan: learn AWS, security, and observability while doing work that looks like real Future Standard infrastructure engineering.

Do not treat AWS practice as separate homework. Treat it as a two-for-one loop:

1. Improve the Shopify/Pokemon/NexusOS site or its operational docs.
2. Translate that same improvement into the AWS/security/observability concept Future Standard would care about.
3. Capture proof that the change made the system safer, clearer, easier to debug, or easier to operate.

The highest-value workstream is:

| Priority | Work | Why Future Standard would care | AWS/security/observability connection |
| --- | --- | --- | --- |
| 1 | Runtime architecture and dependency map | Helps engineers understand what exists, what depends on what, and where failures spread. | Maps local services to VPCs, subnets, load balancers, ECS/EKS/App Runner, RDS, Redis, queues, and CloudWatch logs. |
| 2 | Health/readiness checks | Makes deployments and support safer because the system can prove whether it is actually ready. | Connects to ALB health checks, ECS readiness, CloudWatch alarms, synthetic checks, and deploy gates. |
| 3 | Structured logging and request IDs | Speeds up debugging and incident response across API, workers, and services. | Connects to CloudWatch Logs, log correlation, trace IDs, X-Ray, OpenTelemetry, and incident evidence. |
| 4 | Config/secrets hardening | Reduces the chance of leaked credentials, unsafe defaults, and environment drift. | Connects to IAM, Secrets Manager, SSM Parameter Store, least privilege, and secure deployment config. |
| 5 | Docker/container exposure audit | Finds accidental public ports, weak runtime settings, and unsafe local infrastructure assumptions. | Connects to security groups, private subnets, container hardening, public/private service boundaries, and network segmentation. |
| 6 | Incident runbook | Turns troubleshooting into a repeatable process instead of panic debugging. | Connects to CloudWatch alarms, incident response, rollback, backup restore, escalation, and post-incident review. |
| 7 | Bash/Python ops scripts | Automates repetitive checks and gives the firm reusable operational tooling. | Connects to AWS CLI, boto3, read-only audits, inventory scripts, backup checks, log collection, and report generation. |
| 8 | CI/deploy safety checks | Prevents risky changes from shipping and makes deployment quality visible. | Connects to GitHub Actions, deploy guards, secret scanning, config audits, test gates, and policy-as-code thinking. |

If a practice session does not connect to at least one row in this table, it is probably lower value right now.

For each session, write a short note using this format:

```text
Future Standard value:
Site improvement:
AWS/security/observability concept learned:
Evidence produced:
Next operational risk to reduce:
```

Example:

```text
Future Standard value: Faster incident debugging
Site improvement: Added request IDs to Go API logs
AWS/security/observability concept learned: CloudWatch log correlation and traceability
Evidence produced: Sample log line with request_id, path, status, duration_ms
Next operational risk to reduce: FastAPI worker logs do not share the same request/job correlation ID yet
```

## Practice Lenses

### AWS Lens

For every project service, know the AWS equivalent:

- Go API: ECS service, EKS deployment, App Runner service, or EC2 systemd service
- FastAPI workers: ECS service, Lambda worker, or SQS consumer
- RabbitMQ: Amazon MQ, SQS/SNS, or EventBridge depending on the queue pattern
- Postgres: RDS PostgreSQL
- Redis: ElastiCache
- Docker Compose networks: VPC, subnets, route tables, security groups, load balancers
- Local logs: CloudWatch Logs
- Local metrics: CloudWatch metrics, Prometheus, Grafana
- Traces: OpenTelemetry, AWS X-Ray, ADOT collector
- `.env` secrets: Secrets Manager or SSM Parameter Store

When you document a task, add one short note: "If this ran on AWS, the main resource/risk would be..."

### Security Lens

For each change, check:

- No hardcoded secrets, tokens, passwords, or credentials
- Config comes from environment or a secret manager pattern
- Public ports are intentional
- Auth and rate limiting protect sensitive endpoints
- CORS is environment-specific
- Errors do not leak secrets, SQL, tokens, or internal paths
- Logs do not print credentials or bearer tokens
- Destructive operations require explicit confirmation or `--apply`
- Scripts default to read-only or dry-run behavior
- High-risk findings fail CI or deploy guards

### Observability Lens

For each service or script, make sure you can answer:

- Is it up?
- Is it ready?
- Is it healthy enough?
- How slow is it?
- What changed recently?
- Which dependency is failing?
- Which request/user/job caused the failure?
- Is this a new issue or a recurring issue?
- What would the alert say?

Good observability work produces evidence, not vibes: status, latency, error count, dependency state, timestamp, environment, and next action.

### Automation Lens

Operational scripts should be boring and trustworthy:

- `--help` exists
- inputs are validated
- timeouts are set
- failure exits nonzero
- output can be human-readable or JSON/Markdown
- errors explain what failed and what to try next
- read-only is the default
- mutation requires `--apply`
- reports go under `infra/reports/`
- runbooks go under `infra/runbooks/`

## What To Avoid

Do not create another numbered assignment list in this file.

Avoid:

- duplicating `FUTURE_STANDARD_INFRA_TASKS.md`
- duplicating daily checklists from `LEARNING_ROADMAP.md`
- duplicating exercise instructions from `PRACTICE_READY.md`
- adding generic AWS tutorial notes that are not tied to this repo
- writing big scripts that do ten unrelated things
- making fake reports that do not inspect real local state

If a new concrete task is needed, put it in `FUTURE_STANDARD_INFRA_TASKS.md` or the relevant `infra/practice/` file. Keep this file as the strategy and quality bar.

## Evidence To Capture

For each meaningful infra/security/observability task, capture a short proof note:

```text
Task:
Files changed:
Risk reduced:
How I verified it:
What would change on AWS:
Remaining gap:
```

Example:

```text
Task: Added structured request logging to the Go API
Files changed: Pokemon/server/middleware/logging.go
Risk reduced: Incidents can be tied to request IDs and latency
How I verified it: hit /health and confirmed request_id, method, path, status, duration_ms
What would change on AWS: ship logs to CloudWatch Logs and query by request_id
Remaining gap: traces are not connected across Go and FastAPI yet
```

## Interview Language

Use language like this only after you have real evidence:

> I used my Go and FastAPI project as an infrastructure lab. I mapped runtime dependencies, hardened configuration, improved health and logging, wrote operational scripts, and connected local Docker risks to AWS concepts like security groups, CloudWatch, RDS, ElastiCache, IAM, and Secrets Manager.

For AWS:

> I practiced by translating local infrastructure into AWS resources and controls. Docker networks became VPC and security group thinking, Postgres became RDS backup and access-control thinking, Redis became ElastiCache exposure risk, and app logs became CloudWatch and traceability work.

For security:

> I focused on practical controls: secrets handling, public port exposure, CORS and auth review, rate limits, safe script defaults, and deploy gates that can block high-risk findings.

For observability:

> I treated observability as evidence: health, readiness, latency, structured logs, dependency state, incident snapshots, and runbooks that explain what to do when checks fail.

## Definition Of Useful

This plan is doing its job when:

- the task source stays in the existing roadmap/task files
- each completed task has an AWS/security/observability note
- scripts and docs produce real evidence from this repo
- runbooks explain what to do when something fails
- you can explain both local behavior and the AWS equivalent clearly
