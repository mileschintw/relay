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
from unittest import mock

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
        (self.records / ".gitattributes").write_text("* text eol=lf\n")
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

    def test_invalid_utf8_status_is_could_not_parse(self):
        self.call("status", str(self.records), "13", "--state", "working", "--doing", "x")
        (self.records / "status" / "12.md").write_bytes(b"- state: working\n- doing: \xff\n")
        out = self.ready()
        self.assertIn("Could not parse:\n  12: invalid UTF-8", out)
        self.assertIn("  13: working", out)

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

    def test_no_ci_configured(self):
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        prs = {"lane-12": [{"number": 5, "state": "OPEN", "headRefOid": head,
                            "mergeable": "MERGEABLE", "statusCheckRollup": []}]}
        self.gh({"prs": prs, "workflows": 0})
        out = self.ready()
        self.assertIn("12: PR #5 no CI configured", out)
        self.assertNotIn("no checks reported", out)
        self.assertNotIn("checks pending", out)
        self.gh({"prs": prs, "workflows": 1})
        self.assertIn("PR #5 no checks reported", self.ready())
        self.gh({"prs": prs, "workflows": 0, "broken": ["/actions/workflows"]})
        self.assertIn("PR #5 no checks reported", self.ready())

    def test_ci_outside_actions(self):
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        prs = {"lane-12": [{"number": 5, "state": "OPEN", "headRefOid": head,
                            "mergeable": "MERGEABLE", "statusCheckRollup": []}]}
        self.gh({"prs": prs, "workflows": 0, "head_statuses": 1})
        self.assertIn("PR #5 no checks reported", self.ready())
        self.gh({"prs": prs, "workflows": 0, "head_check_runs": 1})
        self.assertIn("PR #5 no checks reported", self.ready())
        self.gh({"prs": prs, "workflows": 0})
        self.assertIn("PR #5 no CI configured", self.ready())
        self.gh({"prs": prs, "workflows": 0, "broken": ["/status"]})
        self.assertIn("PR #5 no checks reported", self.ready())
        self.gh({"prs": prs, "workflows": 0, "broken": ["/check-runs"]})
        self.assertIn("PR #5 no checks reported", self.ready())

    def test_workflows_skip_head_lookup(self):
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        prs = {"lane-12": [{"number": 5, "state": "OPEN", "headRefOid": head,
                            "mergeable": "MERGEABLE", "statusCheckRollup": []}]}
        self.gh({"prs": prs, "workflows": 1})
        self.assertIn("PR #5 no checks reported", self.ready())
        calls = pathlib.Path(str(self.fake) + ".calls").read_text(encoding="utf-8")
        self.assertIn("/actions/workflows", calls)
        self.assertNotIn("commits/HEAD", calls)

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

    def relay_py_line(self, value):
        (self.records / "project.md").write_text(f"# Project\n\n- **relay.py:** {value}\n")

    def advance_origin(self, n):
        for i in range(n):
            (self.clone / "a.txt").write_text(f"advance {i}\n")
            git("commit", "-qam", f"advance {i}", cwd=self.clone)
        git("push", "-q", "origin", "main", cwd=self.clone)

    def test_relay_py_checkout_behind_warns_with_count(self):
        main = self.tmp / "main"
        git("clone", "-q", str(self.origin), str(main), cwd=self.tmp)
        (main / "plugin" / "tools").mkdir(parents=True)
        self.relay_py_line(f"`{main}/plugin/tools/relay.py` (the main checkout)")
        self.assertNotIn("behind", self.ready())
        self.advance_origin(2)
        out = self.ready()  # fetches the relay.py checkout, though --checkout is the other clone
        self.assertEqual(out.count("behind"), 1)
        self.assertIn(f"relay.py:\n  {main.resolve().as_posix()} is 2 commits behind origin/main:"
                      f" git -C {main.resolve().as_posix()} merge --ff-only origin/main", out)

    def test_relay_py_relative_path_resolves_against_the_checkout(self):
        (self.clone / "plugin" / "tools").mkdir(parents=True)
        self.relay_py_line("plugin/tools/relay.py")
        self.advance_origin(1)
        git("reset", "-q", "--hard", "HEAD~1", cwd=self.clone)
        self.assertIn("is 1 commit behind origin/main", self.ready())

    def test_relay_py_on_another_branch_switches_first(self):
        main = self.tmp / "with space (x86)"
        git("clone", "-q", str(self.origin), str(main), cwd=self.tmp)
        git("switch", "-q", "-c", "feature", cwd=main)
        self.relay_py_line(f"{main}/relay.py (the main checkout; see `origin/main`)")
        self.advance_origin(1)
        where = main.resolve().as_posix()
        self.assertIn(f'1 commit behind origin/main: git -C "{where}" switch main && '
                      f'git -C "{where}" merge --ff-only origin/main', self.ready())

    def test_line_path(self):
        self.assertEqual(relay.line_path("D:/r/relay.py (note; `origin/main`)"), "D:/r/relay.py")
        self.assertEqual(relay.line_path("`C:/a b/relay.py` (note)"), "C:/a b/relay.py")
        self.assertEqual(relay.line_path("C:/Program Files (x86)/relay.py"),
                         "C:/Program Files (x86)/relay.py")

    def test_no_relay_py_line_or_path_outside_a_checkout_does_not_warn(self):
        self.advance_origin(1)
        git("reset", "-q", "--hard", "HEAD~1", cwd=self.clone)
        self.assertNotIn("relay.py:", self.ready())
        self.relay_py_line("none")
        self.assertNotIn("relay.py:", self.ready())
        (self.tmp / "outside").mkdir()
        self.relay_py_line(f"{self.tmp / 'outside'}/relay.py")
        self.assertNotIn("relay.py:", self.ready())
        self.relay_py_line(f"{self.clone}/no/such/dir/relay.py")
        self.assertNotIn("relay.py:", self.ready())

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

    def test_missing_gitattributes_warns_with_fix(self):
        (self.records / ".gitattributes").unlink()
        out = self.ready()
        self.assertIn("Records:\n  .gitattributes missing", out)
        self.assertIn("templates/gitattributes", out)
        self.assertIn("`git add .gitattributes`, `git add --renormalize .`", out)
        self.assertIn("git ls-files --eol", out)
        self.assertEqual(out.count(".gitattributes missing"), 1)

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

    def test_invalid_utf8_status_is_a_one_line_error(self):
        self.lane()
        self.project(f"- **Local checks:** {self.py('print(5)')}\n")
        (self.records / "status" / "12.md").write_bytes(b"- state: done\n- doing: \xff\n")
        code, out, err = self.localcheck()
        self.assertEqual(code, 1)
        self.assertEqual(len(err.strip().splitlines()), 1, err)
        self.assertIn("invalid UTF-8", err)

    def test_command_parsing(self):
        line = ("`python3 -I t.py` (Windows: `py -3 -I t.py`); `claude plugin validate .`; "
                "`npm run e2e` main checkout only.")
        self.assertEqual(relay.check_commands(line, windows=False),
                         (["python3 -I t.py", "claude plugin validate ."], ["npm run e2e"]))
        self.assertEqual(relay.check_commands(line, windows=True)[0],
                         ["py -3 -I t.py", "claude plugin validate ."])


class WaitchecksTests(Base):
    """waitchecks polls PR #5 for its first check on a front-loaded schedule, with time faked."""

    QUEUED = [{"name": "test", "status": "QUEUED", "conclusion": ""}]
    FAILED = [{"name": "test", "status": "COMPLETED", "conclusion": "FAILURE"}]

    def waitchecks(self, after=1, watch=(0, "all checks passed"), project=None, rollup=None,
                   repo=("--repo", "o/r"), **data):
        if project is not None:
            (self.records / "project.md").write_text(project)
        self.gh({"pr_checks": {"5": {"after": after, "rollup": rollup or self.QUEUED}},
                 "watch": {"5": list(watch)}, **data})
        pathlib.Path(str(self.fake) + ".calls").unlink(missing_ok=True)
        now, self.polls = [0.0], []
        real_gh = relay.gh

        def poll(*args, **kw):
            if args[:2] == ("pr", "view"):
                self.polls.append(now[0])
            return real_gh(*args, **kw)

        def sleep(s):
            now[0] += s
        with mock.patch.object(relay.time, "sleep", sleep), \
                mock.patch.object(relay.time, "monotonic", lambda: now[0]), \
                mock.patch.object(relay, "gh", poll):
            return self.call("waitchecks", str(self.records), "5", *repo)

    def watched(self):
        calls = pathlib.Path(str(self.fake) + ".calls").read_text().splitlines()
        return [c for c in calls if c.startswith("pr checks 5")]

    def test_checks_on_first_poll_are_watched_with_no_wait(self):
        code, out, err = self.waitchecks()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.polls, [0.0])
        self.assertEqual(self.watched(), ["pr checks 5 --repo o/r --watch"])
        self.assertIn("all checks passed", out)

    def test_checks_on_a_later_poll_are_watched_to_their_result(self):
        code, out, err = self.waitchecks(after=2)
        self.assertEqual((code, self.polls), (0, [0.0, 60.0]), err)
        code, out, err = self.waitchecks(after=4, watch=(1, "X test fail"), rollup=self.FAILED)
        self.assertEqual(code, 1, err)
        self.assertEqual(self.polls[:4], [0.0, 60.0, 180.0, 360.0])
        self.assertIn("X test fail", out)

    def test_a_watch_error_with_no_failed_check_is_a_lookup_failure(self):
        code, out, err = self.waitchecks(watch=(1, "HTTP 502"))
        self.assertEqual(code, 4, err)
        self.assertIn("HTTP 502", out)
        self.assertIn("no failed check (checks pending)", err)

    def test_no_checks_by_the_last_poll(self):
        code, out, err = self.waitchecks(after=99)
        self.assertEqual(code, 3, err)
        self.assertEqual(self.polls, [0.0, 60.0, 180.0, 360.0])
        self.assertEqual(self.watched(), [])
        self.assertIn("no checks appeared on PR #5 within 6 minutes", out)
        self.assertNotIn("no CI configured", out)
        code, out, err = self.waitchecks(after=99, workflows=0)
        self.assertEqual(code, 3, err)
        self.assertIn("no CI configured", out)

    def test_ci_start_wait_stretches_the_polls(self):
        project = "- **Repo:** o/r\n- **CI start wait:** 12 minutes.\n"
        code, out, err = self.waitchecks(after=99, project=project)
        self.assertEqual(code, 3, err)
        self.assertEqual(self.polls, [0.0, 120.0, 360.0, 720.0])
        self.assertIn("within 12 minutes", out)
        code, _, err = self.waitchecks(project="- **CI start wait:** soon\n")
        self.assertEqual(code, 2)
        self.assertIn("CI start wait", err)

    def test_failed_lookups_retry_and_a_failed_last_poll_is_its_own_exit(self):
        code, out, err = self.waitchecks(after=99, broken=["statusCheckRollup"])
        self.assertEqual(code, 4, err)
        self.assertEqual(len(self.polls), 4)
        self.assertIn("lookup failed", err)
        code, out, err = self.waitchecks(repo=(), broken=["nameWithOwner"])
        self.assertEqual((code, self.polls), (4, []), err)

    def test_wait_checks_takes_a_schedule(self):
        self.gh({"pr_checks": {"5": {"after": 3, "rollup": self.QUEUED}}})
        with mock.patch.object(relay.time, "sleep", lambda s: None), redirect_stdout(io.StringIO()):
            self.assertEqual(relay.wait_checks(5, "o/r", [0]), relay.NO_CHECKS)
            self.assertEqual(relay.wait_checks(5, "o/r", [0, 1]), 0)
        self.assertEqual(relay.poll_schedule(10), [0, 100, 300, 600])
        self.assertEqual(relay.ci_start_schedule(self.records), [0, 60, 180, 360])


class MergeTests(Base):
    """merge takes lanes 12 (PR #5) and 13 (PR #6) from Ready to merge, with time faked."""

    OK = [{"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"}]

    def setUp(self):
        super().setUp()
        self.heads = {}
        for key, pr in (("12", 5), ("13", 6)):
            head = self.branch(f"lane-{key}", content=f"{key}\n")
            self.done(key, f"lane-{key}", head)
            self.heads[key] = (pr, head)

    def merge(self, *keys, view=None, sleep=lambda s: None, **data):
        prs = {f"lane-{k}": [{"number": pr, "state": "OPEN", "headRefOid": head,
                              "mergeable": "MERGEABLE", "statusCheckRollup": self.OK}]
               for k, (pr, head) in self.heads.items()}
        pr_view = {str(pr): {"headRefOid": head, "mergeStateStatus": "CLEAN", "baseRefName": "main",
                             "mergedAt": "2026-10-31T07:00:00Z", "mergeCommit": {"oid": f"m{pr}" * 8},
                             **(view or {}).get(str(pr), {})}
                   for pr, head in self.heads.values()}
        self.gh({"prs": prs, "pr_view": pr_view,
                 "pr_checks": {str(pr): {"rollup": self.OK} for pr, _ in self.heads.values()},
                 **data})
        pathlib.Path(str(self.fake) + ".calls").unlink(missing_ok=True)
        with mock.patch.object(relay.time, "sleep", sleep):
            return self.call("merge", str(self.records), *keys, "--repo", "o/r")

    def merges(self):
        path = pathlib.Path(str(self.fake) + ".calls")
        calls = path.read_text().splitlines() if path.exists() else []
        return [c for c in calls if c.startswith("pr merge")]

    def test_two_lanes_merge_in_order_with_match_head_commit(self):
        run = {"databaseId": 9, "status": "in_progress", "conclusion": "",
               "url": "https://github.com/o/r/actions/runs/9", "headSha": "m6" * 8}
        code, out, err = self.merge("13", "12", runs=[run])
        self.assertEqual(code, 0, err)
        self.assertEqual(self.merges(), [
            f"pr merge 6 --repo o/r --merge --match-head-commit {self.heads['13'][1]}",
            f"pr merge 5 --repo o/r --merge --match-head-commit {self.heads['12'][1]}"])
        self.assertIn("13: merged PR #6 at 2026-10-31T07:00:00Z", out)
        self.assertIn("12: merged PR #5 at 2026-10-31T07:00:00Z", out)
        self.assertIn("main push run for m5m5m5m5: in_progress https://github.com/o/r/actions/runs/9", out)
        calls = pathlib.Path(str(self.fake) + ".calls").read_text()
        self.assertIn("run list --repo o/r --branch main --event push --commit " + "m5" * 8, calls)

    def test_no_push_run_yet_is_said(self):
        code, out, err = self.merge("12")
        self.assertEqual(code, 0, err)
        self.assertIn("no push run on main for m5m5m5m5 yet", out)

    def assert_stopped(self, code, err, *words):
        self.assertEqual(code, 1)
        self.assertEqual(self.merges(), [])
        line = [l for l in err.splitlines() if l.startswith("12: ")]
        self.assertEqual(len(line), 1, err)
        for w in words:
            self.assertIn(w, line[0])

    def test_moved_head_stops_before_any_merge(self):
        code, out, err = self.merge("12", "13", view={"5": {"headRefOid": "f" * 40}})
        self.assert_stopped(code, err, "PR #5", "head ffffffffffff", "not")

    def test_checks_are_not_waited_for_again(self):
        # Ready to merge already needs every check passed: no poll, no watch, no CI start wait
        (self.records / "project.md").write_text("- **CI start wait:** soon\n", encoding="utf-8")
        sleeps = []
        code, out, err = self.merge("12", "13", sleep=sleeps.append)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.merges()), 2)
        calls = pathlib.Path(str(self.fake) + ".calls").read_text().splitlines()
        self.assertEqual([c for c in calls if "--watch" in c or
                          c.startswith("pr view") and "statusCheckRollup" in c], [])
        self.assertEqual([s for s in sleeps if s], list(relay.RUN_WAITS[1:]))

    def test_state_not_clean_stops_before_any_merge(self):
        code, out, err = self.merge("12", "13", view={"5": {"mergeStateStatus": "BLOCKED"}})
        self.assert_stopped(code, err, "PR #5", "BLOCKED", "CLEAN")

    def test_unknown_state_is_retried(self):
        calls = iter(["UNKNOWN", "UNKNOWN", "CLEAN"])
        real_gh = relay.gh

        def gh(*args, **kw):
            out = real_gh(*args, **kw)
            if args[:2] == ("pr", "view") and "mergeStateStatus" in args[-1]:
                out["mergeStateStatus"] = next(calls)
            return out
        with mock.patch.object(relay, "gh", gh):
            code, out, err = self.merge("12")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.merges()), 1)

    def test_unknown_state_after_every_retry_stops(self):
        sleeps = []
        code, out, err = self.merge("12", view={"5": {"mergeStateStatus": "UNKNOWN"}},
                                    sleep=sleeps.append)
        self.assert_stopped(code, err, "PR #5", "UNKNOWN, not CLEAN")
        self.assertEqual([s for s in sleeps if s], list(relay.STATE_RETRIES))

    def test_merge_time_lookup_failure_still_counts_as_merged(self):
        real_gh = relay.gh

        def gh(*args, **kw):
            if "mergedAt,mergeCommit" in args:
                raise RuntimeError("HTTP 502")
            return real_gh(*args, **kw)
        with mock.patch.object(relay, "gh", gh):
            code, out, err = self.merge("12", "13")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.merges()), 2)
        self.assertIn("12: merged PR #5; merge time lookup failed: HTTP 502", out)
        self.assertNotIn("push run", out)

    def test_a_key_not_ready_to_merge_is_refused_before_any_merge(self):
        self.call("status", str(self.records), "14", "--state", "working", "--doing", "x")
        code, out, err = self.merge("12", "14")
        self.assertEqual(code, 1)
        self.assertEqual(self.merges(), [])
        self.assertIn("14: not under Ready to merge (state working)", err)
        code, out, err = self.merge("12", "15")
        self.assertIn("15: not under Ready to merge (no status file)", err)
        code, out, err = self.merge("12", "13", pr_checks={},
                                    prs={"lane-12": [], "lane-13": []})
        self.assertIn("12: not under Ready to merge (Ready for PR: lane-12 @ ", err)
        self.assertEqual(self.merges(), [])
        code, out, err = self.merge("12", "13", "12")
        self.assertEqual((code, self.merges()), (1, []))
        self.assertIn("12: given more than once; nothing merged", err)

    def test_failed_merge_stops_the_rest(self):
        code, out, err = self.merge("12", "13", merge_fail={"5": "Head branch was modified"})
        self.assertEqual(code, 1)
        self.assertEqual(len(self.merges()), 1)
        self.assertIn("12: gh pr merge 5 failed: ", err)
        self.assertIn("Head branch was modified", err)


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

    def test_indented_heading_ends_section_and_checkbox_is_dropped(self):
        self.assertEqual(relay.parse_files(" ## Files:\n- [ ] a.py\n  ## Next\n- b.py\n"),
                         [{"path": "a.py", "new": False, "scope": ""}])

    def test_nested_bullets_skipped_subheading_kept_and_scope_parens_balanced(self):
        body = "## Files\n- a.py (a) and (b)\n  - add foo\n### Tests\n- c.py (x (y))\n"
        self.assertEqual(relay.parse_files(body), [
            {"path": "a.py", "new": False, "scope": "(a) and (b)"},
            {"path": "c.py", "new": False, "scope": "x (y)"},
        ])

    def test_indented_list_is_top_level_from_its_first_bullet(self):
        body = "## Files\n  - a.py\n    - a note\n  - b.py\n"
        self.assertEqual([f["path"] for f in relay.parse_files(body)], ["a.py", "b.py"])


class RoadmapTests(Base):
    def roadmap(self):
        code, out, err = self.call("roadmap", "--repo", "o/r")
        self.assertEqual(code, 0, err)
        return out

    def test_rows_with_blocked_by_and_files(self):
        self.gh({"issues": {"2": ["OPEN", None], "5": ["OPEN", None], "6": ["OPEN", None],
                            "7": ["CLOSED", "COMPLETED"], "1": ["CLOSED", "COMPLETED"],
                            "8": ["OPEN", None], "9": ["OPEN", None]},
                 "blocked_by": {"2": [1, 4]},
                 "bodies": {"2": FILES_BODY, "5": "## Problem\n\nNo files here.\n",
                            "8": "## Files\n\n- a|b.py\n", "9": "## Files\n\nTBD.\n",
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
        self.assertIn("Missing `## Files`: #5, #9", out)
        self.assertIn("| #9 issue 9 | none | **missing: an empty `## Files` section** |", out)

    def test_repo_defaults_to_gh_repo_view(self):
        self.gh({"issues": {"3": ["OPEN", None]}, "bodies": {"3": "## Files\n- a.py\n"}})
        code, out, err = self.call("roadmap")
        self.assertEqual(code, 0, err)
        self.assertIn("| #3 issue 3 | none | a.py |", out)

    def test_failed_lookup_exits_1(self):
        self.gh({"issues": {"2": ["OPEN", None]}, "broken": ["/dependencies/"]})
        code, _, err = self.call("roadmap", "--repo", "o/r")
        self.assertEqual(code, 1)
        self.assertIn("broken", err)


class OwnerNoteTests(Base):
    """A parent's body or comment holding the owner-note marker is listed under Owner notes."""

    MARK = "**Owner action after this set:**"

    def parent(self, body="", comments=(), **extra):
        self.gh({"issues": {"1": ["OPEN", None], "2": ["OPEN", None]}, "children": {"1": ["2"]},
                 "bodies": {"1": body}, "comments": {"1": list(comments)}, **extra})

    def test_marked_comment_links_to_it(self):
        self.parent(comments=[
            {"body": "Unrelated chatter.", "html_url": "https://x/1#issuecomment-10"},
            {"body": f"Context first.\n\n{self.MARK} grill the next stage\n- before the paid run",
             "html_url": "https://x/1#issuecomment-11"}])
        out = self.ready()
        self.assertIn("Owner notes:\n  #1 https://x/1#issuecomment-11\n"
                      "    **Owner action after this set:** grill the next stage\n"
                      "    - before the paid run\n", out)
        self.assertNotIn("issuecomment-10", out)
        self.assertNotIn("Context first", out)

    def test_marked_body_links_to_the_issue(self):
        self.parent(body=f"{self.MARK} book the GPU")
        self.assertIn("  #1 https://github.com/o/r/issues/1\n    **Owner action after this set:** "
                      "book the GPU\n", self.ready())

    def test_unmarked_and_mid_line_markers_ignored(self):
        self.parent(body=f"Mentions {self.MARK} mid-line.",
                    comments=[{"body": "Owner action after this set: no bold",
                               "html_url": "https://x/1#issuecomment-12"}])
        self.assertNotIn("Owner notes:", self.ready())

    def test_only_parents_are_read(self):
        self.gh({"issues": {"1": ["OPEN", None]}, "bodies": {"1": f"{self.MARK} x"}})
        self.assertNotIn("Owner notes:", self.ready())

    def test_failed_comment_lookup_does_not_hold_go(self):
        (self.records / "briefs" / "2.md").write_text("Depends on: none\n")
        self.call("status", str(self.records), "2", "--state", "parked", "--doing", "parked")
        self.parent(body=f"{self.MARK} still listed", broken=["/comments"])
        out = self.ready()
        self.assertIn("Owner notes:\n  #1 https://github.com/o/r/issues/1\n"
                      "    **Owner action after this set:** still listed\n"
                      "  #1: comments lookup failed:", out)
        self.assertIn("2: send `GO #2`", out)


if __name__ == "__main__":
    unittest.main()
