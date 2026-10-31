# Unattended

Only when the user turns it on in words. Record in the plan's Handover, in that turn: their words, the scope (which issues), the merge right, the time, and mode `unattended`. It ends when the user speaks to you again, unless they say it does not; when it ends, set Handover's mode to normal in that turn and commit the records.

## The turn the user turns it on is the only one that can start sessions

In that same turn (the user typed it in the desktop app): check the plan as in *First turn*, write a brief for every in-scope lane with no session yet, adding the worker paragraph below, and start them all: lanes free to begin now, the rest parked. Check where each one landed (`app-limits.md`, *Session folders*), write the list into the plan's Unattended log, commit the records, then set the alarm (*Following progress*). A lane missed now can only be proposed as a card later.

## What is in scope

A lane is in scope when the user's scope names its issue and the roadmap's Kind says `free`: it needs no decision of the user's (an open design question, a ruling), none of their accounts or sign-ins, no special machine, and no release. A free lane with one limited step (say, replacing a release asset) runs to its merge; the limited step goes into the log for the user. A lane whose outcome itself is limited stays out.

## Rules for you

- **PRs and merges** only when the user granted it: a lane finished with no blocker gets its PR; checks all passed and an unchanged head get the merge (`--match-head-commit`).
- **Answering a worker's question:** in scope and reversible, answer from the plan and the rulings, and log the question, your answer and why. Unsure: that lane is Stuck.
- A fix to tests or CI only, changing no behaviour, that a lane in scope needs in order to merge counts as in scope: have a running worker make it, then log it.
- **Stuck** (a check a worker cannot fix, an unexplained moved head, a conflict, a worker blocked on a decision only the user can make, a step from the list below): that lane stops, and so do the parked lanes behind it; log it; move each out of Now (*Finishing a lane* step 6); carry on with the rest.
- At every state change, update the Unattended log and push the records, so the user reads what happened when they return.
- **The round ends** when no in-scope lane is running or parked (each merged or stopped): write a closing summary in the Unattended log, push the records, and end the turn with no alarm. Until then, set the alarm before ending every turn.

## Never, unattended (plus `project.md`'s additions)

Publish or release; archive a session; close an issue (a PR's `Closes` lines excepted); create accounts or VMs; install into the user's real profile; download more than the project's dependencies; sign in to or scrape outside sites; touch the user's own data the project names as off limits.

## The paragraph for each unattended worker's brief

> The user is away. Ask nothing with `AskUserQuestion`; decide or block as follows. For a small, reversible decision in scope, take the recommended option and record the question, the options, your pick and why in the report's *Decided while unattended* section. For anything needing the user (a step on the coordinator's never-list, a change to the issue's scope, deleting the user's data, an open design question): write `state: blocked`, list the options with your recommendation in the report, and end your turn. You may `SendMessage` the coordinator first; it answers what the plan already decides.
