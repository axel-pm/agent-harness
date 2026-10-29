---
name: video-essence
description: Watch a reference video, capture its transferable essence (visual style, motion, pacing, structure, tone, signature technique), and apply that essence to a DIFFERENT context — a new video topic, a landing page, a slide deck, a proposal, an animation. Use when the user wants to "capture the essence/vibe of this video and apply it to X", "make my X in the style of this reference", "recreate this video's feel for a different topic", "extract the style/structure from this clip", or turn a reference into a portable design system. Watches locally and free (no API), and transfers style, not content — never copies the source's substance.
---

# video-essence

Take a reference video, distil **what makes it feel the way it does**, and reapply that to something new. The output is not a copy of the video — it's the video's *essence* (style, motion, structure, tone, technique) captured as a portable spec, then translated into a target medium you choose.

Watching is local and free: `scripts/watch.py` (PyAV + faster-whisper) yields keyframes + a contact sheet + a transcript. See `references/watching.md`.

> **Placeholders:** `<this-skill>` = this skill's own directory (where this SKILL.md lives). `<file-or-URL>` = the reference video. `<portfolio>` = the folder that holds your shared `tools/` dir (the parent of your projects on this setup).

## Prerequisites (one-time per machine, usually already done)

`watch.py` **self-locates and runs under the shared toolchain venv** — no activation, plain `python3` is fine (it re-execs into the venv it finds via `$VIDEO_WATCH_TOOLS` or a `tools/venv` up the tree). You normally do **nothing** here. Only if `watch.py` reports the toolchain is missing (fresh machine) do you install it once:

```sh
bash <portfolio>/tools/install-tools.sh   # venv: av, Pillow, faster-whisper, yt-dlp
```

First transcription downloads the Whisper `base` model (~150 MB), cached after.

## Workflow

### 1. Watch — send an agent
Run watching **in a subagent** (Agent tool) so the frames stay out of the main context:

```sh
python3 <this-skill>/scripts/watch.py "<file-or-URL>" --max-frames 24 --out <a-scratch-dir>
```

The subagent Reads the contact sheet, then the frames that carry the look/motion, plus the transcript, and returns the **essence spec** (next step) — not the raw frames. **Because the subagent produces the spec, hand it the two references it needs** — `essence-spec-template.md` and `essence-dimensions.md` — inline in its prompt (it won't have read them). For style work, err toward more frames (`--max-frames 24–30`) to capture transitions and pacing — but note `--max-frames` is a **cap**: scene mode returns fewer when the video has few distinct scenes (a 6-card explainer yields ~6 frames), which is correct, not a failure. The parent may Read the single **contact sheet** for its own grounding before the fidelity check — that's cheap and fine; just don't pull all frames into the main context.

### 2. Extract the essence
Fill `references/essence-spec-template.md`, working across the dimensions in `references/essence-dimensions.md`: **visual style**, **motion & pacing**, **structure & beats**, **tone & voice**, **signature technique**, **audio/music**. For each observation, record **provenance** (the frame timestamps or transcript span that evidenced it). Mark dimensions **N/A** where they don't apply — a title-card montage has no "voice," a silent screencast has no music. The spec is the deliverable of this stage: portable, source-anchored, reusable.

### 3. Choose the target context
Ask (or confirm) **what you're applying the essence to** — it changes everything downstream. A new *video* keeps motion/pacing; a *landing page* translates motion into scroll/transition feel and structure into section rhythm; a *deck* maps beats to slides; a *proposal/doc* borrows structure + tone but drops literal motion. See `references/apply-playbook.md` for per-medium translation.

### 4. Apply — transfer style, not substance
Produce the target artifact (or a precise build spec if another tool renders it), honoring the essence spec dimension by dimension. **Guardrail:** transfer the *feel*, never the source's actual content, script, footage, or copyrighted assets. If the new context has a house style (e.g. a brand's tokens), reconcile — essence guides, brand governs.

### 5. Check fidelity
Go back through the essence spec dimension by dimension and state, for each, **match / adapted / dropped** and why. Deliberate divergence for the new context is good; unnoticed drift is not. Surface the comparison so the user can judge the transfer.

## Guardrails
- Public / owner-shared references only. Essence transfer ≠ reproducing the source.
- Don't lift the reference's words, brand marks, or footage — recreate the *quality*, originate the *content*.
- Respect the target's own design system if it has one; essence is direction, not override.

## Files
- `scripts/watch.py` — the watch engine (shared with `video-to-skill`).
- `references/watching.md` — engine options + how to read a digest.
- `references/essence-dimensions.md` — the taxonomy + how to read each dimension from frames/transcript.
- `references/essence-spec-template.md` — the portable spec to fill.
- `references/apply-playbook.md` — translating essence per target medium (video / web / slides / doc / animation).
