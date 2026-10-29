# prompt-patterns.md — the six templates

Copy-pasteable prompts for each pattern. Replace `{{...}}` placeholders. These are starting
points — adapt the wording to the task; the *shape* is what matters.

---

## 1. Blind-spot pass
**For:** unknown unknowns — you're new to this codebase or domain.

```
I'm working on {{task}} in this codebase, and I know little about how {{area/subsystem}}
works here. Do a blind-spot pass: read the relevant code and help me figure out my
unknown-unknowns — the decisions and constraints this task touches that I haven't mentioned.
Then suggest how I should prompt you to do this well. Don't start implementing.
```

Domain variant (learning a new field, not just a new repo): replace "in this codebase" with the
field, e.g. "I'm about to do {{color grading / payments / auth}} and know nothing about it — do a
blind-spot pass on what I'd need to decide."

---

## 2. Brainstorm & prototype
**For:** aesthetic / "know it when I see it" decisions you can't specify in words.
**Skip if:** the task's unknowns are data-model or behavioral, not visual.

```
I need {{a dashboard / landing page / component}} and I have no fixed visual taste here.
Make me a single HTML page showing {{3–4}} wildly different design directions side by side,
so I can react to them instead of specifying up front. Make them genuinely distinct, not
variations on one idea.
```

Then react: pick one, or splice ("the layout of A with the type of C"), and feed that back as the spec.

---

## 3. Interview me
**For:** under-specified requirements.

```
Interview me about {{task}} before we build it. Here's context: {{who I am / the stage /
constraints / what exists}}. Ask me questions one or a few at a time, and prioritize
questions whose answers would change the architecture. Keep going until the important
ambiguities are resolved.
```

The architecture-priority instruction is the key line — it stops the interview from burning turns on cosmetics.

---

## 4. Reference — give it another map
**For:** when pointing at an example is easier than writing a spec.
**Skip if:** you have no reference (code, system, or mockup) to point at — but offer it, since an
analogous feature often exists somewhere worth naming.

```
Instead of a written spec, use this as the map for what I want: {{path/URL to reference code,
another system, or an HTML mockup}}. Read it, understand the intent behind it, and use it as
the starting point for {{task}} — adapting it to this codebase / language. Tell me where the
reference doesn't map cleanly onto what we have.
```

The reference can be in a different language or system — you're transferring intent, not copying code.

---

## 5. Implementation notes
**For:** deviations that only appear once the agent is actually building. Inject this into the
**main build run**, not a scouting pass.

```
As you implement {{task}}: whenever you hit a decision the spec doesn't cover, or you deviate
from what I asked, log it — a short "IMPLEMENTATION NOTE: {{what}} — {{why}}" — before you
continue. I want a visible trail of every point where you left the plan.
```

Afterward, read the notes: each one is a place the territory differed from your map.

---

## 6. Quiz me
**For:** making sure *you* understand the result well enough to own it.

```
Quiz me on what you just built for {{task}}: the key decisions, how the main pieces fit, and
anything I'd need to defend in review. Ask one question at a time and tell me when I'm wrong.
```

Use before opening/approving the PR — if you can't answer, you're not really in the loop yet.

---

## Consolidation template
After running the chosen patterns, ask for one summary:

```
Consolidate everything we surfaced into: (1) an Unknowns list — open questions and blind spots;
(2) Architecture-shaping answers we've now settled; (3) a single logging instruction I can paste
into the main run so mid-build deviations keep surfacing. Then stop — I'll kick off the real build.
```
