---
status: accepted
---

# Resume after a compact through a plugin hook and Handover › Next

After a compact, relay points the coordinator or the lane worker back at its records with a plugin `SessionStart` hook (`compact` matcher, `plugin/hooks/hooks.json` running `plugin/tools/resume.py`). The next step lives in the plan's Handover › Next. The user no longer pastes a compact instruction. We chose this because a pasted instruction is only a hint to the summarizer, while hook output is added to the new context as written, and the records already hold every fact the instruction repeated. The hook is relay's first part that is not a skill and runs in every session with relay installed, so dropping it later means bringing back a resume path in the skills.

## Context

- `/compact <text>` steers the summarizer once. The text is not kept as written, and a pasted "reread these files" mostly did not happen.
- After a compact, Claude Code re-attaches the invoked skill and recently read files, but a file it re-attaches only by reference has not been Read, so the Edit tool refuses it until the session reads it again.
- The 2026-11-02 audit of relay runs in three projects found:
  - Coordinator compact instructions at 1.5–3.2 KB, pressed against the 3 KB cap. About half of each was a step-by-step "Next" list, because the plan had no field for the next step. Every other fact in them was already in the records.
  - Workers wrote their own instructions of 1–3.5 KB that only repeated their brief, status and report. Ten worker compacts with no instruction recovered fine from those files.
  - The user's language was lost: after compacts, up to 74% of long replies in one project were in English, and the user corrected it four times.
  - "Read before you edit" was lost: coordinators fell back to shell rewrites of `plan.md`.

## Considered options

- **Longer or stricter compact instructions.** Rejected: they were already at the size cap, and the summarizer still treats them as a hint, so the rereads and the language did not survive.
- **A separate resume document** the user points at when compacting. Rejected: it duplicates the plan and the lane's brief, status and report, and needs the same pasted pointer to be read at all.
- **A plugin `SessionStart` (`compact`) hook plus Handover › Next.** Chosen. The plan carries the next step (#107), and the hook prints a short resume note (#111): for the coordinator, the language line, the mode Handover records, what to reread (Handover with Next, Now, both Waiting sections) and to Read `plan.md` before editing it; for a worker, the language line and the paths of its brief, status and report; anywhere else, nothing.

## Spike result

The docs say `SessionStart` hooks fire in the desktop app but do not name the Code tab, so #111 tested it before shipping:

- **It fires in a Code tab session.** A test plugin whose only content was this hook was installed, a new Code tab session (Claude Code 2.1.309) ran `/compact`, and that session's transcript records `hook_success SessionStart:compact` with the hook's stdout right after the compact boundary. The test plugin was then removed.
- **Its output reaches the model.** In a CLI fixture (2.1.312, `--plugin-dir plugin`) of a coordinator worktree, the model quoted the resume note's lines word for word after `/compact` and answered in the language the note named.

## Consequences

- `coordinate/compact.md` no longer has a pasted instruction: the coordinator writes every live fact into the plan, and `/compact` needs no text after it.
- Every session with relay installed runs the hook after each compact: one `python3` or `py` start and a few `git` calls, with a 10 s timeout. It prints nothing outside a coordinator or lane worktree and never blocks the session.
- The hook finds the coordinator by the worktree path Handover › Coordinator names, so Handover has to keep it current.
- The skill is not injected again; Claude Code already re-attaches it.
- Users get the hook with the first release after #111 merged; until they update, a compact leaves them without the resume note.
