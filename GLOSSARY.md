# Glossary

One word per idea; definitions only. Each rule lives in the one skill that acts on it.

**Coordinator**
The one session that orders the work, starts worker sessions, gates the user's consent and keeps the plan. It writes no product code. One coordinator edits the plan at a time.

**Worker**
A session that works one lane: its own worktree, its own branch, one pull request. It stops at `done`; the coordinator opens the PR.

**Lane**
One unit of parallel work: one issue, or a few small issues closed by one PR, with its brief, its worker and its branch. Named by its **key**: the number of the first issue it closes. Work with no issue gets one opened first, on the user's yes.

**Brief**
`briefs/<key>.md`: about ten lines, only what is specific to one lane. A worker reads it with `relay:work` and `project.md`, which hold everything the lanes share.

**Parked worker**
A worker started before its lane may begin; it waits for GO.

**GO**
The coordinator's message `GO #<key>` to a parked worker, sent once every issue on the brief's `Depends on:` and `Waits for (same section):` lines is closed as completed.

**Hard dependency**
Lane A needs lane B's result. GitHub's blocked-by on A's issue is the source; the brief's `Depends on:` and the roadmap copy it.

**Same-section wait**
Lanes A and B change the same section of a file, though neither needs the other's result: one runs after the other, in either order. The brief's `Waits for (same section):` line is the source (`relay.py ready` reads it); the roadmap and the issue's `Same-section wait:` line copy it. Never blocked-by.

**Mechanical overlap**
Two lanes touch the same file in ways that merge cleanly: separate rows of a table, separate sections that do not refer to each other, or one lane adding an item to a list another lane owns.

**Frontier**
Every lane that can start now: every issue on its brief's `Depends on:` and `Waits for (same section):` lines is closed as completed.

**Wave**
The lanes started together; a lane's Order in the roadmap is its wave (1 = the frontier).

**State**
A lane's stage in its status file: `parked`, `working`, `blocked`, `review`, `done`. The plan's Now table also uses `started`, until the first status file appears.

**Plan**
`plan.md` in the records folder: the current state only. Done work moves to `plan-history.md`.

**Ruling**
A decision the user made that the repo does not record yet, kept in the plan with the user's own words until a doc or ADR carries it.

**Records folder**
The checkout of branch `coord`: an orphan branch of this repo, checked out beside the main checkout as `<repo folder>-coord` (`git worktree list` shows it on `[coord]`), or a separate private repo. It holds the plan, briefs, status files, reports, PR body drafts and decision logs, and is never merged into the default branch.

**Status file**
`status/<key>.md`, one per lane, written by `relay.py status`.

**Report**
`reports/<key>.md`: the worker's full account when it is done or blocked.

**Blocker**
In a review: a wrong judgement, a behaviour change the issues did not ask for, or a failing test. Everything else is a note.

**Unattended**
A mode the user turns on in words ("I'm going to sleep, carry on"), with a scope and a merge right recorded in the plan.

**Consent**
The user's explicit yes, typed to the coordinator in its own session, for one named action or a named set.
