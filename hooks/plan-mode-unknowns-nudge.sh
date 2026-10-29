#!/usr/bin/env bash
# PreToolUse hook, matcher: ExitPlanMode
# Non-blocking nudge: fires as Claude presents a plan. Injects a reminder to
# surface unknowns (the find-your-unknowns skill) before the plan is finalized.
# Always exits 0 (allow) — never blocks. See ~/.claude/CLAUDE.md "## In plan mode".

cat >/dev/null   # consume stdin payload, we don't need it

read -r -d '' NOTE <<'EOF'
Plan-mode backstop (find-your-unknowns): before finalizing this plan, confirm you surfaced
the decisions the request never specified — the gaps between the ask (the "map") and the
codebase (the "territory"). If this task is large, ambiguous, architecture-shaping, or in an
unfamiliar codebase/domain AND you have not yet done discovery, go back and run the relevant
patterns before presenting: blind-spot pass (unknown-unknowns), interview-me (prioritize
questions that change the architecture), reference-as-map, brainstorm/prototype (aesthetic
choices). Fold the surfaced unknowns and their resolutions into the plan, and include the
implementation-notes logging instruction so mid-build deviations keep surfacing. Skip only if
the task is small and fully specified. This is a reminder, not a block — the plan proceeds.
EOF

# Emit as compact JSON with additionalContext (jq if available, else hand-rolled escaping).
if command -v jq >/dev/null 2>&1; then
  jq -n --arg ctx "$NOTE" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse", additionalContext:$ctx}}'
else
  esc=${NOTE//\\/\\\\}; esc=${esc//\"/\\\"}; esc=${esc//$'\n'/ }
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s"}}\n' "$esc"
fi

exit 0
