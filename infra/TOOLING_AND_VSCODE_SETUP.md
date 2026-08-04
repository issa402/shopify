# Tooling And VS Code Setup
## Practical Setup For Infrastructure / Platform / DevOps / Cloud Engineering

This guide is for your actual day-to-day environment.

Goal:
- reduce friction
- improve debugging
- make Python/Bash/Go/Docker work feel smoother
- support the Future Standard style of role

---

## The Big Picture

For this role, your editor is not just for writing app features.

You will constantly do:
- inspect logs
- edit scripts
- trace config
- compare files
- run terminals
- debug processes
- inspect Git diffs
- search large codebases

So the right setup is about:
- visibility
- speed
- correctness

not just aesthetics.

---

## Core VS Code Features To Actually Use

These built-in features already matter a lot:

## 1. Integrated terminal

Use it constantly.

Why:
- infra work is terminal-heavy
- you want editor + commands in one place

Good habits:
- keep one terminal for app startup
- one for logs
- one for Git/tests

## 2. Global search

Shortcut:
- `Ctrl+Shift+F`

Why:
- perfect for finding env vars, routes, health checks, queue usage, Docker refs

This is huge for architecture understanding.

## 3. Problems panel

Why:
- shows syntax/lint/type issues fast

## 4. Source control view

Why:
- see diffs clearly
- review your own changes before committing

Infra engineers should be disciplined about reviewing changes, especially config and scripts.

## 5. Split editor and diff view

Why:
- compare config versions
- compare scripts
- inspect before/after changes

---

## High-Value VS Code Extensions

These are the ones I would actually recommend for your role.

## Must-have

### Python

Why:
- linting
- debugging
- interpreter selection
- test discovery

Use for:
- infra scripts
- AI service work

### Pylance

Why:
- better autocomplete
- type understanding
- import awareness

### Go

Why:
- formatting
- navigation
- diagnostics
- test/debug integration

### Docker

Why:
- inspect containers/images/compose
- easier local visibility

### YAML

Why:
- GitHub Actions
- Docker Compose
- config files

### GitLens

Why:
- understand who changed what and when
- very helpful in a multi-service repo

### ShellCheck

Why:
- catches Bash mistakes early

### Bash IDE / shell-format support

Why:
- nicer Bash editing experience

### EditorConfig

Why:
- keeps formatting behavior consistent

---

## Nice-to-have

### Markdown All in One

Why:
- you are writing docs constantly

### Error Lens

Why:
- makes errors more visible inline

### Even Better TOML / JSON tools

Why:
- config quality matters

---

## Debugging Setup By Language

## Python debugging

You want to be able to:
- run a script with breakpoints
- inspect variables
- step through logic

Use for:
- config validators
- API clients
- health scripts
- DB analysis scripts

Good debugging questions:
- what input did my script actually receive?
- what env vars are missing?
- what did the API return?
- what branch did the script take?

## Go debugging

You want to be able to:
- run the server
- set breakpoints in handlers/services
- inspect startup config and dependency wiring

Useful for:
- health endpoint debugging
- startup failures
- route behavior

## Bash debugging

Bash debugging is more primitive but still important.

Main tools:
- `bash -n script.sh`
- `bash -x script.sh`
- `shellcheck script.sh`

Mental model:
- Bash debugging is usually about seeing command expansion and catching syntax/quoting mistakes

---

## Git Setup You Actually Need

For this role, Git skill matters because infra changes can be risky.

Things you should use every day:
- `git status`
- `git diff`
- `git diff --staged`
- `git log --oneline --graph`
- branch switching
- reviewing file-by-file changes

Inside VS Code:
- use Source Control panel
- read diffs before committing
- do not blindly commit generated junk or `.env` changes

---

## Terminal Tools Worth Having

These make infra work much easier:

## `rg` / ripgrep

Why:
- blazing fast code search

Use for:
- finding env vars
- tracing routes
- locating health checks
- finding Docker references

## `jq`

Why:
- parse JSON in terminal

Use for:
- API responses
- CI output
- logs

## `curl`

Why:
- test APIs and health endpoints

## `docker` / `docker compose`

Why:
- required for local infra work

## `psql`

Why:
- inspect Postgres directly

## `redis-cli`

Why:
- inspect Redis directly

## `shellcheck`

Why:
- Bash linting

## `watch`

Why:
- rerun a command repeatedly for live monitoring

---

## Suggested Workflow For This Repo

Here is a clean daily workflow.

### Terminal 1: startup

Use for:
- `dev-startup.sh`
- `docker compose up`

### Terminal 2: logs

Use for:
- tailing Go logs
- tailing Python logs
- `docker logs`

### Terminal 3: debugging / Git / health

Use for:
- `curl`
- `git diff`
- test commands

This keeps your brain organized.

---

## Recommended VS Code Habits

## 1. Keep `.env` files visible but be careful

You need them for infra understanding.
But do not accidentally commit secrets.

## 2. Use search before asking “where is this defined?”

This repo is big.
Search is one of your main infra tools.

## 3. Read logs in editor tabs sometimes

Useful for:
- startup failures
- comparing runs

## 4. Use markdown docs as working memory

You are already doing this well.
Keep architecture notes, task notes, and troubleshooting notes close.

## 5. Learn the debugger gradually

Do not avoid it.
It will save you a lot of time in Python and Go.

---

## Suggested Settings Mindset

You do not need a million extensions.

Optimize for:
- clean linting
- easy navigation
- strong search
- debugger support
- Docker/YAML visibility

Avoid:
- random theme/AI clutter
- too many overlapping language extensions
- extension bloat that slows the editor

---

## Handy Setup Checklist

Use this as your baseline.

### Languages
- Python
- Pylance
- Go
- YAML

### Infra / Ops
- Docker
- ShellCheck
- Bash support

### General productivity
- GitLens
- Markdown All in One
- EditorConfig

### CLI tools on machine
- `rg`
- `jq`
- `curl`
- `docker`
- `docker compose`
- `psql`
- `redis-cli`
- `shellcheck`

---

## What Matters Most For The Future Standard Role

You do not need a “hacker” setup.
You need a setup that helps you:
- inspect systems quickly
- automate safely
- debug calmly
- navigate large repos
- validate config and runtime state

That is much more valuable than fancy tooling.

---

## Final Advice

Your setup should help you do three things well:
- see what the system is doing
- change it safely
- explain what happened afterward

If a tool does not improve one of those, it is probably not high value right now.
