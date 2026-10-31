# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title unknown (relay-coordinate session), worktree D:\Repos\relay\.claude\worktrees\relay-coordinate-5b7cc3, id local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22, mode normal; back in Handover since 2026-10-30 23:07 -0700 on the user's 「發布0.3.0，接著更新這個coordinator到新release…我compact完再接著直接繼續解issue」. Runs relay 0.3.0 (PR #52, `release` and tag `relay--v0.3.0` = `1d023cd`): skills at `C:\Users\user3\.claude\plugins\cache\relay\relay\0.3.0\`; this session's Skill tool may still load an older copy until a restart, so read the 0.3.0 files by path. `relay.py` is `project.md`'s line (main checkout, at `1d023cd`): fast-forward it after each merge.
- **Standing instructions:** after the compact, start the open frontier without asking again (「我compact完再接著直接繼續解issue」): #46–#51 now, #45 parked until #51 merges. Merge right: per lane, on the user's yes to "open the PR and merge once CI passes" (CI exists since #16).
- **Unattended log:** none.

## Rulings

none (ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|

Lane 42 merged (PR #44, 22:10). Lane 33 merged (PR #43, 18:31) → `plan-history.md`. Wave 2: lanes 24–31 merged (PRs #34–#41, 2026-10-30 17:51–18:02 -0700) → `plan-history.md`. Wave 1: all lanes merged: 1, 2, 3, 7, 8, 9, 10, 11, 12, 16 → `plan-history.md`.

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release) or `limited: <what>`.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #51 relay.py waitchecks: poll for the first check instead of 15 minutes | 1 | none | none | relay.py (new `waitchecks` subcommand), fake_gh.py, test_relay.py, coordinate SKILL.md (Finishing a lane step 4 and Checks not started), setup templates/project.md (CI start wait line), README/GLOSSARY if a term is added | free |
| #45 relay.py merge: merge ready lanes one at a time | 2 | #51 | none | relay.py (new `merge` subcommand), fake_gh.py, test_relay.py, coordinate SKILL.md (Finishing a lane step 4), README.md (usage line if listed) | free |
| #46 ready: warn when the records folder has no .gitattributes | 1 | none | none | relay.py (`cmd_ready` records checks), test_relay.py | free |
| #47 ready: warn when the relay.py checkout is behind | 1 | none | none | relay.py (`cmd_ready`, reading the **relay.py:** line), test_relay.py | free |
| #48 coordinate: stop the alarm once no worker is running | 1 | none | none | coordinate SKILL.md (Following progress, Alarm) | free |
| #49 app-limits: when a session lands in an archived session folder | 1 | none | none | coordinate app-limits.md (Session folders) | free |
| #50 coordinate: say snapshot/ is local only | 1 | none | none | coordinate SKILL.md (Consent, snapshot bullet) | free |

Filed 2026-10-30 from the second retro on the user's 「6 項都開」. Mechanical overlap: relay.py and test_relay.py #45 (new subcommand) / #46 and #47 (both add a check in `cmd_ready`: name each one's line in the briefs); coordinate SKILL.md #45 (step 4) / #48 (Alarm) / #50 (Consent). #51 came from the user's side session (local_219aad9f), relayed and confirmed here with 「另開 issue，#45 等它」; #45 is blocked by #51 on GitHub (merge reuses `waitchecks`), and both touch coordinate SKILL.md step 4. No lane yet. Wave 2's overlap notes → `plan-history.md`. Not filed, by recommendation: unpinned claude-code in CI, stall detection.

## Waiting for the user to be present

none

## Waiting for the user's decision

- Optional issue from the pre-0.3.0 sort of unfiled worker notes: `plugin/skills/work/SKILL.md` gives two answers for a review finding outside the lane that matches only a closed issue (Workflow step 3 says new issue; *Status* says SendMessage). Every other note was already handled or not worth an issue. Since 2026-10-30 23:07 -0700.

## Deadlines

none
