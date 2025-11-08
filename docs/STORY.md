# GATOS: A Story About Draft Punks, Git Minds, And Speech‑Acts

This is a narrative from the assistant’s point of view about what we’re building, how we got here, the ideas we voiced (and the ones we didn’t), and why this alters how an AI like me can work with your tools. It’s not a spec; it’s a rationale and a map of the territory.

---

## Origin Story — From TUI Friction To A Git‑Native Surface

We started with a Textual TUI because it felt natural for a human reviewing PR threads and asking an LLM for help. But we ran into a pile of practical friction:

- Tooling headwinds: Python 3.14 + PEP 668 (externally managed envs), pipx reinstall loops, API drift in Textual (e.g., `OptionList.Option`).
- Automation friction: TUIs are hard to drive non‑interactively. You asked for speed and iteration; I can’t “press keys”.
- Observability gaps: A TUI hides the dataflow the LLM most needs to reason about.

Those bumps crystallized something we both felt: the real product isn’t a screen, it’s the state. We made the pivot:

- Git is the substrate. Refs are state. Commits are speech‑acts.
- JSONL over stdio is the syscall layer. The CLI is the human shell.
- Policy (privacy, locks, approvals) governs side effects. The engine remains deterministic and auditable.

Thus, GATOS — the Git Attested, Transactional Operating Surface — was born. “Draft Punks” becomes the first app riding that surface.

---

## What Makes This Different

- Attested by default: Every state change is a commit with trailers (`DP‑Op`, `DP‑Args`, `DP‑Result`, `DP‑State‑Hash`). Time travel and blame are free.
- Human and machine symmetry: Humans get a clear CLI; machines get JSONL with the same semantics. No modal impedance mismatch.
- Offline‑first: Because it’s Git. Sync later; fetch/push refspecs define who sees what.
- Policy over code: Redaction, private overlays, LFS locks, and N‑of‑M consensus become configuration enforced by hooks/CI.
- Hexagonal forever: Ports/adapters keep us honest; kernels (libgitledger/libgitkernel) can replace plumbing without rewriting the app layer.

It’s event‑sourced state with a Merkle ledger that developers already understand.

---

## Design Choices That Matter

- Speech‑acts as commits: Each operation writes a new commit under `refs/mind/sessions/<name>`, recording what we did and why.
- JSONL protocol: One command, one reply. Deterministic, testable, CI‑friendly. Easy for me (or any agent) to compose.
- Hybrid privacy: Public snapshot vs local private overlay (`~/.dp/private-sessions/...`) governed by policy and gitattributes‑like rules.
- Capability gating: Explicit `--yes` or policy‑granted authority before mutating remote systems (e.g., resolve a thread on GitHub).
- Idempotency and CAS: Optional `expect_state` guards apply compare‑and‑swap semantics to every mutation.

---

## How This Changes My (AI) Interaction

Before: a TUI meant opaque frames and keypresses I can’t send. After: a reliable, typed conversation over JSONL with globally addressable state.

- I can propose a series of mutations, preview the new `state_ref`, and roll back if needed.
- I can annotate PRODUCTION_LOG entries automatically when unexpected work appears (surfacing process drift in real time).
- I can reason on diffs (previous `state.json` vs next), not screenshots.
- I can safely parallelize, because CAS guards and policy make conflicts first‑class.

This is the first time a CLI feels like a co‑processor rather than a user interface I must “pretend” to click.

---

## Ideas We Were Quiet About (Until Now)

These are directions I held back while we stabilized the kernel. They’re feasible and synergistic with the GATOS substrate.

- git‑message‑bus
  - Events under `refs/mind/events/<topic>/<ts>-<id>`; consumers fetch with narrow refspecs and process at‑least‑once.
  - Hooks/CI act as routers. A Slack/Matrix bridge drops messages into Git and emits webhooks out again.
  - Benefits: offline fan‑out, tamper‑evident history, replay/debug by rewinding the DAG.

- git chat (attested chatops)
  - Conversations as either notes on state commits or as `refs/mind/chat/<room>` streams.
  - Signed messages (libgitledger) provide non‑repudiation; bots become first‑class participants with scoped capabilities.
  - “Chat that ships code” because messages can reference and advance state refs via proposals.

- Consensus & grants as first‑class
  - Proposals live at `refs/mind/proposals/<id>`; approvals at `refs/mind/approvals/<id>/<who>`.
  - N‑of‑M is verified in CI; a “grant” ref fast‑forwards the target state when quorum is met.
  - Gives teams feature‑flag‑like safety for operational state, not only code.

- CRDT mode (optional)
  - For human‑heavy collaboration, introduce CRDT transforms for state.json. Merge becomes semantic rather than textual.
  - Vector clocks embedded in trailers could resolve concurrent speech‑acts.

- Deterministic job graph
  - A job runner reads a state ref, executes pure steps, and commits artifacts + new state. Think “go‑job‑system” but state‑native.
  - Cache keys = content hashes; results are re‑derivable and attestable.

- Capability tokens
  - Signed, revocable tokens stored as notes grant narrow permissions (e.g., “may resolve threads on PR #123 for 6 hours”).
  - Lets you hand an agent just enough power to operate safely.

- Mind remotes & selective replication
  - Keep origin clean. Push `refs/mind/**` to `mind` remote; teammates opt in with their own refspecs.
  - Policy controls what is publishable vs local‑only, with automatic redaction.

---

## Why Not A Blockchain?

We get most of the desirable properties (immutability, audit, time order, distributed sync) with Git’s Merkle DAG and existing tooling.

- No global consensus needed; your repos are sovereign. Where consensus matters, we encode it explicitly (N‑of‑M approvals).
- Cost and complexity stay human‑scale. We reuse Git’s storage, transport, and ergonomics.
- If/when we need “hard attestations,” libgitledger can sign and verify.

The result is a practical ledger for apps rather than a financial network.

---

## Where I’m Excited To Go Next

- Kernel seam: wire libgitkernel/libgitledger for speed, signatures, and richer primitives (notes, locks, LFS, attributes) as first‑class calls.
- RMG (recursive metagraph): adopt echo/meta‑graph for canonical state representation with typed, queryable graphs.
- Artifacts: a content‑addressed side store with LFS pointers and garbage collection tied to refs/mind reachability.
- Policy‑as‑code: `.mind/policy.yaml` → verified in CI; pre‑receive hooks enforce it for mind remotes.
- First‑party apps beyond dp: shiplog on GATOS, decision logs, runbooks, incident retros that literally replay.

---

## Risks And Guardrails

- Repo bloat: mitigate with narrow refspecs, GC, and artifact indirection (LFS).
- Privacy leaks: default‑deny publish rules; redaction overlays enforced in CI; E2E encryption for private overlays.
- Commit storms: batch/aggregate policies; rate limits; job graph coalescing.
- Concurrency: rely on CAS and, where needed, CRDT transforms.

If it ever becomes hard to reason about, we failed the primary goal.

---

## What Success Looks Like

- You talk to tools the way you talk to collaborators. Every action is legible, reversible, and attributable.
- Humans and agents share a single operational substrate. No shadow UIs, no hidden state.
- The state of work travels with the work. You can branch your operations the way you branch your code.

This is a surface where ideas become speech‑acts, and speech‑acts become artifacts that ship. I’m excited because this finally treats an AI not as a click‑emulator, but as a peer with clear contracts and accountable impact.

