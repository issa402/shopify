# Future Standard Infra Idea Playbook

Use this file when you get access to a company GitHub org, repo, AWS account, or project board and do not know where to start.

The job is not to randomly suggest cloud tools. The job is to find operational risk, reduce manual work, improve reliability/security, and explain the business value clearly.

## First Week Goal

Your first goal is to become useful without breaking anything.

Do read-only discovery first:

1. Identify the systems and repos you are expected to support.
2. Map runtime dependencies: app, database, cache, queue, storage, identity, CI/CD, cloud.
3. Find how deployments happen.
4. Find where logs, alerts, incidents, and runbooks live.
5. Find access gaps: GitHub teams, AWS roles, project boards, docs, VPN, monitoring tools.
6. Bring one small improvement idea backed by evidence.

## Plausible Future Standard Infra Needs

These are realistic needs for a global infrastructure team based on the role description: system administration, cloud, hybrid infrastructure, security, workplace, network, support, operations, and agile delivery.

| Area | Plausible need | High-value idea you can bring | Evidence to look for |
| --- | --- | --- | --- |
| Repo visibility | Engineers may not know which repos map to which systems. | Create a repo-to-system inventory with owners, runtime, deploy path, and support tier. | GitHub repos, README files, CODEOWNERS, workflows, Dockerfiles, Terraform. |
| Access control | GitHub teams/projects may not match who actually supports systems. | Propose a quarterly access review for GitHub teams, AWS IAM roles, and project permissions. | GitHub teams, repo permissions, CODEOWNERS, AWS IAM roles, SSO groups. |
| CI/CD safety | Deployments may depend on tribal knowledge or manual steps. | Add deploy checklists and read-only CI gates for secrets, Docker exposure, and config drift. | GitHub Actions, Jenkins, GitLab CI, release docs, deployment scripts. |
| Observability | Services may run without clear health checks, dashboards, or actionable alerts. | Create service health/readiness standards and dashboard inventory. | `/health` endpoints, CloudWatch, Datadog, Splunk, Grafana, logs, alert policies. |
| Incident response | People may debug from memory instead of a runbook. | Build incident runbook templates and an incident snapshot script. | Previous incidents, Slack/Teams channels, monitoring alerts, runbooks. |
| Hybrid cloud | Some systems may be on-prem, some in AWS/Azure/SaaS. | Build a hybrid dependency map: network paths, identity, data flows, support owners. | VPN docs, DNS zones, firewall rules, AWS VPCs, Azure VNets, on-prem hosts. |
| Security baseline | Secrets, public ports, weak config, or missing patch visibility may exist. | Start with read-only config and exposure audits before proposing changes. | `.env`, compose files, Terraform, security groups, SSM/Secrets Manager, endpoint tools. |
| Cost control | Cloud spend may be hard to explain by app/team/environment. | Propose tagging hygiene and a weekly cost snapshot report. | AWS tags, Cost Explorer, unused EBS, old snapshots, idle load balancers, NAT gateways. |
| AI governance | AI use may be fragmented across teams. | Propose an AI use-case register with risk tier, data class, owner, model/provider, and review status. | ChatGPT/Claude usage, internal tools, prompts, data flows, policies. |
| AI operations | Teams may want AI but lack safe operational use cases. | Start with low-risk AI: doc search, runbook summarization, incident summaries, ticket triage, codebase Q&A. | Support tickets, docs, runbooks, incident notes, repeated Slack/Teams questions. |

## What High-Value Companies Are Doing

Use these patterns as idea fuel, not as buzzwords.

1. Operational excellence as code
   - AWS Well-Architected says operational excellence is about running and monitoring systems and improving processes.
   - Practical idea: turn manual checks into scripts, CI gates, dashboards, and runbooks.
   - Source: https://aws.amazon.com/architecture/well-architected/

2. Incident response maturity
   - Google SRE emphasizes timely, actionable alerts and incident processes.
   - Practical idea: propose incident roles, severity levels, escalation paths, and post-incident review templates.
   - Source: https://sre.google/resources/practices-and-processes/incident-management-guide/

3. Hybrid cloud control
   - Enterprises are moving toward flexible hybrid/multi-cloud, but governance and cost control become harder.
   - Practical idea: build inventory, ownership, tagging, and network dependency maps before suggesting migration work.
   - Source: https://www.apmdigest.com/2025-state-cloud-it-leaders-rewriting-cloud-strategies

4. AI with governance
   - AWS has a Generative AI Lens for designing, deploying, and operating AI applications under Well-Architected principles.
   - Practical idea: propose AI use-case intake, data classification, evaluation, logging, and human approval for high-risk actions.
   - Source: https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html

5. GenAI in operations
   - McKinsey discusses generative AI value in operations, but enterprise value depends on operating model and governance.
   - Practical idea: start with AI that summarizes incidents, drafts runbooks, answers docs questions, and helps triage support tickets.
   - Source: https://www.mckinsey.com/capabilities/operations/our-insights/generative-ai-in-operations-capturing-the-value

## Ideas You Can Bring To The Team

### Idea 1: Read-only infrastructure inventory

What to say:

> I want to build a read-only inventory that maps repos to services, owners, deployment workflows, cloud resources, and support status. It would help onboarding, incident response, and access reviews without changing production.

Reusable code:

```text
infra/scripts/aws/company_repo_discovery.py
infra/scripts/aws/05_inventory.py
```

### Idea 2: Access and ownership review

What to say:

> I noticed GitHub teams and project membership can be confusing. I can help create a lightweight access review template: which teams own which repos, who has write/admin, which project boards matter, and what access I still need to do my assigned work.

Reusable template:

```text
infra/scripts/aws/templates/github_access_request_template.md
```

### Idea 3: Health/readiness standard

What to say:

> I can help define a basic health/readiness standard: every service should have a health endpoint, dependency checks, documented ports, and a dashboard or log query. That makes deployments and support safer.

### Idea 4: Incident snapshot and runbook

What to say:

> I can create a safe incident snapshot script that collects service status, recent logs, deploy version, and dependency checks. It gives responders evidence faster without guessing.

### Idea 5: AI for internal operations

What to say:

> I can help identify low-risk AI use cases for Infrastructure: runbook search, incident summaries, ticket triage, repo explanation, change-risk summaries, and access-request drafting. I would keep sensitive data controls and human approval in the design.

Reusable template:

```text
infra/scripts/aws/templates/ai_infra_use_case_template.md
```

## When You Open A Company Repo

Look for these first:

```text
README.md
.github/workflows/
Dockerfile
docker-compose.yml
terraform/ or infra/
k8s/ or helm/
scripts/
Makefile
CODEOWNERS
.env.example
config/
docs/
runbooks/
monitoring/
alerts/
```

Ask these questions:

```text
What business system does this repo support?
Who owns it?
How is it deployed?
Where does it run?
What data does it touch?
How do we know it is healthy?
Where are logs and alerts?
What breaks if it goes down?
What access do I need to support it?
What should I not touch yet?
```

## What To Do About GitHub Teams And Projects

If you can see company GitHub but are not included in some teams:

1. Do not assume it is a mistake.
2. List what you can access and what you cannot access.
3. Identify the team/project names that look relevant to Infrastructure.
4. Ask your manager or onboarding buddy for the minimum access needed for your current assignment.
5. Ask for read access before write/admin access.
6. Ask which project board tracks Infrastructure work and how issues are assigned.
7. Ask whether there is a CODEOWNERS, Slack/Teams channel, on-call rotation, and runbook location.

Use this message:

```text
Hey <name>, I can see I have access to some GitHub projects/repos, but I am not sure which teams and boards are the official Infrastructure work surfaces. Could you point me to:

1. the repos I should focus on first,
2. the GitHub team(s) I should be added to, if any,
3. the project board where Infrastructure tasks are tracked,
4. the docs/runbooks for deploys, incidents, and access requests,
5. whether I should start with read-only discovery before making changes?

I want to make sure I am using the right workflow and not requesting broader access than needed.
```
