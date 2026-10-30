# Compact instruction and handover

**Handing over to a new coordinator:** update Handover in the plan, commit the records, and give the user one line to paste in a new desktop-app session: `/relay:coordinate`. No instruction file. Sessions you started keep reporting to you; the new coordinator reads their files and reaches them with `SendMessage`.

**Before the user compacts this session:** write `compact-instruction.md` in the records folder, and give the user its text to paste after `/compact`.

## First, empty your head into the plan

Everything the next reader needs belongs in `plan.md`, not in the instruction. Write every live fact from this conversation into its section there, commit the records, and only then write the instruction. A long instruction means this step was skipped.

## The skeleton (at most 3 KB)

1. **Who you are:** coordinator of <repo>, session title <title>, worktree <path> (the session id only if a tool result showed it); the mode (normal, or unattended with its scope); the merge right in force, with the user's words.
2. **Files over summary:** after the compact, reread `<absolute path of this skill's SKILL.md>`, `project.md` and `plan.md` (name the sections that matter now), `<absolute path of unattended.md>` while unattended, and any `decisions-<date>.md` section in play. Where a file and the summary disagree, the file wins.
3. **In flight:** only what is happening this very turn and is not in the plan yet: a command running in the background, a question just asked, a message sent with no answer yet.
4. **Next:** the next step, and who it waits on.

## Check before handing it over

For each kind the top of `plan.md` says always stays, the instruction either points at the plan section that holds it, or the plan lacks it and you add it now. Size: at most 3072 bytes (`wc -c compact-instruction.md`; PowerShell `(Get-Item compact-instruction.md).Length`).
