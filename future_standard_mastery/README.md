# Future Standard Mastery

This folder is not supposed to be a loose set of notes.
It is supposed to train you for the exact kind of work this role is describing.

So the right way to read this folder is:

1. First understand what the domain means in real infrastructure work.
2. Then understand what that domain would look like at Future Standard.
3. Then learn the concepts and tools you need before touching anything.
4. Then do a Pokemon lab that imitates the same kind of work.
5. Then write down what you learned like an engineer, not like a student copying commands.

That is the structure I am using now.

## What The Job Is Actually Asking For

The posting is broad, but the work is not random.
It breaks into a few big buckets:

- run systems reliably
- understand dependencies and failure modes
- automate repetitive operational work
- work across Linux, Windows, cloud, networking, and security boundaries
- support business platforms used by real people
- document changes, explain tradeoffs, and help teammates

This means the role is not "just coding" and not "just cloud."
It is infrastructure ownership.

## How To Work Through These Docs

Each folder should answer five questions:

### 1. What is this domain?

Not the buzzword version.
The real-world version.

Example:
"System administration" is not learning random Linux commands.
It is knowing how to inspect a host, understand what is running, determine what is broken, and change the machine safely.

### 2. What would I actually do in this domain at Future Standard?

This is where we translate the role into day-to-day work.

Example:
If a team says, "users cannot access an internal platform," that could involve:
- system administration
- networking
- access control
- observability
- documentation

So you need to see how the domains connect.

### 3. What must I understand before I do a task?

Every task in these folders now has a "learn first" section.
That is where you slow down and make sure you understand the mental model.

### 4. What is the exact task?

You asked for concrete work, not just bullet points.
So each section gives explicit Pokemon-project tasks that simulate the same type of thinking you would need on a real infrastructure team.

### 5. How do I prove I actually learned it?

For every task, you should collect evidence:
- commands run
- outputs that mattered
- files you inspected
- what failed
- what changed
- what you would improve next

That is what turns repo work into job-ready experience.

## The Correct Order

Do these in order:

1. [00_master_path/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/00_master_path/README.md)
2. [00_master_path/LIKELY_TOOLING_MAP.md](/home/iscjmz/shopify/shopify/future_standard_mastery/00_master_path/LIKELY_TOOLING_MAP.md)
3. [01_system_administration_linux/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/01_system_administration_linux/README.md)
4. [02_servers_compute_storage/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/02_servers_compute_storage/README.md)
5. [03_networking/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/03_networking/README.md)
6. [04_cloud_hybrid_platforms/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/04_cloud_hybrid_platforms/README.md)
7. [05_windows_workplace/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/05_windows_workplace/README.md)
8. [06_cybersecurity/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/06_cybersecurity/README.md)
9. [07_scripting_programming_data_analysis/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/07_scripting_programming_data_analysis/README.md)
10. [08_operations_observability_troubleshooting/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/08_operations_observability_troubleshooting/README.md)
11. [09_delivery_documentation_collaboration/README.md](/home/iscjmz/shopify/shopify/future_standard_mastery/09_delivery_documentation_collaboration/README.md)

## How These Folders Connect To The Existing Infra Tasks File

[infra/FUTURE_STANDARD_INFRA_TASKS.md](/home/iscjmz/shopify/shopify/infra/FUTURE_STANDARD_INFRA_TASKS.md) is still useful.
Think of it as the operational backlog.

This `future_standard_mastery/` folder is the teaching layer.

The relationship is:
- `infra/FUTURE_STANDARD_INFRA_TASKS.md` tells you what to build or review
- `future_standard_mastery/` teaches you how to think about it and what to learn first

## Important Answer: Do You Need Pandas?

Short answer:
- probably not as a strict requirement from the wording alone
- still very worth learning

Why:
The posting says you should be able to:
- automate tasks
- analyze data
- support infrastructure operations

For infrastructure work, that usually means:
- reading JSON and CSV outputs
- summarizing log exports
- analyzing queue depth or latency samples
- creating operational reports
- turning messy data into clear decisions

That does not require `pandas` for every task.
But `pandas` is a strong tool for that kind of work.

So your priority should be:
1. strong Bash basics
2. strong Python basics
3. Python HTTP/files/JSON/CSV/reporting
4. enough `pandas` to analyze operational data cleanly

That is the right answer for this role.

## What “Good” Looks Like By The End

By the time you finish this folder properly, you should be able to say:

- I can explain how the Pokemon system actually runs.
- I can explain what depends on what.
- I can inspect Linux systems and find useful evidence quickly.
- I can reason about network paths and access boundaries.
- I can map local systems to AWS and Azure concepts.
- I can identify weak security defaults.
- I can automate checks and reports with Bash and Python.
- I can investigate failures using logs, health checks, and dependencies.
- I can write runbooks, change proposals, and architecture notes another engineer could actually use.

That is the kind of preparation that matches this role.
