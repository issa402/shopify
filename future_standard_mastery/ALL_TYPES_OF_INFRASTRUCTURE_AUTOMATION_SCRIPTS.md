# All Types Of Infrastructure Automation Scripts In Bash And Python

This guide is for building real infrastructure intuition. It is not a pile of random commands. The goal is to teach you how to walk into a new Linux machine, a Docker project, a cloud repo, or a messy platform folder and understand what is alive, what is broken, what is risky, and what you can safely automate.

Infrastructure automation is the habit of turning repeated operational thinking into scripts. The script is not the important part at first. The important part is the mental model. A good infrastructure engineer is not someone who memorizes commands. A good infrastructure engineer knows what question they are asking the system, what signal proves the answer, what damage a command could cause, and how to make the next run safer than the last one.

When you enter any platform, think in layers. There is the machine layer, where Linux resources live: CPU, memory, disk, network, users, processes, ports, packages, logs, and services. There is the runtime layer, where Docker, Compose, Kubernetes, systemd, or process managers run programs. There is the app layer, where APIs, frontends, databases, queues, workers, migrations, webhooks, secrets, and health checks live. There is the data layer, where Postgres, Redis, object storage, backups, restores, and migrations determine whether the business survives mistakes. There is the delivery layer, where scripts, CI, deploys, rollbacks, and release checks decide whether changes reach production cleanly.

Your job is to learn how to inspect each layer without guessing. Guessing is how people break systems. Inspection is how people become trusted.

## Script Grammar You Must Understand First

This section is the decoder ring for the rest of the guide. If a script feels like magic, it is usually because the punctuation has not been explained yet. Infrastructure automation is full of punctuation: quotes, brackets, pipes, redirects, parentheses, braces, and weird variable expansion. Once you understand those pieces, scripts stop looking like spells and start looking like small sentences.

In Bash, spaces matter. `name=value` assigns a variable. `name = value` does not. The second version tries to run a command named `name` with arguments `=` and `value`. That is why Bash can feel rude at first. It is not reading English. It is splitting words.

Quotes matter because Bash splits unquoted variables on spaces. If `root="/home/me/My Project"` and you run `cd $root`, Bash sees two words: `/home/me/My` and `Project`. If you run `cd "$root"`, Bash sees one path. The habit is simple: quote variables unless you intentionally want word splitting.

`$var` reads a variable. `"${var}"` also reads a variable, but the braces make the variable boundary explicit. Use braces when adding text next to a variable, like `"${backup_dir}/file.sql"`.

`${1:-.}` means "use argument 1 if it exists and is not empty, otherwise use `.`." This is defaulting. You use it constantly in scripts because good scripts should have sensible defaults but allow overrides.

`${!name}` is indirect expansion. If `name="DATABASE_URL"`, then `${!name}` reads the value of `$DATABASE_URL`. You use this when looping over environment variable names.

`${#value}` gives the length of a variable's value. That is useful for secrets because printing length is safer than printing the actual token.

`$(command)` runs a command and captures its output. `timestamp="$(date +%Y%m%d_%H%M%S)"` stores the date output in a variable.

`|` is a pipe. It sends stdout from the command on the left into stdin of the command on the right. `find . -type f | sort` means "find files, then alphabetize the list."

`>` redirects stdout into a file and overwrites that file. `>>` appends instead of overwriting. Use both carefully. Redirection is how backup scripts write dumps, but it is also how careless scripts destroy files.

`2>&1` sends stderr to the same destination as stdout. File descriptor `1` is stdout. File descriptor `2` is stderr. `>/dev/null 2>&1` means throw away both normal output and error output.

`&&` means run the next command only if the previous one succeeded. `||` means run the next command only if the previous one failed. `grep pattern file || true` is common when "no matches" should not kill a strict script.

`if command; then ... else ... fi` checks the command's exit code. Exit code `0` means success. Anything else means failure. `fi` closes the `if`.

`for item in "${array[@]}"; do ... done` loops through an array. `"${array[@]}"` is the safe way to expand each array item separately.

`[[ ... ]]` is Bash's safer test syntax. `[[ -n "$value" ]]` means value is non-empty. `[[ -f "$file" ]]` means file exists and is a regular file. `[[ -d "$dir" ]]` means directory exists.

In `find`, `\(` and `\)` group conditions. The backslash is there because Bash treats plain parentheses specially. `-o` means OR. `-not` negates a condition. `-maxdepth` limits recursion. `-type f` means files only. `-name` matches filenames. `-path` matches the whole path.

In Python, `from pathlib import Path` gives you a safer way to work with paths than raw strings. `subprocess.run(...)` runs shell commands from Python. `check=True` means raise an exception if the command fails. `stdout=subprocess.PIPE` captures output. `json.dumps(..., indent=2)` turns structured data into readable JSON. `if __name__ == "__main__": main()` means "run main only when this file is executed directly, not when imported."

## How To Think When You Open A New Infrastructure Repo

Before you run anything, slow down and ask what kind of system you are holding. Is it a frontend app, a backend API, a data service, a worker system, a full Docker platform, a monorepo, or a bunch of scripts around a cloud environment? The fastest way to understand that is not reading every file. The fastest way is to map entrypoints.

An entrypoint is where execution begins. In a Linux service, it might be a `systemd` unit. In Docker Compose, it is the `command`, `entrypoint`, `Dockerfile`, and environment block. In a Node app, it is `package.json`. In Go, it is usually `main.go`. In Python, it is often `main.py`, `app.py`, `manage.py`, `pyproject.toml`, or a `uvicorn` command. In databases, it is migrations and seed scripts. In operations, it is usually a `scripts/` folder, a Makefile, a CI workflow, or a README command.

When you inspect a project, you are not asking "what files exist?" You are asking "what runs, in what order, using what configuration, against what dependencies, and how do I prove it works?" That question is the heart of infrastructure automation.

In this Shopify/NexusOS project, the important runtime entrypoints are `docker-compose.dev.yml`, `docker-compose.yml`, `services/gateway/main.go`, `services/ai/main.py`, `apps/web/package.json`, `apps/web/vite.config.ts`, and the database migrations under `services/gateway/internal/db/migrations`. That tells you this is not just a React app. It is a multi-service local platform with web, gateway, AI, Postgres, Redis, Kafka, Qdrant, Temporal, and Shopify-facing integration points.

Your first automation skill is making a repo map. A repo map should not be pretty. It should be useful. It should show you languages, package managers, Docker files, environment files, migrations, scripts, service folders, and obvious danger zones.

### What You Are Trying To Learn Before The Script

Before you write `repo_map.sh`, learn the questions that the script is asking.

The first question is "where am I?" On Linux, almost every command acts relative to your current directory. If you run a script from the wrong directory, it may inspect the wrong project and give you fake confidence. That is why you use `pwd`, which means print working directory. It tells you the absolute path you are standing in.

The second question is "is this a Git repo, and is it dirty?" A dirty repo means there are uncommitted changes. That matters because an automation script should not blindly edit files when someone may already have work in progress. `git rev-parse --is-inside-work-tree` is a quiet way to ask Git whether the current directory is inside a repository. `git status --short` gives a compact list of changed files. The short format is useful in scripts because it is easier to scan than the full friendly human message.

The third question is "what kind of app is this?" You answer that by looking for signature files. `package.json` usually means Node or frontend. `go.mod` means Go. `requirements.txt` or `pyproject.toml` means Python. `Dockerfile` means container build. `docker-compose.yml` means local multi-service runtime. `migrations/` means database schema history. `AGENTS.md` means AI/repo instructions. `README.md` usually explains human startup flow.

The fourth question is "what should I read first?" You do not read every file alphabetically. You find entrypoints. In Go, `main.go` is where a binary starts. In Python, `main.py`, `app.py`, or `server.py` often starts the service. In React/Vite, `main.tsx` is often the browser entrypoint. In Docker, `Dockerfile`, `docker-compose.yml`, `command`, and `entrypoint` explain how services are run.

Once you understand these questions, the script becomes obvious. It is just a repeatable way to ask them.

### Commands To Practice Before The Script

Run these manually first. Do not save a script yet. The point is to build command intuition.

Start with your location:

```bash
pwd
```

`pwd` prints the directory you are currently inside. If you are in `/home/iscjmz/shopify/shopify`, then `.` means `/home/iscjmz/shopify/shopify`. If you are in `/tmp`, then `.` means `/tmp`. That tiny dot is context-sensitive, so checking `pwd` prevents confusion.

List the top-level files:

```bash
ls
```

`ls` shows names in the current directory. It is useful, but it is shallow. It does not tell you what is deeper inside the repo.

List with details:

```bash
ls -la
```

`-l` means long format, which shows permissions, owner, size, and modification time. `-a` means all files, including hidden files like `.git` and `.env`. In infrastructure, hidden files matter because config and secrets often live behind dot names.

Ask whether Git recognizes this directory:

```bash
git rev-parse --is-inside-work-tree
```

`git rev-parse` is a plumbing command, which means it is more script-friendly than people-friendly. `--is-inside-work-tree` prints `true` if you are somewhere inside a Git working tree. This is better than assuming every folder is a repo.

See compact Git changes:

```bash
git status --short
```

The left two columns are status codes. `M` means modified. `??` means untracked. A clean output means Git sees no changed tracked files and no untracked files. In this repo, a dirty status is expected right now because work has been happening, but you still need to know it before editing.

Find files by name:

```bash
find . -name 'package.json'
```

`find` walks directories. The first argument `.` means start here. `-name 'package.json'` means match files or folders named exactly `package.json`. The quotes stop the shell from trying to expand special characters before `find` sees them.

Find only files, not directories:

```bash
find . -type f -name 'package.json'
```

`-type f` means regular files. Without it, `find` can match directories too. For a repo map, you usually want files.

Limit how deep you search:

```bash
find . -maxdepth 4 -type f -name 'package.json'
```

`-maxdepth 4` keeps the search from digging forever through huge dependency folders or generated files. Depth is counted from the starting point. `.` is depth 0, `./apps` is depth 1, `./apps/web` is depth 2, and so on.

Search for more than one filename:

```bash
find . -maxdepth 4 -type f \( -name 'package.json' -o -name 'go.mod' \)
```

This is the first part that looks weird. `\(` and `\)` group conditions. The backslashes matter because plain parentheses have special meaning to the shell. By writing `\(`, you tell Bash "pass this parenthesis to `find`; do not interpret it yourself." `-o` means OR. So this command means find files where the name is `package.json` OR `go.mod`.

Sort output so it is stable:

```bash
find . -maxdepth 4 -type f \( -name 'package.json' -o -name 'go.mod' \) | sort
```

The vertical bar `|` is a pipe. It sends the output of the command on the left into the input of the command on the right. Here, `find` prints paths in filesystem traversal order, which can feel random. `sort` makes the output alphabetical and repeatable.

Search paths, not just names:

```bash
find . -maxdepth 4 -type f -path '*/scripts/*'
```

`-name` only checks the final filename. `-path` checks the whole path. That means `-path '*/scripts/*'` catches files anywhere under a folder named `scripts`. The `*` means any characters. The quotes are important because you want `find` to interpret the `*`, not Bash.

Redirect noisy output away:

```bash
git rev-parse --is-inside-work-tree >/dev/null 2>&1
```

This is a common script pattern. `>/dev/null` sends normal output away. `2>&1` sends error output to the same place normal output is going. `/dev/null` is the Linux trash can for output. You use this when you only care whether the command succeeded, not what it printed.

Check a command inside an `if`:

```bash
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git status --short
else
  echo "not a git repository"
fi
```

In Bash, `if command; then` checks the command's exit code. Exit code `0` means success. Nonzero means failure. The word `fi` ends the `if` block. It is `if` spelled backward.

Understand script arguments:

```bash
root="${1:-.}"
```

This means "set `root` to the first script argument if the user gave one; otherwise use `.`." The `${...}` syntax is Bash parameter expansion. `$1` is the first argument. `:-.` means default to dot when the value is missing or empty. This lets someone run `./repo_map.sh` for the current directory or `./repo_map.sh /some/other/repo` for another directory.

Understand strict mode:

```bash
set -Eeuo pipefail
```

`set` changes Bash behavior. `-E` keeps error traps inherited in functions, which is advanced but safe to include. `-e` exits when a command fails. `-u` errors when you use an unset variable. `-o pipefail` makes a pipeline fail if any command inside the pipeline fails, not only the last command. This catches mistakes earlier. The tradeoff is that strict scripts require more careful handling of expected failures, which is why the Git check uses `if command; then` instead of letting failure crash the script.

### Lesson Task

Run a repo inspection script from the project root. Do not modify files. The goal is to answer this: what kind of project is this, where are the entrypoints, and what files would I read first before touching anything?

### Bash Script

Save this as `scripts/repo_map.sh` when you are ready to keep it. This version is intentionally over-commented. The comments are not how you would write every production script forever. They are here to teach you the Bash grammar and the infrastructure reasoning at the same time.

```bash
#!/usr/bin/env bash
# The shebang tells Linux which program should run this file.
# /usr/bin/env bash asks the system to find bash in the user's PATH.
# This is more portable than hardcoding /bin/bash on machines where bash may live elsewhere.

set -Eeuo pipefail
# set changes Bash safety behavior.
# -E keeps ERR traps inherited by functions and subshells. You will care more later.
# -e exits the script when an unhandled command fails.
# -u exits when the script tries to use a variable that was never set.
# -o pipefail makes a pipeline fail if any command inside it fails.
# Together, these make script failures loud instead of hidden.

root="${1:-.}"
# root is a variable holding the directory we want to inspect.
# $1 means the first argument passed to the script.
# ${1:-.} means use $1 if it exists and is not empty; otherwise use dot.
# Dot means the current directory.
# Example: ./scripts/repo_map.sh inspects the current directory.
# Example: ./scripts/repo_map.sh /tmp/some-repo inspects /tmp/some-repo.

cd "$root"
# cd changes the current directory.
# "$root" is quoted so paths with spaces do not break into multiple words.
# If cd fails, strict mode makes the script exit.

echo "== repo root =="
# echo prints text.
# This heading makes the output easier to scan.

pwd
# pwd means print working directory.
# This proves exactly what directory the script is inspecting.

echo
# echo with no arguments prints a blank line.
# Blank lines make command output easier for humans to read.

echo "== git state =="
# This section checks whether the repo has uncommitted or untracked work.

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
# if command; then runs the command and checks its exit code.
# git rev-parse --is-inside-work-tree succeeds only inside a Git working tree.
# >/dev/null discards normal output.
# 2>&1 discards error output too by sending stderr to stdout's destination.
# We hide output because we only care whether the command succeeded.

  git status --short
# git status --short prints compact changed-file status.
# This matters because automation should know whether user work already exists.

else
# else runs when the if command failed.

  echo "not a git repository"
# This tells the reader why no Git status was printed.

fi
# fi ends a Bash if block. It is "if" backward.

echo
echo "== high-signal files =="
# High-signal files tell you the type of project quickly.
# package.json means Node/frontend tooling.
# go.mod means Go module.
# requirements.txt or pyproject.toml means Python.
# Dockerfile and docker-compose files mean container runtime.
# Makefile means command shortcuts.
# .env.example means expected environment variables.
# AGENTS.md means AI operating instructions.
# README.md means human startup/context docs.

find . -maxdepth 4 -type f \
# find walks a directory tree.
# . means start from the current directory.
# -maxdepth 4 means do not search deeper than four directory levels.
# -type f means only return regular files, not directories.
# The trailing backslash continues this command onto the next line.

  \( -name 'package.json' \
# \( starts a grouped expression for find.
# The backslash is required so Bash passes the parenthesis to find.
# -name checks only the final filename.
# Single quotes keep the shell from interpreting special characters.

  -o -name 'package-lock.json' \
# -o means OR.
# This matches npm lockfiles, which tell you dependency versions are pinned.

  -o -name 'pnpm-lock.yaml' \
# This matches pnpm lockfiles.

  -o -name 'yarn.lock' \
# This matches Yarn lockfiles.

  -o -name 'go.mod' \
# This matches Go module files.

  -o -name 'requirements.txt' \
# This matches classic Python dependency files.

  -o -name 'pyproject.toml' \
# This matches modern Python project configuration.

  -o -name 'Dockerfile' \
# This matches standard Docker build files.

  -o -name 'Dockerfile.*' \
# This matches named Dockerfiles like Dockerfile.dev.
# The * is inside quotes, so find receives the pattern.

  -o -name 'docker-compose*.yml' \
# This matches Compose YAML files with .yml extension.

  -o -name 'docker-compose*.yaml' \
# This matches Compose YAML files with .yaml extension.

  -o -name 'Makefile' \
# This matches Make command shortcut files.

  -o -name '.env.example' \
# This matches example env files, which show required config without secrets.

  -o -name 'AGENTS.md' \
# This matches Codex/AI repo instruction files.

  -o -name 'README.md' \) \
# This matches README docs.
# \) closes the grouped find expression.

  | sort
# | is a pipe. It sends find's output into sort.
# sort makes the paths alphabetical and stable between runs.

echo
echo "== scripts =="
# Scripts are operational entrypoints.
# They often contain backup, setup, deploy, preflight, and maintenance logic.

find . -maxdepth 4 -type f \
# Again, search files up to depth four.

  \( -path './scripts/*' -o -path '*/scripts/*' \) \
# -path checks the whole path, not just the filename.
# './scripts/*' catches files in the root scripts folder.
# '*/scripts/*' catches scripts folders deeper in the repo.
# The group plus -o means either path pattern is accepted.

  | sort
# Sort for stable readable output.

echo
echo "== likely app entrypoints =="
# Entrypoints are files where a runtime probably begins.
# These are not guaranteed, but they are high-value starting points.

find . -maxdepth 5 -type f \
# Search one level deeper because app entrypoints may live under apps/web/src or services/name.

  \( -name 'main.go' \
# Go programs usually start from a main package, often in main.go.

  -o -name 'main.py' \
# Python services often start from main.py.

  -o -name 'app.py' \
# Flask/FastAPI apps are often app.py.

  -o -name 'server.py' \
# Some Python or Node-style services use server.py.

  -o -name 'index.ts' \
# TypeScript libraries and servers often use index.ts.

  -o -name 'index.tsx' \
# React apps can use index.tsx as a browser entrypoint.

  -o -name 'main.ts' \
# TypeScript apps can start from main.ts.

  -o -name 'main.tsx' \) \
# Vite React apps commonly start from main.tsx.
# \) closes the OR group.

  | sort
# Sort the entrypoint list.

echo
echo "== migrations =="
# Migrations are database history.
# If a project has migrations, you should understand them before changing data models.

find . -maxdepth 6 -type f \
# Migrations can be nested more deeply, so use depth six.

  \( -path '*/migrations/*' -o -path '*/migration/*' \) \
# Match either folder name: migrations or migration.
# Different frameworks use different names.

  | sort
# Sort the migration paths.
```

### Python Script

Python is useful when you want structured output instead of a wall of shell text. This version prints JSON so another tool can consume it later.

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(os.environ.get("REPO_ROOT", ".")).resolve()

INTERESTING_NAMES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "go.mod",
    "requirements.txt",
    "pyproject.toml",
    "Dockerfile",
    "Makefile",
    ".env.example",
    "AGENTS.md",
    "README.md",
}

INTERESTING_SUFFIXES = (
    ".Dockerfile",
    ".compose.yml",
    ".compose.yaml",
)

def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))

def is_ignored_dir(path: Path) -> bool:
    return path.name in {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache"}

def main() -> None:
    result = {
        "root": str(ROOT),
        "high_signal_files": [],
        "scripts": [],
        "entrypoints": [],
        "migrations": [],
    }

    for current, dirs, files in os.walk(ROOT):
        current_path = Path(current)
        dirs[:] = [d for d in dirs if not is_ignored_dir(current_path / d)]

        depth = len(current_path.relative_to(ROOT).parts)
        if depth > 6:
            dirs[:] = []
            continue

        for file_name in files:
            path = current_path / file_name
            relative = rel(path)

            if file_name in INTERESTING_NAMES or file_name.startswith("docker-compose"):
                result["high_signal_files"].append(relative)

            if "/scripts/" in f"/{relative}":
                result["scripts"].append(relative)

            if file_name in {"main.go", "main.py", "app.py", "server.py", "main.tsx", "main.ts", "index.ts", "index.tsx"}:
                result["entrypoints"].append(relative)

            if "/migrations/" in f"/{relative}" or "/migration/" in f"/{relative}":
                result["migrations"].append(relative)

    for key in result:
        if isinstance(result[key], list):
            result[key] = sorted(result[key])

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

## How To Think About Local Linux Before You Blame The App

Many app problems are not app problems. They are local machine problems. A port is already taken. Docker cannot access the daemon. The disk is full. DNS is failing inside Docker. A process is dead but the frontend is cached. A container is running but unhealthy. Your job is to separate machine failure from application failure.

The intuition is simple: an app needs resources before it can need correctness. It needs a process. The process needs CPU and memory. It needs disk space for logs, databases, package installs, and Docker layers. It needs ports. It needs network access. It needs secrets. It needs dependencies. If any of those are broken, the source code can be perfect and the app still fails.

When you do local preflight, do not try to prove the whole app works. Prove that the machine is capable of running the app. This is the difference between infrastructure thinking and random debugging.

### Lesson Task

Before starting the project, check Linux health, Docker access, disk, memory, and ports. In this project, the important local ports are `3000`, `8080`, `8000`, `5432`, `6379`, `6333`, `7233`, `8088`, `9092`, and `11434`.

### Commands To Practice Before The Script

Check the kernel and machine:

```bash
uname -a
```

`uname` prints system information. `-a` means all available information. You use this when you need to know what Linux kernel and architecture you are on. Architecture matters because some Docker images, binaries, and packages behave differently on `x86_64` versus ARM.

Check disk space:

```bash
df -h .
```

`df` means disk free. `-h` means human-readable, so you see sizes like `42G` instead of raw block counts. The final `.` means "show the filesystem that contains my current directory." You care because Docker builds, Postgres data, logs, and package installs can fail when disk is full.

Check memory:

```bash
free -h
```

`free` shows memory. Again, `-h` means human-readable. If memory is tight, containers may restart or builds may die in confusing ways.

Check Docker access:

```bash
docker info
```

`docker info` talks to the Docker daemon. If this fails, your app containers do not matter yet. You first need Docker permissions, Docker Desktop/Engine running, or socket access fixed.

Check listening TCP ports:

```bash
ss -ltn
```

`ss` shows sockets. `-l` means listening sockets. `-t` means TCP. `-n` means numeric, so it prints port numbers instead of trying to resolve service names. You use this when a service cannot bind to a port or when you need to know whether something is already using `3000` or `8080`.

Filter one port:

```bash
ss -ltn "( sport = :8080 )"
```

The expression means "show listening TCP sockets whose source port is 8080." In a listening socket, the source/local port is the port the process owns. The spaces inside the parentheses matter for `ss` parsing.

Understand the loop:

```bash
for port in 3000 8080 8000; do
  echo "$port"
done
```

`for` loops over words. `port` is the variable name. `do` starts the loop body. `done` ends it. `"$port"` expands the current value. Quote variables by default because it prevents word-splitting surprises.

### Bash Script

```bash
#!/usr/bin/env bash
# Use bash to run this file.

set -Eeuo pipefail
# Make the script fail loudly on unhandled errors, unset variables, and broken pipelines.

ports=(3000 8080 8000 5432 6379 6333 7233 8088 9092 11434)
# This is a Bash array.
# Parentheses create the array.
# Each space-separated value is one item.
# These are the local ports this project commonly uses.

echo "== machine =="
# Print a heading so the output has readable sections.

uname -a
# Print kernel, hostname, kernel version, date, architecture, and OS info.
# Use this to understand the local Linux environment.

echo
# Print a blank line.

echo "== disk =="
# Start disk section.

df -h .
# Show disk space for the filesystem containing the current directory.
# -h makes sizes human-readable.
# . means current directory.

echo
echo "== memory =="
free -h || true
# Show memory in human-readable units.
# || means OR in shell command flow.
# true always succeeds.
# So if free is missing on some machine, the script keeps going instead of dying.

echo
echo "== docker daemon =="
if docker info >/dev/null 2>&1; then
# Run docker info but hide its output.
# If the command succeeds, Docker is reachable.
# >/dev/null throws away stdout.
# 2>&1 sends stderr to the same place as stdout.

  echo "docker daemon reachable"
# Print success.

else
# If docker info failed, run this branch.

  echo "docker daemon not reachable"
# Print failure without crashing.

fi
# End the if block.

echo
echo "== port preflight =="
for port in "${ports[@]}"; do
# Loop over every item in the ports array.
# "${ports[@]}" expands each array item as its own safe word.
# port becomes the current port number each time through the loop.

  if ss -ltn "( sport = :$port )" | tail -n +2 | grep -q .; then
# ss -ltn lists listening numeric TCP sockets.
# "( sport = :$port )" filters to one local/source port.
# The output includes a header line, so tail -n +2 skips the first line.
# grep -q . checks whether any non-empty line remains.
# The pipe connects ss -> tail -> grep.
# If grep finds a line, something is listening on that port.

    echo "port $port is already listening"
# This means the port is occupied. That may be good or bad depending on context.

  else
# If no process is listening on that port:

    echo "port $port is free"
# This means a service should be able to bind this port.

  fi
# End the if block.

done
# End the for loop.
```

### Python Script

```python
#!/usr/bin/env python3
from __future__ import annotations

import shutil
import socket
import subprocess

PORTS = [3000, 8080, 8000, 5432, 6379, 6333, 7233, 8088, 9092, 11434]

def port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0

def command_ok(command: list[str]) -> bool:
    try:
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False

def main() -> None:
    total, used, free = shutil.disk_usage(".")
    print(f"disk_free_gb={free / 1024 / 1024 / 1024:.2f}")
    print(f"docker_reachable={command_ok(['docker', 'info'])}")

    for port in PORTS:
        state = "listening" if port_is_open(port) else "free"
        print(f"port_{port}={state}")

if __name__ == "__main__":
    main()
```

## How To Think About Environment Variables And Secrets

Configuration is how the same code behaves differently in dev, staging, and production. Secrets are configuration values that can hurt you if leaked. A password, API token, Shopify access token, GitHub token, webhook secret, session key, and database URL with credentials are all secrets.

The intuition is that a service rarely fails because a variable exists. It fails because a required variable is missing, misspelled, points to the wrong host, uses a production value in development, or is accidentally committed. When debugging infra, environment variables are not boring. They are often the whole story.

Never print secret values in normal scripts. Print whether they are present, whether they look like the right kind of value, and where the service expects them. For example, in Docker Compose a container should connect to `postgres:5432`, not `localhost:5432`, because `localhost` inside a container means the container itself.

### Lesson Task

Audit the environment expectations for the project without leaking secrets. Your goal is to know which variables are set, which are missing, and which ones are dangerous to commit.

### Commands To Practice Before The Script

Print one environment variable safely:

```bash
printf '%s\n' "${SHOPIFY_API_VERSION:-missing}"
```

`printf` is more predictable than `echo` for formatted output. `%s\n` means print a string followed by a newline. `${SHOPIFY_API_VERSION:-missing}` means use the variable value if it exists, otherwise print `missing`. This teaches you how to check config without crashing on an unset variable.

Check whether a variable exists without showing the value:

```bash
if [[ -n "${OPENAI_API_KEY:-}" ]]; then echo "set"; else echo "missing"; fi
```

`[[ ... ]]` is Bash's safer test syntax. `-n` means the string length is nonzero. `${OPENAI_API_KEY:-}` expands to an empty string if the variable is unset. This is how you avoid leaking secrets while still knowing whether the process can authenticate.

Understand indirect expansion:

```bash
name="DATABASE_URL"
printf '%s\n' "${!name:-missing}"
```

`${!name}` means "use the value of the variable whose name is stored in `name`." If `name` contains `DATABASE_URL`, then `${!name}` reads `$DATABASE_URL`. This is useful when looping over variable names.

Count secret length without printing it:

```bash
printf '%s' "${DATABASE_URL:-}" | wc -c | tr -d ' '
```

`wc -c` counts bytes. `tr -d ' '` deletes spaces from the output. Length is safe to print because it proves the variable exists without revealing the secret.

Find local env files:

```bash
find . -maxdepth 4 -type f \( -name '.env' -o -name '*.env' -o -name '.env.*' \) -not -name '.env.example' -print
```

This searches for files that may contain real secrets. `-not -name '.env.example'` excludes example files because examples should not contain real secret values.

### Bash Script

```bash
#!/usr/bin/env bash
# Run this file with Bash.

set -Eeuo pipefail
# Strict mode: fail on hidden errors, unset variables, and broken pipelines.

required=(
# Start a Bash array named required.
# Each item is the name of an environment variable we care about.

  DATABASE_URL
# Database connection string. Often contains username/password, so do not print it.

  KAFKA_BROKERS
# Kafka broker list. In Docker Compose, this should usually use service names.

  PORT_GATEWAY
# Gateway HTTP port.

  SHOPIFY_API_VERSION
# Shopify Admin API version.

  SHOPIFY_API_KEY
# Shopify app key. Treat as sensitive.

  SHOPIFY_API_SECRET
# Shopify app secret. Definitely sensitive.

  SHOPIFY_WEBHOOK_SECRET
# Used to verify Shopify webhook signatures.

  OPENAI_API_KEY
# OpenAI token, if cloud models are used.

  ANTHROPIC_API_KEY
# Anthropic token, if Claude models are used.

  GITHUB_TOKEN
# GitHub token, used by GitHub MCP/automation.

)
# End the array.

echo "== environment presence audit =="
# Start the audit section.

for name in "${required[@]}"; do
# Loop over every variable name in the required array.
# name will be DATABASE_URL, then KAFKA_BROKERS, and so on.

  if [[ -n "${!name:-}" ]]; then
# ${!name} is indirect expansion. It reads the environment variable named by $name.
# :- makes the value empty if the variable is missing.
# [[ -n STRING ]] succeeds when STRING is not empty.

    length="${#name}"
# This stores the length of the variable name, not the secret value.
# It is not actually needed for the output below, but shows ${#var} syntax.

    value_length="$(printf '%s' "${!name}" | wc -c | tr -d ' ')"
# $(...) captures command output into a variable.
# printf prints the secret value without adding a newline.
# wc -c counts bytes.
# tr -d ' ' removes spaces from wc output.
# We print only the length, not the secret itself.

    echo "$name=set length=$value_length"
# Show the variable is set and how long it is.

  else
# If the variable is missing or empty:

    echo "$name=missing"
# Print missing.

  fi
# End the if.

done
# End the loop.

echo
echo "== possible committed env files =="
# Search the repo for real env files that may contain secrets.

find . -maxdepth 4 -type f \
# Start at current directory, search up to depth four, return files only.

  \( -name '.env' -o -name '*.env' -o -name '.env.*' \) \
# Match common env filename patterns.
# Grouping is escaped so find receives the parentheses.
# -o means OR.

  -not -name '.env.example' \
# Exclude example env files because they should be safe templates.

  -print
# Print matching paths.
```

### Python Script

```python
#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

REQUIRED = [
    "DATABASE_URL",
    "KAFKA_BROKERS",
    "PORT_GATEWAY",
    "SHOPIFY_API_VERSION",
    "SHOPIFY_API_KEY",
    "SHOPIFY_API_SECRET",
    "SHOPIFY_WEBHOOK_SECRET",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GITHUB_TOKEN",
]

SECRET_HINTS = ("TOKEN", "SECRET", "PASSWORD", "KEY", "DATABASE_URL")

def mask_state(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        return "missing"
    return f"set length={len(value)}"

def looks_secret(path: Path) -> bool:
    name = path.name.lower()
    return name == ".env" or name.endswith(".env") or ".env." in name

def main() -> None:
    print("environment_presence")
    for name in REQUIRED:
        print(f"{name}={mask_state(name)}")

    print()
    print("possible_local_env_files")
    for path in sorted(Path(".").rglob("*")):
        if path.is_file() and looks_secret(path) and path.name != ".env.example":
            print(path)

if __name__ == "__main__":
    main()
```

## How To Think About Docker Compose

Docker Compose is a local platform description. It tells you what services exist, how they are built, what ports they expose, what files they mount, what environment they receive, what healthchecks prove readiness, and what depends on what.

The important intuition is that `running` does not mean `ready`. A database container can be running while still applying migrations. Kafka can be running while the broker is not ready. A web container can be running while Vite is still compiling. That is why healthchecks matter. A good automation script should ask Compose for both container status and real endpoint behavior.

In this project, `docker-compose.dev.yml` includes `docker-compose.yml`. That means the dev app services depend on base infrastructure. If someone runs only one file or forgets the include behavior, they can misread the system.

### Lesson Task

Validate Compose config, start the stack, inspect service status, and then hit real health endpoints.

### Commands To Practice Before The Script

Validate Compose without starting anything:

```bash
docker compose -f docker-compose.dev.yml config --quiet
```

`docker compose` is the Docker plugin for multi-container apps. `-f docker-compose.dev.yml` selects the compose file. `config` asks Compose to parse and merge the file. `--quiet` means print nothing if valid. This catches YAML mistakes, missing includes, and invalid Compose structure before containers move.

Start containers in the background:

```bash
docker compose -f docker-compose.dev.yml up -d
```

`up` creates and starts the services. `-d` means detached mode, so the command returns instead of attaching logs to your terminal. Use this when you want the stack running while you continue checking it.

See service state:

```bash
docker compose -f docker-compose.dev.yml ps
```

`ps` shows Compose services, container names, status, health, and ports. This is the status layer, not the proof layer. A service can be `Up` and still not useful yet.

Hit a health endpoint:

```bash
curl -fsS http://localhost:8080/health
```

`curl` makes HTTP requests. `-f` fails on HTTP error statuses. `-s` makes it quiet. `-S` still shows errors when `-s` is active. This is how you prove a service responds through the port you expect.

### Bash Script

```bash
#!/usr/bin/env bash
# Run this script with Bash.

set -Eeuo pipefail
# Strict mode for safer automation.

compose_file="${1:-docker-compose.dev.yml}"
# Use the first argument as the compose file if provided.
# Otherwise default to docker-compose.dev.yml.
# This lets you run:
# ./compose_check.sh
# or:
# ./compose_check.sh docker-compose.yml

echo "== compose config =="
# Print section heading.

docker compose -f "$compose_file" config --quiet
# Ask Compose to parse and merge the config.
# -f selects the compose file.
# "$compose_file" is quoted so paths with spaces are safe.
# config does not start services.
# --quiet means no output unless something is wrong.

echo "compose config ok"
# If we got here, config validation passed.

echo
echo "== start stack =="
docker compose -f "$compose_file" up -d
# Start or update the stack.
# up creates containers/networks/volumes if needed.
# -d means detached/background mode.

echo
echo "== service status =="
docker compose -f "$compose_file" ps
# Show current service/container status.
# Look for Up, healthy, unhealthy, restarting, exited, and port mappings.

echo
echo "== endpoint checks =="
curl -fsS http://localhost:8080/health
# Hit gateway health.
# -f makes bad HTTP statuses fail the command.
# -s hides progress noise.
# -S still prints errors.

echo
curl -fsS http://localhost:8000/health
# Hit AI service health.

echo
curl -fsS http://localhost:3000 >/dev/null
# Hit the web app root.
# Redirect HTML to /dev/null because we only care that it responds.

echo "web responded"
# Print success if curl did not fail.
```

### Python Script

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import urllib.request

COMPOSE = ["docker", "compose", "-f", "docker-compose.dev.yml"]

def run(command: list[str]) -> str:
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    return completed.stdout

def get(url: str) -> tuple[int, str]:
    with urllib.request.urlopen(url, timeout=5) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, body

def main() -> None:
    run(COMPOSE + ["config", "--quiet"])
    run(COMPOSE + ["up", "-d"])
    ps_json = run(COMPOSE + ["ps", "--format", "json"])

    print("compose_services")
    for line in ps_json.splitlines():
        if line.strip():
            service = json.loads(line)
            print(f"{service.get('Service')} status={service.get('State')} health={service.get('Health')}")

    for url in ["http://localhost:8080/health", "http://localhost:8000/health", "http://localhost:3000"]:
        status, body = get(url)
        print(f"{url} status={status} bytes={len(body)}")

if __name__ == "__main__":
    main()
```

## How To Think About Logs

Logs are the story a system tells after something happened. Beginners read logs from top to bottom and drown. Professionals search for transitions. They look for startup, config loading, dependency connection, migrations, listening ports, warnings, errors, restarts, and shutdown.

A log line is not automatically important because it says warning. A warning about missing plotly in an AI service may be harmless if the service still starts. A single database DNS error during container startup may be transient if the next start connects. But a repeated restart loop with the same error is a real blocker.

Your instinct should be to compare status with logs. If a service is unhealthy, read its healthcheck and logs. If a service is up but endpoint checks fail, read its bind address and port mapping. If a service restarts, read the first real exception after startup.

### Lesson Task

Write a triage script that pulls recent logs for the services that matter and extracts high-signal failure words.

### Commands To Practice Before The Script

Show logs for one service:

```bash
docker compose -f docker-compose.dev.yml logs --tail=80 gateway
```

`logs` reads container logs through Compose. `--tail=80` means show only the last 80 lines. You use a tail because recent startup errors are usually near the end, and dumping thousands of lines trains you to ignore the output.

Search logs for important words:

```bash
docker compose -f docker-compose.dev.yml logs --tail=160 gateway | grep -Ei 'error|failed|started|ready'
```

`grep` searches text. `-E` enables extended regular expressions, so `a|b|c` means match any of those alternatives. `-i` means case-insensitive. You are not letting grep decide the whole truth. You are using it as a flashlight.

Allow an expected no-match:

```bash
grep -Ei 'error|failed' some.log || true
```

`grep` returns a nonzero exit code when it finds no matches. In strict Bash mode, that would stop the script. `|| true` says "if grep finds nothing, that is okay here."

### Bash Script

```bash
#!/usr/bin/env bash
# Run this file with Bash.

set -Eeuo pipefail
# Strict mode so unexpected command failures stop the script.

compose_file="${1:-docker-compose.dev.yml}"
# Default to the dev compose file unless the user passes another file.

services=(gateway ai web postgres qdrant temporal kafka redis)
# Bash array of services worth checking.
# These names must match Compose service names, not container names.

for service in "${services[@]}"; do
# Loop through each service.

  echo
# Blank line for readability.

  echo "== $service status =="
# Print which service status is coming.

  docker compose -f "$compose_file" ps "$service" || true
# Show Compose status for only this service.
# || true prevents one missing/stopped service from ending the whole triage script.

  echo
  echo "== $service high-signal logs =="
# Print log section heading.

  docker compose -f "$compose_file" logs --tail=160 "$service" \
# Read the last 160 log lines for this service.
# The backslash continues the command.

    | grep -Ei 'error|failed|panic|fatal|unhealthy|refused|denied|timeout|migration|started|ready|listening' \
# Pipe logs into grep.
# -E allows the OR pattern with |.
# -i ignores case.
# The pattern includes both bad words and good transition words.

    || true
# If grep finds no matching lines, do not fail the whole script.

done
# End service loop.
```

### Python Script

```python
#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess

SERVICES = ["gateway", "ai", "web", "postgres", "qdrant", "temporal", "kafka", "redis"]
PATTERN = re.compile(r"error|failed|panic|fatal|unhealthy|refused|denied|timeout|migration|started|ready|listening", re.I)

def logs(service: str) -> str:
    completed = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.dev.yml", "logs", "--tail=160", service],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.stdout

def main() -> None:
    for service in SERVICES:
        print(f"\n== {service} ==")
        for line in logs(service).splitlines():
            if PATTERN.search(line):
                print(line)

if __name__ == "__main__":
    main()
```

## How To Think About Databases, Migrations, Backups, And Restores

The database is where mistakes become expensive. Code can be redeployed. Containers can be rebuilt. Data loss is different. That is why infrastructure engineers treat backups and restores as separate things. A backup that has never been restored is only a hope.

Migrations are controlled changes to database shape. A migration can create a table, add an index, change a column, or install an extension. The intuition is that migrations are not just code. They are history. If migration history and database reality drift apart, the app can become confused.

Backups are copies of data. Restores prove copies are usable. A serious automation habit is to create a backup script and a restore drill script. The restore drill can use a temporary database so you do not risk the live one.

### Lesson Task

Create a Postgres backup, list migration files, and practice a restore into a temporary database. Do not restore over the main database.

### Commands To Practice Before The Script

List migrations:

```bash
find services/gateway/internal/db/migrations -type f | sort
```

This tells you what database history exists in the repo. If migrations are missing, out of order, or surprising, stop and understand them before changing schema or data.

Run a command inside a container:

```bash
docker compose -f docker-compose.dev.yml exec -T postgres pg_isready -U nexusos
```

`exec` runs a command inside an already running container. `-T` disables pseudo-terminal allocation, which is better for scripts and redirected output. `pg_isready` checks whether Postgres is accepting connections.

Understand output redirection:

```bash
docker compose -f docker-compose.dev.yml exec -T postgres pg_dump -U nexusos -d nexusos > backup.sql
```

`>` writes stdout to a file. This is powerful and dangerous. If `backup.sql` already exists, it will be overwritten. In backup scripts, use timestamps so each run creates a new file.

### Bash Script

```bash
#!/usr/bin/env bash
# Run this file with Bash.

set -Eeuo pipefail
# Strict mode for safer backup automation.

compose_file="${1:-docker-compose.dev.yml}"
# First argument chooses Compose file, defaulting to dev.

backup_dir="${2:-backups/postgres}"
# Second argument chooses backup folder, defaulting to backups/postgres.

timestamp="$(date +%Y%m%d_%H%M%S)"
# date prints the current time.
# +%Y%m%d_%H%M%S formats it as year month day underscore hour minute second.
# $(...) captures command output into the timestamp variable.

backup_file="$backup_dir/nexusos_$timestamp.sql"
# Build the final backup file path.
# The timestamp prevents overwriting older backups.

mkdir -p "$backup_dir"
# Create the backup directory if it does not exist.
# -p means do not fail if it already exists.

echo "== migrations =="
find services/gateway/internal/db/migrations -type f | sort
# Print migration files so you see schema history near the backup output.

echo
echo "== backup =="
docker compose -f "$compose_file" exec -T postgres \
# Run the next command inside the postgres Compose service.
# -T disables TTY behavior, which keeps redirected SQL output clean.

  pg_dump -U nexusos -d nexusos --clean --if-exists --no-owner \
# pg_dump exports the database.
# -U nexusos connects as the nexusos database user.
# -d nexusos dumps the nexusos database.
# --clean includes DROP statements before CREATE statements.
# --if-exists avoids errors when dropping objects that may not exist.
# --no-owner avoids restoring ownership tied to one machine/user.

  > "$backup_file"
# Redirect the SQL dump into the backup file on the host machine.

echo "backup_written=$backup_file"
# Print where the backup was written.

wc -lh "$backup_file"
# wc shows counts.
# -l counts lines.
# -h prints human-readable size where supported.
```

### Python Script

```python
#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import subprocess
from pathlib import Path

BACKUP_DIR = Path("backups/postgres")

def main() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"nexusos_{timestamp}.sql"

    command = [
        "docker", "compose", "-f", "docker-compose.dev.yml",
        "exec", "-T", "postgres",
        "pg_dump", "-U", "nexusos", "-d", "nexusos",
        "--clean", "--if-exists", "--no-owner",
    ]

    with backup_file.open("wb") as out:
        subprocess.run(command, stdout=out, check=True)

    print(f"backup_written={backup_file}")
    print(f"bytes={backup_file.stat().st_size}")

if __name__ == "__main__":
    main()
```

## How To Think About Smoke Tests

A smoke test is not a full test suite. It is the fastest proof that the system is alive enough to continue. The name comes from hardware: turn it on and see if smoke comes out. In software, smoke tests check health endpoints, essential pages, key APIs, and dependency readiness.

The intuition is that a smoke test should be cheap, repeatable, and boring. It should not require a human clicking around. It should not depend on fake data unless the system explicitly seeds fake data for tests. In this project, a real empty Shopify state is valid. That means a smoke test should accept `setup_required: true` as a good response when no merchant exists.

### Lesson Task

Write a smoke test that checks web, gateway, AI, and dashboard state.

### Commands To Practice Before The Script

Check one endpoint:

```bash
curl -fsS http://localhost:8080/health
```

This proves the gateway answers over HTTP. A health check is stronger than `docker ps` because it proves the service is reachable through the same port your browser or frontend will use.

Check whether HTML contains the root mount:

```bash
curl -fsS http://localhost:3000 | grep -q '<div id="root"></div>'
```

The frontend may return a lot of HTML. `grep -q` searches quietly and exits success if it finds the pattern. This is a tiny smoke test for "Vite served the React shell."

Capture JSON in a variable:

```bash
dashboard="$(curl -fsS http://localhost:8080/api/v1/dashboard)"
```

`$(...)` captures command output. This lets you inspect the dashboard response more than once without making repeated network calls.

### Bash Script

```bash
#!/usr/bin/env bash
# Run with Bash.

set -Eeuo pipefail
# Strict mode.

echo "== gateway health =="
curl -fsS http://localhost:8080/health
# Call the gateway health endpoint. Fail if HTTP status is bad.

echo
# Blank line.

echo "== ai health =="
curl -fsS http://localhost:8000/health
# Call the AI health endpoint.

echo

echo "== web html =="
curl -fsS http://localhost:3000 | grep -q '<div id="root"></div>'
# Fetch web HTML and confirm the React root div exists.
# grep -q prints nothing; it only returns success or failure.

echo "web root found"
# If grep succeeded, print success.

echo
echo "== dashboard api =="
dashboard="$(curl -fsS http://localhost:8080/api/v1/dashboard)"
# Fetch dashboard JSON once and store it in a variable.

printf '%s\n' "$dashboard"
# Print the JSON safely.

if printf '%s' "$dashboard" | grep -q '"setup_required":true'; then
# Pipe the JSON into grep.
# If setup_required is true, the empty-state app is still valid.

  echo "dashboard is in valid setup-required empty state"
# No merchant connected yet, but the API works.

else
# Otherwise:

  echo "dashboard returned merchant-backed state"
# This means a merchant probably exists in Postgres.

fi
# End if.
```

### Python Script

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.request

def get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.read().decode("utf-8", errors="replace")

def main() -> None:
    gateway = json.loads(get("http://localhost:8080/health"))
    ai = json.loads(get("http://localhost:8000/health"))
    web = get("http://localhost:3000")
    dashboard = json.loads(get("http://localhost:8080/api/v1/dashboard"))

    assert gateway["status"] == "healthy", gateway
    assert ai["status"] == "healthy", ai
    assert '<div id="root"></div>' in web
    assert "setup_required" in dashboard

    print("smoke_ok=true")
    print(f"dashboard_setup_required={dashboard['setup_required']}")

if __name__ == "__main__":
    main()
```

## How To Think About Idempotency

Idempotency means a script can run more than once without causing accidental duplicate damage. This is one of the most important automation concepts.

Creating a directory with `mkdir -p` is idempotent. Running it twice is fine. Appending the same line to a config file every time is not idempotent. Running a database migration system that records applied migrations is usually idempotent. Running raw `CREATE TABLE` without `IF NOT EXISTS` may not be.

The instinct you want is this: before writing a script that changes anything, ask what happens on the second run. If the second run breaks something, creates duplicates, or hides a mistake, the script is not safe enough yet.

### Lesson Task

Write an idempotent local setup check that creates local folders only if needed, validates required files, and refuses to continue if it would need secrets.

### Commands To Practice Before The Script

Create a directory safely:

```bash
mkdir -p backups/postgres
```

`mkdir` creates directories. `-p` means create parents as needed and do not fail if the directory already exists. This is idempotent.

Check for a file:

```bash
[[ -f docker-compose.dev.yml ]] && echo "exists"
```

`[[ -f FILE ]]` succeeds only if the path exists and is a regular file. This is better than trying to use the file and failing later.

Exit with an error:

```bash
echo "missing file" >&2
exit 1
```

`>&2` sends output to stderr. `exit 1` stops the script with failure. Use this when continuing would produce nonsense.

### Bash Script

```bash
#!/usr/bin/env bash
# Run with Bash.

set -Eeuo pipefail
# Strict mode.

required_files=(
# Bash array of files that prove we are in the expected project.

  "docker-compose.dev.yml"
  "docker-compose.yml"
  "services/gateway/main.go"
  "services/ai/main.py"
  "apps/web/package.json"
)
# End array.

mkdir -p .codex-cache backups/postgres tmp
# Create local working directories if missing.
# -p makes this safe to run repeatedly.

for file in "${required_files[@]}"; do
# Loop through required files.

  if [[ ! -f "$file" ]]; then
# ! negates the test.
# -f checks for a regular file.

    echo "missing required file: $file" >&2
# Print error to stderr.

    exit 1
# Stop with failure.

  fi
# End if.

done
# End loop.

if [[ -f ".env" ]]; then
# Check whether a local .env file exists.

  echo ".env exists locally; not printing it"
# Never print local secrets.

else
# If no .env:

  echo ".env missing; that is okay for container dev, but real Shopify OAuth needs secrets later"
# Explain what missing means.

fi
# End if.

echo "idempotent_setup_check=ok"
# Final success marker.
```

### Python Script

```python
#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

REQUIRED = [
    Path("docker-compose.dev.yml"),
    Path("docker-compose.yml"),
    Path("services/gateway/main.go"),
    Path("services/ai/main.py"),
    Path("apps/web/package.json"),
]

def main() -> None:
    for directory in [Path(".codex-cache"), Path("backups/postgres"), Path("tmp")]:
        directory.mkdir(parents=True, exist_ok=True)

    missing = [str(path) for path in REQUIRED if not path.is_file()]
    if missing:
        raise SystemExit(f"missing required files: {missing}")

    env_state = "present_not_printed" if Path(".env").exists() else "missing"
    print("idempotent_setup_check=ok")
    print(f"env_state={env_state}")

if __name__ == "__main__":
    main()
```

## How To Think About Safe Cleanup

Cleanup scripts are dangerous because they often delete things. The best cleanup script starts by measuring. How much disk is used? Which Docker objects are dangling? Which logs are huge? Which build artifacts are safe to remove? Never jump straight to `rm`.

Your rule should be: first make cleanup report-only, then make it explicit, then make destructive mode opt-in. A script that deletes by default is not a professional script. It is a future incident.

### Lesson Task

Write a cleanup inspector that shows Docker disk usage and large local files without deleting anything. Only add delete behavior after you understand the output.

### Commands To Practice Before The Script

Show Docker disk use:

```bash
docker system df
```

This tells you how much space images, containers, local volumes, and build cache are using. It does not delete anything.

Find large files:

```bash
find . -type f -printf '%s %p\n' | sort -nr | head
```

`-printf '%s %p\n'` prints file size and path. `sort -nr` sorts numerically in reverse order, so biggest files come first. `head` keeps the output short.

### Bash Script

```bash
#!/usr/bin/env bash
# Run with Bash.

set -Eeuo pipefail
# Strict mode.

echo "== docker disk usage =="
docker system df || true
# Show Docker disk usage.
# || true means do not fail if Docker is unavailable.

echo
echo "== largest files under repo, excluding common dependency caches =="
find . -type f \
# Find files under the current repo.

  -not -path './.git/*' \
# Exclude Git internals.

  -not -path './node_modules/*' \
# Exclude root node_modules.

  -not -path '*/node_modules/*' \
# Exclude nested node_modules.

  -not -path '*/.venv/*' \
# Exclude Python virtualenvs.

  -printf '%s %p\n' \
# Print size in bytes, then path.

  | sort -nr \
# Sort numerically, largest first.

  | head -40 \
# Keep only top 40.

  | awk '{ size=$1; $1=""; printf "%.2f MB %s\n", size/1024/1024, $0 }'
# awk reformats bytes into MB.

echo
echo "report_only=true"
# Make it explicit that this script did not delete anything.
```

### Python Script

```python
#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

SKIP_PARTS = {".git", "node_modules", ".venv", "__pycache__"}

def should_skip(path: Path) -> bool:
    return any(part in SKIP_PARTS for part in path.parts)

def main() -> None:
    files: list[tuple[int, Path]] = []

    for root, dirs, names in os.walk("."):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if d not in SKIP_PARTS]
        for name in names:
            path = root_path / name
            if should_skip(path):
                continue
            try:
                files.append((path.stat().st_size, path))
            except OSError:
                continue

    for size, path in sorted(files, reverse=True)[:40]:
        print(f"{size / 1024 / 1024:.2f} MB {path}")

    print("report_only=true")

if __name__ == "__main__":
    main()
```

## How To Think About Automation That Changes Code

Infrastructure scripts sometimes change files. That is when discipline matters most. A script that edits config should create a backup, check whether the desired change already exists, edit the smallest possible target, and show a diff. If it cannot explain what it changed, it is too risky.

In this repo, docs and code are mixed with user learning files. That means automation should respect boundaries. A script should never wander into `Explanations_TO_EVERYTHING.md` or broad learning folders unless the task explicitly allows it.

The intuition is that file-changing automation should behave like a careful engineer: read first, change narrowly, validate, then explain.

### Lesson Task

Write a script that checks whether a file contains a required line and adds it only once. This teaches safe, idempotent file edits.

### Commands To Practice Before The Script

Search for an exact line:

```bash
grep -Fxq "some exact line" file.txt
```

`-F` means fixed string, not regex. `-x` means match the whole line. `-q` means quiet. Together, this is perfect for "is this exact config line already present?"

Copy a backup:

```bash
cp file.txt file.txt.bak
```

Before a script edits a file, make a backup. This is not a replacement for Git, but it is a useful local safety net.

Append a line:

```bash
printf '\n%s\n' "new line" >> file.txt
```

`>>` appends instead of overwriting. `printf` gives predictable formatting.

### Bash Script

```bash
#!/usr/bin/env bash
# Run with Bash.

set -Eeuo pipefail
# Strict mode.

file="${1:?usage: script FILE LINE}"
# Read first argument into file.
# :? means if missing, print the message and exit.

line="${2:?usage: script FILE LINE}"
# Read second argument into line.

if [[ ! -f "$file" ]]; then
# If the target file does not exist:

  echo "file does not exist: $file" >&2
# Print error to stderr.

  exit 1
# Stop.

fi
# End if.

if grep -Fxq "$line" "$file"; then
# Search for the exact full line.
# -F fixed string, -x full line, -q quiet.

  echo "line already present"
# Nothing to change. This is idempotency.

else
# If line is missing:

  cp "$file" "$file.bak"
# Create a backup next to the file.

  printf '\n%s\n' "$line" >> "$file"
# Append a blank line and then the new line.
# >> appends; it does not overwrite.

  echo "line added; backup written to $file.bak"
# Report what changed.

fi
# End if.

git diff -- "$file" || true
# Show the diff for review.
# || true keeps the script from failing if not in Git.
```

### Python Script

```python
#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: script FILE LINE")

    path = Path(sys.argv[1])
    line = sys.argv[2]

    if not path.is_file():
        raise SystemExit(f"file does not exist: {path}")

    text = path.read_text()
    if line in text.splitlines():
        print("line already present")
        return

    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)
    path.write_text(text.rstrip() + "\n\n" + line + "\n")
    print(f"line added; backup written to {backup}")

    subprocess.run(["git", "diff", "--", str(path)], check=False)

if __name__ == "__main__":
    main()
```

## How To Think About Scheduling

A script becomes operations when it runs on a schedule. Cron and systemd timers are the classic Linux tools. Cron is simple. Systemd timers are more observable. In production-like Linux, systemd timers are often better because you can check logs with `journalctl`, see the unit status, and define dependencies.

The intuition is that scheduled automation must be quieter and safer than manual automation. It cannot ask questions. It cannot depend on your shell being open. It must know its working directory. It must write logs. It must fail loudly enough that someone notices.

### Lesson Task

Turn the smoke test into a scheduled health check. Start with a systemd user timer on your local Linux machine, not production.

### Commands To Practice Before The Unit Files

Check whether user systemd is available:

```bash
systemctl --user status
```

`systemctl` controls systemd. `--user` means use your user's systemd manager instead of the machine-wide root manager. Start with user timers because they are safer while learning.

Reload unit files:

```bash
systemctl --user daemon-reload
```

Systemd does not automatically reread unit files every time you edit them. `daemon-reload` tells it to reload definitions.

Enable and start a timer:

```bash
systemctl --user enable --now nexusos-smoke.timer
```

`enable` means start this timer automatically in future user sessions. `--now` means also start it immediately. Without `--now`, it may be enabled but not currently active.

List timers:

```bash
systemctl --user list-timers
```

This shows scheduled timers, when they last ran, and when they will run next.

Read logs for a user service:

```bash
journalctl --user -u nexusos-smoke.service -n 80
```

`journalctl` reads systemd logs. `--user` reads user-unit logs. `-u` chooses one unit. `-n 80` shows the last 80 lines.

### Bash Unit Files

This is a service unit. It defines what runs.

```ini
[Unit]
# [Unit] contains metadata and dependency info.

Description=NexusOS local smoke check
# Human-readable description.

[Service]
# [Service] describes the process systemd should run.

Type=oneshot
# oneshot means run the command once and then consider the service finished.

WorkingDirectory=/home/iscjmz/shopify/shopify
# The directory systemd should cd into before running ExecStart.
# This matters because scripts often use relative paths.

ExecStart=/usr/bin/env bash scripts/smoke_check.sh
# The command to run.
# /usr/bin/env bash finds bash through PATH.
# scripts/smoke_check.sh is relative to WorkingDirectory.
```

This is a timer unit. It defines when the service runs.

```ini
[Unit]
# Metadata section for the timer.

Description=Run NexusOS local smoke check every 15 minutes
# Human-readable timer description.

[Timer]
# [Timer] defines schedule behavior.

OnBootSec=2min
# First run happens two minutes after the user manager starts.

OnUnitActiveSec=15min
# Run again 15 minutes after the previous activation.

Persistent=true
# If the machine was off during a scheduled run, run once when it comes back.

[Install]
# [Install] defines how enable links this timer into systemd startup targets.

WantedBy=timers.target
# timers.target is the normal target for enabled timers.
```

To install manually, place the first file at `~/.config/systemd/user/nexusos-smoke.service`, place the second at `~/.config/systemd/user/nexusos-smoke.timer`, then run:

```bash
systemctl --user daemon-reload
systemctl --user enable --now nexusos-smoke.timer
systemctl --user list-timers
journalctl --user -u nexusos-smoke.service -n 80
```

### Python Scheduler Alternative

Use this only for learning or a dev helper. For real Linux scheduling, prefer systemd timers.

```python
#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import time

INTERVAL_SECONDS = 15 * 60

def run_once() -> None:
    completed = subprocess.run(
        ["bash", "scripts/smoke_check.sh"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(completed.stdout)
    if completed.returncode != 0:
        print(f"smoke check failed with code {completed.returncode}")

def main() -> None:
    while True:
        run_once()
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
```

## How To Think About CI And Repeatability

CI is automation on a clean machine. That is why CI catches lies your laptop tells you. Your laptop may have old dependencies, cached Docker images, local env files, or running services. CI starts closer to zero.

The intuition is that every serious project needs one command that proves the important parts. Not every check has to run every time. But there should be a clear ladder: fast check, service check, full check.

For this project, a good fast check is Compose config validation, gateway Go tests, frontend typecheck, and AI import validation. A service check starts the stack and hits health endpoints. A full check includes Shopify OAuth/webhook flows once real credentials exist.

### Lesson Task

Create a single local verification script that a future AI or human can run before claiming the project works.

### Commands To Practice Before The Script

Run Go tests inside a clean container:

```bash
docker run --rm -v "$PWD/services/gateway:/workspace" -w /workspace golang:1.22-bookworm go test ./...
```

`docker run` starts a one-off container. `--rm` removes it after it exits. `-v host:container` mounts local code into the container. `-w /workspace` sets the working directory. This avoids relying on the host Go install.

Run frontend typecheck inside Node:

```bash
docker run --rm -v "$PWD/apps/web:/workspace" -w /workspace node:20-bookworm-slim sh -lc 'npm ci --no-audit --no-fund && npm run typecheck'
```

`sh -lc` runs a shell command inside the container. `npm ci` installs from lockfile. `&&` means run typecheck only if install succeeded.

### Bash Script

```bash
#!/usr/bin/env bash
# Run with Bash.

set -Eeuo pipefail
# Strict mode.

echo "== compose config =="
docker compose -f docker-compose.dev.yml config --quiet
# Validate Compose config.

echo
echo "== gateway tests =="
docker run --rm \
# Start a temporary container and remove it after completion.

  -v "$PWD/services/gateway:/workspace" \
# Mount local gateway service into /workspace inside the container.

  -w /workspace \
# Set container working directory.

  golang:1.22-bookworm \
# Use this Go image.

  go test ./...
# Run all Go tests.

echo
echo "== frontend typecheck =="
docker run --rm \
  -v "$PWD/apps/web:/workspace" \
  -w /workspace \
  node:20-bookworm-slim \
  sh -lc 'npm ci --no-audit --no-fund && npm run typecheck'
# Use a Node container.
# npm ci installs exact lockfile dependencies.
# && runs typecheck only if install succeeds.

echo
echo "== ai import check =="
docker compose -f docker-compose.dev.yml exec -T ai python - <<'PY'
# Execute Python inside the running AI service container.
# -T disables TTY.
# <<'PY' starts a heredoc. The quoted marker prevents shell expansion inside it.

from agents.crew import ShopifyRefundTool, CheckInventoryTool
print(ShopifyRefundTool().name)
print(CheckInventoryTool().name)
PY
# End heredoc.

echo
echo "verify_ok=true"
# Final success marker.
```

### Python Script

```python
#!/usr/bin/env python3
from __future__ import annotations

import subprocess

COMMANDS = [
    ["docker", "compose", "-f", "docker-compose.dev.yml", "config", "--quiet"],
    ["docker", "run", "--rm", "-v", "$PWD/services/gateway:/workspace", "-w", "/workspace", "golang:1.22-bookworm", "go", "test", "./..."],
]

def run_shell(label: str, command: str) -> None:
    print(f"== {label} ==")
    subprocess.run(command, shell=True, check=True)

def main() -> None:
    run_shell("compose config", "docker compose -f docker-compose.dev.yml config --quiet")
    run_shell(
        "gateway tests",
        'docker run --rm -v "$PWD/services/gateway:/workspace" -w /workspace golang:1.22-bookworm go test ./...',
    )
    run_shell(
        "frontend typecheck",
        'docker run --rm -v "$PWD/apps/web:/workspace" -w /workspace node:20-bookworm-slim sh -lc "npm ci --no-audit --no-fund && npm run typecheck"',
    )
    run_shell(
        "ai import check",
        "docker compose -f docker-compose.dev.yml exec -T ai python -c \"from agents.crew import ShopifyRefundTool; print(ShopifyRefundTool().name)\"",
    )
    print("verify_ok=true")

if __name__ == "__main__":
    main()
```

## The Master Intuition Loop

Every infrastructure task follows the same loop.

First, observe. Read files. Check ports. Check Docker. Check logs. Check status. Check health endpoints. Do not change anything yet.

Second, form a small hypothesis. Not "the app is broken." That is too vague. Say "the gateway cannot connect to Postgres because the container is using the wrong hostname" or "Qdrant is healthy internally but Compose marks it unhealthy because the healthcheck command is missing from the image."

Third, make the smallest safe change. Edit one config. Restart one service. Hit one endpoint. Avoid broad rewrites.

Fourth, verify with independent evidence. If Docker says a container is up, hit the HTTP endpoint. If logs say a database connected, run a query or health endpoint. If a migration ran, check the migrations table or schema.

Fifth, document the new truth. A future engineer should not have to rediscover the same thing. That is why `AGENTS.md` matters. That is why operational docs matter. Documentation is not schoolwork. It is saved debugging time.

Your job when becoming dangerous in infrastructure is to become calm. Calm does not mean slow. Calm means you know which layer you are inspecting, which command proves the next fact, and which files are safe to touch. Once you think this way, Bash and Python become tools in your hand instead of magic spells.

## Capstone Task

Your capstone is to build a local `scripts/platform_doctor.sh` and `scripts/platform_doctor.py` for this repo.

The doctor should inspect repo entrypoints, check Linux resources, validate Docker Compose, show service status, hit web/gateway/AI health endpoints, report dashboard setup state, scan recent logs for high-signal failures, and exit nonzero only when the platform cannot be used.

Do not make it delete anything. Do not make it print secrets. Do not make it silently fix things yet. A doctor diagnoses first. A repair script comes later.

When you can build that doctor, you are no longer just running commands. You are turning infrastructure intuition into repeatable operational leverage.
