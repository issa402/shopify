# 07 Scripting Programming Data Analysis

This section teaches you how to use programming like an infrastructure engineer, not just like an app developer.

## What This Domain Means

The job says you should be able to:
- automate tasks
- analyze data
- support infrastructure operations

That means your scripts should help people answer questions like:

- is the service healthy
- what dependency is failing
- which env vars are missing
- what queue is backing up
- which endpoint is slow
- what changed in the system state

## What This Would Look Like At Future Standard

Examples:

- writing a Bash script to check a stack before startup
- writing a Python script to summarize health from multiple endpoints
- using PowerShell for Windows-side checks
- analyzing operational data from logs, exports, or metrics
- producing reports that make troubleshooting faster

## Learn This First

### Bash is for glue

Use Bash when:
- orchestrating commands
- validating local conditions
- checking env vars
- printing operator-friendly summaries

### Python is for richer logic

Use Python when:
- parsing JSON or CSV
- calling APIs
- building reports
- aggregating health results
- checking queues, services, or config with more structure

### Data analysis in infra is not fake

Infra engineers do analyze data.
Not always with giant notebooks, but often with:
- CSV exports
- logs
- queue depth samples
- latency summaries
- incident timelines

That is why Python and sometimes `pandas` matter.

## Important Answer: Pandas

Do you absolutely need `pandas` from this job description alone?
No.

Is it a smart thing to learn for this role?
Yes.

Why:
Because if you can take a messy operational export and turn it into a clear summary, you become much more useful.

## Pokemon Lab 1: Bash Startup Audit

### Goal

Write the kind of script a real infra teammate would appreciate before starting the platform.

### Exact task

Create a Bash script that checks:
- required env vars
- whether key ports are free or already bound
- whether core dependencies are reachable
- whether Docker services are up

### What the output should look like

It should not be cryptic.
It should say things like:
- `PASS: Postgres port reachable`
- `FAIL: REDIS_URL missing`
- `WARN: RabbitMQ container running but health endpoint not ready`

### Why this matters

Because good automation reduces guesswork.

## Pokemon Lab 2: Python Health Aggregator

### Goal

Write a script that gives one readable view of platform health.

### Exact task

Create a Python script that:
- calls multiple health endpoints
- records response code and response time
- prints a readable summary
- exits non-zero if a critical dependency fails

### What you are learning

You are learning how to turn distributed service checks into one operational answer.

## Pokemon Lab 3: Analyze Operational Data

### Goal

Practice "analyze data" in an infrastructure way.

### Exact task

Take any one of these:
- health snapshots
- latency samples
- queue depth samples
- service status exports

Then summarize:
- what looks normal
- what looks degraded
- what trend or outlier stands out

If you use `pandas`, great.
If not, use core Python first and then redo it with `pandas`.

### Why this matters

Because the role explicitly values data-driven thinking.
