#!/usr/bin/env python3
"""relay: the two scripted steps of multi-session coordination (see skills/coordinate).

  python3 -I relay.py status <records> <key> --state <state> --doing <text>
                             [--branch <b>] [--head <sha>] [--pr-body <path>]
  python3 -I relay.py ready <records> [--repo <owner/name>] [--checkout <dir>] [--plan-limit <n>]
  python3 -I relay.py localcheck <records> <key> [--checkout <dir>] [--repo <owner/name>]
                                 [--comment <N>]
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
          - No status yet: a brief with no status file.
          - Merged: done lanes whose PR merged (move them to plan-history.md).
          - Inconsistent: a done lane's status head that is not the pushed one; done with no report
            file; a PR head that is not the status head; a PR closed without merging; a dependency
            closed as not planned (it also holds GO); a PR body
            draft with a title line, a closing keyword outside a `Closes #N` line, or `Closes`
            lines that are not exactly one per issue on the brief's `Closes:` line; a line matching
            project.md's deny list (`- **Deny list:** <path>`, one regex per line, matched as a
            whole word; printed by line number only).
          - Plan: a warning when plan.md has more lines than --plan-limit (default 200).
        --checkout <dir>: a local clone; `git fetch` there, then `git merge-tree` each Ready for
        PR / Ready to merge branch against the default branch; a conflict moves it to Waiting.
        --repo defaults to what `gh repo view` finds from the current folder.

localcheck  the checks CI would run, for when it cannot (billing, quota). In --checkout (default
        the current folder): `git fetch`, a detached worktree at the lane's pushed head (from its
        status file's branch) with core.longpaths on, merge the default branch into it, run
        project.md's `Local checks:` line, else its `Checks before done:` line, then remove the
        worktree, even when a check fails. Commands are the backticked items of the line, split on
        `;`; `(Windows: `...`)` replaces an item's command on Windows; items marked "main checkout
        only" are listed as not run. Prints the head and base shas and each command's output;
        --comment <N> also posts that output on PR <N>.

Exit: status 0 when written, 1 when a check fails; ready 0 after printing; localcheck 0 when every
command passed, else 1 (a command, the merge, a lookup or the comment failed); 2 on a usage error or
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
import shutil
import subprocess
import sys
import tempfile

STATES = ("parked", "working", "blocked", "review", "done")
FIELDS = ("state", "branch", "head", "PR body draft", "time", "doing")
CLOSING = re.compile(r"\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\b:?\s*#\d+", re.I)
CLOSES_LINE = re.compile(r"^Closes #\d+\s*$")


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def gh_raw(*args):
    """gh's stdout as text; RuntimeError when it fails."""
    base = [t.strip('"') for t in shlex.split(os.environ.get("RELAY_GH", "gh"), posix=False)]
    code, out, err = run(base + list(args))
    if code:
        raise RuntimeError(f"gh {' '.join(args)}: {err.strip() or out.strip()}")
    return out


def gh(*args):
    out = gh_raw(*args)
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


def checks_state(rollup, repo=None):
    if not rollup:
        return "no checks reported"
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
                               "(move, never delete; the kinds the top of plan.md names stay)")
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
    st = parse_status(status.read_text(encoding="utf-8")) if status.exists() else {}
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
    a = p.parse_args(argv)
    return {"status": cmd_status, "ready": cmd_ready, "localcheck": cmd_localcheck}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
