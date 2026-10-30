## Agent skills

### Issue tracker

Issues live in GitHub Issues on `mileschintw/relay`, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

### Multi-session work

Multi-session work: records in the worktree on branch coord (find it with git worktree list; never merged); the coordinator runs /relay:coordinate, workers follow relay:work.
