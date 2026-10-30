"""A stand-in for `gh` that answers the calls relay.py makes from a JSON file ($RELAY_FAKE_GH).

{"repo": "o/r",
 "blocked_by": {"12": [11]},
 "issues": {"11": ["CLOSED", "COMPLETED"]},
 "prs": {"<branch>": [{"number": 5, "state": "OPEN", "headRefOid": "<sha>",
                       "mergeable": "MERGEABLE", "statusCheckRollup": [...]}]},
 "jobs": {"<job id>": {"steps": [...]}},          # a missing job ran one step
 "annotations": {"<job id>": [{"message": "..."}]}}
`pr comment <N> --body-file <f>` appends `#<N>` and the body to $RELAY_FAKE_GH.comments.
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
