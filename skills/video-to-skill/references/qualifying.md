# qualifying.md — is this video worth a skill?

The gate before any real work (step 1 of the skill). Authoring a skill costs effort and adds a file
that loads into every future session; a weak skill is worse than none. Spend thirty seconds here first.

Do this **cheaply**: run `watch.py --transcript-only` (talks/narrated videos) or just read the title +
description, and judge against the signals below. You don't need the full frame-by-frame watch to decide.

## PASS — worth authoring

A skill is worth it when the video teaches a **concrete, repeatable, transferable procedure** — the kind
of thing you'd want an agent to just *do* later without re-deriving it. Signals:

- It shows a **specific how-to**: setup, a workflow, a build, a fix, a configuration — with actual steps.
- The steps **generalise** beyond this one video (a real user could apply them to their own case).
- You can imagine **triggering it later** ("do the X setup", "run the Y workflow") and being glad it exists.
- The procedure is **non-obvious or easy to get wrong** — capturing it saves real time or mistakes.

## FAIL — don't author (say why, suggest a better home)

Stop and report instead of forcing a skill when the video is:

- **Opinion, commentary, or entertainment** — a talk that inspires but teaches no procedure. → Better as
  notes or a summary, not a skill.
- **A one-off** with nothing reusable — a demo of a specific dataset/account/repo that won't transfer.
- **Too trivial** — the "procedure" is a single obvious command or a menu click. A skill adds ceremony
  for no gain.
- **Already covered** — you (or the user) already have a skill for this. → Point at the existing one.
- **Not actually a procedure** — a product announcement, a keynote, a vlog. → A reference doc at most.

## When it fails

Don't quietly build a mediocre skill. Say plainly: *"This video is <reason>; it isn't a good skill
candidate. Here's what I'd do instead: <notes / reference doc / point at existing skill>."* Then stop.

## Escape hatch

If the video is **obviously** a strong how-to (a clear tutorial with clean steps), don't belabour the
gate — note "clearly a good candidate" in one line and move on to the watch. The gate is there to catch
the bad cases cheaply, not to add ceremony to the good ones.

## Worked examples

- *"Setting up Postgres row-level security with policies"* screencast → **PASS**: concrete, repeatable,
  transferable; a great `configure-postgres-rls` skill.
- *"My thoughts on the future of AI agents"* conference keynote → **FAIL** (opinion): capture 3 bullets
  of notes if useful; no skill.
- *"Deploying MY portfolio site to MY Vercel account"* walkthrough → **FAIL** (one-off): the reusable
  bits are just "vercel deploy" — too trivial and too specific.
- *"Debugging a flaky test with git bisect and reproduction harnesses"* talk → **PASS**: the *method*
  transfers even though the bug doesn't; a solid `bisect-flaky-tests` skill.
