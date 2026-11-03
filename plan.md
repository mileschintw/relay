# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** none. The last coordinator (local_41f71e49-d203-4671-9234-61ad31a7903f, worktree D:/Repos/relay/.claude/worktrees/lane-141-e7f5cd) wrote itself out 2026-11-03 03:49 -0800 after the 2026-11-02/03 rounds and release 0.3.4 (→ `plan-history.md`, "Rounds 2026-11-02/03 and 0.3.4"). `relay.py` is `project.md`'s line (main checkout, at `5b7c556`). Next time: `/relay:coordinate`.
- **Next:** nothing running. Open: #166, #167, #168 (needs-triage, small doc fixes from the 0.3.4 review). Owner steps: upload `docs/social-preview/social-preview.png` in Settings › General › Social preview. The session "btw: 以後CI都只跑ubuntu…" (local_0a2ff276-2189-46a4-9a8e-9cf95abca6f0) shares the coordinator's worktree lane-141-e7f5cd: archive both from the sidebar.
- **Alarm:** `project.md`'s `Alarm: 10` (the user's 10 minutes, 2026-10-31 01:51 「可以就這樣改」, moved there when #82 merged); waiting on CI relies on the background `waitchecks` ending, not the alarm.
- **Merge right:** none (the 2026-11-03 00:28 round's moved to `plan-history.md` once 159 and 161 merged).
- **Unattended log:** none.

## Rulings


none (ruling 2, no new features during the slimming, ended when #112 closed 2026-11-02 18:50 -0800 → `plan-history.md`; ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`.)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|

Lane 169 (PR #171) merged 2026-11-03 11:42 UTC → `plan-history.md`. Lane 165 (PR #170) merged 2026-11-03 11:15 UTC → `plan-history.md`. Lane 159 (PR #164) merged 2026-11-03 → `plan-history.md`. Lane 161 (PR #163) merged 2026-11-03 08:45 UTC → `plan-history.md`. Lane 146 (PR #162) merged 2026-11-03 → `plan-history.md`. Lane 147 (#147, #151, PR #160) merged 2026-11-03 08:23 UTC → `plan-history.md`. Lane 119 (PR #157) merged 2026-11-03 08:05 UTC → `plan-history.md`. Lane 139 (PR #155) merged 2026-11-03 06:13 UTC → `plan-history.md`. Lane 115 (PR #156) merged 2026-11-03 → `plan-history.md`. Lane 118 (PR #154) merged 2026-11-03 06:00 UTC → `plan-history.md`. Lane 130 (PR #153) merged 2026-11-03 05:48 UTC → `plan-history.md`. Lane 116 (PR #152) merged 2026-11-03 05:36 UTC → `plan-history.md`. Lanes 145 (PR #148), 140 (PR #149) and 114 (PR #150) merged 2026-11-03 05:29 UTC → `plan-history.md`. Lane 141 (#141, #142, PR #143) merged → `plan-history.md`. Lanes 132 (#132, PR #135), 131 (#131, PR #136) 133 (#133, PR #137) and 134 (#134, PR #138) merged → `plan-history.md`. Lane 110 (#110, inventory, no PR) finished and #110 closed on the user's "Reviewed, go ahead" → `plan-history.md`. Lanes 109 (PR #121), 107 (PR #122), 108 (PR #124), 120 (PR #125), 111 (PR #127), 123 (PR #128) and 113 (PR #129) merged → `plan-history.md`, "Lanes 107–111". All lanes through 103 merged; 0.3.2 released → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, 0.3.1 and 0.3.2 rounds, close-outs).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #166 coordinate: name the Unattended log for the unattended merge right (needs-triage) | 1 | none | none | coordinate/SKILL.md (Consent › The user's words); unattended.md | free |
| #167 setup: CI start wait also caps the checks watch (needs-triage) | 1 | none | none | setup/templates/project.md; GLOSSARY.md | free |
| #168 Doc drift: ready's exit 2, README word count (needs-triage) | 1 | none | none | relay.py docstring; README.md | free |

Filled 2026-11-02 from `relay.py roadmap`. #112, #115, #116, #117 list several paths on one bullet, which `parse_files` reads as one path; the paths above are from the issue text.




## Waiting for the user to be present

none


## Waiting for the user's decision

- Owner note (#145, from lane 145): after the merge, on a machine with no GitHub SSH key and no `url.*.insteadOf` override (`git config --show-origin --get-regexp '^url\..*insteadof'` prints nothing; remove the one added for 0.3.3 with `git config --global --unset-all url.https://github.com/.insteadOf`), run `claude plugin marketplace update relay` then `claude plugin update relay@relay`: it should succeed with no `Permission denied (publickey)`. (`reports/145.md`)


- Owner note (#112, from lane 133, C126): for the user's own CLAUDE.md: "On Windows, write a commit message with a double quote in it to a file and use `git commit -F`." (`reports/133.md`)
- Owner note (#112, from lane 132, W33): add to the one project that uses it, in its `project.md` checks or brief template: "A test that needs a pull request (a CI trigger, say): open none; write in the report how to confirm it after the merge." (`reports/132.md`)

## Deadlines

none
