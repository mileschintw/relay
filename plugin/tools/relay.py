#!/usr/bin/env python3
"""relay: the two scripted steps of multi-session coordination (see skills/coordinate).

  python3 -I relay.py status <records> <key> --state <state> --doing <text>
                             [--branch <b>] [--head <sha>] [--pr-body <path>]
  python3 -I relay.py ready <records> [--repo <owner/name>] [--checkout <dir>] [--plan-limit <n>]
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
            done lanes with a conflict, pending or failed checks, or a failed lookup.
          - No status yet: a brief with no status file.
          - Merged: done lanes whose PR merged (move them to plan-history.md).
          - Parents: open issues with sub-issues (GitHub's sub_issues_summary), with their
            children's open and closed counts, and whether every child closed as completed. A
            parent is never a lane: a status file keyed on one is Inconsistent and gets no GO.
            While this lookup fails, parked lanes wait instead of getting GO.
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
          - Plan: a warning when plan.md has more lines than --plan-limit (default 200).
        --checkout <dir>: a local clone; `git fetch` there, then `git merge-tree` each Ready for
        PR / Ready to merge branch against the default branch; a conflict moves it to Waiting.
        --repo defaults to what `gh repo view` finds from the current folder.

Exit: status 0 when written, 1 when a check fails; ready 0 after printing; 2 on a usage error or
a missing records folder. `gh` is called through $RELAY_GH
when set (a command line, for tests). Standard library only, Python 3.10+.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys

STATES = ("parked", "working", "blocked", "review", "done")
FIELDS = ("state", "branch", "head", "PR body draft", "time", "doing")
CLOSING = re.compile(r"\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\b:?\s*#\d+", re.I)
CLOSES_LINE = re.compile(r"^Closes #\d+\s*$")
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|\r(?!\n)")


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def gh(*args, jsonl=False):
    base = [t.strip('"') for t in shlex.split(os.environ.get("RELAY_GH", "gh"), posix=False)]
    code, out, err = run(base + list(args))
    if code:
        raise RuntimeError(f"gh {' '.join(args)}: {err.strip() or out.strip()}")
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
    """The patterns of the deny list project.md names (`- **Deny list:** <path>`), else []."""
    project = records / "project.md"
    if not project.exists():
        return []
    m = re.search(r"^- \*\*Deny list:\*\* `?([^`\n]+?)`?\s*$", project.read_text(encoding="utf-8"), re.M)
    if not m or m.group(1).strip().strip('"').lower() == "none":
        return []
    path = pathlib.Path(m.group(1).strip())
    path = path if path.is_absolute() else records / path
    if not path.exists():
        raise FileNotFoundError(f"project.md's deny list {path} does not exist")
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


def checks_state(rollup):
    if not rollup:
        return "no checks reported"
    for c in rollup:
        status = (c.get("status") or "COMPLETED").upper()
        result = (c.get("conclusion") or c.get("state") or "").upper()
        if status != "COMPLETED" or result in ("", "PENDING", "EXPECTED", "QUEUED"):
            return "checks pending"
        if result not in ("SUCCESS", "NEUTRAL", "SKIPPED"):
            return f"check failed: {c.get('name') or c.get('context')}"
    return "passed"


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


def cmd_ready(a):
    records = pathlib.Path(a.records)
    status_dir = records / "status"
    if not records.is_dir():
        print(f"no records folder at {records}", file=sys.stderr)
        return 2
    out = {k: [] for k in ("Ready for GO", "Ready for PR", "Ready to merge", "Waiting",
                           "No status yet", "Merged", "Parents", "Inconsistent", "Could not parse",
                           "Records", "Plan")}
    plan = records / "plan.md"
    for path in [plan, *sorted((records / "briefs").glob("*.md")),
                 *sorted((records / "pr-bodies").glob("*.md"))]:
        if path.is_file():
            out["Records"] += check_encoding(path, path.relative_to(records).as_posix())
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
    repo, parents = ready_parents(repo, out)
    print("Lanes:")
    for path in sorted(status_dir.glob("*.md")):
        key = path.stem
        st = parse_status(path.read_text(encoding="utf-8"))
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


def ready_parents(repo, out):
    """Open issues with sub-issues (GitHub's sub_issues_summary), listed under Parents with their
    children's open and closed counts. Returns (repo, the parents' numbers), or (repo, None) when
    the lookup fails. A parent is never a lane."""
    issue_jq = ".[] | select(.pull_request == null) | {number, title, sub_issues_summary}"
    parents = set()
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
    except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
        out["Parents"].append(f"lookup failed: {e}")
        return repo, None
    return repo, parents


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
    checks = checks_state(pr.get("statusCheckRollup"))
    if pr.get("mergeable", "").upper() == "CONFLICTING":
        out["Waiting"].append(f"{key}: PR #{pr['number']} has a merge conflict")
    elif checks != "passed":
        out["Waiting"].append(f"{key}: PR #{pr['number']} {checks}")
    else:
        out["Ready to merge"].append(f"{key}: PR #{pr['number']} --match-head-commit {pr['headRefOid']}")


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
    a = p.parse_args(argv)
    return cmd_status(a) if a.cmd == "status" else cmd_ready(a)


if __name__ == "__main__":
    sys.exit(main())
