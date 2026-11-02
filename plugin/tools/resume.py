#!/usr/bin/env python3
"""relay's SessionStart (compact) hook: after a compact, point a coordinator or worker at its records.

  python3 -I resume.py          (hook input JSON on stdin; prints the pointer, or nothing)

Finds the records folder (the repo's AGENTS.md/CLAUDE.md pointer line, else the worktree
`git worktree list` shows on branch coord). When this session's worktree is the coordinator's in
plan.md's Handover, prints the user's language line and what to reread; when its branch is a
lane's in status/<key>.md, prints the language line and that lane's brief, status and report
paths. Anything else, or any failure, prints nothing: the hook never blocks a session.
"""
import json
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import relay  # noqa: E402  (beside this file; -I leaves the script's folder off sys.path)

POINTER = re.compile(r"Multi-session work: records in (?:the worktree on branch coord|(\S+) beside)")


def git(cwd, *args):
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else ""


def same(a, b):
    def norm(p):
        return os.path.normcase(os.path.realpath(str(p).strip().rstrip("\\/")))
    return norm(a) == norm(b)


def worktrees(cwd):
    """(path, branch) for each worktree, the main checkout first."""
    out, path = [], None
    for line in git(cwd, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
            out.append((path, None))
        elif line.startswith("branch ") and out:
            out[-1] = (path, line[len("branch refs/heads/"):])
    return out


def find_records(top, trees):
    for name in ("AGENTS.md", "CLAUDE.md"):
        f = pathlib.Path(top) / name
        m = POINTER.search(f.read_text(encoding="utf-8", errors="replace")) if f.is_file() else None
        if m and m.group(1) and trees:
            return pathlib.Path(trees[0][0]).parent / pathlib.Path(m.group(1)).name
        if m:
            break
    return next((pathlib.Path(p) for p, b in trees if b == "coord"), None)


def field(text, label):
    m = re.search(rf"^- \*\*{re.escape(label)}:\*\*(.*)$", text, re.M)
    return m.group(1).strip() if m else ""


def resume(cwd):
    top = git(cwd, "rev-parse", "--show-toplevel").strip()
    if not top:
        return ""
    trees = worktrees(top)
    records = find_records(top, trees)
    if not records or not (records / "project.md").is_file():
        return ""
    language = relay.project_line(records, "Language")
    lang = f"- Language: {language}" if language else None
    value = relay.project_line(records, "relay.py")
    relay_py = (pathlib.Path(top) / relay.line_path(value) if value
                else pathlib.Path(relay.__file__).resolve())
    plan = records / "plan.md"
    text = plan.read_text(encoding="utf-8", errors="replace") if plan.is_file() else ""
    coordinator = field(text, "Coordinator")
    m = re.search(r"worktree (.+?), id ", coordinator)
    if m and same(m.group(1), top):
        mode = re.search(r"\bmode (\w+)", coordinator)
        return "\n".join(filter(None, [
            f"relay: you are the relay coordinator; records at {records}. Files beat the compact summary.",
            lang,
            mode and f"- Mode {mode.group(1)}, as Handover records it: a compact is not the user "
                     "speaking, so it neither starts nor ends unattended mode. Carry on from "
                     "Handover › Next when the authorization recorded there covers it.",
            f"- Reread {plan}: Handover (with Next), Now, and both Waiting for the user sections.",
            "- Read plan.md with the Read tool before you edit it (the Edit tool needs a Read first).",
            f"- Run `{relay_py} ready {records}` and act on its Plan warning, if any, "
            "before adding to plan.md.",
        ])) + "\n"
    branch = git(top, "rev-parse", "--abbrev-ref", "HEAD").strip()
    for st in sorted((records / "status").glob("*.md")):
        body = st.read_text(encoding="utf-8", errors="replace")
        if branch and branch != "HEAD" and re.search(rf"^- branch: {re.escape(branch)}\s*$", body, re.M):
            key = st.stem
            return "\n".join(filter(None, [
                f"relay: you are the relay worker for lane {key}; records at {records}. "
                "Files beat the compact summary.",
                lang,
                f"- Reread your brief {records / 'briefs' / (key + '.md')}, your status {st} "
                f"and your report {records / 'reports' / (key + '.md')} (if written).",
            ])) + "\n"
    return ""


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
        # Bytes, not text: a Windows pipe's default encoding cannot hold the user's language line.
        sys.stdout.buffer.write(resume(data.get("cwd") or os.getcwd()).encode("utf-8"))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
