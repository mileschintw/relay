# A test session on another machine

For a session the user started on another machine (a Remote Control session), to run a test this machine cannot. It reports nothing back on its own, and its messages arrive cut short.

1. Reach it by its `ListAgents` name with `SendMessage`. Ask it to send its report in numbered parts (1/N, 2/N, …), each short enough to arrive whole.
2. On each wake, check its state in `ListAgents`. Idle or offline before every part arrived: ask it to resend the missing parts by number.
3. Keep the alarm running (*Following progress* in `SKILL.md`) until all parts are in.
4. Save the parts, in order, as `reports/<key>.md`.

Check: every part from 1 to N is in `reports/<key>.md`.
