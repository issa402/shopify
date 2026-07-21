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

## AI Cost Optimization And All-Angle Idea Map

Use this section when you want to talk about how a company may already use AI, where AI could reduce cost, and how to suggest ideas without sounding reckless.

The best framing is not:

```text
We should use AI everywhere.
```

The better framing is:

```text
Where is repetitive operational work creating cost, delay, risk, or support load, and can AI safely reduce that work in a read-only or human-approved way?
```

### The Six Angles To Think From

| Angle | What To Look For | AI Idea | Why It Matters |
|---|---|---|---|
| Cost | Repeated manual work, cloud waste, tool sprawl, tickets that keep coming back | AI summarizes, classifies, and routes work; scripts produce cost/risk snapshots | Reduces labor hours and wasted spend |
| Operations | Incidents, alerts, stale runbooks, unclear ownership | AI incident brief, runbook draft, alert explanation, daily ops summary | Speeds up triage and makes support more consistent |
| Security | Access reviews, secret risk, public exposure, stale permissions | AI-assisted access review summaries and config-risk explanations | Helps teams see risk faster without auto-changing anything |
| Cloud | Untagged resources, idle resources, log retention gaps, exposed security groups | AI explains boto3 inventory/audit findings in manager-friendly language | Turns raw AWS data into action |
| Documentation | Old Egnyte docs, missing READMEs, unknown repos, stale diagrams | AI creates current-vs-stale doc index and repo summaries | Reduces tribal knowledge |
| Engineering | PRs, code review, deploy risk, missing tests | AI change-risk summary and affected-file review using code-review-graph | Saves review time and reduces missed impact |

### Good First AI Ideas For Infrastructure

Start with read-only ideas that save time but do not touch production.

1. AI incident summary

   Input:

   ```text
   Auvik alerts, CloudWatch alerts, logs, ticket notes, change window notes
   ```

   Output:

   ```text
   likely root cause, downstream symptoms, affected systems, questions for owner, next checks
   ```

   Business value:

   ```text
   faster triage, less repeated investigation, better handoff notes
   ```

2. AI runbook drafter

   Input:

   ```text
   existing docs, incident notes, repeated support steps
   ```

   Output:

   ```text
   draft runbook with prerequisites, commands, rollback, escalation, verification
   ```

   Business value:

   ```text
   less tribal knowledge, faster onboarding, safer incident response
   ```

3. AI repo explainer

   Input:

   ```text
   README, workflows, Dockerfiles, Terraform, scripts, CODEOWNERS, package files
   ```

   Output:

   ```text
   purpose, runtime, deploy path, owners, dependencies, risks, missing docs
   ```

   Business value:

   ```text
   faster onboarding, easier ownership mapping, better project visibility
   ```

4. AI cloud audit explainer

   Input:

   ```text
   boto3 inventory: EC2, RDS, S3, VPC, security groups, CloudWatch, tags
   ```

   Output:

   ```text
   resource summary, public exposure, missing tags, missing retention, possible waste
   ```

   Business value:

   ```text
   cloud cost control, security visibility, cleaner ownership
   ```

5. AI access review assistant

   Input:

   ```text
   GitHub teams, repo permissions, CODEOWNERS, IAM roles, project boards
   ```

   Output:

   ```text
   who has access, likely owner groups, stale/unclear access, questions for manager
   ```

   Business value:

   ```text
   least privilege, cleaner onboarding/offboarding, less permission confusion
   ```

6. AI weekly ops/cost digest

   Input:

   ```text
   cloud inventory, ticket volume, incident notes, alert counts, stale docs, deploy changes
   ```

   Output:

   ```text
   what changed, what is noisy, what costs money, what needs owner follow-up
   ```

   Business value:

   ```text
   leadership visibility, fewer surprises, better prioritization
   ```

### Cost Reduction Without Being Reckless

AI can reduce cost in infrastructure, but the pitch needs to be specific.

Weak pitch:

```text
AI can reduce costs.
```

Strong pitch:

```text
I want to identify repetitive infrastructure work where AI can reduce manual review time without making production changes. Examples: alert summaries, stale-doc detection, repo onboarding summaries, cloud tagging/cost reports, and change-risk summaries. These can start read-only with human approval.
```

Cost buckets to look for:

| Cost Type | What It Looks Like | AI/Automation Angle |
|---|---|---|
| Human time | Engineers repeatedly explain the same systems or alerts | AI summaries, repo explainers, runbook Q&A |
| Cloud waste | Untagged/idle resources, old snapshots, unused load balancers | boto3 inventory plus AI summary/report |
| Incident cost | Long triage because alerts are noisy or context is scattered | incident brief and root-cause/symptom grouping |
| Onboarding cost | New people cannot find source of truth | AI-assisted doc index and repo map |
| Review cost | PRs require broad manual context gathering | code-review-graph plus AI change-risk summary |
| Security review cost | Access/config drift is hard to summarize | AI-assisted access/config review, human-approved |

### Guardrails That Make The Idea Mature

Always include guardrails. This makes the idea sound safe and professional.

```text
Read-only first
No secrets in prompts
No production changes by AI
Human approval for access/change/remediation
Log every AI-generated recommendation
Track owner, data class, model/provider, risk tier, and expected value
Start with internal docs/logs/tickets, not customer-sensitive data
Measure time saved before expanding
```

### AI Use-Case Register Fields

If Future Standard has scattered AI usage, propose a simple register.

| Field | Why It Matters |
|---|---|
| Use case | What AI is doing |
| Owner | Who is accountable |
| Business value | Time saved, cost saved, risk reduced |
| Data class | Public, internal, confidential, sensitive |
| Model/provider | ChatGPT, Claude, Copilot, internal model, etc. |
| Input sources | Docs, tickets, logs, repos, cloud inventory |
| Output action | Summary, recommendation, ticket, code, report |
| Risk tier | Low, medium, high |
| Human approval needed | Yes/no and who approves |
| Secrets exposure risk | None/low/medium/high |
| Logging/audit trail | Where outputs are stored |
| Success metric | Time saved, reduced tickets, lower MTTR, lower spend |

### Conversation Starters

Use these at work:

> I am trying to understand where AI is already being used internally versus where teams are still doing repetitive manual infrastructure work. Is there an AI use-case register or governance process today?

> For Infrastructure, I think the safest first AI opportunities are read-only: incident summaries, runbook search, repo explainers, cloud inventory summaries, and change-risk summaries. Does that line up with what the team is already exploring?

> I am interested in AI cost optimization from the ops side: not just model cost, but reducing repeated ticket work, stale documentation, manual cloud reviews, and incident triage time. Is there a current pain point where that would be useful?

> If I built a small read-only report that maps cloud resources, GitHub repos, owners, alerts, and runbooks, would that be useful as a starting point for AI-assisted infrastructure visibility?

### What Not To Suggest First

Avoid these early ideas:

```text
AI auto-remediates firewall rules
AI changes IAM permissions
AI deploys production changes
AI reads secrets or browser cookies
AI replaces monitoring tools
AI decides access approvals
AI directly modifies cloud resources without review
```

Better first version:

```text
AI summarizes, explains, classifies, drafts, and recommends. Humans approve changes.
```

### Strong One-Minute Pitch

Use this if someone asks what you are thinking about:

> I am looking at AI for Infrastructure from a cost, operations, and risk angle. I would not start with AI making changes. I would start read-only: summarize alerts, explain incidents, index stale docs, map repos to owners, and turn AWS/Azure inventory into cost/security/observability findings. That can reduce repeated manual work and improve visibility without adding production risk. If it proves useful, the next step would be a simple AI use-case register with owner, data class, model/provider, risk tier, approval requirements, and success metric.
EOF
