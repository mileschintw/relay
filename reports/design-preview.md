# design-preview: social preview, README banner, About and topics

- Branch: `claude/nice-galileo-556006`. Lane 119 took the Clay & Ink assets into main with #157.
- Follow-up: https://github.com/mileschintw/relay/pull/158 (head `40002cd`, open). It switches the background to GitHub Dark and makes the banner transparent outside its card. Only these three files change; README needs nothing.
- Assets, same layout as career-log:
  - `docs/social-preview/social-preview.svg` (source)
  - `docs/social-preview/social-preview.png` (1280x640; the user uploads it in Settings > General > Social preview, no API)
  - `docs/social-preview/banner.svg` (1280x200, same design, for the top of README.md)
- Design: a coordinator box (plan, briefs, status, reports) on `main`; lanes #12 and #14 branch off, run their stations and a PR, and merge back interleaved; lane #15 is parked (dashed) until #12 merges and a GO arrow starts it. Clay & Ink colours (coral coordinator, amber/teal/rose lanes) on a GitHub Dark background after #158.
- Tagline (in the images): "One Claude Code session coordinates many worker sessions."

## For lane 119 (README)

Take the assets from this branch (for example `git checkout origin/claude/nice-galileo-556006 -- docs/social-preview`) and put the banner at the top of README.md, as career-log does:

```markdown
![relay: one Claude Code session coordinates many worker sessions](docs/social-preview/banner.svg)
```

`docs/getting-started.md` still says "The repo is private"; the repo is public now. Not changed here.

## About and topics: applied (user said yes in this session)

- Description: "Claude Code plugin that runs parallel Claude Code sessions on one GitHub repo: one coordinator session plans the work and starts a worker session per issue, each in its own git worktree, and asks before every start, PR and merge."
- Website: empty
- Topics (20): claude-code, claude-code-plugin, claude, anthropic, ai-agents, coding-agents, multi-agent, agent-fleet, agent-orchestration, orchestration, parallel-agents, parallel-sessions, git-worktree, worktrees, ai-coding, developer-tools, github-issues, human-in-the-loop, workflow-automation, mattpocock-skills
- Social preview image: not uploaded yet. Once #158 is merged, the user uploads `docs/social-preview/social-preview.png` by hand.
