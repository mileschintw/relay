# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title unknown, worktree D:\Repos\relay\.claude\worktrees\new-session-208f95, id local_cac5e599-046a-4d94-801f-10187aae7a59, mode normal. Since 2026-11-02 13:01 -0800, branch `claude/relay-coordinate-f026f5`. The previous coordinator (local_41066841-894c-4b9c-8f9e-2ce0ab11a088, folder lane-102-f7b67c) wrote itself out on 2026-11-02 after the round of lanes 107–123 (→ `plan-history.md`, "Lanes 107–111"; its 7 lane sessions archived, scratchpads in `snapshot/`). The next coordinator starts with `/relay:coordinate` in a new desktop-app session. `relay.py` is `project.md`'s line (main checkout, at `1477016`): fast-forward it after each merge.
- **Next:** release 0.3.3 (user: 「release 0.3.3 patch，然後安裝到這個relay自己的repo裡，接著收尾」). #141 merged (PR #143, 1477016) after the coordinator's re-review. Version bump PR #144 (branch `release-0.3.3`) waiting on CI; then merge it, `git push origin main:release`, tag `relay--v0.3.3`, update the local-scope install in D:\Repos\relay, then close out. #114–#119, #130, #139, #140 wait for the user's triage.
- **Alarm:** `project.md`'s `Alarm: 10` (the user's 10 minutes, 2026-10-31 01:51 「可以就這樣改」, moved there when #82 merged); waiting on CI relies on the background `waitchecks` ending, not the alarm.
- **Unattended log:** none.

## Rulings


none (ruling 2, no new features during the slimming, ended when #112 closed 2026-11-02 18:50 -0800 → `plan-history.md`; ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`.)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|

Lane 141 (#141, #142, PR #143) merged → `plan-history.md`. Lanes 132 (#132, PR #135), 131 (#131, PR #136) 133 (#133, PR #137) and 134 (#134, PR #138) merged → `plan-history.md`. Lane 110 (#110, inventory, no PR) finished and #110 closed on the user's "Reviewed, go ahead" → `plan-history.md`. Lanes 109 (PR #121), 107 (PR #122), 108 (PR #124), 120 (PR #125), 111 (PR #127), 123 (PR #128) and 113 (PR #129) merged → `plan-history.md`, "Lanes 107–111". All lanes through 103 merged; 0.3.2 released → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, 0.3.1 and 0.3.2 rounds, close-outs).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #114 Merge right scoped to a round | — | #112 (closed) | none | coordinate/SKILL.md (Consent, Finishing a lane); setup/templates/plan.md (Handover) | needs-triage |
| #115 Spare-worker pool for lanes started while the user is away | — | #112 (closed) | none | coordinate/SKILL.md (Starting a lane); unattended.md; work/SKILL.md; relay.py (ready); tests | needs-triage |
| #116 Run, audit and spare lane kinds; who holds the main checkout | — | #112 (closed) | none | relay.py (ready); tests; setup/templates/plan.md (Now); coordinate/SKILL.md; GLOSSARY.md (Kind) | needs-triage |
| #117 Spend ceilings and authority in the plan | — | #112 (closed) | none | setup/templates/plan.md; unattended.md; coordinate/SKILL.md (Consent) | needs-triage |
| #118 Faster ready, and partial output when a lookup times out | — | #112 (closed) | none | relay.py (cmd_ready); tests | needs-triage |
| #119 README as a one-page product page | — | #112 (closed) | none | README.md; New docs/layout.md; New docs/releasing.md; docs/getting-started.md | needs-triage |
| #130 relay.py hints that need new behaviour (C104 draft changed after PR; F16 workflow on: lines) | — | #112 (closed) | none | relay.py (cmd_ready, cmd_waitchecks); tests; coordinate/SKILL.md (Finishing a lane); ci-fallbacks.md (Checks not started) | needs-triage |
| #139 ready: check every committed records file against the deny list (found in the #112 retro) | — | none | none | relay.py (cmd_ready, deny-list checks); tests; coordinate/SKILL.md (Plan: A `Records:` warning) | needs-triage |
| #140 Alarm only while a worker can move without the user (from the alarm grilling; completes #48) | — | none | none | coordinate/SKILL.md (Following progress: Alarm); GLOSSARY.md (Alarm); unattended.md (The round ends) | needs-triage |

Filled 2026-11-02 from `relay.py roadmap`. #112, #115, #116, #117 list several paths on one bullet, which `parse_files` reads as one path; the paths above are from the issue text.




## Waiting for the user to be present

none


## Waiting for the user's decision

- Owner note (#112, from lane 133, C126): for the user's own CLAUDE.md: "On Windows, write a commit message with a double quote in it to a file and use `git commit -F`." (`reports/133.md`)
- Owner note (#112, from lane 132, W33): add to the one project that uses it, in its `project.md` checks or brief template: "A test that needs a pull request (a CI trigger, say): open none; write in the report how to confirm it after the merge." (`reports/132.md`)
- Since 2026-11-02 00:37 -0800: triage #114–#119, #130, #139 and #140 (labelled needs-triage, "not scheduled until triaged"; #112 closed, so none is blocked any more).

## Deadlines

none
