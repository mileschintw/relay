# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title Relay coordination (new account), worktree D:/Repos/relay/.claude/worktrees/lane-102-f7b67c, id 3d27dfcf-f202-480f-9e08-3499b5e1a916, mode normal. Took over 2026-11-03 21:45 -0800 on the user's `/relay:coordinate` after switching accounts; the previous coordinator (local_f0eb7091-3f4b-4994-afb1-091422a00e8b, lane-114-30073e) lost access right after merging #197 and #198, before step 6.
- **Next:** round 195–196 merged; from the 2026-11-03 retrospectives, #200, #207, #209 are open (#210 waits for the user); the other eight were closed as not planned under the slimming rule. Not started. Changes since 0.3.5 (#181–#187, #195, #196) are unreleased; release on the user's word.
- **Alarm:** `project.md`'s `Alarm: 10` (the user's 10 minutes, 2026-10-31 01:51 「可以就這樣改」, moved there when #82 merged); waiting on CI relies on the background `waitchecks` ending, not the alarm.
- **Merge right:** none. (The 2026-11-03 19:57 -0800 round's, lanes 195–196, is in `plan-history.md`.)
- **Unattended log:** none.

## Rulings


none (ruling 2, no new features during the slimming, ended when #112 closed 2026-11-02 18:50 -0800 → `plan-history.md`; ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`.)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
Lanes 195 (PR #197) and 196 (PR #198) merged 2026-11-04 04:25 / 04:23 UTC → `plan-history.md`. Lane 181 (PR #194) merged 2026-11-04 01:31 UTC → `plan-history.md`. Lane 183 (PR #193) merged 2026-11-04 00:31 UTC → `plan-history.md`. Lane 186 (PR #192) merged 2026-11-04 00:30 UTC → `plan-history.md`. Lane 182 (PR #191) merged 2026-11-04 00:29 UTC → `plan-history.md`. Lane 185 (PR #190) merged 2026-11-04 00:29 UTC → `plan-history.md`. Lane 184 (PR #188) and lane 187 (PR #189) merged 2026-11-04 00:20 UTC → `plan-history.md`. Lane 174 (PR #179) merged 2026-11-03 23:09 UTC → `plan-history.md`. Lane 168 (PR #178) merged 2026-11-03 22:44 UTC → `plan-history.md`. Lane 167 (PR #175) merged 2026-11-03 → `plan-history.md`. Lane 166 (PR #177) merged 2026-11-03 22:36 UTC → `plan-history.md`. Lane 173 (PR #176) merged 2026-11-03 22:35 UTC → `plan-history.md`. Lane 169 (PR #171) merged 2026-11-03 11:42 UTC → `plan-history.md`. Lane 165 (PR #170) merged 2026-11-03 11:15 UTC → `plan-history.md`. Lane 159 (PR #164) merged 2026-11-03 → `plan-history.md`. Lane 161 (PR #163) merged 2026-11-03 08:45 UTC → `plan-history.md`. Lane 146 (PR #162) merged 2026-11-03 → `plan-history.md`. Lane 147 (#147, #151, PR #160) merged 2026-11-03 08:23 UTC → `plan-history.md`. Lane 119 (PR #157) merged 2026-11-03 08:05 UTC → `plan-history.md`. Lane 139 (PR #155) merged 2026-11-03 06:13 UTC → `plan-history.md`. Lane 115 (PR #156) merged 2026-11-03 → `plan-history.md`. Lane 118 (PR #154) merged 2026-11-03 06:00 UTC → `plan-history.md`. Lane 130 (PR #153) merged 2026-11-03 05:48 UTC → `plan-history.md`. Lane 116 (PR #152) merged 2026-11-03 05:36 UTC → `plan-history.md`. Lanes 145 (PR #148), 140 (PR #149) and 114 (PR #150) merged 2026-11-03 05:29 UTC → `plan-history.md`. Lane 141 (#141, #142, PR #143) merged → `plan-history.md`. Lanes 132 (#132, PR #135), 131 (#131, PR #136) 133 (#133, PR #137) and 134 (#134, PR #138) merged → `plan-history.md`. Lane 110 (#110, inventory, no PR) finished and #110 closed on the user's "Reviewed, go ahead" → `plan-history.md`. Lanes 109 (PR #121), 107 (PR #122), 108 (PR #124), 120 (PR #125), 111 (PR #127), 123 (PR #128) and 113 (PR #129) merged → `plan-history.md`, "Lanes 107–111". All lanes through 103 merged; 0.3.2 released → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, 0.3.1 and 0.3.2 rounds, close-outs).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #200 | 1 | none | none | relay.py `pushed_head`, `cmd_status`; tests (StatusTests) | free |
| #207 | 1 | none | none | relay.py done-lane `check_pr_body` call; tests (ReadyTests) | free |
| #209 | 1 | none | none | relay.py `cmd_merge`, `wait_push_run`; tests (PushWaitTests); fake_gh.py | free |
| #210 | — | none | none | relay.py new `retire`; coordinate/SKILL.md (Finishing a lane step 6); tests; docs/layout.md | free |

Filled 2026-11-03 from the two retrospectives; on the user's picks the rest were closed as not planned under the slimming rule (#199, #201–#206, #208), #207 narrowed, #210 waits for the user's decision (Order —). Mechanical overlaps (parallel): relay.py (200 pushed_head/cmd_status, 207 done-lane check_pr_body, 209 cmd_merge/wait_push_run); tests/test_relay.py (each its own tests). (Round 195–196's note → `plan-history.md`.)




## Waiting for the user to be present

none


## Waiting for the user's decision

- #210 (`relay.py retire`): keep or close under the slimming rule; the user asked whether repeated Windows script failures count as recurring. Since 2026-11-03.



## Deadlines

none
