"""Tests for relay.py: python3 -I tools/tests/test_relay.py (Windows: py -3 -I ...)."""
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
sys.path.insert(0, str(HERE.parent))
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


if __name__ == "__main__":
    unittest.main()
