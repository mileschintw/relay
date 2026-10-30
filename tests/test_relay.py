"""Tests for relay.py: python3 -I tests/test_relay.py (Windows: py -3 -I ...)."""
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "plugin" / "tools"))
import relay  # noqa: E402


def git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def sh(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True).stdout.strip()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.records = self.tmp / "records"
        for d in ("status", "briefs", "reports", "pr-bodies"):
            (self.records / d).mkdir(parents=True)
        self.origin = self.tmp / "origin.git"
        self.clone = self.tmp / "clone"
        git("init", "-q", "--bare", "-b", "main", str(self.origin), cwd=self.tmp)
        git("clone", "-q", str(self.origin), str(self.clone), cwd=self.tmp)
        for k, v in (("user.email", "t@example.com"), ("user.name", "t")):
            git("config", k, v, cwd=self.clone)
        (self.clone / "a.txt").write_text("one\n")
        git("add", ".", cwd=self.clone)
        git("commit", "-qm", "init", cwd=self.clone)
        git("push", "-q", "origin", "main", cwd=self.clone)
        git("remote", "set-head", "origin", "main", cwd=self.clone)
        self.fake = self.tmp / "gh.json"
        self.gh({})
        os.environ["RELAY_GH"] = f'"{sys.executable}" "{HERE / "fake_gh.py"}"'
        os.environ["RELAY_FAKE_GH"] = str(self.fake)

    def gh(self, data):
        self.fake.write_text(json.dumps({"repo": "o/r", **data}))

    def branch(self, name, content="two\n", file="a.txt"):
        git("switch", "-q", "-c", name, "main", cwd=self.clone)
        (self.clone / file).write_text(content)
        git("commit", "-qam", name, cwd=self.clone)
        git("push", "-q", "origin", name, cwd=self.clone)
        head = sh("rev-parse", "HEAD", cwd=self.clone)
        git("switch", "-q", "main", cwd=self.clone)
        return head

    def call(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        cwd = os.getcwd()
        os.chdir(self.clone)
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = relay.main(list(argv))
        finally:
            os.chdir(cwd)
        return code, out.getvalue(), err.getvalue()

    def ready(self):
        code, out, err = self.call("ready", str(self.records), "--checkout", str(self.clone))
        self.assertEqual(code, 0, err)
        return out

    def done(self, key, branch, head, body="Closes #{key}\n\nBody.\n"):
        (self.records / "reports" / f"{key}.md").write_text("report")
        (self.records / "pr-bodies" / f"{key}.md").write_text(body.format(key=key))
        code, _, err = self.call("status", str(self.records), key, "--state", "done",
                                 "--doing", "finished", "--branch", branch, "--head", head[:7])
        self.assertEqual(code, 0, err)


class StatusTests(Base):
    def test_writes_and_reads_back(self):
        code, out, _ = self.call("status", str(self.records), "12", "--state", "working",
                                 "--doing", "step 2")
        self.assertEqual(code, 0)
        st = relay.parse_status((self.records / "status" / "12.md").read_text())
        self.assertEqual(st["state"], "working")
        self.assertEqual(st["branch"], "main")
        self.assertRegex(st["head"], r"^[0-9a-f]{7,}$")

    def test_parked_has_no_branch(self):
        self.call("status", str(self.records), "13", "--state", "parked", "--doing", "waits #12")
        st = relay.parse_status((self.records / "status" / "13.md").read_text())
        self.assertEqual((st["branch"], st["head"]), ("none", "none"))

    def test_rejects_line_break_and_bad_head(self):
        code, _, err = self.call("status", str(self.records), "12", "--state", "done",
                                 "--doing", "a\nb")
        self.assertEqual(code, 1)
        code, _, err = self.call("status", str(self.records), "12", "--state", "done",
                                 "--doing", "x", "--head", "zzz")
        self.assertEqual(code, 1)
        self.assertFalse((self.records / "status" / "12.md").exists())


    def test_refuses_records_branch(self):
        code, _, err = self.call("status", str(self.records), "12", "--state", "working",
                                 "--doing", "x", "--branch", "coord")
        self.assertEqual(code, 1)
        self.assertIn("records branch", err)


class ReadyTests(Base):
    def park(self, key, brief):
        (self.records / "briefs" / f"{key}.md").write_text(brief)
        self.call("status", str(self.records), key, "--state", "parked", "--doing", "parked")

    def test_go_when_blockers_closed(self):
        self.gh({"blocked_by": {"13": [12]}, "issues": {"12": ["CLOSED", "COMPLETED"]}})
        self.park("13", "Depends on: #12\n")
        self.assertIn("13: send `GO #13`", self.ready())

    def test_waits_on_open_blocker_and_same_section(self):
        self.gh({"blocked_by": {"13": [12]},
                 "issues": {"12": ["CLOSED", "COMPLETED"], "14": ["OPEN", None]}})
        self.park("13", "Depends on: #12\nWaits for (same section): #14\n")
        out = self.ready()
        self.assertIn("13: parked on #14 open", out)
        self.assertNotIn("Ready for GO", out)

    def test_not_planned_blocker_holds_go(self):
        self.gh({"issues": {"12": ["CLOSED", "NOT_PLANNED"]}})
        self.park("13", "Depends on: #12\n")
        self.assertIn("parked on #12 closed", self.ready())

    def test_ready_for_pr_then_merge(self):
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        self.assertIn("Ready for PR:\n  12: lane-12", self.ready())
        ok = [{"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"}]
        self.gh({"prs": {"lane-12": [{"number": 5, "state": "OPEN", "headRefOid": head,
                                      "mergeable": "MERGEABLE", "statusCheckRollup": ok}]}})
        self.assertIn(f"12: PR #5 --match-head-commit {head}", self.ready())

    def test_closes_lines_match_the_brief(self):
        (self.records / "briefs" / "12.md").write_text("Depends on: none\n- **Closes:** #12 #13\n")
        head = self.branch("lane-12")
        self.done("12", "lane-12", head, body="Closes #12\nCloses #12\nCloses #14\n\nBody.\n")
        out = self.ready()
        self.assertIn("no `Closes #13` line", out)
        self.assertIn("lines [1, 2]: `Closes #12` more than once", out)
        self.assertIn("line 3: `Closes #14`, but the brief's Closes does not list it", out)

    def test_deny_list_reports_lines_only(self):
        (self.records / "deny.txt").write_text("# names\nAcme(?:Corp)?\n")
        (self.records / "project.md").write_text("- **Deny list:** `deny.txt`\n")
        head = self.branch("lane-12")
        self.done("12", "lane-12", head, body="Closes #12\n\nWorked on AcmeCorp data.\nacmeish\n")
        out = self.ready()
        self.assertIn("PR body lines [3]: a deny-list name", out)
        self.assertNotIn("AcmeCorp", out)
        (self.records / "project.md").write_text("- **Deny list:** none\n")
        self.assertNotIn("deny-list", self.ready())

    def test_deny_list_none_and_trailing_period(self):
        project = self.records / "project.md"
        for value in ("none.", "none", '"none"', "`none`", "`none`.", "None.", '"none."'):
            project.write_text(f"- **Deny list:** {value}\n")
            self.assertEqual(relay.deny_patterns(self.records), [], value)
        (self.records / "deny.txt").write_text("Acme\n")
        for value in ("deny.txt", "deny.txt.", "`deny.txt`.", '"deny.txt".'):
            project.write_text(f"- **Deny list:** {value}\n")
            self.assertEqual(relay.deny_patterns(self.records), ["Acme"], value)
        for value in ("missing.txt.", "..", "`deny.txt` (see notes)"):
            project.write_text(f"- **Deny list:** {value}\n")
            with self.assertRaisesRegex(FileNotFoundError, "is not a file"):
                relay.deny_patterns(self.records)
        project.write_text("- **Deny list:** none.\n")
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        self.assertIn("Ready for PR:\n  12: lane-12", self.ready())

    def test_closed_unmerged_pr(self):
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        self.gh({"prs": {"lane-12": [{"number": 5, "state": "CLOSED", "headRefOid": head}]}})
        out = self.ready()
        self.assertIn("12: PR #5 closed without merging", out)
        self.assertNotIn("Ready for PR", out)

    def test_pending_checks_and_no_checks_wait(self):
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        pending = [{"name": "ci", "status": "IN_PROGRESS", "conclusion": None}]
        self.gh({"prs": {"lane-12": [{"number": 5, "state": "OPEN", "headRefOid": head,
                                      "mergeable": "MERGEABLE", "statusCheckRollup": pending}]}})
        self.assertIn("PR #5 checks pending", self.ready())
        self.gh({"prs": {"lane-12": [{"number": 5, "state": "OPEN", "headRefOid": head,
                                      "mergeable": "MERGEABLE", "statusCheckRollup": []}]}})
        self.assertIn("PR #5 no checks reported", self.ready())

    def test_stale_status_head(self):
        self.branch("lane-12")
        self.done("12", "lane-12", "abcdef1234")
        self.assertIn("is not the pushed head", self.ready())

    def test_merge_conflict_waits(self):
        head = self.branch("lane-12", "lane\n")
        (self.clone / "a.txt").write_text("main moved\n")
        git("commit", "-qam", "main", cwd=self.clone)
        git("push", "-q", "origin", "main", cwd=self.clone)
        self.done("12", "lane-12", head)
        self.assertIn("12: conflicts with the default branch: a.txt", self.ready())

    def test_pr_body_checks(self):
        head = self.branch("lane-12")
        self.done("12", "lane-12", head, body="# Title\n\nThis fixes #9.\n")
        out = self.ready()
        self.assertIn("title line", out)
        self.assertIn("no `Closes #N` line", out)
        self.assertIn("line 3: closing keyword", out)

    def test_done_without_report(self):
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        (self.records / "reports" / "12.md").unlink()
        self.assertIn("12: done with no report file", self.ready())

    def test_plan_limit(self):
        (self.records / "plan.md").write_text("x\n" * 201)
        self.assertIn("plan.md has 201 lines", self.ready())

    def test_invalid_utf8_in_plan_warns(self):
        (self.records / "plan.md").write_bytes(b"# Plan\n\nbad \xff byte\n" + b"x\n" * 201)
        out = self.ready()
        self.assertIn("Records:\n  plan.md line 3: invalid UTF-8", out)
        self.assertIn("plan.md has 204 lines", out)

    def test_control_characters_named_by_file_and_line(self):
        (self.records / "plan.md").write_bytes(b"# Plan\r\nrelease\r-0.3.0\n\tok\r\n")
        (self.records / "briefs" / "4.md").write_text("Depends on: none\nbell\x07\n")
        (self.records / "pr-bodies" / "4.md").write_text("Closes #4\n\nesc\x1b[0m\n")
        out = self.ready()
        self.assertIn("plan.md line 2: control character U+000D", out)
        self.assertIn("briefs/4.md line 2: control character U+0007", out)
        self.assertIn("pr-bodies/4.md line 3: control character U+001B", out)
        self.assertNotIn("plan.md line 1", out)
        self.assertNotIn("plan.md line 3", out)

    def test_invalid_utf8_in_brief_and_pr_body_warns(self):
        self.park("13", "Depends on: none\n")
        (self.records / "briefs" / "13.md").write_bytes(b"Depends on: none\n\xc3(\n")
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        (self.records / "pr-bodies" / "12.md").write_bytes(b"Closes #12\n\n\xff\n")
        out = self.ready()
        self.assertIn("briefs/13.md line 2: invalid UTF-8 (byte 0xc3)", out)
        self.assertIn("pr-bodies/12.md line 3: invalid UTF-8 (byte 0xff)", out)

    def test_clean_records_print_no_records_section(self):
        (self.records / "plan.md").write_text("# Plan\n\tindented\n")
        self.assertNotIn("Records:", self.ready())

    def test_fresh_records_and_brief_without_status(self):
        for d in ("status", "reports", "pr-bodies"):
            (self.records / d).rmdir()
        out = self.ready()
        self.assertIn("Lanes:\n  (none)\nNothing to do.", out)
        (self.records / "briefs" / "_template.md").write_text("form")
        (self.records / "briefs" / "4.md").write_text("Depends on: none\n")
        out = self.ready()
        self.assertIn("4: a brief but no status file", out)
        self.assertNotIn("_template", out)

    def test_blocked_lane_waits(self):
        self.call("status", str(self.records), "12", "--state", "blocked",
                  "--doing", "needs a decision on X")
        self.assertIn("Waiting:\n  12: blocked: needs a decision on X", self.ready())

    def test_merged(self):
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        self.gh({"prs": {"lane-12": [{"number": 5, "state": "MERGED", "headRefOid": head}]}})
        self.assertIn("Merged:\n  12: PR #5", self.ready())

    def failed_check(self, head, job, **data):
        url = f"https://github.com/o/r/actions/runs/1/job/{job}"
        rollup = [{"name": "ci", "status": "COMPLETED", "conclusion": "FAILURE", "detailsUrl": url}]
        self.gh({"prs": {"lane-12": [{"number": 5, "state": "OPEN", "headRefOid": head,
                                      "mergeable": "MERGEABLE", "statusCheckRollup": rollup}]},
                 **data})
        return self.ready()

    def test_billing_failure_is_not_a_failed_check(self):
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        out = self.failed_check(head, 77, jobs={"77": {"steps": []}})
        self.assertIn("Waiting:\n  12: PR #5 checks could not run (billing): ci", out)
        self.assertNotIn("check failed", out)
        out = self.failed_check(head, 78, jobs={"78": {"steps": [{"name": "Set up job"}]}},
                                annotations={"78": [{"message": "The job was not started because "
                                                     "your spending limit needs to be increased."}]})
        self.assertIn("checks could not run (billing): ci", out)

    def test_failed_test_is_a_failed_check(self):
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        out = self.failed_check(head, 79, annotations={"79": [{"message": "Process exited with 1"}]})
        self.assertIn("PR #5 check failed: ci", out)
        self.assertNotIn("billing", out)


class LocalcheckTests(Base):
    def project(self, text):
        (self.records / "project.md").write_text(text)

    def py(self, code):
        return f'`"{sys.executable}" -c "{code}"`'

    def lane(self):
        """Lane 12 adds b.txt; main then moves a.txt. Returns (lane head, main head)."""
        git("switch", "-q", "-c", "lane-12", "main", cwd=self.clone)
        (self.clone / "b.txt").write_text("b\n")
        git("add", "b.txt", cwd=self.clone)
        git("commit", "-qm", "lane-12", cwd=self.clone)
        git("push", "-q", "origin", "lane-12", cwd=self.clone)
        head = sh("rev-parse", "HEAD", cwd=self.clone)
        git("switch", "-q", "main", cwd=self.clone)
        (self.clone / "a.txt").write_text("main moved\n")
        git("commit", "-qam", "main", cwd=self.clone)
        git("push", "-q", "origin", "main", cwd=self.clone)
        self.done("12", "lane-12", head)
        return head, sh("rev-parse", "HEAD", cwd=self.clone)

    def localcheck(self, *extra):
        return self.call("localcheck", str(self.records), "12", "--checkout", str(self.clone), *extra)

    def worktrees(self):
        return sh("worktree", "list", cwd=self.clone).splitlines()

    def test_runs_local_checks_on_the_merge_and_cleans_up(self):
        head, base = self.lane()
        check = "import pathlib; print(pathlib.Path('a.txt').read_text().strip(), pathlib.Path('b.txt').exists())"
        self.project(f"- **Checks before done:** `unused`\n- **Local checks:** {self.py(check)}\n")
        code, out, err = self.localcheck()
        self.assertEqual(code, 0, out + err)
        self.assertIn(f"head {head}", out)
        self.assertIn(f"base {base}", out)
        self.assertIn("main moved True", out)
        self.assertIn("passed", out)
        self.assertEqual(len(self.worktrees()), 1)

    def test_falls_back_to_checks_before_done(self):
        self.lane()
        self.project(f"- **Checks before done:** {self.py('print(42)')}.\n")
        code, out, err = self.localcheck()
        self.assertEqual(code, 0, out + err)
        self.assertIn("42", out)

    def test_no_command_line_is_a_clear_error(self):
        self.lane()
        self.project("- **Repo:** o/r\n")
        code, out, err = self.localcheck()
        self.assertEqual(code, 1)
        self.assertIn("Local checks", err)
        self.assertIn("Checks before done", err)

    def test_failing_check_still_removes_the_worktree(self):
        self.lane()
        self.project(f"- **Local checks:** {self.py('import sys; sys.exit(3)')}; {self.py('print(7)')}\n")
        code, out, err = self.localcheck()
        self.assertEqual(code, 1)
        self.assertIn("failed (exit 3)", out)
        self.assertIn("7", out)
        self.assertEqual(len(self.worktrees()), 1)

    def test_comment_posts_the_output(self):
        head, _ = self.lane()
        self.project(f"- **Local checks:** {self.py('print(5)')}\n")
        code, out, err = self.localcheck("--comment", "5")
        self.assertEqual(code, 0, out + err)
        posted = pathlib.Path(str(self.fake) + ".comments").read_text(encoding="utf-8")
        self.assertTrue(posted.startswith("#5\n"))
        self.assertIn(f"head {head}", posted)

    def test_failed_merge_fails(self):
        self.lane()
        git("switch", "-q", "lane-12", cwd=self.clone)
        (self.clone / "a.txt").write_text("lane moved\n")
        git("commit", "-qam", "conflict", cwd=self.clone)
        git("push", "-q", "origin", "lane-12", cwd=self.clone)
        git("switch", "-q", "main", cwd=self.clone)
        self.project(f"- **Local checks:** {self.py('print(5)')}\n")
        code, out, err = self.localcheck()
        self.assertEqual(code, 1)
        self.assertIn("merge of origin/main failed", out)
        self.assertNotIn("$ ", out)
        self.assertEqual(len(self.worktrees()), 1)

    def test_none_falls_back_and_main_checkout_only_is_named(self):
        self.lane()
        self.project(f"- **Checks before done:** {self.py('print(6)')}; `e2e` main checkout only\n"
                     "- **Local checks:** none\n")
        code, out, err = self.localcheck()
        self.assertEqual(code, 0, out + err)
        self.assertIn("not run (main checkout only): e2e", out)
        self.assertIn("result: passed, 1 not run", out)

    def test_failed_comment_is_an_error(self):
        self.lane()
        self.project(f"- **Local checks:** {self.py('print(5)')}\n")
        os.environ["RELAY_GH"] = f'"{sys.executable}" "{HERE / "no_such_gh.py"}"'
        code, out, err = self.localcheck("--comment", "5")
        self.assertEqual(code, 1)
        self.assertIn("could not post on PR #5", err)

    def test_command_parsing(self):
        line = ("`python3 -I t.py` (Windows: `py -3 -I t.py`); `claude plugin validate .`; "
                "`npm run e2e` main checkout only.")
        self.assertEqual(relay.check_commands(line, windows=False),
                         (["python3 -I t.py", "claude plugin validate ."], ["npm run e2e"]))
        self.assertEqual(relay.check_commands(line, windows=True)[0],
                         ["py -3 -I t.py", "claude plugin validate ."])


class ParentTests(Base):
    """An open issue with sub-issues is a parent: listed under Parents, never a lane."""

    def setUp(self):
        super().setUp()
        for key in ("1", "2", "3", "4"):
            (self.records / "briefs" / f"{key}.md").write_text("Depends on: none\n")
            self.call("status", str(self.records), key, "--state", "parked", "--doing", "parked")

    def parent_with_children(self, *children, **extra):
        """Open issue 1 with sub-issues 2, 3 and 4 in the given [state, reason] pairs."""
        issues = {"1": ["OPEN", None]}
        issues.update({str(n): c for n, c in enumerate(children, 2)})
        self.gh({"issues": issues, "children": {"1": ["2", "3", "4"]}, **extra})

    def test_only_children_on_the_frontier(self):
        self.parent_with_children(*[["OPEN", None]] * 3)
        out = self.ready()
        for key in ("2", "3", "4"):
            self.assertIn(f"{key}: send `GO #{key}`", out)
        self.assertNotIn("GO #1", out)
        self.assertIn("1: issue #1 is a parent, never a lane", out)

    def test_parents_listed_with_child_counts(self):
        self.parent_with_children(["OPEN", None], ["CLOSED", "COMPLETED"], ["OPEN", None])
        self.assertIn("Parents:\n  #1 issue 1: 2 open, 1 closed children\n", self.ready())
        self.parent_with_children(*[["CLOSED", "COMPLETED"]] * 3)
        self.assertIn("#1 issue 1: 0 open, 3 closed children; every child closed as completed",
                      self.ready())
        self.parent_with_children(["CLOSED", "COMPLETED"], ["CLOSED", "NOT_PLANNED"],
                                  ["CLOSED", "COMPLETED"])
        self.assertIn("0 open, 3 closed children; every child closed, 1 not as completed",
                      self.ready())

    def test_working_lane_on_a_parent_is_inconsistent(self):
        self.call("status", str(self.records), "1", "--state", "working", "--doing", "x",
                  "--branch", "lane-1", "--head", "abcdef1")
        self.parent_with_children(*[["OPEN", None]] * 3)
        self.assertIn("1: issue #1 is a parent, never a lane", self.ready())

    def test_failed_lookup_holds_go(self):
        self.parent_with_children(*[["OPEN", None]] * 3, broken=["/sub_issues"])
        out = self.ready()
        self.assertIn("Parents:\n  lookup failed:", out)
        self.assertIn("2: parked; no GO while the Parents lookup fails", out)
        self.assertNotIn("Ready for GO", out)


FILES_BODY = """## Problem

- not/a/file.py (a bullet outside the section)

## Files

- plugin/skills/coordinate/app-limits.md (the two rules; its intro line, which says `SKILL.md`)

A prose line between bullets, as in #8's body.
- New: `plugin/tools/roadmap.py` (strategy validation only)
* docs/plain.md
- new: `tests/a b.md`

```
## not a heading inside a fence
- fenced/not-a-file.md
```

## Acceptance

- [ ] after/the/section.md
"""


class FilesTests(unittest.TestCase):
    def test_parses_paths_new_marks_and_scopes(self):
        self.assertEqual(relay.parse_files(FILES_BODY), [
            {"path": "plugin/skills/coordinate/app-limits.md", "new": False,
             "scope": "the two rules; its intro line, which says `SKILL.md`"},
            {"path": "plugin/tools/roadmap.py", "new": True, "scope": "strategy validation only"},
            {"path": "docs/plain.md", "new": False, "scope": ""},
            {"path": "tests/a b.md", "new": True, "scope": ""},
        ])

    def test_no_section_is_none_and_empty_section_is_empty(self):
        self.assertIsNone(relay.parse_files("## Problem\n\n- a.py\n"))
        self.assertIsNone(relay.parse_files(None))
        self.assertEqual(relay.parse_files("## Files\n\nNone yet.\n## Next\n- a.py\n"), [])


class RoadmapTests(Base):
    def roadmap(self):
        code, out, err = self.call("roadmap", "--repo", "o/r")
        self.assertEqual(code, 0, err)
        return out

    def test_rows_with_blocked_by_and_files(self):
        self.gh({"issues": {"2": ["OPEN", None], "5": ["OPEN", None], "6": ["OPEN", None],
                            "7": ["CLOSED", "COMPLETED"], "1": ["CLOSED", "COMPLETED"],
                            "8": ["OPEN", None]},
                 "blocked_by": {"2": [1, 4]},
                 "bodies": {"2": FILES_BODY, "5": "## Problem\n\nNo files here.\n",
                            "8": "## Files\n\n- a|b.py\n",
                            "6": "A parent: its children are the lanes.\n"},
                 "children": {"6": ["7"]}})
        out = self.roadmap()
        self.assertIn("| #8 issue 8 | none | a\\|b.py |", out)
        self.assertIn("| #2 issue 2 | #1 (closed), #4 | plugin/skills/coordinate/app-limits.md (the two "
                      "rules; its intro line, which says `SKILL.md`); New: plugin/tools/roadmap.py "
                      "(strategy validation only); docs/plain.md; New: tests/a b.md |",
                      out)
        self.assertIn("| #5 issue 5 | none | **missing: no `## Files` section** |", out)
        self.assertIn("| #6 issue 6 | none | parent |", out)
        self.assertNotIn("#7", out)
        self.assertNotIn("not/a/file.py", out)
        self.assertIn("Missing `## Files`: #5", out)

    def test_failed_lookup_exits_1(self):
        self.gh({"issues": {"2": ["OPEN", None]}, "broken": ["/dependencies/"]})
        code, _, err = self.call("roadmap", "--repo", "o/r")
        self.assertEqual(code, 1)
        self.assertIn("broken", err)


if __name__ == "__main__":
    unittest.main()
