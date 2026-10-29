#!/usr/bin/env bash
# Tests for the hooks, the installer and the skills. Run from anywhere; exits non-zero on any failure.
# Needs bash, python3 and jq. CI also runs shellcheck over the scripts.
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
fails=0
pass() { echo "ok   $1"; }
fail() { echo "FAIL $1"; fails=$((fails + 1)); }
check() {  # check <name> <command...>
  local name=$1; shift
  if "$@"; then pass "$name"; else fail "$name"; fi
}
quiet() { "$@" >/dev/null; }

for tool in python3 jq; do
  command -v "$tool" >/dev/null || { echo "FAIL $tool is required"; exit 1; }
done

# Hooks get a JSON payload on stdin. Isolate them from the real ~/.claude.
export HOME="$TMP/home"
mkdir -p "$HOME"
export SESSION_LOG_CONFIG="$TMP/config.env"
payload() { printf '{"session_id":"abcdef123456","cwd":"%s","transcript_path":"%s","reason":"exit"}' "$1" "${2:-}"; }
context() { jq -r '.hookSpecificOutput.additionalContext'; }

# Plan hook: always a reminder, never a block.
out=$(echo '{}' | "$REPO/hooks/plan-mode-unknowns-nudge.sh"); code=$?
check "plan hook exits 0" test "$code" -eq 0
check "plan hook names its event" test "$(jq -r '.hookSpecificOutput.hookEventName' <<<"$out")" = PreToolUse
check "plan hook reminds about the discovery pass" grep -q "find-your-unknowns" <<<"$out"

# Start hook without a config: silent.
out=$(payload "$TMP" | "$REPO/hooks/session-log-start.sh")
check "start hook is silent without a config" test -z "$out"

# Start hook with a log holding two auto-drafts.
LOG="$TMP/log.md"
printf '# Log\n\n### 2026-01-01 · auto-draft · x · session 1\n\n### 2026-01-02 · auto-draft · y · session 2\n' >"$LOG"
printf 'SESSION_LOG_FILE="%s"\n' "$LOG" >"$SESSION_LOG_CONFIG"
out=$(payload "$TMP" | "$REPO/hooks/session-log-start.sh" | context)
check "start hook names the log" grep -qF "$LOG" <<<"$out"
check "start hook counts the drafts" grep -q "there are currently 2\." <<<"$out"

printf '# Log\n' >"$LOG"
out=$(payload "$TMP" | "$REPO/hooks/session-log-start.sh" | context)
check "start hook counts zero drafts" grep -q "there are currently 0\." <<<"$out"

# Start hook with a note of your own.
printf 'Log at {log_file}, {drafts} drafts.\n' >"$TMP/note.md"
printf 'SESSION_LOG_FILE="%s"\nSESSION_LOG_NOTE="%s"\n' "$LOG" "$TMP/note.md" >"$SESSION_LOG_CONFIG"
out=$(payload "$TMP" | "$REPO/hooks/session-log-start.sh" | context)
check "start hook fills in a custom note" test "$out" = "Log at $LOG, 0 drafts."

# Workspace limit.
printf 'SESSION_LOG_FILE="%s"\nSESSION_LOG_WORKSPACE="%s/work"\n' "$LOG" "$TMP" >"$SESSION_LOG_CONFIG"
mkdir -p "$TMP/work/app" "$TMP/workshop"
check "start hook runs inside the workspace" test -n "$(payload "$TMP/work/app" | "$REPO/hooks/session-log-start.sh")"
check "start hook skips a sibling folder" test -z "$(payload "$TMP/workshop" | "$REPO/hooks/session-log-start.sh")"

# The summariser's own `claude -p` session is never nudged or summarised.
check "start hook skips the child session" test -z "$(payload "$TMP/work/app" | SESSION_LOG_CHILD=1 "$REPO/hooks/session-log-start.sh")"
payload "$TMP/work/app" | SESSION_LOG_CHILD=1 "$REPO/hooks/session-log-end.sh"
check "end hook skips the child session" test ! -e "$HOME/.claude/hooks/logs/session-log.log"

# Summariser: only the user's and Claude's own words reach the model.
printf '%s' "$(payload "$TMP" "$REPO/tests/fixtures/transcript.jsonl")" >"$TMP/payload.json"
out=$(SESSION_LOG_FILE="$LOG" SESSION_LOG_STATE="$TMP/state.json" SESSION_LOG_DRY_RUN=1 \
  python3 -I "$REPO/hooks/session-log-summarize.py" "$TMP/payload.json")
check "summariser keeps both users' messages" grep -q "2 user messages" <<<"$out"
check "summariser keeps the user's words" grep -q "^USER: Add a retry to the fetch.$" <<<"$out"
check "summariser keeps Claude's words" grep -q "^CLAUDE: Done: three attempts, then fail.$" <<<"$out"
for hidden in REMINDER_TEXT TOOL_INPUT TOOL_OUTPUT SIDECHAIN_TEXT META_TEXT; do
  check "summariser drops $hidden" test -z "$(grep "$hidden" <<<"$out")"
done
out=$(SESSION_LOG_FILE="$LOG" SESSION_LOG_STATE="$TMP/state.json" SESSION_LOG_PROMPT="$TMP/missing.md" SESSION_LOG_DRY_RUN=1 \
  python3 -I "$REPO/hooks/session-log-summarize.py" "$TMP/payload.json")
check "summariser stops when its prompt file is missing" grep -q "can't read prompt file" <<<"$out"

# Installer: links everything, backs up what was there, and can run twice.
CLAUDE_DIR="$TMP/claude"
mkdir -p "$CLAUDE_DIR"
echo "old" >"$CLAUDE_DIR/CLAUDE.md"
CLAUDE_DIR="$CLAUDE_DIR" "$REPO/install.sh" >/dev/null
check "installer links CLAUDE.md" test "$(readlink "$CLAUDE_DIR/CLAUDE.md")" = "$REPO/CLAUDE.md"
check "installer links each skill" test "$(readlink "$CLAUDE_DIR/skills/deploy")" = "$REPO/skills/deploy"
check "installer links the hooks" test -x "$CLAUDE_DIR/hooks/session-log-start.sh"
check "installer backs up what it replaces" grep -qx old "$CLAUDE_DIR"/backups/agent-harness-*/CLAUDE.md
check "installer is idempotent" test -z "$(CLAUDE_DIR="$CLAUDE_DIR" "$REPO/install.sh")"

# Settings and skills.
check "settings.example.json parses" quiet jq -e '.hooks.SessionEnd' "$REPO/settings.example.json"
for skill in "$REPO"/skills/*/; do
  check "skill $(basename "$skill") validates" quiet python3 -I "$REPO/skills/video-to-skill/scripts/validate_skill.py" "$skill"
done

echo
if [ "$fails" -gt 0 ]; then echo "$fails failed"; exit 1; fi
echo "all passed"
