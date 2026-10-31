# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title unknown (relay-coordinate session), worktree D:\Repos\relay\.claude\worktrees\relay-coordinate-5b7cc3, id local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22, mode normal. Runs relay 0.2.0 (released by 2026-10-30 17:33 -0700 on the user's 「把wave1結束的版本發成0.2.0」, PR #32, tag `relay--v0.2.0` = `fa817ff`): skills and `relay.py` at `C:\Users\user3\.claude\plugins\cache\relay\relay\0.2.0\`; this session's Skill tool may still load 0.1.0 until a restart, so read the 0.2.0 files by path.
- **Standing instructions:** none. Merge right: per lane, on the user's yes to "open the PR and merge once CI passes" (CI exists since #16).
- **Unattended log:** none.

## Rulings

none (ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
| 24 | #24 | local_8223afdd-4397-49a4-9540-378b5018e7e2 (worktree lane-24-228c28) | started | — |
| 25 | #25 | local_a390b9b2-f8f2-4f4f-a349-7f44774378c1 (worktree lane-25-cf22e5) | started | — |
| 26 | #26 | local_49c6f09b-66aa-40be-bb3d-c809c925fb34 (worktree lane-26-a6b2f5) | started | — |
| 27 | #27 | local_c8055d4a-f2ac-47c7-abda-54f081a0a26d (worktree lane-27-9a7274) | started | — |
| 28 | #28 | local_644f77a7-f3ea-412a-8136-9f6d0c0c1b08 (worktree lane-28-272abc) | started | — |
| 29 | #29 | local_c0e33f80-d81b-42f9-b22f-622232add8bb (worktree lane-29-ea9758) | started | — |
| 30 | #30 | local_4a03addc-5329-4b11-a472-c53ee8e846e3 (worktree lane-30-fd4564) | started | — |
| 31 | #31 | local_ada54677-b465-4cc6-b678-479d0e40935c (worktree lane-31-b7c2a2) | started | #28 merges (GO #31) |

Wave 2 started 2026-10-30 17:37 -0700 on the user's 「開始wave2」; every lane in its own worktree (checked with list_sessions). Wave 1: all lanes merged: 1, 2, 3, 7, 8, 9, 10, 11, 12, 16 → `plan-history.md`.

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release) or `limited: <what>`.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #24 Coordinate relay with the checkout's relay.py | 1 | none | none | coordinate SKILL.md (top `relay.py` line), work SKILL.md (intro `relay.py` sentence), setup templates/project.md (optional relay.py line) | free |
| #25 Handle a repo with no CI configured | 1 | none | none | relay.py (`checks_state`/`ready_done` no-workflow case), fake_gh.py, test_relay.py, coordinate SKILL.md (Finishing a lane step 4), setup SKILL.md (CI check and offer) | free |
| #26 Records `.gitattributes` | 1 | none | none | New: setup templates/gitattributes; setup SKILL.md (copy step, `ls-tree` check); README.md (Layout row if needed) | free |
| #27 One `ready` section per line | 1 | none | none | relay.py (`cmd_ready` section list) | free |
| #28 plan-history append, oldest first | 1 | none | none | setup templates/plan-history.md (header), coordinate SKILL.md (Plan, move-to-history line) | free |
| #29 A starting session's cwd is not final; tidy the rule | 1 | none | none | coordinate app-limits.md (Session folders, check-where-it-landed rule), coordinate unattended.md (cwd-check sentence) | free |
| #30 Check the tracker before reporting outside the lane | 1 | none | none | work SKILL.md (raising problems outside the lane) | free |
| #31 Say what to do with a `ready` Records warning | 2 | none | after #28, coordinate SKILL.md › Plan | coordinate SKILL.md (Plan: Records warning line) | free |

Filed 2026-10-30 from the coordinator's retro on the user's 「7點都能file」. Mechanical overlap: relay.py #25/#27 (different functions; #27 touches only the section list); setup SKILL.md #25 (new CI step) / #26 (copy step and check); coordinate SKILL.md #24 (top line) / #25 (step 4) / #28 and #31 (Plan: same-section wait, #31 after #28); work SKILL.md #24 (intro) / #30. #29 was widened on the user's 「把值得作的三項開issue或更新現有issue」 with lane 8's two notes; #31 filed the same time (lane 9's note). Not filed, by recommendation: unpinned claude-code in CI, stall detection. Triage of #7–#10: `decisions-2026-10-30.md`.

## Waiting for the user to be present

none

## Waiting for the user's decision

- Close-out: archive finished sessions triage-7-10 (local_25b74a50-b6f9-40d5-86ad-82eae30d7c7f), lane-1, -2, -3, -7, -8, -9, -10, -11, -12, -16 (all merged; none shares the coordinator's folder); since 2026-10-30 16:40 -0700.

## Deadlines

none
