## In plan mode: find the unknowns first

When operating in **plan mode**, before you call `ExitPlanMode` to present a plan, run a
**find-your-unknowns discovery pass** — surface the decisions the request never specified (the
gaps between the ask, "the map," and the actual codebase, "the territory"). Use the
`find-your-unknowns` skill; pick the patterns that fit the task rather than running all six:

- **Blind-spot pass** — enumerate unknown-unknowns when the codebase or domain is unfamiliar.
- **Interview me** — for under-specified requirements; prioritize questions that would change the architecture.
- **Reference — give it another map** — when an example (code/mockup) is easier than a spec.
- **Brainstorm & prototype** — for aesthetic / "know-it-when-I-see-it" choices.

Then **fold the surfaced unknowns and their resolutions into the plan**, and include the
**implementation-notes logging instruction** so mid-build deviations keep surfacing during the run.

**Skip** this when the task is small and fully specified — don't add ceremony to a trivial plan.

> A non-blocking `PreToolUse` hook on `ExitPlanMode` (`~/.claude/hooks/plan-mode-unknowns-nudge.sh`)
> reminds you of this at plan-presentation time; it never blocks. The real work happens here, before
> the plan is formed.
