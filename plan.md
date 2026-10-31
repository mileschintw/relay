# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** relay-coordinate session in worktree D:\Repos\relay\.claude\worktrees\lane-75-b3c0b3 (branch claude/relay-coordinate-a32074), id local_64ef6796-f1f9-4e2a-afe2-d83002ce2094, mode normal; since 2026-10-31 13:46 -0700, running relay 0.3.1 for the 0.3.2 loop below. Previous coordinator (worktree relay-coordinate-5b7cc3, id local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22) wrote itself out after releasing 0.3.1 (`release` and tag `relay--v0.3.1` = `3703e1f`). `relay.py` is `project.md`'s line (main checkout): fast-forward it after each merge.
- **0.3.2 loop:** round 1 done (#82–#86 merged, PRs #87–#90, #92). Round 2: WFA scan + code-review of `relay--v0.3.1..3efbf76` running; #91 (from lane 83) joins round 2's lanes.
- **Standing instructions for 0.3.2** (user, 2026-10-31 01:54 and 02:00 -0700): 「把目前已經規劃好的項目跟loop作為0.3.2，並且同意自動開issue跟lane跟CI，但我會在新coordinator執行。」 together with the plan it refers to (「…重跑wfa跟code-review loop，作為0.3.2的主要內容。loop到無問題後，我們視為0.3.2可以發布。」). So, without asking again:
  1. File an issue to make the alarm interval a `project.md` setting (an optional `- **Alarm:** <minutes>` line like `CI start wait:`; coordinate's Alarm bullet reads it, default as today), from the user's 「下一個patch讓鬧鐘時數可以調整config」, and run it as a lane.
  2. Loop: a fresh subagent runs a writing-for-agents scan of every agent-facing file under `plugin/`, and another runs `mattpocock-skills:code-review` of `relay--v0.3.1..main` (the method used for 0.3.1: `plan-history.md`, "Lanes 60–64" and "Close-out … 0.3.1"). Verify each finding against the files; file the real ones as issues (Files section included), group them into lanes by file, start the lanes, and open each PR and merge it once CI passes (`relay.py waitchecks`, then `relay.py merge`). Repeat with a new scan once a round's lanes have merged.
  3. When a round finds nothing worth an issue, tell the user 0.3.2 is ready, and release it on their yes (README › Releasing).
  - Stop and ask the user only for a real trade-off or a decision the issues cannot settle. Each lane fixes the small problems it finds in its own files instead of filing new issues; anything outside its files goes in its report for the next scan.
- **Alarm:** `project.md`'s `Alarm: 10` (the user's 10 minutes, 2026-10-31 01:51 「可以就這樣改」, moved there when #82 merged); waiting on CI relies on the background `waitchecks` ending, not the alarm.
- **Unattended log:** none.

## Rulings

none (ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
| 91 | #91 #93 #94 | local_ca5e4485-2d6f-4070-b3e2-964b9154bb1e | done; PR #97, waitchecks running (its note for round 3: *Scheduling* could say "the blocked-by of every issue the lane closes") | — |

All lanes through 75 merged; 0.3.1 released; lane 82 merged → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, close-outs, 0.3.2 round 1).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #91 | 1 | — | after #83 (merged) | relay.py (cmd_merge, check_commands); tests | free |
| #93 | 1 | — | — | relay.py (check_pr_body, cmd_localcheck, docstring exit codes); tests | free |
| #94 | 1 | — | — | relay.py (dependencies); tests; templates/briefs/_template.md (Depends on) | free |

Round 2 (2026-10-31): code-review found 2 (filed as #93, the deny-list one a regression from #83); WFA scan found 5 (filed as #94, #95); all verified by the coordinator against `3efbf76`. Two lanes, no shared files: lane 91 (#91 #93 #94, relay.py) and lane 95 (#95, docs). Both started on the user's "Start them" (2026-10-31).

#91 filed 2026-10-31 by lane 83 from its review (merge after a failed fetch; Windows override written first): joins round 2 once #83 merges. Lane 83's full suite takes ~18 min on this box (1093 s), not 2.

Round 1 (2026-10-31): #83–#86 filed from the WFA scan (8 findings) and code-review (6 findings), all verified by the coordinator against `3703e1f`. Mechanical overlap only: templates/project.md 82 (Alarm) / 83 (checks lines) / 84 (relay.py line); coordinate SKILL.md 82 (Alarm) / 84 (preamble) / 86 (Scheduling, Finishing); work SKILL.md 84 (preamble) / 85 (rest). Lanes 83–86 started on the user's "Start them" (2026-10-31).

## Waiting for the user to be present

none (lanes 91 and 95 started on the user's "Start them", 2026-10-31)

## Waiting for the user's decision

none

## Deadlines

none
