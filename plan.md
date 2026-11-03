# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** the session in worktree D:\Repos\relay\.claude\worktrees\new-session-208f95 (branch `claude/relay-coordinate-f026f5`), since 2026-11-02 13:01 -0800; mode normal. The previous coordinator (worktree D:\Repos\relay\.claude\worktrees\lane-102-f7b67c, id local_41066841-894c-4b9c-8f9e-2ce0ab11a088) wrote itself out on 2026-11-02 after the round of lanes 107–123 (→ `plan-history.md`, "Lanes 107–111"; its 7 lane sessions archived, scratchpads in `snapshot/`). The next coordinator starts with `/relay:coordinate` in a new desktop-app session. `relay.py` is `project.md`'s line (main checkout, at `02d1f2d`): fast-forward it after each merge.
- **Next:** lane 110 updating C104/F16 under ruling 2 (user: "Fix it and start", 2026-11-02 13:01 -0800); then the user reviews its one-page summary before #112. #114–#119 triage waits on the user. The compact hook (#111) is on main but reaches the user only with the next release (installed relay is 0.3.2); a release runs `project.md`'s one review pass first. Records `compact-instruction.md` is no longer used by the new flow; kept until the user decides.
- **Alarm:** `project.md`'s `Alarm: 10` (the user's 10 minutes, 2026-10-31 01:51 「可以就這樣改」, moved there when #82 merged); waiting on CI relies on the background `waitchecks` ending, not the alarm.
- **Unattended log:** none.

## Rulings

- **Ruling 2 — no new features during the slimming** (user, 2026-11-02 16:39 -0800: 「我們目前階段盤點以及實作時，如果遇到要做新功能，應該移動到跟其他後續issue一起」). While #110 (inventory) and #112 (slimming) run, any new behaviour (new code in `relay.py`, a new check, a rule with no existing text behind it) is not done in those lanes: it becomes its own issue, scheduled with the backlog (#114–#119) after #112. Ends when #112 closes. Applied on the user's "Yes, all four": #112's body gains a *No new behaviour* paragraph; C104 and F16 moved to new issue #130; #114–#118 and #130 blocked by #112 on GitHub; lane 110 asked to move C104/F16 out of batch H and re-scan for other new-behaviour rows.

(Ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`.)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
| 110 | #110 | local_180d6972-abd7-4597-9faa-3ba80176a3fd (landed in archived lane 113's folder D:\Repos\relay\.claude\worktrees\lane-113-4cca63, on its own branch `claude/lane-110-decec1`; keep lane 113's session archived) | working: moving C104/F16 out under ruling 2 (asked 2026-11-02 16:42 -0800); no PR by design (`ready`'s "branch not pushed" Inconsistent line is expected) | — |

Lanes 109 (PR #121), 107 (PR #122), 108 (PR #124), 120 (PR #125), 111 (PR #127), 123 (PR #128) and 113 (PR #129) merged → `plan-history.md`, "Lanes 107–111". All lanes through 103 merged; 0.3.2 released → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, 0.3.1 and 0.3.2 rounds, close-outs).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #110 Inventory every skill rule with its trigger, incident source and decision | 1 | none | none | local `relay-notes/inventory-2026-11/inventory.md` only (Files line fixed 2026-11-02 on the user's yes) | limited: user reviews the table; lane 110 running |
| #112 Slim the skills by the reviewed inventory | 2 | #110 (#107, #108, #109 closed) | none | all skill files; relay.py (ready hints); tests; GLOSSARY.md; README.md (Layout) | limited: the user's review of #110's table |
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

- Since 2026-11-02 13:21 -0800: review lane 110's one-page summary (`D:\Repos\relay-notes\inventory-2026-11\inventory.md`, top) and its three questions (C10/C25/C27/F15 deletions that change behaviour; the 9 rows moving to other projects; the new CORE and SCAN classes); then close #110 and start #112's batches H and W in parallel, then C1 → C2.
- Since 2026-11-02 00:37 -0800: triage #114–#119 and #130 (labelled needs-triage, "not scheduled until triaged"; all blocked by #112 since ruling 2).

## Deadlines

none
