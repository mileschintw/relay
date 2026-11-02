# Plan

Current state only. An entry moves to `plan-history.md` the moment it is DONE or CONFIRMED, with a one-line pointer here; a ruling moves once its lanes merge; nothing is deleted. These always stay in this file: the sessions in **Now**, both **Waiting for the user** sections, **Deadlines**, and the user's standing instructions under **Handover**.

## Handover

- **Coordinator:** title <session title>, worktree <path>, id <once a tool result shows it, else "unknown">, mode <normal | unattended>.
- **Standing instructions:** <"none", or each with the user's words and time>.
- **Unattended log:** <"none"; while unattended: the user's words, scope, merge right; then each session started, PR merged, question answered (and why), lane stopped, with times>

## Rulings

<"none", or numbered, each with the user's words and time; once a repo doc or ADR carries one, move it to plan-history.md and leave "→ <file>">

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
