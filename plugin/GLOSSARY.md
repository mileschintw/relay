# Glossary

One word per idea; definitions only. Each rule lives in the one skill that acts on it.

**Coordinator**
The one session that orders the work, starts worker sessions, gates the user's consent and keeps the plan. It writes no product code.

**Worker**
A session that works one lane: its own worktree, its own branch, one pull request. It stops at `done`; the coordinator opens the PR.

**Main checkout**
The repo's own clone, not a worktree: the first path `git worktree list` prints. It holds untracked files (gitignored fixtures, a local database) a fresh worktree lacks.

**Lane**
One unit of parallel work: one issue, or a few small issues closed by one PR, with its brief, its worker and its branch. Named by its **key**: the number of the first issue it closes.

**Parent**
An open issue with sub-issues (its children).

**Brief**
`briefs/<key>.md`: about ten lines, only what is specific to one lane. A worker reads it with `relay:work` and `project.md`, which hold everything the lanes share.

**Parked worker**
A worker started before its lane may begin; it waits for GO.

**GO**
The coordinator's message `GO #<key>`, which lets a parked worker start.

**Hard dependency**
Lane A needs lane B's result. Recorded as the tracker's blocking link on A's issue (GitHub's blocked-by).

**Same-section wait**
Lanes A and B change the same section of a file, though neither needs the other's result: one runs after the other, in either order. Recorded on the brief's `Waits for (same section):` line.

**Files section**
An issue body's `## Files` section: one bullet per file the lane will touch, `New:` before a file it creates, a trailing `(...)` scoping the change. `relay.py roadmap` prints it.

**Mechanical overlap**
Two lanes touch the same file in ways that merge cleanly: separate rows of a table, separate sections that do not refer to each other, or one lane adding an item to a list another lane owns.

**Frontier**
Every lane or open issue, parents aside, that can start now: the blocked-by of every issue on its `Closes:` line, other than the lane's own issues (an issue with no lane yet: its own blocked-by), is closed as completed, and no same-section wait on it is still open.

**Wave**
The lanes started together; a lane's Order in the roadmap is its wave (1 = the frontier).

**State**
A lane's stage in its status file: `parked`, `working`, `blocked`, `review`, `done`. The Now table also uses `started`, until the first status file appears.

**Stuck**
In unattended mode, a lane that stops without merging because the next step needs the user (`coordinate/unattended.md` lists the cases).

**Records folder**
The checkout of branch `coord`: an orphan branch of this repo, checked out beside the main checkout as `<repo folder>-coord` (`git worktree list` shows it on `[coord]`), or a separate private repo. It holds the plan, briefs, status files, reports, PR body drafts and decision logs, and is never merged into the default branch.

**Plan**
`plan.md` in the records folder: the current state only. Done work moves to `plan-history.md`.

**Handover**
The plan section naming the current coordinator (title, worktree, id, mode), the user's standing instructions and the unattended log.

**Now table**
The plan table of lanes with a session: key, issues, session, state, and what a parked lane waits for.

**Roadmap**
The plan table of every open issue, once: its Order, blocked-by, same-section wait, the files it owns and its Kind.

**Kind**
A Roadmap column, judged by the lane's outcome: `free` when the outcome needs no user decision, account, special machine or release (a single limited follow-up step, such as replacing a release asset, is logged for the user and leaves it `free`); `limited: <what>` when the outcome itself needs one; `parent` for an issue with sub-issues.

**Ruling**
A decision the user made that the repo does not record yet, kept in the plan with the user's own words until a doc or ADR carries it.

**Status file**
`status/<key>.md`, one per lane, written by `relay.py status`.

**Report**
`reports/<key>.md`: the worker's full account when it is done or blocked.

**Blocker**
In a review: a wrong judgement, a behaviour change the issues did not ask for, or a failing test.

**Review note**
A review finding that is not a blocker.

**Turn-end note**
What the app relays to the starting session when a session ends a turn: the start of its wrap-up recap and last message.

**Owner note**
Work only the user can do, recorded on a parent: a block in the parent's body or a comment on it, from a line that starts with the marker `**Owner action after this set:**` to the end of that body or comment. The marker alone makes a block an owner note.

**Alarm**
The coordinator's background `sleep` that wakes it to read `status/` while lanes run, since a worker's turn end may not. It waits the minutes on project.md's `Alarm:` line, 20 without one.

**CI fallback**
The path a lane on "merge once CI passes" takes when its CI cannot run or no check appears (`coordinate/ci-fallbacks.md`).

**Unattended**
A mode the user turns on in words ("I'm going to sleep, carry on"), with a scope (which issues) and a merge right (which PRs the coordinator may merge without asking) recorded in the plan.

**Mode**
The coordinator's mode, recorded in Handover: `normal` or `unattended`.

**Consent**
The user's explicit yes, typed to the coordinator in its own session, for one named action or a named set; or the user's words that a session the coordinator opened to collect decisions wrote into `decisions-<date>.md`.
