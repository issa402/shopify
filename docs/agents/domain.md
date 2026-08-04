# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- `CONTEXT.md` at the repo root, if it exists.
- `docs/adr/`, reading ADRs that touch the area about to be changed.

If these files do not exist, proceed silently. Do not flag their absence or create them upfront. The producer skill (`/grill-with-docs`) creates them lazily when terms or decisions get resolved.

## File structure

This repo uses the single-context layout:

```text
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-example-decision.md
│   └── 0002-example-decision.md
└── docs/agents/
```

## Use the glossary's vocabulary

When output names a domain concept in an issue title, refactor proposal, hypothesis, or test name, use the term as defined in `CONTEXT.md`. Do not drift to synonyms the glossary explicitly avoids.

If the concept is missing from the glossary, either reconsider whether the term belongs in this project or note it for `/grill-with-docs`.

## Flag ADR conflicts

If output contradicts an existing ADR, surface it explicitly rather than silently overriding it.
