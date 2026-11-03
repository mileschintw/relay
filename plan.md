# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title Relay coordination, worktree D:/Repos/relay/.claude/worktrees/lane-141-e7f5cd, id local_41f71e49-d203-4671-9234-61ad31a7903f, mode normal. Branch `claude/relay-coordinate-821ea1`; took over 2026-11-02 20:34 -0800. The previous coordinator (local_cac5e599-046a-4d94-801f-10187aae7a59, folder new-session-208f95) wrote itself out 2026-11-02 20:31 -0800 after the #112 slimming round and release 0.3.3 (→ `plan-history.md`, "Round #110–#112 and 0.3.3"). `relay.py` is `project.md`'s line (main checkout, at `8abd5c8`): fast-forward it after each merge.
- **Next:** round 2026-11-02 fully merged (119 last, PR #157, 2026-11-03 00:05 -0800); lane 147 (#147, #151) started 2026-11-03 00:07 -0800; lane 146 started 2026-11-03 00:10 -0800; lane 147 merged (PR #160); lanes 159 and 161 started 2026-11-03 00:27 -0800 under the round's merge right (Handover › Merge right); lane 146 merged (PR #162); left: close-out. Earlier: round started 20:49 -0800 (user: start this round): 145, 140, 114 merged (user picked "open the PR and merge once CI passes" 2026-11-02 21:19 -0800). GO #119 sent. 116 merged, GO #115 sent. Lanes 130 (PR #153) and 118 (PR #154): user picked "open the PR and merge once CI passes" (2026-11-02 21:43 -0800 for 118); merge 130 first, then 118 after it catches up if they conflict. 130's pick: 2026-11-02 21:36 -0800 (PR after it merges main; it conflicts with 116). Earlier: 2026-11-02 21:31 -0800. Lane 115: user picked merge once CI passes (2026-11-02 22:01 -0800). Lane 139: user picked merge once CI passes (2026-11-02 21:49 -0800). Lane 119: user wants it last, with a final check and fix pass; a design session (social preview, README banner, About/topics for SEO) was asked for, started by the user from the card as local_d6d5d23f-c42d-4ead-b008-f29ad75ca1bd (not a lane; summary to reports/design-preview.md); its assets go into README through 119. Follow the lanes; GO #115 after #116 merges. 0.3.3 is released (tag `relay--v0.3.3`, release at 8abd5c8) and installed at local scope in D:\Repos\relay; sessions there pick it up on restart. #145: the user approved the marketplace.json change (url to HTTPS only) at triage, 2026-11-02. `ready` keeps one Inconsistent line for lane 110 (no PR by design; its status file stays as the record).
- **Alarm:** `project.md`'s `Alarm: 10` (the user's 10 minutes, 2026-10-31 01:51 「可以就這樣改」, moved there when #82 merged); waiting on CI relies on the background `waitchecks` ending, not the alarm.
- **Merge right:** round 2026-11-03 00:28 -0800, lanes 159 and 161: user picked "是，這輪都 CI 過就合併 (推薦)" (yes, merge every lane of this round once CI passes). Move to plan-history.md once both have merged or stopped.
- **Unattended log:** none.

## Rulings


none (ruling 2, no new features during the slimming, ended when #112 closed 2026-11-02 18:50 -0800 → `plan-history.md`; ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`.)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
| 159 | #159 | local_e50e5c3c-dae6-4c61-92a9-f6a2f35c8de7 | done at dc512c3; PR #164 opened after #163 merged, under the round merge right; waiting for CI | #164 |

Lane 161 (PR #163) merged 2026-11-03 08:45 UTC → `plan-history.md`. Lane 146 (PR #162) merged 2026-11-03 → `plan-history.md`. Lane 147 (#147, #151, PR #160) merged 2026-11-03 08:23 UTC → `plan-history.md`. Lane 119 (PR #157) merged 2026-11-03 08:05 UTC → `plan-history.md`. Lane 139 (PR #155) merged 2026-11-03 06:13 UTC → `plan-history.md`. Lane 115 (PR #156) merged 2026-11-03 → `plan-history.md`. Lane 118 (PR #154) merged 2026-11-03 06:00 UTC → `plan-history.md`. Lane 130 (PR #153) merged 2026-11-03 05:48 UTC → `plan-history.md`. Lane 116 (PR #152) merged 2026-11-03 05:36 UTC → `plan-history.md`. Lanes 145 (PR #148), 140 (PR #149) and 114 (PR #150) merged 2026-11-03 05:29 UTC → `plan-history.md`. Lane 141 (#141, #142, PR #143) merged → `plan-history.md`. Lanes 132 (#132, PR #135), 131 (#131, PR #136) 133 (#133, PR #137) and 134 (#134, PR #138) merged → `plan-history.md`. Lane 110 (#110, inventory, no PR) finished and #110 closed on the user's "Reviewed, go ahead" → `plan-history.md`. Lanes 109 (PR #121), 107 (PR #122), 108 (PR #124), 120 (PR #125), 111 (PR #127), 123 (PR #128) and 113 (PR #129) merged → `plan-history.md`, "Lanes 107–111". All lanes through 103 merged; 0.3.2 released → `plan-history.md` (waves 1–2, lanes 33, 42, 45–51, 60–64, 71–75, 0.3.1 and 0.3.2 rounds, close-outs).

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release), `limited: <what>`, or `parent` (an issue with sub-issues).

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|

Filled 2026-11-02 from `relay.py roadmap`. #112, #115, #116, #117 list several paths on one bullet, which `parse_files` reads as one path; the paths above are from the issue text.




## Waiting for the user to be present

none


## Waiting for the user's decision

- Owner note (#145, from lane 145): after the merge, on a machine with no GitHub SSH key and no `url.*.insteadOf` override (`git config --show-origin --get-regexp '^url\..*insteadof'` prints nothing; remove the one added for 0.3.3 with `git config --global --unset-all url.https://github.com/.insteadOf`), run `claude plugin marketplace update relay` then `claude plugin update relay@relay`: it should succeed with no `Permission denied (publickey)`. (`reports/145.md`)


- Owner note (#112, from lane 133, C126): for the user's own CLAUDE.md: "On Windows, write a commit message with a double quote in it to a file and use `git commit -F`." (`reports/133.md`)
- Owner note (#112, from lane 132, W33): add to the one project that uses it, in its `project.md` checks or brief template: "A test that needs a pull request (a CI trigger, say): open none; write in the report how to confirm it after the merge." (`reports/132.md`)

## Deadlines

none
