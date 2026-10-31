# Plan history

Finished work moved out of `plan.md`, newest first, for checking only; the plan is the source for anything current. Each block names when it moved and the coordinator that moved it.

## 2026-10-30 16:40 -0700, wave 1 merges (coordinator local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22)

| Key | Issue | Session | Branch @ head | PR | Merge |
|---|---|---|---|---|---|
| 10 | #10 Quiet notes | local_7c15cfb3-aec1-478e-94a2-d299ce83092c | claude/lane-10-700d4c @ 4ce4782 | #13 | e386c0b |
| 8 | #8 Session cwd check; archive rule | local_9e8221b7-77e6-4302-86d2-c4718149667c | claude/lane-8-2f7128 @ b4b818e | #14 | merged |
| 9 | #9 Drop Last updated; records encoding check | local_a3b2b8ca-87e8-4f47-aceb-469820317bbd | claude/lane-9-0742ae @ fbf1622 | #15 | merged |

- Repo has no CI: user's "Open and merge both", then 「本機檢查通過就合併」 / 「開 PR，本機檢查過就合併」. The coordinator ran `py -3 -I tests/test_relay.py` and `claude plugin validate .` on each head merged onto the then-current main before each merge: all passed (20, 20, 24 tests).
- Records `project.md` Deny list changed `none.` → `none` (16:40) as a workaround for #11, filed the same time.
- Live `plan.md` dropped its `Last updated:` line after #9 merged.
- Lane 9 filed #12; lane 8 noted `unattended.md:7` could point at app-limits.md › Session folders (not filed).

## 2026-10-30 16:47 -0700, lane 1 merged (coordinator local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22)

| Key | Issue | Session | Branch @ head | PR |
|---|---|---|---|---|
| 1 | #1 Parents, never lanes | local_1579b864-86a9-486d-90c2-506674ab72a7 | claude/lane-1-6a0c93 @ a0c9377 | #17 |

- No CI: user chose 「開 PR，本機檢查過就合併」; coordinator ran tests (28 OK) and plugin validate on a0c9377 merged onto main before merging. GO #2, GO #3 sent 16:47; lane 7 asked to resolve its conflict with lane 1.

## 2026-10-30 16:52 -0700, lane 11 merged (coordinator local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22)

| Key | Issue | Session | Branch @ head | PR |
|---|---|---|---|---|
| 11 | #11 Deny list `none.` | local_68c615d2-7e40-43ab-82da-77985a357b61 | claude/lane-11-f4e84e @ 75435e4 | #18 |

- No CI: user chose 「開 PR，本機檢查過就合併」; coordinator ran tests (29 OK) and plugin validate on 75435e4 merged onto main.

## 2026-10-30 16:53 -0700, lane 7 merged (coordinator local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22)

| Key | Issue | Session | Branch @ head | PR |
|---|---|---|---|---|
| 7 | #7 `relay.py localcheck` | local_96015864-484e-43fd-ba63-f56257c25613 | claude/lane-7-51e899 @ 40eb713 | #19 |

- Resolved its conflict with lane 1 at 40eb713. User's 「解完衝突、本機檢查過就合併」; coordinator ran tests (40 OK) and plugin validate on 40eb713 merged onto main.
- Lane 16's Actions billing block cleared after the repo was made public (16:50, per lane 16's status); user had said 「我讓他重試了」.

## 2026-10-30 17:02 -0700, lanes 16 and 3 merged (coordinator local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22)

| Key | Issue | Session | Branch @ head | PR |
|---|---|---|---|---|
| 16 | #16 CI workflow | local_2fe47f57-11a8-4d72-a4e7-2c91bd1aa81c | claude/lane-16-3bf73f @ a907962 | #20 |
| 3 | #3 Owner notes; hand back when roadmap empties | local_9bd0484c-821d-4349-9663-678666c9e033 | claude/lane-3-af9107 @ f1f09a5 | #21 |

- User's "Open and merge both" (16:58). First merges with real CI: #20 and #21 each passed test (ubuntu, windows) and validate. Rulings on local-check merges are no longer needed from here.

## 2026-10-30 17:07 -0700, lane 2 merged (coordinator local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22)

| Key | Issue | Session | Branch @ head | PR |
|---|---|---|---|---|
| 2 | #2 `## Files` section; `relay.py roadmap` | local_fb37449e-58c9-49eb-b7f4-6878eebd3515 | claude/lane-2-ccd448 @ be6fc5e | #22 |

- User's "Yes, open and merge" (17:02). Resolved conflicts with #21 first; CI passed (test ubuntu/windows, validate). Wave 1 and its follow-ups are all merged; only #12 stays open.

## 2026-10-30 17:18 -0700, lane 12 merged; roadmap empty (coordinator local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22)

| Key | Issue | Session | Branch @ head | PR |
|---|---|---|---|---|
| 12 | #12 Invalid UTF-8 in a status file | local_8cddf2c9-12f8-4e80-96eb-5eef2ee11d86 | claude/lane-12-c970f3 @ 998541a | #23 |

- #12 triaged by the coordinator on the user's "Triage and start #12" (17:08): labels `ready-for-agent`, `bug`; Triage and Files sections added. User's "Open and merge" (17:16); CI passed.
- Ruling 1 moved here (ended with #16's CI): "The repo has no CI. For lanes 8, 9 and 10 the user chose 「本機檢查通過就合併」 and, for lane 9, 「開 PR，本機檢查過就合併」: merge after the coordinator runs project.md's checks on the PR head merged onto current main." Also applied, each on its own yes, to lanes 1, 7, 11.

## 2026-10-30 17:33 -0700, release 0.2.0 (coordinator local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22)

- User: 「把wave1結束的版本發成0.2.0，接著更新這個coordinator到新release」. PR #32 raised `version` to 0.2.0 (CI passed), `git push origin main:release` fast-forwarded 3dbe963..fa817ff, tag `relay--v0.2.0` pushed.
- Installed plugin: `claude plugin marketplace update relay`; `claude plugin update relay@relay --scope local` failed over SSH (host key) and worked with a one-command HTTPS rewrite (`GIT_CONFIG_*` env, no config change). That updated the main checkout's local install only; the coordinator worktree's entry in `~/.claude/plugins/installed_plugins.json` was pointed at the 0.2.0 copy by hand (backup `installed_plugins.json.bak-relay-0.2.0`). Other worktrees' entries (lane sessions, lancet, career-log) stay 0.1.0.
- The marketplace's `"url": "mileschintw/relay"` resolved to SSH on this machine: worth a note if it recurs.

## 2026-10-30 17:56 -0700, wave 2 merged (coordinator local_75cc31e5-4bd1-45b1-92a6-8c63fa48ec22)

- Go-ahead 「開始wave2」 (17:37); merge right 「開 PR，CI 過就合併」. Merged one at a time, CI green on each: #34 lane 27 (17:51), #35 lane 28 (17:52), #36 lane 29 (17:53), #37 lane 30 (17:53), #38 lane 24 (17:54), #39 lane 26 (17:55), #40 lane 25 (17:56).
- Sessions: 24 local_8223afdd, 25 local_a390b9b2, 26 local_49c6f09b, 27 local_c8055d4a, 28 local_644f77a7, 29 local_c0e33f80, 30 local_4a03addc. Lane 25 filed #33. GO #31 sent after #35.
