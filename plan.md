# Plan

Last updated: 2026-10-30 16:08 -0700

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title unknown (relay-coordinate session), worktree D:\Repos\relay\.claude\worktrees\relay-coordinate-5b7cc3, id unknown, mode normal.
- **Standing instructions:** none.
- **Unattended log:** none.

## Rulings

none

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release) or `limited: <what>`.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #1 Treat issues with sub-issues as parents | 1 | none | none | relay.py (`ready` parents), fake_gh.py, test_relay.py, coordinate SKILL.md (First turn step 3; Scheduling frontier bullet), setup templates/plan.md, GLOSSARY.md (**Parent**) | free |
| #2 Issue-body `## Files` section | 2 | none | after #1, coordinate SKILL.md › First turn step 3 | relay.py (new roadmap command), fake_gh.py, test_relay.py, coordinate SKILL.md (First turn step 3; Starting a lane step 1), setup SKILL.md, README.md (Layout row), GLOSSARY.md | free |
| #3 Hand back when the roadmap empties; owner notes | 2 | #1 | none | relay.py (`ready` owner notes), fake_gh.py, test_relay.py, coordinate SKILL.md (First turn step 5; Finishing a lane step 6), GLOSSARY.md (owner-note marker) | free |
| #7 Local checks fallback (`relay.py localcheck`) | 1 | none | none | relay.py (`localcheck`; `checks_state`/`ready_done` billing case), fake_gh.py (`pr comment`, billing rollup), test_relay.py, coordinate SKILL.md (Finishing a lane step 4), setup templates/project.md (Local checks line) | free |
| #8 Check every session's cwd; never archive one sharing the coordinator's folder | 1 | none | none | coordinate app-limits.md (the two rules; intro line), coordinate SKILL.md (Starting a lane step 4; Consent archive bullet) | free |
| #9 Drop Last updated; `ready` warns on control characters | 1 | none | none | setup templates/plan.md (Last updated line), coordinate SKILL.md (Plan), relay.py (`ready` encoding check, before any other read), test_relay.py | free |
| #10 Quiet notes for unchanged turn ends | 1 | none | none | coordinate SKILL.md (Following progress), work SKILL.md (Status) | free |

Mechanical overlap: `plugin/tools/relay.py` (docstring, `cmd_ready` sections) and `tests/test_relay.py` with #1, #2, #3, #7, #9; `tests/fake_gh.py` with #1, #2, #3, #7; `plugin/GLOSSARY.md` with #1, #2, #3; `setup/templates/plan.md` #1 (Roadmap Kind) and #9 (Last updated line); `app-limits.md` #8 and, only if it adds a note-delivery line, #10. #8 owns the archive rule; #3's close-out points at `app-limits.md` (comment on #3). Triage of #7–#10: `decisions-2026-10-30.md`.

## Waiting for the user to be present

none

## Waiting for the user's decision

- Go-ahead for wave 1: start lanes #1, #7, #8, #9, #10 now, with #2 and #3 parked until #1 merges; since 2026-10-30 16:08 -0700 (wave widened after triage).
- Archive the finished triage session triage-7-10 (local_25b74a50-b6f9-40d5-86ad-82eae30d7c7f)? Its results are in `decisions-2026-10-30.md`.

## Deadlines

none
