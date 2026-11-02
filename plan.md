# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** the session in worktree D:\Repos\relay\.claude\worktrees\new-session-208f95 (branch `claude/relay-coordinate-f026f5`), since 2026-11-02 13:01 -0800; mode normal. The previous coordinator (worktree D:\Repos\relay\.claude\worktrees\lane-102-f7b67c, id local_41066841-894c-4b9c-8f9e-2ce0ab11a088) wrote itself out on 2026-11-02 after the round of lanes 107–123 (→ `plan-history.md`, "Lanes 107–111"; its 7 lane sessions archived, scratchpads in `snapshot/`). The next coordinator starts with `/relay:coordinate` in a new desktop-app session. `relay.py` is `project.md`'s line (main checkout, at `02d1f2d`): fast-forward it after each merge.
- **Next:** waits on the user: #110's Files section fix, then its lane; #114–#119 triage. The compact hook (#111) is on main but reaches the user only with the next release (installed relay is 0.3.2); a release runs `project.md`'s one review pass first. Records `compact-instruction.md` is no longer used by the new flow; kept until the user decides.
- **Alarm:** `project.md`'s `Alarm: 10` (the user's 10 minutes, 2026-10-31 01:51 「可以就這樣改」, moved there when #82 merged); waiting on CI relies on the background `waitchecks` ending, not the alarm.
- **Unattended log:** none.

## Rulings

none (ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|

Lanes 109 (PR #121), 107 (PR #122), 108 (PR #124), 120 (PR #125), 111 (PR #127), 123 (PR #128) and 113 (PR #129) merged → `plan-history.md`, "Lanes 107–111". All lanes through 103 merged; 0.3.2 released → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, 0.3.1 and 0.3.2 rounds, close-outs).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #110 Inventory every skill rule with its trigger, incident source and decision | 1 | none | none | local `relay-notes/inventory-2026-11/inventory.md` only (Files section is unparsable: needs a fix on the user's yes) | limited: user reviews the table |
| #112 Slim the skills by the reviewed inventory | 2 | #110 (#107, #108, #109 closed) | none | all skill files; relay.py (ready hints); tests; GLOSSARY.md; README.md (Layout) | limited: the user's review of #110's table |
| #114 Merge right scoped to a round | — | none | none | coordinate/SKILL.md (Consent, Finishing a lane); setup/templates/plan.md (Handover) | needs-triage |
| #115 Spare-worker pool for lanes started while the user is away | — | none | none | coordinate/SKILL.md (Starting a lane); unattended.md; work/SKILL.md; relay.py (ready); tests | needs-triage |
| #116 Run, audit and spare lane kinds; who holds the main checkout | — | none | none | relay.py (ready); tests; setup/templates/plan.md (Now); coordinate/SKILL.md; GLOSSARY.md (Kind) | needs-triage |
| #117 Spend ceilings and authority in the plan | — | none | none | setup/templates/plan.md; unattended.md; coordinate/SKILL.md (Consent) | needs-triage |
| #118 Faster ready, and partial output when a lookup times out | — | none | none | relay.py (cmd_ready); tests | needs-triage |
| #119 README as a one-page product page | — | #112 | none | README.md; New docs/layout.md; New docs/releasing.md; docs/getting-started.md | needs-triage |

Filled 2026-11-02 from `relay.py roadmap`. #112, #115, #116, #117 list several paths on one bullet, which `parse_files` reads as one path; the paths above are from the issue text.




## Waiting for the user to be present

none


## Waiting for the user's decision

- Since 2026-11-02 00:37 -0800: add a parsable `## Files` line to #110 and give it a lane?
- Since 2026-11-02 00:37 -0800: triage #114–#119 (labelled needs-triage, "not scheduled until triaged").

## Deadlines

none
