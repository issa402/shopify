# 09 Delivery Documentation Collaboration

This section is about the part of infrastructure work people underestimate until they work on a real team.

Technical correctness matters.
But trustworthy communication matters too.

## What This Domain Means

You are not only expected to make changes.
You are expected to:

- explain the problem clearly
- explain the risk
- explain the rollback
- document how the system works
- document how to recover it
- collaborate without causing confusion

## What This Would Look Like At Future Standard

Examples:

- writing a change proposal before touching an important system
- documenting a design so others understand the tradeoffs
- giving a clear incident update instead of vague panic
- tracking follow-up work after a production issue
- translating technical risk for non-technical stakeholders

## Learn This First

### Infra trust comes from clarity

People trust infrastructure engineers when they can tell:
- what is changing
- why it is changing
- how risky it is
- how it will be verified
- how it can be rolled back

### A runbook is a tool, not a school assignment

A good runbook lets someone else recover the system without needing you in the room.

## Pokemon Lab 1: Write A Change Proposal

### Goal

Practice thinking before changing something important.

### Exact task

Pick one Pokemon infra improvement and write:
- problem
- current behavior
- proposed change
- risks
- verification plan
- rollback plan

### Why this matters

Because strong infrastructure work is deliberate.

## Pokemon Lab 2: Write A Runbook

### Goal

Document recovery steps another engineer could follow.

### Exact task

Write a runbook for one scenario:
- API down
- Postgres down
- Redis down
- RabbitMQ down
- alerts delayed

For that runbook include:
- symptoms
- first checks
- confirming evidence
- safe mitigations
- deeper follow-up

### Why this matters

Because operational maturity means the team is not dependent on one person's memory.

## Pokemon Lab 3: Explain One Issue Two Ways

### Goal

Practice technical and stakeholder communication.

### Exact task

Take one issue and explain it:
- once for engineers
- once for non-technical stakeholders

The engineer version should include dependencies and failure behavior.
The stakeholder version should include impact, mitigation, and current status.

### Why this matters

Because the job explicitly values collaboration, empathy, and communication.
