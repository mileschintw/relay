# Releasing

`main` is where work lands; installs come from `release`, so a merge to `main` reaches no one until it is released.

1. On `main`, raise `version` in `plugin/.claude-plugin/plugin.json` (users get a new copy only when it changes; keep `version` out of `marketplace.json`).
2. `claude plugin validate .` and the tests pass, and the push run on `main` for the commit being released has finished with every job passing, `test` on both ubuntu and windows included (pull requests run `test` on ubuntu only, so this run is the first on windows). Check it with `python3 -I plugin/tools/relay.py waitchecks <records> --push <sha>` (Windows: `py -3 -I`), giving the full sha (a short one matches no run): it waits for the run and exits 0 only when one passed and none failed. A run its lines mark cancelled or skipped still needs a rerun before the release.
3. `git push origin main:release` (fast-forward only), then tag `relay--v<version>`.

`marketplace.json` is read from `main`, so a change to it reaches users on their next marketplace update, without a release. To try unreleased skills locally: `claude --plugin-dir plugin`.
