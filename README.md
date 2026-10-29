# agent-harness

The global layer of the harness I run around Claude Code: the instructions, hooks, skills and subagent that every session on my machine loads. `~/.claude` links to this repository, so what's here is what runs.

The build note explains why each part exists: [Building a harness so a team of one can trust its coding agents](https://www.axelsooriah.com/builds/agent-harness).

## What's in it

| Path | What it does |
|---|---|
| `CLAUDE.md` | Global instructions. In plan mode, find the decisions the request never made before presenting the plan. |
| `hooks/plan-mode-unknowns-nudge.sh` | `PreToolUse` hook on `ExitPlanMode`. Reminds the agent of the discovery pass as it presents a plan. It never blocks. |
| `hooks/session-log-start.sh` | `SessionStart` hook. Tells the session where the log is and how many auto-drafted entries are waiting for review. |
| `hooks/session-log-end.sh`, `hooks/session-log-summarize.py` | `SessionEnd` hook. Passes the new part of the transcript, without tool output, to a headless `claude -p` run with no tools. If something worth keeping happened, it appends a dated draft to the log. |
| `agents/detrope.md` | A subagent that strips the tells of AI writing from prose. A packaged version is [deslopify](https://github.com/axel-pm/deslopify). |
| `skills/find-your-unknowns` | The discovery pass: six prompt patterns for finding the decisions a plan leaves open. |
| `skills/deploy` | `/deploy`: build, run the end-to-end tests if the project has them, promote `dev` to `main` and deploy on Vercel. Any failure stops it. |
| `skills/video-to-skill` | Watches a tutorial and writes a skill from it. Also packaged as [watch & learn](https://github.com/axel-pm/watch-n-learn). |
| `skills/video-essence` | Watches a reference video and turns its style into a spec for something else. |
| `settings.example.json` | The hook wiring, and the permission rules that make auto mode ask before a production deploy or a database migration. |

## Enforced or only asked

The permission rules are enforced: in auto mode, Claude Code stops and asks before `vercel deploy --prod` or `supabase db push`, whatever the agent intends. The rest of this repository is a request the agent can skip. The plan hook reminds and never blocks, `/deploy` runs its checks only when invoked, and `CLAUDE.md` is an instruction.

The checks that decide whether work ships, such as CI, validators and tool allowlists for headless agents, live in each project's own repository.

## Install

```sh
git clone https://github.com/axel-pm/agent-harness ~/Projects/agent-harness
~/Projects/agent-harness/install.sh
```

`install.sh` symlinks each file into `~/.claude` and moves anything it replaces to `~/.claude/backups/`. It doesn't touch `settings.json`: merge what you want from `settings.example.json` by hand.

The session-log hooks do nothing until you configure them. Copy `hooks/session-log.example.env` to `~/.claude/session-log/config.env` and set `SESSION_LOG_FILE`. The config can also limit the hooks to one folder and swap in your own summariser prompt and start note. Keep those files out of this repository.

## Tests

`tests/run.sh` checks the hooks' output, what the summariser lets through to the model, and the installer, and it validates each skill's frontmatter. CI runs it with shellcheck on every push.

Nothing here measures whether the discovery pass changes plans, or whether the log saves repeated corrections.

## License

MIT
