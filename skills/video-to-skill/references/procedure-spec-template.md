# procedure-spec-template.md

The structured breakdown to produce from a watched how-to video, before authoring any skill.
Fill every section; write "N/A" where the video genuinely doesn't cover it (and note the gap).

```md
# Procedure: <the capability the video teaches, as a verb phrase>

## Goal
One or two sentences: what someone can DO after this that they couldn't before.

## Prerequisites
- Tools / accounts / files that must exist first (versions if shown).
- Assumed starting state.

## Inputs → Outputs
- Input(s): what you start with.
- Output(s): what you end with (files created, state changed, artifact produced).

## Steps
Ordered, imperative, each independently checkable. For each step capture:
1. **<action>** — what to do.
   - exact command / UI action / keystroke shown  (quote it verbatim; cite frame @ T.Ts)
   - expected result / how you know it worked
   - evidence: frame #N @ T.Ts  and/or transcript [start–end]

## Decision points
Where the procedure branches ("if X then …"). State the condition and each path.

## Gotchas
Mistakes the video warns about, easy-to-miss details, ordering that matters, things that
look optional but aren't.

## Uncertain / inferred
Anything you concluded rather than saw stated — flag it so the skill author can verify.
```

## Reading tips
- **Exact syntax** (commands, filenames, flags) → read the **frame**, not the transcript (Whisper mangles code).
- **Intent / rationale** → the **transcript**.
- If a step's evidence is only narration with no supporting frame, mark it inferred.
