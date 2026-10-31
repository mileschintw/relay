#!/usr/bin/env python3
"""relay: the scripted steps of multi-session coordination (see skills/coordinate).

  python3 -I relay.py status <records> <key> --state <state> --doing <text>
                             [--branch <b>] [--head <sha>] [--pr-body <path>]
  python3 -I relay.py ready <records> [--repo <owner/name>] [--checkout <dir>] [--plan-limit <n>]
  python3 -I relay.py roadmap [--repo <owner/name>]
  python3 -I relay.py localcheck <records> <key> [--checkout <dir>] [--repo <owner/name>]
                                 [--comment <N>]
  python3 -I relay.py waitchecks <records> <N> [--repo <owner/name>]
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
        detached HEAD with no --branch.

ready   read-only. Prints what the coordinator can do next:
          - Ready for GO: parked lanes whose every dependency is closed as completed. The
            dependencies are the GitHub blocked-by lists of every issue on the brief's `Closes:`
            line (issue <key> when it has none; numeric keys only), minus those issues, plus
            every `#N` on the brief's `Waits for (same section):` line; the brief's
            `Depends on:` line counts only when every one of those lists is empty.
          - Ready for PR: done lanes with no pull request, status head equal to the pushed head.
          - Ready to merge: done lanes whose open PR head is the status head, checks all passed
            (at least one, none pending) and no conflict.
          - Waiting: parked lanes with an open dependency; blocked lanes, with their `doing` line;
            done lanes with a conflict, pending or failed checks, or a failed lookup. A failed
            check whose job never started (no steps, or an annotation saying it was not started:
            billing, a spending limit) shows as `checks could not run (billing)`, not `check failed`.
            A PR with no checks shows as `no CI configured` when the repo has no Actions workflow
            (`gh api repos/<repo>/actions/workflows`) and no status or check-run on the default
            branch head (`commits/HEAD/status`, `/check-runs`), else as `no checks reported`.
          - No status yet: a brief with no status file.
          - Could not parse: a status file that is not valid UTF-8, or has no valid state or no
            branch, head or time; the other lanes are still listed.
          - Merged: done lanes whose PR merged, even when the branch was deleted since (move
            them to plan-history.md).
          - Parents: open issues with sub-issues (GitHub's sub_issues_summary), with their
            children's open and closed counts, and whether every child closed as completed. A
            parent is never a lane: a status file keyed on one is Inconsistent and gets no GO.
            While this lookup fails, parked lanes wait instead of getting GO.
          - Owner notes: each parent's body or comment with a line that starts with the owner-note
            marker (GLOSSARY.md), with its link and the block from the marker to the end of that
            body or comment. A failed lookup is listed here and holds nothing.
          - Inconsistent: a done lane's status head that is not the pushed one; done with no report
            file; a PR head that is not the status head; a PR closed without merging; a dependency
            closed as not planned (it also holds GO); a PR body
            draft with a title line, a closing keyword outside a `Closes #N` line, or `Closes`
            lines that are not exactly one per issue on the brief's `Closes:` line; a line matching
            project.md's deny list (`- **Deny list:** <path>`, one regex per line; an end of the
            match that is a word character must not touch another; leading inline flags such as
            `(?i)` work; printed by line number only).
          - Records: invalid UTF-8, or a control character other than tab, LF and a CR right
            before LF, in project.md, plan.md, briefs/*.md or pr-bodies/*.md, by file and line
            (for invalid UTF-8, the first bad byte only). Checked first, so a bad byte is a
            warning, never a crash; a lane whose brief or PR body draft has one also shows as
            lookup failed.
            Also a warning when the records folder has no .gitattributes, naming the fix, and
            one when the deny list is missing or has a line that is not a usable pattern (by
            line number, never its text); done lanes then wait, with no deny-list check.
          - Plan: a warning when plan.md has more lines than --plan-limit (default 200).
          - relay.py: a warning when the git checkout holding project.md's `relay.py:` path
            (relative to --checkout, else the current folder) is behind its origin/<default>,
            with the count and the `git -C <checkout> merge --ff-only` fix. A checkout on another
            branch (or a detached HEAD), or whose default branch has commits of its own, gets that
            said instead, with no command. That checkout is fetched first. The path is a leading
            backticked span, else its text before a trailing `(...)` note. No such line, a
            project.md that is not UTF-8 (a Records warning), a missing folder, or a path outside
            a checkout: no check.
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
        missing, listed again under the table; paths are never inferred.

localcheck  the checks CI would run, for when it cannot (billing, quota). In --checkout (default
        the current folder): `git fetch`, a detached worktree at the lane's pushed head (from its
        status file's branch) with core.longpaths on, merge the default branch into it, run
        project.md's `Local checks:` line, else its `Checks before done:` line, then remove the
        worktree, even when a check fails. Commands are the backticked items of the line, split on
        `;`, one per item (an item with two, or with only a `(Windows: `...`)`, is a usage error);
        `(Windows: `...`)` replaces an item's command on Windows; items marked "main checkout
        only" are listed as not run. Prints the head and base shas and each command's output;
        --comment <N> also posts that output on PR <N>.

waitchecks  waits for PR <N>'s first check, then watches its checks. Polls `gh pr view <N> --json
        statusCheckRollup` now and at 1, 3 and 6 minutes; project.md's `CI start wait: <minutes>`
        line stretches that to 1/6, 1/2 and all of its minutes. As soon as a check exists (queued
        or pending counts), runs `gh pr checks <N> --watch`, keeping only its errors (with no
        terminal it reprints the table every 10 s, to stdout), then prints `gh pr checks <N>`
        once; both calls' errors go to stderr. None by the last poll: prints `no checks
        appeared`, plus `no CI configured` when the repo has no Actions workflow and nothing
        reported on the default branch head (as `ready` decides). A failed poll is retried at the
        next one. No overall timeout once watching.

merge   merges lanes one at a time, in the order given. First, every key must be listed under
        `ready`'s Ready to merge and nowhere else (--checkout as for `ready`, default the current
        folder), and given once, or nothing merges; so does a failed `git fetch` there.
        Then, per key, with no wait for checks (Ready to merge already needs them all passed):
        its head still the sha Ready to merge printed; mergeStateStatus `CLEAN` (UNKNOWN, while
        GitHub recomputes after a merge, is asked again after 5, 15 and 30 seconds); `gh pr merge
        <N> --merge --match-head-commit <sha>`; one line with the merge time. The first key that
        fails a test gets one line saying why, and no later key merges. After the last merge,
        prints the default branch's push run for the merge commit (`gh run list --event push
        --commit`), or that none has appeared yet.

Exit: status 0 when written, 1 when a check fails; ready 0 after printing; roadmap 0 after
printing, 1 when a lookup fails; localcheck 0 when every command passed, else 1 (a command, the
merge, a lookup or the comment failed); waitchecks 0 when the checks passed, 1 when one failed,
3 when no check appeared, 4 when a lookup failed (the last poll's, or a watch that failed with
no failed check behind it, a gh error say); merge 0 when every key merged, 1 when it stopped
(a key not ready, or a fetch, lookup, merge state or `gh pr merge` that failed);
2 on a usage error (waitchecks: a CI start wait that is not a number of minutes, or a
project.md that is not UTF-8; merge: a key given twice, or a --checkout that is not a git
checkout; localcheck: a project.md that is not UTF-8, or a checks line with more than one
command, or only a Windows override, in one item) or a missing
records folder (status too: it creates only status/ inside it).
waitchecks and merge: an error not named above (a bug, say) exits 4 with one line, never 1;
output the console cannot encode is replaced, not fatal.
`gh` is called through $RELAY_GH when set (a command line, for tests).
Standard library only, Python 3.10+.
"""
import argparse
import datetime
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


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


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


def deny_regex(pat):
    """Deny-list pattern <pat> compiled inside check_pr_body's boundary wrapper, case-insensitive.
    Leading global flags such as `(?i)` move to the front of the wrapper, the only place Python
    accepts them; re.error for a pattern the wrapper still cannot hold."""
    m = LEADING_FLAGS.match(pat)
    flags, pat = (m.group(), pat[m.end():]) if m else ("", pat)
    return re.compile(rf"{flags}(?:(?<!\w)|(?=\W))(?:{pat})(?:(?!\w)|(?<=\W))", re.I)


def deny_patterns(records):
    """The patterns of the deny list project.md names (`- **Deny list:** <path>`), else [].
    One trailing period, as the template's lines end, is dropped: `none.` means none. A line
    deny_regex cannot compile raises ValueError naming its line number, never its text."""
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
    pats = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        pat = line.strip()
        if not pat or pat.startswith("#"):
            continue
        try:
            deny_regex(pat)
        except re.error as e:
            raise ValueError(f"project.md's deny list {path.name} line {n}: not a usable "
                             f"pattern ({e.msg})") from None
        pats.append(pat)
    return pats


def pushed_head(checkout, branch):
    """The sha of origin's <branch>, "" when origin has no such branch; RuntimeError when
    ls-remote fails (no repo, no network), so the lane reads lookup failed, not unpushed."""
    code, ls, err = run(["git", "ls-remote", "origin", f"refs/heads/{branch}"], cwd=checkout)
    if code:
        raise RuntimeError(f"git ls-remote origin {branch}: {err.strip() or ls.strip()}")
    return ls.split()[0] if ls.strip() else ""


PR_FIELDS = "number,state,headRefOid,mergeable,statusCheckRollup"
PR_LIST_MIN, PR_LIST_PER_LANE = 100, 3  # `ready`'s one PR list: --limit max(MIN, PER_LANE * lanes)


def branch_prs(repo, branch):
    return gh("pr", "list", "--repo", repo, "--head", branch, "--state", "all", "--json",
              PR_FIELDS) or []


class ReadyLookups:
    """What `ready` looks up once per run instead of once per done lane: pushed heads from the
    checkout's just-fetched origin/* refs (ls-remote per branch without a checkout, or when the
    fetch or the ref read failed), and every PR from one `gh pr list --state all`. In a full
    list, a branch with no merged PR there gets its own lookup, since older PRs may be cut off.
    A failed list fails each lane that asks for it."""

    def __init__(self, checkout, fetched, lanes):
        self.checkout, self.limit = checkout, max(PR_LIST_MIN, PR_LIST_PER_LANE * lanes)
        self.use_refs, self.heads = bool(checkout and fetched), None
        self.index, self.full, self.error = None, False, None

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
            try:
                listed = gh("pr", "list", "--repo", repo, "--state", "all", "--limit",
                            str(self.limit), "--json", "headRefName," + PR_FIELDS) or []
            except LOOKUP_ERRORS as e:
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


def checks_state(rollup, repo=None):
    if not rollup:
        return "no CI configured" if no_ci(repo) else "no checks reported"
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


def check_encoding(path, name):
    """Warnings for invalid UTF-8 or a stray control character in a hand-written record."""
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        line = data.count(b"\n", 0, e.start) + 1
        return [f"{name} line {line}: invalid UTF-8 (byte {data[e.start]:#04x})"]
    out = []
    for m in CONTROL.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        out.append(f"{name} line {line}: control character U+{ord(m.group()):04X}")
    return out


# cmd_ready's output sections, in print order. One per line, so lanes adding a section don't conflict.
READY_SECTIONS = (
    "Ready for GO",
    "Ready for PR",
    "Ready to merge",
    "Waiting",
    "No status yet",
    "Merged",
    "Parents",
    "Owner notes",
    "Inconsistent",
    "Could not parse",
    "Records",
    "Plan",
    "relay.py",
)


def cmd_ready(a):
    records = pathlib.Path(a.records)
    status_dir = records / "status"
    if not records.is_dir():
        print(f"no records folder at {records}", file=sys.stderr)
        return 2
    out = {k: [] for k in READY_SECTIONS}
    plan = records / "plan.md"
    for path in [records / "project.md", plan, *sorted((records / "briefs").glob("*.md")),
                 *sorted((records / "pr-bodies").glob("*.md"))]:
        if path.is_file():
            out["Records"] += check_encoding(path, path.relative_to(records).as_posix())
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
        n = len(plan.read_text(encoding="utf-8", errors="replace").splitlines())
        if n > a.plan_limit:
            out["Plan"].append(f"plan.md has {n} lines (limit {a.plan_limit}): prune it "
                               "(move, never delete; the kinds the top of plan.md names stay)")
    repo = a.repo
    fetched = False
    if a.checkout:
        fetched = not run(["git", "fetch", "-q", "--prune", "origin"], cwd=a.checkout)[0]
    out["relay.py"] += relay_py_behind(records, a.checkout)
    repo, parents = ready_parents(repo, out)
    try:
        deny = deny_patterns(records)
    except LOOKUP_ERRORS as e:
        out["Records"].append(str(e))
        deny = None
    lookups = ReadyLookups(a.checkout, fetched, len(have))
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
        print(f"  {key}: {st['state']}, {st['branch']} @ {st['head']}, {st['time']}")
        if parents is None and st["state"] == "parked":
            out["Waiting"].append(f"{key}: parked; no GO while the Parents lookup fails")
            continue
        if key.isdigit() and int(key) in (parents or ()):
            out["Inconsistent"].append(f"{key}: issue #{key} is a parent, never a lane")
            continue
        try:
            if repo is None and (st["state"] in ("parked", "done")):
                repo = gh("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
            if st["state"] == "parked":
                ready_parked(records, key, repo, out)
            elif st["state"] == "done":
                ready_done(records, key, st, repo, a.checkout, out, lookups, fetched, deny)
            elif st["state"] == "blocked":
                out["Waiting"].append(f"{key}: blocked: {st.get('doing', '')}")
        except LOOKUP_ERRORS as e:
            out["Waiting"].append(f"{key}: lookup failed: {e}")
    if not have:
        print("  (none)")
    for section, items in out.items():
        if items:
            print(f"{section}:")
            for item in items:
                print(f"  {item}")
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


def ready_done(records, key, st, repo, checkout, out, lookups=None, fetched=True, deny=()):
    """Sort done lane <key> into out's sections. `lookups` (a ReadyLookups) shares one PR list and
    one ref read across lanes; without it, one ls-remote and one PR list for this lane. When the
    checkout's fetch failed (`fetched` false), its origin/* refs may be stale or missing: the
    conflict check is skipped and the lane's line says so. `deny`: the deny_patterns the caller
    loaded once, None when they failed to load (the lane then waits; the caller reports why),
    () to load them here."""
    branch, head = st["branch"], st["head"]
    pushed_of = lookups.pushed if lookups else (lambda b: pushed_head(checkout, b))
    prs_of = lookups.prs if lookups else branch_prs
    if not (records / "reports" / f"{key}.md").exists():
        out["Inconsistent"].append(f"{key}: done with no report file")
    pushed = pushed_of(branch)
    prs = None if pushed else prs_of(repo, branch)  # a branch deleted after its merge is Merged
    if not pushed.startswith(head) and not any(p["state"].upper() == "MERGED"
                                               and p["headRefOid"].startswith(head) for p in prs or []):
        out["Inconsistent"].append(f"{key}: status head {head} is not the pushed head "
                                   f"{pushed[:12] or '(branch not pushed)'}")
        return
    if deny is None:
        out["Waiting"].append(f"{key}: deny-list check not run (see Records)")
        return
    for problem in check_pr_body(st.get("PR body draft", ""), brief_issues(records, key, "Closes:"),
                                 deny_patterns(records) if deny == () else deny):
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
    checks = checks_state(pr.get("statusCheckRollup"), repo)
    if pr.get("mergeable", "").upper() == "CONFLICTING":
        out["Waiting"].append(f"{key}: PR #{pr['number']} has a merge conflict")
    elif checks != "passed":
        out["Waiting"].append(f"{key}: PR #{pr['number']} {checks}")
    else:
        out["Ready to merge"].append(f"{key}: PR #{pr['number']} --match-head-commit "
                                     f"{pr['headRefOid']}{skipped}")


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


def check_commands(line, windows=None):
    """(commands, skipped) from a project.md checks line: `;`-separated items, each command in
    backticks. A `(Windows: `...`)` in an item, before or after its command, replaces that command
    on Windows; an item marked "main checkout only" is skipped. ValueError, naming the line, when
    an item holds more than one command outside its Windows override (never run only the first),
    or only an override (no command for other systems)."""
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
    commands, skipped = [], []
    for item in items:
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
        (skipped if "main checkout only" in item else commands).append(cmd)
    return commands, skipped


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
        commands, skipped = check_commands(line)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    if not commands:
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
        lines += [f"not run (main checkout only): {c}" for c in skipped]
        result = "passed" if ok else "failed"
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

NO_CHECKS, LOOKUP_FAILED = 3, 4
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
    or pending included, then `gh pr checks --watch` it. Returns 0 when the checks passed, 1 when
    one failed, NO_CHECKS when none appeared by the last poll, LOOKUP_FAILED when the last poll's
    lookup failed with none seen, or the watch failed with no failed check behind it."""
    start, error = time.monotonic(), None
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
            code, _, err = run(checks + ["--watch"])
            _, out, table_err = run(checks)
            print(out.rstrip())
            errors = "\n".join(e.rstrip() for e in (err, table_err) if e.strip())
            if errors:
                print(errors, file=sys.stderr)
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
    if error is not None:
        return LOOKUP_FAILED
    print(f"no checks appeared on PR #{pr} within {schedule[-1] / 60:g} minutes")
    if no_ci(repo):
        print("no CI configured: no Actions workflow and nothing reported on the default branch head")
    return NO_CHECKS


def cmd_waitchecks(a):
    records = pathlib.Path(a.records)
    if not records.is_dir():
        print(f"no records folder at {records}", file=sys.stderr)
        return 2
    try:
        schedule = ci_start_schedule(records)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    try:
        repo = a.repo or gh("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
    except LOOKUP_ERRORS as e:
        print(f"lookup failed: {e}", file=sys.stderr)
        return LOOKUP_FAILED
    return wait_checks(a.pr, repo, schedule)


# merge ----------------------------------------------------------------------------------------

READY_TO_MERGE = re.compile(r"PR #(\d+) --match-head-commit ([0-9a-f]{40})$")
STATE_RETRIES = (5, 15, 30)  # seconds; GitHub says UNKNOWN while it recomputes after a merge
RUN_WAITS = (0, 10, 20)  # seconds; a push run takes a few seconds to appear


def ready_to_merge(records, key, repo, checkout):
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
        ready_done(records, key, st, repo, checkout, out)
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
    code, out, err = run(gh_base() + ["pr", "merge", str(pr), "--repo", repo, "--merge",
                                      "--match-head-commit", sha])
    if code:
        fail(f"{key}: gh pr merge {pr} failed: {' '.join((err or out).split())}")
        return None
    try:
        merged = gh("pr", "view", str(pr), "--repo", repo, "--json", "mergedAt,mergeCommit")
        print(f"{key}: merged PR #{pr} at {merged['mergedAt']}", flush=True)
        return merged["mergeCommit"]["oid"], view["baseRefName"]
    except LOOKUP_ERRORS as e:
        print(f"{key}: merged PR #{pr}; merge time lookup failed: {e}", flush=True)
        return None, view["baseRefName"]


def report_push_run(repo, base, sha):
    """Print the push run on <base> for merge commit <sha>, or say there is none yet."""
    runs = []
    for wait in RUN_WAITS:
        time.sleep(wait)
        try:
            runs = gh("run", "list", "--repo", repo, "--branch", base, "--event", "push", "--commit",
                      sha, "--json", "databaseId,status,conclusion,url") or []
        except LOOKUP_ERRORS as e:
            fail(f"push run lookup failed: {e}")
            return
        if runs:
            break
    for r in runs:
        state = " ".join(filter(None, (r.get("status"), r.get("conclusion"), r.get("url"))))
        print(f"{base} push run for {sha[:8]}: {state}")
    if not runs:
        print(f"no push run on {base} for {sha[:8]} yet: "
              f"gh run list --repo {repo} --branch {base} --event push --commit {sha}")


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
    lanes = []
    for key in a.keys:
        found = ready_to_merge(records, key, repo, a.checkout)
        if isinstance(found, str):
            return fail(f"{key}: not under Ready to merge ({found}); nothing merged")
        lanes.append((key, *found))
    last = None
    for key, pr, sha in lanes:
        last = merge_lane(key, pr, sha, repo)
        if last is None:
            return 1
    if last[0]:
        report_push_run(repo, last[1], last[0])
    return 0


def fail(msg):
    print(msg, file=sys.stderr)
    return 1


def main(argv=None):
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
    r.add_argument("--plan-limit", type=int, default=200)
    c = sub.add_parser("localcheck", help="run the project's checks on a lane merged with the default branch")
    c.add_argument("records")
    c.add_argument("key")
    c.add_argument("--checkout", default=".")
    c.add_argument("--repo")
    c.add_argument("--comment", type=int, metavar="N")
    w = sub.add_parser("waitchecks", help="wait for a PR's first check, then watch its checks")
    w.add_argument("records")
    w.add_argument("pr", type=int)
    w.add_argument("--repo")
    g = sub.add_parser("merge", help="merge Ready to merge lanes one at a time, stopping on the first problem")
    g.add_argument("records")
    g.add_argument("keys", nargs="+", metavar="key")
    g.add_argument("--repo")
    g.add_argument("--checkout", default=".")
    m = sub.add_parser("roadmap", help="print each open issue's blocked-by and `## Files`")
    m.add_argument("--repo")
    a = p.parse_args(argv)
    command = {"status": cmd_status, "ready": cmd_ready, "roadmap": cmd_roadmap,
               "localcheck": cmd_localcheck, "waitchecks": cmd_waitchecks,
               "merge": cmd_merge}[a.cmd]
    if a.cmd in ("localcheck", "waitchecks", "merge"):
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(errors="replace")  # output the console cannot hold
    if a.cmd not in ("waitchecks", "merge"):
        return command(a)
    # their exit 1 means a check failed or a merge stopped: never let an error say that
    try:
        return command(a)
    except Exception as e:  # noqa: BLE001
        print(f"{a.cmd}: unexpected error: {type(e).__name__}: {' '.join(str(e).split())}",
              file=sys.stderr)
        return LOOKUP_FAILED


if __name__ == "__main__":
    sys.exit(main())
