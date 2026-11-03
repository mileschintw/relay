# Project settings

What relay needs to know about this project. The coordinator and every worker read this file.

- **Repo:** mileschintw/relay, default branch `main`.
- **Language:** talk to the user, and write reports, in Traditional Chinese (繁體中文). Repo files, issues, PR bodies, briefs and the plan are written in English.
- **Checks before done:** `python3 -I tests/test_relay.py` (Windows: `py -3 -I tests/test_relay.py`); `claude plugin validate .`.
- **Alarm:** 10
- **Test bar:** the checks above pass and each new behaviour in `plugin/tools/relay.py` has a test in `tests/test_relay.py`; skill and doc changes keep `docs/layout.md`'s table and `plugin/GLOSSARY.md` in step.
- **Off limits for workers:** the `release` branch, `relay--v*` tags, and `version` in `plugin/.claude-plugin/plugin.json`. Workers write only their own `status/`, `reports/` and `pr-bodies/` files in the records folder.
- **Ask the user first, with the exact scope:** creating accounts or VMs, installing into the user's real profile, large downloads, signing in to outside sites, spending money; changing `.claude-plugin/marketplace.json` (it reaches users on their next marketplace update, with no release).
- **Unattended, never:** pushing to `release` or pushing a release tag.
- **Release:** `docs/releasing.md`. A release is ready when no contradiction and no blocker remains, not when a review scan finds nothing. A scan finding enters skill text only if it is a contradiction or a code bug; any other finding becomes an issue or is dropped. One review pass per release, over the diff since the last release: contradictions (between skill files, relay.py and the glossary), code bugs, and kept invariants lost in slimming (the #110 inventory's "stay" rows). After fixing, re-review only what changed, then release; no further full passes (user's ruling, 2026-11-02, after the audit found 48% of 0.3.x skill growth came from scan findings with no incident).
- **Deny list:** none
- **relay.py:** D:/Repos/relay/plugin/tools/relay.py (the main checkout; fast-forward it to `origin/main` after each merge)
