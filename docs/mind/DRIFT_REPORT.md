# git mind — Drift Report (initial)

Purpose: track gaps between vision and current implementation, plus conflicts.

Positive drift
- Ref-native snapshot engine under refs/mind/sessions/** landed early
- JSONL serve scaffold live; PR list/select wired to adapters

Negative drift / Gaps
- Policy projection (public vs private) not implemented yet (spec ready)
- No thread iteration/resolve/reply yet (adapters available)
- No LLM verbs yet (debug/real template pending)
- No artifact depot or mind remote commands yet
- No locks/consensus yet; hooks/CI to be added

Decisions pending
- Ledger integration (ledger-kernel/libgitledger): what to store where (approvals attestations?)
- go-job-system mapping: finalize descriptor/claim/result shapes and ref layout

Next steps
- Finish JSONL tests; add policy projection; thread verbs; debug LLM
