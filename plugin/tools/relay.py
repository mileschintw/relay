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
            dependencies are the GitHub blocked-by list of issue <key> (numeric keys only) plus
            every `#N` on the brief's `Waits for (same section):` line; the brief's
            `Depends on:` line counts only when GitHub lists no blocked-by entry.
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
          - Merged: done lanes whose PR merged (move them to plan-history.md).
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
            project.md's deny list (`- **Deny list:** <path>`, one regex per line, matched as a
            whole word; printed by line number only).
          - Records: invalid UTF-8, or a control character other than tab, LF and a CR right
            before LF, in plan.md, briefs/*.md or pr-bodies/*.md, by file and line (for invalid
            UTF-8, the first bad byte only). Checked first, so a bad byte is a warning, never a
            crash; a lane whose brief or PR body draft has one also shows as lookup failed.
            Also a warning when the records folder has no .gitattributes, naming the fix.
          - Plan: a warning when plan.md has more lines than --plan-limit (default 200).
          - relay.py: a warning when the git checkout holding project.md's `relay.py:` path
            (relative to --checkout, else the current folder) is behind its origin/<default>,
            with the count and the `git -C <checkout> merge --ff-only` fix (a `switch` first when
            it is on another branch). That checkout is fetched first. The path is a leading
            backticked span, else its text before a trailing `(...)` note. No such line, a
            missing folder, or a path outside a checkout: no check.
        --checkout <dir>: a local clone; `git fetch` there, then `git merge-tree` each Ready for
        PR / Ready to merge branch against the default branch; a conflict moves it to Waiting.
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
        `;`; `(Windows: `...`)` replaces an item's command on Windows; items marked "main checkout
        only" are listed as not run. Prints the head and base shas and each command's output;
        --comment <N> also posts that output on PR <N>.

waitchecks  waits for PR <N>'s first check, then watches its checks. Polls `gh pr view <N> --json
        statusCheckRollup` now and at 1, 3 and 6 minutes; project.md's `CI start wait: <minutes>`
        line stretches that to 1/6, 1/2 and all of its minutes. As soon as a check exists (queued
        or pending counts), runs `gh pr checks <N> --watch` and prints its output. None by the last
        poll: prints `no checks appeared`, plus `no CI configured` when the repo has no Actions
        workflow and nothing reported on the default branch head (as `ready` decides). A failed
        poll is retried at the next one. No overall timeout once watching.

merge   merges lanes one at a time, in the order given. First, every key must be listed under
        `ready`'s Ready to merge and nowhere else (--checkout as for `ready`), or nothing merges.
        Then, per key: waitchecks on its PR; its head still the sha Ready to merge printed;
        mergeStateStatus `CLEAN` (UNKNOWN, while GitHub recomputes after a merge, is asked again
        after 5, 15 and 30 seconds); `gh pr merge <N> --merge --match-head-commit <sha>`; one line
        with the merge time. The first key that fails a test gets one line saying why, and no
        later key merges. After the last merge, prints the default branch's push run for the
        merge commit (`gh run list --event push --commit`), or that none has appeared yet.

Exit: status 0 when written, 1 when a check fails; ready 0 after printing; roadmap 0 after
printing, 1 when a lookup fails; localcheck 0 when every command passed, else 1 (a command, the
merge, a lookup or the comment failed); waitchecks 0 when the checks passed, 1 when one failed,
3 when no check appeared, 4 when a lookup failed (the last poll's, or a watch that failed with
no failed check behind it, a gh error say); merge 0 when every key merged, 1 when it stopped;
2 on a usage error (waitchecks, merge: a CI start wait that is not a number of minutes) or a
missing records folder. `gh` is called through $RELAY_GH when set (a command line, for tests).
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
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"wrote {out_path}")
    print(text, end="")
    return 0


# ready ----------------------------------------------------------------------------------------

def check_pr_body(path, closes=None, deny=None):
    """Problems with a PR body draft. closes: the issues the brief's Closes line lists (None or []:
    not known). deny: regex patterns matched as whole words; a hit is reported by line number only."""
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
    hits = sorted({i for i, l in enumerate(lines, 1) for pat in deny or []
                   if re.search(rf"\b(?:{pat})\b", l, re.I)})
    if hits:
        problems.append(f"PR body lines {hits}: a deny-list name (lines only, never the name)")
    return problems


def deny_patterns(records):
    """The patterns of the deny list project.md names (`- **Deny list:** <path>`), else [].
    One trailing period, as the template's lines end, is dropped: `none.` means none."""
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
    pats = [l.strip() for l in path.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.lstrip().startswith("#")]
    for pat in pats:
        re.compile(pat)
    return pats


def pushed_head(checkout, branch):
    code, ls, _ = run(["git", "ls-remote", "origin", f"refs/heads/{branch}"], cwd=checkout)
    return ls.split()[0] if ls.strip() else ""


def dependencies(records, key, repo):
    deps, source = [], "github"
    if key.isdigit():
        blocked = gh("api", f"repos/{repo}/issues/{key}/dependencies/blocked_by") or []
        deps = [b["number"] for b in blocked]
    if not deps:
        deps, source = brief_issues(records, key, "Depends on:") or [], "brief"
    waits = brief_issues(records, key, "Waits for (same section):") or []
    return sorted(set(deps) | set(waits)), source


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
    for path in [plan, *sorted((records / "briefs").glob("*.md")),
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
    if a.checkout:
        run(["git", "fetch", "-q", "origin"], cwd=a.checkout)
    out["relay.py"] += relay_py_behind(records, a.checkout)
    repo, parents = ready_parents(repo, out)
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
                ready_done(records, key, st, repo, a.checkout, out)
            elif st["state"] == "blocked":
                out["Waiting"].append(f"{key}: blocked: {st.get('doing', '')}")
        except (RuntimeError, ValueError, KeyError, TypeError, OSError, re.error) as e:
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
    line, or a path outside a git checkout, is no check. Fetches that checkout unless it is
    `checkout`, which cmd_ready has just fetched."""
    value = project_line(records, "relay.py")
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
    git_c = f'git -C "{where}"' if " " in where else f"git -C {where}"
    name = default.split("/", 1)[-1]
    _, branch, _ = run(["git", "symbolic-ref", "--short", "-q", "HEAD"], cwd=top)
    switch = "" if branch.strip() == name else f"{git_c} switch {name} && "
    return [f"{where} is {count} commit{'s' if count > 1 else ''} behind {default}: "
            f"{switch}{git_c} merge --ff-only {default}"]


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


def ready_done(records, key, st, repo, checkout, out):
    branch, head = st["branch"], st["head"]
    if not (records / "reports" / f"{key}.md").exists():
        out["Inconsistent"].append(f"{key}: done with no report file")
    pushed = pushed_head(checkout, branch)
    if not pushed.startswith(head):
        out["Inconsistent"].append(f"{key}: status head {head} is not the pushed head "
                                   f"{pushed[:12] or '(branch not pushed)'}")
        return
    for problem in check_pr_body(st.get("PR body draft", ""), brief_issues(records, key, "Closes:"),
                                 deny_patterns(records)):
        out["Inconsistent"].append(f"{key}: {problem}")
    prs = gh("pr", "list", "--repo", repo, "--head", branch, "--state", "all", "--json",
             "number,state,headRefOid,mergeable,statusCheckRollup") or []
    if any(p["state"].upper() == "MERGED" for p in prs):
        out["Merged"].append(f"{key}: PR #{[p for p in prs if p['state'].upper() == 'MERGED'][0]['number']}")
        return
    pr = next((p for p in prs if p["state"].upper() == "OPEN"), None)
    if pr is None and prs:
        out["Inconsistent"].append(f"{key}: PR #{prs[0]['number']} closed without merging")
        return
    files = conflicts(checkout, branch) if checkout else []
    if files:
        out["Waiting"].append(f"{key}: conflicts with the default branch: {', '.join(files)}")
        return
    if pr is None:
        out["Ready for PR"].append(f"{key}: {branch} @ {head}")
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
        out["Ready to merge"].append(f"{key}: PR #{pr['number']} --match-head-commit {pr['headRefOid']}")


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
    """The text after `- **<label>:**` in project.md, or None."""
    project = records / "project.md"
    if not project.exists():
        return None
    m = re.search(rf"^- \*\*{re.escape(label)}:\*\*(.*)$", project.read_text(encoding="utf-8"), re.M)
    value = m.group(1).strip() if m else ""
    return value if value.strip("`\". ").lower() not in ("", "none") else None


def check_commands(line, windows=None):
    """(commands, skipped) from a project.md checks line: `;`-separated items, each command in
    backticks. A `(Windows: `...`)` in an item replaces its command on Windows; an item marked
    "main checkout only" is skipped."""
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
        spans = re.findall(r"`([^`]+)`", item)
        if not spans:
            continue
        win = re.search(r"\(Windows:\s*`([^`]+)`", item)
        cmd = win.group(1) if win and windows else spans[0]
        (skipped if "main checkout only" in item else commands).append(cmd)
    return commands, skipped


def cmd_localcheck(a):
    records = pathlib.Path(a.records)
    if not records.is_dir():
        print(f"no records folder at {records}", file=sys.stderr)
        return 2
    checkout = os.path.abspath(a.checkout)
    line = project_line(records, "Local checks") or project_line(records, "Checks before done")
    if line is None:
        return fail(f"{records / 'project.md'} has no `- **Local checks:**` line and no "
                    "`- **Checks before done:**` line: add the command that runs the checks")
    commands, skipped = check_commands(line)
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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # check output may hold what the console cannot
    print(report)
    if a.comment:
        body = pathlib.Path(wt + ".md")
        body.write_text(f"```\n{report}\n```\n", encoding="utf-8")
        try:
            repo = a.repo or gh("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
            gh_raw("pr", "comment", str(a.comment), "--repo", repo, "--body-file", str(body))
        except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
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
        except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
            rollup, error = None, e
            print(f"poll {i} at {at / 60:g} min: lookup failed: {e}", file=sys.stderr)
        if rollup:
            print(f"poll {i} at {at / 60:g} min: {len(rollup)} check(s); watching", flush=True)
            code, out, err = run(gh_base() + ["pr", "checks", str(pr), "--repo", repo, "--watch"])
            print((out + err).rstrip())
            if code == 0:
                return 0
            # gh exits 1 on a failed check and on its own errors alike: ask the rollup which
            try:
                state = checks_state(pr_rollup(pr, repo), repo)
            except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
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
    except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
        print(f"lookup failed: {e}", file=sys.stderr)
        return LOOKUP_FAILED
    return wait_checks(a.pr, repo, schedule)


# merge ----------------------------------------------------------------------------------------

READY_TO_MERGE = re.compile(r"PR #(\d+) --match-head-commit ([0-9a-f]{40})$")
STATE_RETRIES = (5, 15, 30)  # seconds; GitHub says UNKNOWN while it recomputes after a merge
RUN_WAITS = (0, 10, 20)  # seconds; a push run takes a few seconds to appear
LOOKUP_ERRORS = (RuntimeError, ValueError, KeyError, TypeError, OSError, re.error)


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
    if st.get("state") != "done" or not ("branch" in st and "head" in st):
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


def merge_lane(key, pr, sha, repo, schedule):
    """Wait for PR <pr>'s checks, require head <sha> and mergeStateStatus CLEAN, then merge with
    --match-head-commit. Returns (merge commit sha or None, base branch), or None after printing
    one line on why it stopped."""
    code = wait_checks(pr, repo, schedule)
    if code:
        fail(f"{key}: PR #{pr} checks did not pass (waitchecks exit {code})")
        return None
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
            print(f"push run lookup failed: {e}")
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
    try:
        schedule = ci_start_schedule(records)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    try:
        repo = a.repo or gh("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
    except LOOKUP_ERRORS as e:
        return fail(f"lookup failed: {e}")
    if a.checkout:
        run(["git", "fetch", "-q", "origin"], cwd=a.checkout)
    lanes = []
    for key in a.keys:
        found = ready_to_merge(records, key, repo, a.checkout)
        if isinstance(found, str):
            return fail(f"{key}: not under Ready to merge ({found}); nothing merged")
        lanes.append((key, *found))
    last = None
    for key, pr, sha in lanes:
        last = merge_lane(key, pr, sha, repo, schedule)
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
    g.add_argument("--checkout")
    m = sub.add_parser("roadmap", help="print each open issue's blocked-by and `## Files`")
    m.add_argument("--repo")
    a = p.parse_args(argv)
    return {"status": cmd_status, "ready": cmd_ready, "roadmap": cmd_roadmap,
            "localcheck": cmd_localcheck, "waitchecks": cmd_waitchecks, "merge": cmd_merge}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
