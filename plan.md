# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title unknown (relay-coordinate session), worktree D:\Repos\relay\.claude\worktrees\relay-coordinate-5b7cc3, id local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22, mode normal; back in Handover since 2026-10-30 23:07 -0700 on the user's 「發布0.3.0，接著更新這個coordinator到新release…我compact完再接著直接繼續解issue」. Runs relay 0.3.0 (PR #52, `release` and tag `relay--v0.3.0` = `1d023cd`): skills at `C:\Users\user3\.claude\plugins\cache\relay\relay\0.3.0\`; this session's Skill tool may still load an older copy until a restart, so read the 0.3.0 files by path. `relay.py` is `project.md`'s line (main checkout, at `1d023cd`): fast-forward it after each merge.
- **Standing instructions:** after the compact, start the open frontier without asking again (「我compact完再接著直接繼續解issue」): #46–#51 now, #45 parked until #51 merges (done 23:14: all seven started; all merged by 00:04). After lanes 60–63 merge, rerun the writing-for-agents scan of all skills and a code-review (「照推薦開四個lan執行所有問題，並在結束後再跑一次wfa跟code-review」, 2026-10-31 00:11 -0700). Merge right: per lane, on the user's yes to "open the PR and merge once CI passes" (CI exists since #16).
- **Alarm:** 10 minutes while a lane runs (user, 2026-10-31 01:51: 「可以就這樣改」, since a warm-cache wake is cheap); waiting on CI relies on the background `waitchecks` ending, not the alarm. After 0.3.1: file an issue to make the alarm interval a `project.md` setting (「下一個patch讓鬧鐘時數可以調整config」).
- **Unattended log:** none.

## Rulings

none (ruling 1, merging on local checks while the repo had no CI, ended when #16 added CI → `plan-history.md`)

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
| 72 | #72 | local_32b3c9f8-d7d4-44a5-b77f-f0562d8f081b | catching up, PR #80 conflicts with #79 | |

Lanes 71–75 started 2026-10-31 01:22 -0700 on the user's 「照推薦開 A–E」, each in its own new folder. Merge right for 71–75 and the 0.3.1 release: 「好，一路到發布」 (01:34): open each PR when done, merge once CI passes, then release 0.3.1 per README › Releasing. Ruling for this batch (01:32): 「讓他們各自修補自己發現的小問題，先不要再開新issue，我想早點發布patch」: each lane fixes what it found inside the batch, no new issues; then release 0.3.1. Lane 74 fixes its never-list drift note; lane 75 adds the three GLOSSARY rules to coordinate (Plan, Consent, Same-section wait lines). Merge order when several finish together: 71 before 72 (both relay.py). After all merge: release 0.3.1 on the user's yes. Lanes 60–64 (WFA scan) all merged (PRs #65–#67, #69, #70) → `plan-history.md`.

Lanes 51, 46, 48, 49, 50 merged (PRs #53–#57, 23:38–23:40) → `plan-history.md`. Lane 47 merged (PR #58, 23:41). Lane 45 got GO after #53 merged; lane 45 merged (PR #59, 00:04).

Lane 42 merged (PR #44, 22:10). Lane 33 merged (PR #43, 18:31) → `plan-history.md`. Wave 2: lanes 24–31 merged (PRs #34–#41, 2026-10-30 17:51–18:02 -0700) → `plan-history.md`. Wave 1: all lanes merged: 1, 2, 3, 7, 8, 9, 10, 11, 12, 16 → `plan-history.md`.

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release) or `limited: <what>`.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #72 ready: one PR lookup per run instead of one per lane | 1 | none | none | relay.py (cmd_ready fetch, ready_done, pushed_head, PR lookups), tests | free |

Filed 2026-10-31 01:20 from the post-0.3.0 WFA rescan + code-review (both by fresh subagents, findings verified by the coordinator) on the user's 「照推薦開 A–E」; #68 folded into lane 74 on 「併進重掃」. Mechanical overlap: relay.py 71 / 72 (different functions; 71 merges first); coordinate SKILL.md 73 (step 4) / 74 (other sections); unattended.md 73 (PRs and merges) / 74 (First turn pointer, worker paragraph). Not filed, by recommendation: further SKILL.md splits (merge.md, archiving.md); the rescan's `ListAgents` finding (the tool exists); #60/#64 scope notes (accepted as reasonable). #45–#51 and #60–#64 all merged → `plan-history.md`.

## Waiting for the user to be present

none

## Waiting for the user's decision

none (the optional work SKILL.md issue was filed as #60 on 2026-10-31)

## Deadlines

none
