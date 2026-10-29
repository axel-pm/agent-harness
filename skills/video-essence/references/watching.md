# watching.md — the watch engine

`scripts/watch.py` turns a video into a **digest** an agent can read. It's shared verbatim with the
`video-essence` skill.

## Run it

```sh
python3 scripts/watch.py "<file-or-URL>" [options]
```

- A local path is used directly. A URL (YouTube etc.) is downloaded with `yt-dlp` (≤720p) to a temp dir.
- **Output lands in a temp dir** named `<stem>-watch/` (the script prints the absolute `out_dir`). It does **not** write into the current directory, so running from inside a repo won't litter it. Override with `--out DIR`.

## No setup / activation needed
`watch.py` **self-locates the shared toolchain** and re-execs itself under that venv — you never activate anything, and running it with a plain `python3` is fine. It searches, in order: `$VIDEO_WATCH_TOOLS/venv`, then a `tools/venv` found by walking up from the current directory (or from the script), then `~/.video-watch-tools/venv`. Only if none exists (e.g. a fresh machine) does it stop and print the one-time install command. So the "Prerequisites" install step is a **one-time-per-machine** thing, not something to run each time.

## Options

| Flag | Default | Meaning |
|---|---|---|
| `--mode scene\|uniform\|interval` | `scene` | `scene` keeps the most visually-distinct moments; `uniform` samples evenly; `interval` = one frame every `--every` s |
| `--max-frames N` | `20` | cap on frames kept (scene/uniform) |
| `--every SEC` | — | spacing for `interval` mode |
| `--whisper-model` | `base` | `tiny\|base\|small\|medium\|large-v3` — bigger = more accurate, slower |
| `--lang xx` | auto | force a transcript language (e.g. `en`) |
| `--frames-only` (`--no-transcribe`) | off | skip transcription — frames + contact sheet only |
| `--transcript-only` (`--no-frames`) | off | skip frame extraction — transcript only |
| `--quiet` | off | suppress progress on stderr |

> **Capture modes:** default gives both frames and a transcript. For *essence* work the signal is usually
> visual, so `--frames-only` is the common override (skips the Whisper model, faster). `--transcript-only`
> is rarely what you want here, since it discards the visuals. Passing both is an error.

## What you get (the digest)

```
<stem>-watch/
  contact-sheet.png     ← tiled overview of all frames, each labelled "#N  T.Ts"  — READ THIS FIRST
  frames/frame-0001.png … ← full-res individual frames
  transcript.txt        ← human-readable "[start-end] text" lines
  digest.json           ← machine-readable: meta + frames[{index,path,t}] + transcript[] + full_text
```

## How to read a digest (as the watching subagent)

1. **Read `contact-sheet.png` first** — it's one image; it gives you the whole arc cheaply.
2. Read only the **individual frames you actually need** (e.g. the moment a command is typed) — they're full-res so on-screen text is legible.
3. Read `transcript.txt` for narration; cross-reference timestamps with frames.
4. Return a **compact structured summary** (the procedure spec / essence spec), never the raw frames — that's the whole point of doing this in a subagent.

## Notes
- **Scene mode returns *fewer* frames than `--max-frames` when the video has few distinct scenes** — a 6-card explainer yields ~6 frames even if you asked for 24. That's correct, not a failure; `--max-frames` is a cap, not a target. Use `--mode uniform` if you want exactly N frames regardless.
- Whisper's small models mis-hear proper nouns and commands; trust the **frames** for exact syntax and the transcript for intent.
- No audio stream, or transcription fails → the run still succeeds with `transcribed:false` and a `notes` reason; lean on frames.
- Tuning: dense talk → `--max-frames 30`; static screencast → `--mode interval --every 4`; a quick glance → `--max-frames 8`.
