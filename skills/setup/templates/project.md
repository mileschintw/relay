# Project settings

What relay needs to know about this project. The coordinator and every worker read this file; the lane brief overrides it for one lane.

- **Repo:** <owner/name>, default branch `<main>`.
- **Records folder:** `<absolute path of this folder>` (branch `coord`).
- **Language:** talk to the user, and write reports, in <language>. Repo files, issues, PR bodies, briefs and the plan stay in <English>.
- **Checks before done:** <the commands a worker runs, e.g. `npm test`, `npm run lint`>.
- **Test bar:** <what passing means here, e.g. "the checks above pass and each new behaviour has a test">.
- **Off limits for workers:** the records folder (except their own `status/`, `reports/` and `pr-bodies/` files); <paths only the user or the coordinator changes>.
- **Ask the user first, with the exact scope:** creating accounts or VMs, installing into the user's real profile, large downloads, signing in to outside sites, spending money; <project additions>.
- **Unattended, never:** <project additions to `unattended.md`'s list, or "none">.
- **Release:** <"none", or where the release steps are written>.
