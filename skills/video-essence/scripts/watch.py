#!/usr/bin/env python3
"""
watch.py — the shared "watch a video" engine for the video-to-skill / video-essence skills.

Turns a local video file OR a URL into a digest an agent can read:
  - keyframes (PNG) + a labelled contact sheet   (visual understanding)
  - a transcript with timestamps                 (spoken/narrated understanding)
  - digest.json tying it together

Fully local + free: PyAV for frames/audio, faster-whisper for transcription, yt-dlp for URLs.
No ffmpeg binary, no torch, no API keys.

The heavy deps live in a portable venv (see tools/install-tools.sh). This script self-bootstraps
into that venv: run it with any python3 and it re-execs under the venv python it finds via
  1) $VIDEO_WATCH_TOOLS/venv   2) a `tools/venv` found by walking up from CWD or this file
  3) ~/.video-watch-tools/venv   (the default the bundled installer creates)

Capture modes: by default you get both frames and a transcript. Use --transcript-only
(alias --no-frames) for talks/podcasts where the content is spoken, or --frames-only
(alias --no-transcribe) for silent screencasts where the content is on-screen.

Usage:
  python3 watch.py <file-or-URL> [--out DIR] [--mode scene|uniform|interval]
                   [--max-frames N] [--every SEC] [--whisper-model base] [--lang xx]
                   [--transcript-only | --frames-only] [--no-transcribe] [--quiet]
"""
import argparse
import json
import os
import shutil
import sys
import tempfile

REEXEC_FLAG = "_VIDEO_WATCH_REEXEC"


def _candidate_venvs():
    cands = []
    env = os.environ.get("VIDEO_WATCH_TOOLS")
    if env:
        cands.append(os.path.join(env, "venv"))
    starts = [os.getcwd(), os.path.dirname(os.path.abspath(__file__))]
    for start in starts:
        d = start
        for _ in range(10):
            cands.append(os.path.join(d, "tools", "venv"))
            nd = os.path.dirname(d)
            if nd == d:
                break
            d = nd
    cands.append(os.path.expanduser("~/.video-watch-tools/venv"))
    # de-dup, keep order
    seen, out = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _bootstrap_into_venv():
    """If deps are missing, re-exec under a venv python that has them."""
    try:
        import av  # noqa: F401
        return  # deps present, continue
    except Exception:
        pass
    if os.environ.get(REEXEC_FLAG):
        _fail_no_tools()
    # NB: compare the *invoked* paths, not realpath — a venv's bin/python is a symlink
    # to the base interpreter, so realpath() would wrongly equal sys.executable and we'd
    # never re-exec. The REEXEC_FLAG guard above prevents any infinite loop.
    for venv in _candidate_venvs():
        py = os.path.join(venv, "bin", "python")
        if os.path.exists(py) and os.path.abspath(py) != os.path.abspath(sys.executable):
            os.environ[REEXEC_FLAG] = "1"
            os.execv(py, [py, os.path.abspath(__file__), *sys.argv[1:]])
    _fail_no_tools()


def _fail_no_tools():
    sys.stderr.write(
        "\n[watch.py] The video toolchain is not installed.\n"
        "  It needs a Python venv with: av (PyAV), Pillow, faster-whisper, yt-dlp.\n\n"
        "  Fix: run the installer that ships with these skills, e.g.\n"
        "    bash <portfolio>/tools/install-tools.sh\n"
        "  or set VIDEO_WATCH_TOOLS to a dir containing a ready venv/.\n\n"
    )
    sys.exit(3)


_bootstrap_into_venv()

# --- from here we are guaranteed to be running under the venv python ---
import av  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


def log(quiet, *a):
    if not quiet:
        print(*a, file=sys.stderr)


def is_url(s):
    return s.startswith("http://") or s.startswith("https://") or s.startswith("www.")


def fetch_url(url, workdir, quiet):
    import yt_dlp
    out_tmpl = os.path.join(workdir, "source.%(ext)s")
    ydl_opts = {
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
        "outtmpl": out_tmpl,
        "quiet": quiet,
        "no_warnings": quiet,
        "noprogress": quiet,
        "merge_output_format": "mp4",
    }
    log(quiet, f"[watch] downloading {url} ...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title")
    # find the downloaded file
    files = [os.path.join(workdir, f) for f in os.listdir(workdir) if f.startswith("source.")]
    if not files:
        raise RuntimeError("yt-dlp did not produce a file")
    return files[0], title


def open_video(path):
    container = av.open(path)
    vstream = container.streams.video[0]
    tb = vstream.time_base
    duration = None
    if container.duration:
        duration = float(container.duration) / av.time_base
    elif vstream.duration and tb:
        duration = float(vstream.duration * tb)
    fps = float(vstream.average_rate) if vstream.average_rate else None
    width, height = vstream.codec_context.width, vstream.codec_context.height
    total = vstream.frames or 0
    return container, vstream, {
        "duration_sec": round(duration, 3) if duration else None,
        "fps": round(fps, 3) if fps else None,
        "resolution": f"{width}x{height}",
        "frame_count_total": total,
    }


def _frame_at(container, vstream, t_sec):
    """Seek near t_sec and return the next decoded frame as a PIL image + actual pts time."""
    try:
        container.seek(int(t_sec * av.time_base))
    except Exception:
        container.seek(0)
    for frame in container.decode(vstream):
        pts = float(frame.pts * vstream.time_base) if frame.pts is not None else t_sec
        return frame.to_image(), pts
    return None, t_sec


def _luma_signature(img, box=32):
    g = img.convert("L").resize((box, box))
    # Pillow 14 renames getdata() → get_flattened_data(); prefer the new name when present
    # so the distributed skill keeps working on both current and future Pillow.
    getter = getattr(g, "get_flattened_data", None) or g.getdata
    return list(getter())


def _sig_diff(a, b):
    if a is None or b is None:
        return 0.0
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def pick_timestamps(duration, mode, max_frames, every):
    if not duration or duration <= 0:
        duration = max_frames  # degrade: 1s spacing
    if mode == "interval":
        step = every if every else 5.0
        ts = [t for t in _frange(0, duration, step)][:max_frames]
        if not ts:
            ts = [0.0]
        return ts
    # uniform + scene both start from a uniform grid across the timeline
    n = max(1, max_frames)
    if n == 1:
        return [duration / 2]
    return [round(duration * i / (n - 1), 3) for i in range(n)]


def _frange(start, stop, step):
    x = start
    while x < stop:
        yield round(x, 3)
        x += step


def extract_frames(container, vstream, duration, mode, max_frames, every, out_frames, quiet):
    os.makedirs(out_frames, exist_ok=True)
    if mode == "scene":
        # Probe a denser uniform grid, then keep endpoints + the most visually-distinct moments.
        probe_n = min(max(max_frames * 4, 12), 200)
        probes = pick_timestamps(duration, "uniform", probe_n, None)
        scored = []
        prev_sig = None
        for t in probes:
            img, pts = _frame_at(container, vstream, t)
            if img is None:
                continue
            sig = _luma_signature(img)
            scored.append([pts, _sig_diff(sig, prev_sig), img])
            prev_sig = sig
        if not scored:
            chosen = []
        else:
            # always keep first + last; fill the rest by largest change
            first, last = scored[0], scored[-1]
            middle = sorted(scored[1:-1], key=lambda r: r[1], reverse=True)[: max(0, max_frames - 2)]
            chosen = sorted([first, last, *middle], key=lambda r: r[0])
        frames = [(pts, img) for pts, _, img in chosen]
    else:
        ts = pick_timestamps(duration, mode, max_frames, every)
        frames = []
        for t in ts:
            img, pts = _frame_at(container, vstream, t)
            if img is not None:
                frames.append((pts, img))
    # drop near-duplicate timestamps (seeking past the last keyframe can return the same frame twice)
    deduped, last_t = [], None
    for pts, img in frames:
        if last_t is None or abs(pts - last_t) > 0.06:
            deduped.append((pts, img))
            last_t = pts
    frames = deduped
    # save
    saved = []
    for i, (pts, img) in enumerate(frames, 1):
        rel = os.path.join("frames", f"frame-{i:04d}.png")
        img.save(os.path.join(os.path.dirname(out_frames), rel))
        saved.append({"index": i, "path": rel, "t": round(float(pts), 3)})
        log(quiet, f"[watch] frame {i}/{len(frames)} @ {pts:.2f}s")
    return saved, [img for _, img in frames]


def build_contact_sheet(images, saved, out_path, quiet, cols=4, cell=320):
    if not images:
        return None
    rows = (len(images) + cols - 1) // cols
    pad, label_h = 6, 16
    cell_h = int(cell * 9 / 16)
    W = cols * (cell + pad) + pad
    H = rows * (cell_h + label_h + pad) + pad
    sheet = Image.new("RGB", (W, H), (18, 18, 20))
    draw = ImageDraw.Draw(sheet)
    for idx, (img, meta) in enumerate(zip(images, saved)):
        r, c = divmod(idx, cols)
        x = pad + c * (cell + pad)
        y = pad + r * (cell_h + label_h + pad)
        thumb = img.convert("RGB").copy()
        thumb.thumbnail((cell, cell_h))
        sheet.paste(thumb, (x, y))
        draw.text((x + 2, y + cell_h + 2), f"#{meta['index']}  {meta['t']:.1f}s", fill=(220, 220, 220))
    sheet.save(out_path)
    log(quiet, f"[watch] contact sheet → {out_path}")
    return os.path.basename(out_path)


def transcribe(path, model_size, lang, quiet):
    try:
        from faster_whisper import WhisperModel
    except Exception as e:
        log(quiet, f"[watch] faster-whisper unavailable ({e}); skipping transcript")
        return None, "", False, f"faster-whisper unavailable: {e}"
    try:
        log(quiet, f"[watch] transcribing with faster-whisper '{model_size}' (first run downloads the model)…")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, info = model.transcribe(path, language=lang, vad_filter=True)
        segs, parts = [], []
        for s in segments:
            txt = s.text.strip()
            segs.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": txt})
            parts.append(txt)
            log(quiet, f"[watch]   [{s.start:6.1f}-{s.end:6.1f}] {txt}")
        return segs, " ".join(parts).strip(), True, None
    except Exception as e:
        log(quiet, f"[watch] transcription failed ({e}); continuing without audio")
        return None, "", False, f"transcription failed: {e}"


def main():
    ap = argparse.ArgumentParser(description="Watch a video → frames + transcript + digest.json")
    ap.add_argument("source", help="local video file or a URL (YouTube etc.)")
    ap.add_argument("--out", help="output dir (default: <stem>-watch next to CWD)")
    ap.add_argument("--mode", choices=["scene", "uniform", "interval"], default="scene")
    ap.add_argument("--max-frames", type=int, default=20)
    ap.add_argument("--every", type=float, default=None, help="seconds between frames (interval mode)")
    ap.add_argument("--whisper-model", default="base", help="tiny|base|small|medium|large-v3")
    ap.add_argument("--lang", default=None, help="force a language code, e.g. en (default: auto)")
    ap.add_argument("--no-transcribe", action="store_true", help="skip transcription (frames only)")
    ap.add_argument("--no-frames", action="store_true", help="skip frame extraction (transcript only)")
    ap.add_argument("--transcript-only", action="store_true", help="alias for --no-frames")
    ap.add_argument("--frames-only", action="store_true", help="alias for --no-transcribe")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    # Reconcile the friendly aliases into two booleans.
    no_frames = args.no_frames or args.transcript_only
    no_transcribe = args.no_transcribe or args.frames_only
    if no_frames and no_transcribe:
        sys.stderr.write(
            "[watch] nothing to produce — pick at most one of "
            "--transcript-only / --frames-only (not both)\n"
        )
        sys.exit(2)

    workdir = tempfile.mkdtemp(prefix="watch-src-")
    source, title = args.source, None
    try:
        if is_url(args.source):
            source, title = fetch_url(args.source, workdir, args.quiet)
        elif not os.path.exists(args.source):
            sys.stderr.write(f"[watch] no such file: {args.source}\n")
            sys.exit(2)

        stem = os.path.splitext(os.path.basename(source if not title else title))[0]
        stem = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in stem)[:60] or "video"
        # Default output goes to a temp dir, NOT the cwd — running from inside a repo must not
        # litter it with a frames/ dump. Override with --out. The absolute path is printed below.
        out = args.out or os.path.join(tempfile.gettempdir(), f"{stem}-watch")
        os.makedirs(out, exist_ok=True)
        frames_dir = os.path.join(out, "frames")

        saved, images, sheet = [], [], None
        meta = {"duration_sec": None, "fps": None, "resolution": None, "frame_count_total": 0}
        if not no_frames:
            container, vstream, meta = open_video(source)
            log(args.quiet, f"[watch] {meta['resolution']} @ {meta['fps']}fps, {meta['duration_sec']}s")
            saved, images = extract_frames(
                container, vstream, meta["duration_sec"], args.mode,
                args.max_frames, args.every, frames_dir, args.quiet,
            )
            sheet = build_contact_sheet(images, saved, os.path.join(out, "contact-sheet.png"), args.quiet)
            container.close()
        else:
            # transcript-only: grab lightweight metadata if we can, but don't fail on an
            # audio-only file (no video stream) — just proceed with empty meta.
            try:
                container, _vstream, meta = open_video(source)
                container.close()
            except Exception as e:
                log(args.quiet, f"[watch] no video metadata ({e}); continuing transcript-only")

        segs, full_text, transcribed, tnote = (None, "", False, "skipped (frames-only)")
        if not no_transcribe:
            segs, full_text, transcribed, tnote = transcribe(source, args.whisper_model, args.lang, args.quiet)

        if segs is not None:
            with open(os.path.join(out, "transcript.txt"), "w") as f:
                for s in segs:
                    f.write(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}\n")

        digest = {
            "source": args.source,
            "title": title,
            **meta,
            "mode": args.mode,
            "frames": saved,
            "contact_sheet": sheet,
            "transcribed": transcribed,
            "transcript": segs or [],
            "full_text": full_text,
            "notes": tnote,
        }
        digest_path = os.path.join(out, "digest.json")
        with open(digest_path, "w") as f:
            json.dump(digest, f, indent=2)

        # human-facing summary on stdout (the machine-readable part is digest.json)
        print(json.dumps({
            "out_dir": out,
            "digest": digest_path,
            "frames": len(saved),
            "contact_sheet": os.path.join(out, sheet) if sheet else None,
            "duration_sec": meta["duration_sec"],
            "transcribed": transcribed,
            "transcript_chars": len(full_text),
        }, indent=2))
        transcript_path = os.path.join(out, "transcript.txt")
        if sheet and segs is not None:
            nxt = (f"Next: an agent should READ {os.path.join(out, sheet)} (overview), then the "
                   f"individual frames in {frames_dir}, alongside {transcript_path}, to understand the video.")
        elif sheet:
            nxt = (f"Next: an agent should READ {os.path.join(out, sheet)} (overview), then the "
                   f"individual frames in {frames_dir}. (Frames only — no transcript.)")
        else:
            nxt = (f"Next: an agent should READ {transcript_path} to understand the video. "
                   f"(Transcript only — no frames.)")
        print("\n" + nxt, file=sys.stderr)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
