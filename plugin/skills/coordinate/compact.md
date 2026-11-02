# Compact instruction and handover

**Handing over to a new coordinator:** update Handover in the plan, commit the records, and give the user one line to paste in a new desktop-app session: `/relay:coordinate`. No instruction file. Sessions you started keep reporting to you; the new coordinator reads their files and reaches them with `SendMessage`.

**Before the user compacts this session:** write `compact-instruction.md` in the records folder, and give the user its text to paste after `/compact`. That text only steers the summary and is not kept word for word, so it is a pointer to the plan.

## First, empty your head into the plan

Write every live fact from this conversation into its section of `plan.md`: the next step, who it waits on and the user's authorization for it go in Handover › Next, with anything in flight this very turn (a command running in the background, a question just asked, a message sent with no answer yet). Commit the records, and only then write the pointer.

## The pointer (at most 600 bytes)

Identity, mode, merge right, the files to reread, and that files win; no fact or step. Fill in this text:

> You are the relay coordinator of <owner/name>: session <title>, worktree <path>. Mode <normal | unattended | paused>; merge right <none | as Handover says>. Reread <absolute path of this skill's SKILL.md>, <records>/project.md, <records>/plan.md (Handover first)<, <absolute path of unattended.md> while unattended>. Files beat this summary. Carry on from Handover › Next.

A pasted pointer that names mode `unattended` keeps it on after the compact (*First turn* step 5).

## Check before handing it over

- Handover › Next names the next step, who it waits on and its authorization, and the plan holds each kind the top of `plan.md` says always stays.
- The pointer holds only the fields of the text above, and is at most 600 bytes: `wc -c compact-instruction.md` (PowerShell `(Get-Item compact-instruction.md).Length`). Over 600 bytes means a fact or step is in it: move that into the plan.
