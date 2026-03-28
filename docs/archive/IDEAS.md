# GATOS — Ideas Backlog

This is a living backlog of ideas that extend the Git‑native operating surface. These are intentionally out of scope for the current sprint, but close to the kernel so we can slot them in with minimal refactoring.

## 0) Doghouse 2.0 Flight Recorder
- Seed docs live in [`doghouse/`](../doghouse/README.md)
- Goal: add a black-box recorder for PR state across pushes, rerun checks, and reviewer waves
- Core objects: `snapshot`, `sortie`, `delta`, `next_action`
- Output bias: agent-native JSONL plumbing first, human-friendly porcelain later
- Product stance: keep the BunBun / PhiedBach flavor, but stop forcing the worksheet model to carry the entire PR-state burden
- Future fit: the worksheet becomes the adjudication layer on top of Doghouse's state reconstruction

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

---

## 11) Git‑Backed Redis (KV Over Git)

Goal: Redis‑like semantics (GET/SET/DEL, hashes, sets, counters, TTLs, pub/sub) over Git’s Merkle DAG with offline operation, time‑travel, and sync via remotes.

Data model
- Namespace → ref: `refs/mind/kv/<ns>`
- Within a commit tree: keys mapped to paths under `kv/` using a hashed fan‑out (e.g., `kv/ab/cd/<escaped_key>`)
- Value blob: raw bytes or JSON; optional sidecar meta `meta/<path>.json` with `{ttl, expire_at, etag}`
- Trailers: `KV-Op: set|del|incr|hset|…`, `KV-Keys: <k1,k2,…>`, `KV-TTL: <seconds>`

Semantics
- Linearizable per namespace (single ref) with CAS via `update-ref` using previous head (or across multiple refs via `update-ref --stdin`)
- Transactions: bundle multi‑key ops into one commit; a pipeline is just a batch of ops collapsed into one write
- TTLs: stored in meta; a background compactor removes/refreshes expired keys by writing a new commit
- Pub/sub: use message bus; publish under `refs/mind/events/kv/<ns>/<key>/<ts>`

Performance
- Hot cache: a small in‑memory index for the current head (like Redis), with async persistence to Git; on restart, rebuild from head
- Compaction: periodic snapshotting (RDB‑like) from an append‑only ops log to a compact tree
- Large values: store in LFS; the KV tree holds descriptors pointing to LFS pointers

Concurrency
- Client flow: read head → compute new tree → `commit-tree` → `update-ref <old_head> <new_head>`; retry on mismatch
- Optional CRDT mode for conflict‑tolerant types (PN‑counters, OR‑sets) to reduce retries in high contention cases

Prototype CLI (sketch)
- `mind kv get <ns> <key> [--format raw|json]`
- `mind kv set <ns> <key> <value> [--ttl 60]`
- `mind kv del <ns> <key>`
- `mind kv incr <ns> <key> [--by N]`
- `mind kv hset <ns> <key> <field> <value>` / `hget`
- `mind kv scan <ns> [--match pattern]`
- `mind kv serve` (hot cache daemon; JSONL: `kv.get`, `kv.set`, …)

Notes
- There’s an existing `git-kv` repo in your workspace; we should evaluate and align semantics, then either wrap it as a backend or consolidate here.
