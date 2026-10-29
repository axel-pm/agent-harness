# validation-checklist.md — proving an authored skill works

"Make sure the skill works" is a required step, not a nicety. Two layers:

## Layer 1 — structural (automated)
```sh
python3 scripts/validate_skill.py <path-to-new-skill>
```
Checks: valid frontmatter, kebab-case `name` matching the folder, a real `description`, a non-empty
instruction body, referenced `scripts/` & `references/` files exist, and every bundled `.py` compiles.
Fix everything it flags before Layer 2.

## Layer 2 — rehearsal (the real test)
A skill is only proven when a *fresh* agent, given only the skill, can do the task.

1. Pick a **realistic test task** the skill should handle (ideally the same thing the video did, or a
   close variant).
2. Spawn a **fresh subagent** (Agent tool) whose context contains **only**:
   - the new `SKILL.md` (+ its references/scripts), and
   - the test task.
   Do **not** feed it the video digest or your procedure spec — it must succeed from the skill alone.
3. Watch what it does. The skill passes if the subagent:
   - triggers on / follows the intended workflow,
   - produces a **correct** result,
   - without needing information the skill failed to include.
4. If it stumbles, the skill is underspecified or mis-scoped. Note exactly where it got stuck,
   revise the `SKILL.md` (add the missing step, tighten a command, split an overloaded skill),
   and rehearse again. Iterate until it passes cleanly.

## What "correct" means
Define the pass condition **before** rehearsing (a file that should exist, output that should match,
a state that should hold), then check it objectively — don't grade on "looks plausible."

## Record the result
Note in your summary: the test task, pass/fail, and any revisions made. A skill that shipped without a
recorded rehearsal should be treated as a draft.
