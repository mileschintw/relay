# CI fallbacks

For a lane on "merge once CI passes" whose CI cannot run or has not started (coordinate `SKILL.md`, *Finishing a lane*). `<N>` is the lane's PR, `<this repo's checkout>` the one `ready` takes (`SKILL.md`).

## Which case

- `ready` says `checks could not run (billing)` or `no CI configured`, or the account is out of minutes or quota: *CI cannot run*.
- `waitchecks` exits 3: the case its line after `no checks appeared` names.

**Asking the user.** At each step below that asks the user, first read the plan's rulings. A ruling that covers the step is the answer: tell the user which ruling settled it (unattended: write it in the Unattended log). Unattended, the lane is Stuck (`unattended.md`) when no ruling covers the step, a ruling says not to merge, or a second `waitchecks` run still finds no checks.

## CI cannot run

1. Ask the user whether to merge on local checks instead. On no: the PR stays open, unmerged, as on "Only open the PR".
2. On their yes: `relay.py localcheck <records> <key> --checkout <this repo's checkout> --comment <N>`.
3. When it passes with no status-head warning, check the head it printed is still the PR head (`gh pr view <N> --json headRefOid`), then `gh pr merge <N> --merge --match-head-commit <that sha>`. Tell the user the lane merged, and go on to *Finishing a lane*'s after-the-merge step.

A failed local check is a failed check: it goes to the user with its output, as in *Finishing a lane* (`waitchecks`'s hint).

## Checks not started

The repo has CI, but none reported on this PR within the CI start wait. Tell the user no check has reported on PR #<N> after the minutes `waitchecks` printed, and ask whether to keep waiting (run `waitchecks` again) or take *CI cannot run*.
