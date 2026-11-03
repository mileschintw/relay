# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title Relay coordination, worktree D:/Repos/relay/.claude/worktrees/lane-141-e7f5cd, id local_41f71e49-d203-4671-9234-61ad31a7903f, mode normal. Branch `claude/relay-coordinate-821ea1`; took over 2026-11-02 20:34 -0800. The previous coordinator (local_cac5e599-046a-4d94-801f-10187aae7a59, folder new-session-208f95) wrote itself out 2026-11-02 20:31 -0800 after the #112 slimming round and release 0.3.3 (→ `plan-history.md`, "Round #110–#112 and 0.3.3"). `relay.py` is `project.md`'s line (main checkout, at `8abd5c8`): fast-forward it after each merge.
- **Next:** round 2026-11-02 started 20:49 -0800 (user: start this round): follow the lanes; GO #119 after #145 merges, GO #115 after #116 merges. 0.3.3 is released (tag `relay--v0.3.3`, release at 8abd5c8) and installed at local scope in D:\Repos\relay; sessions there pick it up on restart. #145: the user approved the marketplace.json change (url to HTTPS only) at triage, 2026-11-02. `ready` keeps one Inconsistent line for lane 110 (no PR by design; its status file stays as the record).
- **Alarm:** `project.md`'s `Alarm: 10` (the user's 10 minutes, 2026-10-31 01:51 「可以就這樣改」, moved there when #82 merged); waiting on CI relies on the background `waitchecks` ending, not the alarm.
- **Unattended log:** none.

## Rulings


none (ruling 2, no new features during the slimming, ended when #112 closed 2026-11-02 18:50 -0800 → `plan-history.md`; ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`.)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
| 145 | #145 | local_1ac00200-a9a1-4a09-92ab-6fb646392a2f (folder lane-134-eb4fc2, an archived lane's, on its own branch claude/lane-145-6a04eb) | review | — |
| 140 | #140 | local_9ddbb370-6eb0-4ec5-8755-a4c2d0340c77 (folder lane-133-1fd07d, an archived lane's, on its own branch claude/lane-140-4d9a51) | review | — |
| 139 | #139 | local_910e2d1e-d6e1-4dcb-9637-b3d4fc1f2c69 (folder lane-132-1ec78c, an archived lane's, on its own branch claude/lane-139-e5e149) | review | — |
| 118 | #118 | local_7d884ee0-a5da-43f1-afe3-c9263d614127 | started | — |
| 114 | #114 | local_a6578565-d746-41b0-af40-71c7c25aada2 | review | — |
| 116 | #116 | local_1298b089-e1cd-43bc-a2a2-b6afa0824412 | review | — |
| 130 | #130 | local_e3f15009-bb01-44bc-90b3-a31319d90666 | review | — |
| 119 | #119 | local_be67e121-5073-463c-9e5b-f85be961719e | parked | #145 merged |
| 115 | #115 | local_d99544c7-e9aa-457e-b591-c0159b0b23ec | parked | #116 merged |

Lane 141 (#141, #142, PR #143) merged → `plan-history.md`. Lanes 132 (#132, PR #135), 131 (#131, PR #136) 133 (#133, PR #137) and 134 (#134, PR #138) merged → `plan-history.md`. Lane 110 (#110, inventory, no PR) finished and #110 closed on the user's "Reviewed, go ahead" → `plan-history.md`. Lanes 109 (PR #121), 107 (PR #122), 108 (PR #124), 120 (PR #125), 111 (PR #127), 123 (PR #128) and 113 (PR #129) merged → `plan-history.md`, "Lanes 107–111". All lanes through 103 merged; 0.3.2 released → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, 0.3.1 and 0.3.2 rounds, close-outs).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #114 Merge right scoped to a round | 1 | #112 (closed) | none | coordinate/SKILL.md (Consent, Finishing a lane); setup/templates/plan.md (Handover) | free |
| #115 Spare-worker pool for lanes started while the user is away | 2 | #112 (closed) | after #116, relay.py ready (spare kind) | coordinate/SKILL.md (Starting a lane); unattended.md; work/SKILL.md; relay.py (ready); tests | free |
| #116 Run, audit and spare lane kinds; who holds the main checkout | 1 | #112 (closed) | none | relay.py (ready); tests; setup/templates/plan.md (Now); coordinate/SKILL.md; GLOSSARY.md (Kind) | free |
| #118 Faster ready, and partial output when a lookup times out | 1 | #112 (closed) | none | relay.py (cmd_ready); tests | free |
| #119 README as a one-page product page | 2 | #112 (closed) | after #145, README.md Install | README.md; New docs/layout.md; New docs/releasing.md; docs/getting-started.md | free |
| #130 relay.py hints that need new behaviour (C104 draft changed after PR; F16 workflow on: lines) | 1 | #112 (closed) | none | relay.py (cmd_ready, cmd_waitchecks, merge arg parsing); tests; coordinate/SKILL.md (Finishing a lane); ci-fallbacks.md (Checks not started) | free |
| #139 ready: check every committed records file against the deny list (found in the #112 retro) | 1 | none | none | relay.py (cmd_ready, deny-list checks); tests; coordinate/SKILL.md (Plan: A `Records:` warning) | free |
| #140 Alarm only while a worker can move without the user (from the alarm grilling; completes #48) | 1 | none | none | coordinate/SKILL.md (Following progress: Alarm); GLOSSARY.md (Alarm); unattended.md (The round ends) | free |
| #145 marketplace.json: clone the plugin over HTTPS, not SSH (found installing 0.3.3) | 1 | none | none | .claude-plugin/marketplace.json; README.md (Install) | limited: marketplace.json change approved 2026-11-02 (url to HTTPS only) |

Filled 2026-11-02 from `relay.py roadmap`. #112, #115, #116, #117 list several paths on one bullet, which `parse_files` reads as one path; the paths above are from the issue text.




## Waiting for the user to be present

none


## Waiting for the user's decision

- Owner note (#112, from lane 133, C126): for the user's own CLAUDE.md: "On Windows, write a commit message with a double quote in it to a file and use `git commit -F`." (`reports/133.md`)
- Owner note (#112, from lane 132, W33): add to the one project that uses it, in its `project.md` checks or brief template: "A test that needs a pull request (a CI trigger, say): open none; write in the report how to confirm it after the merge." (`reports/132.md`)

## Deadlines

none
