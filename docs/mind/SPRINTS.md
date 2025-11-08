# git mind — Sprints

Cadence: 1-week sprints. v0.1 targets JSONL API + PR/Thread flows + debug LLM.

## Sprint 0 — Snapshot Engine + JSONL (this week)
- Snapshot commits under refs/mind/sessions/* with trailers (done)
- JSONL server: hello, state.show, repo.detect, pr.list, pr.select (in progress)
- Policy skeleton + attr mapping (next)

## Sprint 1 — PR & Threads
- pr list/select/info; thread list/select/show; state selection
- Human: fzf pickers; Machine: JSONL only

## Sprint 2 — LLM Debug + Real Template
- llm send (debug success/fail); real provider template via command runner
- Resolve/reply with explicit --yes gates; snapshots + trailers

## Sprint 3 — Artifacts & Remotes
- Local blob store + descriptors; optional LFS publish; mind remote init/sync

## Sprint 4 — Locks & Hooks
- refs backend for locks; optional LFS lock; pre-commit and CI verify scripts

## Sprint 5 — Consensus (N-of-M)
- proposals/approvals/grants; signed approvals; policy verify CI

Backlog: Jobs subsystem, encryption, advanced policy editor, status dashboards.
