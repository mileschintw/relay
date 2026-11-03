# Layout

Only `plugin/` is installed; everything else is for developing relay.

| Path | What |
|---|---|
| `plugin/skills/setup` | `/relay:setup`: turn relay on in a repo; `templates/` holds the records files it copies |
| `plugin/skills/coordinate` | `/relay:coordinate`: the coordinator; `close-out.md`, `unattended.md`, `compact.md`, `large-outputs.md`, `app-limits.md`, `ci-fallbacks.md` are read on demand |
| `plugin/skills/work` | `relay:work`: what each worker follows |
| `plugin/tools/relay.py` | `status` (a worker's status file), `ready` (what the coordinator can do next, within a 75 s budget, with a Skipped section for what ran past it; also checks records against the deny list and each PR body against its draft), `roadmap` (each open issue's blocked-by and Files section), `localcheck` (the checks, run locally when CI cannot), `waitchecks` (wait for a PR's first check, then watch its checks; passes at once when the workflows' `paths` filters skip every changed path; with none, names the `ci-fallbacks.md` case), `merge` (merge Ready to merge lanes one at a time, stopping on the first problem) |
| `plugin/tools/resume.py` | the `SessionStart` (`compact`) hook: after a compact, points the coordinator or a worker at its records (language line, what to reread) |
| `plugin/hooks/hooks.json` | registers `resume.py` on `SessionStart` with the `compact` matcher |
| `plugin/GLOSSARY.md` | the terms |
| `plugin/.claude-plugin/plugin.json` | the plugin manifest; its `version` decides when users get a new copy ([Releasing](releasing.md)) |
| `.claude-plugin/marketplace.json` | the catalog; its entry installs `plugin/` from the `release` branch |
| `tests/` | `python3 -I tests/test_relay.py`; `fake_gh.py` stands in for `gh` |
| `.github/workflows/test.yml` | CI: the tests (Ubuntu, Windows) and `claude plugin validate .`, each run only when a PR changes the paths it covers (a `changes` job decides) |
| `README.md` | the product page: what relay is for, how it works, install |
| `docs/getting-started.md` | the longer walkthrough and how relay splits work with mattpocock-skills |
| `docs/layout.md` | this table |
| `docs/releasing.md` | how a merge to `main` reaches users |
| `docs/adr/` | decisions and why (ADRs) |
| `docs/social-preview/` | the README banner (`banner.svg`) and the repo's social preview (`social-preview.svg`, its 1280×640 `social-preview.png` upload) |
| `docs/agents/` | the issue tracker, triage labels and domain docs the mattpocock-skills read |
