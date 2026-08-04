# 05 Windows Workplace

You are on Ubuntu, but the job explicitly wants comfort in both Windows and Linux environments.

So this section teaches you how to think across both, not how to pretend they are the same.

## What This Domain Means

Workplace and Windows-oriented infrastructure work often includes:

- user endpoints
- device health
- patching
- software deployment
- scheduled tasks
- basic service management
- event log review
- identity and access integration

This does not mean the whole role is help desk work.
It means the infrastructure team likely supports the broader environment people actually use.

## What This Would Look Like At Future Standard

Examples:

- helping troubleshoot why a Windows endpoint cannot reach a needed platform
- checking service state on a Windows host
- using PowerShell to automate repetitive checks
- understanding how endpoint security and central identity affect access
- working in a mixed Linux/server plus Windows/workplace environment

## Learn This First

### Linux and Windows are different, but the operational questions are similar

For both systems, you still ask:
- what is running
- what failed
- what logs prove it
- what account owns it
- what network path is involved
- what scheduled task or service behavior matters

The tools differ, but the thinking is shared.

## Translation Exercise 1: Service Management

Linux:
- `systemctl status`
- `journalctl`

Windows:
- `Get-Service`
- Services MMC
- Event Viewer

Your task:
Write a table that translates common Linux support actions into Windows equivalents.

## Translation Exercise 2: Scheduling Work

Linux:
- `cron`

Windows:
- Task Scheduler
- scheduled PowerShell script

Your task:
Explain how you would translate a recurring Pokemon health-check script from Ubuntu to Windows.

Include:
- where the script would live
- what account runs it
- where logs go
- how failure is noticed

## Translation Exercise 3: Ports And Connectivity

Linux:
- `ss -tulpn`
- `curl`

Windows:
- `netstat`
- `Test-NetConnection`
- PowerShell HTTP requests

Your task:
Create a short "same troubleshooting problem, two operating systems" guide.

### Why this section matters

Because the job is telling you directly that mixed-environment comfort matters.
You do not need to become a full Windows admin overnight.
You do need to be able to think and communicate across both worlds.
