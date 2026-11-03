# Releasing

`main` is where work lands; installs come from `release`, so a merge to `main` reaches no one until it is released.

1. On `main`, raise `version` in `plugin/.claude-plugin/plugin.json` (users get a new copy only when it changes; keep `version` out of `marketplace.json`).
2. `claude plugin validate .` and the tests pass.
3. `git push origin main:release` (fast-forward only), then tag `relay--v<version>`.

`marketplace.json` is read from `main`, so a change to it reaches users on their next marketplace update, without a release. To try unreleased skills locally: `claude --plugin-dir plugin`.
