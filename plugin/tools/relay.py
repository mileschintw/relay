#!/usr/bin/env python3
"""relay: the scripted steps of multi-session coordination (see skills/coordinate).

  python3 -I relay.py status <records> <key> --state <state> --doing <text>
                             [--branch <b>] [--head <sha>] [--pr-body <path>]
  python3 -I relay.py ready <records> [--repo <owner/name>] [--checkout <dir>] [--plan-limit <bytes>]
  python3 -I relay.py roadmap [--repo <owner/name>]
  python3 -I relay.py localcheck <records> <key> [--checkout <dir>] [--repo <owner/name>]
                                 [--comment <N>]
  python3 -I relay.py waitchecks <records> <N> [--repo <owner/name>]
  python3 -I relay.py waitchecks <records> --push <sha> [--repo <owner/name>]
  python3 -I relay.py merge <records> <key>... [--repo <owner/name>] [--checkout <dir>]
(Windows: py -3 -I ...)

<records> is the records folder (the `coord` worktree): plan.md, briefs/, status/, reports/,
pr-bodies/. <key> names a lane: the number of the first issue it closes (`12`).

status  writes <records>/status/<key>.md, a worker's status file, then reads it back the way
        `ready` does. Run it in the worker's worktree. Fields, one per line:
          - state: parked | working | blocked | review | done
          - branch: --branch, default the current branch (`none` while parked)
          - head: --head, default HEAD's short sha (`none` while parked)
          - PR body draft: --pr-body, default <records>/pr-bodies/<key>.md
          - time: now, `YYYY-MM-DD HH:MM +HHMM`
          - doing: --doing, one line
        Fails (1), writing nothing, on a line break in a value, a head that is not a sha, or a
        detached HEAD with no --branch. With state review or done and a branch and head (not
        `none`), also when `git ls-remote origin <branch>` fails or does not show that head
        (the branch missing on origin, or at another sha), naming the head, origin's sha and
        `git push origin HEAD`; a lane whose plan.md Now Kind is `run`, `audit` or `spare`
        skips this check.

ready   read-only. Prints what the coordinator can do next, the Plan warning and the Default branch
        section first, then one line per lane. When plan.md has a `## Now` table, a done lane
        whose key is not in its first column and whose only line would be under Merged or
        Finished counts as moved to plan-history.md: it gets no line, and one line per section
        gives their count. Any other line it has (a PR still open, an Inconsistent) lists it as
        usual. The sections:
          - Ready for GO: parked lanes whose every dependency is closed as completed. The
            dependencies are the GitHub blocked-by lists of every issue on the brief's `Closes:`
            line (issue <key> when it has none; numeric keys only), minus those issues, plus
            every `#N` on the brief's `Waits for (same section):` line; the brief's
            `Depends on:` line counts only when every one of those lists is empty.
          - Ready for PR: done lanes with no pull request, status head equal to the pushed head.
          - Ready to merge: done lanes whose open PR head is the status head, checks all passed
            (at least one, none pending), no conflict and a body equal to the draft. A PR with
            no checks that CI does not cover (as waitchecks decides) counts as passed: its line
            ends with `(CI does not cover these paths: ...)`.
          - Waiting: parked lanes with an open dependency; a parked spare with no brief
            (`spare, available: waits for a brief`); blocked lanes, with their `doing` line
            (`(doing withheld: a deny-list name)` when it matches the deny list, `(doing
            withheld: deny-list check not run)` when Records reports the deny list);
            done lanes with a conflict, pending or failed checks, a failed lookup, an open PR whose
            body differs from the PR body draft (ends trimmed; the line gives the `gh pr edit`
            command), or a deny list Records reports (`deny-list check not run`). A failed
            check whose job never started (no steps, or an annotation saying it was not started:
            billing, a spending limit) shows as `checks could not run (billing)`, not `check failed`.
            A PR with no checks shows as `no CI configured` when the repo has no Actions workflow
            (`gh api repos/<repo>/actions/workflows`) and no status or check-run on the default
            branch head (`commits/HEAD/status`, `/check-runs`), else as `no checks reported`
            (unless CI does not cover its paths: Ready to merge, above).
          - No status yet: a brief with no status file.
          - Could not parse: a status file that is not valid UTF-8, or has no valid state or no
            branch, head or time; the other lanes are still listed.
          - Merged: done lanes whose PR merged, even when the branch was deleted since (move
            them to plan-history.md).
          - Finished: done lanes whose Now-table Kind is `run`, `audit` or `spare` (GLOSSARY.md,
            **Kind**), with a report file; they get no branch, PR or PR body check, so a missing
            PR or issue is never flagged (without a report: Inconsistent). A lane in a Now table
            with no Kind column, or with an empty cell, is `pr`. A done lane outside the Now table
            has no known kind: it is Finished when its branch was never pushed, it has no PR and
            it has a report (a run, audit or spare moved to plan-history.md), else checked as
            `pr`.
          - Parents: open issues with sub-issues (GitHub's sub_issues_summary), with their
            children's open and closed counts, and whether every child closed as completed. A
            parent is never a lane: a status file keyed on one is Inconsistent and gets no GO.
            While this lookup fails, parked lanes wait instead of getting GO.
          - Owner notes: each parent's body or comment with a line that starts with the owner-note
            marker (GLOSSARY.md), with its link and the block from the marker to the end of that
            body or comment. A failed lookup is listed here and holds nothing.
          - Inconsistent: a done lane's status head that is not the pushed one; done with no report
            file; a lane whose Now Kind is `spare` that has a brief (it took a lane, so its Kind is
            that lane's; done, it is checked as `pr`); a PR head that is not the status head; a PR
            closed without merging; a dependency closed as not planned (it also holds GO); a PR body
            draft with a title line, a closing keyword outside a `Closes #N` line, or `Closes`
            lines that are not exactly one per issue on the brief's `Closes:` line; a line matching
            project.md's deny list (`- **Deny list:** <path>`, one regex per line; an end of the
            match that is a word character must not touch another; leading inline flags such as
            `(?i)` work, `(?x)` with its `#` comments too; printed by line number only).
          - Records: invalid UTF-8, or a control character other than tab, LF and a CR right
            before LF (a bare CR is named so), in project.md, plan.md, plan-history.md,
            briefs/*.md or pr-bodies/*.md, by file and line (for invalid UTF-8, the first bad byte
            only); and mixed line endings (both CRLF and LF) in plan.md, plan-history.md or a
            brief, by file with the count of each. Checked first, so a bad byte is a
            warning, never a crash; a lane whose brief or PR body draft has one also shows as
            lookup failed.
            Also a warning for a Now-table Kind that is not `pr`, `run`, `audit` or `spare`, and
            for a `**Main checkout:**` line in the Now section whose first word (other than
            `none`) is no key of the Now table, each by line number.
            Also a warning when plan.md's Handover > Coordinator line is in neither of its forms
            (the template's `title ..., worktree ..., id ..., mode ....`, or `none`), by line
            number; when the records folder has no .gitattributes, naming the fix; and
            one when the deny list is missing, is not valid UTF-8 (a BOM is fine), or has a line
            that is not a usable pattern, such as one with a zero-length match (`\\b`) (by line
            number, never its text); done lanes then wait, with no deny-list check. And one
            per records file (plan.md, plan-history.md, briefs/*.md, reports/*.md,
            status/*.md) with a line matching the deny list, by line numbers, never the name.
          - Plan: a warning when plan.md is larger than --plan-limit bytes (default 16384, 16 KB).
          - Default branch: one line per workflow whose latest decided push run on the default
            branch (origin/HEAD of --checkout, else of the current folder) failed (`failure`,
            `timed_out` or `startup_failure`). A run decides when it completed as anything but
            `cancelled` or `skipped`: those are passed over, so they never hide an older failure,
            and a newer success clears it. The line gives the workflow, the conclusion, the short
            sha and the run URL (no failed jobs: `gh run list` has none), plus `(a newer run is in
            progress)` when one is and `(newer runs cancelled or skipped)` when one was. From one
            `gh run list --event push` call per `ready`, reading the latest 100 push runs, so a
            workflow with no deciding run among them is not checked. A failed lookup, or no
            origin/HEAD to name the default branch, is one `push run lookup failed` line. All
            green, or no push runs: no section.
            Report only: it changes no lane's section and not the exit code.
          - relay.py: a warning when the git checkout holding project.md's `relay.py:` path
            (relative to --checkout, else the current folder) is behind its origin/<default>,
            with the count and the `git -C <checkout> merge --ff-only` fix. A checkout on another
            branch (or a detached HEAD), or whose default branch has commits of its own, gets that
            said instead, with no command. That checkout is fetched first. The path is a leading
            backticked span, else its text before a trailing `(...)` note. No such line, a
            project.md that is not UTF-8 (a Records warning), a missing folder, or a path outside
            a checkout: no check.
          - Skipped: what ran past ready's time budget ($RELAY_READY_SECONDS, default 75 s, well
            under an agent's 2-minute command limit): the fetch, the relay.py check, Parents, the
            default branch's push runs, each lane by key, and a count of done lanes outside
            plan.md's Now table (no line printed for those, as they are most likely merged or
            finished). Past the budget a running lookup is killed and none starts, so ready still prints every lane's line and the sections it
            sorted in time; a skipped step's or lane's partial findings are dropped (they may be
            wrong), a skipped fetch skips the conflict check as a failed one does, and skipped
            Parents hold every GO.
        After a section's items, `  hint:` lines give the coordinator's next step for the kinds
        of line it holds (READY_HINTS).
        --checkout <dir>: a local clone; `git fetch --prune` there, then `git merge-tree` each
        Ready for PR / Ready to merge branch against the default branch; a conflict moves it to
        Waiting. Pushed heads come from its origin/* refs; without --checkout, or when that
        fetch fails, from one `git ls-remote` per done lane; a failed fetch also skips the
        conflict check, and those lanes' lines end `(conflict check skipped: fetch failed)`.
        Pull requests come from one
        `gh pr list --state all` per run (a branch missing from a full list gets its own `--head`
        lookup).
        --repo defaults to what `gh repo view` finds from the current folder.

roadmap read-only. Prints a table, one row per open issue: `| #N title | blocked-by | files |`,
        ready to copy into the plan's Roadmap. Blocked-by is GitHub's list, a closed blocker
        marked `(closed)`. Files come from the issue body's `## Files`
        section only: one top-level bullet per path, `New:` marks a file the lane creates, a
        trailing `(...)` scopes the change; other lines in the section, nested bullets and fenced
        blocks are skipped, and it ends at the next `#`/`##` heading. A parent (an issue with
        sub-issues) shows `parent`. An issue with no section, or one with no bullet, shows as
        missing, listed again under the table; paths are never inferred. When there are rows, a
        last `hint:` line says how an empty Roadmap is filled from them.

localcheck  the checks CI would run, for when it cannot (billing, quota). In --checkout (default
        the current folder): `git fetch`, a detached worktree at the lane's pushed head (from its
        status file's branch) with core.longpaths on, merge the default branch into it, run
        project.md's `Local checks:` line, else its `Checks before done:` line, then remove the
        worktree, even when a check fails. Commands are the backticked items of the line, split on
        `;`, one per item (an item with two, or with only a `(Windows: `...`)`, is a usage error);
        `(Windows: `...`)` replaces an item's command on Windows; items marked "main checkout
        only" are listed as not run. `(covers: <path>, ...)` in an item names the paths it
        covers (globs, `*` crossing `/`; folders; files): when the lane's diff against the
        default branch (`git diff <base>...<head>`) touches none, it is listed as not needed
        (no covered path changed) and not run; an item with no list always runs. Prints the
        head and base shas and each command's output; --comment <N> also posts that output on
        PR <N>.

waitchecks  waits for PR <N>'s first check, then watches its checks. Polls `gh pr view <N> --json
        statusCheckRollup` now and at 1, 3 and 6 minutes; project.md's `CI start wait: <minutes>`
        line stretches that to 1/6, 1/2 and all of its minutes. As soon as a check exists (queued
        or pending counts), runs `gh pr checks <N> --watch`, keeping only its errors (with no
        terminal it reprints the table every 10 s, to stdout), then prints `gh pr checks <N>`
        once; both calls' errors go to stderr. None at the first poll, and every default-branch
        workflow that runs on `pull_request` has a `paths` or `paths-ignore` filter that skips
        all of the PR's changed paths (`gh api .../pulls/<N>/files`; none under
        .github/workflows/, fewer than 300): prints `CI does not cover these paths` and passes,
        with no CI start wait. None by the last poll: prints `no checks
        appeared`, then one line naming the `ci-fallbacks.md` case: `no CI configured` (as `ready`
        decides) or no workflow under the default branch's .github/workflows/ runs on
        `pull_request` or `pull_request_target` (each file's top-level `on:`): *CI cannot run*;
        one does, there is no workflow file (CI outside Actions), or the lookup failed: *Checks
        not started*. A failed poll is retried at the next one. A watch still running after 20
        times the CI start wait (2 hours by default) is stopped and the table printed.
        --push <sha> waits instead for the default branch's push runs for that commit (`gh run
        list --event push --commit`, the branch from `gh repo view`); a sha of 7 to 39 hex
        characters is first resolved to the full one (`gh api repos/<repo>/commits/<sha> --jq
        .sha`), and the lines print that full sha as for a full one. The runs are polled on
        the same schedule until one appears, then every 30 s until each has completed, within
        the same 20 CI start waits (a failed lookup meanwhile waits for the next poll). Prints
        one line per run (workflow, conclusion, short sha, URL) and, under a failed one
        (`failure`, `timed_out`, `startup_failure`), its failed jobs (`gh run view --json
        jobs`). `cancelled` and `skipped` decide nothing, as in
        `ready`: the line says so; a failure beside them still fails, a success still passes,
        and with nothing else it ends as when no run appeared.

merge   merges lanes one at a time, in the order given. First, every key must be listed under
        `ready`'s Ready to merge and nowhere else (--checkout as for `ready`, default the current
        folder), and given once, or nothing merges; so does a failed `git fetch` there, a
        deny list `ready` reports under Records (one line, by line number), or a deny-list name
        in a records file (one line per file, as `ready` prints it).
        Then, per key, with no wait for checks (Ready to merge already needs them all passed):
        its head still the sha Ready to merge printed; mergeStateStatus `CLEAN` (UNKNOWN, while
        GitHub recomputes after a merge, is asked again after 5, 15 and 30 seconds); `gh pr merge
        <N> --merge --match-head-commit <sha>`; one line with the merge time. A failed `gh pr
        merge` rereads the PR at once: MERGED counts as merged. After a 5xx or `Merge already
        in progress` it is also asked after 10, 20, 30, 60 and 60 seconds, then the merge is
        retried once with the same --match-head-commit (a retry that fails the same way waits
        out those polls again, with no further retry); any other error gets no retry. The first
        key that fails a test gets one line saying why (a merge that still failed: the last
        error), and no later key merges. After the last merge, waits for the default branch's
        push runs for its merge commit as `waitchecks --push` does (project.md's CI start wait,
        read before any merge), and prints them.

Exit: status 0 when written, 1 when a check fails; ready 0 after printing, 2 on a bad
$RELAY_READY_SECONDS; roadmap 0 after printing, 1 when a lookup fails; localcheck 0
when every command passed, else 1 (a command, the merge, a lookup or the comment failed);
waitchecks 0 when the checks passed (or CI does not cover the PR's paths), 1 when one failed,
3 when no check appeared, 4 when a lookup failed (the last poll's, or a watch that failed with
no failed check behind it, a gh error say), 5 when the watch timed out; with --push, 0 when a
push run passed and none failed, 1 when one did (even past the bound), 3 when none appeared or
decided, 4 when the short sha's lookup failed, or the last poll's with none seen, 5 when one
still ran past the bound; merge 0 when every key merged (a failed `gh pr merge` whose PR
reads MERGED counts) and the last merge commit's push run passed, 1 when it stopped (a key
not ready, or a fetch, lookup, merge state or `gh pr merge` that failed, after its one retry
for a 5xx or `Merge already in progress`), and after every key merged: 6 when that push run
failed, 3 when none appeared or decided, 5 when the wait timed out, 4 when the merge commit or
its push run lookup failed;
2 on a usage error (argparse's too, after which waitchecks and merge still print their hint;
ready: a $RELAY_READY_SECONDS that is not a number of seconds; waitchecks: a CI start wait that
is not a number of minutes, or a project.md that is not UTF-8, both or neither of <N> and
--push, a --push that is not 7 to 40 hex characters, or a short one that matches no commit
or more than one;
merge: a CI start wait or project.md as for waitchecks (nothing merged), a key given twice, or
a --checkout that is not a git checkout; localcheck: a project.md
that is not UTF-8, or a checks line with more than one command, only a Windows override, or a
covers list with no path or a second one, in one item) or a missing records folder (status too: it creates only status/ inside it).
waitchecks and merge: an error not named above (a bug, say) exits 4 with one line, never 1;
output the console cannot encode is replaced, not fatal; a last `hint (exit <code>):` line on
stdout gives the coordinator's next step for that exit (EXIT_HINTS).
`gh` is called through $RELAY_GH when set (a command line, for tests).
Standard library only, Python 3.10+.
"""
import argparse
import datetime
import fnmatch
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

STATES = ("parked", "working", "blocked", "review", "done")
FIELDS = ("state", "branch", "head", "PR body draft", "time", "doing")
CLOSING = re.compile(r"\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\b:?\s*#\d+", re.I)
CLOSES_LINE = re.compile(r"^Closes #\d+\s*$")
OWNER_NOTE = re.compile(r"^\*\*Owner action after this set:\*\*", re.M)
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|\r(?!\n)")
LOOKUP_ERRORS = (RuntimeError, ValueError, KeyError, TypeError, OSError, re.error)


READY_SECONDS = 75  # ready's default time budget: well under an agent's 2-minute command limit
TIMED_OUT = 124  # run's exit code for a command killed, or never started, past `deadline`,
# or killed past its own `timeout`
deadline = None  # the time.monotonic() ready's lookups must end by; None outside ready
timed_out = []  # the commands run killed or skipped past `deadline`, in order


def run(cmd, cwd=None, timeout=None):
    """(exit code, stdout, stderr). Past `deadline`, a running command is killed and a new one
    never starts: both return TIMED_OUT and are added to `timed_out`. Past <timeout> seconds, a
    command is killed and returns TIMED_OUT, not added."""
    left = None if deadline is None else deadline - time.monotonic()
    if left is not None and left <= 0:
        timed_out.append(cmd)
        return TIMED_OUT, "", "skipped: ready's time budget is spent"
    by_deadline = timeout is None or (left is not None and left <= timeout)
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         encoding="utf-8")
    try:
        out, err = p.communicate(timeout=left if by_deadline else timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        try:  # a grandchild holding the pipes open must not hold ready past its budget
            p.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        if not by_deadline:
            return TIMED_OUT, "", f"timed out after {timeout:g} s"
        timed_out.append(cmd)
        return TIMED_OUT, "", "timed out: ready's time budget is spent"
    except BaseException:  # as subprocess.run: an interrupt leaves no child running
        p.kill()
        raise
    return p.returncode, out, err


def gh_base():
    """The gh command line: $RELAY_GH when set, else `gh`."""
    return [t.strip('"') for t in shlex.split(os.environ.get("RELAY_GH", "gh"), posix=False)]


def gh_raw(*args):
    """gh's stdout as text; RuntimeError when it fails."""
    code, out, err = run(gh_base() + list(args))
    if code:
        raise RuntimeError(f"gh {' '.join(args)}: {err.strip() or out.strip()}")
    return out


def gh(*args, jsonl=False):
    out = gh_raw(*args)
    if jsonl:
        return [json.loads(line) for line in out.splitlines() if line.strip()]
    return json.loads(out) if out.strip() else None


def parse_status(text):
    fields = {}
    for line in text.splitlines():
        m = re.match(r"- ([A-Za-z ]+): (.*)$", line)
        if m and m.group(1) in FIELDS:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def brief_issues(records, key, label):
    path = records / "briefs" / f"{key}.md"
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if label in line:
            return [int(n) for n in re.findall(r"#(\d+)", line.split(label, 1)[1])]
    return []


# status ---------------------------------------------------------------------------------------

def cmd_status(a):
    records = pathlib.Path(a.records)
    if not records.is_dir():
        print(f"no records folder at {records}", file=sys.stderr)
        return 2
    parked = a.state == "parked"
    branch = a.branch
    head = a.head
    if branch is None:
        code, out, _ = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        branch = "none" if parked else out.strip()
        if not parked and (code or branch == "HEAD"):
            return fail("detached HEAD or no git checkout: pass --branch")
    if branch == "coord" and not parked:
        return fail("this is the records branch: run status in your lane's worktree")
    if head is None:
        code, out, _ = run(["git", "rev-parse", "--short", "HEAD"])
        head = "none" if parked else out.strip()
    if head != "none" and not re.fullmatch(r"[0-9a-f]{7,40}", head):
        return fail(f"head is not a sha: {head!r}")
    pr_body = a.pr_body or str(records / "pr-bodies" / f"{a.key}.md")
    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z")
    values = dict(zip(FIELDS, (a.state, branch, head, pr_body, now, a.doing)))
    if any("\n" in v or "\r" in v for v in values.values()):
        return fail("a value holds a line break")
    text = f"# {a.key} status\n\n" + "".join(f"- {k}: {v}\n" for k, v in values.items())
    if parse_status(text) != values:
        return fail("the status would not read back as written")
    if a.state in ("review", "done") and head != "none" and branch != "none":
        kinds = now_kinds(records / "plan.md") or {}
        if kinds.get(a.key, "pr") not in NO_PR_KINDS:
            try:
                pushed = pushed_head(None, branch)
            except RuntimeError as e:
                return fail(f"could not check the head on origin: {e}")
            if not pushed.startswith(head):
                where = (f"origin/{branch} is at {pushed[:12]}" if pushed
                         else f"origin has no branch {branch}")
                return fail(f"head {head} is not on origin: {where}. Push it with "
                            "`git push origin HEAD`, then rerun this status command.")
    out_path = records / "status" / f"{a.key}.md"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"wrote {out_path}")
    print(text, end="")
    return 0


# ready ----------------------------------------------------------------------------------------

def check_pr_body(path, closes=None, deny=None):
    """Problems with a PR body draft. closes: the issues the brief's Closes line lists (None or []:
    not known). deny: regex patterns; an end of a match that is a word character must not touch
    another one, an end that is not one may (so `acme` misses `acmecorp`, while `@acmebot` matches
    `dev@acmebot` and `\\.internal` matches `build.internal`); a hit is reported by line number
    only."""
    p = pathlib.Path(path)
    if not p.exists():
        return ["no PR body draft"]
    lines = p.read_text(encoding="utf-8").splitlines()
    problems = []
    if lines and lines[0].startswith("# "):
        problems.append("PR body starts with a title line")
    found = {}
    for i, l in enumerate(lines, 1):
        if CLOSES_LINE.match(l):
            found.setdefault(int(re.search(r"\d+", l).group()), []).append(i)
        elif CLOSING.search(l):
            problems.append(f"PR body line {i}: closing keyword outside a `Closes #N` line")
    if not found:
        problems.append("PR body has no `Closes #N` line")
    if closes:
        for n in closes:
            if n not in found:
                problems.append(f"PR body has no `Closes #{n}` line (the brief's Closes lists it)")
            elif len(found[n]) > 1:
                problems.append(f"PR body lines {found[n]}: `Closes #{n}` more than once")
        for n, where in sorted(found.items()):
            if n not in closes:
                problems.append(f"PR body line {where[0]}: `Closes #{n}`, but the brief's Closes does not list it")
    regexes = [deny_regex(pat) for pat in deny or []]
    hits = sorted({i for i, l in enumerate(lines, 1) for rx in regexes if rx.search(l)})
    if hits:
        problems.append(f"PR body lines {hits}: a deny-list name (lines only, never the name)")
    return problems


LEADING_FLAGS = re.compile(r"(?:\(\?[aiLmsux]+\))+")
DENY_PROBE = "Aa1_ .,-@#/\té中()[] a.Z-9@b_c"


def deny_regex(pat):
    """Deny-list pattern <pat> compiled inside check_pr_body's boundary wrapper, case-insensitive.
    Leading global flags such as `(?i)` move to the front of the wrapper, the only place Python
    accepts them; under `(?x)` a newline ends the pattern, so a `#` comment stays inside it.
    re.error for a pattern the wrapper cannot hold whole (it would break out of its group, as
    `a)|(b` does), or that matches empty text or gives a zero-length match in DENY_PROBE (as
    `\\b` does): every line would hit it."""
    m = LEADING_FLAGS.match(pat)
    flags, pat = (m.group(), pat[m.end():]) if m else ("", pat)
    re.compile(flags + pat)
    end = "\n" if "x" in flags else ""
    rx = re.compile(rf"{flags}(?:(?<!\w)|(?=\W))(?:{pat}{end})(?:(?!\w)|(?<=\W))", re.I)
    if rx.search("") or any(h.start() == h.end() for h in rx.finditer(DENY_PROBE)):
        raise re.error("matches empty text")
    return rx


def deny_patterns(records):
    """The patterns of the deny list project.md names (`- **Deny list:** <path>`), else [].
    One trailing period, as the template's lines end, is dropped: `none.` means none. The file
    is UTF-8, a leading BOM dropped. Invalid UTF-8, or a line deny_regex refuses, raises
    ValueError naming the file and the line number, never its text."""
    project = records / "project.md"
    if not project.exists():
        return []
    m = re.search(r"^- \*\*Deny list:\*\*[ \t]*(.*?)\s*$", project.read_text(encoding="utf-8"), re.M)
    value = m.group(1).strip('`"') if m else ""
    value = (value[:-1] if value.endswith(".") else value).strip().strip('`"')
    if value.lower() in ("", "none"):
        return []
    path = pathlib.Path(value)
    path = path if path.is_absolute() else records / path
    if not path.is_file():
        raise FileNotFoundError(f"project.md's deny list {path} is not a file")
    data = path.read_bytes().removeprefix(b"\xef\xbb\xbf")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        n = data.count(b"\n", 0, e.start) + 1
        raise ValueError(f"project.md's deny list {path.name} line {n} is not valid UTF-8") from None
    pats = []
    for n, line in enumerate(text.splitlines(), 1):
        pat = line.strip()
        if not pat or pat.startswith("#"):
            continue
        try:
            deny_regex(pat)
        except re.error as e:
            raise ValueError(f"project.md's deny list {path.name} line {n} is not a usable "
                             "pattern (the error is not shown: it can quote the name)") from None
        pats.append(pat)
    return pats


def records_deny_hits(records, deny):
    """One line per records file the coordinator commits (plan.md, plan-history.md, briefs,
    reports, status) with a line matching a <deny> pattern, by file and line numbers, never the
    name; [] when <deny> is empty. PR body drafts are checked per lane, by check_pr_body."""
    regexes = [deny_regex(pat) for pat in deny or []]
    if not regexes:
        return []
    paths = [records / "plan.md", records / "plan-history.md",
             *(p for d in ("briefs", "reports", "status") for p in sorted((records / d).glob("*.md")))]
    found = []
    for path in paths:
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        hits = sorted({i for i, l in enumerate(lines, 1) for rx in regexes if rx.search(l)})
        if hits:
            found.append(f"{path.relative_to(records).as_posix()} lines {hits}: a deny-list name "
                         "(lines only, never the name)")
    return found


def pushed_head(checkout, branch):
    """The sha of origin's <branch>, "" when origin has no such branch; RuntimeError when
    ls-remote fails (no repo, no network), so the lane reads lookup failed, not unpushed."""
    code, ls, err = run(["git", "ls-remote", "origin", f"refs/heads/{branch}"], cwd=checkout)
    if code:
        raise RuntimeError(f"git ls-remote origin {branch}: {err.strip() or ls.strip()}")
    return ls.split()[0] if ls.strip() else ""


PR_FIELDS = "number,state,headRefOid,mergeable,statusCheckRollup,body"
PR_LIST_MIN, PR_LIST_PER_LANE = 100, 3  # `ready`'s one PR list: --limit max(MIN, PER_LANE * lanes)


def branch_prs(repo, branch):
    return gh("pr", "list", "--repo", repo, "--head", branch, "--state", "all", "--json",
              PR_FIELDS) or []


class ReadyLookups:
    """What `ready` looks up once per run instead of once per done lane: pushed heads from the
    checkout's just-fetched origin/* refs (ls-remote per branch without a checkout, or when the
    fetch or the ref read failed), and every PR from one `gh pr list --state all`. In a full
    list, a branch with no merged PR there gets its own lookup, since older PRs may be cut off.
    A failed list fails each lane that asks for it; one that timed out is asked for again, so
    each such lane times out too and `ready` lists it as skipped. The default branch's workflow
    texts and no_ci's answer, for PRs with no checks, are kept the same way (#169)."""

    def __init__(self, checkout, fetched, lanes):
        self.checkout, self.limit = checkout, max(PR_LIST_MIN, PR_LIST_PER_LANE * lanes)
        self.use_refs, self.heads = bool(checkout and fetched), None
        self.index, self.full, self.error = None, False, None
        self.kept = {}

    def once(self, fn, repo):
        """fn(repo), or what it returned or raised earlier this run; a call that timed out is not
        kept."""
        value = self.kept.get((fn, repo))
        if (fn, repo) not in self.kept:
            before = len(timed_out)
            try:
                value = fn(repo)
            except LOOKUP_ERRORS as e:
                value = e
            if len(timed_out) == before:
                self.kept[fn, repo] = value
        if isinstance(value, Exception):
            raise value
        return value

    def no_ci(self, repo):
        return self.once(no_ci, repo)

    def workflow_texts(self, repo):
        return self.once(workflow_texts, repo)

    def pushed(self, branch):
        if self.use_refs and self.heads is None:
            code, out, _ = run(["git", "for-each-ref", "--format=%(refname:lstrip=3) %(objectname)",
                                "refs/remotes/origin"], cwd=self.checkout)
            self.use_refs = not code
            self.heads = dict(ln.split() for ln in out.splitlines() if ln.strip())
        if not self.use_refs:
            return pushed_head(self.checkout, branch)
        return self.heads.get(branch, "")

    def prs(self, repo, branch):
        if self.error:
            raise RuntimeError(self.error)
        if self.index is None:
            before = len(timed_out)
            try:
                listed = gh("pr", "list", "--repo", repo, "--state", "all", "--limit",
                            str(self.limit), "--json", "headRefName," + PR_FIELDS) or []
            except LOOKUP_ERRORS as e:
                if len(timed_out) == before:
                    self.error = str(e)
                raise
            self.full, self.index = len(listed) >= self.limit, {}
            for p in listed:
                self.index.setdefault(p["headRefName"], []).append(p)
        listed = self.index.get(branch, [])
        if not self.full or any(p["state"].upper() == "MERGED" for p in listed):
            return listed
        return branch_prs(repo, branch)


def dependencies(records, key, repo):
    """(issue numbers, source): the GitHub blocked-by of every issue the lane closes (the brief's
    `Closes:` line, else issue <key>), minus those issues; the brief's `Depends on:` when every
    list is empty (source "brief"); plus the brief's `Waits for (same section):` either way."""
    blocked, source = set(), "github"
    closes = brief_issues(records, key, "Closes:") or ([int(key)] if key.isdigit() else [])
    for n in closes:
        blocked |= {b["number"] for b in gh("api", f"repos/{repo}/issues/{n}/dependencies/blocked_by") or []}
    deps = blocked - set(closes)
    if not blocked:
        deps, source = set(brief_issues(records, key, "Depends on:") or []), "brief"
    waits = brief_issues(records, key, "Waits for (same section):") or []
    return sorted(deps | set(waits)), source


def default_branch(checkout):
    code, out, _ = run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=checkout)
    return out.strip() if not code else "origin/main"


def conflicts(checkout, branch):
    code, out, err = run(["git", "merge-tree", "--write-tree", "--name-only",
                          default_branch(checkout), f"origin/{branch}"], cwd=checkout)
    if code == 0:
        return []
    if code == 1:
        files = []
        for line in out.splitlines()[1:]:
            if not line.strip():
                break
            files.append(line.strip())
        return files or ["(conflict)"]
    return [f"merge-tree failed: {err.strip()}"]


NOT_STARTED = re.compile(r"was not started|spending limit|payments have failed", re.I)


def never_started(check, repo):
    """True when a failed check's job never ran: no steps, or an annotation saying it was not
    started (billing, a spending limit). The rollup alone says only FAILURE. A failed lookup
    counts as a real failure."""
    m = re.search(r"/job/(\d+)", check.get("detailsUrl") or "")
    if not (m and repo):
        return False
    try:
        job = gh("api", f"repos/{repo}/actions/jobs/{m.group(1)}") or {}
        if not job.get("steps"):
            return True
        notes = gh("api", f"repos/{repo}/check-runs/{m.group(1)}/annotations") or []
    except (RuntimeError, ValueError, OSError):
        return False
    return any(NOT_STARTED.search(n.get("message") or "") for n in notes)


def no_ci(repo):
    """True when the repo has no GitHub Actions workflow and nothing reported on the default
    branch head (`commits/HEAD`: a commit status or check-run means CI outside Actions). A
    failed lookup counts as CI existing, so the PR keeps waiting on checks."""
    if not repo:
        return False
    try:
        if (gh("api", f"repos/{repo}/actions/workflows") or {}).get("total_count", 1) != 0:
            return False
        return all((gh("api", f"repos/{repo}/commits/HEAD/{kind}") or {}).get("total_count", 1) == 0
                   for kind in ("status", "check-runs"))
    except (RuntimeError, ValueError, OSError, AttributeError):
        return False


ON_LINE = re.compile(r"""^["']?on["']?\s*:(.*)$""")
PR_EVENT = re.compile(r"\bpull_request(?:_target)?\b")
PR_EVENT_ITEM = re.compile(r"""^\s*(?:-\s*)?["']?pull_request(?:_target)?["']?\s*(?::|$)""")


def indent(line):
    return len(line) - len(line.lstrip())


def on_block(text):
    """Workflow text's top-level `on:`: (its inline value, the lines below that belong to it),
    comments stripped; None when there is none."""
    lines = [re.sub(r"(^|\s)#.*", "", ln).rstrip() for ln in text.lstrip("﻿").splitlines()]
    for i, line in enumerate(lines):
        m = ON_LINE.match(line)
        if not m:
            continue
        block = []
        for child in lines[i + 1:]:
            if child:
                if not child[0].isspace() and not child.startswith(("-", "]", "}")):
                    break
                block.append(child)
        return m.group(1).strip(), block
    return None


def runs_on_pull_request(text):
    """True when workflow text's top-level `on:` names `pull_request` or `pull_request_target`
    (counting both errs toward asking the user): inline (`on: pull_request`, a flow list or map,
    which may run on over the lines below) or as a child key or list item."""
    return bool(pull_request_filters(text))


PATHS_KEY = re.compile(r"""^\s*["']?(paths(?:-ignore)?)["']?\s*:(.*)$""")


def unquote(item):
    item = item.strip()
    return item[1:-1] if len(item) > 1 and item[0] == item[-1] and item[0] in "'\"" else item


def paths_filter(lines):
    """(`paths` or `paths-ignore`, its patterns) from the lines under a pull_request key; None
    when it has neither, both, an empty list or a form not read here (a flow list over lines)."""
    level = min(map(indent, lines), default=0)
    found = []
    for i, line in enumerate(lines):
        m = PATHS_KEY.match(line)
        if not m or indent(line) != level:
            continue
        value = m.group(2).strip()
        if value.startswith("["):
            if not value.endswith("]"):
                return None
            items = [unquote(v) for v in value[1:-1].split(",") if v.strip()]
        elif value:
            items = [unquote(value)]
        else:
            items = []
            for c in lines[i + 1:]:
                if indent(c) < level or (indent(c) == level and not c.lstrip().startswith("-")):
                    break
                if c.lstrip().startswith("-"):
                    items.append(unquote(c.lstrip()[1:]))
        found.append((m.group(1), items))
    return found[0] if len(found) == 1 and found[0][1] else None


def pull_request_filters(text):
    """One entry per `pull_request` or `pull_request_target` event under workflow text's
    top-level `on:`: its paths_filter, or None when it has none (or an inline value, read as
    none); empty when the workflow does not run on either."""
    found = on_block(text)
    if not found:
        return []
    inline, block = found
    if inline:
        return [None] * len(PR_EVENT.findall(" ".join([inline] + block)))
    top = min(map(indent, block), default=0)
    filters = []
    for i, line in enumerate(block):
        if indent(line) != top or not PR_EVENT_ITEM.match(line):
            continue
        sub = []
        for c in block[i + 1:]:
            if indent(c) <= top:
                break
            sub.append(c)
        bare = line.lstrip().startswith("-") or line.partition(":")[2].strip()
        filters.append(None if bare else paths_filter(sub))
    return filters


def path_pattern(pattern):
    """A GitHub path filter pattern as a regex: `*` any characters but `/`, `**` any, `**/` any
    folders or none, `?` and `+` zero-or-one and one-or-more of the character before, `[...]` a
    character class."""
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] in "?+":
            out.append(pattern[i])
            i += 1
        elif pattern[i] == "[" and "]" in pattern[i + 1:]:
            end = pattern.index("]", i + 1)
            out.append(pattern[i:end + 1])
            i = end + 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out))


def path_filter_matches(patterns, path):
    """True when the last of patterns that matches path is not a `!` one."""
    hit = False
    for p in patterns:
        if path_pattern(p.removeprefix("!")).fullmatch(path):
            hit = not p.startswith("!")
    return hit


PR_FILES_LIMIT = 300  # GitHub's paths filters see only this many changed files


def uncovered_line(pr, repo, texts_of=None):
    """The line saying CI does not cover PR <pr>: every default-branch workflow that runs on
    pull_request has a paths filter that none of its changed paths (renames' old paths too)
    passes. None when one may run: no such workflow, one with no filter, a changed path under
    .github/workflows/ (the PR may change a filter), PR_FILES_LIMIT changed paths or more, no
    changed path, or a failed lookup. `texts_of`: what reads the workflow texts, workflow_texts
    by default (ReadyLookups keeps them for the whole `ready` run)."""
    try:
        texts = (texts_of or workflow_texts)(repo)
        filters = {f: fs for f, fs in ((f, pull_request_filters(t)) for f, t in texts.items())
                   if fs}
        each = [f for fs in filters.values() for f in fs]
        if not each or None in each:  # no PR workflow, or one with no filter: skip the PR lookup
            return None
        paths = list(dict.fromkeys(p for p in gh_raw(
            "api", f"repos/{repo}/pulls/{pr}/files", "--paginate",
            "--jq", ".[] | .filename, (.previous_filename // empty)").splitlines() if p))
        if (not paths or len(paths) >= PR_FILES_LIMIT
                or any(p.startswith(".github/workflows/") for p in paths)):
            return None
        for kind, patterns in each:
            hits = [path_filter_matches(patterns, p) for p in paths]
            if (any(hits) if kind == "paths" else not all(hits)):
                return None
    except LOOKUP_ERRORS:
        return None
    return (f"CI does not cover these paths: the {len(paths)} changed path(s) are outside the "
            f"paths filters of {', '.join(filters)}; no checks to wait for")


def workflow_texts(repo):
    """{path: text} for each .yml or .yaml file in the default branch's .github/workflows/, none
    when the folder is missing. Raises LOOKUP_ERRORS."""
    try:
        listed = gh("api", f"repos/{repo}/contents/.github/workflows")
    except RuntimeError as e:
        if "HTTP 404" not in str(e):
            raise
        listed = None
    if not isinstance(listed, list):  # no folder, or a file by that name
        listed = []
    return {f["path"]: gh_raw("api", "-H", "Accept: application/vnd.github.raw+json",
                              f"repos/{repo}/contents/{f['path']}")
            for f in listed if f.get("type") == "file" and f["name"].endswith((".yml", ".yaml"))}


def ci_case(repo):
    """Which ci-fallbacks.md case a PR with no checks is, from the default branch's workflow
    files (their `on:` lines) and no_ci: one line naming the case."""
    if no_ci(repo):
        return ("no CI configured: no Actions workflow and nothing reported on the default branch "
                "head: take *CI cannot run*")
    try:
        texts = workflow_texts(repo)
        files = list(texts)
        on_pr = [f for f, text in texts.items() if runs_on_pull_request(text)]
    except LOOKUP_ERRORS as e:
        return f"workflow lookup failed ({e}): take *Checks not started*"
    if not files:
        return ("no workflow file on the default branch (CI outside Actions): take *Checks not "
                "started*")
    if not on_pr:
        return (f"no workflow on the default branch runs on a pull_request event "
                f"({', '.join(files)}): take *CI cannot run*")
    return (f"a workflow on the default branch runs on a pull_request event ({', '.join(on_pr)}): "
            "take *Checks not started*")


def checks_state(rollup, repo=None, no_ci_of=None):
    if not rollup:
        return "no CI configured" if (no_ci_of or no_ci)(repo) else "no checks reported"
    billing = []
    for c in rollup:
        status = (c.get("status") or "COMPLETED").upper()
        result = (c.get("conclusion") or c.get("state") or "").upper()
        name = c.get("name") or c.get("context")
        if status != "COMPLETED" or result in ("", "PENDING", "EXPECTED", "QUEUED"):
            return "checks pending"
        if result not in ("SUCCESS", "NEUTRAL", "SKIPPED"):
            if not never_started(c, repo):
                return f"check failed: {name}"
            billing.append(name)
    return f"checks could not run (billing): {', '.join(billing)}" if billing else "passed"


def check_encoding(path, name, endings=False):
    """Warnings for invalid UTF-8 or a stray control character in a hand-written record; with
    endings, also for a file whose lines end in both CRLF and LF."""
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        line = data.count(b"\n", 0, e.start) + 1
        return [f"{name} line {line}: invalid UTF-8 (byte {data[e.start]:#04x})"]
    out = []
    for m in CONTROL.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        what = "bare CR" if m.group() == "\r" else f"control character U+{ord(m.group()):04X}"
        out.append(f"{name} line {line}: {what}")
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    if endings and crlf and lf:
        out.append(f"{name}: mixed line endings ({crlf} CRLF, {lf} LF)")
    return out


# cmd_ready's output sections, in print order. One per line, so lanes adding a section don't conflict.
# cmd_ready prints Plan and Default branch before the lane list (a long output gets cut; the
# warnings must survive).
READY_SECTIONS = (
    "Plan",
    "Default branch",
    "Ready for GO",
    "Ready for PR",
    "Ready to merge",
    "Waiting",
    "Skipped",
    "No status yet",
    "Merged",
    "Finished",
    "Parents",
    "Owner notes",
    "Inconsistent",
    "Could not parse",
    "Records",
    "relay.py",
)


# A lane's kind in plan.md's Now table (GLOSSARY.md, **Kind**); an empty cell, or no Kind column,
# is `pr`. The others close no issue and open no PR, so `ready` never flags them for either.
LANE_KINDS = ("pr", "run", "audit", "spare")
NO_PR_KINDS = LANE_KINDS[1:]
MAIN_CHECKOUT = re.compile(r"[-*\s]*Main checkout:\**\s*(.*)$")


def now_section(plan):
    """plan.md's `## Now` section as {"rows": [(line number, key, kind)], "checkout": (line
    number, holder key or None) or None}, or None when plan.md is missing or has no `## Now`
    section. A kind is its cell lowercased, `pr` when empty, unknown ones kept as written."""
    if not plan.is_file():
        return None
    now = None
    inside = False
    kind_col = None
    for n, line in enumerate(plan.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if re.match(r"#{1,2}\s", line):
            inside = re.fullmatch(r"##\s+Now\s*", line.rstrip()) is not None
            if inside:
                now, kind_col = {"rows": [], "checkout": None}, None
        elif inside and line.lstrip().startswith("|"):
            cells = [c.strip().strip("`*") for c in line.strip().strip("|").split("|")]
            key = cells[0].lstrip("#")
            if key.lower() == "key":
                kind_col = next((i for i, c in enumerate(cells) if c.lower() == "kind"), None)
            elif key and not set(key) <= set("-: "):
                kind = cells[kind_col].lower() if kind_col is not None and kind_col < len(cells) else ""
                now["rows"].append((n, key, kind or LANE_KINDS[0]))
        elif inside and (m := MAIN_CHECKOUT.match(line)):
            holder = (m.group(1).split() or ["none"])[0].strip("`*#.,;")
            now["checkout"] = (n, None if holder.lower() in ("none", "") else holder)
    return now


def now_kinds(plan):
    """{key: kind} for plan.md's Now table, or None when plan.md is missing or has no `## Now`
    section."""
    now = now_section(plan)
    return None if now is None else {key: kind for _, key, kind in now["rows"]}


def now_keys(plan):
    """The keys in the first column of plan.md's `## Now` table, or None when plan.md is missing
    or has no `## Now` section."""
    kinds = now_kinds(plan)
    return None if kinds is None else set(kinds)


def now_problems(plan):
    """Records lines for plan.md's Now section: a kind not in LANE_KINDS, and a Main checkout
    holder that is no key of the Now table."""
    now = now_section(plan)
    if now is None:
        return []
    out = [f"plan.md line {n}: Now kind `{kind}` for {key} is not one of {', '.join(LANE_KINDS)}"
           for n, key, kind in now["rows"] if kind not in LANE_KINDS]
    if now["checkout"] and now["checkout"][1] is not None:
        n, holder = now["checkout"]
        if holder not in {key for _, key, _ in now["rows"]}:
            out.append(f"plan.md line {n}: Main checkout names lane {holder}, which is not in Now")
    return out


# A push run conclusion `ready` reports under Default branch. `cancelled` and `skipped` are
# neither failure nor success: `ready` passes over them, so they never hide an older failure.
PUSH_RUN_FAILED = ("failure", "timed_out", "startup_failure")
PUSH_RUN_PASSED_OVER = ("cancelled", "skipped")
PUSH_RUN_LIMIT = 100  # the push runs `ready` reads, newest first: enough to reach each workflow's
# latest decided one


# The coordinator's next step for each kind of `ready` line, printed as `  hint:` lines after the
# section's items: (section, a regex one of its items must match, hint). Each hint prints once.
# The regexes are anchored to the line's own shape, so text a line quotes (a blocked lane's
# `doing`) or a lookup failure in the section never picks another kind's hint.
READY_HINTS = (
    ("Plan", "", "do one pruning pass of everything else: move each entry that is DONE or "
     "CONFIRMED (a merged lane, a done wave, a process log) to the end of plan-history.md, "
     "leaving a one-line pointer"),
    ("Default branch", rf"^.+: push run ({'|'.join(PUSH_RUN_FAILED)}) at \S+: ", "a failed push "
     "run on the default branch: tell the user once per line (workflow and sha) and add the line "
     "to each PR-and-merge question; merging stays their call (unattended: `unattended.md`)"),
    ("Ready for GO", "", "send each `GO #<key>` to its worker (coordinate's *Finishing a lane* "
     "step 6); while Handover's mode is paused, hold it and send it once the user resumes"),
    ("Ready for PR", "", "coordinate's *Finishing a lane* step 1, when nothing for its key is "
     "under Inconsistent or Waiting"),
    ("Ready to merge", "", "coordinate's *Finishing a lane* step 4, **Merge**: run `relay.py "
     "merge` in the background, keys in merge order"),
    ("Waiting", r"^\S+: blocked: ", "a blocked lane's question goes to the user as options with "
     "your recommendation (unattended: `unattended.md`)"),
    ("Waiting", r"^\S+: (conflicts with the default branch|PR #\d+ has a merge conflict)",
     "a conflict: message its worker to catch up, push, and write `done` again"),
    ("Waiting", r"^\S+: lookup failed: ", "a lookup failure: rerun `ready`"),
    ("Waiting", r"^\S+: PR #\d+ check failed", "a failed check goes to the user with the watch "
     "output"),
    ("Waiting", r"^\S+: PR #\d+ (checks could not run|no CI configured|no checks reported)",
     "a CI fallback: follow `ci-fallbacks.md`; its *Which case* says which applies"),
    ("Waiting", r"^\S+: (PR #\d+ checks pending|parked on )", "`checks pending` and a parked "
     "lane's open dependency need nothing"),
    ("Waiting", r"^\S+: PR #\d+ body differs from its draft", "the draft changed after the PR "
     "opened: run the line's `gh pr edit`, after fixing the draft first when `ready` flags its PR "
     "body under Inconsistent"),
    ("Waiting", r"^\S+: spare, available: ", "a spare needs nothing until a lane needs a "
     "worker: write that lane's brief as `briefs/<the spare's key>.md`, set the spare's Now "
     "Kind to that lane's (`pr` unless it is a run or audit), and send `GO #<the spare's key>`"),
    ("Waiting", r"^\S+: deny-list check not run", "deny-list check not run: follow the deny-list "
     "line under Records, and rerun `ready` only after the user says the deny list is fixed"),
    ("Skipped", "", "the machine is likely busy (builds, low memory): rerun `ready` once it is "
     "quieter, or in the background with a larger $RELAY_READY_SECONDS; until then a skipped "
     "lane's state is its status file, and its line above"),
    ("No status yet", "", "a lane in Now stays `started` until its worker writes one; a brief "
     "with no session is a lane not started (*Starting a lane*, on the user's yes) or one "
     "stopped (move it to plan-history.md)"),
    ("Merged", "", "coordinate's *Finishing a lane* step 6, for a lane still in Now"),
    ("Finished", "", "a lane that closes no issue and opens no PR: read its report, tell the "
     "user, release the Main checkout if it held it, and move it from Now to plan-history.md"),
    ("Parents", r"^#\d+ ", "a parent gets one Roadmap row with Kind `parent` and no brief or "
     "worker; its children are the lanes"),
    ("Parents", r"every child closed as completed", "every child closed as completed: ask the "
     "user before closing the parent (*Consent*)"),
    ("Owner notes", r"^#\d+ http", "copy each one plan.md's *Waiting for the user's decision* "
     "lacks into it, with its link; owner-only work stays an owner note on its parent: it gets "
     "no lane and no Roadmap row"),
    ("Inconsistent", "", "fix the plan line it contradicts, or message the lane's worker when "
     "its own files are wrong"),
    ("Inconsistent", r"PR body", "a PR body problem: message its worker to fix the draft, push, "
     "and write `done` again"),
    ("Could not parse", "", "message its worker to rerun its last `relay.py status`; never edit "
     "a status file by hand"),
    ("Records", r"^(plan\.md|plan-history\.md|briefs/)", "in plan.md, plan-history.md or a "
     "brief: fix that line with the Edit tool (mixed line endings: rewrite the whole file as "
     "UTF-8 with LF endings), rerun `ready`, and commit the records"),
    ("Records", r"^pr-bodies/", "in a PR body draft: message its worker to fix that line in the "
     "draft and write `done` again, since `ready` checks the draft before a PR opens; open no PR "
     "for that lane until `ready` no longer flags it"),
    ("Records", r"^(reports|status)/.*a deny-list name", "a deny-list name in a worker's report or "
     "status file: message its worker to fix that line (a status: rerun its last `relay.py "
     "status` with a `--doing` that leaves the name out); commit the records only once `ready` "
     "no longer flags it"),
    ("Records", r"^plan\.md line \d+: Main checkout names lane ", "a Main checkout holder not "
     "in Now: release it (`none`), or name the lane in Now that holds it"),
    ("Records", r"^plan\.md line \d+: Now kind ", "set that Now row's Kind to one of pr, run, "
     "audit, spare (`../../GLOSSARY.md`, **Kind**)"),
    ("Records", r"^project\.md(?!'s deny list)", "in project.md, the user's settings: give the "
     "user the line"),
    ("Records", r"deny list", "a deny-list line: give the user the line and wait for them to fix "
     "it; never open, read or print the deny file, since its lines are the names it keeps out"),
    ("Records", r"^(plan\.md|plan-history\.md|briefs/).*(invalid UTF-8|control character|bare "
     r"CR|mixed line endings)", "whatever edits plan.md, plan-history.md or a brief keeps its "
     "encoding (UTF-8) and its line endings (LF, as .gitattributes sets)"),
    ("Records", r"^plan\.md line \d+: Handover > Coordinator ", "rewrite it as the template's "
     "`title ..., worktree ..., id ..., mode ....`, or `none` when no coordinator holds the plan"),
    ("relay.py", r"merge --ff-only", "tell the user; run that `git -C ... merge --ff-only` "
     "command only on the user's yes, since it moves their checkout; a standing instruction to "
     "keep it current (on project.md's relay.py line, or under Handover) is that yes"),
    ("relay.py", r"by hand", "tell the user, and give them the line to settle by hand"),
)

# The coordinator's next step for each exit code of waitchecks and merge, printed last.
EXIT_HINTS = {
    "waitchecks": {
        0: "the checks passed, or CI does not cover the PR's paths: merge (coordinate's "
           "*Finishing a lane* step 4, **Merge**)",
        1: "a failed check goes to the user with the watch output; checks that could not run "
           "(as `ready` then says) are a CI fallback (`ci-fallbacks.md`, its *Which case*)",
        2: "a usage error: fix what its error line names and rerun",
        3: "no checks appeared: take the `ci-fallbacks.md` case the line above names",
        4: "a lookup failed or an unexpected error: rerun it once; if it exits 4 again, give the "
           "user its line",
        5: "the checks watch timed out (a hung watch, or CI slower than 20 CI start waits): "
           "rerun it once; if it exits 5 again, give the user its line and the table above it",
    },
    "waitchecks --push": {
        0: "the push run passed: nothing to do; for a release, a run a line marks cancelled or "
           "skipped still needs a rerun (`docs/releasing.md` step 2)",
        1: "a red push run: after a merge, coordinate's *Finishing a lane* step 4, **Merge**, says "
           "what follows; for a release, do not release (`docs/releasing.md` step 2)",
        2: "a usage error: fix what its error line names and rerun",
        3: "no push run decided for that commit: when none appeared, check it is on the default "
           "branch and give the user the line; when each was cancelled or skipped, rerun one "
           "(`gh run rerun <id>`) and wait again",
        4: "a lookup failed or an unexpected error: rerun it once; if it exits 4 again, give the "
           "user its line",
        5: "the push run watch timed out: rerun it once; if it exits 5 again, give the user its "
           "line",
    },
    "merge": {
        0: "every key merged and the last merge commit's push run passed; do not rerun the "
           "checks locally; tell the user which lanes merged",
        1: "it stopped at one lane, on the line saying why, and merged no lane after it. A key "
           "not under Ready to merge (nothing merged): fix what `ready` says, as for a deny-list "
           "name in a records file. Any other stop (a "
           "moved head, a merge state other than CLEAN, a failed lookup or `gh pr merge`): give "
           "the user that line. Tell the user which lanes merged and where it stopped",
        2: "a usage error, nothing merged: fix what its error line names and rerun",
        3: "every key merged, but for the last merge commit no push run appeared, or each was "
           "cancelled or skipped: tell the user which lanes merged and give them that line",
        4: "an unexpected error, which may come after some merges; exit 4: do not rerun; give "
           "the user its line, and run `ready` to see which lanes merged. When a line says every "
           "key merged and the push run is not checked, run the `waitchecks <records> --push` it "
           "names, or with the sha from `gh pr view <N> --json mergeCommit` for the last PR "
           "merged. Tell the user which "
           "lanes merged and where it stopped",
        5: "every key merged; the push run watch timed out: run `waitchecks <records> --push "
           "<sha>` once with the sha its line names; if it exits 5 again, give the user its line",
        6: "every key merged, but the last merge commit's push run failed: coordinate's "
           "*Finishing a lane* step 4, **Merge**, says what follows (a follow-up issue)",
    },
}
ROADMAP_HINT = ("hint: an empty Roadmap: fill Issue, Blocked by and Files it owns from these rows, "
                "then Order and Kind, and replace every placeholder")


def section_hints(section, items):
    """The READY_HINTS for <section> that one of <items> matches, in table order."""
    return [hint for s, pattern, hint in READY_HINTS
            if s == section and any(re.search(pattern, i) for i in items)]


def print_section(section, items):
    if items:
        print(f"{section}:")
        for item in items:
            print(f"  {item}")
        for hint in section_hints(section, items):
            print(f"  hint: {hint}")


def cmd_ready(a):
    global deadline
    try:
        budget = float(os.environ.get("RELAY_READY_SECONDS") or READY_SECONDS)
    except ValueError:
        budget = -1.0
    if not 0 <= budget < float("inf"):
        print("RELAY_READY_SECONDS is not a number of seconds", file=sys.stderr)
        return 2
    deadline = time.monotonic() + budget
    timed_out.clear()
    try:
        return ready_report(a, budget)
    finally:
        deadline = None


def timed_step(label, out, skipped, fallback, fn, *args):
    """fn(*args); when one of its commands ran past ready's budget, drop what it added to out,
    add label to skipped and return fallback instead, since what it found may be wrong."""
    sizes, before = {k: len(v) for k, v in out.items()}, len(timed_out)
    result = fn(*args)
    if len(timed_out) == before:
        return result
    for k, size in sizes.items():
        del out[k][size:]
    skipped.append(label)
    return fallback


def ready_report(a, budget):
    records = pathlib.Path(a.records)
    status_dir = records / "status"
    if not records.is_dir():
        print(f"no records folder at {records}", file=sys.stderr)
        return 2
    out = {k: [] for k in READY_SECTIONS}
    plan = records / "plan.md"
    with_endings = [plan, records / "plan-history.md", *sorted((records / "briefs").glob("*.md"))]
    for path in [records / "project.md", *with_endings,
                 *sorted((records / "pr-bodies").glob("*.md"))]:
        if path.is_file():
            out["Records"] += check_encoding(path, path.relative_to(records).as_posix(),
                                             endings=path in with_endings)
    coordinator = (coordinator_field(plan.read_text(encoding="utf-8", errors="replace"))
                   if plan.is_file() else None)
    if coordinator and parse_coordinator(coordinator[1]) is None:
        out["Records"].append(f"plan.md line {coordinator[0]}: Handover > Coordinator is not in "
                              "the template's shape")
    out["Records"] += now_problems(plan)
    if not (records / ".gitattributes").is_file():
        out["Records"].append(
            ".gitattributes missing, so records stay CRLF on Windows: copy setup's "
            "templates/gitattributes to .gitattributes, `git add .gitattributes`, "
            "`git add --renormalize .`, commit, then "
            "delete each file `git ls-files --eol` shows as w/crlf and `git checkout` it again")
    have = {p.stem for p in status_dir.glob("*.md")}
    for b in sorted((records / "briefs").glob("*.md")):
        if not b.stem.startswith("_") and b.stem not in have:
            out["No status yet"].append(f"{b.stem}: a brief but no status file (not started, or not yet run)")
    if plan.exists():
        n = plan.stat().st_size
        if n > a.plan_limit:
            out["Plan"].append(f"plan.md is {n} bytes (limit {a.plan_limit}): prune it "
                               "(move, never delete; the kinds the top of plan.md names stay)")
    now = now_kinds(plan)
    left_out = {"Merged": 0, "Finished": 0}
    repo = a.repo
    fetched = False
    skipped, skipped_lanes, skipped_moved = [], [], 0
    if a.checkout:
        fetched = not timed_step("fetch", out, skipped, (TIMED_OUT,), run,
                                 ["git", "fetch", "-q", "--prune", "origin"], a.checkout)[0]
    out["relay.py"] += timed_step("relay.py check", out, skipped, [], relay_py_behind, records,
                                  a.checkout)
    repo, parents = timed_step("Parents", out, skipped, (repo, None), ready_parents, repo, out)
    timed_step("the default branch's push runs", out, skipped, None, ready_push_runs, repo,
               a.checkout, out)
    try:
        deny = deny_patterns(records)
    except LOOKUP_ERRORS as e:
        out["Records"].append(str(e))
        deny = None
    try:
        out["Records"] += records_deny_hits(records, deny)
    except LOOKUP_ERRORS as e:
        out["Records"].append(f"records deny-list check failed: {e}")
    lookups = ReadyLookups(a.checkout, fetched, len(have))
    deny_rx = None if deny is None else [deny_regex(pat) for pat in deny]
    print_section("Plan", out["Plan"])
    print_section("Default branch", out["Default branch"])
    print("Lanes:")
    for path in sorted(status_dir.glob("*.md")):
        key = path.stem
        try:
            st = parse_status(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            out["Could not parse"].append(f"{key}: invalid UTF-8")
            continue
        missing = [f for f in ("state", "branch", "head", "time") if f not in st]
        if missing or st.get("state") not in STATES:
            out["Could not parse"].append(f"{key}: missing or bad {missing or ['state']}")
            continue
        line = f"  {key}: {st['state']}, {st['branch']} @ {st['head']}, {st['time']}"
        # a done lane outside Now is left out when its only line is Merged or Finished (moved to
        # plan-history.md); its kind is unknown there, so it is `pr`
        moved = st["state"] == "done" and now is not None and key not in now
        kind = (now or {}).get(key, LANE_KINDS[0])
        lane, before = {k: [] for k in READY_SECTIONS}, len(timed_out)
        if not moved:
            print(line)
        # a spare given a brief has taken a lane: as `spare` it would finish with no PR
        spare_brief = kind == "spare" and (records / "briefs" / f"{key}.md").exists()
        if spare_brief:
            lane["Inconsistent"].append(f"{key}: a spare with a brief: set its Now Kind to its "
                                        "lane's (`pr` unless it is a run or audit)")
        if parents is None and st["state"] == "parked":
            why = "is skipped" if "Parents" in skipped else "fails"
            lane["Waiting"].append(f"{key}: parked; no GO while the Parents lookup {why}")
        elif key.isdigit() and int(key) in (parents or ()):
            lane["Inconsistent"].append(f"{key}: issue #{key} is a parent, never a lane")
        else:
            try:
                if repo is None and (st["state"] in ("parked", "done")):
                    repo = gh("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
                if st["state"] == "parked" and kind == "spare":
                    if not spare_brief:
                        lane["Waiting"].append(f"{key}: spare, available: waits for a brief")
                elif st["state"] == "parked":
                    ready_parked(records, key, repo, lane)
                elif st["state"] == "done" and kind in NO_PR_KINDS and not spare_brief:
                    ready_finished(records, key, kind, lane)
                elif st["state"] == "done":
                    ready_done(records, key, st, repo, a.checkout, lane, deny, lookups, fetched,
                               moved)
                elif st["state"] == "blocked":
                    doing = st.get("doing", "")  # Records names the file of a hit
                    if deny_rx is None:
                        doing = "(doing withheld: deny-list check not run)"
                    elif any(rx.search(doing) for rx in deny_rx):
                        doing = "(doing withheld: a deny-list name)"
                    lane["Waiting"].append(f"{key}: blocked: {doing}")
            except LOOKUP_ERRORS as e:
                lane["Waiting"].append(f"{key}: lookup failed: {e}")
        sections = [s for s, items in lane.items() if items]
        if len(timed_out) > before:  # what the lane found before the timeout may be wrong
            if moved:  # most likely merged or finished, so counted, not listed
                skipped_moved += 1
            else:
                skipped_lanes.append(key)
        elif moved and sections in (["Merged"], ["Finished"]):
            left_out[sections[0]] += 1
        else:
            if moved:
                print(line)
            for s, items in lane.items():
                out[s] += items
    if skipped_lanes:
        skipped.append(f"lane{'s' if len(skipped_lanes) > 1 else ''} {', '.join(skipped_lanes)}")
    if skipped_moved:
        skipped.append(f"{skipped_moved} done lane{'s' if skipped_moved > 1 else ''} not in "
                       "plan.md's Now table")
    if skipped:
        out["Skipped"].append(f"lookups past ready's {budget:g} s budget ($RELAY_READY_SECONDS): "
                              f"{', '.join(skipped)}")
    if not have:
        print("  (none)")
    for what, n in (("merged", left_out["Merged"]), ("finished, no-PR", left_out["Finished"])):
        if n:
            print(f"  ({n} {what} lane{'s' if n > 1 else ''} not in plan.md's Now table left out)")
    for section, items in out.items():
        if section not in ("Plan", "Default branch"):
            print_section(section, items)
    if not any(out.values()):
        print("Nothing to do.")
    return 0


def relay_py_behind(records, checkout):
    """A warning when the checkout holding project.md's `relay.py:` path is behind its default
    branch, else []. A relative path resolves against `checkout` (default the current folder); no
    line, a project.md that is not UTF-8 (the Records check names it), or a path outside a git
    checkout, is no check. Fetches that checkout unless it is `checkout`, which cmd_ready has just
    fetched. Never offers a command that moves the checkout's branch or would fail: on another
    branch, or with commits of its own, it says so instead."""
    try:
        value = project_line(records, "relay.py")
    except ValueError:
        return []
    if value is None:
        return []
    path = pathlib.Path(line_path(value))
    base = pathlib.Path(checkout or ".").resolve()
    path = path if path.is_absolute() else base / path
    path = path if path.is_dir() else path.parent
    if not path.is_dir():
        return []
    code, top, _ = run(["git", "rev-parse", "--show-toplevel"], cwd=path)
    if code:
        return []
    top = pathlib.Path(top.strip()).resolve()
    if not checkout or top != base:
        run(["git", "fetch", "-q", "origin"], cwd=top)
    default = default_branch(top)
    code, count, _ = run(["git", "rev-list", "--count", f"HEAD..{default}"], cwd=top)
    if code or not count.strip().isdigit() or int(count) == 0:
        return []
    count, where = int(count), top.as_posix()
    behind = f"{where} is {count} commit{'s' if count > 1 else ''} behind {default}"
    name = default.split("/", 1)[-1]
    _, branch, _ = run(["git", "symbolic-ref", "--short", "-q", "HEAD"], cwd=top)
    branch = branch.strip()
    if branch != name:
        on = f"on branch {branch}" if branch else "on a detached HEAD"
        return [f"{behind}, but it is {on}, not {name}: update it by hand once its work is safe "
                "(no command offered: one would move that work off its branch)"]
    code, ahead, _ = run(["git", "rev-list", "--count", f"{default}..HEAD"], cwd=top)
    if code or not ahead.strip().isdigit():
        return []
    if int(ahead):
        return [f"{behind}, but its {name} has commits {default} does not, so a fast-forward "
                "would fail: merge or move those commits by hand"]
    git_c = f'git -C "{where}"' if " " in where else f"git -C {where}"
    return [f"{behind}: {git_c} merge --ff-only {default}"]


def line_path(value):
    """The path at the start of a project.md value: the first backticked span when it opens with
    one, else the text before a trailing `(...)` note, so `C:/Program Files (x86)/x` stays whole."""
    if value.startswith("`"):
        return value[1:].split("`", 1)[0].strip()
    value = value.strip()
    if value.endswith(")"):
        depth = 0
        for i in range(len(value) - 1, -1, -1):
            depth += {")": 1, "(": -1}.get(value[i], 0)
            if depth == 0:
                value = value[:i] if value[:i].endswith(" ") else value
                break
    return value.strip().strip('"')


def ready_parents(repo, out):
    """Open issues with sub-issues (GitHub's sub_issues_summary), listed under Parents with their
    children's open and closed counts. Returns (repo, the parents' numbers), or (repo, None) when
    the lookup fails. A parent is never a lane."""
    issue_jq = ".[] | select(.pull_request == null) | {number, title, body, html_url, sub_issues_summary}"
    parents, parent_issues = set(), []
    try:
        repo = repo or gh("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
        for issue in gh("api", "--paginate", f"repos/{repo}/issues?state=open&per_page=100",
                        "--jq", issue_jq, jsonl=True):
            if not (issue.get("sub_issues_summary") or {}).get("total"):
                continue
            n = issue["number"]
            children = gh("api", "--paginate", f"repos/{repo}/issues/{n}/sub_issues?per_page=100",
                          "--jq", ".[] | {state, state_reason}", jsonl=True)
            still_open = sum(c["state"] == "open" for c in children)
            closed = len(children) - still_open
            line = f"#{n} {issue['title']}: {still_open} open, {closed} closed children"
            if children and not still_open:
                other = sum(c.get("state_reason") != "completed" for c in children)
                line += (f"; every child closed, {other} not as completed" if other
                         else "; every child closed as completed")
            parents.add(n)
            out["Parents"].append(line)
            parent_issues.append(issue)
    except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
        out["Parents"].append(f"lookup failed: {e}")
        return repo, None
    for issue in parent_issues:
        ready_owner_notes(repo, issue, out)
    return repo, parents


def ready_push_runs(repo, checkout, out):
    """One line under Default branch per workflow whose latest decided push run on the default
    branch (of <checkout>, else the current folder) failed: the newest completed run that is not
    cancelled or skipped. The line says so when a newer run of it is in progress, or was cancelled
    or skipped; a failed lookup is one line there. One `gh run list` call."""
    code, base, _ = run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=checkout)
    if code:  # default_branch's origin/main guess would read a red master as green
        out["Default branch"].append("push run lookup failed: no origin/HEAD names the default "
                                     f"branch in {checkout or 'the current folder'}: run `git "
                                     "remote set-head origin --auto` there")
        return
    base = base.strip().removeprefix("origin/")
    try:
        runs = gh("run", "list", *(["--repo", repo] if repo else []), "--branch", base,
                  "--event", "push", "--limit", str(PUSH_RUN_LIMIT), "--json",
                  "workflowName,status,conclusion,headSha,url") or []
    except LOOKUP_ERRORS as e:
        out["Default branch"].append(f"push run lookup failed: {e}")
        return
    decided, running, passed_over = set(), set(), set()
    for r in runs:  # newest first
        name = r.get("workflowName") or "(unnamed workflow)"
        if name in decided:
            continue
        if r.get("status") != "completed":
            running.add(name)
            continue
        if r.get("conclusion") in PUSH_RUN_PASSED_OVER:
            passed_over.add(name)
            continue
        decided.add(name)
        if r.get("conclusion") in PUSH_RUN_FAILED:
            line = (f"{name}: push run {r['conclusion']} at {(r.get('headSha') or '?')[:8]}: "
                    f"{r.get('url')}")
            if name in running:
                line += " (a newer run is in progress)"
            if name in passed_over:
                line += " (newer runs cancelled or skipped)"
            out["Default branch"].append(line)


def ready_owner_notes(repo, issue, out):
    """List under Owner notes each block in a parent's body or comments that starts with the
    owner-note marker at the start of a line, with the link to that body or comment."""
    n = issue["number"]

    def add(post):
        m = OWNER_NOTE.search(post.get("body") or "")
        if m:
            block = m.string[m.start():].rstrip().splitlines()
            out["Owner notes"].append(f"#{n} {post['html_url']}\n" +
                                      "\n".join(f"    {line}" for line in block))
    add(issue)
    try:
        for comment in gh("api", "--paginate", f"repos/{repo}/issues/{n}/comments?per_page=100",
                          "--jq", ".[] | {body, html_url}", jsonl=True):
            add(comment)
    except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
        out["Owner notes"].append(f"#{n}: comments lookup failed: {e}")


def ready_parked(records, key, repo, out):
    if not (records / "briefs" / f"{key}.md").exists():
        out["Inconsistent"].append(f"{key}: parked with no brief")
    deps, source = dependencies(records, key, repo)
    open_deps = []
    for d in deps:
        issue = gh("issue", "view", str(d), "--repo", repo, "--json", "state,stateReason")
        reason = (issue.get("stateReason") or "").upper()
        if issue["state"].upper() != "CLOSED":
            open_deps.append(f"#{d} open")
        elif reason not in ("", "COMPLETED"):
            out["Inconsistent"].append(f"{key}: dependency #{d} closed as {reason.lower().replace('_', ' ')}")
            open_deps.append(f"#{d} closed")
    if open_deps:
        out["Waiting"].append(f"{key}: parked on {', '.join(open_deps)}")
    else:
        note = " (dependencies from the brief's Depends on:)" if source == "brief" and deps else ""
        out["Ready for GO"].append(f"{key}: send `GO #{key}`{note}")


def ready_finished(records, key, kind, out):
    """A done lane of a kind that closes no issue and opens no PR: Finished once its report is
    written, with no branch, PR or PR body check."""
    if not (records / "reports" / f"{key}.md").exists():
        out["Inconsistent"].append(f"{key}: done with no report file")
    else:
        out["Finished"].append(f"{key}: {kind} done, no PR: read reports/{key}.md")


def ready_done(records, key, st, repo, checkout, out, deny, lookups=None, fetched=True,
               moved=False):
    """Sort done lane <key> into out's sections. `lookups` (a ReadyLookups) shares one PR list,
    one ref read and one workflow read across lanes; without it, each is looked up for this
    lane. When the checkout's fetch failed (`fetched` false), its origin/* refs may be stale or
    missing: the conflict check is skipped and the lane's line says so. `deny`: the deny_patterns
    the caller loaded once, None when they failed to load (the lane then waits; the caller
    reports why). `moved`: the lane is outside plan.md's Now table, so its kind is unknown; one
    never pushed, with no PR and a report, is taken as a run, audit or spare moved to
    plan-history.md; one whose PR merged gets no PR body check (#207)."""
    branch, head = st["branch"], st["head"]
    pushed_of = lookups.pushed if lookups else (lambda b: pushed_head(checkout, b))
    prs_of = lookups.prs if lookups else branch_prs
    no_ci_of, texts_of = (lookups.no_ci, lookups.workflow_texts) if lookups else (None, None)
    if not (records / "reports" / f"{key}.md").exists():
        out["Inconsistent"].append(f"{key}: done with no report file")
    pushed = pushed_of(branch)
    prs = None if pushed else prs_of(repo, branch)  # a branch deleted after its merge is Merged
    if not pushed.startswith(head) and not any(p["state"].upper() == "MERGED"
                                               and p["headRefOid"].startswith(head) for p in prs or []):
        if moved and not pushed and not prs and (records / "reports" / f"{key}.md").exists():
            out["Finished"].append(f"{key}: done outside Now, never pushed, no PR: read "
                                   f"reports/{key}.md")
            return
        out["Inconsistent"].append(f"{key}: status head {head} is not the pushed head "
                                   f"{pushed[:12] or '(branch not pushed)'}")
        return
    if prs is None and moved:
        prs = prs_of(repo, branch)
    merged = next((p for p in prs or [] if p["state"].upper() == "MERGED"), None)
    if moved and merged:  # after the merge, its body draft can no longer change anything (#207)
        out["Merged"].append(f"{key}: PR #{merged['number']}")
        return
    if deny is None:
        out["Waiting"].append(f"{key}: deny-list check not run (see Records)")
        return
    for problem in check_pr_body(st.get("PR body draft", ""), brief_issues(records, key, "Closes:"),
                                 deny):
        out["Inconsistent"].append(f"{key}: {problem}")
    if prs is None:
        prs = prs_of(repo, branch)
        merged = next((p for p in prs if p["state"].upper() == "MERGED"), None)
    if merged:
        out["Merged"].append(f"{key}: PR #{merged['number']}")
        return
    pr = next((p for p in prs if p["state"].upper() == "OPEN"), None)
    if pr is None and prs:
        out["Inconsistent"].append(f"{key}: PR #{prs[0]['number']} closed without merging")
        return
    files = conflicts(checkout, branch) if checkout and fetched else []
    skipped = " (conflict check skipped: fetch failed)" if checkout and not fetched else ""
    if files:
        out["Waiting"].append(f"{key}: conflicts with the default branch: {', '.join(files)}")
        return
    if pr is None:
        out["Ready for PR"].append(f"{key}: {branch} @ {head}{skipped}")
        return
    if not pr["headRefOid"].startswith(head):
        out["Inconsistent"].append(f"{key}: PR #{pr['number']} head {pr['headRefOid'][:12]} "
                                   f"is not the status head {head}")
        return
    draft = pathlib.Path(st.get("PR body draft", ""))
    stale = pr.get("body") is not None and draft.is_file() and (  # gh may return CRLF
        pr["body"].replace("\r\n", "\n").strip() != draft.read_text(encoding="utf-8").strip())
    if stale:
        out["Waiting"].append(f"{key}: PR #{pr['number']} body differs from its draft: "
                              f'gh pr edit {pr["number"]} --body-file "{draft.as_posix()}"')
    checks, uncovered = checks_state(pr.get("statusCheckRollup"), repo, no_ci_of), ""
    if checks == "no checks reported":  # as waitchecks: no workflow runs on these paths (#165)
        line = uncovered_line(pr["number"], repo, texts_of)
        if line:
            checks, uncovered = "passed", f" ({line})"
    if pr.get("mergeable", "").upper() == "CONFLICTING":
        out["Waiting"].append(f"{key}: PR #{pr['number']} has a merge conflict")
    elif checks != "passed":
        out["Waiting"].append(f"{key}: PR #{pr['number']} {checks}")
    elif not stale:
        out["Ready to merge"].append(f"{key}: PR #{pr['number']} --match-head-commit "
                                     f"{pr['headRefOid']}{uncovered}{skipped}")


# roadmap --------------------------------------------------------------------------------------

def parse_files(body):
    """The `## Files` section of an issue body: [{path, new, scope}], or None with no section.
    Only top-level bullets count (the first bullet's indent; a `[ ]` checkbox dropped); other
    lines inside the section, nested bullets and fenced blocks are skipped.
    The section ends at the next `#` or `##` heading."""
    items, inside, fence, top = None, False, False, None
    for line in (body or "").splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if re.match(r" {0,3}#{1,2}\s", line):
            if inside:
                break
            inside = re.fullmatch(r" {0,3}##\s+Files:?\s*", line, re.I) is not None
            if inside:
                items = []
            continue
        m = re.match(r"(\s*)[-*+]\s+(?:\[[ xX]\]\s+)?(.*\S)", line) if inside else None
        if not m:
            continue
        top = len(m.group(1)) if top is None else top
        if len(m.group(1)) > top:
            continue
        rest = m.group(2)
        new = re.match(r"new:\s*", rest, re.I)
        rest = rest[new.end():] if new else rest
        p = re.match(r"`([^`]+)`|([^\s(]+)", rest)
        if not p:
            continue
        scope = rest[p.end():].strip()
        if scope.startswith("(") and scope.endswith(")") and balanced(scope[1:-1]):
            scope = scope[1:-1].strip()
        items.append({"path": p.group(1) or p.group(2), "new": bool(new), "scope": scope})
    return items


def balanced(text):
    depth = 0
    for ch in text:
        depth += (ch == "(") - (ch == ")")
        if depth < 0:
            return False
    return depth == 0


def cmd_roadmap(a):
    """One Roadmap row per open issue: blocked-by and the `## Files` paths, never guessed."""
    issue_jq = ".[] | select(.pull_request == null) | {number, title, body, sub_issues_summary}"
    try:
        repo = a.repo or gh("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
        issues = gh("api", "--paginate", f"repos/{repo}/issues?state=open&per_page=100",
                    "--jq", issue_jq, jsonl=True)
        rows, missing = [], []
        for issue in sorted(issues, key=lambda i: i["number"]):
            n = issue["number"]
            blocked = gh("api", f"repos/{repo}/issues/{n}/dependencies/blocked_by") or []
            blocked = ", ".join(f"#{b['number']}" + (" (closed)" if b.get("state") == "closed" else "")
                                for b in blocked) or "none"
            files = parse_files(issue.get("body"))
            if (issue.get("sub_issues_summary") or {}).get("total"):
                cell = "parent"
            elif not files:
                cell = f"**missing: {'no' if files is None else 'an empty'} `## Files` section**"
                missing.append(f"#{n}")
            else:
                cell = "; ".join(("New: " if f["new"] else "") + f["path"]
                                 + (f" ({f['scope']})" if f["scope"] else "") for f in files)
            title, cell = (s.replace("|", "\\|").replace("\n", " ")
                           for s in (f"#{n} {issue['title']}", cell))
            rows.append(f"| {title} | {blocked} | {cell} |")
    except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
        return fail(f"roadmap lookup failed: {e}")
    print("| Issue | Blocked by (GitHub) | Files it owns |")
    print("|---|---|---|")
    for row in rows:
        print(row)
    if missing:
        print(f"\nMissing `## Files`: {', '.join(missing)}")
    if rows:
        print(ROADMAP_HINT)
    return 0


# localcheck -----------------------------------------------------------------------------------

def longpaths_env():
    """os.environ plus core.longpaths=true for every git the checks run, after any GIT_CONFIG_* set."""
    n = int(os.environ.get("GIT_CONFIG_COUNT") or 0)
    return {**os.environ, "GIT_CONFIG_COUNT": str(n + 1),
            f"GIT_CONFIG_KEY_{n}": "core.longpaths", f"GIT_CONFIG_VALUE_{n}": "true"}


def project_line(records, label):
    """The text after `- **<label>:**` in project.md, or None. ValueError, naming project.md, when
    it is not UTF-8."""
    project = records / "project.md"
    if not project.exists():
        return None
    try:
        text = project.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"{project} is not valid UTF-8 ({e.reason} at byte {e.start})") from None
    m = re.search(rf"^- \*\*{re.escape(label)}:\*\*(.*)$", text, re.M)
    value = m.group(1).strip() if m else ""
    return value if value.strip("`\". ").lower() not in ("", "none") else None


COORDINATOR_FIELD = re.compile(r"^- \*\*Coordinator:\*\*(.*)$", re.M)
COORDINATOR_SHAPE = re.compile(r"title .+?, worktree ([^`]+?), id [^,\s]+, "
                               r"mode (normal|unattended|paused)\.(?:\s|$)")


def coordinator_field(text):
    """(line number, text) of plan.md's `- **Coordinator:**` line, or None when it has none."""
    m = COORDINATOR_FIELD.search(text)
    return (text.count("\n", 0, m.start()) + 1, m.group(1).strip()) if m else None


def parse_coordinator(value):
    """Handover's Coordinator field in one of its two forms: {"worktree", "mode"} for the
    template's `title <t>, worktree <path>, id <id>, mode <mode>.`, {} for `none` (no coordinator
    holds the plan), each at the field's start and optionally followed by more text; None for
    anything else. A path in backticks is anything else."""
    if re.match(r"none(?=[\s.,;:]|$)", value):
        return {}
    m = COORDINATOR_SHAPE.match(value)
    return {"worktree": m.group(1), "mode": m.group(2)} if m else None


def check_items(line, windows=None):
    """[(command, main checkout only, covered paths or None)] from a project.md checks line:
    `;`-separated items, each command in backticks. A `(Windows: `...`)` in an item, before or
    after its command, replaces that command on Windows; a `(covers: <path>, ...)` lists the paths
    the item covers (separated by `,`, backticks optional; see `covered`); an item marked "main
    checkout only" is flagged. ValueError, naming the line, when an item holds more than one command outside its
    Windows override (never run only the first), only an override (no command for other
    systems), or a covers list with no path or a second one."""
    windows = os.name == "nt" if windows is None else windows
    items, cur, tick = [], "", False
    for ch in line:
        tick ^= ch == "`"
        if ch == ";" and not tick:
            items.append(cur)
            cur = ""
        else:
            cur += ch
    items.append(cur)
    result = []
    for item in items:
        covs = list(re.finditer(r"\(covers:([^)]*)\)", item))
        covers = None
        if len(covs) > 1:
            raise ValueError(f"project.md's checks line has two `(covers: ...)` lists in one item "
                             f"(one per item, paths separated by `,`): {line.strip()}")
        if covs:
            cov = covs[0]
            covers = [p.strip() for p in cov.group(1).replace("`", "").split(",") if p.strip()]
            if not covers:
                raise ValueError(f"project.md's checks line has a `(covers: ...)` with no path: "
                                 f"{line.strip()}")
            item = item[:cov.start()] + item[cov.end():]
        win = re.search(r"\(Windows:\s*`([^`]+)`", item)
        spans = re.findall(r"`([^`]+)`", item[:win.start()] + item[win.end():] if win else item)
        if not spans and not win:
            continue
        if len(spans) > 1:
            raise ValueError(f"project.md's checks line has more than one command in one item "
                             f"(each backticked span is a command; one per item, items separated "
                             f"by `;`): {line.strip()}")
        if not spans:
            raise ValueError(f"project.md's checks line has an item with only a Windows override "
                             f"(write the command, then `(Windows: `...`)`): {line.strip()}")
        cmd = win.group(1) if win and windows else spans[0]
        result.append((cmd, "main checkout only" in item, covers))
    return result


def check_commands(line, windows=None):
    """(commands, skipped) from a project.md checks line (`check_items`), ignoring covers lists:
    skipped are the items marked "main checkout only"."""
    items = check_items(line, windows)
    return [c for c, main, _ in items if not main], [c for c, main, _ in items if main]


def covered(patterns, paths):
    """True when a changed path matches one of an item's covered patterns: an fnmatch glob (`*`
    crosses `/`, so `plugin/tools/**` is everything under it), a folder (`tests` or `tests/`), or
    a file."""
    for path in paths:
        for pat in patterns:
            folder = pat.rstrip("/") + "/"
            if fnmatch.fnmatchcase(path, pat) or path == pat or path.startswith(folder):
                return True
    return False


def cmd_localcheck(a):
    records = pathlib.Path(a.records)
    if not records.is_dir():
        print(f"no records folder at {records}", file=sys.stderr)
        return 2
    checkout = os.path.abspath(a.checkout)
    try:
        line = project_line(records, "Local checks") or project_line(records, "Checks before done")
        if line is None:
            return fail(f"{records / 'project.md'} has no `- **Local checks:**` line and no "
                        "`- **Checks before done:**` line: add the command that runs the checks")
        items = check_items(line)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    if not any(not main for _, main, _ in items):
        return fail(f"no backticked command on project.md's checks line: {line}")
    status = records / "status" / f"{a.key}.md"
    try:
        st = parse_status(status.read_text(encoding="utf-8")) if status.exists() else {}
    except UnicodeDecodeError:
        return fail(f"{status}: invalid UTF-8")
    branch = st.get("branch", "none")
    if branch == "none":
        return fail(f"lane {a.key} has no branch in {status}")
    run(["git", "fetch", "-q", "origin"], cwd=checkout)
    head = pushed_head(checkout, branch)
    if not head:
        return fail(f"branch {branch} is not pushed")
    default = default_branch(checkout)
    _, base, _ = run(["git", "rev-parse", default], cwd=checkout)
    base = base.strip()
    lines = [f"relay localcheck, lane {a.key}: {branch}", f"head {head}", f"base {base} ({default})"]
    if not head.startswith(st.get("head", "")):
        lines.append(f"warning: the status head {st.get('head')} is not this head")
    code, out, _ = run(["git", "diff", "--name-only", "-z", "--no-renames", f"{base}...{head}"],
                       cwd=checkout)  # -z: paths unquoted, so a non-ASCII path still matches
    changed = [p for p in out.split("\0") if p] if code == 0 else None
    if changed is None and any(cov for _, _, cov in items):
        lines.append("warning: could not list the lane's changed paths; every item runs")
    commands, skipped, not_needed = [], [], []
    for cmd, main, cov in items:
        if changed is not None and cov is not None and not covered(cov, changed):
            not_needed.append(cmd)
        else:
            (skipped if main else commands).append(cmd)
    env = longpaths_env()
    wt = tempfile.mkdtemp(prefix="relay-lc-")
    ok = False
    try:
        code, _, err = run(["git", "-c", "core.longpaths=true", "worktree", "add", "-q", "--detach",
                            wt, head], cwd=checkout)
        if code:
            return fail(f"git worktree add failed: {err.strip()}")
        code, out, err = run(["git", "-c", "core.longpaths=true", "-c", "user.name=relay", "-c",
                              "user.email=relay@localhost", "merge", "-q", "--no-edit", base], cwd=wt)
        if code:
            lines.append(f"merge of {default} failed:\n{(out + err).strip()}")
        else:
            ok = True
            for cmd in commands:
                p = subprocess.run(cmd, shell=True, cwd=wt, env=env, capture_output=True,
                                   text=True, encoding="utf-8", errors="replace")
                lines += ["", f"$ {cmd}", (p.stdout + p.stderr).rstrip(),
                          "passed" if p.returncode == 0 else f"failed (exit {p.returncode})"]
                ok = ok and p.returncode == 0
        lines += [f"not needed (no covered path changed): {c}" for c in not_needed]
        lines += [f"not run (main checkout only): {c}" for c in skipped]
        result = "passed" if ok else "failed"
        if ok and not_needed:
            result += f", {len(not_needed)} not needed"
        if ok and skipped:
            result += f", {len(skipped)} not run: run them in the main checkout before the merge"
        lines += ["", f"result: {result}"]
    finally:
        run(["git", "-c", "core.longpaths=true", "worktree", "remove", "--force", wt], cwd=checkout)
        shutil.rmtree(wt, ignore_errors=True)
        run(["git", "worktree", "prune"], cwd=checkout)
        if os.path.exists(wt):
            print(f"warning: could not remove {wt}", file=sys.stderr)
    report = "\n".join(lines)
    print(report)
    if a.comment:
        body = pathlib.Path(wt + ".md")
        body.write_text(f"```\n{report}\n```\n", encoding="utf-8")
        try:
            repo = a.repo or gh("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
            gh_raw("pr", "comment", str(a.comment), "--repo", repo, "--body-file", str(body))
        except LOOKUP_ERRORS as e:
            return fail(f"could not post on PR #{a.comment}: {e}")
        finally:
            body.unlink()
        print(f"posted on PR #{a.comment}")
    return 0 if ok else 1


# waitchecks -----------------------------------------------------------------------------------

NO_CHECKS, LOOKUP_FAILED, WATCH_TIMED_OUT = 3, 4, 5
WATCH_FACTOR = 20  # the checks watch may run this many CI start waits (6 min: 2 hours)
CI_START_WAIT = 6  # minutes, when project.md has no `CI start wait:` line


def poll_schedule(minutes):
    """Poll times in seconds: now, then 1/6, 1/2 and all of the CI start wait (6: 0, 1, 3, 6 min)."""
    return [0, minutes * 10, minutes * 30, minutes * 60]


def ci_start_schedule(records):
    """poll_schedule for project.md's `CI start wait: <minutes>` line, else CI_START_WAIT.
    ValueError when the line is not a positive number of minutes."""
    line = project_line(records, "CI start wait")
    if line is None:
        return poll_schedule(CI_START_WAIT)
    m = re.fullmatch(r"`?(\d+(?:\.\d+)?)`?(?:\s*min(?:ute)?s?)?\.?", line.strip())
    if not (m and float(m.group(1)) > 0):
        raise ValueError(f"project.md's CI start wait is not a number of minutes: {line}")
    return poll_schedule(float(m.group(1)))


def pr_rollup(pr, repo):
    return (gh("pr", "view", str(pr), "--repo", repo, "--json", "statusCheckRollup")
            or {})["statusCheckRollup"]


def wait_checks(pr, repo, schedule):
    """Poll PR <pr>'s checks at each time in schedule (seconds from now) until one exists, queued
    or pending included, then `gh pr checks --watch` it. Returns 0 when the checks passed, or at
    the first poll that finds none when CI does not cover the PR's paths (uncovered_line), 1
    when one failed, NO_CHECKS when none appeared by the last poll, LOOKUP_FAILED when the last
    poll's lookup failed with none seen, or the watch failed with no failed check behind it,
    WATCH_TIMED_OUT when the watch ran past WATCH_FACTOR times the last poll's time (it is
    killed)."""
    start, error, paths_read = time.monotonic(), None, False
    for i, at in enumerate(schedule, 1):
        time.sleep(max(0, at - (time.monotonic() - start)))
        try:
            rollup, error = pr_rollup(pr, repo), None
        except LOOKUP_ERRORS as e:
            rollup, error = None, e
            print(f"poll {i} at {at / 60:g} min: lookup failed: {e}", file=sys.stderr)
        if rollup:
            print(f"poll {i} at {at / 60:g} min: {len(rollup)} check(s); watching", flush=True)
            # with no terminal, the watch reprints the whole table every 10 s: keep only its
            # errors, then print the final table once
            checks = gh_base() + ["pr", "checks", str(pr), "--repo", repo]
            limit = schedule[-1] * WATCH_FACTOR
            code, _, err = run(checks + ["--watch"], timeout=limit)
            _, out, table_err = run(checks)
            print(out.rstrip())
            errors = "\n".join(e.rstrip() for e in (err, table_err) if e.strip())
            if errors:
                print(errors, file=sys.stderr)
            if code == TIMED_OUT:
                print(f"the checks watch on PR #{pr} ran past {limit / 60:g} minutes with no "
                      "result; it was stopped")
                return WATCH_TIMED_OUT
            if code == 0:
                return 0
            # gh exits 1 on a failed check and on its own errors alike: ask the rollup which
            try:
                state = checks_state(pr_rollup(pr, repo), repo)
            except LOOKUP_ERRORS as e:
                state = f"lookup failed: {e}"
            if state.startswith(("check failed", "checks could not run")):
                return 1
            print(f"the watch failed with no failed check ({state})", file=sys.stderr)
            return LOOKUP_FAILED
        if error is None:
            print(f"poll {i} at {at / 60:g} min: no checks yet", flush=True)
            if not paths_read:
                paths_read, line = True, uncovered_line(pr, repo)
                if line:
                    print(line, flush=True)
                    return 0
    if error is not None:
        return LOOKUP_FAILED
    print(f"no checks appeared on PR #{pr} within {schedule[-1] / 60:g} minutes")
    print(ci_case(repo))
    return NO_CHECKS


def push_runs(repo, base, sha):
    return gh("run", "list", "--repo", repo, "--branch", base, "--event", "push", "--commit", sha,
              "--json", "databaseId,workflowName,status,conclusion,url") or []


def wait_push_run(repo, base, sha, schedule):
    """Wait for the push runs on <base> for commit <sha>: polled at each time in schedule (seconds
    from now) until one appears, then every PUSH_RUN_POLL seconds until each has completed, for
    at most WATCH_FACTOR times the last poll's time. Prints one line per run, and each failed
    run's failed jobs. Returns 0 when one passed and none failed (`cancelled` and `skipped`
    decide nothing, as in `ready`), 1 when one failed (PUSH_RUN_FAILED), NO_CHECKS when none
    appeared by the last poll or none decided, LOOKUP_FAILED when the last poll's lookup failed
    with none seen, WATCH_TIMED_OUT when one still runs past the cap and none failed. Once runs
    have appeared, a failed or empty lookup keeps the last runs seen and waits for the next
    poll."""
    start, runs, error = time.monotonic(), [], None
    for i, at in enumerate(schedule, 1):
        time.sleep(max(0, at - (time.monotonic() - start)))
        try:
            runs, error = push_runs(repo, base, sha), None
        except LOOKUP_ERRORS as e:
            error = e
            print(f"poll {i} at {at / 60:g} min: push run lookup failed: {e}", file=sys.stderr)
        if runs:
            break
    if not runs:
        if error is not None:
            return LOOKUP_FAILED
        print(f"no push run on {base} for {sha[:8]} appeared within {schedule[-1] / 60:g} minutes: "
              f"gh run list --repo {repo} --branch {base} --event push --commit {sha}")
        return NO_CHECKS
    print(f"{len(runs)} push run(s) on {base} for {sha[:8]}; waiting", flush=True)
    limit = schedule[-1] * WATCH_FACTOR
    while any(r.get("status") != "completed" for r in runs):
        if time.monotonic() - start + PUSH_RUN_POLL > limit:
            break
        time.sleep(PUSH_RUN_POLL)
        try:
            runs = push_runs(repo, base, sha) or runs
        except LOOKUP_ERRORS as e:
            print(f"push run lookup failed: {e}", file=sys.stderr)
    failed = False
    for r in runs:
        name = r.get("workflowName") or "(unnamed workflow)"
        result = r.get("conclusion") if r.get("status") == "completed" else r.get("status")
        line = f"{name}: push run {result} at {sha[:8]}: {r.get('url')}"
        if result in PUSH_RUN_PASSED_OVER:
            line += " (decides nothing, as in `ready`)"
        print(line)
        if result in PUSH_RUN_FAILED:
            failed = True
            print(f"  failed jobs: {failed_jobs(repo, r.get('databaseId'))}")
    if any(r.get("status") != "completed" for r in runs):
        print(f"the push run watch for {sha} on {base} ran past {limit / 60:g} minutes with "
              "no result; it was stopped")
        return 1 if failed else WATCH_TIMED_OUT
    if failed:
        return 1
    if all(r.get("conclusion") in PUSH_RUN_PASSED_OVER for r in runs):
        print(f"no push run on {base} for {sha[:8]} decided: each was cancelled or skipped")
        return NO_CHECKS
    return 0


def failed_jobs(repo, run_id):
    """The names of push run <run_id>'s failed jobs, joined, or why there are none to name."""
    try:
        jobs = gh("run", "view", str(run_id), "--repo", repo, "--json", "jobs")["jobs"] or []
    except LOOKUP_ERRORS as e:
        return f"lookup failed: {e}"
    names = [j.get("name") or "?" for j in jobs if j.get("conclusion") in PUSH_RUN_FAILED]
    return ", ".join(names) or "none reported"


def full_sha(repo, sha):
    """The full sha of commit <sha> on <repo>, a hex prefix of 7 to 40 characters (#196): as it
    is when full, else through GitHub, so no checkout is needed. None when it matches no commit
    or more than one (GitHub's HTTP 422 for both); RuntimeError when the lookup failed."""
    if len(sha) == 40:
        return sha
    try:
        full = gh_raw("api", f"repos/{repo}/commits/{sha}", "--jq", ".sha").strip()
    except RuntimeError as e:
        if "(HTTP 422)" in str(e):
            return None
        raise
    if not (re.fullmatch(r"[0-9a-f]{40}", full) and full.startswith(sha)):
        raise RuntimeError(f"gh api repos/{repo}/commits/{sha}: not the sha of a commit: {full}")
    return full


def cmd_waitchecks(a):
    records = pathlib.Path(a.records)
    if not records.is_dir():
        print(f"no records folder at {records}", file=sys.stderr)
        return 2
    if (a.pr is None) == (a.push is None):
        print("give exactly one of a PR number and --push <sha>", file=sys.stderr)
        return 2
    if a.push is not None and not re.fullmatch(r"[0-9a-fA-F]{7,40}", a.push):
        print(f"--push takes a commit sha of 7 to 40 hex characters, not {a.push}",
              file=sys.stderr)
        return 2
    try:
        schedule = ci_start_schedule(records)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    try:
        view = {} if a.repo and a.pr is not None else gh(
            "repo", "view", *([a.repo] if a.repo else []), "--json", "nameWithOwner,defaultBranchRef")
        repo = a.repo or view["nameWithOwner"]
        if a.pr is None:
            base = view["defaultBranchRef"]["name"]
            sha = full_sha(repo, a.push.lower())
    except LOOKUP_ERRORS as e:
        print(f"lookup failed: {e}", file=sys.stderr)
        return LOOKUP_FAILED
    if a.pr is None:
        if sha is None:
            print(f"--push {a.push} matches no commit on {repo} (not pushed?), or more than "
                  "one: give more of the sha", file=sys.stderr)
            return 2
        return wait_push_run(repo, base, sha, schedule)
    return wait_checks(a.pr, repo, schedule)


# merge ----------------------------------------------------------------------------------------

READY_TO_MERGE = re.compile(r"PR #(\d+) --match-head-commit ([0-9a-f]{40})"
                            r"(?: \(CI does not cover these paths: .*; no checks to wait for\))?$")
STATE_RETRIES = (5, 15, 30)  # seconds; GitHub says UNKNOWN while it recomputes after a merge
PUSH_RUN_POLL = 30  # seconds between push run polls once one has appeared
PUSH_RED = 6  # merge's exit when every key merged and the last merge commit's push run failed
MERGE_POLLS = (10, 20, 30, 60, 60)  # seconds; how long a transient merge failure is waited out
# a gh pr merge failure GitHub may still be working through (#183): a 5xx, or a merge underway
TRANSIENT_MERGE = re.compile(r"HTTP 5\d\d\b|\b5\d\d (?:Bad Gateway|Service Unavailable|Gateway "
                             r"Time-?out|Internal Server Error)|already in progress", re.I)


def ready_to_merge(records, key, repo, checkout, deny):
    """(PR number, head sha) when `ready` lists lane <key> under Ready to merge and nowhere else,
    else the reason it does not, as text."""
    path = records / "status" / f"{key}.md"
    if not path.exists():
        return "no status file"
    try:
        st = parse_status(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return "status file is not valid UTF-8"
    if st.get("state") != "done" or not all(f in st for f in ("branch", "head", "time")):
        return f"state {st.get('state', 'unknown')}"
    out = {k: [] for k in READY_SECTIONS}
    try:
        ready_done(records, key, st, repo, checkout, out, deny)
    except LOOKUP_ERRORS as e:
        return f"lookup failed: {e}"
    prefix = f"{key}: "
    found = [(s, i[len(prefix):]) for s, items in out.items() for i in items if i.startswith(prefix)]
    m = next((READY_TO_MERGE.match(i) for s, i in found if s == "Ready to merge"), None)
    others = [f"{s}: {i}" for s, i in found if s != "Ready to merge"]
    if m and not others:
        return int(m.group(1)), m.group(2)
    return "; ".join(others) or "not listed"


def merge_lane(key, pr, sha, repo):
    """Require PR <pr>'s head <sha> and mergeStateStatus CLEAN, then merge with --match-head-commit.
    Returns (merge commit sha or None, base branch), or None after printing one line on why it
    stopped."""
    try:
        for wait in (*STATE_RETRIES, None):
            view = gh("pr", "view", str(pr), "--repo", repo, "--json",
                      "headRefOid,mergeStateStatus,baseRefName")
            if view["mergeStateStatus"].upper() != "UNKNOWN" or wait is None:
                break
            time.sleep(wait)
    except LOOKUP_ERRORS as e:
        fail(f"{key}: PR #{pr} lookup failed: {e}")
        return None
    if view["headRefOid"] != sha:
        fail(f"{key}: PR #{pr} head {view['headRefOid'][:12]} is not {sha[:12]}, the head ready listed")
        return None
    state = view["mergeStateStatus"].upper()
    if state != "CLEAN":
        fail(f"{key}: PR #{pr} merge state is {state}, not CLEAN")
        return None
    for retry_left in (True, False):
        code, out, err = run(gh_base() + ["pr", "merge", str(pr), "--repo", repo, "--merge",
                                          "--match-head-commit", sha])
        if not code:
            break
        error = " ".join((err or out).split())
        transient = bool(TRANSIENT_MERGE.search(error))
        if merged_after_failure(pr, repo, transient):
            break
        if not (retry_left and transient):
            fail(f"{key}: gh pr merge {pr} failed: {error}")
            return None
    try:
        merged = gh("pr", "view", str(pr), "--repo", repo, "--json", "mergedAt,mergeCommit")
        oid = merged["mergeCommit"]["oid"]
        print(f"{key}: merged PR #{pr} at {merged['mergedAt']}", flush=True)
        return oid, view["baseRefName"]
    except LOOKUP_ERRORS as e:
        print(f"{key}: merged PR #{pr}; merge time lookup failed: {e}", flush=True)
        return None, view["baseRefName"]


def merged_after_failure(pr, repo, transient):
    """Whether PR <pr> reads MERGED after a failed `gh pr merge`: asked at once, then, when the
    failure was transient, again after each MERGE_POLLS wait. A failed lookup counts as not
    merged yet."""
    for wait in (0, *(MERGE_POLLS if transient else ())):
        time.sleep(wait)
        try:
            if gh("pr", "view", str(pr), "--repo", repo, "--json", "state")["state"].upper() == "MERGED":
                return True
        except LOOKUP_ERRORS:
            continue
    return False

def cmd_merge(a):
    records = pathlib.Path(a.records)
    if not records.is_dir():
        print(f"no records folder at {records}", file=sys.stderr)
        return 2
    repeated = sorted({k for k in a.keys if a.keys.count(k) > 1})
    if repeated:
        print(f"{', '.join(repeated)}: given more than once; nothing merged", file=sys.stderr)
        return 2
    try:
        schedule = ci_start_schedule(records)
    except ValueError as e:
        print(f"{e}; nothing merged", file=sys.stderr)
        return 2
    try:
        repo = a.repo or gh("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
    except LOOKUP_ERRORS as e:
        return fail(f"lookup failed: {e}")
    if not os.path.isdir(a.checkout) or run(["git", "rev-parse", "--git-dir"], cwd=a.checkout)[0]:
        print(f"{os.path.abspath(a.checkout)} is not a git checkout: pass --checkout <a clone of "
              f"{repo}>", file=sys.stderr)
        return 2
    code, out, err = run(["git", "fetch", "-q", "origin"], cwd=a.checkout)
    if code:
        return fail(f"git fetch failed in {os.path.abspath(a.checkout)}: "
                    f"{' '.join((err or out).split())}; nothing merged")
    try:
        deny = deny_patterns(records)
    except LOOKUP_ERRORS as e:
        return fail(f"{e}; nothing merged")
    hits = records_deny_hits(records, deny)
    for hit in hits:
        print(f"{hit}; nothing merged", file=sys.stderr)
    if hits:
        return 1
    lanes = []
    for key in a.keys:
        found = ready_to_merge(records, key, repo, a.checkout, deny)
        if isinstance(found, str):
            return fail(f"{key}: not under Ready to merge ({found}); nothing merged")
        lanes.append((key, *found))
    last = None
    for key, pr, sha in lanes:
        last = merge_lane(key, pr, sha, repo)
        if last is None:
            return 1
    if not last[0]:
        print("every key merged; the push run is not checked: the merge commit lookup failed",
              file=sys.stderr)
        return LOOKUP_FAILED
    code = wait_push_run(repo, last[1], last[0], schedule)
    if code == LOOKUP_FAILED:
        print(f"every key merged; the push run is not checked: run `waitchecks <records> --push "
              f"{last[0]}`", file=sys.stderr)
    return PUSH_RED if code == 1 else code


def fail(msg):
    print(msg, file=sys.stderr)
    return 1


def main(argv=None):
    # records text holds non-ASCII (`›`, the user's words); a piped Windows stdout defaults to
    # the locale code page (cp950), and -I ignores PYTHONIOENCODING (#161)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status", help="write a worker's status file")
    s.add_argument("records")
    s.add_argument("key")
    s.add_argument("--state", required=True, choices=STATES)
    s.add_argument("--doing", required=True)
    s.add_argument("--branch")
    s.add_argument("--head")
    s.add_argument("--pr-body")
    r = sub.add_parser("ready", help="print what the coordinator can do next")
    r.add_argument("records")
    r.add_argument("--repo")
    r.add_argument("--checkout")
    r.add_argument("--plan-limit", type=int, default=16384, metavar="BYTES")
    c = sub.add_parser("localcheck", help="run the project's checks on a lane merged with the default branch")
    c.add_argument("records")
    c.add_argument("key")
    c.add_argument("--checkout", default=".")
    c.add_argument("--repo")
    c.add_argument("--comment", type=int, metavar="N")
    w = sub.add_parser("waitchecks", help="wait for a PR's first check, then watch its checks; "
                       "--push: wait for the default branch's push run for a commit")
    w.add_argument("records")
    w.add_argument("pr", type=int, nargs="?")
    w.add_argument("--push", metavar="SHA", help="the commit: a sha of 7 to 40 hex characters, "
                   "a short one resolved through GitHub")
    w.add_argument("--repo")
    g = sub.add_parser("merge", help="merge Ready to merge lanes one at a time, stopping on the first problem")
    g.add_argument("records")
    g.add_argument("keys", nargs="+", metavar="key")
    g.add_argument("--repo")
    g.add_argument("--checkout", default=".")
    m = sub.add_parser("roadmap", help="print each open issue's blocked-by and `## Files`")
    m.add_argument("--repo")
    try:
        a = p.parse_args(argv)
    except SystemExit as e:  # argparse's usage error exits 2 before the command runs
        cmd = next((t for t in (sys.argv[1:] if argv is None else argv)
                    if not t.startswith("-")), None)
        if e.code == 2 and cmd in EXIT_HINTS:
            print(f"hint (exit 2): {EXIT_HINTS[cmd][2]}", flush=True)
        raise
    command = {"status": cmd_status, "ready": cmd_ready, "roadmap": cmd_roadmap,
               "localcheck": cmd_localcheck, "waitchecks": cmd_waitchecks,
               "merge": cmd_merge}[a.cmd]
    if a.cmd not in ("waitchecks", "merge"):
        return command(a)
    # their exit 1 means a check failed or a merge stopped: never let an error say that
    try:
        code = command(a)
    except Exception as e:  # noqa: BLE001
        print(f"{a.cmd}: unexpected error: {type(e).__name__}: {' '.join(str(e).split())}",
              file=sys.stderr)
        code = LOOKUP_FAILED
    hints = EXIT_HINTS["waitchecks --push" if getattr(a, "push", None) else a.cmd]
    if code in hints:
        print(f"hint (exit {code}): {hints[code]}", flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
