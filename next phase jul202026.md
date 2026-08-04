# Next Phase - July 20, 2026

## Why This File Exists

This is the handoff file for where the project is right now and what the next phase should be.

Read this when starting a new Codex session before asking for more infra work.

The key correction:

> We are not starting from zero. This repo already has a lot of dependency mapping, scripts, Docker work, Odoo work, AWS practice docs, and Future Standard notes. The next phase is not repeating the same inventory forever. The next phase is turning the local/dev system into a production-shaped operating model and using that to build real AWS, security, observability, and IaC intuition.

## Current Phase

We are in:

```text
Phase 2: Production-shaped infrastructure readiness
```

We are not in:

```text
Phase 0: What is this project?
Phase 1: Basic local Docker setup
Phase 4: Big scale / Kubernetes / multi-region / enterprise platform
```

The project is not fully production-ready yet, but it is beyond basic local setup.

Current maturity:

```text
Local runtime: mostly established
Core product direction: PokemonTool intelligence + Odoo storefront
Dependency awareness: partially documented
Operational scripts: started, several are scaffolded or partially implemented
AWS practice: started with identity/inventory field kit
Security practice: started with secrets/config/audit surfaces
Observability practice: started with health/reporting/logging surfaces
IaC: not meaningfully started yet
Cloud deployment: not production-shaped yet
```

## Active Product Direction

The active product direction is:

```text
PokemonTool = intelligence engine
Odoo = storefront / ERP / inventory / orders / CRM
AWS = future hosting and infra practice layer
Python/boto3 = read-only cloud inventory and audit tooling
Terraform/IaC = repeatable cloud network/security baseline later
```

Do not treat NexusOS as the main product direction right now. It exists in the repo, but the active practical path is PokemonTool plus Odoo.

## Current System Mental Model

```text
External market data / seller research
  -> PokemonTool ingestion and intelligence
  -> Postgres data model
  -> Finder / watchlists / alerts / inventory
  -> Odoo product sync
  -> Odoo storefront / sales / CRM / inventory workflow
```

Infrastructure view:

```text
Local machine
  -> Docker Compose stacks
      -> PokemonTool services
      -> Odoo services
      -> Postgres / Redis / RabbitMQ / observability components
  -> Python/Bash infra scripts
  -> GitHub repo + docs + CI
  -> Future AWS target architecture
```

Future cloud view:

```text
Users
  -> DNS
  -> HTTPS reverse proxy / load balancer
  -> app services / Odoo
  -> managed database / durable storage
  -> logs / metrics / alerts
  -> backups / restore process
  -> deployment pipeline
```

## What Already Exists

### Project Docs And Roadmaps

Important files:

```text
AGENTS.md
next phase jul202026.md

docs/PROJECT_INFRASTRUCTURE.md
infra/MASTER_INDEX.md
infra/AWS_SECURITY_OBSERVABILITY_PRACTICE_PLAN.md
infra/FUTURE_STANDARD_INFRA_TASKS.md
infra/scripts/aws/HQ_Hybrid_Infrastructure_Notes.md
infra/scripts/aws/FUTURE_STANDARD_NYC_ALERT_CONVERSATION_NOTES.md
infra/scripts/aws/FUTURE_STANDARD_INFRA_IDEA_PLAYBOOK.md
odoo/README.md
```

These are not all perfect, but they mean the project already has a strong documentation spine.

### Active Runtime Surfaces

Important files:

```text
Pokemon/docker-compose.yml
Pokemon/docker-compose.prod.yml
Pokemon/docker-compose.local-no-postgres-port.yml
docker-compose.odoo.yml
odoo/config/odoo.conf
odoo/.env.example
odoo/custom_addons/pokecard_storefront/
```

The local system already has a real service stack shape:

```text
Pokemon Go API
React dashboard
Python api-consumer
Python analytics engine
Go scraping service
Postgres
Redis
RabbitMQ
Odoo
Odoo Postgres
Odoo custom addon
Prometheus / Grafana / Loki / Promtail in Pokemon stack
```

### Existing Infra Scripts

Important script areas:

```text
infra/scripts/aws/
infra/scripts/python/
infra/scripts/security/
infra/scripts/network/
infra/scripts/linux/
infra/scripts/bash/
```

Notable scripts:

```text
infra/scripts/aws/01_identity_check.py
infra/scripts/aws/05_inventory.py
infra/scripts/aws/company_repo_discovery.py
infra/scripts/python/pokevend_health_monitor.py
infra/scripts/python/pokevend_config_validator.py
infra/scripts/python/pokevend_rabbitmq_monitor.py
infra/scripts/security/01_secrets_auditor.py
infra/scripts/network/01_port_scanner.py
infra/scripts/linux/pokevend_stack_audit.sh
infra/scripts/bash/pokevend_db_ops.sh
odoo/scripts/validate_odoo_scaffold.sh
odoo/scripts/odoo_infra_doctor.py
```

Important reality:

> Some scripts are complete enough to run, some are learning scaffolds with TODOs, and some are older NexusOS/Pokevend-oriented scripts that need to be updated for the active PokemonTool + Odoo direction.

So the next phase is not always "make a new script." Often it is:

```text
Audit the existing script
Rename/refocus it if needed
Make it active-stack aware
Make it produce reports
Make it runnable from Makefile
Add clear verification commands
```

## What Is Not Next

Do not jump straight to these:

```text
Kubernetes
multi-region scaling
full cloud migration
complex VPC peering
AI autonomous remediation
big refactors
rewriting Odoo
replacing every local dependency with managed cloud services
```

Those are later.

Also do not keep repeating generic dependency inventory forever. Basic dependency understanding exists. The next work should produce operational proof.

## What Is Actually Next

The next phase is:

```text
Production-shaped readiness
```

That means proving the system can be operated outside your memory and outside one lucky laptop state.

Questions this phase must answer:

```text
Can I start it reliably?
Can I verify it is healthy?
Can I identify what is exposed?
Can I back up data?
Can I restore data?
Can I find logs when something breaks?
Can I detect queue backlog or stale automation?
Can I safely sync Pokemon inventory into Odoo?
Can I sketch the AWS equivalent without overbuilding?
Can I create a small Terraform baseline later?
```

## Phase 2 Outcome

By the end of this phase, the repo should have:

```text
1. A current production-readiness report
2. A real backup/restore runbook and tested restore proof
3. A consolidated health/observability report
4. A security/exposure report
5. An Odoo/Pokemon sync readiness report
6. An AWS target architecture note
7. A first Terraform network/security lab
8. A small set of Makefile commands for repeatable checks
```

The project does not need huge scale yet. It needs reliable operation.

## Phase 2 Workstreams

### Workstream 1: Runtime Truth And Current State

Goal:

```text
One current report that says what is running, what should be running, and what is stale/legacy.
```

Why this matters:

You already have many docs and scripts. The risk now is not lack of notes. The risk is drift.

Things to inspect:

```text
Pokemon/docker-compose.yml
Pokemon/docker-compose.prod.yml
Pokemon/docker-compose.local-no-postgres-port.yml
docker-compose.odoo.yml
odoo/.env.example
odoo/config/odoo.conf
Makefile
scripts/dev-universe.sh if present
```

Produce:

```text
infra/reports/current-runtime-state-jul2026.md
```

Include:

```text
service
compose file
container name
port binding
internal dependency
persistent volume
data owner
healthcheck exists yes/no
logs location
backup requirement
production risk
```

Do not just list dependencies. Mark each one as:

```text
active
legacy
local-only
future/cloud-only
unknown
```

The key judgment:

> If a doc says NexusOS but the active system is Odoo/PokemonTool, label it as legacy or secondary so future sessions do not chase the wrong target.

### Workstream 2: Backup And Restore Proof

Goal:

```text
Prove the important data can be backed up and restored.
```

This is more important than scale.

Data stores:

```text
PokemonTool Postgres
Odoo Postgres
RabbitMQ state if needed
Odoo filestore / odoo_data volume
possibly uploaded product images/static assets later
```

Files/scripts to inspect:

```text
infra/scripts/bash/pokevend_db_ops.sh
Pokemon/docker-compose.yml
docker-compose.odoo.yml
odoo/README.md
```

Produce:

```text
infra/runbooks/postgres-backup-restore.md
infra/reports/backup-restore-test-jul2026.md
```

Minimum proof:

```text
1. Create a backup from local Postgres
2. Restore it into a separate test DB/container/volume
3. Run a simple query proving data exists
4. Document exact commands
5. Document what could fail
```

The intuition:

> A backup is just a hope until restore is tested.

Future Standard connection:

At work, if someone says "we have backups," a good infra engineer asks:

```text
When was the last restore test?
How long did it take?
Where is the runbook?
Who owns it?
What data is excluded?
```

### Workstream 3: Security And Exposure Baseline

Goal:

```text
Know what is exposed, what uses defaults, and what cannot be public yet.
```

Files/scripts to inspect:

```text
infra/scripts/security/01_secrets_auditor.py
infra/scripts/network/01_port_scanner.py
infra/scripts/python/pokevend_config_validator.py
odoo/config/odoo.conf
odoo/.env.example
Pokemon/docker-compose.yml
Pokemon/docker-compose.prod.yml
docker-compose.odoo.yml
.github/workflows/ci.yml
```

Produce:

```text
infra/reports/security-exposure-baseline-jul2026.md
```

Report sections:

```text
Ports exposed on host
Ports bound to 127.0.0.1 only
Admin UIs exposed locally
Default passwords still present
Env vars required before public deploy
Secrets in tracked files
GitHub Actions secret usage
Containers or services that should never be internet-facing
```

Important examples from the current project:

```text
Odoo dev admin password exists in odoo/config/odoo.conf
Odoo DB password defaults exist for local dev
RabbitMQ guest/guest may exist in local compose
Postgres local ports are acceptable locally but not public
Odoo should not be exposed directly without HTTPS/reverse proxy/hardening
```

The intuition:

> Security is not just finding hackers. It is knowing what trust boundary each port, password, network, and role crosses.

Future AWS mapping:

```text
Docker port exposure -> AWS security group exposure
.env secrets -> SSM Parameter Store / Secrets Manager
local admin password -> production secret rotation requirement
localhost-only bind -> private subnet / internal security group
public web port -> ALB listener + HTTPS
```

### Workstream 4: Observability And Incident Readiness

Goal:

```text
Know how to tell whether the app is healthy and what to inspect when it is not.
```

Files/scripts to inspect:

```text
infra/scripts/python/pokevend_health_monitor.py
infra/scripts/python/pokevend_rabbitmq_monitor.py
Pokemon/prometheus.yml
Pokemon/promtail-config.yaml
Pokemon/scripts/incident_snapshot.sh if present
odoo/scripts/odoo_infra_doctor.py
```

Produce:

```text
infra/reports/observability-baseline-jul2026.md
infra/runbooks/app-down-first-response.md
infra/runbooks/queue-backlog-first-response.md
infra/runbooks/odoo-down-first-response.md
```

Minimum checks:

```text
Pokemon API health
PokeTCG health
api-consumer health if exposed
RabbitMQ management health
queue depth
Postgres port/container health
Redis health
Odoo HTTP health
Odoo DB health
Prometheus/Grafana presence
log collection status
```

Operational questions:

```text
What alert would tell me the app is down?
What alert would tell me data ingestion is stale?
What alert would tell me Odoo sync is failing?
What alert would tell me RabbitMQ is backing up?
Where do I look first when a user says the store is broken?
```

The intuition:

> Observability is not "we have Grafana." Observability is being able to answer what is broken, why it is broken, who is affected, and what changed.

### Workstream 5: Odoo/Pokemon Sync Readiness

Goal:

```text
Make sure the active business direction is operationally safe: PokemonTool intelligence syncing into Odoo products.
```

Files to inspect:

```text
odoo/custom_addons/pokecard_storefront/
odoo/custom_addons/pokecard_storefront/scripts/sync_pokemon_inventory_to_odoo.py
Pokemon/server Odoo sync code if present
Pokemon/database/migrations/
docs/PROJECT_INFRASTRUCTURE.md
odoo/README.md
```

Produce:

```text
infra/reports/odoo-sync-readiness-jul2026.md
```

Questions to answer:

```text
What is the stable key between Pokemon inventory and Odoo product.template?
What fields are synced?
Which fields should Odoo own after sync?
Which fields should PokemonTool own after sync?
Is sync idempotent?
What happens if Odoo is down?
What happens if Pokemon DB is down?
Can dry-run prove what would change before writing?
Where are errors logged?
Can a failed sync be retried safely?
```

The key design principle:

> PokemonTool should remain the intelligence engine. Odoo should own sellable products, storefront, orders, customers, CRM, and inventory operations.

Do not blur ownership.

### Workstream 6: AWS Target Architecture

Goal:

```text
Create a realistic first cloud target, not a fantasy enterprise platform.
```

Produce:

```text
infra/reports/aws-target-architecture-jul2026.md
```

Start with this shape:

```text
Route53 DNS
  -> HTTPS reverse proxy / ALB
  -> EC2 or ECS service for app/Odoo
  -> RDS Postgres
  -> S3 for backups/assets
  -> CloudWatch logs/alarms
  -> Secrets Manager or SSM Parameter Store
```

Do not overbuild.

First AWS target should be:

```text
single region
one VPC
public subnet for ingress only
private subnet for app/database where possible
security groups with least required ports
managed Postgres if budget allows
CloudWatch logs
simple backup path
```

Networking intuition:

On laptop:

```text
networking = Docker networks + localhost ports + host firewall
```

In AWS:

```text
networking = VPC + subnets + route tables + security groups + DNS + load balancer
```

VLANs are mostly on-prem/switching language. In AWS, the equivalent mental model is segmentation through:

```text
subnets
security groups
routing
NACLs if needed
private/public IP paths
```

Do not invent VLAN complexity for this project right now. Use cloud-native segmentation.

### Workstream 7: AWS boto3 Practice

Goal:

```text
Use Python/boto3 to safely inspect cloud state in read-only mode.
```

Files already present:

```text
infra/scripts/aws/01_identity_check.py
infra/scripts/aws/01_identity_check_WORKSHEET.md
infra/scripts/aws/05_inventory.py
infra/scripts/aws/company_repo_discovery.py
```

Next boto3 scripts to build or improve:

```text
infra/scripts/aws/02_vpc_network_inventory.py
infra/scripts/aws/03_security_group_audit.py
infra/scripts/aws/04_s3_public_access_audit.py
infra/scripts/aws/06_cloudwatch_observability_audit.py
infra/scripts/aws/07_tag_hygiene_report.py
```

Order:

```text
1. Prove identity with STS
2. Inventory VPC/subnets/routes/security groups
3. Audit security groups for public exposure
4. Audit S3 public access/encryption/versioning
5. Audit CloudWatch log retention/alarms
6. Audit tags and ownership
```

The intuition:

> boto3 is not about writing random Python. It is about converting cloud control-plane state into operational evidence.

Every script should answer:

```text
What question am I answering?
What AWS API has the truth?
Is this read-only?
What risk would a manager care about?
What action should follow?
```

### Workstream 8: Terraform / IaC Foundation

Goal:

```text
Start IaC only after the target architecture is clear.
```

Create later:

```text
infra/terraform/aws_odoo_pokemon_sandbox/
```

First Terraform should define:

```text
VPC
public subnet
private subnet
route table
internet gateway
security groups
CloudWatch log group
tags
```

Do not start with full ECS/RDS/Odoo deployment if the basics are unclear.

The first Terraform win is:

```text
terraform plan clearly explains the network/security baseline
terraform destroy can clean it up
all resources have tags
security groups are not wide open by accident
```

The intuition:

> IaC is not "cloud magic." IaC is a repeatable contract for infrastructure state.

## Immediate Next 10 Tasks

Do these in order.

### Task 1: Create Current Runtime State Report

File to produce:

```text
infra/reports/current-runtime-state-jul2026.md
```

Read:

```text
docs/PROJECT_INFRASTRUCTURE.md
odoo/README.md
Pokemon/docker-compose.yml
docker-compose.odoo.yml
Makefile
```

Include:

```text
active systems
legacy/secondary systems
ports
volumes
healthchecks
known gaps
what is already solved
what is not solved
```

Why first:

It stops future sessions from repeating old advice.

### Task 2: Run And Improve Odoo Infra Doctor

File:

```text
odoo/scripts/odoo_infra_doctor.py
```

Run:

```bash
make odoo-doctor
```

Improve if needed:

```text
check Odoo HTTP endpoint path
check database port
check custom addon mount
check dev defaults
check bridge network
output markdown report
```

Produce:

```text
infra/reports/odoo-infra-doctor-jul2026.md
```

### Task 3: Make Existing Health Monitor Active-Stack Aware

File:

```text
infra/scripts/python/pokevend_health_monitor.py
```

Problem:

It still references some NexusOS-style services. Update or clearly mode-split it.

Better design:

```text
--stack pokemon
--stack odoo
--stack all
--format text|markdown|json
```

Expected checks:

```text
Pokemon API
PokeTCG
RabbitMQ
Postgres
Redis
Odoo HTTP
Odoo DB
Grafana/Prometheus if running
```

### Task 4: Run Security Exposure Baseline

Use/improve:

```text
infra/scripts/security/01_secrets_auditor.py
infra/scripts/network/01_port_scanner.py
infra/scripts/python/pokevend_config_validator.py
```

Produce:

```text
infra/reports/security-exposure-baseline-jul2026.md
```

Answer:

```text
Which ports are exposed?
Which are localhost-only?
Which defaults are still present?
Which values must never ship to production?
```

### Task 5: Backup/Restore Proof

Use/improve:

```text
infra/scripts/bash/pokevend_db_ops.sh
```

Also cover:

```text
Odoo DB
Pokemon DB
Odoo filestore/volume if needed
```

Produce:

```text
infra/runbooks/postgres-backup-restore.md
infra/reports/backup-restore-test-jul2026.md
```

### Task 6: Odoo Sync Readiness Report

Read:

```text
odoo/custom_addons/pokecard_storefront/scripts/sync_pokemon_inventory_to_odoo.py
odoo/custom_addons/pokecard_storefront/models/product_template.py
Pokemon database inventory schema/migrations
```

Produce:

```text
infra/reports/odoo-sync-readiness-jul2026.md
```

Answer:

```text
Is dry-run safe?
Is sync idempotent?
What fields are source-of-truth in PokemonTool?
What fields are source-of-truth in Odoo?
What happens on partial failure?
```

### Task 7: AWS Target Architecture Note

Produce:

```text
infra/reports/aws-target-architecture-jul2026.md
```

Keep it simple:

```text
Route53
ALB or reverse proxy
EC2/ECS
RDS
S3
CloudWatch
Secrets Manager/SSM
security groups
```

Do not write Terraform yet until this note is clear.

### Task 8: boto3 VPC Inventory Script

Create:

```text
infra/scripts/aws/02_vpc_network_inventory.py
```

Use the guided style from:

```text
infra/scripts/aws/01_identity_check.py
```

It should list:

```text
VPCs
subnets
route tables
internet gateways
NAT gateways if any
security groups count per VPC
```

Read-only only.

### Task 9: boto3 Security Group Audit

Create:

```text
infra/scripts/aws/03_security_group_audit.py
```

Find:

```text
0.0.0.0/0 ingress
::/0 ingress
SSH/RDP open to world
DB ports open to world
wide ephemeral ranges
security groups with no description/tags
```

Output:

```text
markdown and json
severity
resource id
rule
why it matters
next action
```

### Task 10: Terraform Network Lab

Create later:

```text
infra/terraform/aws_odoo_pokemon_sandbox/
```

Only after Tasks 7-9 are done.

First target:

```text
VPC
public/private subnets
security groups
tags
CloudWatch log group
```

## What To Tell Future Codex Sessions

When continuing this project, say:

```text
Read AGENTS.md and next phase jul202026.md first. Use code-review-graph before broad repo scans. We are in Phase 2 production-shaped infra readiness, not basic discovery and not scale. Help me work through the immediate next tasks without repeating old dependency inventory.
```

## How To Use code-review-graph Now

The repo has `code-review-graph` installed and configured for Codex MCP.

Before broad questions or reviews:

```bash
code-review-graph status --repo /home/iscjmz/shopify/shopify
code-review-graph update --repo /home/iscjmz/shopify/shopify --skip-flows
code-review-graph detect-changes --repo /home/iscjmz/shopify/shopify --brief
```

Use it to avoid rereading huge files when asking:

```text
what changed?
what is impacted?
what files should I inspect?
where is the function/class?
what tests might be relevant?
```

Do not trust graph output blindly. Use it to choose files, then read the critical code.

## What To Stop Doing

Stop doing these:

```text
Repeating generic "inventory dependencies" advice without checking existing docs/scripts
Treating Docker-ready as production-ready
Treating scale as the immediate next phase
Mixing NexusOS direction with the active Odoo/Pokemon direction without labeling it
Building new scripts when an existing script should be improved
Installing more tools before using the ones already installed
```

## What To Start Doing

Start doing these:

```text
Produce dated reports under infra/reports/
Produce runbooks under infra/runbooks/
Keep scripts read-only by default
Add --format markdown/json to scripts
Use Makefile shortcuts for repeatable checks
Tie every script to a Future Standard skill: AWS, security, observability, IaC, networking, incident response
Turn every local check into its AWS equivalent mentally
```

## The Main Intuition

This project is low-key infrastructure because the hard part is no longer just writing app code.

The hard part is operating a system:

```text
data comes in
workers process it
queues buffer it
databases persist it
Odoo sells it
logs explain it
alerts catch failures
backups protect it
DNS/HTTPS expose it safely
AWS/IaC make it repeatable outside one machine
```

That is infrastructure.

The next phase is not "make it huge."

The next phase is:

> Make it operationally believable.

## Definition Of Done For Phase 2

Phase 2 is done when you can answer these without guessing:

```text
What runs the product?
What data matters?
What happens if each dependency dies?
How do I know the system is healthy?
Where are logs?
What ports are exposed?
What secrets/defaults must change before public deploy?
Can I back up and restore the databases?
Can I safely sync Pokemon inventory into Odoo?
What would the first AWS version look like?
What boto3 scripts prove cloud state safely?
What Terraform baseline describes the network/security shape?
```

When those are answered with reports, scripts, and runbooks, then the project is ready for a small cloud deployment.

Only after that should the next question be scale.
