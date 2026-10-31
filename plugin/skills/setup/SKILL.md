---
name: setup
description: "Turn on relay in this repo once: create the coord records branch and its worktree, and fill project.md."
disable-model-invocation: true
---

Set up relay's records for the repo in the current folder. Each step ends on its check; stop at a failed check and tell the user what is missing. Terms are defined in `../../GLOSSARY.md` (paths here are relative to this skill's base directory). `<main>` below is the main checkout: the first path `git worktree list` prints (a desktop-app session usually runs in a worktree under `.claude/worktrees/`, which the app may clean up, so nothing goes beside it).

1. Existing records. If `AGENTS.md`/`CLAUDE.md` has the relay pointer line naming a records repo URL: `git clone -b coord <url>` to the path it names beside `<main>`, tell the user the path, and stop. Otherwise run `git ls-remote origin coord`. If it prints a sha, the repo is already set up: `git fetch origin coord`, `git -C <main> worktree add ../<main's folder name>-coord coord`, tell the user the path, and stop. Check: it printed nothing.
2. Prerequisites. Check: `git remote get-url origin` names a GitHub repo; `gh auth status` passes; skills named `mattpocock-skills:` are in your skill list; `docs/agents/issue-tracker.md` exists and names GitHub Issues (else ask the user to run `/setup-matt-pocock-skills` first); `python3 --version` (Windows `py -3 --version`) is 3.10 or later; `git --version` is 2.27 or later.
3. Where the records live. Run `gh repo view --json visibility -q .visibility`.
   - `PRIVATE` or `INTERNAL`: an orphan branch `coord` of this repo.
   - `PUBLIC`: the plan would be public. Ask the user: an orphan branch here anyway, or a separate private records repo (they give its URL, creating it if needed).
   Check: the choice, and the URL for a separate repo, are known.
4. Settings. Fill Repo and the default branch from `gh repo view --json nameWithOwner,defaultBranchRef`. Read the repo (package scripts, CI workflows, `AGENTS.md`/`CLAUDE.md`, `CONTRIBUTING.md`) and draft every other field of `templates/project.md`. Show the whole draft in one message and ask the user to confirm or correct it. Remove each `<optional: …>` line the user leaves unanswered. Check: every `<…>` left in the draft has an answer.
5. Create the records folder `<records>` = `<main>/../<main's folder name>-coord`, unless the user names another path.
   - orphan branch: `git -C <main> worktree add --detach <records>`, then `git -C <records> switch --orphan coord`;
   - separate repo: `mkdir <records>`, `git -C <records> init -b coord`, `git -C <records> remote add origin <url>`.
   Copy `templates/` into it (`gitignore` becomes `.gitignore`, `gitattributes` becomes `.gitattributes`, which keeps records LF on Windows), write the confirmed `project.md`, and commit `relay: records`. Check: `git -C <records> rev-list --count coord` is 1; `git -C <records> ls-tree -r --name-only HEAD` lists exactly the files under this skill's `templates/`, with `gitignore` and `gitattributes` renamed; `project.md` holds no `<`.
6. Push, on the user's yes: `git -C <records> push -u origin coord`. Check: `git -C <records> ls-remote origin coord` prints a sha.
7. Pointer. Propose this line for the repo's `AGENTS.md` (or `CLAUDE.md`), committed the way the repo commits doc changes:
   - orphan branch: `Multi-session work: records in the worktree on branch coord (find it with git worktree list; never merged); the coordinator runs /relay:coordinate, workers follow relay:work.`
   - separate repo: `Multi-session work: records in ../<folder>-coord beside the main checkout, cloned from <url> on branch coord (never merged); the coordinator runs /relay:coordinate, workers follow relay:work.` It is the only way the coordinator and other machines find them, so it is required.
   Check: orphan branch: the user accepted or declined it; separate repo: the line is committed.
8. Files convention. Propose this paragraph for the repo's `docs/agents/issue-tracker.md`, committed the way the repo commits doc changes:
   ```markdown
   **Files section:** an issue that will become a lane ends with a `## Files` section, one bullet per file it will touch: `- path/to/file (short scope)`, with `New:` before a file it creates. relay reads it to fill its roadmap and to tell which lanes can run in parallel, so list the paths here even when the rest of the ticket stays free of them.
   ```
   Check: the paragraph is committed, or the user declined it.
9. CI. Run `gh api repos/{owner}/{repo}/actions/workflows -q .total_count` (gh fills in `{owner}/{repo}`). When it prints `0`, also run `gh api repos/{owner}/{repo}/commits/HEAD/status -q .total_count` and `gh api repos/{owner}/{repo}/commits/HEAD/check-runs -q .total_count`. When either prints a number above `0`, tell the user CI was found outside GitHub Actions and do not offer a workflow; this case wins even when the other lookup failed. Otherwise, when either exits non-zero, tell the user the lookup failed and do not offer one. When both print `0`, tell the user the repo has no CI workflow, so every lane's PR will wait for local checks and an extra yes before its merge, and offer a workflow that runs `project.md`'s checks on `pull_request` (relay's own is a model: https://github.com/mileschintw/relay/blob/main/.github/workflows/test.yml), committed the way the repo commits CI changes. Check: a lookup printed a number above `0` or exited non-zero, or the workflow is committed, or the user declined it.
10. Tell the user, in the language they chose: the records path; that `/relay:coordinate` in a new desktop-app session starts a coordinator; and, for another machine, running `/relay:setup` there (step 1 attaches the existing records; for a separate repo, `git clone -b coord <url> ../<folder>-coord` beside the main checkout).
