# relay

Lightweight multi-session coordination for Claude Code, built to sit beside [mattpocock-skills](https://github.com/mattpocock/skills). The **coordinator** is one desktop-app session. It orders the work, starts one **worker** session per issue and gates your consent. A records branch holds the plan and each worker's status.

Requires: Claude Code desktop app, mattpocock-skills, git 2.38+, `gh` (signed in), Python 3.10+. The project must be a GitHub repo.

## Quick start

Install once per machine, in Claude Code:

```
/plugin marketplace add mileschintw/relay
/plugin install relay@relay
```

Then, once per project, in the project's repo:

```
/setup-matt-pocock-skills     # issue tracker and labels relay builds on
/relay:setup                  # creates the coord records branch beside the repo, asks a few settings
```

Day to day:

```
/grill-with-docs              # design; no code yet
/to-tickets                   # issues with blocking links on GitHub
/relay:coordinate             # in a new desktop-app session: the coordinator
```

## Example

```
you          /relay:coordinate
coordinator  Open: #1 add subtract, #2 README function list, #3 CLI (blocked by #1).
             Can start now: #1, #2. Behind them: #3 after #1. Start #1 and #2, park #3?
you          yes
coordinator  Started lane 1 and lane 2, lane 3 parked (waits for GO #3).
   ...       workers branch, test, review, write status/<key>.md and a report
coordinator  Lane 1 is done (no blocker). Open the PR and merge once CI passes?
you          yes
coordinator  PR merged. Sent GO #3; lane 3 started from the new main.
```

What `/relay:setup` leaves beside the repo (`<repo>-coord/`, the orphan branch `coord`):

```
project.md      settings: language, checks, test bar, off-limits paths
plan.md         current state only (done work moves to plan-history.md)
briefs/<key>.md ~10-line briefs, one per lane
status/<key>.md written by relay.py status
reports/  pr-bodies/
```

## Layout

Only `plugin/` is installed; everything else is for developing relay.

| Path | What |
|---|---|
| `plugin/skills/setup` | `/relay:setup`: turn relay on in a repo |
| `plugin/skills/coordinate` | `/relay:coordinate`: the coordinator; `unattended.md`, `compact.md`, `large-outputs.md`, `cross-machine.md`, `app-limits.md` are read on demand |
| `plugin/skills/work` | `relay:work`: what each worker follows |
| `plugin/tools/relay.py` | `status` (a worker's status file), `ready` (what the coordinator can do next), `localcheck` (the checks, run locally when CI cannot) |
| `plugin/GLOSSARY.md` | the terms |
| `.claude-plugin/marketplace.json` | the catalog; its entry installs `plugin/` from the `release` branch |
| `tests/` | `python3 -I tests/test_relay.py` |
| `docs/getting-started.md` | the longer walkthrough and how relay splits work with mattpocock-skills |

## Releasing

`main` is where work lands; installs come from `release`, so a merge to `main` reaches no one until it is released.

1. On `main`, raise `version` in `plugin/.claude-plugin/plugin.json` (users get a new copy only when it changes; keep `version` out of `marketplace.json`).
2. `claude plugin validate .` and the tests pass.
3. `git push origin main:release` (fast-forward only), then tag `relay--v<version>`.

`marketplace.json` is read from `main`, so a change to it reaches users on their next marketplace update, without a release. To try unreleased skills locally: `claude --plugin-dir plugin`.
