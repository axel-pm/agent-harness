#!/usr/bin/env bash
# Links this repository into ~/.claude, so every Claude Code session loads it.
# Anything already in the way is moved to ~/.claude/backups/agent-harness-<time>/.
# settings.json is left alone: merge what you want from settings.example.json by hand.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
BACKUP="$CLAUDE_DIR/backups/agent-harness-$(date +%Y%m%d-%H%M%S)"

link() {  # link <path relative to the repo>
  local src="$REPO/$1" dest="$CLAUDE_DIR/$1"
  if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
    return
  fi
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    mkdir -p "$BACKUP/$(dirname "$1")"
    mv "$dest" "$BACKUP/$1"
    echo "backed up $1"
  fi
  mkdir -p "$(dirname "$dest")"
  ln -s "$src" "$dest"
  echo "linked $1"
}

link CLAUDE.md
for f in agents/*.md hooks/*.sh hooks/*.py; do
  link "$f"
done
for d in skills/*/; do
  link "${d%/}"
done
