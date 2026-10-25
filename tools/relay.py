#!/usr/bin/env python3
"""relay: the two scripted steps of multi-session coordination (see skills/coordinate).

  python3 -I relay.py status <records> <key> --state <state> --doing <text>
                             [--branch <b>] [--head <sha>] [--pr-body <path>]
  python3 -I relay.py ready <records> [--repo <owner/name>] [--checkout <dir>] [--plan-limit <n>]
(Windows: py -3 -I ...)

<records> is the records folder (the `coord` worktree): plan.md, briefs/, status/, reports/,
pr-bodies/. <key> names a lane: the issue number it closes first (`12`), or a short name.

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
            `Depends on:` line counts only when GitHub lists no blocker.
          - Ready for PR: done lanes with no pull request, status head equal to the pushed head.
          - Ready to merge: done lanes whose open PR head is the status head, checks all passed
            (at least one, none pending) and no conflict.
          - Waiting: everything blocked on someone else, with the reason.
          - No status yet: a brief with no status file.
          - Merged: done lanes whose PR merged (move them to plan-history.md).
          - Inconsistent: a status head that is not the pushed one, done with no report file, a
            PR head that is not the status head, a PR body draft with a closing keyword outside a
            `Closes #N` line, a title line, or no `Closes` line.
          - Plan: a warning when plan.md has more lines than --plan-limit (default 200).
        --checkout <dir>: a local clone; `git fetch` there, then `git merge-tree` each Ready for
        PR / Ready to merge branch against the default branch; a conflict moves it to Waiting.
        --repo defaults to what `gh repo view` finds from the current folder.

Exit 0 when done, 1 when a check fails, 2 on a usage error or a missing records folder. `gh` is called through $RELAY_GH
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


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def gh(*args):
    base = [t.strip('"') for t in shlex.split(os.environ.get("RELAY_GH", "gh"), posix=False)]
    code, out, err = run(base + list(args))
    if code:
        raise RuntimeError(f"gh {' '.join(args)}: {err.strip() or out.strip()}")
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

def check_pr_body(path):
    p = pathlib.Path(path)
    if not p.exists():
        return ["no PR body draft"]
    lines = p.read_text(encoding="utf-8").splitlines()
    problems = []
    if lines and lines[0].startswith("# "):
        problems.append("PR body starts with a title line")
    if not any(CLOSES_LINE.match(l) for l in lines):
        problems.append("PR body has no `Closes #N` line")
    for i, l in enumerate(lines, 1):
        if CLOSING.search(l) and not CLOSES_LINE.match(l):
            problems.append(f"PR body line {i}: closing keyword outside a `Closes #N` line")
    return problems


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


def cmd_ready(a):
    records = pathlib.Path(a.records)
    status_dir = records / "status"
    if not records.is_dir():
        print(f"no records folder at {records}", file=sys.stderr)
        return 2
    out = {k: [] for k in ("Ready for GO", "Ready for PR", "Ready to merge", "Waiting",
                           "No status yet", "Merged", "Inconsistent", "Could not parse", "Plan")}
    have = {p.stem for p in status_dir.glob("*.md")}
    for b in sorted((records / "briefs").glob("*.md")):
        if not b.stem.startswith("_") and b.stem not in have:
            out["No status yet"].append(f"{b.stem}: a brief but no status file (not started, or not yet run)")
    plan = records / "plan.md"
    if plan.exists():
        n = len(plan.read_text(encoding="utf-8").splitlines())
        if n > a.plan_limit:
            out["Plan"].append(f"plan.md has {n} lines (limit {a.plan_limit}): prune it "
                               "(move, never delete; the five kept kinds stay)")
    repo = a.repo
    if a.checkout:
        run(["git", "fetch", "-q", "origin"], cwd=a.checkout)
    print("Lanes:")
    for path in sorted(status_dir.glob("*.md")):
        key = path.stem
        st = parse_status(path.read_text(encoding="utf-8"))
        missing = [f for f in ("state", "branch", "head", "time") if f not in st]
        if missing or st.get("state") not in STATES:
            out["Could not parse"].append(f"{key}: missing or bad {missing or ['state']}")
            continue
        print(f"  {key}: {st['state']}, {st['branch']} @ {st['head']}, {st['time']}")
        try:
            if repo is None and (st["state"] in ("parked", "done")):
                repo = gh("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
            if st["state"] == "parked":
                ready_parked(records, key, repo, out)
            elif st["state"] == "done":
                ready_done(records, key, st, repo, a.checkout, out)
        except (RuntimeError, ValueError, KeyError, TypeError) as e:
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


def ready_parked(records, key, repo, out):
    if not (records / "briefs" / f"{key}.md").exists():
        out["Inconsistent"].append(f"{key}: parked with no brief")
    deps, source = dependencies(records, key, repo)
    open_deps = []
    for d in deps:
        issue = gh("issue", "view", str(d), "--repo", repo, "--json", "state,stateReason")
        if issue["state"].upper() != "CLOSED" or (issue.get("stateReason") or "").upper() != "COMPLETED":
            open_deps.append(f"#{d} {issue['state'].lower()}")
    if open_deps:
        out["Waiting"].append(f"{key}: parked on {', '.join(open_deps)}")
    else:
        note = " (dependencies from the brief's Depends on:)" if source == "brief" and deps else ""
        out["Ready for GO"].append(f"{key}: send `GO #{key}`{note}")


def ready_done(records, key, st, repo, checkout, out):
    branch, head = st["branch"], st["head"]
    if not (records / "reports" / f"{key}.md").exists():
        out["Inconsistent"].append(f"{key}: done with no report file")
    code, ls, _ = run(["git", "ls-remote", "origin", f"refs/heads/{branch}"], cwd=checkout)
    pushed = ls.split()[0] if ls.strip() else ""
    if not pushed.startswith(head):
        out["Inconsistent"].append(f"{key}: status head {head} is not the pushed head "
                                   f"{pushed[:12] or '(branch not pushed)'}")
        return
    for problem in check_pr_body(st.get("PR body draft", "")):
        out["Inconsistent"].append(f"{key}: {problem}")
    prs = gh("pr", "list", "--repo", repo, "--head", branch, "--state", "all", "--json",
             "number,state,headRefOid,mergeable,statusCheckRollup") or []
    if any(p["state"].upper() == "MERGED" for p in prs):
        out["Merged"].append(f"{key}: PR #{[p for p in prs if p['state'].upper() == 'MERGED'][0]['number']}")
        return
    pr = next((p for p in prs if p["state"].upper() == "OPEN"), None)
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
