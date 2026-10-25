# Getting started

relay coordinates several Claude Code desktop-app sessions on one repo: a **coordinator** session orders the work and gates your consent, one **worker** session per lane writes the code, and a records branch keeps the plan. It adds only what mattpocock-skills does not cover: running real sessions side by side.

## Install (once per machine)

1. Install mattpocock-skills (`/plugin` → claude-plugins-official → mattpocock-skills).
2. Add the repo as a marketplace and install relay (a local clone works too: `/plugin marketplace add <path of the clone>`):
   ```
   /plugin marketplace add mileschintw/relay
   /plugin install relay@relay
   ```
   The repo is private, so the machine's git must be signed in to GitHub.
   Check: `/relay:setup` and `/relay:coordinate` appear when you type `/relay`.

   For the lightest footprint, install at project scope in the repos that use relay, not user scope: `relay:work` is model-invoked, so its one-line description is loaded in every session where relay is installed.

Needs: git 2.38+, `gh` signed in, Python 3.10+ (standard library only).

## Turn it on in a project (once per repo)

1. `/setup-matt-pocock-skills` (the issue tracker and labels relay builds on).
2. `/relay:setup`. It asks a few questions (language, checks, test bar, off-limits paths), creates the orphan branch `coord` checked out beside the main checkout as `<repo folder>-coord`, and proposes one pointer line for `AGENTS.md`. A public repo gets the choice of a separate private records repo instead.

On another machine: `git fetch origin coord`, then, in the main checkout, `git worktree add ../<repo folder>-coord coord`.

## Use it

1. **Design.** Grill the idea: `/grill-with-docs`, or ask for a grill using `mattpocock-skills:grilling` + `mattpocock-skills:domain-modeling`. No code yet.
2. **Tickets.** `/to-tickets` turns the result into issues with native blocking links (`/wayfinder` first if the work is too foggy to slice).
3. **Coordinate.** In a new desktop-app session, `/relay:coordinate`. It checks the plan against GitHub, then proposes every lane that can start now and the chains behind them. Say yes; it starts them in that same turn, the waiting ones parked.
4. **Workers** follow `relay:work`: branch, `mattpocock-skills:tdd`, `mattpocock-skills:code-review` until no blocker, a PR body draft, a report, `done`. They talk to you directly when they need a decision; answer there.
5. **PR and merge.** For each finished lane the coordinator asks one question: open the PR and merge when CI passes, or only open it. After a merge it sends `GO` to the parked lanes that were waiting.
6. **Away?** Tell the coordinator "unattended" with the scope and whether it may merge; it starts everything in that turn and logs what it did in the plan.
7. **Long session?** Ask the coordinator for a compact instruction before `/compact`.

## Who does what

| You need | Use |
|---|---|
| Sharpen a design | `mattpocock-skills:grilling`, `grill-with-docs`, `mattpocock-skills:domain-modeling` |
| Issues with blocking edges | `/to-tickets`, `/wayfinder` |
| One agent, many subagents, one session | mattpocock's `chief-of-staff` |
| Several real sessions in parallel, with your consent gated | relay |
| Build a lane | `relay:work`, which calls `mattpocock-skills:tdd`, `mattpocock-skills:code-review`, `mattpocock-skills:writing-for-agents`, `mattpocock-skills:pr` |

## Rules worth knowing

- A yes covers only what it names; a yes passed on by another session does not count until you confirm it to the coordinator.
- Sessions can be started only in a turn you typed in the desktop app; messages (`GO`) reach existing sessions any time. That is why waiting lanes are started parked.
- Hard dependencies live in GitHub's blocked-by; "same section, not at the same time" lives in the brief and the plan, and its order can be swapped.
- The plan holds current state only and moves, never deletes, what is done.
