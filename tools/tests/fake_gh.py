"""A stand-in for `gh` that answers the calls relay.py makes from a JSON file ($RELAY_FAKE_GH).

{"repo": "o/r",
 "blocked_by": {"12": [11]},
 "issues": {"11": ["CLOSED", "COMPLETED"], "12": ["CLOSED", "COMPLETED", []]},
 "prs": {"<branch>": [{"number": 5, "state": "OPEN", "headRefOid": "<sha>",
                       "mergeable": "MERGEABLE", "statusCheckRollup": [...]}]}}
An issue's optional third item lists the PRs that closed it (default [99] when closed).
"""
import json
import os
import sys

data = json.load(open(os.environ["RELAY_FAKE_GH"], encoding="utf-8"))
a = sys.argv[1:]
if a[:2] == ["repo", "view"]:
    print(json.dumps({"nameWithOwner": data["repo"]}))
elif a[0] == "api" and a[1].endswith("/dependencies/blocked_by"):
    n = a[1].split("/")[-3]
    print(json.dumps([{"number": b} for b in data.get("blocked_by", {}).get(n, [])]))
elif a[:2] == ["issue", "view"]:
    if a[2] not in data.get("issues", {}):
        sys.exit(f"issue {a[2]} not found")
    state, reason, *prs = data["issues"][a[2]]
    refs = [{"number": n} for n in (prs[0] if prs else ([99] if state == "CLOSED" else []))]
    print(json.dumps({"state": state, "stateReason": reason, "closedByPullRequestsReferences": refs}))
elif a[:2] == ["pr", "list"]:
    print(json.dumps(data.get("prs", {}).get(a[a.index("--head") + 1], [])))
else:
    sys.exit(f"fake gh: unhandled {a}")
