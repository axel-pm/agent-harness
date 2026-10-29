#!/usr/bin/env bash
# SessionStart hook (all sources: startup, resume, clear, compact).
# Tells Claude where the session log is and to add to it when something worth
# keeping happens. Settings come from an untracked config file (see
# session-log.example.env); without a log file it does nothing.
# Never blocks; always exits 0. The SessionEnd hook (session-log-end.sh) appends auto-drafts.

CONFIG="${SESSION_LOG_CONFIG:-$HOME/.claude/session-log/config.env}"
# shellcheck source=/dev/null
[ -f "$CONFIG" ] && { set -a; . "$CONFIG"; set +a; }

payload=$(cat)
# The SessionEnd summariser runs `claude -p`; don't nudge that child session.
[ -n "$SESSION_LOG_CHILD" ] && exit 0

LOG_FILE="$SESSION_LOG_FILE"
{ [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; } || exit 0

if [ -n "$SESSION_LOG_WORKSPACE" ]; then
  cwd=$(printf '%s' "$payload" | python3 -I -c 'import json,sys; print(json.load(sys.stdin).get("cwd",""))' 2>/dev/null)
  case "$cwd/" in "${SESSION_LOG_WORKSPACE%/}/"*) ;; *) exit 0 ;; esac
fi

drafts=$(grep -c '^### .* · auto-draft · ' "$LOG_FILE" 2>/dev/null)
drafts=${drafts:-0}

if [ -n "$SESSION_LOG_NOTE" ] && [ -f "$SESSION_LOG_NOTE" ]; then
  # A note of your own, with {log_file} and {drafts} filled in.
  NOTE=$(python3 -I -c 'import sys; print(open(sys.argv[1], encoding="utf-8").read().replace("{log_file}", sys.argv[2]).replace("{drafts}", sys.argv[3]).strip())' \
    "$SESSION_LOG_NOTE" "$LOG_FILE" "$drafts")
else
  read -r -d '' NOTE <<EOF
A session log is kept at
$LOG_FILE
When this session does something worth keeping (an architecture decision, a tradeoff, a security or privacy fix, an eval result, an incident), add a dated entry to it before finishing. Facts only, with sources; never secrets; say what was measured and how small it was.
A SessionEnd hook also appends auto-drafted entries; there are currently $drafts. Review them before relying on them.
EOF
fi

if command -v jq >/dev/null 2>&1; then
  jq -n --arg ctx "$NOTE" \
    '{hookSpecificOutput:{hookEventName:"SessionStart", additionalContext:$ctx}}'
else
  esc=${NOTE//\\/\\\\}; esc=${esc//\"/\\\"}; esc=${esc//$'\n'/ }
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$esc"
fi

exit 0
