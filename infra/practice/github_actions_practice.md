# GitHub Actions Practice
## Hands-On CI/CD Tasks For This Repo

Use this after reading:
- `infra/lessons/06_github_actions_mastery.md`

Goal:
- build intuition first
- write your own workflow files
- do not copy blindly

---

## Ground Rules

Before each task, write down:
- what truth the workflow is proving
- what the minimum dependencies are
- what logs you need on failure

If you cannot answer those 3 questions, do not write YAML yet.

---

## Task 1: Read Existing Workflow Syntax

Inspect:
- `.github/workflows/ci.yml`

Answer these:
- what triggers it?
- how many jobs exist?
- where does it use `uses` vs `run`?
- what assumptions is it making?

Write your answers in:
- `infra/practice/github_actions_notes.md`

---

## Task 2: Design Your First CI Truth

Pick one:
- Pokemon Go build
- Pokemon Go health
- api-consumer install/import
- shell script syntax validation

Best choice:
- Pokemon Go health

Write a short design note with:
- workflow name
- trigger events
- dependencies needed
- pass condition
- failure logs to print

---

## Task 3: Draft The Workflow Skeleton

Without writing full commands yet, sketch:
- `name`
- `on`
- `jobs`
- one job name
- `runs-on`
- ordered step names

Example level of abstraction:
- checkout
- setup language
- start dependencies
- start service
- probe health
- print logs on failure

Do not write exact commands yet.
Force yourself to think structurally first.

---

## Task 4: Decide Whether To Use `dev-startup.sh`

Answer:
- is `dev-startup.sh` a human convenience script or a CI truth script?
- what does it assume about local state?
- what parts of it are useful in CI?
- what parts should stay visible directly in YAML?

Write your answer in 5-10 lines.

Expected intuition:
- first CI should usually keep steps visible in YAML
- later CI can call a trusted script

---

## Task 5: Design A Pokemon Go Health Workflow

Target:
- prove `Pokemon/server` starts and `/health` passes

Your task:
- list the exact env vars the Go service needs
- identify whether RabbitMQ is needed for `/health`
- choose whether to use service containers or Compose
- define what log output you want if startup fails

Question to answer:
- why is Postgres + Redis enough for this workflow?

---

## Task 6: Design A Python Workflow

Target:
- validate `Pokemon/services/api-consumer`

Your task:
- decide whether this workflow should:
- install deps only
- import app only
- start uvicorn
- or run tests

Write the tradeoffs:
- fastest useful workflow
- strongest useful workflow

---

## Task 7: Design A Script Quality Workflow

Target:
- validate Bash scripts in `Pokemon/scripts/` and `infra/scripts/`

Think about:
- `bash -n`
- ShellCheck
- executable permissions

Why this matters:
- infra engineers automate heavily
- broken scripts are platform risk

---

## Task 8: Design A Docker Validation Workflow

Target:
- validate Docker-related correctness

Ideas:
- `docker compose config`
- build one image
- build all images

Question:
- why is “compose parses successfully” a meaningful CI truth?

---

## Task 9: Design A Multi-Job CI Pipeline

Design jobs for:
- `pokemon-go`
- `pokemon-python`
- `scripts`

Answer:
- which jobs can run in parallel?
- which jobs should use `needs`?
- which failures are highest-signal?

This is real platform thinking.

---

## Task 10: Failure Investigation Practice

Pretend the workflow fails at each stage.

For each failure, write:
- likely cause
- first log to inspect
- next diagnostic command you would add

Scenarios:
- Go server fails to boot
- `/health` returns 503
- Python dependency install fails
- service container never becomes ready
- Docker build fails

This is where CI becomes infra training, not just YAML practice.

---

## Task 11: Conditional CI Thinking

This repo has multiple services.

Answer:
- should frontend changes trigger Pokemon health CI?
- should `Pokemon/` changes trigger gateway CI?
- should docs-only changes run everything?

Write your own branch/path strategy before implementing anything.

This is a real monorepo/platform concern.

---

## Task 12: Artifact And Log Design

Think about what you want to preserve after a CI failure:
- Go logs
- Python logs
- Docker logs
- test reports

Answer:
- when is printing logs enough?
- when should logs be uploaded as artifacts?

---

## Syntax Cheat Sheet

Use these patterns while learning:

### Trigger block

```yaml
on:
  push:
  pull_request:
  workflow_dispatch:
```

### One job

```yaml
jobs:
  pokemon-health:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
      - name: Setup Go
      - name: Start dependencies
      - name: Start service
      - name: Probe health
```

### Action step

```yaml
- uses: actions/checkout@v4
```

### Command step

```yaml
- name: Run command
  run: echo "hello"
```

### Multiline command

```yaml
- name: Multiple commands
  run: |
    echo "one"
    echo "two"
```

### Environment variables

```yaml
env:
  PORT: 3001
  POSTGRES_HOST: localhost
```

### Job dependency

```yaml
needs: pokemon-go
```

---

## Recommended Build Order

Do these in order:
1. Task 2
2. Task 3
3. Task 5
4. Task 7
5. Task 6
6. Task 8
7. Task 9
8. Task 10
9. Task 11
10. Task 12

---

## What Mastery Looks Like

You are getting good when you can:
- explain why a workflow exists before writing it
- choose the smallest truthful environment
- separate local scripts from CI responsibilities
- debug failures from logs, not vibes
- design multi-service validation without over-testing
- keep workflows readable and intentional

That is the actual skill.
