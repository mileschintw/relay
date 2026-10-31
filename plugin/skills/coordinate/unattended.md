# Unattended

Only when the user turns it on in words. Record in the plan's Handover, in that turn: their words, the scope (which issues), the merge right, the time, and mode `unattended`. It ends when the user speaks to you again, unless they say it does not; when it ends, in that turn: remove the worker paragraph below from every brief that carries it, `SendMessage` each unparked worker to reread its brief and ask the user again from now on, set Handover's mode to normal, and commit the records.

## The turn the user turns it on is the only one that can start sessions

In that same turn (the user typed it in the desktop app): check the plan as in *First turn* step 3, write a brief for every in-scope lane with no session yet, adding the worker paragraph below, and start them all: lanes free to begin now, the rest parked. Add the same paragraph to the brief of every in-scope lane already in Now, and `SendMessage` each of their workers not parked (`done` ones included, since a fix request can still wake them) to reread its brief now. A parked worker rereads its brief on GO, so it needs no message, now or when the mode ends. Check where each one landed (`app-limits.md`, *Session folders*), write the list into the plan's Unattended log, commit the records, then set the alarm (*Following progress*). A lane missed now can only be proposed as a card later.

## What is in scope

A lane is in scope when the user's scope names its issue and the roadmap's Kind says `free` (`../../GLOSSARY.md`, **Kind**). A free lane's single limited follow-up step goes into the log for the user.

## Rules for you

- **PRs and merges** only when the user granted it: a lane finished with no blocker gets its PR; a lane under `ready`'s Ready to merge gets `relay.py merge` (*Finishing a lane* step 4). A CI fallback goes on only as `ci-fallbacks.md` › *Asking the user* allows.
- **Answering a worker's question:** in scope and reversible, answer from the plan and the rulings, and log the question, your answer and why. Unsure: that lane is Stuck.
- A fix to tests or CI only, changing no behaviour, that a lane in scope needs in order to merge counts as in scope: have a running worker make it, then log it.
- **Stuck** (a check a worker cannot fix, an unexplained moved head, a conflict, a worker blocked on a decision only the user can make, a step from the list below): that lane stops, and so do the parked lanes behind it; log it; move each out of Now (*Finishing a lane* step 6); carry on with the rest.
- At every state change, update the Unattended log and push the records, so the user reads what happened when they return.
- **The round ends** when no in-scope lane is running or parked (each merged or stopped): write a closing summary in the Unattended log, push the records, and end the turn with no alarm. Until then, set the alarm before ending every turn.

## Never, unattended (plus `project.md`'s additions)

Publish or release; archive a session; close an issue (a PR's `Closes` lines excepted); create accounts or VMs; spend money; install into the user's real profile; download more than the project's dependencies; sign in to or scrape outside sites; touch the user's own data the project names as off limits.

The worker paragraph below copies this list, since a worker cannot read this file: change both together.

## The paragraph for each unattended worker's brief

> The user is away. Ask nothing with `AskUserQuestion`; decide or block as follows. For a small, reversible decision in scope, take the recommended option and record the question, the options, your pick and why in the report's *Decided while unattended* section. For anything needing the user (publishing or releasing, archiving a session, closing an issue (a PR body's `Closes` lines excepted), creating accounts or VMs, spending money, installing into the user's real profile, downloading more than the project's dependencies, signing in to or scraping outside sites, touching the user's own data the project names as off limits, anything on `project.md`'s *Unattended, never* line or its ask-first list, a change to the issue's scope, deleting the user's data, an open design question): run `relay.py status <records> <key> --state blocked --doing "<the question>"`, list the options with your recommendation in the report, and end your turn. Before blocking, you may `SendMessage` the coordinator one short question: if it answers from the plan, carry on and log it under *Decided while unattended*; otherwise block as above.
