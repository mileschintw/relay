# What the Claude desktop app allows

Measured, not documented; the app can change. When a tool result contradicts a line here or in the skill, trust the result and tell the user so the file can be updated.

- **Starting a session** (`start_session`, `user_asked`) works only in a turn the user typed in the desktop app. A turn woken by a session's note, a background command ending or another session's message is refused. Remote Control turns the user typed have both worked and failed: try, and fall back on refusal.
- **Fallback:** an `own_initiative` card; the user's click starts it with no further typing. Under Remote Control even cards can be refused ("Nothing was proposed"): keep the brief in the records folder, list it in the plan, and ask the user to say one line in the desktop app.
- **SendMessage to a session that already exists** works in any turn, event turns included, and starts a turn in it. This is what makes parked workers and GO work.
- A target session in a different permission mode may hold the message for the user's approval: start workers in your own mode.
- When a note you expected is missing after a long run of notes with no user message, the app may have stopped delivering them: stop there and wait for the user.
- `AskUserQuestion` answers in a worker's session are invisible to you (`list_events` does not show them).
- Transcripts are deleted after 30 days by default. When the user wants statistics from a run (rounds, agents, models per step), copy the transcripts into the records folder's `snapshot/` before then, and put the date in the plan's Deadlines.

## Session folders

The app does not always put a session where `start_session` asked: a lane started with `use_worktree: true` has landed in an archived lane's folder, and a plain session started in the main checkout with `use_worktree: false` reported the coordinator's own worktree.

- **Check where it landed.** After every `start_session`, lanes and plain sessions alike, compare the `cwd` that `list_sessions` reports with the one you asked for. While the row says `starting: true`, its `cwd` is not final (it can show the main checkout for a few seconds): list again until `starting` is gone, then compare. Record any difference in that session's row of the plan's Now table, in its Session column.
- **Landed in an archived session's folder.** The new session can keep working there when the folder is on the new session's own branch (`git -C <folder> branch --show-current`) and no other session that is not archived has that folder as its `cwd` in `list_sessions`. Record the folder in its Now row's Session column, and keep the old session archived while the new one runs: unarchiving it would put two sessions in one folder.
- **Archiving** a session: `SKILL.md`, *Archiving sessions*.
