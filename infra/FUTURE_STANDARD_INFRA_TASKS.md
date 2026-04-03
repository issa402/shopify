# Future Standard Infra Tasks

This file turns the Future Standard Infrastructure Engineering role into hands-on work inside this repo.

Goal:
- Build infrastructure intuition from this project
- Practice the exact skills the job asks for
- Stay project-based instead of falling into tutorial hell

How to use this file:
- Do the tasks in order
- Do not copy code from me
- For each task, first explain the problem in your own words
- Then write a short design note before touching code
- After finishing, write what broke, what you changed, and how you verified it

Mental model:
- Backend asks: how do we build the feature?
- Infrastructure asks: how do we run it safely, reliably, observably, and securely?

## What This Project Already Gives You

Use this repo as your infra lab:
- `Pokemon/` = standalone distributed service with Go API, Python workers, RabbitMQ, Redis, PostgreSQL, Docker Compose
- `services/gateway/` = Go gateway with auth, webhooks, Kafka, middleware
- `services/ai/` = FastAPI AI service with background consumer
- `apps/web/` = frontend that depends on these services being healthy
- root `docker-compose.yml` = shared infra for NexusOS

This means you can practice:
- Linux operations
- networking
- containers
- service startup/shutdown
- health checks
- logging
- monitoring
- queue reliability
- troubleshooting
- security hardening
- documentation

## Job Requirement Map

These are the role themes you should train for here:
- system administration
- server / compute / storage basics
- networking and service-to-service communication
- scripting and automation
- platform support and operations
- security fundamentals
- troubleshooting and incident thinking
- documentation and communication

## Phase 1: Master Pokemon As An Infrastructure System

### Task 1: Draw the real runtime architecture

Why this matters:
- Matches: develop expertise in platforms, communicate with stakeholders, document solutions
- If you cannot explain the system clearly, you do not yet own it

What to study:
- `Pokemon/server/main.go`
- `Pokemon/server/routes/routes.go`
- `Pokemon/server/config/`
- `Pokemon/server/worker/notification_worker.go`
- `Pokemon/docker-compose.yml`
- `Pokemon/services/api-consumer/`
- `Pokemon/services/analytics-engine/`
- `Pokemon/services/scraping-service/`

What to produce:
- Create `Pokemon/docs/runtime-architecture.md`
- Add one diagram section for HTTP flow
- Add one diagram section for async/event flow
- Add one section called `Dependencies`
- Add one section called `Failure Points`

How to think:
- What starts first?
- What depends on what?
- Which parts are synchronous?
- Which parts are asynchronous?
- What happens if Redis is down?
- What happens if RabbitMQ is down?
- What happens if Postgres is down?

Done when:
- You can explain one user request end-to-end
- You can explain one RabbitMQ message end-to-end

Resource:
- Google SRE Workbook: https://sre.google/workbook/table-of-contents/

### Task 2: Add a startup and dependency inventory

Why this matters:
- Matches: seamless operation of infrastructure, support operations, analytical thinking

What to study:
- `Pokemon/docker-compose.yml`
- `Pokemon/server/config/db.go`
- `Pokemon/server/config/redis.go`
- `Pokemon/server/config/rabbitmq.go`

What to produce:
- Create `Pokemon/docs/dependency-inventory.md`
- List every runtime dependency
- For each dependency include:
- purpose
- protocol
- default port
- whether the app is hard-dependent or soft-dependent
- what symptoms show up if it fails

How to think:
- Infra people need inventories, not vibes
- You are building the habit of knowing what exists, why it exists, and how it fails

Done when:
- You can answer “what breaks if X is unavailable?” for each dependency

Resource:
- Linux Journey networking basics: https://linuxjourney.com/

### Task 3: Improve Pokemon health checks

Why this matters:
- Matches: design scalable reliable solutions, investigate system events, support operations

Current project hooks:
- `Pokemon/server/handlers/health_handler.go`
- `Pokemon/server/main.go`

What to change:
- Upgrade the health response so it reports dependency-level status
- Decide whether to treat RabbitMQ as degraded or failed
- Make the response useful for humans and for automation

What to produce:
- Update `Pokemon/server/handlers/health_handler.go`
- Create `Pokemon/docs/health-strategy.md`

Your design note should answer:
- What is liveness vs readiness here?
- Should a cache outage fail the service or only degrade it?
- Should RabbitMQ be required for API readiness?

How to think:
- A health endpoint is an operational contract
- It should help load balancers, Docker, and humans

Done when:
- You can justify every status your endpoint returns

Resources:
- Kubernetes probes concepts: https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/
- Google reliability pillar: https://cloud.google.com/architecture/framework/reliability

### Task 4: Add graceful shutdown to the Pokemon Go server

Why this matters:
- Matches: reliable solutions, risk reduction, platform operations

Current project hooks:
- `Pokemon/server/main.go`

What to change:
- Replace basic `ListenAndServe` flow with a server that handles shutdown signals
- Make sure in-flight requests can finish
- Make sure background resources close cleanly

What to produce:
- Update `Pokemon/server/main.go`
- Create `Pokemon/docs/graceful-shutdown.md`

Your design note should answer:
- What signal should stop the service?
- What timeout is reasonable?
- What happens to SSE clients?
- What happens to the RabbitMQ worker?

How to think:
- Infra engineers care about shutdown just as much as startup
- A process exiting safely is part of reliability

Done when:
- You can explain what happens during `docker stop`

Resources:
- Go graceful shutdown guide: https://go.dev/doc/
- Docker stop signal behavior: https://docs.docker.com/reference/cli/docker/container/stop/

### Task 5: Add structured logging and request IDs

Why this matters:
- Matches: investigate events, resolve defects, communicate clearly

Current project hooks:
- `Pokemon/server/main.go`
- `Pokemon/server/routes/routes.go`
- `Pokemon/server/worker/notification_worker.go`

What to change:
- Introduce structured logs for the Go API
- Add request IDs at the router layer
- Include request ID, user ID when available, route, status, and duration
- Improve worker logs so they are searchable

What to produce:
- Update the files above
- Create `Pokemon/docs/logging-standard.md`

How to think:
- Ask: if prod breaks at 2 AM, what exact fields do I need in logs?
- Good logs are for debugging under pressure, not for looking pretty

Done when:
- You can trace one request and one queue event through logs

Resources:
- Go `slog` docs: https://pkg.go.dev/log/slog
- OpenTelemetry logging concepts: https://opentelemetry.io/docs/concepts/

### Task 6: Fix RabbitMQ worker reliability

Why this matters:
- Matches: scalable reliable solutions, troubleshooting, platform optimization

Current project hooks:
- `Pokemon/server/worker/notification_worker.go`
- `Pokemon/server/config/rabbitmq.go`

What to inspect carefully:
- The worker currently starts a goroutine per message and acknowledges quickly
- Think about what happens if the process crashes after ack but before the work is truly done

What to change:
- Design a safer ack strategy
- Add reconnect behavior or connection-close handling
- Add retry policy for transient failures
- Add dedupe or idempotency protection for repeated messages

What to produce:
- Update the files above
- Create `Pokemon/docs/rabbitmq-reliability.md`

Your design note should answer:
- When should a message be acked?
- What is a poison message?
- What should be retried?
- What should be dropped?
- How do you prevent duplicate alerts?

How to think:
- Message queues are infra systems, not just dev convenience
- Delivery semantics matter: at-most-once, at-least-once, effectively-once

Done when:
- You can explain the exact failure behavior of one message

Resources:
- RabbitMQ reliability guide: https://www.rabbitmq.com/docs/reliability
- RabbitMQ acknowledgements: https://www.rabbitmq.com/docs/confirms

### Task 7: Harden configuration and secrets

Why this matters:
- Matches: cybersecurity principles, secure configuration, risk profile improvement

Current project hooks:
- `Pokemon/server/config/config.go`
- `Pokemon/server/config/db.go`
- `.env` patterns in `Pokemon/`

What to change:
- Strengthen config validation
- Identify insecure defaults
- Separate dev-safe defaults from prod-required values
- Document secret handling expectations

What to produce:
- Update `Pokemon/server/config/config.go`
- Create `Pokemon/docs/config-and-secrets.md`

Your design note should answer:
- Which values are safe to default?
- Which values must fail startup if missing?
- Which values are secrets?
- How would this differ in AWS or Azure?

How to think:
- Config is part of security
- Startup should fail loudly for dangerous misconfiguration

Done when:
- You can explain which env vars are operationally critical

Resources:
- Twelve-Factor config: https://12factor.net/config
- AWS security pillar: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html

### Task 8: Audit Docker Compose and container behavior

Why this matters:
- Matches: system administration, compute, storage, operations

Current project hooks:
- `Pokemon/docker-compose.yml`
- `Pokemon/docker-compose.prod.yml`
- service Dockerfiles

What to inspect:
- service dependencies
- health checks
- restart policies
- volumes
- exposed ports
- duplicated config
- secrets exposure
- local-vs-prod differences

What to change:
- Clean up invalid or duplicated Compose definitions
- Improve dependency ordering and health logic
- Add notes on persistence and data loss risk

What to produce:
- Update compose files as needed
- Create `Pokemon/docs/container-audit.md`

How to think:
- Containers are not magic
- Ask what persists, what restarts, what binds to the host, and what is publicly exposed

Done when:
- You can explain which data survives a restart and which does not

Resources:
- Docker Compose docs: https://docs.docker.com/compose/
- Docker networking overview: https://docs.docker.com/engine/network/

### Task 9: Add observability basics

Why this matters:
- Matches: investigate system events, data-driven thinking, platform support

Project areas:
- `Pokemon/server/`
- `Pokemon/services/`
- docker environment

What to change:
- Add basic metrics collection strategy
- Track request latency, error rate, queue lag or queue depth, worker failures, cache usage
- If you do not fully implement metrics yet, at minimum create the metric design doc and instrumentation plan

What to produce:
- Create `Pokemon/docs/observability-plan.md`
- Optionally add code or middleware where appropriate

How to think:
- Logs tell stories after the fact
- Metrics tell you something is drifting before users complain

Done when:
- You can name the top 5 signals for Pokemon as a service

Resources:
- Prometheus getting started: https://prometheus.io/docs/introduction/overview/
- Grafana docs: https://grafana.com/docs/

### Task 10: Write an incident runbook

Why this matters:
- Matches: investigate resolve defects, collaboration, communication, professionalism

What to produce:
- Create `Pokemon/docs/incident-runbook.md`

Include sections:
- API down
- Postgres down
- Redis down
- RabbitMQ down
- alerts delayed
- bad deploy
- high latency

For each section include:
- symptoms
- first checks
- likely root causes
- immediate mitigation
- deeper follow-up

How to think:
- Infra engineering is not only building systems
- It is also helping humans recover systems under pressure

Done when:
- Someone else could follow your runbook without asking you questions

Resources:
- Google incident management basics: https://sre.google/workbook/

## Phase 2: Expand The Same Thinking To NexusOS

### Task 11: Map the whole shopify repo as a platform

Why this matters:
- Matches: develop expertise across areas of the business and platforms

What to study:
- `services/gateway/main.go`
- `services/ai/main.py`
- root `docker-compose.yml`
- `services/gateway/internal/pokemon/`
- `services/ai/consumers/pokemon_events.py`

What to produce:
- Create `docs/nexusos-platform-architecture.md`

Include:
- external entrypoints
- internal services
- data stores
- event flows
- where Pokemon fits into the whole system

How to think:
- At this level you are not documenting one service
- You are documenting a platform

Done when:
- You can explain the full system to a new engineer in 5 minutes

Resources:
- C4 model overview: https://c4model.com/

### Task 12: Audit root infrastructure services

Why this matters:
- Matches: compute, storage, platform operations, infrastructure technology

Current project hooks:
- root `docker-compose.yml`

What to inspect:
- Postgres
- Redis
- Qdrant
- Kafka
- Zookeeper
- Ollama
- Temporal

What to produce:
- Create `docs/root-infra-audit.md`

For each service answer:
- why it exists
- who depends on it
- what protocol it uses
- what data is persistent
- what happens if it is unavailable

How to think:
- Infra intuition comes from dependency mapping and failure mapping

Done when:
- You can say which failures are business-critical vs annoying-but-tolerable

Resources:
- Temporal docs: https://docs.temporal.io/
- Kafka intro: https://kafka.apache.org/intro

### Task 13: Trace the Pokemon to NexusOS integration

Why this matters:
- Matches: design/implementation of solutions, troubleshooting, stakeholder communication

What to study:
- `services/gateway/internal/pokemon/handler.go`
- `services/gateway/internal/pokemon/client.go`
- `services/ai/consumers/pokemon_events.py`
- Pokemon-side bridge or integration files

What to produce:
- Create `docs/pokemon-integration-trace.md`

Include:
- outbound event from Pokemon
- inbound gateway handling
- Kafka publication
- AI consumer processing
- failure points
- auth boundary

How to think:
- Cross-service tracing is a core infra skill
- You are learning contracts, timeouts, retries, and trust boundaries

Done when:
- You can explain how a single market event becomes an AI action

Resources:
- OpenTelemetry concepts: https://opentelemetry.io/docs/concepts/

### Task 14: Add platform-level health and readiness strategy

Why this matters:
- Matches: seamless operation, scalable reliable solutions

What to change:
- Review current health endpoints in gateway and AI service
- Define what “healthy” means per service
- Decide how dependent services should surface degraded status

What to produce:
- Create `docs/platform-health-strategy.md`
- Optionally update:
- `services/gateway/main.go`
- `services/ai/routers/health.py`

How to think:
- A healthy platform is not “process exists”
- It means the process can do its job safely

Done when:
- You can distinguish liveness, readiness, and degraded state for gateway, AI, and Pokemon

Resources:
- Kubernetes health checks: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/

### Task 15: Create a security boundary review

Why this matters:
- Matches: access controls, segmentation, secure configuration practices

What to inspect:
- auth middleware
- internal secrets
- webhook verification
- exposed ports
- default credentials
- env files

Files to inspect:
- `services/gateway/internal/middleware/`
- `services/gateway/internal/auth/`
- `services/gateway/internal/pokemon/handler.go`
- `Pokemon/server/middleware/auth.go`
- compose files

What to produce:
- Create `docs/security-boundary-review.md`

Include sections:
- internet-facing entrypoints
- internal-only routes
- trust assumptions
- secret locations
- highest-risk defaults
- recommended fixes

How to think:
- Security review is mostly asking who can talk to what, and why

Done when:
- You can identify the top 5 realistic risks in this repo

Resources:
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Microsoft IAM fundamentals: https://learn.microsoft.com/en-us/entra/fundamentals/introduction-identity-access-management

## Phase 3: Scripting Practice Tied To The Job

### Task 16: Bash operational scripts

Why this matters:
- Matches: scripting, Linux, support operations

What to build:
- A script that checks key services and prints a readable summary
- A script that tails logs from the most important containers
- A script that verifies required env vars exist before startup

Where to place them:
- `infra/scripts/bash/`

Suggested names:
- `pokemon_stack_status.sh`
- `pokemon_log_tail.sh`
- `pokemon_env_audit.sh`

How to think:
- Bash is for glue, checks, orchestration, and local ops
- Keep scripts small, readable, and safe

Done when:
- A new engineer could run them and understand the output

Resources:
- BashGuide: https://mywiki.wooledge.org/BashGuide
- Missing Semester shell lecture: https://missing.csail.mit.edu/

### Task 17: Python operational scripts

Why this matters:
- Matches: automate tasks, analyze data, support infrastructure operations

What to build:
- A script that validates config files or env values
- A script that summarizes app health from service endpoints
- A script that checks RabbitMQ or Kafka message backlog assumptions

Where to place them:
- `infra/scripts/python/`

Suggested names:
- `pokemon_health_report.py`
- `pokemon_config_validator.py`
- `pokemon_queue_report.py`

How to think:
- Python is stronger when the script needs parsing, reporting, or richer logic

Done when:
- Your scripts reduce manual operational work

Resources:
- Python docs tutorial: https://docs.python.org/3/tutorial/
- Real Python subprocess and requests articles: https://realpython.com/

## Phase 4: Communication And Project Ownership

### Task 18: Write a change proposal before each infra task

Why this matters:
- Matches: collaboration, communication, organization, attention to detail

What to produce before each meaningful change:
- `problem`
- `current behavior`
- `proposed change`
- `risk`
- `verification plan`
- `rollback plan`

Where to keep it:
- `docs/proposals/` at repo root or under `Pokemon/docs/proposals/`

How to think:
- Infra engineers are trusted because they think before they change production-shaped systems

Done when:
- Your future self can understand why you made the change

Resource:
- Atlassian agile tutorials: https://www.atlassian.com/agile/tutorials

### Task 19: Keep a troubleshooting journal

Why this matters:
- Matches: investigate defects, adapt to changing priorities, professionalism

What to produce:
- `docs/troubleshooting-journal.md`

For each issue record:
- symptom
- first wrong guess
- evidence gathered
- root cause
- final fix
- prevention idea

How to think:
- This builds operational intuition fast
- You become dangerous when you can see patterns across failures

Done when:
- You stop saying “it was random” and start saying “the signal pointed here”

## Priority Order

If you want the best order for job prep, do this:
1. Task 1
2. Task 3
3. Task 4
4. Task 5
5. Task 6
6. Task 7
7. Task 8
8. Task 10
9. Task 11
10. Task 13
11. Task 14
12. Task 15
13. Task 16
14. Task 17

## What To Avoid

Do not:
- jump straight into random cloud cert content without understanding this system first
- add code before writing down the operational problem
- treat logs as enough observability
- treat health checks as a yes/no toy endpoint
- treat queues as magic
- ignore shutdown behavior
- assume Docker Compose means “production ready”

## What “Good” Looks Like

You are on the right track if you can:
- explain Pokemon as a running system, not just as folders
- explain the full path of one request and one event
- say what happens when a dependency fails
- improve reliability without changing product features
- write small ops scripts that save time
- document systems so another engineer can operate them
- reason about risk before making changes

When you can do that consistently in this repo, you are training the exact muscle this job is asking for.
