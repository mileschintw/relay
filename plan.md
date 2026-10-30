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
| 1 | #1 | local_1579b864-86a9-486d-90c2-506674ab72a7 (claude/lane-1-6a0c93) | done @ a0c9377, Ready for PR (main merged in) | |
| 7 | #7 | local_96015864-484e-43fd-ba63-f56257c25613 (claude/lane-7-51e899) | done @ 6141451, Ready for PR; conflicts with lane 1 in relay.py and fake_gh.py, so merges after lane 1 and resolves | |
| 11 | #11 | local_68c615d2-7e40-43ab-82da-77985a357b61 (claude/lane-11-f4e84e) | started (user: "Start lane 11", 16:41) | |
| 16 | #16 | local_2fe47f57-11a8-4d72-a4e7-2c91bd1aa81c (claude/lane-16-3bf73f) | started (user: "Start lane 16", 16:44) | |
| 2 | #2 | local_fb37449e-58c9-49eb-b7f4-6878eebd3515 (claude/lane-2-ccd448) | parked | GO #2 after #1 merges |
| 3 | #3 | local_9bd0484c-821d-4349-9663-678666c9e033 (claude/lane-3-af9107) | parked | GO #3 after #1 merges |

Started 2026-10-30 16:29 -0700 on the user's "Start wave 1" (16:28). Lanes 8, 9, 10 merged → `plan-history.md`.

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release) or `limited: <what>`.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #1 Treat issues with sub-issues as parents | 1 | none | none | relay.py (`ready` parents), fake_gh.py, test_relay.py, coordinate SKILL.md (First turn step 3; Scheduling frontier bullet), setup templates/plan.md, GLOSSARY.md (**Parent**) | free |
| #2 Issue-body `## Files` section | 2 | none | after #1, coordinate SKILL.md › First turn step 3 | relay.py (new roadmap command), fake_gh.py, test_relay.py, coordinate SKILL.md (First turn step 3; Starting a lane step 1), setup SKILL.md, README.md (Layout row), GLOSSARY.md | free |
| #3 Hand back when the roadmap empties; owner notes | 2 | #1 | none | relay.py (`ready` owner notes), fake_gh.py, test_relay.py, coordinate SKILL.md (First turn step 5; Finishing a lane step 6), GLOSSARY.md (owner-note marker) | free |
| #7 Local checks fallback (`relay.py localcheck`) | 1 | none | none | relay.py (`localcheck`; `checks_state`/`ready_done` billing case), fake_gh.py (`pr comment`, billing rollup), test_relay.py, coordinate SKILL.md (Finishing a lane step 4), setup templates/project.md (Local checks line) | free |
| #11 Deny list `none.` read as a path | 1 (lane 11) | none | none | relay.py (`deny_patterns`), test_relay.py | free |
| #16 Run the test suite in CI on pull requests (filed from session local_4a270d8d-79d2-4faa-b7f2-c35503c4c316 on the user's 「可以，開issue，然後通知main session把issue排進計畫中」) | 1 (lane 16) | none | none | New: .github/workflows/test.yml | free |
| #12 Invalid UTF-8 in a status file crashes `ready` (filed by lane 9, `needs-triage`, no `## Files`) | 1 (no lane yet; #9 merged) | none | none | relay.py (`cmd_ready` status reads), test_relay.py | free |

Mechanical overlap: `plugin/tools/relay.py` (docstring, `cmd_ready` sections) and `tests/test_relay.py` with #1, #2, #3, #7, #11, #12; `tests/fake_gh.py` with #1, #2, #3, #7; `plugin/GLOSSARY.md` with #1, #2, #3. #8 (merged) owns the archive rule in `app-limits.md` › Session folders; #3 points at it. Triage of #7–#10: `decisions-2026-10-30.md`.

## Waiting for the user to be present

none

## Waiting for the user's decision

- Archive finished sessions: triage-7-10 (local_25b74a50-b6f9-40d5-86ad-82eae30d7c7f), lane-8, lane-9, lane-10 (merged); since 2026-10-30 16:40 -0700.
- Lane for #12 (no lane yet; still `needs-triage`, no `## Files`); since 2026-10-30 16:40 -0700.
- PR-and-merge for lanes 1 and 7 (repo still has no CI; lane 7 must resolve against lane 1 after it merges); since 2026-10-30 16:45 -0700.

## Deadlines

none
