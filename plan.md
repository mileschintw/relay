# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** the `/relay:coordinate` session in worktree D:\Repos\relay\.claude\worktrees\lane-102-f7b67c (branch `claude/relay-coordinate-342391`), since 2026-11-02 00:37 -0800; id not yet shown. Mode: normal. The previous coordinator (worktree lane-75-b3c0b3, id local_64ef6796-f1f9-4e2a-afe2-d83002ce2094) wrote itself out on 2026-10-31 after releasing 0.3.2 (`release` and tag `relay--v0.3.2` = `ec4aba9`; → `plan-history.md`, "Close-out of 0.3.2"). `relay.py` is `project.md`'s line (main checkout, at `ec4aba9`): fast-forward it after each merge.
- **Alarm:** `project.md`'s `Alarm: 10` (the user's 10 minutes, 2026-10-31 01:51 「可以就這樣改」, moved there when #82 merged); waiting on CI relies on the background `waitchecks` ending, not the alarm.
- **Unattended log:** none.

## Rulings

none (ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|

All lanes through 103 merged; 0.3.2 released → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, 0.3.1 and 0.3.2 rounds, close-outs).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #107 Handover Next field, pointer-only compact instruction, quote the user only for authority | 1 | none | none | setup/templates/plan.md (Handover, owner); briefs/_template.md (go-ahead line); coordinate/compact.md (owner); coordinate/SKILL.md (First turn, Consent, Starting a lane step 3); unattended.md (user's words); work/SKILL.md (report); GLOSSARY.md (Handover, Ruling, Consent, Mode) | free |
| #108 Plan limit in bytes, pruning that fires, shorter ready output, line-ending check | 1 | none | none | relay.py (cmd_ready); tests/test_relay.py; setup/templates/plan.md (header line); coordinate/SKILL.md (Plan) | free |
| #109 Audit fixes: release lane waits, one-line quiet wakes, workers wait on jobs, no transient Handover facts | 1 | none | none (adds one comment line to #107's plan-template Handover: mechanical) | coordinate/SKILL.md (Scheduling, Following progress); work/SKILL.md (waiting on a background job); setup/templates/plan.md (Handover comment) | free |
| #110 Inventory every skill rule with its trigger, incident source and decision | 1 | none | none | local `relay-notes/inventory-2026-11/inventory.md` only (Files section is unparsable: needs a fix on the user's yes) | limited: user reviews the table |
| #111 Spike: resume after compact with a plugin SessionStart(compact) hook | 2 | none | after #107, coordinate/compact.md | New plugin/hooks/hooks.json; New plugin/tools/resume.py; tests/test_relay.py; compact.md; setup/templates/README.md; README.md (Layout) | limited: proving the hook fires in a Code tab session needs the plugin loaded in the app |
| #112 Slim the skills by the reviewed inventory | 3 | #110, #107, #108, #109 | none | all skill files; relay.py (ready hints); tests; GLOSSARY.md; README.md (Layout) | limited: the user's review of #110's table |
| #113 ADR 0001: resume after compact through a hook and Handover | 3 | #111 | none | New docs/adr/0001-resume-after-compact.md | free |
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

- Since 2026-11-02 00:37 -0800: start wave 1 (#107, #108, #109) and park #111 behind #107?
- Since 2026-11-02 00:37 -0800: add a parsable `## Files` line to #110 and give it a lane?
- Since 2026-11-02 00:37 -0800: triage #114–#119 (labelled needs-triage, "not scheduled until triaged").

## Deadlines

none
