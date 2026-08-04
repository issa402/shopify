# Plane Project Management

Last updated: 2026-06-18

## What Plane Is

Plane is a self-hosted project-management app. In this project it should be treated like Jira, Linear, or GitHub Projects: a planning and documentation surface for humans, not a runtime dependency for PokemonTool, Odoo, PokeTCG, Hermes, or NexusOS.

Plane is useful here for:

- turning product ideas into work items
- grouping work into cycles/sprints
- tracking modules like PokemonTool, Odoo storefront, Seller Hub research, scraping, security, and infra
- writing pages/specs for features before coding
- keeping roadmap and execution state out of chat history

Plane should not be used for:

- storing secrets
- replacing Git commits, code review, or source control
- becoming part of the card-store request path
- running automation that can mutate Odoo/eBay/Shopify without approval

## Where It Is Installed

Plane is installed outside the repo:

```text
/home/iscjmz/ops/plane-selfhost
```

This is intentional. It keeps third-party AGPL application code and generated Docker config out of the Shopify repo. The Shopify repo can document Plane usage, but it should not vendor Plane source or generated runtime files.

## Local URL

```text
http://localhost:8095
```

HTTPS is configured on local port `8445`, but use HTTP locally unless you intentionally configure certificates.

## Commands

```bash
/home/iscjmz/ops/plane-selfhost/plane.sh start
/home/iscjmz/ops/plane-selfhost/plane.sh status
/home/iscjmz/ops/plane-selfhost/plane.sh logs api
/home/iscjmz/ops/plane-selfhost/plane.sh stop
/home/iscjmz/ops/plane-selfhost/plane.sh backup
```

The raw generated Compose command is:

```bash
docker compose   -f /home/iscjmz/ops/plane-selfhost/plane-app/docker-compose.yaml   --env-file /home/iscjmz/ops/plane-selfhost/plane-app/plane.env   ps --all
```

Prefer the wrapper unless debugging Plane itself.

## Services Plane Runs

Plane is not a tiny plugin. Self-hosted Plane runs its own stack:

```text
web           frontend
admin         admin UI
space         public/share area
api           Django API
worker        background worker
beat-worker   scheduled worker
migrator      database migrations
live          realtime service
plane-db      Postgres
plane-redis   Valkey/Redis protocol
plane-mq      RabbitMQ
plane-minio   file/object storage
proxy         local reverse proxy
```

Because it runs its own Postgres, Redis/Valkey, RabbitMQ, MinIO, and web proxy, do not merge it into the Pokemon/Odoo compose files. Keep it as a separate ops stack.

## Big Tech Reality: Jira, GitHub, Or Both

Large companies usually use both issue tracking and Git hosting/code review:

- Jira or a Jira-like tool tracks product work, sprint planning, epics, roadmaps, approvals, ownership, and cross-team status.
- GitHub, GitLab, Bitbucket, or internal Git tooling stores code, pull requests, reviews, CI, releases, and source-of-truth technical history.
- Documentation often lives in Confluence, Notion, Google Docs, GitHub markdown, internal wikis, or a mix.

So Plane is not GitHub. Plane is closer to Jira/Linear. It can complement GitHub by holding planning and roadmap state while Git remains the proof of code changes.

## Recommended Project Setup

Suggested Plane workspace structure:

```text
Workspace: Card Vendor OS

Projects:
- PokemonTool
- Odoo Storefront
- PokeTCG Identity
- Marketplace Research
- Infrastructure/Ops
- Security/Compliance
- Documentation

Modules:
- Watchlist and Alerts
- Seller Hub Research
- eBay Browse API
- Scrapling / Sold Comps
- Inventory to Odoo Sync
- Storefront Search and Filters
- Data Freshness
- Auth and Session Hardening
```

Suggested labels:

```text
P0, P1, P2
bug, feature, security, infra, docs, research, polish
data-freshness, odoo-sync, ebay, seller-hub, scraping, frontend, backend
```

Suggested issue flow:

```text
Inbox -> Planned -> In Progress -> In Review -> Verified -> Done
```

Use Plane Pages for specs and decisions that are too product-oriented for code comments but too important to leave in chat.

## Current Verification

Verified locally on 2026-06-18:

- Plane v1.3.1 official self-host files installed.
- Docker images pulled.
- Local ports set to `8095` and `8445`.
- Proxy bound to `127.0.0.1` only.
- Database migrations completed.
- API readiness check returned `api ok`.
- Web responded with HTTP 200 at `http://localhost:8095`.

## Operational Rule

Run Plane when doing planning, triage, roadmap cleanup, or project documentation. Stop it when doing normal Pokemon/Odoo coding if the machine is warm or memory pressure is high.
