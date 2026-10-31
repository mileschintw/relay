# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title unknown (relay-coordinate session), worktree D:\Repos\relay\.claude\worktrees\relay-coordinate-5b7cc3, id local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22, mode normal; back in Handover since 2026-10-30 23:07 -0700 on the user's 「發布0.3.0，接著更新這個coordinator到新release…我compact完再接著直接繼續解issue」. Runs relay 0.3.0 (PR #52, `release` and tag `relay--v0.3.0` = `1d023cd`): skills at `C:\Users\user3\.claude\plugins\cache\relay\relay\0.3.0\`; this session's Skill tool may still load an older copy until a restart, so read the 0.3.0 files by path. `relay.py` is `project.md`'s line (main checkout, at `1d023cd`): fast-forward it after each merge.
- **Standing instructions:** after the compact, start the open frontier without asking again (「我compact完再接著直接繼續解issue」): #46–#51 now, #45 parked until #51 merges (done 23:14: all seven started; all merged by 00:04). After lanes 60–63 merge, rerun the writing-for-agents scan of all skills and a code-review (「照推薦開四個lan執行所有問題，並在結束後再跑一次wfa跟code-review」, 2026-10-31 00:11 -0700). Merge right: per lane, on the user's yes to "open the PR and merge once CI passes" (CI exists since #16).
- **Unattended log:** none.

## Rulings

none (ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|

Lanes 60–63 started 2026-10-31 00:12 -0700 on the user's 「照推薦開四個lan執行所有問題，並在結束後再跑一次wfa跟code-review」.  Lanes 62, 63 merged (PRs #65, #66, 00:49, via `relay.py merge`, first real run) → `plan-history.md`. Lane 60 merged (PR #67, 00:53). Lane 64 (#64, 「要，一起做」) proposed as a card (task_913c43b8) after the start was refused in an event turn; the user started it 00:51.

Lanes 51, 46, 48, 49, 50 merged (PRs #53–#57, 23:38–23:40) → `plan-history.md`. Lane 47 merged (PR #58, 23:41). Lane 45 got GO after #53 merged; lane 45 merged (PR #59, 00:04).

Lane 42 merged (PR #44, 22:10). Lane 33 merged (PR #43, 18:31) → `plan-history.md`. Wave 2: lanes 24–31 merged (PRs #34–#41, 2026-10-30 17:51–18:02 -0700) → `plan-history.md`. Wave 1: all lanes merged: 1, 2, 3, 7, 8, 9, 10, 11, 12, 16 → `plan-history.md`.

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release) or `limited: <what>`.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #68 coordinate: step 7 hand-back when only stopped lanes remain in the Roadmap | 1 | none | none | coordinate SKILL.md (Finishing a lane step 7) | free |

#68 opened by lane 64 (standing permission); folded into the post-batch WFA + code-review rescan on the user's 「併進重掃」. Lanes 61, 64 merged (PRs #69, #70, 01:13). Now running the requested WFA rescan + code-review of relay--v0.3.0..main. #64 opened by lane 63 (standing permission, a gap its review found), no lane yet. Filed 2026-10-31 from the writing-for-agents scan, on the user's 「照推薦開四個lan執行所有問題…」. Mechanical overlap in coordinate SKILL.md: 61 (step 4), 62 (Consent, step 7), 63 (First turn step 3, Alarm). #45–#51 (second retro) all merged → `plan-history.md`.

## Waiting for the user to be present

none

## Waiting for the user's decision

none (the optional work SKILL.md issue was filed as #60 on 2026-10-31)

## Deadlines

none
