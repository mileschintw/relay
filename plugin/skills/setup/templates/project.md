# Project settings

What relay needs to know about this project. The coordinator and every worker read this file.

- **Repo:** <owner/name>, default branch `<default branch>`.
- **Language:** talk to the user, and write reports, in <language for the user>. Repo files, issues, PR bodies, briefs and the plan are written in <language for repo files, usually English>.
- **Checks before done:** <the commands a worker runs, e.g. `npm test`; `npm run lint`. One backticked command per item, items separated by `;` (`relay.py localcheck` refuses an item with two); mark an item that needs untracked files (gitignored fixtures, a local database, credentials) "main checkout only" inside that item; an optional `(covers: <path>, ...)` in an item (globs, `*` crossing `/`; folders; files) makes workers and `relay.py localcheck` skip it, as "not needed: no covered path changed", when the diff against the default branch touches none of them, e.g. `npm test` (covers: src/**, tests/**); an item without one always runs>.
- **Local checks:** <the commands that run the repo's checks on a change merged with the default branch, the way CI would (`relay.py localcheck` runs them when CI cannot), e.g. `npm test`; `npm run lint`. One backticked command per item, items separated by `;`, a "main checkout only" mark and a `(covers: ...)` list inside its own item, as in Checks before done. "none" or no line: it runs Checks before done>.
- **CI start wait:** <optional: the number of minutes CI may take to report its first check on a new PR, for CI that registers slowly; `relay.py waitchecks` polls for that long, then watches the checks for at most 20 times that long (2 hours at 6) and exits 5 past it, so a small value can cut off slow-running CI. Unanswered, setup removes this line and `waitchecks` waits 6>.
- **Alarm:** <optional: minutes between the coordinator's background wake-ups while a worker can move without the user. Unanswered, setup removes this line and the coordinator waits 20>.
- **Test bar:** <what passing means here, e.g. "the checks above pass and each new behaviour has a test">.
- **Off limits for workers:** <paths only the user or the coordinator changes, or "none">. Workers write only their own `status/`, `reports/` and `pr-bodies/` files in the records folder.
- **Ask the user first, with the exact scope:** creating accounts or VMs, installing into the user's real profile, large downloads, signing in to outside sites, spending money; <project additions, or "none">.
- **Unattended, never:** <project additions to relay's `skills/coordinate/unattended.md` list, or "none">.
- **Release:** <"none", or where the release steps are written>.
- **Deny list:** <"none", or the path (absolute, or relative to the records folder) of a file of names that must never appear in a PR body: one regex per line, `#` for comments; `relay.py ready` reports hits by line number only>.
- **relay.py:** <optional: the `relay.py` the coordinator and workers run, e.g. the main checkout's `plugin/tools/relay.py`; prefer an absolute path, since a relative one resolves against each session's own checkout. Unanswered, setup removes this line and sessions run the installed plugin's copy>.
