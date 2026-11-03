# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** the session in worktree D:\Repos\relay\.claude\worktrees\new-session-208f95 (branch `claude/relay-coordinate-f026f5`), since 2026-11-02 13:01 -0800; mode normal. The previous coordinator (worktree D:\Repos\relay\.claude\worktrees\lane-102-f7b67c, id local_41066841-894c-4b9c-8f9e-2ce0ab11a088) wrote itself out on 2026-11-02 after the round of lanes 107–123 (→ `plan-history.md`, "Lanes 107–111"; its 7 lane sessions archived, scratchpads in `snapshot/`). The next coordinator starts with `/relay:coordinate` in a new desktop-app session. `relay.py` is `project.md`'s line (main checkout, at `d0d553f`): fast-forward it after each merge.
- **Next:** #112 runs as lane 134 (C2) now (131, 132, 133 merged); then ask the user before closing parent #112. #114–#119 and #130 triage waits on the user (all blocked by #112). The compact hook (#111) is on main but reaches the user only with the next release (installed relay is 0.3.2); a release runs `project.md`'s one review pass first. Records `compact-instruction.md` is no longer used by the new flow; kept until the user decides.
- **Alarm:** `project.md`'s `Alarm: 10` (the user's 10 minutes, 2026-10-31 01:51 「可以就這樣改」, moved there when #82 merged); waiting on CI relies on the background `waitchecks` ending, not the alarm.
- **Unattended log:** none.

## Rulings

- **Ruling 2 — no new features during the slimming** (user, 2026-11-02 16:39 -0800: 「我們目前階段盤點以及實作時，如果遇到要做新功能，應該移動到跟其他後續issue一起」). While #110 (inventory) and #112 (slimming) run, any new behaviour (new code in `relay.py`, a new check, a rule with no existing text behind it) is not done in those lanes: it becomes its own issue, scheduled with the backlog (#114–#119) after #112. Ends when #112 closes. Applied on the user's "Yes, all four": #112's body gains a *No new behaviour* paragraph; C104 and F16 moved to new issue #130; #114–#118 and #130 blocked by #112 on GitHub; lane 110 asked to move C104/F16 out of batch H and re-scan for other new-behaviour rows.

(Ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`.)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
| 134 | #134 | local_199699b7-06a0-4986-b24b-d069ebe14bb8 (lane-134-eb4fc2, `claude/lane-134-eb4fc2`) | review | — |

Lanes 132 (#132, PR #135), 131 (#131, PR #136) and 133 (#133, PR #137) merged → `plan-history.md`. Lane 110 (#110, inventory, no PR) finished and #110 closed on the user's "Reviewed, go ahead" → `plan-history.md`. Lanes 109 (PR #121), 107 (PR #122), 108 (PR #124), 120 (PR #125), 111 (PR #127), 123 (PR #128) and 113 (PR #129) merged → `plan-history.md`, "Lanes 107–111". All lanes through 103 merged; 0.3.2 released → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, 0.3.1 and 0.3.2 rounds, close-outs).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #112 Slim the skills by the reviewed inventory | — | none (#107–#110 closed) | none | its children's | parent (children #131–#134; ask the user before closing once all four close) |
| #134 Slim batch C2: coordinate sub-files and close-out.md | running | #133 (closed) | none | New close-out.md; coordinate/SKILL.md (Other branches, C2's rows); app-limits, ci-fallbacks, compact, large-outputs, unattended .md; cross-machine.md (deleted); README.md (Layout); GLOSSARY.md | free |
| #114 Merge right scoped to a round | — | #112 | none | coordinate/SKILL.md (Consent, Finishing a lane); setup/templates/plan.md (Handover) | needs-triage |
| #115 Spare-worker pool for lanes started while the user is away | — | #112 | none | coordinate/SKILL.md (Starting a lane); unattended.md; work/SKILL.md; relay.py (ready); tests | needs-triage |
| #116 Run, audit and spare lane kinds; who holds the main checkout | — | #112 | none | relay.py (ready); tests; setup/templates/plan.md (Now); coordinate/SKILL.md; GLOSSARY.md (Kind) | needs-triage |
| #117 Spend ceilings and authority in the plan | — | #112 | none | setup/templates/plan.md; unattended.md; coordinate/SKILL.md (Consent) | needs-triage |
| #118 Faster ready, and partial output when a lookup times out | — | #112 | none | relay.py (cmd_ready); tests | needs-triage |
| #119 README as a one-page product page | — | #112 | none | README.md; New docs/layout.md; New docs/releasing.md; docs/getting-started.md | needs-triage |
| #130 relay.py hints that need new behaviour (C104 draft changed after PR; F16 workflow on: lines) | — | #112 | none | relay.py (cmd_ready, cmd_waitchecks); tests; coordinate/SKILL.md (Finishing a lane); ci-fallbacks.md (Checks not started) | needs-triage |

Filled 2026-11-02 from `relay.py roadmap`. #112, #115, #116, #117 list several paths on one bullet, which `parse_files` reads as one path; the paths above are from the issue text.




## Waiting for the user to be present

none


## Waiting for the user's decision

- Owner note (#112, from lane 133, C126): for the user's own CLAUDE.md: "On Windows, write a commit message with a double quote in it to a file and use `git commit -F`." (`reports/133.md`)
- Owner note (#112, from lane 132, W33): add to the one project that uses it, in its `project.md` checks or brief template: "A test that needs a pull request (a CI trigger, say): open none; write in the report how to confirm it after the merge." (`reports/132.md`)
- Since 2026-11-02 00:37 -0800: triage #114–#119 and #130 (labelled needs-triage, "not scheduled until triaged"; all blocked by #112 since ruling 2).

## Deadlines

none
