---
name: deploy
description: Promote dev to main and deploy to production via Vercel (adapts to the current repo's setup)
allowed-tools: Bash Read Glob Grep
argument-hint: [deploy]
---

Promote `dev` to `main` and deploy to production on Vercel. Adapts to the repo: app in root or a monorepo subdirectory, E2E tests optional, git-integration push or CLI deploy.

**This workflow runs without confirmation. The user said /deploy which means DO IT.**

## Steps

1. **Locate the app.** APP_DIR = the directory whose `package.json` has a `build` script: the repo root if it qualifies, otherwise the first match under `apps/*/`. If none found, abort: "No buildable app found."

2. **Verify branch.** Run `git branch --show-current`. If a `dev` branch exists (`git show-ref --verify --quiet refs/heads/dev`), require being on `dev`; abort otherwise: "Switch to dev first." If no `dev` branch exists, deploy from the current branch (skip step 6's promote and treat the current branch as what ships).

3. **Check for uncommitted changes.** Run `git status --porcelain`. If non-empty (excluding untracked), abort: "Uncommitted changes — commit or stash first."

4. **Verify build.** In APP_DIR run `npx next build` (or `npm run build` if it's not a Next.js app). If it fails, abort: "Build failed — fix errors before deploying."

5. **Run E2E tests — only if Playwright is configured.** If a `playwright.config.*` exists in APP_DIR or the repo root, run `npx playwright test --reporter=line` from that directory (timeout: 180s). If any test fails, abort: "E2E tests failed — fix before deploying." Report pass count. If there is no Playwright config, skip and note "No E2E suite — skipped."

6. **Check for commits to promote** (only when a `dev` branch exists). Run `git log main..dev --oneline`. If empty AND main has already been deployed to production before, say "dev is already up to date with main — nothing to deploy." and stop. Otherwise promote immediately, no confirmation:
   ```
   git checkout main
   git merge dev --no-edit
   ```

7. **Ship.** Pick the path the repo supports:
   - **Git integration** (a git remote exists and the Vercel project deploys from it): from `main`, `git push origin main`. Vercel auto-deploys. Return to `dev`.
   - **CLI deploy** (no git remote, or the Vercel project has no git integration; `.vercel/project.json` exists): from `main`, run `vercel deploy --prod --yes`, then return to `dev` if it exists.
   - If the repo isn't Vercel-linked at all (no `.vercel/project.json`), abort: "Not linked to a Vercel project — run `vercel link` first."

8. **Report.**
   - List of commits promoted (or "deployed current branch")
   - E2E result (pass count, or skipped)
   - The production URL: take it from the deploy output or the project's configured domains; do not guess
   - Deploy status link: `https://vercel.com/<org>/<projectName>` using names from `.vercel/project.json` or `vercel inspect`
