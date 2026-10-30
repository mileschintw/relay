"""A stand-in for `gh` that answers the calls relay.py makes from a JSON file ($RELAY_FAKE_GH).

{"repo": "o/r",
 "blocked_by": {"12": [11]},
 "issues": {"10": ["OPEN", null], "11": ["CLOSED", "COMPLETED"]},
 "children": {"10": ["11"]},
 "bodies": {"10": "## Files\\n\\n- a.py\\n"},
 "broken": ["/sub_issues"],
 "prs": {"<branch>": [{"number": 5, "state": "OPEN", "headRefOid": "<sha>",
                       "mergeable": "MERGEABLE", "statusCheckRollup": [...]}]},
 "jobs": {"<job id>": {"steps": [...]}},          # a missing job ran one step
 "annotations": {"<job id>": [{"message": "..."}]}}
children: an issue's sub-issues. bodies: issue bodies (default empty).
broken: a call with an argument containing one of these fails.
`pr comment <N> --body-file <f>` appends `#<N>` and the body to $RELAY_FAKE_GH.comments.
"""
import json
import os
import sys

data = json.load(open(os.environ["RELAY_FAKE_GH"], encoding="utf-8"))
a = sys.argv[1:]
issues = data.get("issues", {})
children = data.get("children", {})


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
                              "body": data.get("bodies", {}).get(n, ""),
                              "sub_issues_summary": {"total": len(kids), "completed": done}}))
elif a[0] == "api" and any("/sub_issues" in x for x in a):
    n = next(x for x in a if "/sub_issues" in x).split("/")[-2]
    for c in children.get(n, []):
        print(json.dumps({k: v for k, v in rest(c).items() if k != "number"}))
elif a[:2] == ["issue", "view"]:
    if a[2] not in data.get("issues", {}):
        sys.exit(f"issue {a[2]} not found")
    state, reason = data["issues"][a[2]]
    print(json.dumps({"state": state, "stateReason": reason}))
elif a[:2] == ["pr", "list"]:
    print(json.dumps(data.get("prs", {}).get(a[a.index("--head") + 1], [])))
elif a[0] == "api" and "/actions/jobs/" in a[1]:
    print(json.dumps(data.get("jobs", {}).get(a[1].split("/")[-1], {"steps": [{"name": "Run"}]})))
elif a[0] == "api" and a[1].endswith("/annotations"):
    print(json.dumps(data.get("annotations", {}).get(a[1].split("/")[-2], [])))
elif a[:2] == ["pr", "comment"]:
    body = open(a[a.index("--body-file") + 1], encoding="utf-8").read()
    with open(os.environ["RELAY_FAKE_GH"] + ".comments", "a", encoding="utf-8") as f:
        f.write(f"#{a[2]}\n{body}\n")
    print(f"https://github.com/{data['repo']}/pull/{a[2]}#issuecomment-1")
else:
    sys.exit(f"fake gh: unhandled {a}")
