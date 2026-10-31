# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title unknown (relay-coordinate session), worktree D:\Repos\relay\.claude\worktrees\relay-coordinate-5b7cc3, id local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22, mode normal.
- **Standing instructions:** none.
- **Unattended log:** none.

## Rulings

none (ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|

All lanes merged: 1, 2, 3, 7, 8, 9, 10, 11, 12, 16 → `plan-history.md`.

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release) or `limited: <what>`.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #24 Coordinate relay with the checkout's relay.py | 1 | none | none | coordinate SKILL.md (top `relay.py` line), work SKILL.md (intro `relay.py` sentence), setup templates/project.md (optional relay.py line) | free |
| #25 Handle a repo with no CI configured | 1 | none | none | relay.py (`checks_state`/`ready_done` no-workflow case), fake_gh.py, test_relay.py, coordinate SKILL.md (Finishing a lane step 4), setup SKILL.md (CI check and offer) | free |
| #26 Records `.gitattributes` | 1 | none | none | New: setup templates/gitattributes; setup SKILL.md (copy step, `ls-tree` check); README.md (Layout row if needed) | free |
| #27 One `ready` section per line | 1 | none | none | relay.py (`cmd_ready` section list) | free |
| #28 plan-history append, oldest first | 1 | none | none | setup templates/plan-history.md (header), coordinate SKILL.md (Plan, move-to-history line) | free |
| #29 A starting session's cwd is not final | 1 | none | none | coordinate app-limits.md (Session folders, check-where-it-landed rule) | free |
| #30 Check the tracker before reporting outside the lane | 1 | none | none | work SKILL.md (raising problems outside the lane) | free |

Filed 2026-10-30 from the coordinator's retro on the user's 「7點都能file」. Mechanical overlap: relay.py #25/#27 (different functions; #27 touches only the section list); setup SKILL.md #25 (new CI step) / #26 (copy step and check); coordinate SKILL.md #24 (top line) / #25 (step 4) / #28 (Plan); work SKILL.md #24 (intro) / #30. No same-section waits. Triage of #7–#10: `decisions-2026-10-30.md`.

## Waiting for the user to be present

none

## Waiting for the user's decision

- Close-out: archive finished sessions triage-7-10 (local_25b74a50-b6f9-40d5-86ad-82eae30d7c7f), lane-1, -2, -3, -7, -8, -9, -10, -11, -12, -16 (all merged; none shares the coordinator's folder); since 2026-10-30 16:40 -0700.
- Start wave 2 (#24–#30, all Order 1); since 2026-10-30 17:25 -0700.
- Small worker notes not filed yet (coordinator's recommendation given 17:25): file or drop; since 2026-10-30 17:18 -0700.
- Release: none of this is released yet (the installed relay plugin is 0.1.0); README › Releasing, on the user's yes; since 2026-10-30 17:18 -0700.

## Deadlines

none
