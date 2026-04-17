# 02 Servers Compute Storage

This section teaches you how to think about the machine as a resource host.
That means CPU, memory, disk, persistence, and data loss risk.

## What This Domain Means

When infrastructure people talk about servers, compute, and storage, they are asking:

- where does the workload run
- how much CPU and memory does it need
- what data must survive restart
- what data can disappear safely
- what happens if disk fills up
- what happens if the host dies

This is how you move from "the app runs on my machine" to "I understand how the platform survives."

## What This Would Look Like At Future Standard

Examples of this kind of work:

- identifying whether a workload needs more memory or just better behavior
- separating persistent data from disposable data
- deciding what must be backed up
- reviewing whether a service should run on a VM, container host, or managed platform
- checking whether logs or caches are consuming dangerous disk space
- understanding whether a restart is safe or destructive

## Learn This First

### Compute

Compute is not just "the server exists."
It includes:
- CPU scheduling
- memory availability
- concurrency load
- resource contention

If compute is mismanaged, you get:
- latency spikes
- crashes
- slow background jobs
- OOM kills

### Storage

Storage must be split into categories:

- authoritative persistent data
- cache or derived state
- logs
- secrets/config
- backups

If you lump these together, you will not understand risk correctly.

## Example Before The Real Task

Imagine RabbitMQ is empty after a restart.
Should you panic?

Answer:
It depends on what lived there.

If it held transient in-flight work, that is bad but maybe recoverable.
If Postgres data vanished, that is far more severe because it is likely source-of-truth business data.

That is storage classification thinking.

## Pokemon Lab 1: Classify All State

### Goal

Figure out what data in Pokemon is:
- authoritative
- derived
- temporary
- cache

### Files to inspect

- [Pokemon/docker-compose.yml](/home/iscjmz/shopify/shopify/Pokemon/docker-compose.yml)
- [Pokemon/docker-compose.prod.yml](/home/iscjmz/shopify/shopify/Pokemon/docker-compose.prod.yml)
- [Pokemon/database/migrations/001_init.sql](/home/iscjmz/shopify/shopify/Pokemon/database/migrations/001_init.sql)

### Exact task

Create a table for:
- Postgres
- Redis
- RabbitMQ
- any mounted volumes

For each one, answer:
- what data lives there
- whether it is source of truth
- what happens if it is lost
- whether restart is safe
- whether backup is necessary

### Why this matters

Because infrastructure engineers must know the difference between:
- "annoying loss"
- "platform outage"
- "business data loss"

## Pokemon Lab 2: Compute Pressure Review

### Goal

Learn to reason about which services are likely to be CPU-heavy, memory-heavy, bursty, or sensitive to resource limits.

### Exact task

Review the Pokemon services and write:

- which service is likely most CPU-intensive
- which service is likely to hold memory
- which service is likely sensitive to queue bursts
- which services should be watched for resource pressure first

### Good reasoning examples

- analytics workloads may be heavier on CPU or memory than simple request routing
- scraper services can become heavy because they drive browsers or concurrent fetches
- databases care about memory and disk behavior differently from stateless APIs

### Why this matters

Because at Future Standard, you may need to distinguish:
- app bug
- resource saturation
- dependency bottleneck

## Pokemon Lab 3: Write A Persistence And Backup Stance

### Goal

Act like the engineer who has to explain what must survive failure.

### Exact task

Write a short note for Pokemon that answers:

- what absolutely must be backed up
- what can be regenerated
- what should survive container restarts
- what should survive host restarts
- what secrets or config should be stored separately from code

### Why this matters

Because real infrastructure ownership includes recovery thinking, not just startup thinking.
