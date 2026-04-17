# LESSON 06: GitHub Actions Mastery
## CI/CD, Infrastructure Thinking, and Project-Real Examples

---

## Why This Matters For Your Job

This lesson maps directly to the Future Standard Infrastructure Engineering role.

GitHub Actions trains these job muscles:
- scripting and automation
- support and operations of platforms
- documenting and standardizing workflows
- investigating failures from logs and signals
- designing reliable delivery pipelines
- collaborating through repeatable, visible automation

In plain English:
- Bash and Python teach you how to automate on one machine
- GitHub Actions teaches you how to automate in a clean, repeatable environment every time code changes

That is infrastructure engineering.

---

## The Core Mental Model

### What GitHub Actions is

GitHub Actions is a system that:
- listens for repository events
- starts a temporary runner machine
- checks out your code
- runs steps you define
- reports success or failure

The runner is not your laptop.
The runner is not your production server.
The runner is a temporary clean machine used to automate checks or deployments.

### What a runner is

A runner is the machine that executes your workflow.

Think:
- your laptop = messy, personal, stateful
- GitHub runner = clean, disposable, predictable

This is exactly why CI is valuable:
- it proves your code works outside your personal machine

### What CI means

Continuous Integration means:
- every push / PR gets validated automatically
- code is built, tested, checked, maybe lightly integrated

### What CD means

Continuous Delivery or Deployment means:
- validated code can be shipped or prepared to ship automatically

For your repo, CI comes first.
CD comes later.

---

## What GitHub Actions Is NOT

GitHub Actions is not:
- your permanent server
- your production runtime
- a replacement for Docker or Kubernetes
- a magic background environment where all services already exist

If your workflow needs Postgres, Redis, or RabbitMQ, you must provide them.

You do that using one of three approaches:
- GitHub Actions service containers
- Docker Compose
- direct process startup

---

## The YAML Mental Model

A workflow file lives in:

```text
.github/workflows/ci.yml
```

At the highest level, a workflow has:
- a name
- triggers
- jobs
- steps inside each job

Think of the structure like this:

```yaml
name: workflow name

on:
  event:

jobs:
  job_name:
    runs-on: machine type
    steps:
      - one action
      - another action
```

### Syntax intuition

YAML is indentation-sensitive.

That means:
- spaces matter
- indentation level creates structure
- lists use `-`
- mappings use `key: value`

Example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
      - name: Run tests
```

Here:
- `jobs` contains `test`
- `test` contains `runs-on` and `steps`
- `steps` contains a list of step objects

---

## GitHub Actions Building Blocks

## 1. `name`

Human-friendly label shown in the Actions UI.

Example:

```yaml
name: Pokemon CI
```

## 2. `on`

Defines which repository events trigger the workflow.

Common examples:
- `push`
- `pull_request`
- `workflow_dispatch`

Example:

```yaml
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
```

Meaning:
- run on pushes to `main`
- run on every PR
- allow manual runs from GitHub UI

## 3. `jobs`

A workflow can have multiple jobs.
Jobs run:
- in parallel by default
- or in sequence if one needs another

Think of jobs as separate machines or stages.

Examples:
- `lint`
- `test-go`
- `test-python`
- `integration`
- `docker-build`

## 4. `runs-on`

Defines the runner OS.

Examples:
- `ubuntu-latest`
- `windows-latest`
- `macos-latest`

For your repo and infra prep, `ubuntu-latest` is the main one.

## 5. `steps`

Each job runs a list of steps in order.

Typical steps:
- checkout code
- install language toolchains
- install dependencies
- run commands
- upload logs/artifacts

## 6. `uses`

This means “use a prebuilt action.”

Example:

```yaml
- uses: actions/checkout@v4
```

That action checks out your repo into the runner.

## 7. `run`

This means “run shell commands.”

Example:

```yaml
- name: Run Go tests
  run: go test ./...
```

## 8. `env`

Defines environment variables.

Example:

```yaml
env:
  PORT: 3001
  POSTGRES_HOST: localhost
```

This is important because your apps use env-driven configuration.

---

## The Most Important CI Question

Before writing any workflow, ask:

**What exact truth do I want this workflow to prove?**

Examples:
- the Go code builds
- the Python service installs cleanly
- the Pokemon Go server boots
- the health endpoint works with real dependencies
- Docker images can build

If you do not know what truth a workflow is proving, the workflow becomes random.

---

## Start Small: The Right CI Maturity Ladder

Do not start with a giant “run the whole world” workflow.

Start in this order:

### Level 1: Static validation

No running servers needed.

Examples:
- `go test ./...`
- `go build ./...`
- `pytest`
- `python -m compileall`
- `npm test`
- ShellCheck

### Level 2: Service boot checks

Start one service with minimum dependencies.

Examples:
- start Pokemon Go server
- hit `/health`

### Level 3: Service integration

Bring up real dependencies and prove the service behaves correctly.

Examples:
- Postgres + Redis + Go server
- health endpoint
- one real API request

### Level 4: Multi-service integration

Examples:
- gateway + AI service + Kafka
- or Pokemon full stack

### Level 5: Build/deploy pipelines

Examples:
- Docker image build
- publish artifact
- deploy to environment

For your repo, you should start with Levels 1 and 2.

---

## Your Repo: What To Test First

This project has multiple systems.

### Pokemon

Services:
- Go API
- Python API consumer
- analytics engine
- scraping service
- Redis
- RabbitMQ
- PostgreSQL

### NexusOS outer repo

Services:
- Go gateway
- Python AI service
- React app
- Redis
- Postgres
- Kafka
- Qdrant
- Temporal

This is why your first CI should be **narrow**, not full-stack.

Recommended first CI truth:

**Pokemon Go server can start against Postgres + Redis and pass `/health`.**

That is focused, meaningful, and tied to infrastructure engineering.

---

## Should You Use `dev-startup.sh` In GitHub Actions?

Short answer:
- maybe later
- not as your first CI foundation

### Why not first

Your `dev-startup.sh` is a local-developer convenience script.
CI workflows are easier to debug when the steps are visible directly in YAML.

If CI fails, you want to know whether it failed during:
- infra startup
- Python startup
- Go startup
- health check

If everything is hidden inside one script, debugging is harder early on.

### When it becomes useful

Use `dev-startup.sh` in CI later if:
- it is stable
- it is deterministic
- it is documented
- you trust it

### Good compromise

First CI:
- copy the logic into workflow steps directly

Later:
- optionally call `bash Pokemon/scripts/dev-startup.sh`

This is a very normal progression.

---

## Three Ways To Provide Dependencies In GitHub Actions

## Option 1: Service containers

This is often the best beginner choice.

GitHub Actions lets a job define service containers for:
- Postgres
- Redis
- RabbitMQ

These start automatically for the job.

Use this when:
- you need a DB/cache/broker
- you do not want full Docker Compose complexity

Good for:
- Pokemon Go health checks
- gateway integration tests

## Option 2: Docker Compose

Run `docker compose up -d ...` inside the workflow.

Use this when:
- your local stack is already modeled well in Compose
- you need several tightly related services

Good later, once your compose files are clean and intentional.

## Option 3: Direct process startup only

No containers.
Just install dependencies and run app processes.

Use this when:
- the service has no external dependency
- or dependencies are mocked/skipped

Good for:
- pure build checks
- some unit tests

---

## Understanding `actions/checkout`

This is usually your first step:

```yaml
- uses: actions/checkout@v4
```

Why:
- the runner starts empty
- your repo is not there until checkout happens

Without checkout:
- your files do not exist in the runner workspace

---

## Understanding Language Setup Actions

Typical setup actions:

### Go

```yaml
- uses: actions/setup-go@v5
```

This installs the Go toolchain for the job.

### Python

```yaml
- uses: actions/setup-python@v5
```

This installs Python for the job.

### Node

```yaml
- uses: actions/setup-node@v4
```

This installs Node for frontend work.

These actions let you pick versions and keep CI consistent.

---

## Understanding `run` Steps

Each `run` step executes shell commands.

Example:

```yaml
- name: Build Go API
  run: |
    cd Pokemon/server
    go test ./...
```

What matters:
- the default shell on Ubuntu is Bash-like
- multiline commands use `|`
- each step starts in the repo workspace

Important thinking:
- steps are sequential inside a job
- but each step is not magic state preservation for shell variables unless you export or script carefully

---

## Background Processes In CI

If you start a service manually in CI, you usually:
- run it in the background with `&`
- wait a bit or poll for readiness
- hit the endpoint

Conceptually:

```bash
go run main.go > go.log 2>&1 &
sleep 5
curl http://localhost:3001/health
```

The key infrastructure lesson:
- starting a process is not the same as it being ready
- you must wait or probe readiness

That is why health checks matter.

---

## Logs In CI

If a service fails in CI, logs are your best friend.

Good pattern:
- redirect logs to a file
- print the file on failure
- optionally upload as an artifact

Examples of useful logs:
- Go app startup logs
- Python traceback output
- Docker logs
- `docker ps`

This is the same operational thinking you need in a real infrastructure role.

---

## Your First Real CI Goal

Your first CI file should prove this:

### Goal
Pokemon Go server boots and passes `/health`.

### Minimum dependencies
- Postgres
- Redis

### Not required for first pass
- RabbitMQ
- client
- analytics engine
- scraping service
- full Pokemon stack
- full NexusOS stack

### Why this is the right first target
- small enough to understand
- relevant to infra
- tests real startup behavior
- validates health check design

---

## The Thinking For Your First `ci.yml`

In order:

1. Trigger on PR and push
2. Checkout repo
3. Setup Go
4. Provide Postgres + Redis
5. Create needed env vars
6. Start Pokemon Go server
7. Poll `/health`
8. Fail loudly if unhealthy
9. Print logs on failure

That is the right first CI shape.

Do not start by adding:
- gateway
- AI service
- full Compose
- deployment

---

## CI vs Local Dev Script

### Local dev script

Goal:
- convenience for humans
- reuse local state
- keep services alive for development

### CI workflow

Goal:
- prove a repeatable truth
- start from clean state
- run unattended
- fail predictably

That is why they feel similar but are not identical.

Your `dev-startup.sh` teaches good operational thinking, but CI is stricter.

---

## Practice Tasks You Should Do

You should learn GitHub Actions by building these in order:

### Task 1: Go build workflow

Truth proved:
- Pokemon Go server builds and tests cleanly

### Task 2: Pokemon health workflow

Truth proved:
- Pokemon Go server starts with Postgres + Redis and passes health

### Task 3: Python install/test workflow

Truth proved:
- `services/api-consumer` dependencies install and app imports cleanly

### Task 4: Shell script quality workflow

Truth proved:
- your Bash scripts pass syntax checks / ShellCheck

### Task 5: Docker build workflow

Truth proved:
- Docker images build successfully

### Task 6: Multi-job workflow

Truth proved:
- several independent parts of the repo validate in parallel

### Task 7: Conditional workflow behavior

Truth proved:
- certain jobs only run when specific folders change

This is super relevant for monorepo or multi-service thinking.

---

## Syntax Patterns You Need To Recognize

## Arrays in triggers

```yaml
branches: [main, develop]
```

## Multiline shell

```yaml
run: |
  echo "one"
  echo "two"
```

## Action step

```yaml
- uses: actions/checkout@v4
```

## Shell command step

```yaml
- name: Run health check
  run: curl -f http://localhost:3001/health
```

## Environment variables

```yaml
env:
  PORT: 3001
```

## Job dependency

```yaml
needs: build
```

Meaning:
- this job waits for `build`

---

## When To Use `needs`

Use `needs` when:
- one job depends on another’s success

Examples:
- `deploy` should need `test`
- `integration` might need `build`

Do not overuse it.
Independent jobs can run in parallel and save time.

---

## Common Beginner Mistakes

### Mistake 1: giant single workflow doing everything

Result:
- slow
- hard to debug
- confusing

### Mistake 2: testing too much too early

Result:
- fragile workflows
- poor intuition

### Mistake 3: hiding everything inside one script too soon

Result:
- hard to tell where CI failed

### Mistake 4: confusing “process started” with “service ready”

Result:
- flaky CI

### Mistake 5: depending on laptop assumptions

Result:
- “works on my machine” syndrome

GitHub Actions helps cure this if you use it well.

---

## Project-Relevant Examples

## Example A: Pokemon Go health CI

What it validates:
- configuration
- startup
- DB connectivity
- Redis connectivity
- health endpoint behavior

Infra concepts trained:
- readiness
- dependencies
- logs
- environment variables

## Example B: Gateway build/test CI

What it validates:
- Go modules install
- gateway compiles
- basic tests pass

Infra concepts trained:
- reproducible build environment
- dependency management

## Example C: AI service import/install CI

What it validates:
- Python dependency graph is valid
- FastAPI app imports
- no missing package regressions

Infra concepts trained:
- runtime dependency discipline
- consistent environments

## Example D: Shell script validation CI

What it validates:
- your Bash infrastructure scripts are syntactically valid
- optional ShellCheck lint passes

Infra concepts trained:
- operations scripting hygiene

---

## What Counts As “Infrastructure Engineer” Work Here

When you design CI in this repo, you are practicing:
- standardizing engineering workflows
- reducing deployment risk
- making failures visible earlier
- documenting platform assumptions
- improving reliability of technical systems

That is not “just dev work.”
That is infrastructure/platform engineering work.

---

## How To Start Your First `ci.yml`

Start with this exact thought process:

1. Pick one service
2. Pick one truth to prove
3. List minimum dependencies
4. Decide how to provide them
5. Decide which logs you need if it fails
6. Keep the workflow as short as possible

For you:

### Best first file goal
Pokemon Go health CI

### Best first dependency model
GitHub Actions service containers for Postgres and Redis

### Best first success condition
`curl /health` returns 200

### Best first failure visibility
print Go logs on failure

That is the strongest beginner move.

---

## What To Build After The First CI File

After your first health workflow works, build these next:

1. Go test workflow
2. Python dependency/install workflow
3. ShellCheck workflow
4. Docker image build workflow
5. Integration workflow for gateway or Pokemon stack
6. branch-protection-ready workflow set

That progression will teach you more than jumping straight to deploy automation.

---

## Final Takeaway

GitHub Actions is not just “write YAML.”

It teaches you to think like this:
- what system am I validating?
- what dependencies does it really need?
- what is the smallest truthful test?
- how do I make failures visible?
- how do I make this reproducible for every engineer?

That is infrastructure engineering mindset.

Read this lesson first, then do the practice tasks.
