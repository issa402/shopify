# 04 Cloud Hybrid Platforms

This section teaches you how to translate what you know locally into AWS, Azure, and hybrid infrastructure thinking.

## What This Domain Means

Cloud understanding for this role is not just "I know service names."
It means you can take a running system and ask:

- where should this workload live
- what should be managed vs self-hosted
- what should be public vs private
- where should secrets live
- how should access be controlled
- what happens across cloud and on-prem boundaries

## What This Would Look Like At Future Standard

Examples:

- helping decide whether a service belongs on a VM, container host, or managed platform
- mapping an internal dependency to AWS or Azure networking
- reviewing how a hybrid environment should handle identity and secure access
- separating internet-facing entrypoints from internal-only systems
- reasoning about operational risk, not just deployment convenience

## Learn This First

### Cloud is still infrastructure

A VM is still a machine.
A managed DB is still a dependency.
A load balancer is still part of the network path.

Do not let cloud vocabulary hide the underlying system behavior.

### Hybrid means boundaries matter more

Hybrid environments increase questions about:
- identity
- network trust
- remote access
- secrets
- operational visibility across environments

## Pokemon Lab 1: Cloud-Map The Stack

### Goal

Translate the Pokemon stack into cloud equivalents.

### Exact task

For each component, decide what the cloud version would likely be:
- frontend
- API
- Postgres
- Redis
- RabbitMQ
- Python workers
- scraper service
- secrets storage
- logs and metrics

Then explain whether each should be:
- VM-based
- container-based
- managed service

### Why this matters

Because it trains you to think in architecture choices instead of local habits.

## Pokemon Lab 2: Design A Hybrid Version

### Goal

Practice thinking like a company with internal systems, corporate identity, and mixed environments.

### Exact task

Write a short design note that assumes:
- the app runs in cloud
- corporate identity exists outside the app
- some internal tools should be private only
- engineers need secure administrative access

Then explain:
- what should be public
- what should be private
- how secrets should be handled
- how admins and apps should authenticate

### Why this matters

Because hybrid infrastructure is about boundaries and trust, not just hosting.

## Pokemon Lab 3: Local Vs Cloud Failure Thinking

### Goal

See how operational thinking changes when a system moves from one host to a broader platform.

### Exact task

Explain the difference between:
- Docker Compose on one machine
- multiple services spread across cloud resources

Focus on:
- blast radius
- restarts
- persistence
- observability
- access control

### Why this matters

Because the role wants cloud exposure, but the real skill is architecture reasoning.
