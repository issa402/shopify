# Azure Hybrid Cloud Mastery

This guide is for going from "I run stuff on my Linux machine" to "I can reason like an infrastructure engineer designing hybrid cloud systems."

The goal is not to memorize Azure product names.
The goal is to build the instincts that let you look at any system and answer:

- where should this run
- how should it be secured
- how should it recover
- how should it scale
- how should it be monitored
- what risk does this design create
- what would I document so another engineer can operate it

This is the mindset behind these role requirements:

- document designs, solutions, processes, and ideas to improve workflows and systems
- design and implement scalable, reliable solutions
- improve efficiency and the risk profile of technical platforms
- understand cloud platforms like Azure
- understand hybrid infrastructure models

By the end, you should be able to take your local Pokemon infrastructure and explain how to run it as:

- local only
- cloud only
- hybrid on-prem plus Azure
- production-style, monitored, secured, backed up, and documented

## Your Actual Project Is The Lab

This guide is not about random cloud examples.
Your `Pokemon/` project is already a real infrastructure training environment.

Here is what you actually have:

```text
Pokemon/
  client/                         React frontend served by Nginx
  server/                         Go API gateway and main backend
  services/api-consumer/          Python FastAPI/eBay/TCG ingestion service
  services/analytics-engine/      Python analytics, trend, deal, and news engine
  services/scraping-service/      Go scraping service
  database/migrations/            Postgres schema and seed path
  scripts/port_preflight.sh       checks if required local ports are already taken
  scripts/health-check.sh         checks service health after startup/deploy
  scripts/postgres_backup_drill.sh proves backup, verify, and restore workflow
  scripts/infra_report.sh         early host report script
  prometheus.yml                  metrics scraping config
  promtail-config.yaml            log shipping config
  docker-compose.yml              local on-prem/homelab infrastructure
  docker-compose.prod.yml         production-style deployment shape
  .github/workflows/              CI/deploy automation
```

That is not toy learning.
That is a small platform.

The local platform has an app tier, data tier, queue tier, cache tier, frontend tier, ingestion tier, analytics tier, scraping tier, logging tier, metrics tier, startup scripts, health checks, and backup drills.

So when this guide says "cloud" or "hybrid," translate it like this:

```text
Your Linux host running Docker Compose
  becomes the on-prem side.

Azure
  becomes the cloud management, backup, secrets, registry, monitoring, and optional compute side.
```

Your job is not to memorize Azure.
Your job is to take this exact platform and make it more reliable, more secure, more observable, more recoverable, and easier to explain.

That is exactly what the Future Standard role is asking for.

## The Pokemon-To-Azure Map

Think of every service in your project as something you either keep local, move to Azure, or connect to Azure.

| Your project piece | What it does | Azure/hybrid translation | What to learn from it |
| --- | --- | --- | --- |
| `client/` | user interface served by Nginx | Azure Static Web Apps, App Service, Container Apps, or Front Door plus storage/CDN | public entrypoints, TLS, frontend deployment |
| `server/` | Go API, auth, health, business routes | Azure Container Apps or AKS | stateless app compute, health probes, scaling |
| `services/api-consumer/` | FastAPI ingestion from external APIs | Container Apps job/service, AKS worker, or VM worker | background services, secrets, external API credentials |
| `services/analytics-engine/` | analytics/trends/deals/news | Container Apps job, AKS CronJob, or scheduled worker | scheduled compute, data freshness, queue processing |
| `services/scraping-service/` | scraping and publishing events | container worker or VM if browser/runtime needs are special | workload fit, browser deps, queue publishing |
| Postgres container | source-of-truth data | Azure Database for PostgreSQL or local Postgres with Blob backups | managed database, backups, restore drills |
| Redis container | cache | Azure Cache for Redis or private Redis container | cache risk, private networking |
| RabbitMQ container | queue/broker | Azure Service Bus, Container Apps compatible broker pattern, or self-managed RabbitMQ | async processing, queue depth, backpressure |
| Loki/Promtail/Grafana | logs and dashboards | Azure Monitor and Log Analytics | centralized logs, queries, retention |
| Prometheus | metrics | Azure Monitor managed Prometheus or Container Apps metrics | service metrics, alerting |
| `.env` | local secrets/config | Azure Key Vault plus managed identity | secret storage, rotation, least privilege |
| Dockerfiles | deployable units | Azure Container Registry images | image build, versioning, deployment |
| `health-check.sh` | operational verification | health probes, Azure Monitor alerts, runbook checks | evidence-based operations |
| `postgres_backup_drill.sh` | backup/restore proof | Blob Storage backup target, Azure Backup patterns | recovery, RPO/RTO |
| GitHub workflows | automation | CI/CD to ACR and Container Apps/AKS | repeatable deployment |

This is the core move:

```text
Do not ask "what Azure service should I learn?"

Ask "which part of my Pokemon platform has a real operational problem,
and which Azure service teaches me how a company would solve that problem?"
```

For example, your `postgres_backup_drill.sh` is not "just a script."
It is the beginning of disaster recovery.

Your `port_preflight.sh` is not "just Bash."
It is the beginning of deployment safety.

Your `health-check.sh` is not "just curl and Docker."
It is the beginning of production verification and alert design.

Your `docker-compose.prod.yml` hiding Postgres, Redis, and RabbitMQ ports is not trivia.
It is the beginning of private network design.

Your Loki, Promtail, Grafana, and Prometheus files are not decoration.
They are your bridge into Azure Monitor thinking.

## What You Should Do First In This Repo

Before reading any more theory, do this sequence.

Start from:

```bash
cd /home/iscjmz/shopify
mkdir -p shopify/future_standard_mastery/labs/azure_hybrid
```

Then create this file:

```bash
touch shopify/future_standard_mastery/labs/azure_hybrid/00_project_infra_map.md
```

Now run these commands:

```bash
sed -n '1,230p' shopify/Pokemon/docker-compose.yml
sed -n '1,170p' shopify/Pokemon/docker-compose.prod.yml
sed -n '1,220p' shopify/Pokemon/scripts/port_preflight.sh
sed -n '1,220p' shopify/Pokemon/scripts/health-check.sh
sed -n '1,280p' shopify/Pokemon/scripts/postgres_backup_drill.sh
rg -n "ports:|healthcheck|depends_on|POSTGRES|REDIS|RABBIT|JWT_SECRET|EBAY_CLIENT_SECRET|EVENTBRITE_TOKEN|GF_SECURITY_ADMIN_PASSWORD" shopify/Pokemon
```

In `00_project_infra_map.md`, write this in your own words:

```markdown
# Pokemon Project Infrastructure Map

## What This Platform Is
This is a multi-service Pokemon trading card intelligence platform. It has a frontend, Go API, Python ingestion, analytics workers, scraping workers, Postgres, Redis, RabbitMQ, logs, metrics, health checks, and backup drills.

## Compute
- client:
- server:
- api-consumer:
- analytics-engine:
- scraping-service:

## Data
- Postgres:
- Redis:
- RabbitMQ:
- Docker volumes:

## Network Exposure
- public/local browser entrypoints:
- localhost-only infra ports:
- internal Docker-only service names:

## Secrets
- JWT_SECRET:
- POSTGRES_PASSWORD:
- RabbitMQ guest credentials:
- EBAY_CLIENT_SECRET:
- EVENTBRITE_TOKEN:
- Grafana admin password:

## Operations
- port preflight:
- health check:
- backup drill:
- logs:
- metrics:

## What Would Break If My Linux Host Dies

## What Azure Should Help With First

## What Should Stay Local For Now
```

This is the first real artifact.
This is how you stop being in tutorial hell.

You read the actual infra files.
You explain the actual platform.
Then Azure becomes a way to improve this platform, not a cloud vocabulary list.

## Read This First: This Is Not A Reading Course

Do not read this whole file like a textbook.

Read one lesson, then do the work immediately.

The point is:

```text
learn a concept
touch your actual Linux/repo environment
produce an artifact
explain what changed in your understanding
```

If you only read, you will stay stuck in tutorial hell.
If you build evidence after every lesson, you start becoming dangerous in the good way.

For every lesson below, your output is one of these:

- a markdown lab note
- a command output summary
- a small architecture map
- a local script or command sequence
- a risk table
- a runbook
- an Azure CLI dry-run plan

You do not need to spend money for the first pass.
The first pass is local and free.

The paid/cloud-connected pass comes later, only after the design makes sense.

## How To Use This Guide Without Getting Lost

Use this loop every time:

1. Read the lesson.
2. Stop after the first "Do This Now" section.
3. Create the lab file it names.
4. Run the commands.
5. Paste only the important evidence into the lab file.
6. Write three sentences:
   - what I thought before
   - what I observed
   - what I would do in Azure

Your lab folder should be:

```text
future_standard_mastery/labs/azure_hybrid/
```

Create it once:

```bash
mkdir -p shopify/future_standard_mastery/labs/azure_hybrid
```

The real skill is not copying commands.
The real skill is connecting command output to infrastructure decisions.

## Free Hands-On Tracks

You have three tracks.

### Track A: Free Local-Only

Do this first.

You use:

- Linux
- Bash
- Docker files in the repo
- local scripts
- markdown design notes
- command output

You learn the cloud concepts without paying for cloud resources.

### Track B: Azure Free/Cheap Practice

Do this after Track A.

You use:

- Azure account
- resource group
- budget alerts
- Azure CLI
- maybe Blob Storage, Key Vault, Container Registry, or Container Apps

Important: Azure pricing and free grants change.
Before creating resources, check the Azure portal pricing screen and set a budget alert.
Delete lab resource groups when finished.

### Track C: Production-Style Simulation

Do this after you understand the basics.

You write:

- architecture design
- runbook
- change proposal
- risk register
- rollback plan
- operational improvement note

This is the part that maps directly to the Future Standard job description.

## Your First 7 Days In This Actual Repo

This is the real path.
Do not start by opening Azure.
Start by understanding the platform you already built.

### Day 1: Map The Pokemon Platform

Your job today is to explain the project as infrastructure, not as code files.

Run:

```bash
sed -n '1,230p' shopify/Pokemon/docker-compose.yml
sed -n '1,170p' shopify/Pokemon/docker-compose.prod.yml
find shopify/Pokemon -maxdepth 4 -type f \( -name "Dockerfile" -o -name "*.sh" -o -name "*.yml" -o -name "*.yaml" \) | sort
```

Create:

```text
future_standard_mastery/labs/azure_hybrid/00_project_infra_map.md
```

Explain the system in plain English:

```text
Users hit the React client.
The client talks to the Go API.
The Go API depends on Postgres, Redis, and RabbitMQ.
Python services ingest and analyze data.
The scraping service publishes work.
Loki/Promtail/Grafana/Prometheus give local observability.
Scripts verify ports, health, and backup readiness.
```

You win the day when you can explain the whole project without saying "I have some containers."

### Day 2: Prove The Network Boundary

Your job today is to learn what is reachable from your host and what is internal.

Run:

```bash
sed -n '1,220p' shopify/Pokemon/scripts/port_preflight.sh
bash shopify/Pokemon/scripts/port_preflight.sh
rg -n "ports:|NO \"ports:\"|127.0.0.1|3001|5173|5432|6379|5672|15672|9090|3000|3100" shopify/Pokemon/docker-compose.yml shopify/Pokemon/docker-compose.prod.yml
```

Create:

```text
future_standard_mastery/labs/azure_hybrid/03_public_private_map.md
```

Explain why local dev exposes Postgres, Redis, RabbitMQ, Grafana, Prometheus, and Loki only on `127.0.0.1`, while prod tries to hide Postgres, Redis, and RabbitMQ completely.

Then write the Azure version:

```text
Public: frontend/API entrypoint
Private: Postgres, Redis, RabbitMQ/Service Bus, logs, metrics, admin dashboards
Admin-only: Grafana-like dashboards, RabbitMQ management
```

You win the day when you can say exactly what should never be internet-facing.

### Day 3: Prove Health And Failure Paths

Your job today is to understand what "healthy" means in this project.

Run:

```bash
sed -n '1,220p' shopify/Pokemon/scripts/health-check.sh
rg -n "GET /health|/health|/api/health/freshness|/metrics|Ping|pg_isready|redis-cli|rabbitmq" shopify/Pokemon/server shopify/Pokemon/services shopify/Pokemon/scripts
```

If the stack is running, run:

```bash
bash shopify/Pokemon/scripts/health-check.sh
```

Create:

```text
future_standard_mastery/labs/azure_hybrid/07_observability_aiops_plan.md
```

Do not just write "health check exists."
Explain what each check proves.

The Go API `/health` proves the API can respond and can check dependencies.
The FastAPI `/health` proves the ingestion service is alive and can report RabbitMQ health.
The Postgres check proves the database process accepts connections.
The Redis check proves cache responds.
The RabbitMQ log check is weaker because it infers health from today's auth logs, so note that a direct `rabbitmq-diagnostics ping` or management API check would be stronger.

You win the day when you can separate process-up from dependency-ready from business-data-fresh.

### Day 4: Prove Backup And Recovery

Your job today is to turn `postgres_backup_drill.sh` into disaster recovery thinking.

Run:

```bash
sed -n '1,280p' shopify/Pokemon/scripts/postgres_backup_drill.sh
rg -n "pg_dump|pg_restore|BACKUP_DIR|verify|restore|prune|POSTGRES_CONTAINER" shopify/Pokemon/scripts/postgres_backup_drill.sh
```

If Postgres is running, run:

```bash
cd shopify/Pokemon
./scripts/postgres_backup_drill.sh backup
./scripts/postgres_backup_drill.sh list
```

Create:

```text
future_standard_mastery/labs/azure_hybrid/06_backup_recovery_design.md
```

Explain this:

```text
Local today:
Postgres container -> pg_dump custom format -> host backup file -> pg_restore verify/list -> optional restore.

Azure hybrid later:
Postgres backup file -> private Azure Blob container -> lifecycle retention -> restore drill -> alert if no backup exists.
```

You win the day when you can explain RPO, RTO, backup verification, and restore risk using your script.

### Day 5: Secrets And Identity In Your Project

Your job today is to find where trust and credentials live.

Run:

```bash
rg -n "POSTGRES_PASSWORD|JWT_SECRET|ENCRYPTION_KEY|RABBITMQ_DEFAULT_PASS|RABBITMQ_URL|EBAY_CLIENT_SECRET|EVENTBRITE_TOKEN|GF_SECURITY_ADMIN_PASSWORD|guest:guest|change-me|super_secret" shopify/Pokemon
```

Create:

```text
future_standard_mastery/labs/azure_hybrid/05_identity_secret_model.md
```

Explain each secret by damage:

```text
JWT_SECRET leak: attackers may forge or attack tokens.
POSTGRES_PASSWORD leak: database access risk.
RABBITMQ guest credentials: queue tampering risk.
EBAY_CLIENT_SECRET leak: external API/account risk.
Grafana admin password: observability/admin dashboard risk.
```

Then write the Azure version:

```text
Key Vault stores secrets.
Container Apps/AKS workloads use managed identity where possible.
Humans use Entra ID groups and least privilege.
Production does not use guest/guest or change-me secrets.
```

You win the day when every secret has an owner, purpose, risk, and better storage plan.

### Day 6: Deployment And Azure Mapping

Your job today is to connect your Dockerfiles and workflows to cloud deployment.

Run:

```bash
find shopify/Pokemon -maxdepth 5 -type f \( -name "Dockerfile" -o -path "*/.github/workflows/*" \) | sort
sed -n '1,220p' shopify/Pokemon/.github/workflows/ci.yml
sed -n '1,220p' shopify/Pokemon/.github/workflows/deploy.yml
rg -n "docker build|docker compose|image|build|deploy|registry|ssh|scp|health-check" shopify/Pokemon/.github shopify/Pokemon
```

Create:

```text
future_standard_mastery/labs/azure_hybrid/08_deployment_design.md
```

Write the real deployment evolution:

```text
Today:
Docker Compose builds and runs local services.
Prod compose is EC2-style and exposes only app ports.
GitHub workflows exist for CI/deploy.

Azure learning target:
Build images -> push to Azure Container Registry -> deploy server/api-consumer/analytics/scraper to Container Apps -> store secrets in Key Vault -> verify with health checks -> view logs in Azure Monitor.
```

You win the day when you can say which containers deploy first and which dependencies must exist before them.

### Day 7: Write The Platform Design

Your job today is to sound like someone who can own this platform.

Create:

```text
future_standard_mastery/labs/azure_hybrid/12_capstone_azure_hybrid_design.md
```

Your design must be about this project:

```text
Pokemon Hybrid Azure Platform
```

It should say:

```text
The current Pokemon platform runs as a Docker Compose homelab/on-prem stack on Linux. It includes React/Nginx frontend, Go API, Python ingestion, Python analytics, Go scraping, Postgres, Redis, RabbitMQ, Loki, Promtail, Grafana, Prometheus, CI/deploy workflows, health checks, port preflight, and Postgres backup drills.
```

Then propose:

```text
Phase 1: keep app local, send backups to Azure Blob, move secrets plan to Key Vault, document health and risk.
Phase 2: push images to ACR, deploy one stateless service to Container Apps, keep Postgres local or test managed Postgres.
Phase 3: centralize logs/metrics in Azure Monitor, use Azure Arc for local Linux visibility.
Phase 4: decide whether full cloud migration makes sense.
```

You win the day when the design feels like a real internal engineering proposal, not a tutorial note.

## The Big Idea

Cloud is not magic.

Cloud is someone else's data center exposed through APIs.

When you run a service on your Linux machine, you personally own almost everything:

- operating system
- process startup
- disk
- network ports
- firewall rules
- secrets
- backups
- monitoring
- patching
- scaling
- recovery

When you use Azure, you choose which responsibilities you keep and which responsibilities Azure takes over.

That is the heart of cloud architecture.

The question is not "Should I use Azure?"
The question is "Which responsibilities should this team stop managing manually?"

Example:

```text
Local Postgres on Linux:
- you install it
- you patch it
- you back it up
- you monitor disk
- you recover it
- you secure access

Azure Database for PostgreSQL:
- Azure runs the database platform
- Azure handles much of the platform maintenance
- you still own schemas, access, query behavior, cost, backups policy, networking, and app usage
```

Cloud removes some work.
It does not remove responsibility.

## Your Current Setup Is On-Prem Thinking

If your services run on your own Linux machine, Docker host, mini PC, laptop, home server, or local VM, that is local infrastructure.

For learning, call it:

```text
homelab on-prem
```

In a company, "on-prem" usually means systems running in company-controlled spaces:

- office server room
- private data center
- colocated rack
- factory or warehouse edge location
- local Kubernetes cluster
- local virtualization cluster

Your Linux system is a smaller version of the same pattern.

You are already practicing on-prem concepts when you work with:

- ports
- Docker
- Postgres
- Redis
- RabbitMQ
- shell scripts
- health checks
- backups
- cron jobs
- logs
- local firewalls
- environment variables
- service dependencies

The grown-up version uses more formal tooling, but the core questions are the same.

## What Hybrid Cloud Means

Hybrid cloud means some resources live in a private environment and some live in a public cloud, with intentional connectivity and governance between them.

It might look like this:

```text
On-prem:
- internal app
- database
- file server
- local identity integration
- factory systems
- private network

Azure:
- backup storage
- monitoring
- public API
- managed database replica
- identity controls
- security posture management
- disaster recovery environment
```

Or this:

```text
On-prem Linux server
  -> sends logs to Azure Monitor
  -> sends backups to Azure Blob Storage
  -> is managed by Azure Arc
  -> uses Microsoft Defender for Cloud recommendations
  -> deploys containers from Azure Container Registry
```

Hybrid is not "half local and half cloud by accident."

Hybrid is a designed relationship between environments.

The relationship must answer:

- how traffic moves between environments
- how identity works across environments
- where secrets live
- where logs go
- how backups are stored
- who can access what
- how incidents are investigated
- what happens if the network link fails

## The Mental Model: Five Layers

Every infrastructure design can be understood through five layers.

Use these layers whenever you feel lost.

### Layer 1: Compute

Compute means where code runs.

Examples:

- your Linux host
- a VM
- Docker container
- Kubernetes pod
- Azure App Service
- Azure Container Apps
- Azure Kubernetes Service
- Azure Functions

Ask:

- what process is running
- who starts it
- how is it restarted
- how much CPU and memory does it need
- how does it scale
- how does it deploy
- what happens if the host dies

### Layer 2: Network

Network means how systems reach each other.

Examples:

- localhost
- Docker bridge network
- private IP
- public IP
- DNS
- load balancer
- reverse proxy
- Azure Virtual Network
- VPN Gateway
- ExpressRoute
- firewall
- private endpoint

Ask:

- what needs to talk to what
- is the path public or private
- which port and protocol
- where does TLS terminate
- which firewall allows it
- what DNS name is used
- what should never be reachable from the internet

### Layer 3: Data

Data means state that must survive restarts.

Examples:

- Postgres
- Redis
- RabbitMQ queues
- files
- object storage
- logs
- backups
- container volumes

Ask:

- is this source-of-truth data or cache data
- how bad is data loss
- how often must it be backed up
- how fast must it recover
- does it need encryption
- who can read it
- where should it live

### Layer 4: Identity And Secrets

Identity means who or what is allowed to do something.

Secrets mean credentials used to prove identity.

Examples:

- Linux users
- SSH keys
- database passwords
- API tokens
- service principals
- managed identities
- Microsoft Entra ID
- Azure Key Vault

Ask:

- who is the human user
- what is the application identity
- what permissions are required
- where are secrets stored
- how are secrets rotated
- can this use managed identity instead of a password
- can access be logged and reviewed

### Layer 5: Operations

Operations means how you keep the system healthy.

Examples:

- health checks
- logs
- metrics
- alerts
- dashboards
- runbooks
- backup drills
- patching
- incident response
- change documentation

Ask:

- how do I know it is healthy
- how do I know it is unhealthy
- who gets alerted
- what is the first check
- what is the rollback
- how do I prove recovery works
- what should be automated

If you master these five layers, cloud becomes much easier.

## The Azure Map For A Local Stack

Use this as your translation table.

| Local concept | Azure equivalent | What you are really choosing |
| --- | --- | --- |
| Linux machine | Azure Virtual Machine | Keep OS control, gain cloud hosting |
| Docker Compose app | Azure Container Apps | Run containers without managing Kubernetes |
| Docker image | Azure Container Registry | Store images in a managed registry |
| Kubernetes cluster | Azure Kubernetes Service | Orchestrate containers at scale |
| Local Postgres | Azure Database for PostgreSQL | Managed database platform |
| Local files/backups | Azure Blob Storage | Durable object storage |
| `.env` secrets | Azure Key Vault | Central secret storage |
| Local network | Azure Virtual Network | Private cloud network boundary |
| Local firewall | NSG / Azure Firewall | Cloud network access control |
| Reverse proxy | Azure Application Gateway / Front Door | HTTP routing, TLS, edge entry |
| Local logs | Azure Monitor / Log Analytics | Central observability |
| Local alerts | Azure Monitor alerts | Automated notification and response |
| Manual scripts | Azure Automation / GitHub Actions | Repeatable operations |
| Local server inventory | Azure Arc | Cloud management for non-Azure resources |
| Security checklist | Defender for Cloud | Security posture and recommendations |
| SSH only | Bastion / VPN / Just-in-time access | Safer administrative access |
| Cron backup | Azure Backup / scripts to Blob | Recovery planning |

Do not memorize the table like trivia.

Use it to ask: "What responsibility am I trying to move into a managed platform?"

## Azure Services You Should Know First

### Azure Resource Group

A resource group is a logical folder for Azure resources.

Example:

```text
rg-pokemon-dev
```

It might contain:

- container app
- database
- storage account
- key vault
- log analytics workspace
- virtual network

Good resource groups make cleanup and ownership easier.

Bad resource groups become junk drawers.

Task instinct:

- group resources by app, environment, and lifecycle
- do not mix unrelated production and testing resources

### Azure Virtual Network

A virtual network is your private network boundary in Azure.

It is like saying:

```text
these cloud resources live on this private network
```

Inside it, you create subnets.

Example:

```text
vnet-pokemon-dev
  subnet-app
  subnet-data
  subnet-private-endpoints
```

Design instinct:

- public entrypoints should be limited
- databases should not need public exposure
- private endpoints reduce internet-facing risk
- network segmentation limits blast radius

### Azure Virtual Machine

An Azure VM is closest to your Linux machine.

Use a VM when:

- you need OS control
- software does not fit a managed service
- you are lifting and shifting an existing workload
- you need to practice Linux cloud administration

Avoid using VMs by default when:

- a managed service can remove operational burden
- you do not want to patch the OS
- you need automatic scaling

VMs teach fundamentals.
Managed services teach platform thinking.
You need both.

### Azure Container Registry

Azure Container Registry stores Docker images.

Local pattern:

```text
docker build -t pokemon-api .
docker run pokemon-api
```

Cloud pattern:

```text
docker build -t myregistry.azurecr.io/pokemon-api:v1 .
docker push myregistry.azurecr.io/pokemon-api:v1
Azure pulls image and runs it
```

Design instinct:

- deployments should use immutable image tags
- production should not depend on building manually from a laptop
- registry access should be controlled

### Azure Container Apps

Azure Container Apps runs containers without making you manage Kubernetes directly.

It is a strong first cloud deployment target for your Pokemon app.

Use it when:

- you have containers
- you want simpler operations than Kubernetes
- you need HTTP services or background workers
- you want scaling without cluster management

Design instinct:

- good for learning real cloud deployment
- simpler than AKS
- still needs logs, secrets, networking, and database design

### Azure Kubernetes Service

AKS is managed Kubernetes.

Use it when:

- many services need orchestration
- you need Kubernetes-native workflows
- teams already understand Kubernetes
- you need advanced deployment patterns
- you need strong control over networking and runtime behavior

Do not jump to AKS just because it sounds advanced.

Kubernetes is powerful, but it adds operational complexity:

- cluster upgrades
- ingress
- network policies
- node pools
- autoscaling
- secrets
- service mesh decisions
- pod security
- observability

Master the simpler pattern first.
Then use AKS when you understand why you need it.

### Azure Database For PostgreSQL

This is managed Postgres.

Azure handles much of the platform layer, but you still own:

- schema
- indexes
- query performance
- database access
- backup policy
- maintenance choices
- connection security
- private networking
- cost

Design instinct:

- databases are high-risk dependencies
- make backups and restore drills non-negotiable
- use private access when possible
- do not put admin passwords in app files

### Azure Blob Storage

Blob Storage is durable object storage.

Use it for:

- database backups
- exported reports
- logs archive
- static assets
- disaster recovery artifacts

Design instinct:

- object storage is not a mounted disk in your app's brain
- it is great for durable blobs
- lifecycle rules can move old data to cheaper tiers
- access must be scoped carefully

### Azure Key Vault

Key Vault stores secrets, keys, and certificates.

Use it for:

- database passwords
- API keys
- signing secrets
- TLS certificates
- connection strings

Design instinct:

- secrets do not belong in Git
- secrets do not belong in plain `.env` files for production
- apps should use managed identity where possible
- access should be logged

### Microsoft Entra ID

Microsoft Entra ID is the identity platform behind Azure access.

It answers:

- who is this user
- what groups are they in
- what roles do they have
- should MFA be required
- should this login be blocked

Design instinct:

- cloud security starts with identity
- use groups and roles, not random one-off permissions
- avoid permanent high privilege
- separate human access from app access

### Azure Monitor And Log Analytics

Azure Monitor collects metrics, logs, alerts, and diagnostic data.

Log Analytics is where you query logs.

Design instinct:

- if you cannot observe it, you cannot operate it
- every production design needs logs, metrics, alerts, and runbooks
- alerts should indicate user-impacting or risk-increasing problems

### Azure Arc

Azure Arc lets Azure manage or govern resources that are not physically in Azure.

Examples:

- your Linux server
- on-prem Kubernetes
- servers in another cloud
- edge infrastructure

This is one of the most important hybrid concepts for you.

Mental model:

```text
My machine is not in Azure,
but Azure can see it, organize it, apply policy, collect signals, and help govern it.
```

Design instinct:

- Azure Arc is a bridge between on-prem and cloud management
- useful for inventory, governance, security posture, and hybrid operations
- it does not magically make local systems highly available

### Microsoft Defender For Cloud

Defender for Cloud helps assess and improve security posture across cloud and hybrid resources.

Use it to think about:

- exposed ports
- missing updates
- weak configurations
- insecure databases
- identity risk
- recommendations and compliance

Design instinct:

- security is not a one-time checklist
- posture management means continuously finding and reducing risk

### Copilot In Azure And AI Operations

AI is becoming part of infrastructure work.

The serious version is not "AI replaces engineers."
The serious version is:

```text
AI helps engineers inspect, summarize, query, generate commands, compare risk, and document faster.
```

Use AI carefully for:

- explaining logs
- drafting runbooks
- summarizing incidents
- generating Azure CLI examples
- creating design alternatives
- reviewing configuration risk
- turning messy notes into clean documentation

Do not blindly trust AI for:

- deleting resources
- changing firewall rules
- changing identity permissions
- production database operations
- incident decisions without evidence

Your edge is combining AI speed with engineering judgment.

## The Core Architecture Choices

### Choice 1: VM, Container Platform, Or Managed Service

When placing a workload, ask:

```text
Do I need to manage the machine?
```

If yes, VM may make sense.

Ask:

```text
Do I just need to run containers?
```

If yes, Container Apps or AKS may make sense.

Ask:

```text
Is this a common dependency that Azure can run for me?
```

If yes, managed database, storage, cache, queue, or identity may make sense.

Example:

```text
Pokemon API:
- containerized app
- stateless if designed well
- good fit for Azure Container Apps

Pokemon Postgres:
- stateful database
- high backup and recovery importance
- good fit for Azure Database for PostgreSQL

Pokemon backup files:
- durable blob artifacts
- good fit for Azure Blob Storage
```

### Choice 2: Public Or Private

Every endpoint must be classified.

Public:

- user-facing website
- public API gateway
- static website

Private:

- database
- Redis
- RabbitMQ
- admin dashboards
- internal APIs
- management ports

Rule:

```text
If users do not need direct access, it should not be public by default.
```

### Choice 3: Passwords Or Managed Identity

Old pattern:

```text
app has a password
app uses password to access secret/database/storage
```

Better Azure pattern where supported:

```text
app has a managed identity
Azure knows the app identity
permissions are assigned to that identity
no long-lived secret is stored in app config
```

Managed identity reduces secret sprawl.

### Choice 4: Manual Clicks Or Infrastructure As Code

Manual Azure portal changes are okay for learning.

Production infrastructure should move toward repeatable definitions:

- Bicep
- Terraform
- Pulumi
- Azure CLI scripts
- GitHub Actions workflows

Design instinct:

- if a system matters, you should be able to recreate it
- if a change is risky, it should be reviewed
- if setup steps are tribal memory, they should become documentation or code

### Choice 5: Best Effort Or Reliable

A system becomes reliable through design choices:

- health checks
- restart policy
- scaling rules
- backups
- restore drills
- multiple instances
- monitored dependencies
- limited blast radius
- rollback plans
- documented recovery

Reliability is not a feeling.
Reliability is evidence.

## The Infrastructure Engineer Thought Process

When someone says:

```text
We need to put this app in Azure.
```

Do not start by clicking buttons.

Start by asking:

1. What is the app's purpose?
2. Who uses it?
3. What data does it store?
4. What are the hard dependencies?
5. What must be public?
6. What must stay private?
7. What happens if it goes down?
8. What happens if data is lost?
9. What is the recovery target?
10. What logs and metrics prove health?
11. Who administers it?
12. How are secrets handled?
13. How is deployment performed?
14. How do we roll back?
15. What is the cheapest acceptable design that still meets risk requirements?

That is how you move from "person who knows commands" to "engineer who can design."

## Scalable, Reliable, Efficient, Lower-Risk

The role wording matters.

### Scalable

Scalable means the system can handle more demand without a full redesign.

Signals:

- stateless app instances
- horizontal scaling
- database connection management
- queue-based background work
- load balancing
- caching where appropriate
- clear resource limits

Bad scalable thinking:

```text
make the VM bigger forever
```

Better scalable thinking:

```text
run multiple app replicas, keep state in managed data services, and scale workers based on queue depth
```

### Reliable

Reliable means the system keeps working or recovers predictably.

Signals:

- health checks
- redundant app instances
- backup policy
- restore testing
- monitored dependencies
- alerts
- retry behavior
- graceful failure
- runbooks

Bad reliable thinking:

```text
it worked when I tried it once
```

Better reliable thinking:

```text
we tested failure, recovery, and alerts
```

### Efficient

Efficient means the system reduces wasted time, wasted compute, and manual labor.

Signals:

- automated deployments
- scripted checks
- right-sized resources
- lifecycle policies
- self-service runbooks
- less manual toil

Bad efficient thinking:

```text
I can manually fix it quickly
```

Better efficient thinking:

```text
the fix is automated, documented, and repeatable
```

### Lower-Risk

Lower-risk means fewer ways to cause damage and faster detection when something goes wrong.

Signals:

- least privilege
- private networking
- backups
- rollback plans
- change review
- audit logs
- segmentation
- secret rotation
- tested recovery

Bad lower-risk thinking:

```text
only I know how to do it
```

Better lower-risk thinking:

```text
the team can understand, operate, and recover it
```

## Documentation You Must Learn To Write

You asked specifically about documenting designs, solutions, processes, and improvements.

This is not optional extra work.
In infrastructure, documentation is part of the system.

### 1. Architecture Design Note

Use this when proposing or explaining a system.

Template:

```markdown
# Design: <system name>

## Problem
What are we solving?

## Goals
What must be true when this is done?

## Non-Goals
What are we intentionally not solving?

## Current State
How does it work today?

## Proposed Architecture
What changes?

## Components
- compute:
- network:
- data:
- identity:
- secrets:
- observability:

## Access Model
Who can access what?

## Reliability Model
How does it recover?

## Security Considerations
What risks exist and how are they reduced?

## Cost Considerations
What could become expensive?

## Rollout Plan
How do we deploy safely?

## Rollback Plan
How do we undo it?

## Open Questions
What still needs a decision?
```

### 2. Runbook

Use this when someone needs to operate or recover a system.

Template:

```markdown
# Runbook: <scenario>

## Symptoms
What would users or alerts show?

## Impact
Who or what is affected?

## First Checks
What commands, dashboards, or logs should be checked first?

## Likely Causes
What usually causes this?

## Mitigation
What can be done safely right now?

## Recovery Steps
How do we restore normal service?

## Verification
How do we prove it is fixed?

## Escalation
When do we involve another team/person?

## Follow-Up
What should be improved after the incident?
```

### 3. Change Proposal

Use this before changing something important.

Template:

```markdown
# Change Proposal: <change>

## Summary
One paragraph.

## Why Now
What pain, risk, or opportunity exists?

## Current Behavior
What happens today?

## Proposed Change
What will be different?

## Risk
What could go wrong?

## Verification Plan
How will we know it worked?

## Rollback Plan
How do we return to the previous state?

## Communication Plan
Who needs to know?
```

### 4. Workflow Improvement Note

Use this to suggest better processes.

Template:

```markdown
# Workflow Improvement: <workflow>

## Current Workflow
What does the team do today?

## Pain Points
Where is time wasted or risk created?

## Proposed Improvement
What should change?

## Expected Benefit
What gets faster, safer, clearer, or cheaper?

## Implementation Steps
How do we roll it out?

## Measurement
How will we know it helped?
```

This is how you show business value.
Not just "I built a thing."
More like:

```text
I reduced manual recovery time, lowered credential exposure, improved backup confidence, and made the platform easier for another engineer to operate.
```

## Azure Hybrid Reference Architecture For Pokemon

Start with your local system.

Possible local components:

```text
frontend
API
Postgres
Redis
RabbitMQ
worker
scraper
health check scripts
backup scripts
logs
Dockerfiles
```

Now map it to Azure.

### Version 1: Simple Cloud-Native

```text
User
  -> Azure Container Apps frontend/API
  -> Azure Database for PostgreSQL
  -> Azure Cache for Redis
  -> Azure Service Bus or managed RabbitMQ-compatible option
  -> Azure Blob Storage for backups/exports
  -> Azure Key Vault for secrets
  -> Azure Monitor for logs/metrics
```

Good for:

- learning managed services
- reducing host maintenance
- simple cloud deployment

Risk:

- you need to understand cost
- networking can still be misconfigured
- app changes may be needed for cloud services

### Version 2: Hybrid Local Plus Azure

```text
Local Linux host
  -> runs Pokemon containers
  -> local Postgres
  -> local health scripts
  -> Azure Arc for server visibility
  -> Azure Monitor for logs
  -> Azure Blob Storage for backups
  -> Azure Key Vault for production-like secrets
  -> Defender for Cloud for posture recommendations
```

Good for:

- learning hybrid without moving everything
- keeping local control
- practicing cloud operations around on-prem

Risk:

- local machine is still a single point of failure
- home network reliability is not enterprise reliability
- secret and network setup must be deliberate

### Version 3: Production-Style Hybrid

```text
Users
  -> public Azure entrypoint
  -> cloud app tier
  -> private database tier

Engineers
  -> VPN or secure access path
  -> private admin tools

On-prem
  -> internal services
  -> backup source
  -> Arc-managed servers
  -> monitoring agent

Azure
  -> central logging
  -> cloud database
  -> object storage
  -> identity
  -> security posture
  -> disaster recovery
```

Good for:

- real enterprise thinking
- identity and network boundary practice
- Future Standard-style infrastructure conversations

Risk:

- more moving pieces
- more documentation needed
- more governance needed

## Lab Rules

For every lab, you are not allowed to just write definitions.
You need evidence.

Every lesson must produce a file.

Use this exact pattern:

```text
future_standard_mastery/labs/azure_hybrid/<lesson_number>_<topic>.md
```

Every lab file must include:

```markdown
# <Lesson Name>

## What I Think Before

## Commands I Ran

## Evidence I Found

## What This Means

## Azure Translation

## Risk Or Tradeoff

## Next Action
```

For every lab:

1. Write what you think before touching commands.
2. Draw or describe the architecture.
3. Identify public and private surfaces.
4. Identify data that must survive.
5. Identify secrets.
6. Identify how health is verified.
7. Identify how recovery is tested.
8. Write a short engineer-style note when done.

Your output should prove understanding, not just command execution.

If a lesson says "design," you still do hands-on work first.
The design should come from what you observed.

## Lesson 1: Local Infra Is Already Infrastructure

### Intuition

Before Azure, understand what you already have.

Your Linux machine is doing jobs that cloud platforms also do:

- process hosting
- network binding
- storage
- secret injection
- logging
- backup execution
- dependency startup

Cloud is easier when you can say:

```text
I know what this machine is responsible for.
Now I can decide which responsibilities Azure should take.
```

### Task

Create a file:

```text
future_standard_mastery/labs/azure_hybrid/01_local_inventory.md
```

Document your Pokemon stack:

- services
- ports
- data stores
- secrets
- scripts
- health checks
- backup paths
- logs
- what breaks if your Linux machine shuts down

### How To Do It

Use repo inspection and local commands.

Suggested commands:

```bash
rg --files Pokemon
rg "ports:|POSTGRES|REDIS|RABBIT|DATABASE|SECRET|TOKEN|PASSWORD" Pokemon
find Pokemon -maxdepth 3 -type f -name "docker-compose*.yml" -o -name "*.env*" -o -name "Dockerfile"
```

Then write:

```markdown
# Local Inventory

## Services
...

## Ports
...

## Data
...

## Secrets
...

## Failure If Host Dies
...
```

### Mastery Check

You should be able to explain your local machine as if it were a tiny data center.

### Do This Now: Free Hands-On

Create the lab folder and first note:

```bash
mkdir -p shopify/future_standard_mastery/labs/azure_hybrid
touch shopify/future_standard_mastery/labs/azure_hybrid/01_local_inventory.md
```

Run these from the repo root:

```bash
rg --files shopify/Pokemon | sed -n '1,80p'
rg -n "ports:|POSTGRES|REDIS|RABBIT|DATABASE|SECRET|TOKEN|PASSWORD|localhost|127.0.0.1" shopify/Pokemon
find shopify/Pokemon -maxdepth 4 -type f \( -name "docker-compose*.yml" -o -name "*.env*" -o -name "Dockerfile" -o -name "*.sh" \)
```

Put this in `01_local_inventory.md`:

```markdown
# Local Inventory

## What I Think Before
I think my Linux machine is acting as the host, network boundary, secret holder, log source, and backup operator.

## Commands I Ran
- rg --files shopify/Pokemon
- rg -n "ports:|POSTGRES|REDIS|RABBIT|DATABASE|SECRET|TOKEN|PASSWORD|localhost|127.0.0.1" shopify/Pokemon
- find shopify/Pokemon -maxdepth 4 ...

## Evidence I Found
- services:
- ports:
- scripts:
- database references:
- queue/cache references:
- secrets/env references:

## What This Means

## Azure Translation
If this moved to Azure, compute could map to Container Apps or AKS, data to managed Postgres/storage, secrets to Key Vault, logs to Azure Monitor.

## Risk Or Tradeoff
If this one machine dies, everything local dies unless backups and restore are externalized.

## Next Action
Map responsibilities in Lesson 2.
```

Done means you can point to actual files and say what your machine is responsible for.

## Lesson 2: Cloud Responsibility Split

### Intuition

Cloud architecture is a responsibility split.

Ask:

```text
What do I want Azure to operate for me?
What do I still own?
```

Example:

```text
Azure Container Apps runs containers,
but I still own image quality, environment config, health behavior, logs, and app bugs.
```

### Task

Create:

```text
future_standard_mastery/labs/azure_hybrid/02_responsibility_matrix.md
```

Make a table:

| Component | Local responsibility | Azure option | Azure owns | I still own |
| --- | --- | --- | --- | --- |

Include:

- API
- frontend
- worker
- Postgres
- Redis
- RabbitMQ
- backups
- secrets
- logs
- alerts

### How To Do It

Use the Azure map in this guide.

Example row:

```markdown
| Postgres | install, patch, backup, monitor disk | Azure Database for PostgreSQL | database platform availability, managed backups depending on config | schema, queries, access, private networking, restore testing |
```

### Mastery Check

You should stop saying "move to cloud" vaguely.
You should say which responsibilities move and which remain.

### Do This Now: Free Hands-On

Create:

```bash
touch shopify/future_standard_mastery/labs/azure_hybrid/02_responsibility_matrix.md
```

Run:

```bash
rg -n "FROM |image:|build:|ports:|volumes:|depends_on:|POSTGRES|REDIS|RABBIT|DATABASE_URL" shopify/Pokemon
```

For every service or dependency you find, write one table row:

```markdown
| Component | Local responsibility | Azure option | Azure owns | I still own |
| --- | --- | --- | --- | --- |
| API | build image, run process, configure env, expose port | Azure Container Apps | container hosting, scaling platform, logs integration | code, image, env config, health endpoint, dependency behavior |
| Postgres | run DB container/server, store volume, back up, restore | Azure Database for PostgreSQL | managed DB platform, backup features depending on tier/config | schema, access, query health, restore drills, private networking |
```

Then add a section:

```markdown
## The First Thing I Would Move To Azure

I would move ___ first because ___.

## The Last Thing I Would Move To Azure

I would move ___ last because ___.
```

Done means you can explain cloud migration as a responsibility trade, not a vibe.

## Lesson 3: Public Vs Private Architecture

### Intuition

Security begins by deciding what should be reachable.

Most systems should not be fully public.

Example:

```text
Public:
- website
- public API route

Private:
- database
- cache
- queues
- admin endpoints
- metrics internals
```

### Task

Create:

```text
future_standard_mastery/labs/azure_hybrid/03_public_private_map.md
```

Classify each Pokemon component:

- public
- private app-to-app
- private admin-only
- local-only

Then explain the risk of making each private component public.

### How To Do It

Write a table:

| Component | Exposure | Who should access it | Risk if public |
| --- | --- | --- | --- |

Example:

```markdown
| Postgres | private | API only, admin through secure path | data theft, destructive access, credential attacks |
```

### Mastery Check

You should be able to reject bad designs calmly:

```text
We should not expose the database publicly because the API is the intended access boundary.
```

### Do This Now: Free Hands-On

Create:

```bash
touch shopify/future_standard_mastery/labs/azure_hybrid/03_public_private_map.md
```

Run:

```bash
rg -n "ports:|expose:|localhost|0.0.0.0|127.0.0.1|listen|bind|CORS|ALLOWED_HOSTS" shopify/Pokemon
```

Write this:

```markdown
# Public Private Map

| Component | Exposure | Who should access it | Risk if public | Safer pattern |
| --- | --- | --- | --- | --- |
| frontend | public | users | low/medium depending on auth | public HTTPS entrypoint |
| API | public or private behind frontend | users/app clients | abuse, auth attacks, data exposure | API gateway/reverse proxy, auth, rate limits |
| Postgres | private | API/admin only | data theft/destruction | private network, no public port, least privilege |
| Redis | private | API/worker only | cache poisoning/data leak | private network only |
| RabbitMQ | private/admin-only | worker/API/admin | queue tampering/admin exposure | private network, restricted admin UI |
```

Then answer:

```markdown
## The Dumbest Thing To Expose Publicly

The worst thing to expose would be ___ because ___.

## The Correct Public Entry Point

Users should enter through ___ because ___.
```

Done means you can draw the outside boundary of the system.

## Lesson 4: Azure Networking Basics

### Intuition

Azure networking is how you build private space in the cloud.

The important ideas:

- Virtual Network: private network boundary
- Subnet: smaller network zone
- NSG: traffic rules for subnet or network interface
- Public IP: internet reachable address
- Private Endpoint: private access to Azure services
- VPN Gateway: encrypted connection from on-prem to Azure
- ExpressRoute: private enterprise circuit to Azure

Your first design does not need every piece.
But you must understand what each one is for.

### Task

Create:

```text
future_standard_mastery/labs/azure_hybrid/04_azure_network_design.md
```

Design a VNet for Pokemon:

```text
vnet-pokemon-dev
  subnet-public-entry
  subnet-app
  subnet-data
  subnet-private-endpoints
```

For each subnet, explain:

- what belongs there
- what should be allowed inbound
- what should be allowed outbound
- what should be blocked

### How To Do It

Use this starting point:

```markdown
# Azure Network Design

## VNet
Name:
Address space:

## Subnets

### subnet-public-entry
Purpose:
Allowed inbound:
Allowed outbound:
Blocked:

### subnet-app
...
```

### Mastery Check

You should understand that networks are design boundaries, not just IP addresses.

### Do This Now: Free Hands-On

Create:

```bash
touch shopify/future_standard_mastery/labs/azure_hybrid/04_azure_network_design.md
```

Do a local network inspection first:

```bash
ss -tulpen
ip addr
ip route
docker network ls
```

If Docker is running and you have networks:

```bash
docker network inspect bridge
```

Write:

```markdown
# Azure Network Design

## What I Saw Locally
- listening ports:
- local IPs:
- Docker networks:
- default route:

## Azure Translation

| Local idea | Azure idea | Why it matters |
| --- | --- | --- |
| Docker bridge network | VNet/subnet | private communication boundary |
| host listening port | public/private endpoint | decides who can reach the service |
| localhost-only service | private-only service | not reachable from internet |

## Proposed VNet
Name: vnet-pokemon-dev
Address space: 10.20.0.0/16

| Subnet | CIDR | Belongs here | Inbound | Outbound | Block |
| --- | --- | --- | --- | --- | --- |
| subnet-public-entry | 10.20.1.0/24 | gateway/reverse proxy | HTTPS from internet | app subnet | direct DB access |
| subnet-app | 10.20.2.0/24 | API/workers | entry subnet only | data/private endpoints | internet inbound |
| subnet-data | 10.20.3.0/24 | DB/cache/queue if self-hosted | app subnet only | backup/log destinations | public inbound |
| subnet-private-endpoints | 10.20.4.0/24 | Azure private endpoints | app/data only | Azure services | public inbound |
```

Done means you can translate local ports into cloud network boundaries.

## Lesson 5: Identity, Access, And Secrets

### Intuition

Security is mostly identity plus boundaries.

Questions:

- who are you
- what are you allowed to do
- how do we know it was you
- where are the credentials
- can we remove the credential entirely

Azure gives you:

- Microsoft Entra ID for human and workload identity
- Role-Based Access Control for permissions
- Managed Identity for Azure-hosted apps
- Key Vault for secrets

### Task

Create:

```text
future_standard_mastery/labs/azure_hybrid/05_identity_secret_model.md
```

Design access for:

- human admin
- developer
- app runtime
- backup script
- monitoring integration

For each, define:

- identity type
- permissions needed
- permissions not needed
- secret storage
- audit concern

### How To Do It

Example:

```markdown
| Actor | Identity | Needs | Does not need | Secret model | Audit concern |
| --- | --- | --- | --- | --- | --- |
| API container | Managed identity | read app secrets, connect to database | owner access to subscription | no stored cloud password | alert on unexpected secret reads |
```

### Mastery Check

You should be able to explain least privilege in concrete terms.

### Do This Now: Free Hands-On

Create:

```bash
touch shopify/future_standard_mastery/labs/azure_hybrid/05_identity_secret_model.md
```

Find possible secrets and identity assumptions:

```bash
rg -n "PASSWORD|SECRET|TOKEN|KEY|DATABASE_URL|REDIS_URL|RABBIT|USER|USERNAME|AUTH|JWT" shopify/Pokemon
find shopify/Pokemon -maxdepth 4 -type f \( -name "*.env*" -o -name "*.yml" -o -name "*.yaml" -o -name "*.sh" \)
```

Write:

```markdown
# Identity And Secret Model

## Secret Candidates I Found
- name:
- file/reference:
- purpose:
- should it be in Key Vault later:

## Access Table

| Actor | Identity | Needs | Does Not Need | Secret Model | Audit Concern |
| --- | --- | --- | --- | --- | --- |
| developer | Entra user/group later | deploy/read logs in dev | production owner | no shared passwords | privilege creep |
| API container | managed identity later | read app secrets, connect DB | subscription owner | Key Vault/managed identity | unexpected secret reads |
| backup script | workload identity/service principal later | write backup blobs | read all resources | scoped storage access | backup overwrite/delete |
```

Then answer:

```markdown
## One Permission I Would Refuse To Give

I would not give ___ to ___ because ___.
```

Done means you can say exactly who needs access to what.

## Lesson 6: Data, Backups, And Recovery

### Intuition

Data is where infrastructure gets serious.

A stateless app can be redeployed.
A lost database can end a business process.

You need to know:

- RPO: how much data loss is acceptable
- RTO: how long recovery can take
- backup frequency
- backup location
- restore test process
- access controls
- encryption

RPO example:

```text
If backups run every 24 hours, worst-case loss may be near 24 hours.
```

RTO example:

```text
If restore takes 2 hours, users may be impacted for 2 hours.
```

### Task

Create:

```text
future_standard_mastery/labs/azure_hybrid/06_backup_recovery_design.md
```

Design a backup and recovery plan:

- local Postgres backup
- upload to Azure Blob Storage
- retention policy
- restore drill
- verification query
- who can read backups
- what happens if local machine dies

### How To Do It

Write:

```markdown
# Backup And Recovery Design

## Data Classification
...

## Backup Flow
Local Postgres -> dump file -> compression -> Azure Blob Storage -> retention

## RPO
...

## RTO
...

## Restore Drill
...

## Access Control
...

## Risks
...
```

### Mastery Check

You should understand that a backup is not real until restore has been tested.

### Do This Now: Free Hands-On

Create:

```bash
touch shopify/future_standard_mastery/labs/azure_hybrid/06_backup_recovery_design.md
```

Inspect the existing backup drill:

```bash
sed -n '1,240p' shopify/Pokemon/scripts/postgres_backup_drill.sh
rg -n "pg_dump|pg_restore|psql|backup|restore|POSTGRES|DATABASE" shopify/Pokemon
```

Then write the actual recovery design:

```markdown
# Backup And Recovery Design

## Current Backup Evidence
- script:
- command used:
- output location:
- restore command or gap:

## RPO
Target:
Reason:

## RTO
Target:
Reason:

## Free Local Drill
1. Run the existing backup script.
2. Confirm the backup file exists.
3. Record file size and timestamp.
4. Identify the exact restore command.
5. Write the verification query.

## Azure Later
Local Postgres -> dump -> compress -> upload to private Blob container -> lifecycle retention -> restore drill.

## Verification Query
Use a query like: SELECT COUNT(*) FROM <important_table>;

## Risk
A backup file that has never been restored is only a hope, not a recovery plan.
```

If your local DB is not running, still complete the design and mark the blocker.
Done means you know the difference between "backup exists" and "restore works."

## Lesson 7: Observability And AI-Assisted Operations

### Intuition

Operations means seeing the system clearly enough to act.

Observability includes:

- logs: what happened
- metrics: how much, how fast, how many
- traces: where time went across services
- alerts: when humans need to act
- dashboards: current state and trends

AI can help summarize and investigate, but the raw evidence still matters.

Good AI use:

```text
Summarize these logs and suggest likely causes.
```

Bad AI use:

```text
Change production networking because the model guessed.
```

### Task

Create:

```text
future_standard_mastery/labs/azure_hybrid/07_observability_aiops_plan.md
```

Design an observability plan:

- key health checks
- logs to collect
- metrics to track
- alerts to create
- dashboard sections
- AI prompts you would use during an incident
- rules for verifying AI suggestions

### How To Do It

Example alert table:

| Signal | Why it matters | Alert threshold | First check |
| --- | --- | --- | --- |
| API 5xx rate | user impact | above normal for 5 minutes | app logs and dependency health |
| Postgres connection failures | app cannot use DB | any sustained failures | DB status, secrets, networking |
| Backup missing | recovery risk | no backup in 24 hours | backup script logs, storage upload |

Example AI prompt:

```text
Given these API logs, classify the failure as app bug, dependency failure, network issue, or auth issue. Show the evidence for each claim and list the first three checks I should run.
```

### Mastery Check

You should know what evidence you need before an incident happens.

### Do This Now: Free Hands-On

Create:

```bash
touch shopify/future_standard_mastery/labs/azure_hybrid/07_observability_aiops_plan.md
```

Inspect health and logs:

```bash
sed -n '1,240p' shopify/Pokemon/scripts/health-check.sh
rg -n "health|ready|live|metrics|logger|logging|console.log|print\\(|error|warn" shopify/Pokemon
```

If containers are running:

```bash
docker ps
docker logs --tail 80 <container-name-or-id>
```

Write:

```markdown
# Observability And AIOps Plan

## Current Health Checks
- script:
- endpoints/commands:
- what it proves:
- what it does not prove:

## Logs I Can Inspect
- service:
- where logs appear:
- useful error strings:

## Alerts I Would Create

| Signal | Why It Matters | Alert Threshold | First Check |
| --- | --- | --- | --- |
| API health fails | user impact | 2 failures in 5 minutes | health-check output and API logs |
| DB connection error | app cannot use data | sustained errors | DB container/status, secrets, network |
| backup missing | recovery risk | no backup in 24 hours | backup script log and backup directory |

## AI Incident Prompt
Given these logs and health-check results, classify the issue as app bug, dependency failure, network issue, auth/secret issue, or resource exhaustion. Quote the evidence and list the next three checks.

## AI Verification Rule
I will not run destructive commands from AI unless I can explain the evidence and rollback.
```

Done means you have an incident evidence checklist before an incident.

## Lesson 8: Deployment And Automation

### Intuition

Manual deployment does not scale.

A professional platform has repeatable movement:

```text
code change
  -> test
  -> build image
  -> push image
  -> deploy
  -> verify
  -> rollback if needed
```

For Azure:

```text
GitHub Actions
  -> Docker build
  -> Azure Container Registry
  -> Azure Container Apps or AKS
  -> Azure Monitor verification
```

### Task

Create:

```text
future_standard_mastery/labs/azure_hybrid/08_deployment_design.md
```

Design a deployment pipeline for Pokemon.

Include:

- trigger
- tests
- image build
- image tag
- registry
- deployment target
- secrets handling
- smoke test
- rollback

### How To Do It

Use this structure:

```markdown
# Deployment Design

## Flow
1. Developer opens PR
2. Tests run
3. Image builds
4. Image is pushed to ACR
5. Deployment updates Container App
6. Smoke test verifies health

## Rollback
Previous image tag:
Rollback command/process:
Verification:
```

### Mastery Check

You should understand deployment as a controlled system, not a lucky command.

### Do This Now: Free Hands-On

Create:

```bash
touch shopify/future_standard_mastery/labs/azure_hybrid/08_deployment_design.md
```

Inspect build/deploy surfaces:

```bash
find shopify/Pokemon -maxdepth 5 -type f \( -name "Dockerfile" -o -name "docker-compose*.yml" -o -name "*.yml" -o -name "*.yaml" \)
rg -n "docker build|docker compose|image:|build:|ports:|healthcheck|CMD|ENTRYPOINT" shopify/Pokemon
```

Write:

```markdown
# Deployment Design

## Current Local Build Evidence
- Dockerfile(s):
- compose files:
- startup command:
- healthcheck:

## Free Local Deployment Loop
1. Build image locally.
2. Run container or compose stack.
3. Run health check.
4. Stop the service.
5. Start again.
6. Confirm data behavior.

## Azure Later
GitHub Actions -> tests -> docker build -> push to ACR -> deploy to Container Apps -> smoke test.

## Image Tag Rule
Use immutable tags like commit SHA for real deployments.

## Rollback
Redeploy previous known-good image tag and verify health endpoint.
```

Optional local build command after you identify the Dockerfile:

```bash
docker build -t pokemon-api:local -f shopify/Pokemon/services/api-consumer/Dockerfile shopify/Pokemon/services/api-consumer
```

Done means you can describe deployment as a repeatable pipeline.

## Lesson 9: Hybrid With Azure Arc

### Intuition

Azure Arc is the bridge between "my server exists outside Azure" and "I want Azure governance and visibility."

It is useful when:

- workloads remain on-prem
- a company has multiple environments
- servers need central inventory
- security posture should be visible
- policy and monitoring need consistency

It does not remove the need to understand the local machine.

### Task

Create:

```text
future_standard_mastery/labs/azure_hybrid/09_arc_hybrid_plan.md
```

Design how your Linux host would connect to Azure Arc.

Include:

- what metadata you want visible in Azure
- what logs should be collected
- what security recommendations matter
- what policies would be useful
- what should remain local
- what risks Arc does not solve

### How To Do It

Write an architecture like:

```text
Local Linux host
  -> Azure Connected Machine agent
  -> Azure Arc
  -> Log Analytics
  -> Defender for Cloud
  -> Azure Policy
```

Then write:

```markdown
## What Azure Can Help Govern
...

## What Still Remains My Responsibility
...
```

### Mastery Check

You should be able to explain hybrid management without pretending the cloud magically owns the local machine.

### Do This Now: Free Hands-On

Create:

```bash
touch shopify/future_standard_mastery/labs/azure_hybrid/09_arc_hybrid_plan.md
```

Inventory your local host like Azure Arc would:

```bash
hostnamectl
uname -a
df -h
free -h
ss -tulpen
systemctl --type=service --state=running --no-pager
```

Write:

```markdown
# Azure Arc Hybrid Plan

## Local Host Inventory
- hostname:
- OS:
- kernel:
- CPU/memory summary:
- disk summary:
- listening ports:
- important running services:

## What Azure Arc Would Help With
- inventory:
- governance:
- security posture:
- monitoring:
- policy visibility:

## What Azure Arc Does Not Solve
- my local power/network reliability:
- bad app code:
- missing restore test:
- wrong firewall exposure:
- weak secrets:

## Hybrid Architecture
Local Linux host -> Azure Arc -> Log Analytics -> Defender for Cloud -> Azure Policy.
```

Done means you understand Arc as visibility/governance, not magic high availability.

## Lesson 10: Cost And Right-Sizing

### Intuition

Cloud makes it easy to create resources.
That means it is also easy to create waste.

Cost-aware engineers ask:

- what runs 24/7
- what can scale to zero
- what storage tier fits the data
- what logs are worth retaining
- what environment is dev vs prod
- what can be deleted
- what has budget alerts

### Task

Create:

```text
future_standard_mastery/labs/azure_hybrid/10_cost_model.md
```

Estimate cost risk for your design.

Do not worry about exact prices at first.
Classify resources:

- low cost risk
- medium cost risk
- high cost risk

Explain why.

### How To Do It

Use this table:

| Resource | Cost driver | Risk level | Control |
| --- | --- | --- | --- |
| Container Apps | CPU/memory, replicas, traffic | medium | min replicas, autoscale rules |
| Log Analytics | ingestion and retention | medium | filter noisy logs, set retention |
| Blob Storage | size, tier, transactions | low/medium | lifecycle rules |
| Database | compute size, storage, backups | high | right-size, monitor usage |

### Mastery Check

You should know that good architecture includes cost controls.

### Do This Now: Free Hands-On

Create:

```bash
touch shopify/future_standard_mastery/labs/azure_hybrid/10_cost_model.md
```

Do a local "cost" model first using resource pressure:

```bash
du -sh shopify/Pokemon
find shopify/Pokemon -type f -printf '%s %p\n' | sort -nr | sed -n '1,25p'
docker system df
```

If Docker is not running, record that and continue.

Write:

```markdown
# Cost Model

## Local Resource Signals
- repo size:
- largest files:
- Docker image/container/storage usage:

## Azure Cost Risk Table

| Resource | Cost Driver | Risk Level | Control |
| --- | --- | --- | --- |
| Container Apps | CPU/memory, replicas, traffic | medium | scale rules, min replicas, dev shutdown |
| Log Analytics | ingestion and retention | medium | avoid noisy logs, retention policy |
| Blob Storage | data size, tier, operations | low/medium | lifecycle rules, delete old lab data |
| Database | compute tier, storage, backups | high | smallest dev tier, stop/delete labs, monitor |

## Budget Rule
Before creating Azure resources, create a budget alert and delete lab resource groups when done.
```

Done means you can name what creates cost before you create it.

## Lesson 11: Risk Profile Improvement

### Intuition

"Improve risk profile" means make the system less likely to fail badly, leak data, or depend on undocumented human memory.

Examples:

- move secrets to Key Vault
- remove public database access
- add backups and restore drills
- add alerts for missing backups
- use least privilege
- document runbooks
- reduce manual deploy steps
- add health checks
- segment networks
- patch hosts

### Task

Create:

```text
future_standard_mastery/labs/azure_hybrid/11_risk_register.md
```

Build a risk register for Pokemon.

Include at least 10 risks.

Table:

| Risk | Impact | Likelihood | Current control | Better control | Owner | Priority |
| --- | --- | --- | --- | --- | --- | --- |

### How To Do It

Example:

```markdown
| DB backup not restorable | high | medium | backup script exists | monthly restore drill plus alert on missing backup | infra | P1 |
```

### Mastery Check

You should be able to connect engineering work to business risk reduction.

### Do This Now: Free Hands-On

Create:

```bash
touch shopify/future_standard_mastery/labs/azure_hybrid/11_risk_register.md
```

Use evidence from Lessons 1-10 and write at least 10 rows:

```markdown
# Risk Register

| Risk | Impact | Likelihood | Current Control | Better Control | Owner | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| Local machine is single point of failure | high | medium | local scripts | external backups, documented restore, cloud deploy option | infra | P1 |
| Secrets in local env/files | high | medium | local file permissions | Key Vault later, least privilege, rotation | infra/app | P1 |
| Database exposed accidentally | high | low/medium | compose/local defaults | private network, no public DB, firewall rules | infra | P1 |
| Backup not restorable | high | medium | backup script | restore drill and alert | infra | P1 |
```

Then add:

```markdown
## Top 3 Improvements
1. 
2. 
3. 

## Why These Reduce Risk
```

Done means every improvement you suggest is tied to a risk.

## Lesson 12: Final Capstone Design

### Intuition

This is where you stop learning pieces and start acting like the engineer who owns the platform.

You are going to write a real design packet.

### Task

Create:

```text
future_standard_mastery/labs/azure_hybrid/12_capstone_azure_hybrid_design.md
```

Write a complete design for:

```text
Pokemon Azure Hybrid Platform
```

Required sections:

- executive summary
- current local architecture
- proposed Azure/hybrid architecture
- compute design
- network design
- data design
- identity and secrets design
- observability design
- backup and recovery design
- deployment design
- security controls
- cost controls
- risks and mitigations
- rollout plan
- rollback plan
- open questions
- future improvements

### How To Do It

Use this skeleton:

```markdown
# Pokemon Azure Hybrid Platform Design

## Executive Summary
This design moves the Pokemon platform from a single local operational model toward a hybrid Azure model that improves visibility, backup durability, secret handling, and deployment repeatability while preserving a local learning environment.

## Current Local Architecture
...

## Proposed Architecture
...

## Compute
...

## Network
...

## Data
...

## Identity And Secrets
...

## Observability
...

## Backup And Recovery
...

## Deployment
...

## Security Controls
...

## Cost Controls
...

## Risks And Mitigations
...

## Rollout Plan
...

## Rollback Plan
...

## Open Questions
...

## Future Improvements
...
```

### Mastery Check

You should be able to hand this to another engineer and have them understand the system, the tradeoffs, the risks, and the next steps.

### Do This Now: Free Hands-On

Create:

```bash
touch shopify/future_standard_mastery/labs/azure_hybrid/12_capstone_azure_hybrid_design.md
```

Use your previous 11 lab files as source material.

Do not invent from thin air.
Reference your evidence:

```markdown
# Pokemon Azure Hybrid Platform Design

## Executive Summary
One paragraph explaining the move from local-only to hybrid-ready.

## Evidence Used
- 01_local_inventory.md
- 02_responsibility_matrix.md
- 03_public_private_map.md
- 04_azure_network_design.md
- 05_identity_secret_model.md
- 06_backup_recovery_design.md
- 07_observability_aiops_plan.md
- 08_deployment_design.md
- 09_arc_hybrid_plan.md
- 10_cost_model.md
- 11_risk_register.md

## Current Local Architecture

## Proposed Hybrid Architecture

## What I Would Build First For Free
1. local inventory
2. backup restore drill
3. public/private map
4. risk register
5. deployment design

## What I Would Build First In Azure
1. budget/resource group
2. Blob backup target
3. Key Vault
4. ACR
5. Container Apps deployment

## Risks And Mitigations

## Rollout Plan

## Rollback Plan

## Open Questions
```

Done means you have a portfolio-quality artifact, not notes.

## Hands-On Build Path With Azure

Do these only after you finish the design labs above.

The design work builds your intuition.
The hands-on work proves it.

Before any Azure build, do the safety setup:

```bash
az login
az account show --output table
az group create --name rg-pokemon-dev --location eastus
```

Then create a budget alert in the Azure portal for the subscription or resource group before you create paid resources.
Azure pricing/free grants change, so verify the cost screen before pressing create.

Cleanup command for the whole lab environment:

```bash
az group delete --name rg-pokemon-dev
```

Only run cleanup when you are sure everything inside that resource group is disposable.

### Build 1: Azure Account Hygiene

Goal:

- create a clean subscription/resource group structure
- set budgets
- set naming conventions

Tasks:

- create `rg-pokemon-dev`
- create a budget alert
- define naming standards
- document cleanup commands

Evidence:

- resource group name
- budget screenshot or note
- naming convention doc

How:

```bash
az login
az account show --output table
az group create --name rg-pokemon-dev --location eastus
az resource list --resource-group rg-pokemon-dev --output table
```

Write:

```markdown
# Azure Account Hygiene

## Subscription

## Resource Group
rg-pokemon-dev

## Region
eastus

## Budget Alert
Created: yes/no
Threshold:

## Naming Convention
- resource group: rg-<app>-<env>
- storage: st<app><env><random>
- key vault: kv-<app>-<env>-<random>
- container registry: acr<app><env><random>

## Cleanup Plan
Delete rg-pokemon-dev after labs.
```

### Build 2: Blob Backup Target

Goal:

- send local Postgres backups to Azure Blob Storage

Tasks:

- create storage account
- create private container for backups
- upload a test file
- update backup drill documentation
- test download and restore path

Evidence:

- backup file appears in Blob Storage
- restore procedure is documented
- access is not public

How:

Storage account names must be globally unique and lowercase.
Replace the placeholder with your own name.

```bash
az storage account create \
  --name stpokemondev12345 \
  --resource-group rg-pokemon-dev \
  --location eastus \
  --sku Standard_LRS

az storage container create \
  --name backups \
  --account-name stpokemondev12345 \
  --auth-mode login

az storage blob upload \
  --account-name stpokemondev12345 \
  --container-name backups \
  --name test-backup.txt \
  --file shopify/future_standard_mastery/labs/azure_hybrid/06_backup_recovery_design.md \
  --auth-mode login

az storage blob list \
  --account-name stpokemondev12345 \
  --container-name backups \
  --output table \
  --auth-mode login
```

Write what happened in:

```text
future_standard_mastery/labs/azure_hybrid/azure_build_02_blob_backup.md
```

### Build 3: Key Vault For Secrets

Goal:

- move production-like secrets out of local plain files

Tasks:

- create Key Vault
- add test secret
- retrieve it with Azure CLI
- document which Pokemon secrets belong there
- define who can read or manage secrets

Evidence:

- secret retrieval works
- access model documented

How:

Key Vault names must be globally unique.

```bash
az keyvault create \
  --name kv-pokemon-dev-12345 \
  --resource-group rg-pokemon-dev \
  --location eastus

az keyvault secret set \
  --vault-name kv-pokemon-dev-12345 \
  --name pokemon-demo-secret \
  --value "replace-me-demo-value"

az keyvault secret show \
  --vault-name kv-pokemon-dev-12345 \
  --name pokemon-demo-secret \
  --query value \
  --output tsv
```

Do not put real production secrets in a learning lab.

Write:

```text
future_standard_mastery/labs/azure_hybrid/azure_build_03_key_vault.md
```

### Build 4: Container Registry

Goal:

- push Pokemon container images to Azure Container Registry

Tasks:

- create ACR
- build an image locally
- tag image for ACR
- push image
- document image naming and versioning

Evidence:

- image exists in ACR
- version tag is documented

How:

ACR names must be globally unique and alphanumeric.

```bash
az acr create \
  --name acrpokemondev12345 \
  --resource-group rg-pokemon-dev \
  --sku Basic

az acr login --name acrpokemondev12345

docker build \
  -t acrpokemondev12345.azurecr.io/pokemon-api:local \
  -f shopify/Pokemon/services/api-consumer/Dockerfile \
  shopify/Pokemon/services/api-consumer

docker push acrpokemondev12345.azurecr.io/pokemon-api:local

az acr repository list \
  --name acrpokemondev12345 \
  --output table
```

If the Docker build fails, that is still learning.
Record the error and identify whether it is a missing dependency, wrong build context, Dockerfile issue, or auth issue.

### Build 5: Container App Deployment

Goal:

- run one Pokemon service in Azure Container Apps

Tasks:

- deploy API or simple worker first
- configure environment variables
- connect to logs
- define health check
- test endpoint

Evidence:

- service runs
- logs visible
- health check passes

How:

Only do this after Build 4 succeeds.

```bash
az extension add --name containerapp

az containerapp env create \
  --name cae-pokemon-dev \
  --resource-group rg-pokemon-dev \
  --location eastus

az containerapp create \
  --name ca-pokemon-api-dev \
  --resource-group rg-pokemon-dev \
  --environment cae-pokemon-dev \
  --image acrpokemondev12345.azurecr.io/pokemon-api:local \
  --target-port 8080 \
  --ingress external \
  --registry-server acrpokemondev12345.azurecr.io

az containerapp show \
  --name ca-pokemon-api-dev \
  --resource-group rg-pokemon-dev \
  --query properties.configuration.ingress.fqdn \
  --output tsv

az containerapp logs show \
  --name ca-pokemon-api-dev \
  --resource-group rg-pokemon-dev
```

The port may need to change based on your actual API container.
Use your Dockerfile/app config as the source of truth.

### Build 6: Managed Postgres

Goal:

- understand managed database setup

Tasks:

- create Azure Database for PostgreSQL in dev
- configure access carefully
- migrate sample schema/data
- connect app or test client
- document backup and restore options

Evidence:

- connection succeeds
- sample query works
- access model documented

### Build 7: Azure Monitor

Goal:

- centralize operational signals

Tasks:

- create Log Analytics workspace
- send app logs
- create at least three useful queries
- create one alert
- document first-check workflow

Evidence:

- query results exist
- alert design is documented

### Build 8: Azure Arc For Local Linux

Goal:

- connect local infrastructure into Azure governance

Tasks:

- onboard local Linux host or test VM to Azure Arc
- confirm inventory visibility
- connect monitoring/security recommendations where appropriate
- document what Azure sees and what it does not control

Evidence:

- Arc resource visible
- hybrid responsibility split documented

### Build 9: CI/CD Pipeline

Goal:

- automate build and deploy

Tasks:

- GitHub Actions workflow
- test step
- Docker build
- push to ACR
- deploy to Container Apps
- smoke test
- rollback note

Evidence:

- pipeline run link or notes
- image tag
- deployment verification

### Build 10: Full Design Review

Goal:

- act like this is a real platform review

Tasks:

- write final design packet
- write runbook
- write risk register
- write cost controls
- write incident scenario
- write improvement backlog

Evidence:

- capstone design
- runbook
- risk register
- backlog

## Commands To Learn Gradually

You do not need to memorize these all at once.
Know what each category is for.

### Azure CLI Basics

```bash
az login
az account show
az group list
az group create --name rg-pokemon-dev --location eastus
az resource list --resource-group rg-pokemon-dev --output table
```

### Storage

```bash
az storage account list --output table
az storage container list --account-name <storage-account>
az storage blob upload --account-name <storage-account> --container-name backups --file <file>
az storage blob list --account-name <storage-account> --container-name backups --output table
```

### Container Registry

```bash
az acr list --output table
az acr login --name <registry-name>
docker tag pokemon-api <registry-name>.azurecr.io/pokemon-api:v1
docker push <registry-name>.azurecr.io/pokemon-api:v1
```

### Logs

```bash
az monitor log-analytics workspace list --output table
az monitor metrics list-definitions --resource <resource-id>
```

### Resource Cleanup

Be careful with cleanup.
Only delete lab resource groups when you are sure nothing important is inside.

```bash
az group delete --name rg-pokemon-dev
```

## What To Say In An Interview

Weak answer:

```text
I know Azure and hybrid cloud.
```

Strong answer:

```text
I practiced mapping a local Docker-based application to Azure and hybrid architecture. I broke the system into compute, network, data, identity, and operations layers. For the hybrid model, I kept local Linux infrastructure visible through Azure Arc, moved backups to Azure Blob Storage, planned secrets through Key Vault, and designed centralized monitoring through Azure Monitor. I also wrote a risk register, recovery plan, and deployment design so the architecture was operable, not just deployable.
```

That is the difference between buzzword knowledge and engineering maturity.

## Mastery Rubric

Use this to grade yourself.

### Level 1: Familiar

You can define:

- VM
- container
- VNet
- subnet
- storage account
- Key Vault
- managed identity
- Azure Monitor
- Azure Arc

### Level 2: Practical

You can:

- create a resource group
- upload backups to Blob Storage
- push image to ACR
- deploy a container
- store a secret in Key Vault
- inspect logs
- write a basic runbook

### Level 3: Design Capable

You can:

- choose between VM, Container Apps, AKS, and managed services
- classify public vs private endpoints
- design backup and restore
- explain RPO and RTO
- design least privilege access
- write a change proposal
- identify cost and risk tradeoffs

### Level 4: Hybrid Engineer

You can:

- explain Azure Arc clearly
- connect local/on-prem thinking to Azure governance
- design hybrid monitoring
- design secure admin access
- explain what happens if cloud/on-prem connectivity fails
- document responsibility boundaries

### Level 5: Platform-Minded

You can:

- reduce manual toil
- improve reliability with evidence
- reduce security risk
- automate repeatable deployment
- explain tradeoffs to technical and non-technical people
- propose workflow improvements
- build systems other people can operate

This is the level you are aiming for.

## The Final Mindset

Do not chase cloud as a trophy.

Chase the ability to make systems:

- clearer
- safer
- more recoverable
- easier to operate
- easier to explain
- less dependent on heroics

That is infrastructure mastery.

Azure is the platform.
Hybrid is the operating reality.
Documentation is how the team trusts the system.
Automation is how the system stops depending on memory.
Observability is how you know what is true.
Security is how you reduce blast radius.
Recovery is how you prove the business can survive failure.

If you can connect all of that, you are not just "learning cloud."
You are becoming the kind of engineer who can own a technical platform.
