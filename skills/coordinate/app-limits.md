# What the Claude desktop app allows

Measured, not documented; the app can change. When a tool result contradicts a line here, trust the result and tell the user so this file can be updated.

- **Starting a session** (`start_session`, `user_asked`) works only in a turn the user typed in the desktop app. A turn woken by a session's note, a background command ending or another session's message is refused. Remote Control turns the user typed have both worked and failed: try, and fall back on refusal.
- **Fallback:** an `own_initiative` card; the user's click starts it with no further typing. Under Remote Control even cards can be refused ("Nothing was proposed"): keep the brief in the records folder, list it in the plan, and ask the user to say one line in the desktop app.
- **SendMessage to a session that already exists** works in any turn, event turns included, and starts a turn in it. This is what makes parked workers and `GO` work.
- A target session in a different permission mode may hold the message for the user's approval: start workers in your own mode.
- **A turn-end note** carries only the first 400 characters of the report, and a turn ending is not the work being done. Read the files.
- **A worker ending its turn while yours is still running** does not wake you later. Whenever you wait on workers without the user, end each turn with a background `sleep 1200` (PowerShell `Start-Sleep 1200`) as an alarm; on any wake, read `status/` and `gh` first.
- After a long run of notes with no user message, the app may stop delivering them: stop there and wait for the user.
- A new session can land in another session's worktree: check `cwd` with `list_sessions` after each start, record a shared one in the plan, and run `git status` there before anything archives either session.
- The app's "needs the user" marker goes stale: check `list_events` before telling the user a session waits for them.
- `AskUserQuestion` answers in a worker's session are invisible to you (`list_events` does not show them): the worker writes them, with the user's words, into its report.
- Session scratchpads (`%TEMP%`) and shared notes folders can be cleared: copy what matters into the records folder's `snapshot/` before archiving a session.
- Transcripts are deleted after 30 days by default: copy them before then if the user wants statistics from them.
