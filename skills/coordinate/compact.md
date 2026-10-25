# Compact instruction and handover

Before the user compacts this session, or hands it to a new coordinator, write `compact-instruction.md` in the records folder and give it to the user to paste after `/compact` (a new coordinator gets `/relay:coordinate` and is pointed at the plan instead).

## First, empty your head into the plan

Everything the next reader needs belongs in `plan.md`, not in the instruction. Write every live fact from this conversation into its section there, commit the records, and only then write the instruction. A long instruction means this step was skipped.

## The skeleton (at most 3 KB)

1. **Who you are:** coordinator of <repo>, session <id>, worktree <path>; the mode (normal, or unattended with its scope); the merge right in force, with the user's words.
2. **Files over summary:** after the compact, reread `relay:coordinate`, `project.md` and `plan.md` (name the sections that matter now) and any `decisions-<date>.md` section in play. Where a file and the summary disagree, the file wins.
3. **In flight:** only what is happening this very turn and is not in the plan yet: a command running in the background, a question just asked, a message sent with no answer yet.
4. **Next:** the next step, and who it waits on.

## Check before handing it over

For each of the five kinds the plan keeps (sessions in Now, rulings, the two Waiting sections, deadlines, standing instructions), the instruction either points at the plan section that holds it or the plan lacks it and you add it now. Size: `wc -c compact-instruction.md` is at most 3072.

## A new coordinator

The plan's Handover says who coordinates now; update it in the turn you hand over. Sessions the old coordinator started keep reporting to it: the new one reads their files and talks to them with `SendMessage`.
