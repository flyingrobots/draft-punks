# Integration Plan — GATOS (git mind) × git-kv (Project Stargate)

This document maps overlap and defines a phased plan to interoperate and, where sensible, converge designs between `draft-punks` GATOS components and the `git-kv` (Stargate) project.

## Executive Summary

- Both systems treat Git as a verifiable data plane with speech‑acts encoded as commits.
- `git-kv` focuses on a high‑performance, audit‑grade KV with fast prefix listing, chunked large values, epochs, and a write gateway (Stargate).
- GATOS (git mind) is a general state engine with JSONL commands; our “git‑backed Redis” idea is largely a subset of `git-kv`.
- Plan: adopt `git-kv` as the KV backend for GATOS, provide a local fallback, and converge on indexing, chunking, and policy semantics over time.

## Crosswalk (Concepts)

- State commits with trailers → same principle; unify trailer keys across projects (see Appendix A).
- CAS via `update-ref` → shared.
- Namespaces → `refs/mind/kv/<ns>` (GATOS) vs `refs/kv/<ns>` (`git-kv`). We will prefer `refs/kv/**` for KV and keep `refs/mind/**` for session/state.
- Fast listing → `git-kv`’s `refs/kv-index/<ns>`; GATOS should adopt this index format when using the KV backend.
- Large values → GATOS uses LFS today; `git-kv` uses FastCDC chunking. We will keep LFS for generic artifacts and use chunking for KV values.
- Bounded clone → adopt `git-kv` epochs for KV repos; optional for GATOS state repos (not typically needed).
- Pub/Sub → GATOS message‑bus can reuse `git-kv` watchlog/events layout.
- Policy → converge `.mind/policy.yaml` and `.kv/policy.yaml` into a shared schema where overlapping.

## Phased Plan

### Phase 0 — Adapter & Protocol

- Add a `kv` module to GATOS with a backend interface: `LocalPlumbingKV` and `GitKVBackend` (CLI/stdio bridge or direct plumbing if we vend a library).
- JSONL commands: `kv.get`, `kv.set`, `kv.del`, `kv.mset`, `kv.scan`.
- If `git kv` is on PATH and `.kv/policy.yaml` exists, default to `GitKVBackend`; otherwise use `LocalPlumbingKV` under `refs/mind/kv/<ns>`.

### Phase 1 — Index & TTL Alignment

- When `GitKVBackend` is active, defer listing to `refs/kv-index/<ns>`.
- Implement TTL and read‑side expiry semantics to match `git-kv` (store `expire_at` in meta; compactor writes a new commit that removes expired items).

### Phase 2 — Chunked Values & Artifacts

- For KV values above threshold, use `git-kv` chunk manifests; for general GATOS artifacts, continue with LFS descriptors.
- Provide a migration path for existing large KV values stored via LFS to chunked manifests.

### Phase 3 — Gateway & Remotes

- Introduce a `mind` remote for state and a `kv` remote for `git-kv` refs, or keep a single repo with split ref spaces.
- Add `dp kv remote setup` that delegates to `git kv remote setup` to configure `pushurl` to Stargate.
- Optionally route some GATOS state pushes via Stargate (policy enforcement) when configured.

### Phase 4 — Observability & Watchers

- Expose GATOS bus subscribers compatible with `git-kv` watchlog/events.
- Surface mirror watermarks for read‑after‑write when reading from mirrors.

## Open Questions

- Do we embed `git-kv` as a library (direct plumbing) or shell out to its CLI? Initial approach: shell out; medium‑term: shared plumbing lib.
- Should `git-kv` and GATOS share a repo (split namespaces) or use separate repos with submodules/remotes? Start with shared repo; keep an option to split.
- Trailer harmonization: adopt generic keys (e.g., `Op`, `Args`, `Result`, `State-Hash`, `Idempotency`, `Version`) or keep project‑prefixed forms? Proposed: generic keys with optional project prefix for routers.

## Risks & Mitigations

- Diverging semantics: keep a single integration spec and tests for both backends.
- Performance drift: use `git-kv` index for listing; compaction for large histories; avoid scanning.
- Policy mismatch: define a superset policy schema and validate both `.mind/policy.yaml` and `.kv/policy.yaml` against it.

## Next Steps

- Implement `GitKVBackend` adapter and `kv.*` JSONL commands in GATOS.
- Write tests for CAS, TTL, and scan behavior under both backends.
- Update TECH‑SPECs with reference layouts; add CLI examples.

---

### Appendix A — Trailer Harmonization

Current keys (GATOS): `DP-Op`, `DP-Args`, `DP-Result`, `DP-State-Hash`, `DP-Version`, optional `DP-Idempotency`.

Current keys (git-kv): `KV-Op`, `KV-Keys`, `KV-TTL`, etc.

Proposal: Core keys without prefix for routers →
- `Op: kv.set|kv.del|mind.repo.detect|…`
- `Args: key=…&ttl=…`
- `Result: ok|fail`
- `State-Hash: <blob>`
- `Idempotency: <uuid>`
- `Version: 0`

Routers may add additional project‑specific trailers next to these.

