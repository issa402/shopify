# Likely Tooling Map

This file is intentionally labeled "likely."

From the job posting alone, we can infer tool categories and common platform families.
We should not pretend we know Future Standard's exact internal stack unless they state it directly.

## Very Likely Tool Categories

### Operating systems

Because the role explicitly mentions both environments:
- Ubuntu or other Linux servers
- Windows endpoints and/or Windows Server systems

### Cloud and hybrid

Because the role explicitly names both:
- AWS
- Azure

That usually also implies some comfort with:
- IAM and role-based access
- cloud networking
- secrets handling
- monitoring
- managed compute/storage services

### Scripting and automation

Because the role explicitly names them:
- Bash
- Python
- PowerShell

### Security tooling categories

Because the role mentions antivirus, IDS/IPS, endpoint protection, and secure configuration:
- firewall platforms
- endpoint protection/EDR
- vulnerability or patching tools
- identity/access tooling
- logging or security event review tools

Common examples in many companies:
- Microsoft Defender
- CrowdStrike
- SentinelOne
- Palo Alto
- Fortinet
- Microsoft Entra ID

These are examples, not claims about their exact stack.

### Network and infrastructure services

Because the role mentions protocols, troubleshooting, and segmentation:
- DNS
- VPN
- VLAN or subnet segmentation
- firewalls
- switching/routing concepts
- reverse proxy or load balancing

### Documentation and project tracking

Because the posting mentions agile, collaboration, tracking, and documentation:
- Jira or similar issue tracking
- Confluence or other internal documentation tools
- GitHub or Git-based version control and automation

## Best Way To Use This File

Do not memorize vendor names first.
Instead, learn the function each category serves.

Examples:
- identity platform: who are you and what can you access
- endpoint protection: is this device or server behaving maliciously
- firewall: what traffic is allowed
- secrets manager: where sensitive config should live
- project tracker: how delivery and priority are communicated

## What You Should Be Ready To Say In An Interview

You want answers like:
- "I have hands-on Linux experience and I’m comfortable translating the same operational thinking into Windows and PowerShell."
- "I understand AWS and Azure fundamentals and can map workloads across compute, storage, network, identity, and observability concerns."
- "I think in terms of access boundaries, failure modes, secure defaults, and operational visibility."

That is stronger than trying to bluff exact tool names.
