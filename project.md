# Project settings

What relay needs to know about this project. The coordinator and every worker read this file.

- **Repo:** mileschintw/relay, default branch `main`.
- **Language:** talk to the user, and write reports, in Traditional Chinese (繁體中文). Repo files, issues, PR bodies, briefs and the plan are written in English.
- **Checks before done:** `python3 -I tests/test_relay.py` (Windows: `py -3 -I tests/test_relay.py`); `claude plugin validate .`.
- **Test bar:** the checks above pass and each new behaviour in `plugin/tools/relay.py` has a test in `tests/test_relay.py`; skill and doc changes keep README's Layout table and `plugin/GLOSSARY.md` in step.
- **Off limits for workers:** the `release` branch, `relay--v*` tags, and `version` in `plugin/.claude-plugin/plugin.json`. Workers write only their own `status/`, `reports/` and `pr-bodies/` files in the records folder.
- **Ask the user first, with the exact scope:** creating accounts or VMs, installing into the user's real profile, large downloads, signing in to outside sites, spending money; changing `.claude-plugin/marketplace.json` (it reaches users on their next marketplace update, with no release).
- **Unattended, never:** pushing to `release` or pushing a release tag.
- **Release:** README.md, section "Releasing".
- **Deny list:** none
