"""Tests for relay.py: python3 -I tests/test_relay.py (Windows: py -3 -I ...)."""
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
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

    def test_missing_records_folder_exits_2_and_writes_nothing(self):
        gone = self.tmp / "no-such-records"
        code, _, err = self.call("status", str(gone), "12", "--state", "working", "--doing", "x")
        self.assertEqual(code, 2)
        self.assertIn("no records folder", err)
        self.assertFalse(gone.exists())


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

    def test_blocked_by_of_every_issue_the_lane_closes(self):
        self.gh({"blocked_by": {"13": [20]}, "issues": {"20": ["OPEN", None]}})
        self.park("12", "Depends on: none\n- **Closes:** #12 #13\n")
        out = self.ready()
        self.assertIn("12: parked on #20 open", out)
        self.assertNotIn("Ready for GO", out)
        # an issue the lane closes is never its own dependency, and a non-empty list (even of
        # those issues only) means Depends on: is not read; no Closes line: the key alone
        self.gh({"blocked_by": {"13": [12], "12": [13]}, "issues": {"12": ["OPEN", None],
                                                                   "13": ["OPEN", None],
                                                                   "30": ["OPEN", None]}})
        self.park("12", "Depends on: #30\n- **Closes:** #12 #13\n")
        self.assertIn("12: send `GO #12`", self.ready())
        self.park("12", "Depends on: none\n")
        self.assertIn("12: parked on #13 open", self.ready())

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

    def test_deny_list_matches_names_with_non_word_ends(self):
        (self.records / "deny.txt").write_text("@acmebot\nC\\+\\+\n\\.internal\n")
        (self.records / "project.md").write_text("- **Deny list:** `deny.txt`\n")
        head = self.branch("lane-12")
        body = ("Closes #12\n\nPinged @acmebot.\nIn C++ code.\nUse .internal hosts.\n"
                "@acmebots and .internals\n")
        self.done("12", "lane-12", head, body=body)
        self.assertIn("PR body lines [3, 4, 5]: a deny-list name", self.ready())

    def test_deny_list_ends_next_to_a_word_character(self):
        pats = [r"\.internal", "@acmebot", r"C\+\+", "acme co", "acme"]
        for text in ("build.internal", "dev@acmebot", "cc @acmebot", "C++", "the acme co"):
            self.assertTrue(relay.check_pr_body(self.write_body(text), [1], pats), text)
        for text in (".internals", "@acmebots", "acmecorp"):
            self.assertFalse(relay.check_pr_body(self.write_body(text), [1], pats), text)

    def test_deny_list_leading_inline_flags_work(self):
        (self.records / "deny.txt").write_text("(?i)acme\n(?s)(?x) secret \\s code\n")
        (self.records / "project.md").write_text("- **Deny list:** `deny.txt`\n")
        pats = relay.deny_patterns(self.records)
        self.assertTrue(relay.check_pr_body(self.write_body("the acme co"), [1], pats))
        self.assertTrue(relay.check_pr_body(self.write_body("a secret code"), [1], pats))
        self.assertFalse(relay.check_pr_body(self.write_body("acmecorp"), [1], pats))
        head = self.branch("lane-12")
        self.done("12", "lane-12", head, body="Closes #12\n\nFor Acme.\n")
        out = self.ready()
        self.assertIn("PR body lines [3]: a deny-list name", out)
        self.assertNotIn("lookup failed", out)

    def test_deny_list_unusable_line_is_one_records_error(self):
        (self.records / "deny.txt").write_text("# names\nAcme\nacme(?i)corp\n")
        (self.records / "project.md").write_text("- **Deny list:** `deny.txt`\n")
        for bad in ("acme(?i)corp", "(?i)", "acme|", "a)|(b", "(?P=acmesecret)"):
            (self.records / "deny.txt").write_text(f"# names\nAcme\n{bad}\n")
            with self.assertRaisesRegex(ValueError, "deny.txt line 3 is not a usable pattern") as cm:
                relay.deny_patterns(self.records)
            self.assertNotIn("acmesecret", str(cm.exception))
        for key in ("12", "13"):
            self.done(key, f"lane-{key}", self.branch(f"lane-{key}"))
        out = self.ready()
        self.assertEqual(out.count("deny.txt line 3"), 1, out)
        self.assertIn("Records:\n  project.md's deny list", out)
        self.assertNotIn("lookup failed", out)
        self.assertNotIn("acme(?i)corp", out)
        self.assertIn("12: deny-list check not run (see Records)", out)
        self.assertNotIn("Ready for PR", out)

    def test_deny_list_with_a_bom_matches_its_first_line(self):
        (self.records / "deny.txt").write_bytes("Acme\nGlobex\n".encode("utf-8-sig"))
        (self.records / "project.md").write_text("- **Deny list:** `deny.txt`\n")
        self.assertEqual(relay.deny_patterns(self.records), ["Acme", "Globex"])
        head = self.branch("lane-12")
        self.done("12", "lane-12", head, body="Closes #12\n\nFor Acme.\n")
        self.assertIn("PR body lines [3]: a deny-list name", self.ready())

    def test_deny_list_not_utf8_names_the_file_and_line(self):
        (self.records / "project.md").write_text("- **Deny list:** `deny.txt`\n")
        for data, line in (("Acmesecret\n".encode("utf-16"), 1),
                           ("Acme\n# names\nAcmesecrét\n".encode("cp1252"), 3)):
            (self.records / "deny.txt").write_bytes(data)
            with self.assertRaises(ValueError) as cm:
                relay.deny_patterns(self.records)
            self.assertEqual(str(cm.exception),
                             f"project.md's deny list deny.txt line {line} is not valid UTF-8")
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        out = self.ready()
        self.assertIn("Records:\n  project.md's deny list deny.txt line 3 is not valid UTF-8", out)
        self.assertNotIn("Acmesecr", out)
        self.assertNotIn("codec", out)
        self.assertIn("12: deny-list check not run (see Records)", out)

    def test_deny_list_refuses_zero_length_matches_by_line(self):
        (self.records / "project.md").write_text("- **Deny list:** `deny.txt`\n")
        for bad in (r"\b", r"\B", r"(?<=\w)", r"(?=\W)", r"acmesecret|\b", r"(?i)\b", "$",
                    "(?=[a-z])", "acmesecret|(?=9)"):
            (self.records / "deny.txt").write_text(f"# names\nAcme\n{bad}\n")
            with self.assertRaisesRegex(ValueError, "deny.txt line 3 is not a usable pattern") as cm:
                relay.deny_patterns(self.records)
            self.assertNotIn("acmesecret", str(cm.exception))
        (self.records / "deny.txt").write_text("Acme\\b\n\\bGlobex\n")
        self.assertEqual(len(relay.deny_patterns(self.records)), 2)

    def test_deny_list_verbose_comments_work(self):
        (self.records / "deny.txt").write_text("(?x) acme \\s corp  # the old name\n")
        (self.records / "project.md").write_text("- **Deny list:** `deny.txt`\n")
        pats = relay.deny_patterns(self.records)
        self.assertTrue(relay.check_pr_body(self.write_body("at acme corp today"), [1], pats))
        self.assertFalse(relay.check_pr_body(self.write_body("acme corporate"), [1], pats))
        self.assertFalse(relay.check_pr_body(self.write_body("the old name"), [1], pats))

    def write_body(self, text):
        path = self.tmp / "body.md"
        path.write_text(f"Closes #1\n\n{text}\n")
        return path

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
        (self.records / "plan.md").write_bytes(b"x" * 16385)
        self.assertIn("plan.md is 16385 bytes (limit 16384)", self.ready())

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
        (self.records / "plan.md").write_bytes(b"# Plan\n\nbad \xff byte\n" + b"x" * 16384)
        out = self.ready()
        self.assertIn("Records:\n  plan.md line 3: invalid UTF-8", out)
        self.assertIn("plan.md is 16403 bytes", out)

    def test_control_characters_named_by_file_and_line(self):
        (self.records / "plan.md").write_bytes(b"# Plan\r\nrelease\r-0.3.0\n\tok\r\n")
        (self.records / "briefs" / "4.md").write_text("Depends on: none\nbell\x07\n")
        (self.records / "pr-bodies" / "4.md").write_text("Closes #4\n\nesc\x1b[0m\n")
        out = self.ready()
        self.assertIn("plan.md line 2: bare CR", out)
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

    def test_free_form_coordinator_line_warns_with_hint(self):
        (self.records / "plan.md").write_text(
            "# Plan\n\n## Handover\n\n- **Coordinator:** the session in worktree D:\\w (branch b), "
            "since 2026-11-01; mode normal.\n", encoding="utf-8")
        out = self.ready()
        self.assertIn("Records:\n  plan.md line 5: Handover > Coordinator is not in the "
                      "template's shape", out)
        self.assertIn("hint: rewrite it as the template's `title ..., worktree ..., id ..., "
                      "mode ....`, or `none` when no coordinator holds the plan", out)
        # ASCII only: `ready` prints to a console that may not hold more (cp950, say)
        self.assertTrue(all(line.isascii() for line in out.splitlines() if "Coordinator" in line))

    def test_template_and_none_coordinator_lines_do_not_warn(self):
        for line in ("title t, worktree D:\\w, id unknown, mode paused. Since today.",
                     "none. The previous coordinator (worktree D:\\old, id local_0ld)"):
            (self.records / "plan.md").write_text(f"# Plan\n\n- **Coordinator:** {line}\n",
                                                  encoding="utf-8")
            self.assertNotIn("Coordinator", self.ready())

    def test_setup_plan_template_passes_coordinator_check(self):
        template = HERE.parent / "plugin" / "skills" / "setup" / "templates" / "plan.md"
        (self.records / "plan.md").write_bytes(template.read_bytes())
        self.assertNotIn("Coordinator", self.ready())
        self.assertEqual(relay.parse_coordinator(relay.coordinator_field(
            template.read_text(encoding="utf-8"))[1]), {})

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

    def test_plan_limit_counts_bytes(self):
        # 150 lines, each long: under any line limit, over 16 KB
        (self.records / "plan.md").write_bytes(b"# Plan\n" + (b"x" * 119 + b"\n") * 150)
        self.assertIn("plan.md is 18007 bytes (limit 16384)", self.ready())
        (self.records / "plan.md").write_bytes(b"x\n" * 300)
        self.assertNotIn("Plan:", self.ready())
        code, out, err = self.call("ready", str(self.records), "--checkout", str(self.clone),
                                   "--plan-limit", "100")
        self.assertIn("plan.md is 600 bytes (limit 100)", out)

    def test_plan_warning_prints_first(self):
        (self.records / "plan.md").write_bytes(b"x" * 20000)
        self.call("status", str(self.records), "12", "--state", "blocked", "--doing", "a question")
        out = self.ready()
        self.assertTrue(out.startswith("Plan:\n  plan.md is 20000 bytes"), out)
        self.assertEqual(out.count("Plan:"), 1)
        self.assertLess(out.index("Plan:"), out.index("Lanes:"))

    def test_lanes_moved_to_plan_history_are_left_out(self):
        (self.records / "plan.md").write_text(
            "# Plan\n\n## Now\n\n| Key | Issues | Session | State | Parked until |\n"
            "|---|---|---|---|---|\n| 13 | #13 | s | started | - |\n\n## Roadmap\n\n"
            "| Issue | Order |\n|---|---|\n| #12 | 1 |\n")
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        self.gh({"prs": {"lane-12": [{"number": 5, "state": "MERGED", "headRefOid": head}]}})
        self.call("status", str(self.records), "13", "--state", "working", "--doing", "x")
        self.call("status", str(self.records), "14", "--state", "blocked", "--doing", "why")
        out = self.ready()
        self.assertNotIn("  12: ", out)
        self.assertNotIn("Merged:", out)
        self.assertIn("  13: working", out)
        self.assertIn("  14: blocked", out)  # only done lanes outside Now are left out
        self.assertIn("  (1 merged lane not in plan.md's Now table left out)", out)
        (self.records / "plan.md").write_text("# Plan\n")  # no Now table: every lane listed
        self.assertIn("Merged:\n  12: PR #5", self.ready())

    def test_unmerged_done_lane_outside_now_is_still_listed(self):
        (self.records / "plan.md").write_text("# Plan\n\n## Now\n\n| Key | Issues |\n|---|---|\n")
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        out = self.ready()
        self.assertIn("  12: done", out)
        self.assertIn("Ready for PR:\n  12: lane-12", out)
        self.assertNotIn("left out", out)
        self.gh({"prs": {"lane-12": [{"number": 5, "state": "CLOSED", "headRefOid": head}]}})
        self.assertIn("  12: done", self.ready())

    def test_now_keys_reads_the_first_column(self):
        plan = self.records / "plan.md"
        plan.write_text("# Plan\n\n## Now\n\n| Key | Issues |\n|---|---|\n| `12` | #12 |\n"
                        "| **#13** | #13 |\n\n## Roadmap\n\n| Issue |\n|---|\n| 14 |\n")
        self.assertEqual(relay.now_keys(plan), {"12", "13"})
        plan.write_text("# Plan\n")
        self.assertIsNone(relay.now_keys(plan))

    def test_bare_cr_and_mixed_line_endings_flagged(self):
        (self.records / "plan.md").write_bytes(b"# Plan\r\n\r\nNow\n")
        (self.records / "plan-history.md").write_bytes(b"# History\nold\rentry\n")
        (self.records / "briefs" / "4.md").write_bytes(b"Depends on: none\r\nx\n")
        (self.records / "briefs" / "5.md").write_bytes(b"Depends on: none\r\nx\r\n")
        out = self.ready()
        self.assertIn("plan.md: mixed line endings (2 CRLF, 1 LF)", out)
        self.assertIn("plan-history.md line 2: bare CR", out)
        self.assertIn("briefs/4.md: mixed line endings (1 CRLF, 1 LF)", out)
        self.assertNotIn("briefs/5.md", out)


class ReadyLookupTests(Base):
    """ready looks pull requests and pushed heads up once per run, not once per done lane."""

    OK = [{"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"}]

    def lanes(self):
        heads = {k: self.branch(f"lane-{k}", content=f"{k}\n") for k in ("12", "13", "14")}
        for k, head in heads.items():
            self.done(k, f"lane-{k}", head)
        self.gh({"prs": {"lane-12": [{"number": 5, "state": "MERGED", "headRefOid": heads["12"]}],
                         "lane-13": [{"number": 6, "state": "OPEN", "headRefOid": heads["13"],
                                      "mergeable": "MERGEABLE", "statusCheckRollup": self.OK}]}})
        return heads

    def counted_ready(self, *extra):
        calls = pathlib.Path(str(self.fake) + ".calls")
        calls.unlink(missing_ok=True)
        with mock.patch.object(relay, "run", wraps=relay.run) as run:
            code, out, err = self.call("ready", str(self.records), *extra)
        self.assertEqual(code, 0, err)
        gits = [" ".join(c.args[0][1:]) for c in run.call_args_list if c.args[0][0] == "git"]
        prs = [c for c in calls.read_text(encoding="utf-8").splitlines() if c.startswith("pr list")]
        return out, gits, prs

    def test_one_pr_list_and_no_ls_remote_with_a_checkout(self):
        heads = self.lanes()
        out, gits, prs = self.counted_ready("--checkout", str(self.clone))
        self.assertEqual(len(prs), 1, prs)
        self.assertNotIn("--head", prs[0])
        self.assertFalse([g for g in gits if g.startswith("ls-remote")], gits)
        self.assertIn("fetch -q --prune origin", gits)
        self.assertIn("Merged:\n  12: PR #5", out)
        self.assertIn(f"Ready to merge:\n  13: PR #6 --match-head-commit {heads['13']}", out)
        self.assertIn("Ready for PR:\n  14: lane-14", out)

    def test_without_a_checkout_pushed_heads_come_from_ls_remote(self):
        self.lanes()
        out, gits, prs = self.counted_ready()
        self.assertEqual(len(prs), 1, prs)
        self.assertEqual(len([g for g in gits if g.startswith("ls-remote")]), 3, gits)
        self.assertIn("Merged:\n  12: PR #5", out)
        self.assertIn("Ready for PR:\n  14: lane-14", out)

    def test_branch_deleted_after_merge_is_still_merged(self):
        self.lanes()
        git("push", "-q", "origin", "--delete", "lane-12", cwd=self.clone)
        for extra in ((), ("--checkout", str(self.clone))):
            out, _, _ = self.counted_ready(*extra)
            self.assertIn("Merged:\n  12: PR #5", out)
            self.assertNotIn("12: status head", out)

    def test_deleted_unmerged_branch_is_still_not_pushed(self):
        self.lanes()
        git("push", "-q", "origin", "--delete", "lane-14", cwd=self.clone)
        out, _, _ = self.counted_ready("--checkout", str(self.clone))
        self.assertIn("14: status head", out)
        self.assertIn("(branch not pushed)", out)

    def test_merged_pr_of_another_head_on_a_deleted_branch_is_not_merged(self):
        self.lanes()
        self.gh({"prs": {"lane-12": [{"number": 5, "state": "MERGED", "headRefOid": "f" * 40}]}})
        git("push", "-q", "origin", "--delete", "lane-12", cwd=self.clone)
        out, _, _ = self.counted_ready("--checkout", str(self.clone))
        self.assertIn("12: status head", out)
        self.assertNotIn("Merged", out)

    def test_a_failed_fetch_falls_back_to_ls_remote(self):
        self.lanes()
        real = relay.run

        def run(cmd, cwd=None):
            return (1, "", "offline") if cmd[1] == "fetch" else real(cmd, cwd)
        with mock.patch.object(relay, "run", run):
            out, gits, _ = self.counted_ready("--checkout", str(self.clone))
        self.assertEqual(len([g for g in gits if g.startswith("ls-remote")]), 3, gits)
        self.assertIn("Ready for PR:\n  14: lane-14", out)

    def test_a_failed_fetch_skips_the_conflict_check_and_says_so(self):
        heads = self.lanes()
        real = relay.run

        def run(cmd, cwd=None):
            return (1, "", "offline") if cmd[1] == "fetch" else real(cmd, cwd)
        with mock.patch.object(relay, "run", run):
            out, gits, _ = self.counted_ready("--checkout", str(self.clone))
        self.assertFalse([g for g in gits if g.startswith("merge-tree")], gits)
        self.assertIn(f"  13: PR #6 --match-head-commit {heads['13']} "
                      "(conflict check skipped: fetch failed)", out)
        self.assertIn(f"  14: lane-14 @ {heads['14'][:7]} "
                      "(conflict check skipped: fetch failed)", out)

    def test_an_unreachable_origin_is_a_lookup_failure_not_unpushed(self):
        self.lanes()
        git("remote", "set-url", "origin", str(self.tmp / "gone.git"), cwd=self.clone)
        out, _, _ = self.counted_ready("--checkout", str(self.clone))
        self.assertIn("14: lookup failed: git ls-remote origin lane-14", out)
        self.assertNotIn("branch not pushed", out)

    def test_a_full_list_looks_up_each_branch_without_a_merged_pr(self):
        self.lanes()
        with mock.patch.object(relay, "PR_LIST_MIN", 2), mock.patch.object(relay, "PR_LIST_PER_LANE", 0):
            out, _, prs = self.counted_ready("--checkout", str(self.clone))
        self.assertEqual(prs[1:], ["pr list --repo o/r --head lane-13 --state all --json "
                                   "number,state,headRefOid,mergeable,statusCheckRollup,body",
                                   "pr list --repo o/r --head lane-14 --state all --json "
                                   "number,state,headRefOid,mergeable,statusCheckRollup,body"])
        self.assertIn("Merged:\n  12: PR #5", out)
        self.assertIn("Ready to merge:\n  13: PR #6", out)
        self.assertIn("Ready for PR:\n  14: lane-14", out)

    def test_a_failed_list_is_a_lookup_failure_for_each_done_lane(self):
        self.lanes()
        self.gh({"broken": ["--limit"]})
        out, _, prs = self.counted_ready("--checkout", str(self.clone))
        self.assertEqual(len(prs), 1, prs)
        for k in ("12", "13", "14"):
            self.assertIn(f"  {k}: lookup failed: gh pr list", out)


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

    def test_two_commands_in_one_item_is_an_error(self):
        for line in ("`npm test`, `npm run lint`", "`a`; `b` and `c` main checkout only",
                     "`a` (Windows: `b`) `c`"):
            with self.assertRaisesRegex(ValueError, "more than one command"):
                relay.check_commands(line, windows=False)
        self.assertEqual(relay.check_commands("`a` (Windows: `b`).", windows=False), (["a"], []))
        self.assertEqual(relay.check_commands("`a` (Windows: `b`).", windows=True), (["b"], []))

    def test_windows_override_written_before_the_command(self):
        line = "(Windows: `b`) `a`; `c`"
        self.assertEqual(relay.check_commands(line, windows=False), (["a", "c"], []))
        self.assertEqual(relay.check_commands(line, windows=True), (["b", "c"], []))
        for line in ("`a`; (Windows: `b`)", "(Windows: `b`) main checkout only"):
            for windows in (False, True):
                with self.assertRaisesRegex(ValueError, "only a Windows override") as e:
                    relay.check_commands(line, windows=windows)
                self.assertIn(line, str(e.exception))

    def test_non_utf8_project_md_exits_2_with_one_line(self):
        self.lane()
        (self.records / "project.md").write_bytes(b"- **Local checks:** `x` caf\xe9\n")
        code, out, err = self.localcheck()
        self.assertEqual(code, 2, out + err)
        self.assertEqual(len(err.strip().splitlines()), 1, err)
        self.assertIn("not valid UTF-8", err)
        self.assertEqual(len(self.worktrees()), 1)

    def test_two_commands_in_one_item_exits_2_naming_the_line(self):
        self.lane()
        self.project(f"- **Local checks:** {self.py('print(5)')}, `npm run lint`\n")
        code, out, err = self.localcheck()
        self.assertEqual(code, 2, out + err)
        self.assertIn("more than one command", err)
        self.assertIn("`npm run lint`", err)
        self.assertNotIn("$ ", out)


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
        self.assertEqual(self.watched(), ["pr checks 5 --repo o/r --watch", "pr checks 5 --repo o/r"])
        self.assertIn("checks of 5", out)

    def test_checks_on_a_later_poll_are_watched_to_their_result(self):
        code, out, err = self.waitchecks(after=2)
        self.assertEqual((code, self.polls), (0, [0.0, 60.0]), err)
        code, out, err = self.waitchecks(after=4, watch=(1, "X test fail"), rollup=self.FAILED,
                                         checks={"5": "test\tfail"})
        self.assertEqual(code, 1, err)
        self.assertEqual(self.polls[:4], [0.0, 60.0, 180.0, 360.0])
        self.assertIn("test\tfail", out)

    def test_a_watch_error_with_no_failed_check_is_a_lookup_failure(self):
        code, out, err = self.waitchecks(watch=(1, "", "HTTP 502"))
        self.assertEqual(code, 4, err)
        self.assertIn("HTTP 502", err)
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
                          (c.startswith("pr view") and "statusCheckRollup" in c)], [])
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
        failed = [{"name": "ci", "status": "COMPLETED", "conclusion": "FAILURE"}]
        prs = {f"lane-{k}": [{"number": pr, "state": "OPEN", "headRefOid": head,
                              "mergeable": "MERGEABLE", "statusCheckRollup": failed}]
               for k, (pr, head) in self.heads.items()}
        code, out, err = self.merge("12", "13", prs=prs)
        self.assertIn("12: not under Ready to merge (Waiting: ", err)
        self.assertIn("check failed", err)
        self.assertEqual(self.merges(), [])
        code, out, err = self.merge("12", "13", "12")
        self.assertEqual((code, self.merges()), (2, []))
        self.assertIn("12: given more than once; nothing merged", err)

    def test_an_unusable_deny_list_is_one_line_before_any_merge(self):
        (self.records / "deny.txt").write_text("Acme\nacme(?i)corp\n")
        (self.records / "project.md").write_text("- **Deny list:** `deny.txt`\n")
        code, out, err = self.merge("12", "13")
        self.assertEqual((code, self.merges()), (1, []))
        self.assertEqual(err.strip().splitlines(), [
            "project.md's deny list deny.txt line 2 is not a usable pattern (the error is not "
            "shown: it can quote the name); nothing merged"])
        (self.records / "deny.txt").write_bytes("Acmesecret\n".encode("utf-16"))
        code, out, err = self.merge("12", "13")
        self.assertEqual((code, self.merges()), (1, []))
        self.assertEqual(err.strip().splitlines(), [
            "project.md's deny list deny.txt line 1 is not valid UTF-8; nothing merged"])

    def test_failed_merge_stops_the_rest(self):
        code, out, err = self.merge("12", "13", merge_fail={"5": "Head branch was modified"})
        self.assertEqual(code, 1)
        self.assertEqual(len(self.merges()), 1)
        self.assertIn("12: gh pr merge 5 failed: ", err)
        self.assertIn("Head branch was modified", err)


class SafeExitTests(Base):
    """waitchecks and merge exit by what CI and GitHub say, never by an error of their own; the
    watch output appears once; ready's relay.py and project.md warnings never mislead or crash."""

    QUEUED, FAILED, OK = WaitchecksTests.QUEUED, WaitchecksTests.FAILED, MergeTests.OK
    waitchecks, watched = WaitchecksTests.waitchecks, WaitchecksTests.watched
    merge, merges = MergeTests.merge, MergeTests.merges
    relay_py_line, advance_origin = ReadyTests.relay_py_line, ReadyTests.advance_origin

    def lanes(self):
        self.heads = {}
        for key, pr in (("12", 5), ("13", 6)):
            head = self.branch(f"lane-{key}", content=f"{key}\n")
            self.done(key, f"lane-{key}", head)
            self.heads[key] = (pr, head)

    def call_cp1252(self, *argv):
        """Base.call with stdout and stderr encoding as a piped Windows console does."""
        out, err = (io.TextIOWrapper(io.BytesIO(), encoding="cp1252") for _ in range(2))
        cwd = os.getcwd()
        os.chdir(self.clone)
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = relay.main(list(argv))
        finally:
            os.chdir(cwd)
        texts = []
        for s in (out, err):
            s.flush()
            texts.append(s.buffer.getvalue().decode("cp1252"))
        return code, *texts

    def test_non_ascii_check_name_on_a_cp1252_stdout_exits_by_the_checks(self):
        table = "\u6e2c\u8a66 \u2713\tpass"
        with mock.patch.object(self, "call", self.call_cp1252):
            code, out, err = self.waitchecks(watch=(0, table, "\u8b66\u544a"), checks={"5": table})
            self.assertEqual(code, 0, err)
            self.assertIn("?? ?\tpass", out)
            self.assertIn("??", err)
            code, out, err = self.waitchecks(watch=(1, table), rollup=self.FAILED, checks={"5": table})
            self.assertEqual(code, 1, err)

    def test_an_unexpected_error_exits_4_with_one_line(self):
        def boom(*args, **kw):
            raise ZeroDivisionError("bad\nthing")
        with mock.patch.object(relay, "wait_checks", boom):
            code, out, err = self.call("waitchecks", str(self.records), "5", "--repo", "o/r")
        self.assertEqual((code, err), (4, "waitchecks: unexpected error: ZeroDivisionError: bad thing\n"))
        with mock.patch.object(relay, "ready_to_merge", boom):
            code, out, err = self.call("merge", str(self.records), "12", "--repo", "o/r")
        self.assertEqual((code, err), (4, "merge: unexpected error: ZeroDivisionError: bad thing\n"))

    def test_watch_output_appears_once(self):
        tick = "Refreshing checks status every 10 seconds.\ntest\tpending\n"
        code, out, err = self.waitchecks(watch=(0, tick * 3), checks={"5": "test\tpass\t1m"})
        self.assertEqual(code, 0, err)
        self.assertEqual(out.count("test\tpass"), 1)
        self.assertNotIn("pending", out)
        self.assertNotIn("Refreshing", out)

    def test_a_repo_with_workflows_behaves_as_before_apart_from_the_timing(self):
        # fake_gh reports one workflow by default: no no-CI lookup, the same calls as before #51
        code, out, err = self.waitchecks(after=2)
        self.assertEqual((code, self.polls), (0, [0.0, 60.0]), err)
        calls = pathlib.Path(str(self.fake) + ".calls").read_text().splitlines()
        self.assertEqual(calls, ["pr view 5 --repo o/r --json statusCheckRollup"] * 2 +
                         ["pr checks 5 --repo o/r --watch", "pr checks 5 --repo o/r"])

    def test_a_pr_left_behind_by_an_earlier_merge_stops(self):
        self.lanes()
        base = {"headRefOid": self.heads["12"][1], "baseRefName": "main",
                "mergedAt": "2026-10-31T07:00:00Z", "mergeCommit": {"oid": "m5" * 20}}
        views = {"5": [{**base, "mergeStateStatus": s} for s in ("UNKNOWN", "UNKNOWN", "BEHIND")],
                 "6": {**base, "headRefOid": self.heads["13"][1], "mergeStateStatus": "CLEAN",
                       "mergeCommit": {"oid": "m6" * 20}}}
        code, out, err = self.merge("13", "12", pr_view=views)
        self.assertEqual(code, 1, err)
        self.assertEqual(len(self.merges()), 1)
        self.assertIn("13: merged PR #6", out)
        self.assertIn("12: PR #5 merge state is BEHIND, not CLEAN", err)

    def test_merge_checks_conflicts_in_the_current_folder_by_default(self):
        self.lanes()
        (self.clone / "a.txt").write_text("main\n")
        git("commit", "-qam", "conflict", cwd=self.clone)
        git("push", "-q", "origin", "main", cwd=self.clone)
        code, out, err = self.merge("12")
        self.assertEqual((code, self.merges()), (1, []), err)
        self.assertIn("12: not under Ready to merge (Waiting: ", err)
        self.assertIn("conflict", err)

    def test_merge_stops_when_its_fetch_fails(self):
        self.lanes()
        real = relay.run

        def run(cmd, cwd=None):
            return (1, "", "offline") if cmd[:2] == ["git", "fetch"] else real(cmd, cwd)
        with mock.patch.object(relay, "run", run):
            code, out, err = self.merge("12")
        self.assertEqual((code, self.merges()), (1, []), err)
        self.assertIn("git fetch failed", err)
        self.assertIn("offline", err)
        self.assertIn("nothing merged", err)
        self.assertNotIn("merge-tree", err)

    def test_merge_refuses_a_checkout_that_is_not_a_git_checkout(self):
        (self.tmp / "outside").mkdir()
        for folder in (self.tmp / "outside", self.tmp / "missing"):
            code, out, err = self.call("merge", str(self.records), "12", "--repo", "o/r",
                                       "--checkout", str(folder))
            self.assertEqual(code, 2, err)
            self.assertIn("is not a git checkout: pass --checkout <a clone of o/r>", err)

    def test_relay_py_behind_on_another_branch_or_ahead_offers_no_command(self):
        main = self.tmp / "with space (x86)"
        git("clone", "-q", str(self.origin), str(main), cwd=self.tmp)
        for k, v in (("user.email", "t@example.com"), ("user.name", "t")):
            git("config", k, v, cwd=main)
        git("switch", "-q", "-c", "feature", cwd=main)
        self.relay_py_line(f"{main}/relay.py (the main checkout; see `origin/main`)")
        self.advance_origin(1)
        where = main.resolve().as_posix()
        out = self.ready()
        self.assertIn(f"{where} is 1 commit behind origin/main, but it is on branch feature, "
                      "not main: update it by hand", out)
        self.assertNotIn("git -C", out)
        git("switch", "-q", "main", cwd=main)
        (main / "local.txt").write_text("x\n")
        git("add", ".", cwd=main)
        git("commit", "-qm", "local", cwd=main)
        out = self.ready()
        self.assertIn(f"{where} is 1 commit behind origin/main, but its main has commits "
                      "origin/main does not", out)
        self.assertNotIn("git -C", out)
        git("switch", "-q", "--detach", cwd=main)
        self.assertIn("on a detached HEAD, not main", self.ready())

    def test_a_non_utf8_project_md_is_one_records_warning(self):
        (self.clone / "plugin" / "tools").mkdir(parents=True)
        self.advance_origin(1)
        git("reset", "-q", "--hard", "HEAD~1", cwd=self.clone)
        for data in ("- **relay.py:** plugin/tools/relay.py\n".encode("utf-16"),
                     "- **relay.py:** plugin/tools/relay.py \u8def\u5f91\n".encode("cp950")):
            (self.records / "project.md").write_bytes(data)
            out = self.ready()
            self.assertEqual(out.count("project.md line 1: invalid UTF-8"), 1, out)
            self.assertNotIn("behind", out)
        with self.assertRaisesRegex(ValueError, "project.md is not valid UTF-8"):
            relay.project_line(self.records, "relay.py")
        code, _, err = self.call("waitchecks", str(self.records), "5", "--repo", "o/r")
        self.assertEqual(code, 2)
        self.assertIn("not valid UTF-8", err)


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


class HintTests(Base):
    """ready, roadmap, waitchecks and merge print the coordinator's next step beside the output it
    applies to (#131); one test per batch-H row of the #110 inventory."""

    QUEUED, FAILED, OK = WaitchecksTests.QUEUED, WaitchecksTests.FAILED, MergeTests.OK
    waitchecks = WaitchecksTests.waitchecks
    merge, merges = MergeTests.merge, MergeTests.merges
    lanes = SafeExitTests.lanes
    parent = OwnerNoteTests.parent

    def hints(self, section, *items):
        return " | ".join(relay.section_hints(section, list(items)))

    def test_c18_roadmap_ends_with_how_to_fill_an_empty_roadmap(self):
        self.gh({"issues": {"3": ["OPEN", None]}, "bodies": {"3": "## Files\n- a.py\n"}})
        code, out, err = self.call("roadmap", "--repo", "o/r")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.rstrip().endswith(
            "hint: an empty Roadmap: fill Issue, Blocked by and Files it owns from these rows, "
            "then Order and Kind, and replace every placeholder"), out)
        self.gh({})
        code, out, err = self.call("roadmap", "--repo", "o/r")
        self.assertNotIn("hint:", out)  # no rows to fill from

    def test_c22_owner_notes_say_where_they_go(self):
        self.parent(body=f"{OwnerNoteTests.MARK} book the GPU")
        self.assertIn("    **Owner action after this set:** book the GPU\n  hint: copy each one "
                      "plan.md's *Waiting for the user's decision* lacks into it, with its link; "
                      "owner-only work stays an owner note on its parent: it gets no lane and no "
                      "Roadmap row\n", self.ready())
        self.assertEqual(self.hints("Owner notes", "#1: comments lookup failed: HTTP 502"), "")

    def test_c61_parents_get_one_row_and_closing_asks_the_user(self):
        self.gh({"issues": {"1": ["OPEN", None], "2": ["CLOSED", "COMPLETED"]},
                 "children": {"1": ["2"]}})
        out = self.ready()
        self.assertIn("  hint: a parent gets one Roadmap row with Kind `parent` and no brief or "
                      "worker; its children are the lanes\n", out)
        self.assertIn("  hint: every child closed as completed: ask the user before closing the "
                      "parent (*Consent*)\n", out)
        self.assertNotIn("ask the user before closing",
                         self.hints("Parents", "#1 t: 1 open, 0 closed children"))
        self.assertEqual(self.hints("Parents", "lookup failed: HTTP 502"), "")

    def test_c90_each_ready_section_has_its_handler(self):
        cases = {
            ("Ready for GO", "13: send `GO #13`"): "hold it",
            ("Ready for PR", "12: lane-12 @ abc1234"): "*Finishing a lane* step 1",
            ("Ready to merge", "12: PR #5 --match-head-commit " + "a" * 40): "step 4, **Merge**",
            ("Waiting", "12: blocked: which name?"): "options with your recommendation",
            ("Waiting", "12: lookup failed: HTTP 502"): "rerun `ready`",
            ("Waiting", "12: PR #5 check failed: test"): "goes to the user with the watch output",
            ("Waiting", "12: PR #5 no checks reported"): "a CI fallback",
            ("Waiting", "12: PR #5 checks pending"): "need nothing",
            ("Waiting", "13: parked on #12 open"): "need nothing",
            ("Waiting", "12: deny-list check not run (see Records)"): "rerun `ready` only after",
            ("No status yet", "4: a brief but no status file"): "stays `started`",
            ("Merged", "12: PR #5"): "*Finishing a lane* step 6",
            ("Inconsistent", "12: done with no report file"): "fix the plan line",
        }
        for (section, item), words in cases.items():
            self.assertIn(words, self.hints(section, item), (section, item))
        # only the kinds present get a hint
        self.assertEqual(self.hints("Waiting", "12: blocked: which name?").count("|"), 0)
        # a blocked lane's own words never pick another kind's hint
        self.assertEqual(self.hints("Waiting", "12: blocked: conflict, lookup failed, check failed, "
                                               "checks pending or parked on #3?").count("|"), 0)
        self.call("status", str(self.records), "12", "--state", "blocked", "--doing", "pick one")
        self.assertIn("Waiting:\n  12: blocked: pick one\n  hint: a blocked lane's question",
                      self.ready())

    def test_c91_could_not_parse_never_edits_by_hand(self):
        (self.records / "status" / "12.md").write_bytes(b"- state: working\n- doing: \xff\n")
        self.assertIn("Could not parse:\n  12: invalid UTF-8\n  hint: message its worker to rerun "
                      "its last `relay.py status`; never edit a status file by hand\n", self.ready())

    def test_c94_conflict_or_pr_body_problem_goes_back_to_the_worker(self):
        self.assertIn("message its worker to catch up, push, and write `done` again",
                      self.hints("Waiting", "12: conflicts with the default branch: a.txt"))
        self.assertIn("message its worker to catch up",
                      self.hints("Waiting", "12: PR #5 has a merge conflict"))
        head = self.branch("lane-12")
        self.done("12", "lane-12", head, body="# Title\n\nCloses #12\n")
        self.assertIn("  hint: a PR body problem: message its worker to fix the draft, push, and "
                      "write `done` again\n", self.ready())

    def test_c99_waitchecks_prints_the_next_step_for_each_exit(self):
        code, out, _ = self.waitchecks()
        self.assertEqual(code, 0)
        self.assertTrue(out.rstrip().endswith("hint (exit 0): the checks passed: merge "
                                              "(coordinate's *Finishing a lane* step 4, **Merge**)"))
        code, out, _ = self.waitchecks(watch=(1, "X test fail"), rollup=self.FAILED,
                                       checks={"5": "test\tfail"})
        self.assertEqual(code, 1)
        self.assertIn("hint (exit 1): a failed check goes to the user with the watch output", out)
        code, out, _ = self.waitchecks(project="- **CI start wait:** soon\n")
        self.assertEqual(code, 2)
        self.assertIn("hint (exit 2): a usage error: fix what its error line names and rerun", out)
        code, out, _ = self.waitchecks(after=99, project="")
        self.assertEqual(code, 3)
        self.assertIn("hint (exit 3): no checks appeared: take the `ci-fallbacks.md` case", out)
        code, out, _ = self.waitchecks(after=99, broken=["statusCheckRollup"])
        self.assertEqual(code, 4)
        self.assertIn("hint (exit 4): a lookup failed or an unexpected error: rerun it once; if it "
                      "exits 4 again, give the user its line", out)

    def test_c102_merge_says_read_the_push_run(self):
        self.lanes()
        code, out, err = self.merge("12")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.rstrip().endswith(
            "hint (exit 0): read the default branch's run for the last merge commit instead of "
            "rerunning checks locally; tell the user which lanes merged"), out)

    def test_c103_merge_prints_the_next_step_for_each_stop(self):
        self.lanes()
        code, out, _ = self.merge("12", "13", view={"5": {"mergeStateStatus": "BLOCKED"}})
        self.assertEqual(code, 1)
        self.assertIn("hint (exit 1): it stopped at one lane", out)
        self.assertIn("A key not under Ready to merge (nothing merged): fix what `ready` says", out)
        code, out, _ = self.merge("12", "12")
        self.assertEqual(code, 2)
        self.assertIn("hint (exit 2): a usage error, nothing merged", out)

        def boom(*args, **kw):
            raise ZeroDivisionError("bad")
        with mock.patch.object(relay, "ready_to_merge", boom):
            code, out, _ = self.call("merge", str(self.records), "12", "--repo", "o/r")
        self.assertEqual(code, 4)
        self.assertIn("hint (exit 4): an unexpected error, which may come after some merges; "
                      "exit 4: do not rerun; give the user its line, and run `ready` to see which "
                      "lanes merged", out)

    def test_c121_plan_warning_asks_for_one_pruning_pass(self):
        (self.records / "plan.md").write_bytes(b"x" * 20000)
        out = self.ready()
        self.assertTrue(out.startswith("Plan:\n  plan.md is 20000 bytes"), out)
        self.assertIn("\n  hint: do one pruning pass of everything else: move each entry that is "
                      "DONE or CONFIRMED", out)
        self.assertLess(out.index("hint: do one pruning pass"), out.index("Lanes:"))

    def test_c125_bad_bytes_in_plan_files_say_keep_utf8_and_lf(self):
        (self.records / "plan.md").write_bytes(b"# Plan\r\nrelease\r-0.3.0\n")
        self.assertIn("  hint: whatever edits plan.md, plan-history.md or a brief keeps its "
                      "encoding (UTF-8) and its line endings (LF", self.ready())
        self.assertNotIn("keeps its encoding",
                         self.hints("Records", "pr-bodies/4.md line 3: control character U+001B"))

    def test_c127_records_warnings_get_the_handler_for_their_file(self):
        self.assertIn("fix that line with the Edit tool",
                      self.hints("Records", "briefs/4.md line 2: control character U+0007"))
        self.assertIn("since `ready` checks the draft before a PR opens; open no PR for that lane "
                      "until `ready` no longer flags it",
                      self.hints("Records", "pr-bodies/4.md line 3: control character U+001B"))
        project = self.hints("Records", "project.md line 2: invalid UTF-8 (byte 0xff)")
        self.assertIn("in project.md, the user's settings: give the user the line", project)
        self.assertNotIn("Edit tool", project)
        self.assertEqual(self.hints("Records", ".gitattributes missing, so ..."), "")

    def test_c128_deny_list_warning_never_reads_the_file(self):
        (self.records / "deny.txt").write_text("\\b\n")
        (self.records / "project.md").write_text("- **Deny list:** `deny.txt`\n")
        out = self.ready()
        self.assertIn("  hint: a deny-list line: give the user the line and wait for them to fix "
                      "it; never open, read or print the deny file", out)
        self.assertNotIn("the user's settings", out)

    def test_c129_relay_py_behind_runs_the_command_only_on_yes(self):
        hint = self.hints("relay.py", "D:/r is 2 commits behind origin/main: git -C D:/r merge "
                                      "--ff-only origin/main")
        self.assertIn("only on the user's yes", hint)
        self.assertIn("a standing instruction to keep it current", hint)
        hint = self.hints("relay.py", "D:/r is 2 commits behind origin/main, but it is on branch "
                                      "x, not main: update it by hand once its work is safe")
        self.assertEqual(hint, "tell the user, and give them the line to settle by hand")


class CoordinatorLineTests(unittest.TestCase):
    """parse_coordinator: Handover's Coordinator line in the template's shape, or `none`."""

    def test_template_shape(self):
        self.assertEqual(relay.parse_coordinator(
            "title t, worktree D:\\Repos\\x, id local_1, mode unattended. Since 2026-11-02."),
            {"worktree": "D:\\Repos\\x", "mode": "unattended"})

    def test_path_with_spaces(self):
        self.assertEqual(relay.parse_coordinator(
            "title t, worktree /home/u/my repo, id unknown, mode normal.")["worktree"],
            "/home/u/my repo")

    def test_none_names_no_coordinator(self):
        self.assertEqual(relay.parse_coordinator("none"), {})
        self.assertEqual(relay.parse_coordinator(
            "none. The previous coordinator (worktree D:\\old, id local_0ld)"), {})

    def test_other_lines_rejected(self):
        for line in (
                "the session in worktree D:\\w (branch b), since 2026-11-01; mode normal. "
                "The previous coordinator (worktree D:\\old, id local_0ld)",
                "the session in worktree D:\\w, id local_1; mode normal.",
                "title t, worktree `D:\\w`, id unknown, mode normal.",
                "title t, worktree D:\\w, id unknown, mode sleepy.",
                "title t, worktree D:\\w, id unknown, mode normal",
                "nonexistent", "none-ish", ""):
            self.assertIsNone(relay.parse_coordinator(line), line)


class ResumeTests(unittest.TestCase):
    """resume.py, the SessionStart (compact) hook, run the way the hook runs it."""
    RESUME = HERE.parent / "plugin" / "tools" / "resume.py"

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
        self.main = self.tmp / "repo"
        git("init", "-q", "-b", "main", str(self.main), cwd=self.tmp)
        for k, v in (("user.email", "t@example.com"), ("user.name", "t")):
            git("config", k, v, cwd=self.main)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=self.main)
        self.records = self.tmp / "repo-coord"
        git("worktree", "add", "-q", "--detach", str(self.records), cwd=self.main)
        git("switch", "-q", "--orphan", "coord", cwd=self.records)
        for d in ("status", "briefs", "reports"):
            (self.records / d).mkdir()
        (self.records / "project.md").write_text(
            "- **Language:** talk to the user in Traditional Chinese (繁體中文).\n"
            "- **relay.py:** none\n", encoding="utf-8")
        self.coord = self.tmp / "coordwt"
        self.lane = self.tmp / "lanewt"
        git("worktree", "add", "-q", "-b", "c", str(self.coord), cwd=self.main)
        git("worktree", "add", "-q", "-b", "claude/lane-7-ab", str(self.lane), cwd=self.main)
        (self.records / "plan.md").write_text(
            f"# Plan\n\n## Handover\n\n- **Coordinator:** title t, worktree {self.coord}, "
            "id unknown, mode normal.\n", encoding="utf-8")
        (self.records / "status" / "7.md").write_text(
            "# 7 status\n\n- state: working\n- branch: claude/lane-7-ab\n- head: 1\n")

    def resume(self, cwd):
        r = subprocess.run([sys.executable, "-I", str(self.RESUME)], capture_output=True,
                           input=json.dumps({"cwd": str(cwd), "source": "compact"}).encode())
        self.assertEqual(r.returncode, 0)
        return r.stdout.decode("utf-8")

    def test_coordinator_gets_language_and_plan(self):
        out = self.resume(self.coord)
        self.assertIn("relay coordinator", out)
        self.assertIn("- Language: talk to the user in Traditional Chinese (繁體中文).", out)
        self.assertIn(f"Reread {self.records / 'plan.md'}: Handover (with Next), Now", out)
        self.assertIn("Read tool before you edit it", out)
        self.assertIn("- Mode normal, as Handover records it", out)
        self.assertIn(f"(relay.py: {(HERE.parent / 'plugin' / 'tools' / 'relay.py').resolve()})", out)
        self.assertNotIn("SKILL.md", out)

    def test_coordinator_path_with_other_slashes(self):
        plan = self.records / "plan.md"
        plan.write_text(plan.read_text(encoding="utf-8").replace(
            str(self.coord), self.coord.as_posix() + "/"), encoding="utf-8")
        self.assertIn("relay coordinator", self.resume(self.coord))

    def test_free_form_coordinator_line_prints_nothing(self):
        (self.records / "plan.md").write_text(
            f"# Plan\n\n## Handover\n\n- **Coordinator:** the session in worktree {self.coord} "
            "(branch c), since 2026-11-01; mode normal.\n", encoding="utf-8")
        self.assertEqual(self.resume(self.coord), "")

    def test_none_with_previous_coordinator_prints_nothing(self):
        (self.records / "plan.md").write_text(
            f"# Plan\n\n## Handover\n\n- **Coordinator:** none. The previous coordinator "
            f"(worktree {self.coord}, id local_0ld)\n", encoding="utf-8")
        self.assertEqual(self.resume(self.coord), "")

    def test_worker_gets_its_lane_files_from_a_subfolder(self):
        (self.lane / "sub").mkdir()
        out = self.resume(self.lane / "sub")
        self.assertIn("relay worker for lane 7", out)
        self.assertIn("(繁體中文)", out)
        for f in (self.records / "briefs" / "7.md", self.records / "status" / "7.md",
                  self.records / "reports" / "7.md"):
            self.assertIn(str(f), out)
        self.assertNotIn("coordinator", out)

    def test_unrelated_worktree_and_folder_print_nothing(self):
        self.assertEqual(self.resume(self.main), "")
        self.assertEqual(self.resume(self.tmp), "")

    def test_relay_py_line_relative_to_checkout(self):
        (self.records / "project.md").write_text(
            "- **relay.py:** `tools/relay.py` (vendored)\n", encoding="utf-8")
        out = self.resume(self.coord)
        self.assertIn(f"(relay.py: {self.coord / 'tools' / 'relay.py'})", out)
        self.assertNotIn("Language", out)

    def test_separate_repo_pointer_line(self):
        other = self.tmp / "repo-records"
        other.mkdir()
        (other / "status").mkdir()
        (other / "project.md").write_text("- **Language:** English.\n", encoding="utf-8")
        (other / "status" / "7.md").write_text("- branch: claude/lane-7-ab\n")
        (self.lane / "CLAUDE.md").write_text(
            "Multi-session work: records in ../repo-records beside the main checkout, cloned "
            "from https://x/r.git on branch coord (never merged); the coordinator runs "
            "/relay:coordinate, workers follow relay:work.\n")
        out = self.resume(self.lane)
        self.assertIn(f"records at {other}", out)
        self.assertIn("- Language: English.", out)

    def test_no_records_prints_nothing(self):
        (self.records / "project.md").unlink()
        self.assertEqual(self.resume(self.coord), "")


class RecordsDenyTests(Base):
    """ready and merge check every committed records file against the deny list (#139)."""

    OK = MergeTests.OK
    merge, merges = MergeTests.merge, MergeTests.merges

    def setUp(self):
        super().setUp()
        (self.records / "deny.txt").write_text("Acme(?:Corp)?\n")
        (self.records / "project.md").write_text("- **Deny list:** `deny.txt`\n")

    def test_each_file_kind_is_reported_by_file_and_line_never_the_name(self):
        cases = {
            "plan.md": "# Plan\n\nWorked on AcmeCorp.\n",
            "plan-history.md": "# History\nacme lane merged\n",
            "briefs/12.md": "Depends on: none\n- **Closes:** #12\n\n\nfor Acme\n",
            "reports/12.md": "- branch\n- AcmeCorp data\n",
            "status/12.md": "- state: working\n- doing: porting acme\n- branch: lane-12\n"
                            "- head: abc1234\n- time: 2026-11-02 21:00 -0800\n",
        }
        lines = {"plan.md": 3, "plan-history.md": 2, "briefs/12.md": 5, "reports/12.md": 2,
                 "status/12.md": 2}
        for name, text in cases.items():
            with self.subTest(name):
                path = self.records / name
                path.write_text(text)
                out = self.ready()
                self.assertIn(f"Records:\n  {name} lines [{lines[name]}]: a deny-list name "
                              "(lines only, never the name)", out)
                self.assertNotRegex(out.lower(), "acme")
                path.unlink()
        self.assertNotIn("deny-list name", self.ready())

    def test_a_word_inside_another_is_no_hit(self):
        (self.records / "reports" / "12.md").write_text("acmeish\nAcme.\n")
        self.assertIn("reports/12.md lines [2]:", self.ready())

    def test_deny_list_none_checks_nothing(self):
        (self.records / "plan.md").write_text("AcmeCorp\n")
        (self.records / "project.md").write_text("- **Deny list:** none\n")
        self.assertNotIn("deny-list", self.ready())

    def test_a_failed_records_scan_keeps_the_pr_body_check(self):
        head = self.branch("lane-12")
        self.done("12", "lane-12", head, body="Closes #12\n\nFor Acme.\n")
        with mock.patch.object(relay, "records_deny_hits", side_effect=OSError("disk")):
            out = self.ready()
        self.assertIn("records deny-list check failed: disk", out)
        self.assertIn("PR body lines [3]: a deny-list name", out)

    def test_hints_say_who_fixes_a_hit(self):
        for name in ("reports/12.md", "status/12.md"):
            self.assertIn("message its worker", relay.section_hints(
                "Records", [f"{name} lines [2]: a deny-list name (lines only, never the name)"])[0])
        self.assertIn("fix that line with the Edit tool", relay.section_hints(
            "Records", ["briefs/12.md lines [2]: a deny-list name (lines only, never the name)"])[0])

    def test_merge_stops_on_a_hit_and_never_prints_the_name(self):
        for key in ("12", "13"):
            head = self.branch(f"lane-{key}", content=f"{key}\n")
            self.done(key, f"lane-{key}", head)
        self.heads = {"12": (5, sh("rev-parse", "origin/lane-12", cwd=self.clone)),
                      "13": (6, sh("rev-parse", "origin/lane-13", cwd=self.clone))}
        (self.records / "plan-history.md").write_text("x\nAcmeCorp moved\n")
        code, out, err = self.merge("12", "13")
        self.assertEqual((code, self.merges()), (1, []))
        self.assertEqual(err.strip().splitlines(), [
            "plan-history.md lines [2]: a deny-list name (lines only, never the name); "
            "nothing merged"])
        self.assertNotRegex((out + err).lower(), "acme")
        self.assertIn("fix what `ready` says, as for a deny-list name in a records file", out)
        (self.records / "plan-history.md").write_text("x\n")
        code, out, err = self.merge("12", "13")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.merges()), 2)


class ReadyTimeoutTests(Base):
    """Past its time budget ($RELAY_READY_SECONDS) ready stops looking things up, prints what it
    has, and names what it skipped."""

    def setUp(self):
        super().setUp()
        self.addCleanup(os.environ.pop, "RELAY_READY_SECONDS", None)
        self.heads = {k: self.branch(f"lane-{k}", content=f"{k}\n") for k in ("12", "13")}
        for k, head in self.heads.items():
            self.done(k, f"lane-{k}", head)
        (self.records / "briefs" / "20.md").write_text("Closes: #20\n")

    def timed_ready(self, seconds):
        os.environ["RELAY_READY_SECONDS"] = str(seconds)
        start = time.monotonic()
        out = self.ready()
        return out, time.monotonic() - start

    def test_a_lookup_that_times_out_skips_its_lanes_and_the_rest_still_prints(self):
        self.gh({"slow": {"pr list": 30}})
        out, took = self.timed_ready(3)
        self.assertLess(took, 20)
        self.assertIn("  12: done, lane-12 @", out)
        self.assertIn("  13: done, lane-13 @", out)
        self.assertIn("No status yet:\n  20: a brief but no status file", out)
        self.assertIn("Skipped:\n  lookups past ready's 3 s budget ($RELAY_READY_SECONDS): "
                      "lanes 12, 13\n  hint: the machine is likely busy", out)
        self.assertNotIn("Ready for PR", out)
        self.assertNotIn("lookup failed", out)
        self.assertNotIn("Nothing to do", out)

    def test_a_spent_budget_skips_every_lookup(self):
        calls = pathlib.Path(str(self.fake) + ".calls")
        calls.unlink(missing_ok=True)
        out, _ = self.timed_ready(0)
        self.assertFalse(calls.exists(), "gh was called after the budget ran out")
        self.assertIn("  12: done, lane-12 @", out)
        self.assertIn("No status yet:\n  20: a brief but no status file", out)
        skipped = next(ln for ln in out.splitlines() if ln.startswith("  lookups past"))
        for what in ("fetch", "Parents", "lanes 12, 13"):
            self.assertIn(what, skipped)

    def test_skipped_done_lanes_outside_now_are_counted_not_listed(self):
        (self.records / "plan.md").write_text(
            "# Plan\n\n## Now\n\n| Key | Issues |\n|---|---|\n| `12` | #12 |\n")
        out, _ = self.timed_ready(0)
        self.assertIn("  12: done, lane-12 @", out)
        self.assertNotIn("  13: done", out)
        self.assertIn("lane 12, 1 done lane not in plan.md's Now table", out)

    def test_within_budget_nothing_is_skipped(self):
        out, _ = self.timed_ready(60)
        self.assertNotIn("Skipped", out)
        self.assertIn("Ready for PR:\n  12: lane-12", out)

    def test_a_grandchild_holding_the_pipes_does_not_hold_run(self):
        # as git-remote-https outlives a killed `git fetch`; run waits 2 s for the pipes, no more
        child = self.tmp / "child.py"
        child.write_text("import subprocess, sys, time\n"
                         "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(40)'])\n"
                         "time.sleep(40)\n")
        driver = ("import sys, time; sys.path.insert(0, sys.argv[1]); import relay; "
                  "relay.deadline = time.monotonic() + 2; "
                  "print(relay.run([sys.executable, sys.argv[2]])[0])")
        start = time.monotonic()
        p = subprocess.run([sys.executable, "-c", driver, str(HERE.parent / "plugin" / "tools"),
                            str(child)], capture_output=True, text=True, timeout=60)
        self.assertEqual(p.stdout.strip(), str(relay.TIMED_OUT), p.stderr)
        self.assertLess(time.monotonic() - start, 20)

    def test_a_budget_that_is_not_seconds_is_a_usage_error(self):
        for bad in ("soon", "nan", "-1", "inf"):
            os.environ["RELAY_READY_SECONDS"] = bad
            code, _, err = self.call("ready", str(self.records))
            self.assertEqual(code, 2, bad)
            self.assertIn("RELAY_READY_SECONDS", err)

    def test_a_step_cut_off_midway_returns_its_fallback_and_drops_its_lines(self):
        out, skipped = {"relay.py": ["kept"], "Records": []}, []

        def step():  # one command in time, then one past the budget
            out["Records"].append("partial")
            relay.run(["git", "--version"])
            relay.deadline = time.monotonic()
            relay.run(["git", "--version"])
            return ["a wrong warning"]
        relay.deadline = time.monotonic() + 60
        try:
            got = relay.timed_step("relay.py check", out, skipped, [], step)
        finally:
            relay.deadline = None
        self.assertEqual(got, [])
        self.assertEqual(out, {"relay.py": ["kept"], "Records": []})
        self.assertEqual(skipped, ["relay.py check"])

    def test_parked_lanes_wait_while_parents_are_skipped(self):
        code, _, err = self.call("status", str(self.records), "20", "--state", "parked",
                                 "--doing", "waits")
        self.assertEqual(code, 0, err)
        out, _ = self.timed_ready(0)
        self.assertIn("20: parked; no GO while the Parents lookup is skipped", out)
        self.assertNotIn("Ready for GO", out)

    def test_other_commands_have_no_budget(self):
        os.environ["RELAY_READY_SECONDS"] = "0"
        self.assertEqual(relay.run(["git", "--version"])[0], 0)


class DraftCiCaseUsageHintTests(Base):
    """#130: ready flags a draft that differs from the open PR's body; waitchecks exit 3 names the
    ci-fallbacks.md case; an argparse usage error still prints waitchecks' and merge's hint."""

    waitchecks, QUEUED = WaitchecksTests.waitchecks, WaitchecksTests.QUEUED
    OK = [{"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"}]
    FAILED = WaitchecksTests.FAILED

    def open_pr(self, body, rollup=None):
        if not (self.records / "status" / "12.md").exists():
            self.head = self.branch("lane-12")
            self.done("12", "lane-12", self.head)
        self.gh({"prs": {"lane-12": [{"number": 5, "state": "OPEN", "headRefOid": self.head,
                                      "mergeable": "MERGEABLE", "body": body,
                                      "statusCheckRollup": rollup or self.OK}]}})

    def test_ready_flags_a_draft_that_differs_from_the_open_pr(self):
        self.open_pr("Closes #12\r\n\r\nBody.")
        self.assertIn(f"12: PR #5 --match-head-commit {self.head}", self.ready())
        self.open_pr("Closes #12\n\nOld body.\n")
        out = self.ready()
        draft = (self.records / "pr-bodies" / "12.md").as_posix()
        self.assertIn(f'Waiting:\n  12: PR #5 body differs from its draft: gh pr edit 5 '
                      f'--body-file "{draft}"', out)
        self.assertNotIn("Ready to merge", out)
        self.assertIn("hint: the draft changed after the PR opened", out)
        self.open_pr("Old body.", rollup=self.FAILED)
        out = self.ready()
        self.assertIn("12: PR #5 body differs from its draft", out)
        self.assertIn("12: PR #5 check failed: test", out)

    def test_runs_on_pull_request(self):
        yes = ["on: pull_request\n", "on: [push, pull_request]\n", "'on': pull_request\n",
               "on:\n  push:\n    branches: [main]\n  pull_request:\n    types: [opened]\n",
               "on:\n  - push\n  - pull_request\n", "name: ci\non:\n- pull_request\njobs: {}\n",
               "on:  # triggers\n  # a comment\n  pull_request: {}\n",
               "# header\non:\n# a comment\n  pull_request:\n", "on: [\n  push,\n  pull_request]\n",
               "﻿on: pull_request\n", "on: pull_request_target\n",
               "on:\n  pull_request_target:\n    types: [opened]\n"]
        no = ["on: push\n", "on: pull_request_review\n", "on: [push, workflow_dispatch]\n",
              "on:\n  push:\n    paths: [pull_request]\n", "on: push  # not pull_request\n",
              "on:\n  workflow_dispatch:\njobs:\n  pull_request:\n", "jobs: {}\n"]
        for text in yes:
            self.assertTrue(relay.runs_on_pull_request(text), text)
        for text in no:
            self.assertFalse(relay.runs_on_pull_request(text), text)

    def test_waitchecks_exit_3_names_the_ci_case(self):
        cases = (
            ({"workflow_files": {"ci.yml": "on: push\n", "pr.yaml": "on:\n  pull_request:\n"}},
             "a workflow on the default branch runs on a pull_request event "
             "(.github/workflows/pr.yaml): take *Checks not started*"),
            ({"workflow_files": {"ci.yml": "on: push\n", "notes.md": "on: pull_request\n"}},
             "no workflow on the default branch runs on a pull_request event "
             "(.github/workflows/ci.yml): take *CI cannot run*"),
            ({"workflows": 0, "head_statuses": 1},
             "no workflow file on the default branch (CI outside Actions): take *Checks not "
             "started*"),
            ({"workflows": 0}, "no CI configured: no Actions workflow and nothing reported on the "
             "default branch head: take *CI cannot run*"),
            ({"workflow_files": {"ci.yml": "on: pull_request"}, "broken": ["ci.yml"]},
             "workflow lookup failed"),
        )
        for data, line in cases:
            code, out, err = self.waitchecks(after=99, **data)
            self.assertEqual(code, 3, err)
            self.assertIn(f"no checks appeared on PR #5 within 6 minutes\n{line}", out)
            self.assertTrue(out.rstrip().endswith("hint (exit 3): no checks appeared: take the "
                                                  "`ci-fallbacks.md` case the line above names"))
        with mock.patch.object(relay, "no_ci", lambda repo: False), \
                mock.patch.object(relay, "gh", lambda *a: {"type": "file", "name": "workflows"}):
            self.assertIn("no workflow file", relay.ci_case("o/r"))  # .github/workflows a file

    def usage(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err), self.assertRaises(SystemExit) as e:
            relay.main(list(argv))
        return e.exception.code, out.getvalue(), err.getvalue()

    def test_usage_errors_print_the_exit_2_hint(self):
        for argv in (("waitchecks", str(self.records), "five"),
                     ("waitchecks", str(self.records), "5", "--bogus"),
                     ("merge", str(self.records))):
            code, out, err = self.usage(*argv)
            self.assertEqual(code, 2)
            self.assertIn("usage:", err)
            self.assertEqual(out, f"hint (exit 2): {relay.EXIT_HINTS[argv[0]][2]}\n")
        self.assertEqual(self.usage("ready")[:2], (2, ""))
        code, out, _ = self.usage("waitchecks", "--help")
        self.assertEqual(code, 0)
        self.assertNotIn("hint (exit", out)


class LaneKindTests(Base):
    """Now-table lane kinds `run`, `audit` and `spare` close no issue and open no PR, so `ready`
    does not flag them for one; plan.md's Main checkout names the lane holding it (#116)."""

    def plan(self, rows, checkout="none"):
        (self.records / "plan.md").write_text(
            "# Plan\n\n## Now\n\n| Key | Kind | Issues | Session | State | Parked until |\n"
            "|---|---|---|---|---|---|\n" + "".join(f"| {k} | {kind} | - | s | started | - |\n"
                                                for k, kind in rows)
            + f"\n**Main checkout:** {checkout}\n\n## Roadmap\n\n| Issue |\n|---|\n| #9 |\n")

    def done_no_pr(self, key):
        """A done lane like the live records' lane 110: an audit whose branch was never pushed
        and that has no PR body draft."""
        (self.records / "reports" / f"{key}.md").write_text("report")
        code, _, err = self.call("status", str(self.records), key, "--state", "done", "--doing",
                                 "x", "--branch", f"claude/lane-{key}-x", "--head", "02d1f2d")
        self.assertEqual(code, 0, err)

    def test_now_kinds_reads_the_kind_column(self):
        self.plan([("12", "`run`"), ("13", "Audit"), ("14", ""), ("15", "pr"), ("s1", "spare")])
        self.assertEqual(relay.now_kinds(self.records / "plan.md"),
                         {"12": "run", "13": "audit", "14": "pr", "15": "pr", "s1": "spare"})
        self.assertEqual(relay.now_keys(self.records / "plan.md"), {"12", "13", "14", "15", "s1"})
        (self.records / "plan.md").write_text(  # no Kind column: every lane is `pr`
            "# Plan\n\n## Now\n\n| Key | Issues |\n|---|---|\n| 12 | #12 |\n")
        self.assertEqual(relay.now_kinds(self.records / "plan.md"), {"12": "pr"})

    def test_each_no_pr_kind_is_not_flagged_for_a_missing_pr_or_issue(self):
        for kind in ("run", "audit", "spare"):
            with self.subTest(kind=kind):
                self.plan([("110", kind)])
                self.done_no_pr("110")
                out = self.ready()
                self.assertNotIn("Inconsistent:", out)
                self.assertNotIn("Ready for PR:", out)
                self.assertIn(f"Finished:\n  110: {kind} done, no PR: read reports/110.md", out)

    def test_a_pr_lane_is_still_flagged_for_a_missing_pr(self):
        self.plan([("110", "pr")])
        self.done_no_pr("110")
        self.assertIn("Inconsistent:\n  110: status head 02d1f2d is not the pushed head "
                      "(branch not pushed)", self.ready())

    def test_a_no_pr_lane_moved_out_of_now_is_left_out(self):
        self.plan([])  # lane 110 today: done and moved out of Now, so its kind is unknown
        self.done_no_pr("110")
        out = self.ready()
        self.assertNotIn("110", out)
        self.assertIn("  (1 finished, no-PR lane not in plan.md's Now table left out)", out)
        (self.records / "reports" / "110.md").unlink()  # no report: still flagged
        self.assertIn("110: status head 02d1f2d is not the pushed head", self.ready())

    def test_a_moved_lane_with_a_pushed_branch_is_still_flagged(self):
        self.plan([])
        head = self.branch("lane-12")
        self.done("12", "lane-12", head)
        self.assertIn("Ready for PR:\n  12: lane-12", self.ready())

    def test_a_no_pr_lane_still_needs_its_report(self):
        self.plan([("12", "run")])
        self.done_no_pr("12")
        (self.records / "reports" / "12.md").unlink()
        out = self.ready()
        self.assertIn("Inconsistent:\n  12: done with no report file", out)
        self.assertNotIn("Finished:", out)

    def test_a_parked_spare_is_available(self):
        self.plan([("s1", "spare"), ("13", "pr")])
        for key in ("s1", "13"):
            self.call("status", str(self.records), key, "--state", "parked", "--doing", "parked")
        out = self.ready()
        self.assertIn("Waiting:\n  s1: spare, available: waits for a brief", out)
        self.assertIn("hint: a spare needs nothing until a lane needs a worker", out)
        self.assertNotIn("s1: parked with no brief", out)
        self.assertNotIn("s1: a spare", out)
        self.assertNotIn("GO #s1", out)
        self.assertIn("13: parked with no brief", out)  # a normal lane still is flagged
        # given a brief and its lane's kind, the spare is a parked lane like any other
        self.plan([("s1", "pr")])
        (self.records / "briefs" / "s1.md").write_text("Depends on: none\n")
        self.assertIn("s1: send `GO #s1`", self.ready())

    def test_a_spare_with_a_brief_but_kind_spare_is_flagged(self):
        # the coordinator wrote its brief but left the Kind: as `spare` it would finish with no PR
        self.plan([("s1", "spare")])
        (self.records / "briefs" / "s1.md").write_text("Depends on: none\n- **Closes:** #13\n")
        self.call("status", str(self.records), "s1", "--state", "parked", "--doing", "parked")
        out = self.ready()
        self.assertIn("Inconsistent:\n  s1: a spare with a brief: set its Now Kind", out)
        self.assertNotIn("available", out)
        self.assertNotIn("GO #s1", out)
        self.call("status", str(self.records), "s1", "--state", "blocked", "--doing", "which?",
                  "--branch", "lane-s1", "--head", "02d1f2d")
        out = self.ready()
        self.assertIn("s1: a spare with a brief", out)
        self.assertIn("s1: blocked: which?", out)
        self.done("s1", "lane-s1", self.branch("lane-s1"), body="Closes #13\n\nBody.\n")
        out = self.ready()  # done, it is checked as the `pr` lane it took
        self.assertIn("s1: a spare with a brief", out)
        self.assertIn("Ready for PR:\n  s1: lane-s1", out)
        self.assertNotIn("Finished:", out)

    def test_go_turns_a_spare_into_its_lane(self):
        """GO #s1 after its brief and Kind are written: the spare is lane s1 for issue #13, with
        its own key, branch and status file, checked like any `pr` lane."""
        self.gh({"issues": {"13": ["OPEN", None]}})
        self.plan([("s1", "pr")])
        (self.records / "briefs" / "s1.md").write_text("Depends on: none\n- **Closes:** #13\n")
        self.call("status", str(self.records), "s1", "--state", "parked", "--doing", "spare")
        self.assertIn("Ready for GO:\n  s1: send `GO #s1`", self.ready())
        head = self.branch("claude/lane-s1-ab12cd")
        self.done("s1", "claude/lane-s1-ab12cd", head, body="Closes #12\n\nBody.\n")
        self.assertIn("s1: PR body", self.ready())  # checked against the brief's Closes line
        self.done("s1", "claude/lane-s1-ab12cd", head, body="Closes #13\n\nBody.\n")
        out = self.ready()
        self.assertIn("Ready for PR:\n  s1: claude/lane-s1-ab12cd", out)
        self.assertNotIn("Inconsistent:", out)
        self.assertNotIn("Finished:", out)

    def test_a_spare_never_given_a_brief_closes_out(self):
        """Told `CLOSE #s1`, a spare writes its report and `done` with no branch or head (its
        worktree may sit on the pushed default branch): Finished in Now, and left out once moved
        to plan-history.md."""
        self.plan([("s1", "spare")])
        (self.records / "reports" / "s1.md").write_text("Spare, never given a lane.\n")
        code, _, err = self.call("status", str(self.records), "s1", "--state", "done",
                                 "--branch", "none", "--head", "none",
                                 "--doing", "spare closed out, no lane")
        self.assertEqual(code, 0, err)
        out = self.ready()
        self.assertIn("Finished:\n  s1: spare done, no PR: read reports/s1.md", out)
        self.assertNotIn("Inconsistent:", out)
        self.plan([])
        out = self.ready()
        self.assertNotIn("s1", out)
        self.assertIn("(1 finished, no-PR lane not in plan.md's Now table left out)", out)

    def test_an_unknown_kind_is_flagged(self):
        self.plan([("12", "audits")])
        self.assertRegex(self.ready(), r"plan\.md line \d+: Now kind `audits` for 12 is not "
                                       r"one of pr, run, audit, spare")

    def test_main_checkout_held_by_a_lane_not_in_now_is_flagged(self):
        self.plan([("12", "run")], checkout="12 (benchmark data)")
        self.assertNotIn("Main checkout", self.ready())
        self.plan([("12", "run")], checkout="none")
        self.assertNotIn("Main checkout", self.ready())
        self.plan([("12", "run")], checkout="`13`")
        out = self.ready()
        self.assertRegex(out, r"plan\.md line \d+: Main checkout names lane 13, which is not in "
                              r"Now")
        self.assertIn("hint: a Main checkout holder not in Now: release it", out)


if __name__ == "__main__":
    unittest.main()
