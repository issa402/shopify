# 06 Cybersecurity

This section is about practical infrastructure security.

Not movie security.
Not buzzword security.
Operational security.

## What This Domain Means

For this role, security means:

- least privilege
- segmentation
- secure configuration
- secret handling
- exposed service review
- endpoint and service protection
- reducing blast radius

## What This Would Look Like At Future Standard

Examples:

- reviewing whether internal services are exposed more broadly than needed
- checking that secrets are handled safely
- making sure service accounts have only the access they need
- validating secure defaults in config
- checking trust boundaries between users, services, and infrastructure

## Learn This First

### Security is part of normal engineering work

If a service starts with weak defaults, that is a security problem.
If a database port is publicly exposed, that is a security problem.
If a worker has credentials it does not need, that is a security problem.

Security is not a side topic.
It is part of operating the platform safely.

### Think in blast radius

Always ask:
- if this component is compromised, what else can it reach
- what data can it read
- what secrets can it steal
- what damage can it do

That is how infrastructure security becomes concrete.

## Pokemon Lab 1: Trust Boundary Review

### Goal

Identify who should be allowed to talk to what.

### Exact task

Using the Pokemon code and compose setup, classify:
- public routes
- authenticated routes
- internal-only services
- infrastructure dependencies
- secret-bearing components

For each one, answer:
- who should reach it
- what secrets it uses
- what happens if it is exposed or compromised

## Pokemon Lab 2: Secret Inventory

### Goal

Separate ordinary config from sensitive config.

### Files to inspect

- [Pokemon/server/config/config.go](/home/iscjmz/shopify/shopify/Pokemon/server/config/config.go)
- [Pokemon/server/pkg/crypto.go](/home/iscjmz/shopify/shopify/Pokemon/server/pkg/crypto.go)
- [Pokemon/docker-compose.yml](/home/iscjmz/shopify/shopify/Pokemon/docker-compose.yml)

### Exact task

Create a table of:
- DB credentials
- RabbitMQ credentials
- JWT/auth secrets
- API keys
- encryption-related values

For each one, answer:
- where it comes from
- whether startup should fail if missing
- whether it should ever be committed
- what a safer production pattern would be

## Pokemon Lab 3: Exposure Review

### Goal

Review the Pokemon stack like an infra engineer trying to reduce unnecessary exposure.

### Exact task

Inspect all port bindings and classify each as:
- safe for local developer convenience
- risky if used in a real deployment
- should be localhost-only
- should never be public

### Why this matters

Because this is exactly how teams improve security posture without needing exotic tooling.
