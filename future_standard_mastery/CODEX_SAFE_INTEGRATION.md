# Codex Safe Integration Playbook

Use this when asking Codex to bring outside repos, MCP servers, browser tools, skills, or memory workflows into this project.

## Read Order For Future AI Sessions

The next AI should not have to guess where the truth lives:

1. Read root `AGENTS.md` first. Codex-style agents normally treat this as the repo instruction file.
2. Read this file when the task is about MCPs, Codex skills, browser tools, memory, outside repos, or safe tool integration.
3. For Shopify/NexusOS runtime work, inspect the actual service files after reading the docs: `docker-compose.dev.yml`, `docker-compose.yml`, `services/gateway/main.go`, `services/gateway/internal/dashboard/handler.go`, `services/ai/main.py`, and the relevant frontend page.
4. Do not edit `Explanations_TO_EVERYTHING.md` unless the user explicitly asks for it.

## Current App Handoff

The Shopify/NexusOS root app has been brought up locally with real service wiring rather than frontend demo arrays.

Working local URLs:

- Web: `http://localhost:3000`
- Gateway: `http://localhost:8080`
- AI: `http://localhost:8000`
- AI docs: `http://localhost:8000/docs`
- Temporal UI: `http://localhost:8088`

What was made real:

- Gateway dashboard/order/customer/AI decision/approval/workflow endpoints now read/write Postgres.
- Frontend dashboard, agent logs, approvals, workflows, and settings pages now call the gateway API.
- Approve/reject and workflow create/toggle actions persist through the gateway instead of mutating fake local data.
- Dev gateway auth uses `DEV_AUTH_BYPASS=true` so local UI work can continue before Shopify OAuth/JWT is fully wired.
- Qdrant, Temporal, gateway, AI, and web container startup issues were fixed.

Important truth:

- If no Shopify merchant is connected, `/api/v1/dashboard` returns `setup_required: true`.
- That empty state is expected and real. It means there is no merchant/store data in Postgres yet.
- Do not re-add fake demo data to make the dashboard look full.

Remaining real-product work:

- Configure a real Shopify app and OAuth environment.
- Complete/verify webhook registration with Shopify.
- Sync real merchants, orders, customers, products, and inventory into Postgres.
- Add focused tests for the new dashboard handler behavior if those endpoints are expanded.
- Decide whether Temporal is part of the near-term execution path or just available infrastructure.

## What Is Actually Available Here

- Codex CLI is installed as `codex-cli 0.130.0`.
- This workspace is trusted in `~/.codex/config.toml`.
- Configured Codex MCPs: `openaiDeveloperDocs`, `github`, `context7`, `memory`, `playwright`, `shadcn`, and `browser-use`.
- Repo-local instructions now live in `AGENTS.md`.
- Installed local Codex skills include system skills under `~/.codex/skills/.system/` plus `ui-ux-pro-max`.
- Browser Use is installed in `.codex-venvs/browser-use`; runtime config/cache are kept in ignored `.codex-browser-use/` and `.codex-cache/`.

## Codex Equivalents Installed

| Claude-style ask | Codex replacement here | Status |
| --- | --- | --- |
| Superpowers / repo brain | `AGENTS.md` + Codex skills + Context7 docs MCP | Installed |
| everything-claude-code style toolbox | Codex MCP set: GitHub, Context7, Memory, Playwright, shadcn, Browser Use | Installed |
| UI UX Pro Max | `ui-ux-pro-max` Codex skill from `jMerta/codex-skills` | Installed |
| Browser Use | Official Browser Use local MCP via project virtualenv | Installed; `doctor` passes core checks |
| Claude Mem | `@modelcontextprotocol/server-memory` MCP | Installed |
| n8n MCP | n8n built-in instance-level MCP server | Needs your n8n MCP URL/token |
| GitHub repo/PR powers | Official GitHub MCP remote server | Installed; needs `GITHUB_TOKEN` in shell |
| Live component UI help | Official shadcn/ui MCP | Installed |

## What Still Needs Your Token Or URL

- GitHub MCP: set `GITHUB_TOKEN` before launching Codex.
- n8n MCP: in n8n, enable Settings > Instance-level MCP, expose the workflows you want, then give Codex the server URL and token env var name. The URL usually looks like `https://<your-n8n-domain>/mcp-server/http`.
- Browser Use Cloud MCP is not configured. We installed the free local Browser Use MCP instead.

## Best Prompt To Use

```text
Codex, integrate this tool safely:

Tool/repo/package:
Goal:
Allowed scope:

Before installing or editing config:
1. Verify the official source, maintainer, license, latest release, and install command.
2. Explain what files/config will change.
3. Do not write secrets to git-tracked files.
4. Prefer repo-local docs/instructions over global config.
5. Ask before package installs, network downloads, or global Codex config changes.

After setup:
1. Show how to invoke it from Codex.
2. Run the smallest useful verification.
3. Document rollback steps.
```

## MCP Setup Pattern

1. Check existing MCP servers:

```bash
codex mcp list
```

2. Verify the target MCP server from official docs or the maintainer's repo.

3. Add it only after confirmation. Prefer environment variable references for secrets:

```toml
[mcp_servers.example]
command = "npx"
args = ["-y", "verified-package-name"]
env_vars = ["EXAMPLE_API_KEY"]
enabled = true
```

4. Restart Codex if the new tools do not appear.

## n8n MCP Pattern

Do not install random `n8n-mcp-server` packages. n8n has a built-in MCP server. Ask Codex:

```text
Add my n8n MCP server to Codex. URL: https://<my-n8n-domain>/mcp-server/http. Use env var N8N_MCP_TOKEN for the token. Do not write the token value into config.
```

Once verified, keep n8n credentials outside git:

```bash
export N8N_MCP_TOKEN="..."
```

Then add a Codex MCP config that references the token env var instead of a literal value.

## Browser Use Pattern

Use the installed `browser-use` MCP or the simpler `playwright` MCP. Ask:

```text
Use the browser to open http://localhost:5173, reproduce the issue, take a screenshot if possible, and fix only the UI files involved.
```

Browser Use local checks:

```bash
BROWSER_USE_HOME=/home/iscjmz/shopify/shopify/.codex-browser-use/home \
BROWSER_USE_CONFIG_DIR=/home/iscjmz/shopify/shopify/.codex-browser-use/config \
XDG_CACHE_HOME=/home/iscjmz/shopify/shopify/.codex-cache \
.codex-venvs/browser-use/bin/browser-use doctor
```

## Skills Pattern

Use installed skills by naming the goal clearly:

```text
Use the OpenAI docs skill to verify current Codex MCP config syntax, then update our playbook if needed.
```

For UI/UX work, invoke `$ui-ux-pro-max` or ask Codex naturally to use the UI/UX Pro Max skill. Restart Codex after installing skills.

## Safe Repo Integration Pattern

For any external repo:

1. Verify source and license.
2. Clone only into an explicit sandbox path such as `/tmp` or a clearly named `vendor/` area after approval.
3. Read docs before running scripts.
4. Avoid install scripts that modify shell profiles or global config unless the user approves.
5. Add a short integration note with how to update or remove it.

## Rollback Checklist

- Remove any added `mcp_servers.*` entry from `~/.codex/config.toml`.
- Unset related local environment variables.
- Delete unneeded cloned repos or dependencies after confirming they are not used.
- Re-run `codex mcp list`.
- Restart Codex.
