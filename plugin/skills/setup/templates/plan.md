# Plan

Current state only. Done work moves to `plan-history.md` with a one-line pointer here; nothing is deleted. These always stay in this file: the sessions in **Now**, **Rulings** not yet carried by a repo doc, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title <session title>, worktree <path>, id <once a tool result shows it, else "unknown">, mode <normal | unattended | paused>.
- **Next:** <the next step; who it waits on (the user, lane <key>, a check, nobody); the user's authorization for it (the yes, standing instruction or unattended scope that covers it, or "needs a yes")>. Also anything in flight: a background command, a question asked, a message with no answer yet.
- **Standing instructions:** <"none", or each with the user's words and time; once one is withdrawn, move it to plan-history.md>.
- **Unattended log:** <"none"; while unattended: the user's words, scope, merge right; then each session started, PR merged, question answered (and why), lane stopped, with times; once it ends, move the log to plan-history.md and leave one summary line>

## Rulings

<"none", or numbered, one line each: the decision and its date; once a repo doc or ADR carries one, move it to plan-history.md and leave "→ <file>">

## Now

| Key | Issues | Session | State | Parked until |
|---|---|---|---|---|

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free`, `limited: <what>` or `parent`, as the relay plugin's `GLOSSARY.md` defines under **Kind**.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|

## Waiting for the user to be present

<"none", or one line each: what, which lane, since when>

## Waiting for the user's decision

<"none", or one line each: what, which lane, since when>

## Deadlines

<"none", or one line each: what, by when>
