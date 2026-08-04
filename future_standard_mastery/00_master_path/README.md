# 00 Master Path

This file is the "how to use the whole training system" guide.
Do not skip it.

If you skip this and jump into random tasks, you will end up doing work without understanding why it matters.

## What The Future Standard Role Is In Plain English

This role is asking for an engineer who can help keep business infrastructure usable, reliable, and safe.

That includes:
- understanding systems
- supporting platforms people depend on
- improving reliability and operational clarity
- automating repetitive work
- working across Linux, Windows, cloud, networking, and security concerns
- communicating clearly with both technical and non-technical people

So the role is not just:
- backend engineering
- cloud certification trivia
- help desk support
- cybersecurity only

It is a blended infrastructure role.

## What You Would Actually Be Doing In A Role Like This

You might be asked to do things like:

- investigate why an internal service is slow or unavailable
- figure out which dependency failed and how severe it is
- improve a health check so it actually tells the truth
- write a script that reduces manual validation work
- review exposed ports and access boundaries
- help migrate a system from a laptop-style setup to a cloud-ready setup
- write a runbook so someone else can recover the service
- explain risk and rollback before changing an important system

That is why this training is organized by operational domains instead of by random technologies.

## The Right Learning Sequence

### Phase 1: Learn the machine

Start with:
- Linux
- processes
- services
- filesystems
- permissions
- logs

Reason:
If you do not understand the host, you will not really understand containers, cloud VMs, or service failures.

### Phase 2: Learn how the app behaves as a running system

Use `Pokemon/` to learn:
- service startup
- dependencies
- health checks
- logs
- shutdown behavior
- queue flows
- data stores

Reason:
Infrastructure engineering is about running systems, not just reading code.

### Phase 3: Learn the path between systems

Then learn:
- DNS
- ports
- TCP
- routing
- TLS
- firewalls
- internal vs external exposure

Reason:
A huge number of production problems are really dependency or network path problems.

### Phase 4: Learn cloud as an extension of system thinking

Then map what you already know into:
- AWS
- Azure
- hybrid architecture
- secrets management
- load balancing
- managed services

Reason:
Cloud makes more sense when you already understand the machine and the service.

### Phase 5: Learn how to automate, secure, and explain your work

That means:
- Bash
- Python
- PowerShell
- security boundaries
- operational reports
- runbooks
- change proposals

Reason:
Teams trust infrastructure engineers who reduce chaos.

## How To Use Each Domain Folder

Every domain folder should be worked the same way:

1. Read the "what this is" section.
2. Read the "what this looks like at Future Standard" section.
3. Read the "learn first" section and make sure the mental model is clear.
4. Do the example before the real task.
5. Do the Pokemon task exactly as written.
6. Write down what you observed and how you verified it.

If you are ever tempted to skip the explanation and just run commands, slow down.
That is how people end up memorizing without understanding.

## Your Main Training Loop

For every meaningful lab:

1. State the problem.
2. State what you think is happening.
3. Identify the dependencies involved.
4. Gather evidence.
5. Make or propose the change.
6. Verify the outcome.
7. Write what you learned.

That is how real infrastructure work feels.

## Example Of The Difference Between Weak Practice And Strong Practice

Weak practice:
"I ran `docker compose ps` and the containers were up."

Strong practice:
"I verified the core services were running, then mapped which ones are hard dependencies for the API. I checked which ports were bound, verified the health endpoint, and noted that the API could start while a downstream dependency was still unhealthy, which means process-up and service-ready are not the same thing."

That second way of thinking is what you are building here.

## Your First Three Steps

Do these first:

1. Read [01_system_administration_linux/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/01_system_administration_linux/README.md) and complete the host inspection task.
2. Read [02_servers_compute_storage/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/02_servers_compute_storage/README.md) and classify Pokemon data and persistence.
3. Read [03_networking/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/03_networking/README.md) and produce the port/protocol map for Pokemon.

Those three together build the foundation for almost everything else.
