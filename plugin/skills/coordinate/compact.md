# Compact and handover

**Handing over to a new coordinator:** update Handover in the plan, commit the records, and give the user one line to paste in a new desktop-app session: `/relay:coordinate`. No instruction file. Sessions you started keep reporting to you; the new coordinator reads their files and reaches them with `SendMessage`.

**Before the user compacts this session:** empty your head into the plan (below); `/compact` needs no text after it. After any compact, manual or automatic, the plugin's `SessionStart` hook (`tools/resume.py`) adds a resume note to the new context: the language line, the mode and what to reread.

## First, empty your head into the plan

Write every live fact from this conversation into its section of `plan.md`: the next step, who it waits on and the user's authorization for it go in Handover › Next, with anything in flight this very turn (a command running in the background, a question just asked, a message sent with no answer yet). Commit the records.

Check: the plan holds each kind the top of `plan.md` says always stays, and Handover › Coordinator names this session's worktree: the hook finds the coordinator by that path, and prints nothing for a worktree it does not know.
