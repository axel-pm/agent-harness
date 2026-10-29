# skill-authoring.md — how to write a good Claude Code skill

A skill is a folder with a `SKILL.md` (YAML frontmatter + Markdown body), optionally `scripts/`
and `references/`. It's loaded by its `description` and, once triggered, its body instructs the agent.

## Frontmatter
```yaml
---
name: kebab-case-capability        # matches the folder name
description: >
  What it does + explicit "use when …" triggers (the phrases a user would actually say).
  This is the ONLY thing the model sees when deciding to fire the skill — make it earn its trigger.
---
```
- `name`: lowercase, hyphenated, names the **capability** (not the source video).
- `description`: one to three sentences. Lead with the capability, then concrete trigger phrases
  ("use when the user wants to …", quoting real user language). Vague descriptions = skills that never fire.

## Body — principles
- **Action-oriented.** Tell the agent what to *do*, in order. Imperative voice.
- **Lean.** Keep `SKILL.md` scannable. Push long tables, templates, and background into `references/`
  and link to them — the agent reads a reference only when it needs it.
- **Deterministic work → scripts.** If a step is exact and repeatable, ship a script in `scripts/`
  and call it, rather than describing it in prose the model might drift from.
- **Self-contained.** Don't assume state from the video (paths, secrets, names). Parameterise.
- **State the guardrails.** Compliance, safety, "don't do X" — inline, briefly.

## The boundary rubric (one skill vs several)
Make it **one** skill when:
- the steps only make sense as a single flow, and
- there's a single trigger a user would say, and
- splitting would create fragments nobody would invoke alone.

Split into **several** when the video teaches capabilities that:
- have distinct triggers ("set up X" vs "debug X"), or
- are independently reusable, or
- would otherwise force one bloated `SKILL.md` with unrelated branches.

When in doubt, prefer **one focused skill** over a sprawling one; you can extract later.

## Structure to aim for
```
<name>/
  SKILL.md                 # triggers + the workflow, lean
  scripts/<tool>.py        # deterministic steps, each with --help
  references/<topic>.md    # depth loaded on demand
```

## Smells to avoid
- A `description` with no trigger phrases.
- A `SKILL.md` that's a wall of text with no ordered steps.
- Prose reimplementing something that should be a script.
- Hardcoded machine paths, API keys, or the demo's specific filenames.
- A skill that was never run before being called "done".
