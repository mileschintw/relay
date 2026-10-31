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
| 60 | #60 | local_7d4910b0-c96b-4ba9-88ab-a402f73db01b (folder lane-25-cf22e5, archived lane 25's; own branch claude/lane-60-bbae79) | review | |
| 61 | #61 | local_955327e8-f19c-4d39-9b44-e8ae04a594c7 | review | |
| 62 | #62 | local_b7ceebb0-7408-4bc9-aa39-7e6a0fc5245b | review | |
| 63 | #63 | local_f066e114-a1e3-4399-b421-f91ad2e1ab2f | review | |

Lanes 60–63 started 2026-10-31 00:12 -0700 on the user's 「照推薦開四個lan執行所有問題，並在結束後再跑一次wfa跟code-review」.

Lanes 51, 46, 48, 49, 50 merged (PRs #53–#57, 23:38–23:40) → `plan-history.md`. Lane 47 merged (PR #58, 23:41). Lane 45 got GO after #53 merged; lane 45 merged (PR #59, 00:04).

Lane 42 merged (PR #44, 22:10). Lane 33 merged (PR #43, 18:31) → `plan-history.md`. Wave 2: lanes 24–31 merged (PRs #34–#41, 2026-10-30 17:51–18:02 -0700) → `plan-history.md`. Wave 1: all lanes merged: 1, 2, 3, 7, 8, 9, 10, 11, 12, 16 → `plan-history.md`.

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release) or `limited: <what>`.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #60 work: one rule for an out-of-lane finding that matches only a closed issue | 1 | none | none | work SKILL.md (Workflow step 3 last bullet; Status last bullet) | free |
| #61 coordinate: step 4 keeps the common merge path; CI fallbacks move to ci-fallbacks.md | 1 | none | none | coordinate SKILL.md (Finishing step 4; Other branches), New: ci-fallbacks.md, relay.py (`cmd_merge` wait), test_relay.py, fake_gh.py, README Layout | free |
| #62 coordinate: archiving rules in one place | 1 | none | none | coordinate SKILL.md (Consent last bullet; Finishing step 7 Sessions), app-limits.md (intro; Session folders) | free |
| #63 coordinate: First turn step 3 branches on their own lines; trim the Alarm bullet | 1 | none | none | coordinate SKILL.md (First turn step 3; Alarm) | free |

Filed 2026-10-31 from the writing-for-agents scan, on the user's 「照推薦開四個lan執行所有問題…」. Mechanical overlap in coordinate SKILL.md: 61 (step 4), 62 (Consent, step 7), 63 (First turn step 3, Alarm). #45–#51 (second retro) all merged → `plan-history.md`.

## Waiting for the user to be present

none

## Waiting for the user's decision

none (the optional work SKILL.md issue was filed as #60 on 2026-10-31)

## Deadlines

none
