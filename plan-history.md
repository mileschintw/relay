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
