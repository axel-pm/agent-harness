"""Background worker for the session-log SessionEnd hook.

Reads the session transcript, keeps only the user's and Claude's own words (no
tool output), and asks `claude -p` whether anything worth keeping happened.
If so, the draft is appended to the log as an "auto-draft" entry for the user
to review. A per-session state file remembers how far each transcript has been
read, so a resumed session only contributes what's new.

Settings (exported by the hook from its config file): SESSION_LOG_FILE (required),
SESSION_LOG_PROMPT (a prompt file of your own; the default is below),
SESSION_LOG_STATE, SESSION_LOG_MAX_CHARS, SESSION_LOG_DRY_RUN=1 (report what
would be sent, call nothing).
"""

import datetime
import json
import os
import re
import subprocess
import sys
import tempfile

LOG_FILE = os.environ.get("SESSION_LOG_FILE", "")
PROMPT_FILE = os.environ.get("SESSION_LOG_PROMPT", "")
STATE_FILE = os.environ.get(
    "SESSION_LOG_STATE", os.path.expanduser("~/.claude/hooks/state/session-log.json")
)
MAX_CHARS = int(os.environ.get("SESSION_LOG_MAX_CHARS", "80000"))
PER_MESSAGE = 4000
MIN_USER_MESSAGES = 2
DRY_RUN = os.environ.get("SESSION_LOG_DRY_RUN") == "1"

DEFAULT_PROMPT = """You keep a private engineering log for the developer who ran this session.

Standard input is a condensed transcript of one Claude Code session (USER = the developer, CLAUDE = the assistant; tool output removed).

If nothing in it is worth keeping (a decision, a tradeoff, a fix, an eval or benchmark result, an incident, a lesson), reply with exactly: NONE

Otherwise reply with one Markdown entry, under 300 words, in this shape and nothing else:
**What happened:** 2-4 bullets: decisions, tradeoffs, fixes, results. Include numbers only if they appear in the transcript, with what they measured.
**Why it matters:** one or two sentences on what it changes or teaches.
**Caveats:** what's small, unfinished, private or done by the agent rather than the developer.

Rules: facts only from the transcript; never invent numbers or outcomes. Never include secrets, keys, tokens, passwords or personal contact details. Refer to people by role, and use they/them for them. Plain, direct sentences."""


def log(msg: str) -> None:
    print(f"{datetime.datetime.now().isoformat(timespec='seconds')} {msg}", flush=True)


def text_of(content) -> str:
    """The prose in a message: plain strings and text blocks, never tool calls or results."""
    if isinstance(content, str):
        parts = [content]
    elif isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    else:
        return ""
    text = "\n".join(parts)
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S)
    text = re.sub(r"<(local-command-[a-z]+|command-[a-z]+|bash-[a-z]+)>.*?</\1>", "", text, flags=re.S)
    return text.strip()


def condense(lines: list[str]) -> tuple[str, int]:
    out, users = [], 0
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        kind = entry.get("type")
        if kind not in ("user", "assistant") or entry.get("isMeta") or entry.get("isCompactSummary"):
            continue
        if entry.get("isSidechain"):
            continue
        text = text_of((entry.get("message") or {}).get("content"))
        if not text:
            continue
        if len(text) > PER_MESSAGE:
            text = text[:PER_MESSAGE] + " […]"
        if kind == "user":
            users += 1
        out.append(f"{'USER' if kind == 'user' else 'CLAUDE'}: {text}")
    joined = "\n\n".join(out)
    if len(joined) > MAX_CHARS:
        tail = joined[-MAX_CHARS:]
        joined = tail[tail.find("\n\n") + 2 :] if "\n\n" in tail else tail  # start on a whole message
    return joined, users


def load_prompt():
    if not PROMPT_FILE:
        return DEFAULT_PROMPT
    try:
        with open(PROMPT_FILE, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None  # a prompt was asked for and can't be read: don't fall back to a different one


def main() -> None:
    payload_path = sys.argv[1]
    try:
        with open(payload_path) as f:
            payload = json.load(f)
    finally:
        if not DRY_RUN:
            try:
                os.remove(payload_path)
            except OSError:
                pass

    session_id = payload.get("session_id", "")
    transcript = payload.get("transcript_path", "")
    project = os.path.basename((payload.get("cwd") or "").rstrip("/")) or "?"
    if not LOG_FILE:
        log(f"skip {session_id[:8]}: SESSION_LOG_FILE not set")
        return
    if not session_id or not os.path.isfile(transcript):
        log(f"skip {session_id[:8]}: no transcript")
        return
    prompt = load_prompt()
    if prompt is None:
        log(f"error {session_id[:8]} ({project}): can't read prompt file {PROMPT_FILE}")
        return

    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {}

    with open(transcript, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    start = state.get(session_id, 0)
    condensed, users = condense(lines[start:])
    if users < MIN_USER_MESSAGES:
        log(f"skip {session_id[:8]} ({project}): {users} new user message(s)")
        state[session_id] = len(lines)
        save_state(state)
        return

    if DRY_RUN:
        log(f"dry run {session_id[:8]} ({project}): lines {start}-{len(lines)}, {users} user messages, {len(condensed)} chars")
        print(condensed[:1500])
        return

    env = dict(os.environ, SESSION_LOG_CHILD="1")
    env.pop("CLAUDECODE", None)  # a hook runs inside a Claude Code process; the child is a separate session
    try:
        result = subprocess.run(
            ["claude", "-p", "--model", "sonnet", "--tools", "", "--strict-mcp-config",
             "--no-session-persistence", "--output-format", "text", prompt],
            input=condensed, capture_output=True, text=True, env=env,
            cwd=tempfile.gettempdir(), timeout=900,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f"error {session_id[:8]} ({project}): {e}")
        return
    if result.returncode != 0:
        log(f"error {session_id[:8]} ({project}): exit {result.returncode}: {result.stderr.strip()[:300]}")
        return

    draft = result.stdout.strip()
    state[session_id] = len(lines)
    if not draft or draft.upper().startswith("NONE"):
        log(f"none {session_id[:8]} ({project}): nothing worth keeping")
        save_state(state)
        return

    day = datetime.date.today().isoformat()
    entry = f"\n### {day} · auto-draft · {project} · session {session_id[:8]} (review before relying on it)\n\n{draft}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
    save_state(state)
    log(f"appended {session_id[:8]} ({project}): {len(draft)} chars")


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_FILE)


if __name__ == "__main__":
    main()
