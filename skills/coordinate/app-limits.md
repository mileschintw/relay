# What the Claude desktop app allows

Measured, not documented; the app can change. When a tool result contradicts a line here or in the skill, trust the result and tell the user so the file can be updated. The rules every run needs (the 400-character note, the alarm, `list_events`, shared worktrees, snapshots) are in `SKILL.md`; this file holds the rest.

- **Starting a session** (`start_session`, `user_asked`) works only in a turn the user typed in the desktop app. A turn woken by a session's note, a background command ending or another session's message is refused. Remote Control turns the user typed have both worked and failed: try, and fall back on refusal.
- **Fallback:** an `own_initiative` card; the user's click starts it with no further typing. Under Remote Control even cards can be refused ("Nothing was proposed"): keep the brief in the records folder, list it in the plan, and ask the user to say one line in the desktop app.
- **SendMessage to a session that already exists** works in any turn, event turns included, and starts a turn in it. This is what makes parked workers and GO work.
- A target session in a different permission mode may hold the message for the user's approval: start workers in your own mode.
- When a note you expected is missing after a long run of notes with no user message, the app may have stopped delivering them: stop there and wait for the user.
- `AskUserQuestion` answers in a worker's session are invisible to you (`list_events` does not show them).
