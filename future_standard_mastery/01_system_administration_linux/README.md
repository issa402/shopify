# 01 System Administration Linux

This section is where you stop thinking about the Pokemon app as "just code" and start thinking about it as a real system running on a machine.

Because you are on Ubuntu, this is one of the highest-value sections for you.

## What System Administration Actually Means

System administration is not a list of Linux commands.
It is the skill of understanding and safely operating a machine that runs important workloads.

That means you need to know:
- what is running
- which user owns it
- what ports are open
- where logs live
- how services start
- how services fail
- how disk, memory, and CPU pressure show up
- what you are allowed to change safely

If a platform breaks, system administration is often the first layer of truth.

## What This Would Look Like At Future Standard

In a role like this, system administration work might look like:

- checking why an internal platform is slow
- seeing whether the process is even running
- finding whether the machine is overloaded
- checking whether a service restarted unexpectedly
- checking whether logs show dependency failures
- validating that a service account has the right permissions
- confirming that a service is listening on the right port
- reviewing whether a server is exposing something it should not

So if the team says "the platform is broken," the system admin mindset asks:

- is the process up
- is the service healthy
- is the dependency reachable
- is the machine under pressure
- did a config or permission issue break startup

That is the mindset you are building in this section.

## Learn This First

Before you do any task, understand these mental models.

### 1. The machine has layers

Think in layers:

1. host
2. process
3. socket
4. dependency
5. application behavior

Example:
If the API is down, maybe:
- the process never started
- the process started but failed to bind a port
- the port is open but Postgres is unavailable
- the process is alive but not actually ready

If you do not separate those layers, you will debug badly.

### 2. "Running" is not the same as "healthy"

A process can exist and still be useless.

Examples:
- API process is up, but DB connection fails
- queue consumer is running, but RabbitMQ is disconnected
- service port is open, but it returns 500 on every request

That is why infra people care about health and readiness, not just process existence.

### 3. Permissions are part of reliability and security

If the wrong user owns a file or process:
- startup may fail
- secrets may leak
- services may run with too much privilege

So permissions are not just "security homework."
They are part of making systems safe and predictable.

## Example Before The Real Task

Imagine this situation:

"The Pokemon API stopped working after a restart."

A weak response is:
"Maybe the code is broken."

A strong system administration response is:

1. Is the API process running?
2. Is the expected port listening?
3. What do the logs say during startup?
4. Did the service fail because Postgres, Redis, or RabbitMQ was unavailable?
5. Did an env var or file permission break startup?

That is the kind of step-by-step thinking you need.

## Core Commands You Must Understand

Do not just copy these.
Know what question each one answers.

### Process and service questions

```bash
ps aux
pgrep -a <name>
systemctl status <service>
journalctl -u <service> --since "30 minutes ago"
```

These answer:
- is it running
- what command started it
- who owns it
- what does the service manager think
- what happened recently

### Network questions

```bash
ss -tulpn
curl -I http://localhost:<port>
nc -vz localhost <port>
```

These answer:
- what is listening
- whether the process responds over HTTP
- whether the port is reachable at all

### Resource questions

```bash
df -h
free -h
uptime
top
```

These answer:
- is disk full
- is memory under pressure
- is the machine overloaded
- who is consuming resources

## Pokemon Lab 1: Build A Real Operator View Of The App

### Goal

Stop looking at Pokemon as a folder tree.
Start looking at it as a running platform.

### Learn first

Make sure you understand:
- process vs container
- port vs route
- dependency vs feature

### What to inspect

Use:
- [Pokemon/docker-compose.yml](/home/iscjmz/shopify/shopify/Pokemon/docker-compose.yml)
- [Pokemon/server/main.go](/home/iscjmz/shopify/shopify/Pokemon/server/main.go)
- [Pokemon/scripts/health-check.sh](/home/iscjmz/shopify/shopify/Pokemon/scripts/health-check.sh)

### Exact task

Create your own note answering all of these:

1. What services exist in the Pokemon stack?
Rabbitmq, Redis, Postgres
2. Which ones are application services?
scraping-service, server, analytics-engine, api-consumer, client 
3. Which ones are infrastructure dependencies?
postgres, redis, rabbitmq
4. Which ports do they use?
postgres : 5432, redis: 6379, rabbitmq: 5672, rabbitmq ui:15672, Server: 3001
5. Which services are hard requirements for the API to be useful?
postgres, rabbitmq, server
6. Which services are optional or degradeable?
redis, scraping-service, analytics-engine, api-consumer
### Commands to run

If the stack is up:

```bash
docker compose -f /home/iscjmz/shopify/shopify/Pokemon/docker-compose.yml ps
docker compose -f /home/iscjmz/shopify/shopify/Pokemon/docker-compose.yml logs --tail=50
sudo ss -tulpn
```

### What you should produce

A short operator-style inventory with:
- service name
- purpose
- port
- dependency type
- what breaks if it fails

### Why this matters at Future Standard

Because infrastructure engineers are expected to know what exists and what depends on what.
If someone asks "what breaks if Redis dies," you should not guess.

## Pokemon Lab 2: Investigate Startup Like A Sysadmin

### Goal

Learn the difference between:
- process started
- service healthy
- platform useful

### Learn first

Understand that startup failures often come from:
- bad config
- missing env vars
- dependency unavailability
- permission mistakes
- port conflicts

### Exact task

Trace the startup path for the Pokemon API.

You need to answer:

1. What config does it need?
2. What dependencies does it touch on startup?
3. What happens if Postgres is missing?
4. What happens if Redis is missing?
5. What happens if RabbitMQ is missing?
6. Does the app fail fast or partially limp along?

### Files to inspect

- [Pokemon/server/config/config.go](/home/iscjmz/shopify/shopify/Pokemon/server/config/config.go)
- [Pokemon/server/config/db.go](/home/iscjmz/shopify/shopify/Pokemon/server/config/db.go)
- [Pokemon/server/config/redis.go](/home/iscjmz/shopify/shopify/Pokemon/server/config/redis.go)
- [Pokemon/server/config/rabbitmq.go](/home/iscjmz/shopify/shopify/Pokemon/server/config/rabbitmq.go)

### What you should write down

For each dependency:
- why it exists
- whether startup requires it
- what user-facing symptom appears if it is absent

### Why this matters at Future Standard

Because "supporting infrastructure" means being able to tell whether a failure is:
- total outage
- partial degradation
- configuration error
- dependency outage

## Pokemon Lab 3: Simulate An Incident And Recover It

### Goal

Practice behaving like the person who has to investigate and recover a service, not just write code.

### Learn first

Before simulating anything, remember:
- break one thing at a time
- watch symptoms
- capture evidence
- restore service cleanly

### Exact task

Choose one dependency:
- Postgres
- Redis
- RabbitMQ

Then:

1. Stop it.
2. Observe what breaks first.
3. Check logs.
4. Check ports.
5. Check health behavior.
6. Restore the dependency.
7. Confirm whether the app recovers automatically or needs help.

### Evidence to collect

- error message from logs
- health endpoint behavior
- service/container status
- whether restart was needed

### What you should learn

You are building answers to questions like:
- how does failure show up
- what is the fastest confirming signal
- what is the safest first recovery step

That is real sysadmin value.

## What You Should Know Before Moving On

Before leaving this section, you should be able to explain:

- the difference between a process and a healthy service
- how to inspect running services on Ubuntu
- how to identify ports and listeners
- how to tell whether a dependency outage is causing an app outage
- how to inspect logs and resource pressure
- how Pokemon behaves as a real running system

If you cannot explain those clearly yet, stay here longer.
