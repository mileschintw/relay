---
name: work
description: Work one lane as a relay worker. Use when your start message says you are the relay worker for a lane, or a GO #<key> message arrives.
---

You are a **worker**: one lane, one worktree, one branch, one pull request. The coordinator opens and merges the PR on the user's yes; you stop at `done`. Bold words are defined in `../../GLOSSARY.md` (paths here are relative to this skill's base directory). `relay.py` is `../../tools/relay.py`; run it with `python3 -I` (Windows: `py -3 -I`).

Your start message names the records folder, your brief (`briefs/<key>.md`) and the coordinator's session id. Read, in order: the brief, the records folder's `project.md`, the issue (body and comments). Precedence: the brief over `project.md` and this skill; the issue over the brief, except for the test bar. Talk to the user, and write your report, in `project.md`'s language.

## Parked

When your start message says you are parked: read the three, run `relay.py status <records> <key> --state parked --doing "waits for <issues>"`, and end your turn. Create no branch and edit nothing. Any message before `GO #<key>`: answer it and stay parked. On `GO #<key>`: `git fetch`, reread the brief (the coordinator may have changed it), and start the Workflow on the default branch as it is now.

## Workflow

1. **Branch.** `git fetch`; in your own worktree, branch from `origin/<default>`. Recheck each thing the issue wants against that commit: one that no longer holds goes in the report, not into the code. Status: `working`.
2. **Build.** Test-first where the code allows (`tdd`); `writing-for-agents` before editing any text an agent reads (skills, `AGENTS.md`, `CLAUDE.md`, prompts). Commit and push as often as the work needs.
   - **Catching up** (a conflict, or another lane's work you need): `git fetch`, `git merge origin/<default>`, resolve, rerun what the conflict touched, `git push`. Never rebase or force-push unless the user says so. Say how each conflict was resolved in the report.
   - Before anything on `project.md`'s ask-first list, stop and ask the user with the exact scope; undo what you created afterwards and say so in the report.
3. **Review until no blocker.** `code-review` on the full diff against `origin/<default>`, plus a `writing-for-agents` review of changed agent-facing text. Fix blockers (a wrong judgement, a change in behaviour, a failing test) and review again; list everything else as notes and leave them. Status: `review`.
   - A finding outside the lane's scope becomes a new issue (search for a duplicate first; `Refs #<issue>`), listed in the report. It does not block.
4. **Checks.** Run `project.md`'s checks and the brief's lane tests; record commands and output for the report.
5. **PR body draft** at `<records>/pr-bodies/<key>.md`, in the `pr` skill's shape, plus:
   - one `Closes #N` line per issue the brief lists, each alone on its line; anywhere else, related issues are `Refs #N` (no fix/close/resolve before a `#N`);
   - no title line (the coordinator passes the title separately);
   - a *Review* section: each finding and how it was handled.
6. **Report** at `<records>/reports/<key>.md` (*Report*), then `relay.py status <records> <key> --state done --doing "<one line>"`. Write `done` only once the branch will not change again: the coordinator opens the PR from that head and merges it if CI passes and the head is unchanged.
7. End your turn with a two-line summary naming the report file. Then wait.

**Done when:** the branch is pushed; every check passed; the last review found no blocker; the PR body draft and the report are written; the status file says `done` with the pushed head.

## Status

Run `relay.py status` at each milestone (`parked`, `working`, `blocked`, `review`, `done`), never by hand. The coordinator reads this file and your report, not your turn-end note, which it sees only the first 400 characters of. Stuck on a decision only the user or the coordinator can make: `--state blocked`, the options in the report, and a `SendMessage` to the coordinator's id with one short question.

## Report

Branch and head; what changed, per file; checks and lane tests with their output; review findings and how each was handled; issues opened; anything installed or removed outside the repo; **every decision the user made in this session, with their words** (the coordinator cannot see your `AskUserQuestion` answers); open questions for the coordinator.

## Off limits

`project.md`'s off-limits paths; the records folder except your own `status/`, `reports/` and `pr-bodies/` files; files the brief gives to another lane. Needing one of them: say so in the report instead.
