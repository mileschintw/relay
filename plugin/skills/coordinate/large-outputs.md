# Verifying a large output

For a lane whose product is a large document (an inventory, an audit, a list of hundreds of rows). A whole-document review does not converge on it: each round reads different parts first, so new findings are first reads, not regressions. Instead, add one line to the brief's *Lane tests*: "Verify as `<absolute path of this file>` says." The worker follows the steps below.

1. **Machine-readable rows.** The output also comes as a TSV, one row per item: file, line(s), a short verbatim quote from the source (10–40 characters), kind, proposal, batch.
2. **Scripts** (in the worker's scratchpad), run at the base commit, output in the report:
   - *completeness*: every heading and numbered rule or step of each in-scope file has a row or an explicit "left out, on purpose";
   - *accuracy*: each row's quote appears at its file:line (±2);
   - *bookkeeping*: every row belongs to a batch, and the batch dependency graph has no cycle.
   Each prints its gaps; the worker closes them.
3. **Judgement review, sliced.** Fresh read-only subagents in parallel, each given one file (or a few small ones), its rows and the base, never the worker's reasoning. One pass. A blocker is only a wrong judgement, a proposal that would change behaviour, or a mis-split batch; the rest are listed.
4. **One page for the user:** per batch, what it does, its size, what it waits for, its order. The user approves this page, not the full table.
5. The output is a map, not a spec: each lane that implements a batch re-verifies its rows against the default branch of its day. Say so on the page.
