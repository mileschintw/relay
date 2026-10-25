---
name: setup
description: "Turn on relay in this repo once: create the coord records branch and its worktree, and fill project.md."
disable-model-invocation: true
---

Set up relay's records for the repo in the current folder. Each step ends on its check; stop at a failed check and tell the user what is missing. Words in **bold** are defined in `../../GLOSSARY.md` (from this skill's base directory).

1. **Prerequisites.** `git remote get-url origin` names a GitHub repo and `gh auth status` passes. mattpocock-skills is installed and `/setup-matt-pocock-skills` has run here: `docs/agents/issue-tracker.md` exists. Check: all three hold. (When the last one fails, ask the user to run `/setup-matt-pocock-skills` first; relay uses the tracker it records.)
2. **Where the records live.** Run `gh repo view --json visibility -q .visibility`.
   - `PRIVATE` or `INTERNAL`: the records go on an orphan branch `coord` of this repo.
   - `PUBLIC`: the plan would be public. Ask the user: an orphan branch here anyway, or a separate private records repo (they name or create it; you `git init` the folder and add it as `origin`).
   Check: the user's choice is known.
3. **Settings.** Read the repo (package scripts, CI workflows, `AGENTS.md`/`CLAUDE.md`, `CONTRIBUTING.md`) and draft each field of `templates/project.md`. Ask the user to confirm or change them in one round, your draft as the recommended answer: language, checks before done, test bar, off-limits paths, ask-first additions, unattended additions, release. Check: every `<…>` in the draft has an answer.
4. **Create the records folder** beside the main checkout, never beside this session's folder (a desktop-app session usually runs in a worktree under `.claude/worktrees/`, which the app may clean up). The main checkout `<main>` is the first path `git worktree list` prints; the records folder `<records>` is `<main>/../<main's folder name>-coord`, unless the user names another path.
   - orphan branch: `git -C <main> worktree add --detach <records>`, then in it `git switch --orphan coord` (works on git 2.27+);
   - separate repo: `mkdir <records>`, `git init -b coord` there.
   Copy `templates/` into it (`gitignore` becomes `.gitignore`), write the confirmed `project.md`, and commit `relay: records`. Check: `git -C <records> log --oneline` shows that one commit on `coord`, and its tree has no file from the default branch.
5. **Push**, on the user's yes: `git -C <records> push -u origin coord`. Check: `git ls-remote origin coord` prints a sha.
6. **Pointer.** Propose this line for the repo's `AGENTS.md` (or `CLAUDE.md`), committed the way the repo commits doc changes:
   `Multi-session work: records in the worktree on branch coord (find it with git worktree list; never merged); the coordinator runs /relay:coordinate, workers follow relay:work.`
   With a separate records repo, the line names its absolute path instead of the worktree.
   Check: the user accepted or declined it.
7. Tell the user, in the language they chose: the records path; that `/relay:coordinate` in a new desktop-app session starts a coordinator; and, for another machine, `git fetch origin coord` then, in the main checkout, `git worktree add ../<folder>-coord coord`.
