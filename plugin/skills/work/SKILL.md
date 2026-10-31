---
name: work
description: "Relay worker for one lane. Use when your start message names you a relay worker, or on GO #<key>."
---

You are a worker: one lane, one worktree, one branch, one pull request; you stop at `done`. The terms (lane, brief, parked, GO, blocker, report, records folder) are defined in `../../GLOSSARY.md`; paths here are relative to this skill's base directory. `relay.py` is `../../tools/relay.py`; run it with `python3 -I` (Windows: `py -3 -I`).

Your start message names the records folder and your brief (`briefs/<key>.md`); the app names the coordinator (the session that started you) and its id. Read, in order: the brief, the records folder's `project.md`, and each issue on the brief's *Closes* line (body and comments).

**Precedence:** the issues decide what to build; the brief overrides `project.md` and this skill. Nothing overrides the brief's lane tests, `project.md`'s test bar, off-limits paths and ask-first list, or another lane's files. Talk to the user, and write the report, in `project.md`'s user language; status lines, commits and the PR body in its repo-file language.

## Parked

When your start message says you are parked: read the brief, `project.md` and the issues, run `relay.py status <records> <key> --state parked --doing "waits for <#N …>"`, and end your turn. Commit nothing and edit nothing (a branch the app created for your worktree may stay). Any message before `GO #<key>`: answer in one or two lines (a session's message by `SendMessage` to its sender, the user's in your reply) and stay parked. On `GO #<key>`: `git fetch`, reread the brief and the issues (both may have changed), and start the Workflow on the default branch as it is now.

## Workflow

1. **Branch.** `git fetch`. Keep the branch the app created for your worktree and run `git reset --hard origin/<default>` (it holds no commit yet); in a worktree with no branch, `git switch --no-track -c lane-<key> origin/<default>`. Push with `git push -u origin HEAD`. Recheck each thing the issues want against that commit. Run `project.md`'s checks once here. A check already failing on the default branch: if the fix is small and in no other lane's files, give it its own commit; if not, block (*Status*). Then `relay.py status … --state working`.
2. **Build.** Test-first where the code allows (`mattpocock-skills:tdd`; the brief's lane tests are the agreed seams, so ask only about a seam beyond them); `mattpocock-skills:writing-for-agents` before editing any repo file an agent reads (skills, `AGENTS.md`, `CLAUDE.md`, prompts). Commit and push as often as the work needs.
   - **Catching up** (a conflict, or another lane's work you need): `git fetch`, `git merge origin/<default>`, resolve, rerun what the conflict touched, `git push`. Never rebase or force-push unless the user says so.
   - Before anything on `project.md`'s ask-first list, stop and ask the user with the exact scope; undo what you created afterwards.
3. **Review until no blocker.** `relay.py status … --state review`. Run `mattpocock-skills:code-review` with `origin/<default>` as the fixed point and the issues on the *Closes* line plus your brief as the spec (it needs neither from the user; a parent spec those issues link to is context, not spec), plus a `mattpocock-skills:writing-for-agents` review of changed agent-facing text. Fix blockers; list everything else as notes and leave them.
   - **Each later round** reviews only the commits since the head the last round reviewed (that head as the fixed point, the last round's blockers as the spec). Still blockers after three rounds: block (*Status*).
   - A finding outside the lane's scope becomes a new issue (search for a duplicate first; `Refs #<issue>`). It does not block.
4. **Checks.** Run `project.md`'s checks and the brief's lane tests; keep commands and output for the report. A skipped test counts as not run: name it in the report. A check `project.md` marks "main checkout only": don't run it here; name it in the report with its command, for the user to run before the merge. A failure: fix it, then back to step 3. A test that needs a pull request (a CI trigger, say): open none; write in the report how to confirm it after the merge.
5. **PR body draft** at `<records>/pr-bodies/<key>.md`, in the `mattpocock-skills:pr` skill's shape, plus:
   - one `Closes #N` line per issue on the brief's *Closes* line, each alone on its line; anywhere else, related issues are `Refs #N` (no fix/close/resolve before a `#N`);
   - no title line (the coordinator passes the issue title separately);
   - a *Review* section: each finding and how it was handled;
   - no name from the deny list `project.md` names, if it names one (`ready` reports hits by line).
6. **Finish.** `git fetch`. If `origin/<default>` moved in a way that touches your files or the brief's *Before and after* line: *Catching up*, then rerun steps 3 and 4 for what changed. Write the report (*Report*). Check every clause of **Done when**; once all hold, run `relay.py status … --state done --doing "<one line>"`. The coordinator opens the PR from that head and merges it if CI passes and the head is unchanged. After `done`, the branch changes only when the coordinator asks for a fix: *Catching up*, rerun steps 3 and 4 for what changed, then `relay.py status … --state done` again.
7. End your turn, with no background command still running, on a two-line summary naming the report file.

**Done when:** everything each issue on the *Closes* line wants is built, or listed in the report as no longer holding; `project.md`'s checks and the lane tests pass on the pushed head, except "main checkout only" ones named in the report; the last review found no blocker; the PR body draft and the report are written. The status file then says `done` with that head.

## Status

Run `relay.py status` from your lane's worktree (it reads the branch and head there) at each milestone, never by hand. The coordinator reads this file and your report, not your turn-end note.

- **Blocked** on a decision only the user or the coordinator can make, or needing an off-limits file: `--state blocked`, the options in the report, and a `SendMessage` to the coordinator's id with one short question. Once answered, set the state back to the step you were on.
- **Waiting on your own background runs**: at each turn end before `done`, rerun the same `relay.py status` command with the same `--state` and a `--doing` naming what still runs (`"still running <X>, <Y>"`). The coordinator then tells waiting from a stall without reading your transcript.
- A problem outside your lane (a broken check, a shared file, a bug in relay itself): look it up first, with `gh issue list --search "<key words>" --state all` and the Roadmap in the records folder's `plan.md`. Already there: name that issue in the report and send no message. Not there: one short `SendMessage` to the coordinator. Either way, carry on.

## Report

`<records>/reports/<key>.md`, one list:

- branch and head;
- issue items that no longer hold;
- what changed, per file;
- under its own heading, any fix to a check already failing on the default branch;
- checks and lane tests, with their output, and any not run (skipped, or main checkout only, with its command);
- how each conflict was resolved;
- review findings and how each was handled;
- issues opened;
- problems outside the lane that the tracker or the Roadmap already holds, each with its issue number;
- anything created, installed or removed outside the repo and your scratchpad, and whether you undid it;
- **every decision the user made in this session, with their words** (the coordinator cannot see your `AskUserQuestion` answers);
- when the brief says the user is away, a *Decided while unattended* section;
- open questions for the coordinator.

`relay.py ready` checks the PR body draft for the coordinator, who commits the records folder; you commit neither.

## Off limits

`project.md`'s off-limits paths and the brief's *Other lanes' files*. Needing one of them: block (*Status*).
