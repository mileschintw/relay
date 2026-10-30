# Decisions 2026-10-30: triage of #7, #8, #9, #10

Session: triage-7-10 (local_25b74a50-b6f9-40d5-86ad-82eae30d7c7f), started by the coordinator on the user's words 「有新issue，先開新session檢查triage跟研究需不需要額外拆解spec/ticket」.
Read against `main` @ 422ecff. Each issue's problem is still present.

## Summary

| Issue | Proposed label | Breakdown | `## Files` | Blocked by | Same-section wait | Kind |
|---|---|---|---|---|---|---|
| #7 localcheck | `ready-for-agent` after a body edit (open design points below) | one lane; no spec, no split | present; add `tests/fake_gh.py`, scope notes | none | none | free |
| #8 cwd check, archive rule | `ready-for-agent` | one lane | present; add `app-limits.md` intro line scope | none | none | free |
| #9 drop Last updated; control chars | `ready-for-agent` | one lane | present; scope notes | none | none | free |
| #10 quiet notes | `ready-for-agent` | one lane | present | none | none | free |

None needs `/to-spec` or `/to-tickets`: each is one PR's worth, and its parts must land together (a skill rule plus the tool or template it names). All four can join wave 1 beside #1.

## #7 Finishing a lane when CI cannot run: `relay.py localcheck`

Confirmed: `coordinate/SKILL.md` › Finishing a lane step 4 knows only `gh pr checks --watch`; `relay.py` has no `localcheck`; `checks_state` reports any non-success conclusion as `check failed: <name>`, a billing failure included; `project.md` template has no Local checks line.

Open points the body leaves to the worker (should be settled in the body before `ready-for-agent`):

1. **How a billing failure is told apart.** The rollup gives only conclusion `FAILURE`. Proposal: a failed check whose run has no steps / whose annotation says the job "was not started" because of billing or spending limit is reported by `ready` as `checks could not run (billing)`, under Waiting, not `check failed`. This makes `ready` (`checks_state`, `ready_done`) part of the lane.
2. **The merge sha.** `ready` prints `--match-head-commit` only under Ready to merge, which needs passed checks. Proposal: `localcheck` prints the head sha it tested; the coordinator merges with that sha, after checking it is still the PR head and the status head.
3. **Local checks vs Checks before done.** `project.md` already has **Checks before done**. Proposal: `localcheck` runs the Local checks line when present, else Checks before done; with neither, it fails with a clear message (older records folders have no Local checks line).
4. **Where it runs.** Needs `--checkout <dir>` like `ready`, and the records folder to read `project.md`. Worktree with `core.longpaths=true`; removed even when the checks fail.

Files additions: `tests/fake_gh.py` (`pr comment`, and a billing-failed rollup entry); `plugin/tools/relay.py` scope gains `checks_state`/`ready_done` if point 1 is accepted.

Overlap: #3's second comment mentions the temporary ruling "CI minutes are used up, run checks locally" for its close-out list: it only names that such a ruling gets an end condition; no file overlap. SKILL.md Finishing a lane step 4 (#7) vs step 6 (#3): different steps, mechanical. `relay.py` docstring and `ReadyTests`: mechanical with #1, #2, #3, #9 (each adds its own command or ready section).

## #8 Check every session's cwd after start; never archive one sharing the coordinator's folder

Confirmed: `app-limits.md` has no cwd rule; `SKILL.md` › Starting a lane step 4 checks lanes only and only against another lane's folder; › Consent's archive bullet (snapshot) says nothing on shared folders.

Notes for the body:

- `app-limits.md` line 3 says the shared-worktree rule lives in `SKILL.md`; moving it makes that line wrong. Add to Files: `plugin/skills/coordinate/app-limits.md (new cwd and archive rules; the intro line that lists what SKILL.md holds)`.
- Overlap with #3: #3's second comment proposes the same archive rule ("skip any session whose `cwd` is the coordinator's own worktree") inside a close-out list. Proposal: #8 owns the rule; #3's close-out list points at `app-limits.md` instead of restating it. Different sections (#8: Starting a lane step 4, Consent archive bullet; #3: First turn step 5, Finishing a lane step 6), so no same-section wait; a comment on #3 records the ownership.

## #9 Plan: drop the Last updated line; `ready` warns on control characters

Confirmed: `setup/templates/plan.md` line 3 holds `Last updated: <time from the command in relay:coordinate › Plan>`; `ready` has no encoding check. Worse than the issue says: `cmd_ready` reads `plan.md` with `read_text(encoding="utf-8")` outside any try (the plan-limit count), so invalid UTF-8 crashes `ready` with a traceback today.

Notes for the body:

- `SKILL.md` › Plan never says "Last updated"; its time command is still needed for "since when" and Unattended log times. The skill edit is: nothing stamps the plan's top; times are for the entries that carry one. The acceptance line for the skill already holds and needs no change.
- "`ready` can print the last commit time of `plan.md`": decide in or out. Proposal: out (git log covers it), so the lane has no optional part.
- The check must run before any other read of those files, so invalid UTF-8 gives the warning instead of a crash. Scope: `plan.md`, `briefs/*.md`, `pr-bodies/*.md` as written; `reports/` and `project.md` are also hand-written and could be added.
- The live records `plan.md` still has the line; the coordinator drops it once the lane merges (records, not a lane file).

## #10 Quiet notes: no user message for a worker turn end that changes nothing

Confirmed: `coordinate/SKILL.md` › Following progress has no quiet rule; `work/SKILL.md` › Status says "at each milestone", with no update while waiting on background runs.

Notes for the body:

- `relay.py status` rewrites `time` on every call, so "unchanged" means the `state` field, not the file. The issue already says "the state"; keep it.
- `app-limits.md` line 9: after a long run of notes with no user message the app may stop delivering notes. Quiet turns lengthen such runs; the coordinate rule may want one line saying the alarm still covers it. Not a blocker.

## Dependencies and order

- Hard (blocked-by): none among #7–#10, none against #1–#3.
- Same-section waits: none. Checked sections: coordinate `SKILL.md` First turn step 3 (#1, #2), step 5 (#3); Consent archive bullet (#8); Starting a lane step 1 (#2), step 4 (#8); Following progress (#10); Finishing a lane step 4 (#7), step 6 (#3); Plan (#9). `setup/templates/plan.md`: Roadmap Kind (#1) vs Last updated line (#9).
- Mechanical overlaps: `plugin/tools/relay.py` (docstring, `cmd_ready`'s section dict) and `tests/test_relay.py` with #1, #2, #3, #7, #9; `tests/fake_gh.py` with #1, #2, #3, #7; `setup/templates/plan.md` #1 and #9; `app-limits.md` #8 and #10 (only if #10 adds the line above, a separate bullet).
- Roadmap rows to add: all four Order 1, Kind free.

## User decisions

Asked in one `AskUserQuestion`, 2026-10-30; answers below with the user's words (the option they picked).

1. **Labels.** Question: swap `needs-triage` for `ready-for-agent` on #7–#10 (#7 after its body edit)? User: 「四個都換 (Recommended)」. Done: all four now `enhancement, ready-for-agent`.
2. **#7 design points.** Question: write the four proposals (billing detection in `ready`, merge sha from `localcheck`, Local checks → Checks before done → error, `--checkout` + longpaths + cleanup) into #7's body? User: 「照建議寫進 body (Recommended)」. Done: #7 body gains `## Decisions (triage, 2026-10-30)`; `## Files` gains `tests/fake_gh.py` and the `checks_state` / `ready_done` scope.
3. **Body fixes and the #3 comment.** User picked all four: 「修改 #8 body, 修改 #9 body, 修改 #10 body, 在 #3 留言」. Done:
   - #8: `## Files` scope note for `app-limits.md` (the rules, and its intro line); a line saying #8 owns the archive rule and #3 points at it.
   - #9: `## Decisions (triage, 2026-10-30)`: the UTF-8 crash and check order; printing the last commit time of `plan.md` is out of scope (removed from the Proposal); *Plan* keeps its time command for entries that carry a time.
   - #10: notes that "unchanged" means the `state` field, and the app-limits note-delivery caveat.
   - #3: comment https://github.com/mileschintw/relay/issues/3#issuecomment-6535623675 recording that #8 owns the archive rule and there is no same-section wait.

Not done (not asked, not needed): no dependency links (there are none), no new issues, no roadmap edit (the coordinator adds the four rows, Order 1, Kind free).
