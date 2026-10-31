"""A stand-in for `gh` that answers the calls relay.py makes from a JSON file ($RELAY_FAKE_GH).

{"repo": "o/r",
 "blocked_by": {"12": [11]},
 "issues": {"10": ["OPEN", null], "11": ["CLOSED", "COMPLETED"]},
 "children": {"10": ["11"]},
 "bodies": {"10": "issue body"},
 "comments": {"10": [{"body": "...", "html_url": "https://..."}]},
 "broken": ["/sub_issues"],
 "prs": {"<branch>": [{"number": 5, "state": "OPEN", "headRefOid": "<sha>",
                       "mergeable": "MERGEABLE", "statusCheckRollup": [...]}]},
                                                  # `pr list --head <branch>`; without --head,
                                                  # every PR with its headRefName, cut at --limit
 "jobs": {"<job id>": {"steps": [...]}},          # a missing job ran one step
 "annotations": {"<job id>": [{"message": "..."}]},
 "workflows": 0,                                  # the repo's Actions workflow count, default 1
 "head_statuses": 1, "head_check_runs": 1,      # counts on the default branch head, default 0
 "pr_checks": {"5": {"after": 3, "rollup": [...]}},  # `pr view 5`'s statusCheckRollup: empty
                                                  # before its 3rd call (default 1st), then rollup
 "watch": {"5": [1, "output"]},                   # `pr checks 5 --watch`: exit code and output
 "pr_view": {"5": {"headRefOid": "<sha>", "mergeStateStatus": "CLEAN", "baseRefName": "main",
                   "mergedAt": "<time>", "mergeCommit": {"oid": "<sha>"}}},  # other `pr view 5`
 "merge_fail": {"5": "message"},                  # `pr merge 5` exits 1 with this message
 "runs": [{"databaseId": 9, "status": "queued"}]} # `run list`'s answer, default []
children: an issue's sub-issues. bodies, comments: an issue's body and comments.
broken: a call with an argument containing one of these fails.
`pr comment <N> --body-file <f>` appends `#<N>` and the body to $RELAY_FAKE_GH.comments.
Every call appends its arguments, one line, to $RELAY_FAKE_GH.calls.
"""
import json
import os
import sys

data = json.load(open(os.environ["RELAY_FAKE_GH"], encoding="utf-8"))
a = sys.argv[1:]
issues = data.get("issues", {})
children = data.get("children", {})
with open(os.environ["RELAY_FAKE_GH"] + ".calls", "a", encoding="utf-8") as f:
    f.write(" ".join(a) + "\n")


def rest(n):
    state, reason = issues[n]
    return {"number": int(n), "state": state.lower(), "state_reason": (reason or "").lower() or None}


if any(b in x for b in data.get("broken", []) for x in a):
    sys.exit(f"fake gh: broken {a}")
if a[:2] == ["repo", "view"]:
    print(json.dumps({"nameWithOwner": data["repo"]}))
elif a[0] == "api" and a[1].endswith("/dependencies/blocked_by"):
    n = a[1].split("/")[-3]
    print(json.dumps([rest(str(b)) if str(b) in issues else {"number": b}
                      for b in data.get("blocked_by", {}).get(n, [])]))
elif a[0] == "api" and any("/issues?state=open" in x for x in a):
    for n, (state, _) in issues.items():
        if state == "OPEN":
            kids = [rest(c) for c in children.get(n, [])]
            done = sum(k["state_reason"] == "completed" for k in kids)
            print(json.dumps({"number": int(n), "title": f"issue {n}",
                              "body": data.get("bodies", {}).get(n),
                              "html_url": f"https://github.com/{data['repo']}/issues/{n}",
                              "sub_issues_summary": {"total": len(kids), "completed": done}}))
elif a[0] == "api" and any("/comments" in x for x in a):
    n = next(x for x in a if "/comments" in x).split("/")[-2]
    for c in data.get("comments", {}).get(n, []):
        print(json.dumps(c))
elif a[0] == "api" and any("/sub_issues" in x for x in a):
    n = next(x for x in a if "/sub_issues" in x).split("/")[-2]
    for c in children.get(n, []):
        print(json.dumps({k: v for k, v in rest(c).items() if k != "number"}))
elif a[:2] == ["issue", "view"]:
    if a[2] not in data.get("issues", {}):
        sys.exit(f"issue {a[2]} not found")
    state, reason = data["issues"][a[2]]
    print(json.dumps({"state": state, "stateReason": reason}))
elif a[:2] == ["pr", "list"] and "--head" in a:
    print(json.dumps(data.get("prs", {}).get(a[a.index("--head") + 1], [])))
elif a[:2] == ["pr", "list"]:
    prs = [{"headRefName": b, **p} for b, ps in data.get("prs", {}).items() for p in ps]
    print(json.dumps(prs[:int(a[a.index("--limit") + 1])]))
elif a[0] == "api" and "/actions/jobs/" in a[1]:
    print(json.dumps(data.get("jobs", {}).get(a[1].split("/")[-1], {"steps": [{"name": "Run"}]})))
elif a[0] == "api" and a[1].endswith("/actions/workflows"):
    n = data.get("workflows", 1)
    print(json.dumps({"total_count": n, "workflows": [{"name": f"ci{i}"} for i in range(n)]}))
elif a[0] == "api" and a[1].endswith("/commits/HEAD/status"):
    print(json.dumps({"total_count": data.get("head_statuses", 0)}))
elif a[0] == "api" and a[1].endswith("/commits/HEAD/check-runs"):
    print(json.dumps({"total_count": data.get("head_check_runs", 0)}))
elif a[0] == "api" and a[1].endswith("/annotations"):
    print(json.dumps(data.get("annotations", {}).get(a[1].split("/")[-2], [])))
elif a[:2] == ["pr", "view"] and "statusCheckRollup" in a:
    if a[2] not in data.get("pr_checks", {}):
        sys.exit(f"no pull requests found for {a[2]}")
    pc = data["pr_checks"][a[2]]
    calls = open(os.environ["RELAY_FAKE_GH"] + ".calls", encoding="utf-8").read().splitlines()
    seen = sum(c.startswith(f"pr view {a[2]} ") for c in calls)
    print(json.dumps({"statusCheckRollup": pc["rollup"] if seen >= pc.get("after", 1) else []}))
elif a[:2] == ["pr", "checks"] and "--watch" in a:
    code, output = data.get("watch", {}).get(a[2], [0, "all checks passed"])
    print(output)
    sys.exit(code)
elif a[:2] == ["pr", "view"]:
    if a[2] not in data.get("pr_view", {}):
        sys.exit(f"no pull requests found for {a[2]}")
    print(json.dumps(data["pr_view"][a[2]]))
elif a[:2] == ["pr", "merge"]:
    if a[2] in data.get("merge_fail", {}):
        sys.exit(data["merge_fail"][a[2]])
    print(f"merged pull request #{a[2]}")
elif a[:2] == ["run", "list"]:
    print(json.dumps(data.get("runs", [])))
elif a[:2] == ["pr", "comment"]:
    body = open(a[a.index("--body-file") + 1], encoding="utf-8").read()
    with open(os.environ["RELAY_FAKE_GH"] + ".comments", "a", encoding="utf-8") as f:
        f.write(f"#{a[2]}\n{body}\n")
    print(f"https://github.com/{data['repo']}/pull/{a[2]}#issuecomment-1")
else:
    sys.exit(f"fake gh: unhandled {a}")
