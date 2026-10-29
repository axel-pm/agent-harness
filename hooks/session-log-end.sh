#!/usr/bin/env bash
# SessionEnd hook. Hands the session to session-log-summarize.py in the
# background, which asks `claude -p` (subscription, no API key) whether anything
# worth keeping happened and, if so, appends an auto-draft entry to the log.
# Returns immediately so exiting Claude isn't delayed. Without a log file it
# does nothing. Always exits 0.

CONFIG="${SESSION_LOG_CONFIG:-$HOME/.claude/session-log/config.env}"
# shellcheck source=/dev/null
[ -f "$CONFIG" ] && { set -a; . "$CONFIG"; set +a; }
HERE=$(dirname "$0")
STATE="$HOME/.claude/hooks"

payload=$(cat)
# Never summarise the summariser's own `claude -p` session.
[ -n "$SESSION_LOG_CHILD" ] && exit 0
{ [ -n "$SESSION_LOG_FILE" ] && [ -f "$SESSION_LOG_FILE" ]; } || exit 0

cwd=$(printf '%s' "$payload" | python3 -I -c 'import json,sys; print(json.load(sys.stdin).get("cwd",""))' 2>/dev/null)
if [ -n "$SESSION_LOG_WORKSPACE" ]; then
  case "$cwd/" in "${SESSION_LOG_WORKSPACE%/}/"*) ;; *) exit 0 ;; esac
fi

mkdir -p "$STATE/logs" "$STATE/state"
tmp=$(mktemp "$STATE/state/session-end.XXXXXX") || exit 0
printf '%s' "$payload" >"$tmp"
reason=$(printf '%s' "$payload" | python3 -I -c 'import json,sys; d=json.load(sys.stdin); print(d.get("session_id","")[:8], d.get("reason",""))' 2>/dev/null)
echo "$(date '+%Y-%m-%dT%H:%M:%S') session end $reason ($(basename "$cwd")): handing off" >>"$STATE/logs/session-log.log"

nohup python3 -I "$HERE/session-log-summarize.py" "$tmp" >>"$STATE/logs/session-log.log" 2>&1 &
disown 2>/dev/null

exit 0
