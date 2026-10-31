You are the relay coordinator for mileschintw/relay. Session worktree D:\Repos\relay\.claude\worktrees\relay-coordinate-5b7cc3, id local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22, mode normal. Talk to the user in Traditional Chinese; write repo files, issues, briefs and the plan in English.

Merge right: per lane, only on the user's yes to "open the PR and merge once CI passes".

Files over summary. Reread now, and trust them over this summary:
- C:\Users\user3\.claude\plugins\cache\relay\relay\0.3.0\skills\coordinate\SKILL.md (relay 0.3.0; the Skill tool may still load an older copy until a restart, so read this path) and its app-limits.md.
- D:\Repos\relay-coord\project.md (its `relay.py:` line: run relay.py from the main checkout D:/Repos/relay with `py -3 -I`; fast-forward that checkout after each merge).
- D:\Repos\relay-coord\plan.md: Handover (standing instruction), Now (empty), Roadmap (#45–#51 with Files and overlaps; #45 blocked by #51), Waiting for the user's decision.

In flight: nothing. No workers, no background commands, no question pending. 0.3.0 is released (tag relay--v0.3.0 = 1d023cd).

Next: the user said 「我compact完再接著直接繼續解issue」, the go-ahead for the whole frontier. In the first turn they type after the compact:
1. Run `relay.py ready` and `relay.py roadmap --repo mileschintw/relay`; check the Roadmap still matches open issues.
2. Write briefs/<key>.md for 46, 47, 48, 49, 50, 51 and 45 from briefs/_template.md, naming shared files' owners per the Roadmap's overlap line (#46 and #47 each add one check in `cmd_ready`; #45 and #51 both edit coordinate SKILL.md step 4). Brief 45 says `Depends on: #51`.
3. Start all seven lanes in that same turn (start_session, user_asked, fresh, use_worktree true, source_branch main, branch_name lane-<key>), 45 parked until GO #45. If it refuses (Remote Control), say so and wait for a desktop-app message. Check each cwd with list_sessions until `starting` is gone.
4. Fill Now, commit and push the records, set the 20-minute alarm.
