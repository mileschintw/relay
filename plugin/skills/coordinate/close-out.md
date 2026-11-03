# Close-out

Read when no lane is left to start, or before archiving any session (the user can ask for an archive mid-round).

## Nothing left to start

No lane left in Now, and no open Roadmap row you can start without the user: each one left is a stopped lane (`SKILL.md`, *Finishing a lane*), waits for the user's decision, is a **Parent**, or waits behind one of those. Hand control back: report each such row with why it waits, the two Waiting sections (owner notes included) and Deadlines, and send no further GO. On the user's yes, close out:

- **Sessions:** archive every finished session (*Archiving sessions*, below).
- **Temporary rulings:** give each ruling tied to a passing condition ("CI minutes are used up, run checks locally") an end condition in the plan, so the next coordinator drops it.
- **Handover:** write yourself out of Handover with the date, commit the records, and give the user `/relay:coordinate` for next time.

## Archiving sessions

Archiving cleans up a session's folder, and the app can clear its scratchpad and any shared notes folder. For every archive:

1. **Shared folder?** Read each session's `cwd` in `list_sessions`. Never archive a session whose `cwd` is your own worktree or the folder of any other session not yet archived: run `git status` there, record the shared folder in the plan, and tell the user to archive it from the sidebar once the other session is done (for your own worktree, once you are).
2. **Snapshot.** Copy what matters from each remaining session's scratchpad (top-level files only; skip test copies) and its shared notes folder into the records folder's `snapshot/`.
3. **One question.** If any session remains, ask the user once to archive them all (`SKILL.md`, *Consent*), then archive those the yes names.
