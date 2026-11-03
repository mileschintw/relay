# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title Relay coordination, worktree D:/Repos/relay/.claude/worktrees/lane-114-30073e, id local_f0eb7091-3f4b-4994-afb1-091422a00e8b, mode normal. Took over 2026-11-03 14:17 -0800 from local_41f71e49-… (lane-141-e7f5cd), which wrote itself out 2026-11-03 03:49 -0800 after release 0.3.4 (→ `plan-history.md`, "Rounds 2026-11-02/03 and 0.3.4").
- **Next:** nothing running. Open: #166, #167, #168, #173, #174, all triaged ready-for-agent (#173's triage settled the CI question: windows tests on push to main only; #174 is its follow-up, report a failed push run in `ready`). Round of all five approved 2026-11-03 14:19 -0800, all five started. README's coordinate word-count line: owned by 168; 166 asked to revert its edit (2026-11-03); 174 recounts it last. 167 (PR #175) and 166 (PR #177) merged; 168 (PR #178) merged; PR #179 (174) open, 174 asked (2026-11-03) to merge main after #178 and recount README's coordinate line last. Owner steps: upload `docs/social-preview/social-preview.png` in Settings › General › Social preview.
- **Alarm:** `project.md`'s `Alarm: 10` (the user's 10 minutes, 2026-10-31 01:51 「可以就這樣改」, moved there when #82 merged); waiting on CI relies on the background `waitchecks` ending, not the alarm.
- **Merge right:** 2026-11-03 14:19 -0800, lanes 166, 167, 168, 173, 174: question "這一輪五條 lane（#166、#167、#168、#173、#174）全部平行啟動，並且每條都「開 PR，CI 通過後合併」？", picked "啟動五條並授權合併 (Recommended)". (The 2026-11-03 00:28 round's moved to `plan-history.md`.)
- **Unattended log:** none.

## Rulings


none (ruling 2, no new features during the slimming, ended when #112 closed 2026-11-02 18:50 -0800 → `plan-history.md`; ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`.)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
| 174 | #174 | local_26577313-8008-4c8a-9a1e-27654eb46084 | started | — |

Lane 168 (PR #178) merged 2026-11-03 22:44 UTC → `plan-history.md`. Lane 167 (PR #175) merged 2026-11-03 → `plan-history.md`. Lane 166 (PR #177) merged 2026-11-03 22:36 UTC → `plan-history.md`. Lane 173 (PR #176) merged 2026-11-03 22:35 UTC → `plan-history.md`. Lane 169 (PR #171) merged 2026-11-03 11:42 UTC → `plan-history.md`. Lane 165 (PR #170) merged 2026-11-03 11:15 UTC → `plan-history.md`. Lane 159 (PR #164) merged 2026-11-03 → `plan-history.md`. Lane 161 (PR #163) merged 2026-11-03 08:45 UTC → `plan-history.md`. Lane 146 (PR #162) merged 2026-11-03 → `plan-history.md`. Lane 147 (#147, #151, PR #160) merged 2026-11-03 08:23 UTC → `plan-history.md`. Lane 119 (PR #157) merged 2026-11-03 08:05 UTC → `plan-history.md`. Lane 139 (PR #155) merged 2026-11-03 06:13 UTC → `plan-history.md`. Lane 115 (PR #156) merged 2026-11-03 → `plan-history.md`. Lane 118 (PR #154) merged 2026-11-03 06:00 UTC → `plan-history.md`. Lane 130 (PR #153) merged 2026-11-03 05:48 UTC → `plan-history.md`. Lane 116 (PR #152) merged 2026-11-03 05:36 UTC → `plan-history.md`. Lanes 145 (PR #148), 140 (PR #149) and 114 (PR #150) merged 2026-11-03 05:29 UTC → `plan-history.md`. Lane 141 (#141, #142, PR #143) merged → `plan-history.md`. Lanes 132 (#132, PR #135), 131 (#131, PR #136) 133 (#133, PR #137) and 134 (#134, PR #138) merged → `plan-history.md`. Lane 110 (#110, inventory, no PR) finished and #110 closed on the user's "Reviewed, go ahead" → `plan-history.md`. Lanes 109 (PR #121), 107 (PR #122), 108 (PR #124), 120 (PR #125), 111 (PR #127), 123 (PR #128) and 113 (PR #129) merged → `plan-history.md`, "Lanes 107–111". All lanes through 103 merged; 0.3.2 released → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, 0.3.1 and 0.3.2 rounds, close-outs).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #174 ready: report a failed push run on the default branch | 1 | none | none | relay.py (`cmd_ready`, READY_SECTIONS/HINTS, push-run lookup); tests/test_relay.py; tests' fake_gh.py; coordinate/SKILL.md (handling the Default branch section); coordinate/unattended.md (log a failed push run); GLOSSARY.md (**Push run**) | free |

Refilled 2026-11-03 from `relay.py roadmap`; #173 and #174 triaged ready-for-agent. Mechanical overlaps (different sections, parallel): relay.py docstring (#168 Exit section, #174 ready's section list), coordinate/SKILL.md (#166 Consent › The user's words, #174 its own section), unattended.md (#166 first paragraph, #174 log rule), GLOSSARY.md (#167 CI start wait if any, #174 Push run). #112, #115, #116, #117 list several paths on one bullet, which `parse_files` reads as one path; the paths above are from the issue text.




## Waiting for the user to be present

none


## Waiting for the user's decision

- Owner note (#145, from lane 145): after the merge, on a machine with no GitHub SSH key and no `url.*.insteadOf` override (`git config --show-origin --get-regexp '^url\..*insteadof'` prints nothing; remove the one added for 0.3.3 with `git config --global --unset-all url.https://github.com/.insteadOf`), run `claude plugin marketplace update relay` then `claude plugin update relay@relay`: it should succeed with no `Permission denied (publickey)`. (`reports/145.md`)


- Owner note (#112, from lane 133, C126): for the user's own CLAUDE.md: "On Windows, write a commit message with a double quote in it to a file and use `git commit -F`." (`reports/133.md`)
- Owner note (#112, from lane 132, W33): add to the one project that uses it, in its `project.md` checks or brief template: "A test that needs a pull request (a CI trigger, say): open none; write in the report how to confirm it after the merge." (`reports/132.md`)

## Deadlines

none
