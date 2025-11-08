# GATOS — Ideas Backlog

This is a living backlog of ideas that extend the Git‑native operating surface. These are intentionally out of scope for the current sprint, but close to the kernel so we can slot them in with minimal refactoring.

## 1) git‑message‑bus
- Refs: `refs/mind/events/<topic>/<yyyymmddHHMMssZ>_<id>`
- Producers: write events as small JSON blobs with trailers (`Bus-Topic`, `Bus-Source`, `Bus-Correlation`)
- Consumers: fetch/pull refspecs for topics, process, and advance consumer cursors under `refs/mind/cursors/<consumer>/<topic>`
- Delivery semantics: at‑least‑once; idempotency via `Bus-Idempotency` trailer and consumer cursor checks
- Bridges: CI/hooks to Slack/Matrix/Webhooks; replay by reset to older cursor

## 2) Attested Chat (git chat)
- Refs: `refs/mind/chat/<room>/<ts>-<id>` or Git notes on state commits
- Signing: libgitledger to sign messages; include `Chat-Sig` trailer
- Commands: `/propose <desc>`, `/approve <proposal-id>`, `/grant <proposal-id>` mutate proposal/approval refs
- UX: human CLI prints a scroll; JSONL exposes a streaming tail for LLMs

## 3) Consensus & Grants
- Refs: `refs/mind/proposals/<id>` (targets + payload), `refs/mind/approvals/<id>/<who>`, `refs/mind/grants/<id>`
- Policy: N‑of‑M thresholds per path prefix; CI validates before advancing grant
- Advancement: grant fast‑forwards target state ref when quorum is met

## 4) CRDT Mode (optional)
- State representation: CRDT for `state.json` collections (threads, selections)
- Merge: semantic; vector clocks in trailers (`Mind-VC: <clock>`) resolve concurrency without manual CAS retries

## 5) Deterministic Job Graph
- Refs: `refs/mind/jobs/<pipeline>/<run-id>`
- Inputs: a state ref + artifacts; steps produce new state/artifacts
- Cache: content‑addressed by inputs; reproduce by recomputing
- Use case: automation for PR review, batch LLM runs, report generation

## 6) Capability Tokens
- Storage: Git notes on state commits with `Cap-Grant` records or `refs/mind/caps/<cap-id>`
- Scope: limited verbs/targets (e.g., `thread.resolve` on PR 123) and TTL
- Verification: adapters check token validity before remote effects

## 7) Mind Remotes & Selective Replication
- Default remote: `mind` for `refs/mind/**` (keep `origin` clean)
- Refpolicy: publish allowlist/denylist + redactions from `.mind/policy.yaml`
- Private overlays: `~/.dp/private-sessions/<session>` never published

## 8) Artifacts Store
- Path: `.mind/artifacts/*` with descriptors committed; bytes in LFS or local CAS
- GC: mark/sweep across reachable refs/mind

## 9) Kernel Backends
- Bindings for libgitkernel/libgitledger for speed and signatures
- Map plumbing ops → kernel API; feature‑flag via `MIND_BACKEND=kernel`

## 10) RMG Integration (Graph Core)
- Use echo/meta‑graph to model state as a typed metagraph
- Provide canonical serialization; query layer over state

---

### Minimal Prototypes (future)
- `mind bus publish --topic <t> --json <file>` → writes event ref
- `mind bus subscribe --topic <t> --cursor <name>` → tails events and advances cursor
- `mind chat post --room <r> --body <text>` → writes chat message
- `mind cap grant --verb thread.resolve --pr 123 --ttl 6h --to @bot` → publishes capability token

