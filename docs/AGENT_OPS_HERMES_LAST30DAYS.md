# Agent Ops: Hermes and last30days

This project already has the core trading loop in the Pokemon app: Finder evidence, eBay/Seller Hub research, vendor insight scoring, alerts, and Odoo storefront sync. Hermes and last30days are useful, but they belong at the ops and intelligence layer, not inside the request path that serves users.

## Recommendation

Use `last30days` now for market pulse research. It is installed globally for this user at:

```bash
~/.agents/skills/last30days
```

Hermes Agent is installed locally as an ops copilot, not as part of the app runtime. It is a full autonomous agent runtime with terminal access, memory, messaging gateways, cron, MCPs, and credential surfaces. That can be powerful for operations, but it must stay behind scoped secrets and explicit approval boundaries.

Verified local install as of 2026-06-17:

```text
CLI:      /home/iscjmz/.local/bin/hermes
Project:  /home/iscjmz/.hermes/hermes-agent
Config:   /home/iscjmz/.hermes/config.yaml
Env:      /home/iscjmz/.hermes/.env
Skills:   /home/iscjmz/.hermes/skills
Data:     /home/iscjmz/.hermes/{cron,sessions,logs,memories}
Version:  Hermes Agent v0.16.0
```

`hermes doctor --fix` has migrated the config to v29. Core checks pass for Python, the CLI, Docker, Node, browser tooling, cron, terminal, file, memory, delegation, and skills. Remaining setup is optional provider/login/API-key work; add credentials only when a workflow needs them.

Setup status after running `hermes setup --quick`:

```text
Terminal backend: local machine
Messaging gateway: skipped for now
Cron jobs: none configured yet
Nous Portal auth: logged in via device_code OAuth
Model provider: nous
Default model: nvidia/nemotron-3-ultra:free
Free portal tools: web, image generation, TTS, STT, browser automation
Local Ollama fallback: available at 127.0.0.1:11434, currently only llama3:8b
```

Model policy for this machine:

1. The current Free plan runs Hermes through Nous Portal on `nvidia/nemotron-3-ultra:free`. Treat it as better than the local `llama3:8b` fallback and good for smoke tests, summaries, research, and read-only ops reports.
2. For high-stakes autonomous work, especially code edits, Docker triage, marketplace research, and multi-step planning, upgrade/select a stronger hosted model such as Claude Sonnet/Opus, GPT-5.x, Gemini Pro, or another high-quality provider.
3. Keep local Ollama models as fallback for cheap summaries, classification, formatting, and offline tasks. Do not rely on `llama3:8b` as the primary autonomous operator.
4. If a local model is needed, prefer a tool/JSON-oriented model such as Hermes-3 or another strong instruction/tool-calling model, then test it on read-only repo and health-check tasks before trusting it with cron.
5. Never grant write access to eBay, Odoo, Shopify, production databases, or credentials until read-only reports are boring and reliable.


## High-value last30days use cases

1. Detect buyer demand before it reaches pricing tools.
   Search Reddit, Hacker News, GitHub, Polymarket, and optional social sources for cards, sets, slabs, seller pain, and platform issues discussed in the last 30 days.

2. Improve Finder and alert priorities.
   Use research output to tune watchlists, identify card names or sets worth monitoring, and explain why a card should be watched even before eBay sold evidence is strong.

3. Find vendor workflow pain.
   Research what card sellers complain about around eBay, Shopify, Odoo, sold comps, watchers, bidders, inventory sync, and repricing.

4. Produce weekly vendor intelligence briefs.
   Save reports under `Pokemon/reports/last30days/` and review them alongside Seller Hub automation output.

5. Improve marketplace language.
   Pull real buyer/seller wording from recent communities to improve listing titles, app copy, and vendor-facing explanations.

## High-value Hermes use cases

1. Always-on operator from Telegram or Slack.
   Ask from a phone: "What are today's SOURCE_NOW opportunities?", "What slabs need research refreshed?", or "What failed overnight?"

2. Scheduled ops reports.
   Run daily or weekly reports for Seller Hub freshness, Odoo sync health, queue backlog, new vendor opportunities, stale sold evidence, and top margin cards.

3. Incident response assistant.
   Give it read-only access to Docker status, logs, service health, queue reports, and runbooks so it can triage app, Odoo, Postgres, and scraping failures.

4. Self-improving runbooks.
   Turn repeated fixes into reusable skills, especially for Seller Hub login/session renewal, Odoo sync recovery, and data freshness audits.

5. Parallel research agent.
   Use it to run separate workstreams for market pulse, competitor vendors, pricing strategy, and listing copy while the main app keeps running.

## Boundaries

Hermes should not get broad write access to eBay, Odoo, Shopify, production databases, or credentials on day one. Start with read-only reports and explicit operator approvals. Add write permissions only for narrow, reversible operations with logs.

Do not put Hermes in the app runtime path. If Hermes is down, PokemonTool should still work.

## Commands

Run the curated Pokemon vendor pulse:

```bash
cd /home/iscjmz/shopify/shopify/Pokemon
scripts/run_last30days_vendor_pulse.sh
```

Run a faster report:

```bash
scripts/run_last30days_vendor_pulse.sh --quick
```

Run with richer sources after adding optional API keys or browser sessions:

```bash
scripts/run_last30days_vendor_pulse.sh --search reddit,hackernews,github,web,polymarket,youtube,tiktok
```

Hermes Agent local verification:

```bash
hermes version
hermes doctor
hermes portal info
hermes chat -q "Reply with exactly: Hermes online" -Q --max-turns 1
hermes skills list
```

Last smoke test: `hermes chat -q "Reply with exactly: Hermes online" -Q --max-turns 1` returned `Hermes online`.

For this project, the first Hermes cron jobs should be read-only:

```text
Daily 8 AM: inspect Pokemon app health, Odoo health, Seller Hub automation freshness, and latest vendor opportunity alerts. Send a brief to the operator.
Weekly Monday: run the last30days vendor pulse, summarize new card/set demand signals, and suggest watchlist additions for review.
```

