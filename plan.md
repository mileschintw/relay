# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** relay-coordinate session in worktree D:\Repos\relay\.claude\worktrees\lane-75-b3c0b3 (branch claude/relay-coordinate-a32074), id local_64ef6796-f1f9-4e2a-afe2-d83002ce2094, mode normal; since 2026-10-31 13:46 -0700, running relay 0.3.1 for the 0.3.2 loop below. Previous coordinator (worktree relay-coordinate-5b7cc3, id local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22) wrote itself out after releasing 0.3.1 (`release` and tag `relay--v0.3.1` = `3703e1f`). `relay.py` is `project.md`'s line (main checkout): fast-forward it after each merge.
- **0.3.2 loop, round 1** (started 2026-10-31 13:50 -0700): item 1 filed as #82, lane 82 started; WFA scan and code-review subagents running.
- **Standing instructions for 0.3.2** (user, 2026-10-31 01:54 and 02:00 -0700): 「把目前已經規劃好的項目跟loop作為0.3.2，並且同意自動開issue跟lane跟CI，但我會在新coordinator執行。」 together with the plan it refers to (「…重跑wfa跟code-review loop，作為0.3.2的主要內容。loop到無問題後，我們視為0.3.2可以發布。」). So, without asking again:
  1. File an issue to make the alarm interval a `project.md` setting (an optional `- **Alarm:** <minutes>` line like `CI start wait:`; coordinate's Alarm bullet reads it, default as today), from the user's 「下一個patch讓鬧鐘時數可以調整config」, and run it as a lane.
  2. Loop: a fresh subagent runs a writing-for-agents scan of every agent-facing file under `plugin/`, and another runs `mattpocock-skills:code-review` of `relay--v0.3.1..main` (the method used for 0.3.1: `plan-history.md`, "Lanes 60–64" and "Close-out … 0.3.1"). Verify each finding against the files; file the real ones as issues (Files section included), group them into lanes by file, start the lanes, and open each PR and merge it once CI passes (`relay.py waitchecks`, then `relay.py merge`). Repeat with a new scan once a round's lanes have merged.
  3. When a round finds nothing worth an issue, tell the user 0.3.2 is ready, and release it on their yes (README › Releasing).
  - Stop and ask the user only for a real trade-off or a decision the issues cannot settle. Each lane fixes the small problems it finds in its own files instead of filing new issues; anything outside its files goes in its report for the next scan.
- **Alarm:** 10 minutes while a lane runs (user, 2026-10-31 01:51: 「可以就這樣改」, since a warm-cache wake is cheap); waiting on CI relies on the background `waitchecks` ending, not the alarm. Ends when the configurable-alarm issue (item 1 above) merges: then use the `project.md` value.
- **Unattended log:** none.

## Rulings

none (ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
| 82 | #82 | local_fb03bf35-40b4-45d4-aef1-a1d3c50f221a (landed in archived lane 74's folder D:\Repos\relay\.claude\worktrees\lane-74-56fc4d, on its own branch claude/lane-82-62c59f) | started | — |

All lanes through 75 merged; 0.3.1 released → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, close-outs).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #82 | 1 | — | — | coordinate SKILL.md (Alarm bullet); setup templates/project.md (Alarm line); GLOSSARY.md (Alarm entry) | free |
| #83 | 1 | — | — | relay.py (check_commands, check_pr_body, cmd_status, conflicts); tests; templates/project.md (checks lines) | free |
| #84 | 1 | — | — | templates/project.md (relay.py line); setup SKILL.md (step 2); coordinate and work SKILL.md (preamble relay.py sentence) | free |
| #85 | 1 | — | — | unattended.md (scope, worker paragraph); work SKILL.md (Precedence, Workflow, Status); templates/plan.md (Kind) | free |
| #86 | 1 | — | — | coordinate SKILL.md (Scheduling first bullet; Finishing steps 4, 7) | free |

Round 1 (2026-10-31): #83–#86 filed from the WFA scan (8 findings) and code-review (6 findings), all verified by the coordinator against `3703e1f`. Mechanical overlap only: templates/project.md 82 (Alarm) / 83 (checks lines) / 84 (relay.py line); coordinate SKILL.md 82 (Alarm) / 84 (preamble) / 86 (Scheduling, Finishing); work SKILL.md 84 (preamble) / 85 (rest). Briefs written; sessions not yet started: the app refuses starts outside a turn the user typed.

## Waiting for the user to be present

- Since 2026-10-31 13:58 -0700: any message from the user here, so lanes 83–86 can start (already covered by the standing 0.3.2 go-ahead; the app only starts sessions in a turn the user typed).

## Waiting for the user's decision

none

## Deadlines

none
