# Plan

Last updated: 2026-10-30 16:08 -0700

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title unknown (relay-coordinate session), worktree D:\Repos\relay\.claude\worktrees\relay-coordinate-5b7cc3, id local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22, mode normal.
- **Standing instructions:** none.
- **Unattended log:** none.

## Rulings

none

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
| 1 | #1 | local_1579b864-86a9-486d-90c2-506674ab72a7 (claude/lane-1-6a0c93) | started | |
| 7 | #7 | local_96015864-484e-43fd-ba63-f56257c25613 (claude/lane-7-51e899) | started | |
| 8 | #8 | local_9e8221b7-77e6-4302-86d2-c4718149667c (claude/lane-8-2f7128) | started | |
| 9 | #9 | local_a3b2b8ca-87e8-4f47-aceb-469820317bbd (claude/lane-9-0742ae) | started | |
| 10 | #10 | local_7c15cfb3-aec1-478e-94a2-d299ce83092c (claude/lane-10-700d4c) | started | |
| 2 | #2 | local_fb37449e-58c9-49eb-b7f4-6878eebd3515 (claude/lane-2-ccd448) | started, parked | GO #2 after #1 merges |
| 3 | #3 | local_9bd0484c-821d-4349-9663-678666c9e033 (claude/lane-3-af9107) | started, parked | GO #3 after #1 merges |

Started 2026-10-30 16:29 -0700 on the user's "Start wave 1" (16:28).

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
| #11 Deny list `none.` read as a path | 1 (no lane yet) | none | none | relay.py (`deny_patterns`), test_relay.py | free |

Mechanical overlap: `plugin/tools/relay.py` (docstring, `cmd_ready` sections) and `tests/test_relay.py` with #1, #2, #3, #7, #9; `tests/fake_gh.py` with #1, #2, #3, #7; `plugin/GLOSSARY.md` with #1, #2, #3; `setup/templates/plan.md` #1 (Roadmap Kind) and #9 (Last updated line); `app-limits.md` #8 and, only if it adds a note-delivery line, #10. #8 owns the archive rule; #3's close-out points at `app-limits.md` (comment on #3). Triage of #7–#10: `decisions-2026-10-30.md`.

## Waiting for the user to be present

none

## Waiting for the user's decision

- PR-and-merge for lanes 8 and 10 (both Ready for PR); since 2026-10-30 16:40 -0700.
- Records workaround for #11: `project.md` Deny list changed from `none.` to `none` (same meaning) so `ready` stops failing every done lane; done by the coordinator 2026-10-30 16:40 -0700, tell the user.
- Archive the finished triage session triage-7-10 (local_25b74a50-b6f9-40d5-86ad-82eae30d7c7f)? Its results are in `decisions-2026-10-30.md`.

## Deadlines

none
