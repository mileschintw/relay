# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title Relay coordination, worktree D:/Repos/relay/.claude/worktrees/lane-114-30073e, id local_f0eb7091-3f4b-4994-afb1-091422a00e8b, back 2026-11-03 19:56 -0800 on the user's `/relay:coordinate` for round 195–196. Mode: normal.
- **Next:** round 195–196 running (started 2026-11-03 19:57 -0800 on the user's yes). Changes since 0.3.5 (#181–#187) are unreleased; release on the user's word. Owner steps: upload `docs/social-preview/social-preview.png` in Settings › General › Social preview.
- **Alarm:** `project.md`'s `Alarm: 10` (the user's 10 minutes, 2026-10-31 01:51 「可以就這樣改」, moved there when #82 merged); waiting on CI relies on the background `waitchecks` ending, not the alarm.
- **Merge right:** 2026-11-03 19:57 -0800, lanes 195, 196: asked "這一輪每條 lane 都「開 PR，CI 通過後合併」嗎？", picked 「開 PR，CI 通過後合併 (Recommended)」. (The 2026-11-03 16:06 -0800 round's, lanes 181–187, is in `plan-history.md`.)
- **Unattended log:** none.

## Rulings


none (ruling 2, no new features during the slimming, ended when #112 closed 2026-11-02 18:50 -0800 → `plan-history.md`; ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`.)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
| 195 | #195 | local_fca49d50-7f32-4d95-8554-ea6adc8981a7 (landed in archived lane 134's folder D:/Repos/relay/.claude/worktrees/lane-134-eb4fc2, on its own branch claude/lane-195-582e1a) | started | |
| 196 | #196 | local_a527b888-8def-4411-942a-1902e0507e5b (D:/Repos/relay/.claude/worktrees/new-session-208f95, branch claude/lane-196-cdf218) | started | |

Lane 181 (PR #194) merged 2026-11-04 01:31 UTC → `plan-history.md`. Lane 183 (PR #193) merged 2026-11-04 00:31 UTC → `plan-history.md`. Lane 186 (PR #192) merged 2026-11-04 00:30 UTC → `plan-history.md`. Lane 182 (PR #191) merged 2026-11-04 00:29 UTC → `plan-history.md`. Lane 185 (PR #190) merged 2026-11-04 00:29 UTC → `plan-history.md`. Lane 184 (PR #188) and lane 187 (PR #189) merged 2026-11-04 00:20 UTC → `plan-history.md`. Lane 174 (PR #179) merged 2026-11-03 23:09 UTC → `plan-history.md`. Lane 168 (PR #178) merged 2026-11-03 22:44 UTC → `plan-history.md`. Lane 167 (PR #175) merged 2026-11-03 → `plan-history.md`. Lane 166 (PR #177) merged 2026-11-03 22:36 UTC → `plan-history.md`. Lane 173 (PR #176) merged 2026-11-03 22:35 UTC → `plan-history.md`. Lane 169 (PR #171) merged 2026-11-03 11:42 UTC → `plan-history.md`. Lane 165 (PR #170) merged 2026-11-03 11:15 UTC → `plan-history.md`. Lane 159 (PR #164) merged 2026-11-03 → `plan-history.md`. Lane 161 (PR #163) merged 2026-11-03 08:45 UTC → `plan-history.md`. Lane 146 (PR #162) merged 2026-11-03 → `plan-history.md`. Lane 147 (#147, #151, PR #160) merged 2026-11-03 08:23 UTC → `plan-history.md`. Lane 119 (PR #157) merged 2026-11-03 08:05 UTC → `plan-history.md`. Lane 139 (PR #155) merged 2026-11-03 06:13 UTC → `plan-history.md`. Lane 115 (PR #156) merged 2026-11-03 → `plan-history.md`. Lane 118 (PR #154) merged 2026-11-03 06:00 UTC → `plan-history.md`. Lane 130 (PR #153) merged 2026-11-03 05:48 UTC → `plan-history.md`. Lane 116 (PR #152) merged 2026-11-03 05:36 UTC → `plan-history.md`. Lanes 145 (PR #148), 140 (PR #149) and 114 (PR #150) merged 2026-11-03 05:29 UTC → `plan-history.md`. Lane 141 (#141, #142, PR #143) merged → `plan-history.md`. Lanes 132 (#132, PR #135), 131 (#131, PR #136) 133 (#133, PR #137) and 134 (#134, PR #138) merged → `plan-history.md`. Lane 110 (#110, inventory, no PR) finished and #110 closed on the user's "Reviewed, go ahead" → `plan-history.md`. Lanes 109 (PR #121), 107 (PR #122), 108 (PR #124), 120 (PR #125), 111 (PR #127), 123 (PR #128) and 113 (PR #129) merged → `plan-history.md`, "Lanes 107–111". All lanes through 103 merged; 0.3.2 released → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, 0.3.1 and 0.3.2 rounds, close-outs).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #195 | 1 | none | none | work/SKILL.md (step 1, Catching up); relay.py `cmd_status`; tests | free |
| #196 | 1 | none | none | relay.py `cmd_waitchecks`; tests; fake_gh.py; docs/releasing.md step 2 | free |

Filled 2026-11-03 from the round 181–187 retrospective. Mechanical overlaps (parallel): relay.py (195 `cmd_status`, 196 `cmd_waitchecks`); tests/test_relay.py (each its own tests).




## Waiting for the user to be present

none


## Waiting for the user's decision

- Owner note (#145, from lane 145): after the merge, on a machine with no GitHub SSH key and no `url.*.insteadOf` override (`git config --show-origin --get-regexp '^url\..*insteadof'` prints nothing; remove the one added for 0.3.3 with `git config --global --unset-all url.https://github.com/.insteadOf`), run `claude plugin marketplace update relay` then `claude plugin update relay@relay`: it should succeed with no `Permission denied (publickey)`. (`reports/145.md`)


- Owner note (#112, from lane 133, C126): for the user's own CLAUDE.md: "On Windows, write a commit message with a double quote in it to a file and use `git commit -F`." (`reports/133.md`)
- Owner note (#112, from lane 132, W33): add to the one project that uses it, in its `project.md` checks or brief template: "A test that needs a pull request (a CI trigger, say): open none; write in the report how to confirm it after the merge." (`reports/132.md`)

## Deadlines

none
