# CI fallbacks

For a lane on "merge once CI passes" whose CI cannot run or has not started (coordinate `SKILL.md`, *Finishing a lane* step 4). `<N>` is the lane's PR, `<clone>` the local clone you pass `ready`.

## CI cannot run

When `ready` says `checks could not run (billing)` or `no CI configured`, `waitchecks` prints `no CI configured`, or the account is out of minutes or quota:

1. Tell the user and ask whether to merge on local checks instead.
2. On their yes: `relay.py localcheck <records> <key> --checkout <clone> --comment <N>`. A `result: passed, N not run` line names main-checkout-only commands: run them in the main checkout at that head first.
3. When it passes with no status-head warning, check the head it printed is still the PR head (`gh pr view <N> --json headRefOid`), then `gh pr merge <N> --merge --match-head-commit <that sha>`. Tell the user the lane merged, and go on to step 6.

A failed local check is a failed check: it goes to the user with its output, as in step 4.

## Checks not started

When `waitchecks` exits 3 with `no checks appeared` and no `no CI configured` line: the repo has CI, either a workflow under `.github/workflows/` or CI outside Actions (a commit status or check-run on the default branch head), but none reported on this PR within the CI start wait. List the workflows on the default branch (`git ls-tree --name-only origin/<default> .github/workflows/`):

- **Workflow files listed:** read their `on:` lines; when none runs on `pull_request`, take *CI cannot run*.
- **None listed** (CI outside Actions): tell the user the external CI has not reported on PR #<N> after <minutes> minutes, and ask whether to keep waiting or take *CI cannot run*. On keep waiting: run `waitchecks` again.
