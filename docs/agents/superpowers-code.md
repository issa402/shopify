# Superpowers-Style Coding Playbook

This repo does not vendor or depend on `obra/superpowers`.

Use this file as the local coding workflow inspired by Superpowers: clarify the goal, make a small plan, implement in focused steps, verify with tests or runtime checks, and leave a clear handoff.

## What Superpowers Is

Superpowers is an external coding-agent methodology/plugin from `obra/superpowers`.

- Maintainer/source: `obra/superpowers`
- License: MIT, per the repository metadata provided by the user
- Intended use: coding-agent workflow, skills, review loops, planning, and disciplined implementation
- Project impact here: documentation-only unless the user separately approves installing the external Codex plugin

Do not add it as a production dependency. It is not part of the Pokemon app, Shopify app, Docker services, frontend bundle, backend runtime, or database schema.

## How It Benefits This Repo

For this project, the useful part is not magic. The useful part is the operating discipline:

- Ask what the feature or bug must actually do before changing code.
- Read the relevant files first.
- Keep changes small and tied to the request.
- Prefer existing patterns over new abstractions.
- Verify behavior with focused tests, builds, logs, database checks, or HTTP checks.
- Explain remaining risk instead of pretending everything is perfect.

This should make Codex more reliable in this repo because it gives repeatable rules for handling code changes, debugging, and verification.

## Coding Workflow

Use this flow for non-trivial code work:

1. Read repo instructions: `AGENTS.md`, then the task-specific files.
2. State the real goal in one or two concrete sentences.
3. Identify the smallest files/modules that own the behavior.
4. Inspect current behavior before editing.
5. Make the smallest code change that solves the issue.
6. Run focused verification.
7. If verification fails, debug from logs/errors, not guesses.
8. Finish with changed files, checks run, and remaining risk.

## Pokemon Verification Defaults

For `Pokemon/` code changes, prefer these checks when relevant:

- Go backend: `go test ./...` from `Pokemon/server`
- Python syntax: `python3 -m py_compile <changed-file>`
- Docker Compose config: `docker compose -f docker-compose.yml -f docker-compose.local-no-postgres-port.yml config --quiet`
- Frontend build: build through Docker if host `node_modules` is missing
- Runtime status: `docker compose ... ps`
- API health: `curl http://localhost:3001/health`
- Frontend health: `curl http://localhost:5173`
- Data pipeline: inspect service logs and PostgreSQL timestamps

## Stop Conditions

Stop and report when:

- A command needs network or system-level permissions the user has not approved.
- The task requires credentials, API keys, or private tokens.
- A fix would require deleting or reverting user work.
- The behavior depends on external marketplace data and the system is working but no matching data exists.

## External Plugin Policy

If the user wants the actual Superpowers plugin installed later:

1. Verify the exact install path from the official Codex plugin marketplace or the `obra/superpowers` repository.
2. Confirm the target harness: Codex CLI, Codex App, Claude Code, Cursor, etc.
3. Explain where it installs: global/user Codex plugin area, not app runtime code.
4. Do not commit generated plugin files unless the user explicitly asks for repo-local plugin development.
5. Do not install it into `package.json`, Docker images, Python requirements, or app source.
