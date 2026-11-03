Raises `version` to 0.3.4 so installs pick up the work merged since 0.3.3.

## Since 0.3.3

- **Merge right for a round (#114, #146):** the coordinator asks "open the PR and merge once CI passes" once per round and records it in Handover › Merge right, instead of once per lane.
- **Lane kinds and spares (#116, #115):** Now gets a Kind column (run, audit, spare); a pool of spare workers can take lanes started while the user is away; Handover records who holds the main checkout.
- **`ready`:** faster, with partial output when a lookup times out (#118); every committed records file is checked against the deny list, not only PR bodies (#139), and a blocked lane's `doing` is withheld when it matches (#147); a PR body draft changed after the PR opened, and workflows' `on:` lines, get their own hints (#130); one run reads the workflow files once (#169).
- **`waitchecks`:** the checks watch has an overall timeout with its own exit code (#151).
- **CI path tiers (#159, #165):** test.yml runs `test` and `validate` only when a PR touches what they cover; `waitchecks` and `ready` pass a PR whose paths no workflow covers, so `merge` takes it.
- **Windows:** `relay.py` writes stdout and stderr as UTF-8, so a cp950 pipe no longer crashes a command (#161).
- **Alarm only while a worker can move without the user (#140).**
- **Install over HTTPS (#145):** `marketplace.json` clones the plugin over HTTPS, so no SSH key is needed.
- **README (#119, #158):** a one-page product page with a banner; reference sections move to `docs/`.

## Checks

CI on this PR runs the tests and `claude plugin validate .`. The pre-release review pass over `relay--v0.3.3..main` found one blocker, fixed by #165 (PR #170); its review follow-up #169 (PR #171) is in too. No stay rule of the #110 inventory was lost. Three small doc findings are open as #166, #167, #168.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
