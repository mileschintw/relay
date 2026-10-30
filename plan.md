# Plan

Last updated: 2026-10-30 16:08 -0700

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title unknown (relay-coordinate session), worktree D:\Repos\relay\.claude\worktrees\relay-coordinate-5b7cc3, id unknown, mode normal.
- **Standing instructions:** none.
- **Unattended log:** none.

## Rulings

none

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free` (needs no user decision, account, special machine or release) or `limited: <what>`.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #1 Treat issues with sub-issues as parents | 1 | none | none | relay.py (`ready` parents), fake_gh.py, test_relay.py, coordinate SKILL.md (First turn step 3; Scheduling frontier bullet), setup templates/plan.md, GLOSSARY.md (**Parent**) | free |
| #2 Issue-body `## Files` section | 2 | none | after #1, coordinate SKILL.md › First turn step 3 | relay.py (new roadmap command), fake_gh.py, test_relay.py, coordinate SKILL.md (First turn step 3; Starting a lane step 1), setup SKILL.md, README.md (Layout row), GLOSSARY.md | free |
| #3 Hand back when the roadmap empties; owner notes | 2 | #1 | none | relay.py (`ready` owner notes), fake_gh.py, test_relay.py, coordinate SKILL.md (First turn step 5; Finishing a lane step 6), GLOSSARY.md (owner-note marker) | free |

Mechanical overlap: all three touch `plugin/tools/relay.py`, `tests/fake_gh.py`, `tests/test_relay.py` and `plugin/GLOSSARY.md` in different functions/entries; #2 and #3 can run together after #1 merges.

## Waiting for the user to be present

none

## Waiting for the user's decision

- Go-ahead to start lane 1 now, with lanes 2 and 3 parked until #1 merges; since 2026-10-30 16:08 -0700.

## Deadlines

none
