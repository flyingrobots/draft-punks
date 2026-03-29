# git mind — Product Spec (v0.1)

## Vision

Turn Git into a conversational, policy‑governed operating surface:
- Sessions are Git refs (refs/mind/sessions/*) you can branch, merge, and time‑travel.
- Every action is a commit with trailers (speech‑acts) and an optional shiplog event.
- A JSONL stdio API makes it deterministic for scripts/agents; an optional fzf layer makes it fast for humans.
- Privacy is policy‑driven: hybrid projection puts non‑sensitive state in snapshots, keeps secrets/artifacts local (and optional LFS for publishing).
- Governance is programmable: N‑of‑M approvals, locks, roles.

## User Outcomes

- As a contributor, I can operate on PRs/threads/jobs without leaving my terminal and without losing history.
- As a maintainer, I can require approvals and locks, and audit every step.
- As an agent (LLM/bot), I can “talk” to git mind via JSONL and mutate state safely using state_ref + expect_state.

## Core Flows (v0.1)

- Repo init & detect → write minimal snapshot (state.json)
- PR list/select → cache in snapshot; set selection.pr
- Thread list/select/show (unresolved/all)
- LLM send (debug; then provider template) → success/failure branch
- Resolve/reply (explicit --yes gate)

## Non‑Goals (v0.1)

- No TUI; fzf pickers only as optional niceties.
- No remote push by default; user opts in (mind remote).

## Reference Namespace (in‑repo; no worktree churn)

- refs/mind/sessions/<name>     — materialized snapshot commits
- refs/mind/snaps/<ts>          — optional snapshot tags/refs
- refs/mind/locks/<lock-id>     — lock heads (or mirror LFS locks)
- refs/mind/proposals/<op-id>   — gated op requests (future)
- refs/mind/approvals/<op-id>/* — signed approvals (future)
- refs/mind/jobs/<job-id>/...   — job descriptors/claims/results (future)
- refs/mind/artifacts/<id>      — LFS pointer commits (optional future)

Snapshot commit trailers (baseline):
- DP-Op, DP-Args, DP-Result, DP-State-Hash, DP-Version

## CLI (human)

- git mind session-new/use/show
- git mind state-show | nuke
- git mind repo-detect
- git mind pr-list | pr-pick
- git mind thread-list | thread-pick (future)
- git mind llm send --debug success|fail (future)

## JSONL API (machine)

- git mind serve --stdio
- Request: {"id","cmd","args", "expect_state"?}
- Response: {"id","ok", ("result"|"error"), "state_ref"}
- v0.1 commands: hello, state.show, repo.detect, pr.list, pr.select

## Privacy & Artifacts (hybrid by default)

- Public projection in snapshot tree (state.json + small metadata).
- Private overlay at ~/.dp/private-sessions/<owner>/<repo>/<session> (optional encryption).
- Local blob store for big files with pointer records in snapshot; optional publish via Git‑LFS for selected artifacts.

## Policy & Attributes

- .mind/policy.yaml defines storage mode, redactions, approvals, locks.
- .gitattributes can declare intent per path: mind-local, mind-private, mind-lock, mind-publish=lfs, mind-encrypt.
- Hooks/CI enforce locks/approvals on protected paths.

## Remotes

- Optional dedicated “mind” remote (local bare or server) syncing only refs/mind/* via explicit refspecs.

## Integrations

- shiplog (optional): append mind.* events; snapshots remain canonical.
- go‑job‑system: job descriptors/claims/results map to refs/mind/jobs/* (see TECH‑SPEC).
- ledger‑kernel/libgitledger: ledger for approvals/attestations (TBD mapping).
