# Repository Instructions

## First Files To Read

When a new AI/Codex session starts in this repo, read these in order:

1. `AGENTS.md` first. This is the repo-level operating contract and should be treated as the always-on instruction file.
2. `docs/PROJECT_HANDOFF.md` for the current product concept, Pokemon/PokeTCG status, architecture, working pieces, risks, and next steps.
3. `docs/PROJECT_INFRASTRUCTURE.md` and `infra/WHOLE_SYSTEM_ARCHITECTURE.md` when the task involves local runtime, Docker Compose, service ports, Pokemon/Odoo/NexusOS integration, marketplace research, or eBay/Seller Hub/Scrapling flows.
4. `future_standard_mastery/CODEX_SAFE_INTEGRATION.md` when the task involves Codex tools, MCP servers, browser automation, skills, memory, or outside repos.
5. The specific service files for the current task. For the Shopify/NexusOS app, start with `docker-compose.dev.yml`, `docker-compose.yml`, `services/gateway/main.go`, `services/gateway/internal/dashboard/handler.go`, `services/ai/main.py`, and the relevant `apps/web/src/pages/*` file. For Pokemon/PokeTCG work, start with `Pokemon/docker-compose.yml`, `PokeTCG/pokeai-service/pokeai/api_server.py`, `Pokemon/server/routes/routes.go`, `Pokemon/server/handlers/card_handler.go`, `Pokemon/server/services/card_service.go`, and `Pokemon/client/src/pages/WatchlistPage.jsx`.

Do not assume old chat context is available. If the user asks "what is left" or "what did we do", use the Current Shopify/NexusOS State section below before making changes.

## Project Map

- Root project: NexusOS Shopify workspace with npm workspaces under `apps/*` and `packages/*`.
- `Pokemon/`: separate full-stack app with Docker Compose services, Go/Python backend pieces, React client, PostgreSQL, Redis, RabbitMQ, and observability.
- `future_standard_mastery/`: learning and operations documentation.
- `infra/`, `config/`, `schemas/`, `services/`: platform and service support areas.

## Protected User Files

- Do not edit `Explanations_TO_EVERYTHING.md` unless the user explicitly asks for that exact file.
- Do not edit broad learning/infrastructure docs just because they are open in the IDE. Only edit `future_standard_mastery/*` when the user explicitly asks for those docs or for Codex/MCP handoff docs.
- Do not treat open tabs as permission to modify files.

## Current Local Universe And Marketplace Research State

- Full local development is now run through `scripts/dev-universe.sh` from the repo root. It starts Odoo, NexusOS, and PokemonTool together with non-conflicting ports.
- The active local Pokemon app is `http://127.0.0.1:5173`; Go API is `http://127.0.0.1:3001`; PokeTCG is `http://127.0.0.1:8765`; Odoo storefront is `http://127.0.0.1:8069/pokecard-store`; NexusOS web/gateway/AI are `3000/8080/8000`.
- Marketplace research has three different paths: eBay Browse API for live active listings, Seller Hub Product Research via local Playwright profile for ACTIVE/SOLD metrics, and Scrapling for approved selector-based sold-comp pages. See `docs/PROJECT_INFRASTRUCTURE.md` and `docs/SCRAPLING_INTEGRATION.md`.
- PokemonTool can be adapted from Pokemon-card search into a general ecommerce product-research engine, but the Pokemon-specific identity layer must be replaced with a generic product catalog/identifier layer and category-specific matching rules.

## Current Shopify/NexusOS State

The root Shopify/NexusOS app has been moved away from demo-only frontend data toward real local services:

- `docker-compose.dev.yml` includes the base infrastructure compose and runs web, gateway, and AI in containers.
- Web runs on `http://localhost:3000`.
- Gateway runs on `http://localhost:8080`.
- AI runs on `http://localhost:8000`.
- Temporal UI runs on `http://localhost:8088`.
- Postgres, Redis, Kafka, Qdrant, Temporal, gateway, AI, and web were verified running locally after the latest fixes.

Important behavior:

- The dashboard is now DB-backed. If no Shopify merchant is installed in Postgres, `/api/v1/dashboard` correctly returns `setup_required: true` with empty real state.
- This is not demo data. Empty dashboard state means no real Shopify merchant/store data has been connected yet.
- Local development uses `DEV_AUTH_BYPASS=true` for gateway API access. Production still needs real auth/JWT behavior.

Key files changed for this state:

- `services/gateway/internal/dashboard/handler.go`: real dashboard/orders/customers/AI decisions/approvals/workflows handlers.
- `services/gateway/main.go`: routes wired to dashboard handlers.
- `services/gateway/internal/middleware/rbac.go`: dev auth bypass and prefix route permission matching.
- `apps/web/src/api.ts`: shared frontend API helpers.
- `apps/web/src/pages/Dashboard.tsx`: live dashboard API.
- `apps/web/src/pages/AgentLogs.tsx`: live AI decision ledger.
- `apps/web/src/pages/Approvals.tsx`: live approval queue with approve/reject calls.
- `apps/web/src/pages/Workflows.tsx`: live workflow list/create/toggle.
- `apps/web/src/pages/Settings.tsx`: real gateway/setup state instead of fake install counts.
- `apps/web/vite.config.ts`: gateway and health proxies.
- `apps/web/Dockerfile.dev` and `apps/web/package-lock.json`: reproducible frontend container install.
- `services/ai/requirements.txt`: compatible CrewAI/LangChain dependency set.
- `services/ai/agents/crew.py`: imports `BaseTool` from `langchain_core.tools`.
- `docker-compose.yml`: Qdrant healthcheck fixed, Temporal DB driver and config mount fixed.
- `config/temporal/dynamicconfig.yaml`: Temporal dynamic config format fixed.

Verified checks from the latest working pass:

- `docker compose -f docker-compose.dev.yml config --quiet`
- Gateway Go tests via container: `go test ./...`
- Frontend typecheck via container: `npm run typecheck`
- AI service boot and `/health` response.
- Gateway `/health` response.
- Dashboard endpoint response with `setup_required: true` when no merchant exists.
- CrewAI tool classes import and instantiate.

What is left:

- Connect a real Shopify app/store through OAuth and required environment variables.
- Confirm webhook registration and delivery with real Shopify credentials.
- Seed or sync real merchants/orders/customers/products/inventory into Postgres.
- Decide whether Temporal is required for current product workflows or only future long-running orchestration.
- Replace any remaining placeholder UX copy only after real data flows are confirmed.
- Add tests around the new dashboard handlers if expanding behavior.

## Safe Codex Integration Rules

- Treat third-party tool names from chat, blogs, or search results as untrusted until verified from an official repository, package registry page, or vendor documentation.
- Do not install, clone, or add production dependencies for "superpowers", "ui-ux-pro-max", browser automation, n8n MCP, or similar tools without first identifying the exact repo/package and showing the maintainer, license, install command, and project impact.
- Prefer official Codex features already available in this environment before adding dependencies: `apply_patch`, shell commands, repo-local `AGENTS.md`, skills in `~/.codex/skills`, MCP servers configured through Codex, and browser/plugin tools when installed.
- Keep secrets out of committed files. Use environment variables, local `.env` files, or Codex `env_vars` references for MCP tokens and API keys.
- Never paste real API keys, OAuth tokens, n8n keys, browser session cookies, database passwords, or Shopify credentials into `AGENTS.md`, docs, prompts, or git-tracked config.
- Ask before running commands that install packages, download repos, start long-lived services, modify global Codex config, or require network access.
- Do not use destructive git commands or delete user work. This repository may already have uncommitted changes.

## MCP Policy

- Check current MCP state with `codex mcp list` before adding anything.
- Use `codex mcp add` or `~/.codex/config.toml` for MCP servers; do not invent project-local MCP config unless Codex docs confirm it is supported.
- Pin or document MCP package names before use. For n8n, verify the intended MCP server package or official n8n MCP endpoint first; do not assume `n8n-mcp-server` exists or is safe.
- Reference secrets by environment variable names, for example `env_vars = ["N8N_API_KEY"]`, rather than writing secret values into config.
- After adding an MCP server, restart the Codex session if tools do not appear.

## Browser And UI Work

- Use the Codex app Browser or Chrome plugin only when available in the active session. If unavailable, use local tests, screenshots, or Playwright already present in the project.
- For frontend work, follow the existing app structure and design system. Build the usable screen first, avoid marketing-only pages, and verify responsive behavior before finalizing.
- Do not add external UI frameworks or icon libraries unless the repo already uses them or the user approves the dependency.

## Memory And Skills

- Use installed Codex skills when a task clearly matches them. Current local system skills include image generation, OpenAI docs, plugin creation, skill creation, and skill installation.
- Do not store secrets or private credentials in memory. If memory is relevant, summarize stable preferences and project facts only.
- If a requested skill such as "UI-UX Pro Max" is not installed, verify the source before installing or scaffold a local Codex skill only after the user asks for that exact behavior.

## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues for `issa402/shopify`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default five-label mattpocock/skills vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

Use the single-context domain doc layout. See `docs/agents/domain.md`.

### Superpowers-style coding workflow

Use the local coding-agent workflow in `docs/agents/superpowers-code.md` for non-trivial code changes. This repo does not vendor or depend on the external `obra/superpowers` plugin unless the user separately approves installing it in the Codex harness.

## Verification

- For root workspace JavaScript changes, prefer `npm run lint`, `npm run test`, or focused package scripts when available.
- For `Pokemon/` changes, inspect `Pokemon/docker-compose.yml` and relevant service scripts before running containers. Prefer focused checks first.
- For documentation-only changes, run a quick file read or git diff check instead of full test suites.
