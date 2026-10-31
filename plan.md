# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title unknown (relay-coordinate session), worktree D:\Repos\relay\.claude\worktrees\relay-coordinate-5b7cc3, id local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22, mode normal.
- **Standing instructions:** none.
- **Unattended log:** none.

## Rulings

1. The repo has no CI. For lanes 8, 9 and 10 the user chose 「本機檢查通過就合併」 and, for lane 9, 「開 PR，本機檢查過就合併」 (2026-10-30 ~16:38 -0700): merge after the coordinator runs project.md's checks on the PR head merged onto current main. Applies to those lanes only; ask again for the next ones until #7 lands.

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|
| 12 | #12 | local_8cddf2c9-12f8-4e80-96eb-5eef2ee11d86 (claude/lane-12-c970f3) | started (user: "Triage and start #12", 17:08) | |

Started 2026-10-30 16:29 -0700 on the user's "Start wave 1" (16:28). Lanes 1, 2, 3, 7, 8, 9, 10, 11, 16 merged → `plan-history.md`.

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release) or `limited: <what>`.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #12 Invalid UTF-8 in a status file crashes `ready` (triaged by the coordinator 17:08: `ready-for-agent`, `## Files` added) | 1 (lane 12) | none | none | relay.py (`cmd_ready` and `cmd_localcheck` status reads), test_relay.py | free |

Mechanical overlap: none (only lane open). Triage of #7–#10: `decisions-2026-10-30.md`.

## Waiting for the user to be present

none

## Waiting for the user's decision

- Archive finished sessions: triage-7-10 (local_25b74a50-b6f9-40d5-86ad-82eae30d7c7f), lane-1, lane-8, lane-9, lane-10, lane-11, lane-7, lane-16, lane-3, lane-2 (merged); since 2026-10-30 16:40 -0700.

## Deadlines

none
