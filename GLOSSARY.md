# Glossary

One word per idea. The skills use these and nothing else.

**Coordinator**
The one session that orders the work, starts worker sessions, gates the user's consent and keeps the plan. It writes no product code. One coordinator edits the plan at a time.
_Avoid_: orchestrator, manager, main session

**Worker**
A session that works one lane: its own worktree, its own branch, one pull request. It stops at `done`; the coordinator opens the PR.
_Avoid_: agent, sub-session

**Lane**
One unit of parallel work: an issue (or a few small issues closed by one PR), its brief, its worker, its branch. Named by its **key**, the number of the first issue it closes.

**Parked worker**
A worker started before its lane may begin. It reads its brief, writes `state: parked` and ends its turn. It begins only on `GO #<key>`.

**GO**
The coordinator's message `GO #<key>` to a parked worker, sent once every issue the lane waits for has merged.

**Hard dependency**
Lane A needs lane B's result. Recorded only as GitHub's "blocked by" on A's issue; the brief's `Depends on:` copies it.

**Same-section wait**
Lanes A and B change the same section of a file, though neither needs the other's result: they run one after the other, in either order. Recorded on the brief's `Waits for (same section):` line and in the plan, never as blocked-by.

**Mechanical overlap**
Two lanes touch the same file in ways that merge cleanly (separate rows of a table, separate sections that do not refer to each other), or one lane adds an item that a list another lane owns must name (the adding lane adds that one row). They run at the same time; the later one merges the default branch into its branch.

**Brief**
What a worker reads before it starts: the `relay:work` skill and the project's `project.md` (the shared part, the same for every lane) plus its **lane brief** `briefs/<key>.md` (about ten lines, only what is specific to the lane).

**Plan**
`plan.md` in the records folder: the current state only. Done work moves to `plan-history.md`.

**Ruling**
A decision the user made that the repo does not record yet, kept in the plan with the user's own words until a doc or ADR carries it.

**Records folder**
The checkout of the orphan branch `coord`, beside the repo (`../<repo>-coord`): plan, briefs, status files, reports, PR body drafts, decision logs. Never merged into the default branch.

**Status file**
`status/<key>.md`, one per lane, written by `relay.py status` at each milestone. The coordinator reads it instead of turn-end notifications.

**Report**
`reports/<key>.md`: the worker's full account when it is done or blocked, including every decision the user made in its session, in the user's words.

**Blocker**
In a review: a wrong judgement, a change in behaviour, or a failing test. Everything else is a note, listed and not chased.

**Unattended**
A mode the user turns on in words ("I'm going to sleep, carry on"), with a scope and a merge right recorded in the plan. It ends when the user speaks again, unless they say otherwise.

**Consent**
The user's explicit yes, given to the coordinator in its own session, for one named action. A yes relayed by another session is a claim to check, not consent.
