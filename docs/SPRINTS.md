# Draft Punks — Delivery Plan (Sprints)

This plan sequences the work required to satisfy `docs/SPEC.md`, resolve drift, and close current tech debt. It links directly to Feature IDs (DP-F-XX) and User Story IDs (DP-US-XXXX) defined in `FEATURES.md`. Progress is tracked in `TASKLIST.md`. Drift is tracked in `DRIFT_REPORT.md`.

Cadence & Dates
- Sprint length: 1 week (Mon–Fri) to keep iteration tight.
- Start date: Monday, 2025-11-10 (US Pacific). Subsequent sprints roll weekly.
- Code freeze on Fridays; demo + retro on Fridays 3pm local.

Definitions
- DoR: Each story must have clear Requirements, AC, and Test Plan (see FEATURES.md) and any mocks/fixtures ready.
- DoD: All AC met; tests passing; basic docs updated; feature toggled/flagged if partial; no TODOs that affect AC.

Dependencies & Environments
- Python 3.11+ (dev uses 3.14). Textual >= 0.44 (APIs stabilized for ListView, OptionList).
- GitHub: GH_TOKEN or `gh auth login` for API/GraphQL actions.
- Dev wrapper: `draft-punks-dev` (uses repo `.venv`) for fast iteration.

---

## Sprint 0 (2025-11-10 → 2025-11-14) — CLI Pivot & State Engine

Goals
- Pivot to CLI‑only for v0.1 and implement a Git‑backed state engine with a deterministic JSONL protocol.

Scope
- CLI State & Protocol (see docs/CLI-STATE.md)
  - dp state init/use/undo/redo/snapshot (writes/commits state.json with trailers)
  - dp session new/use/list (branch management in state repo)
  - dp repo detect/set
  - dp serve --stdio (repo/pr/thread scaffolding only)
- Packaging groundwork (minimal): keep single package; add `dp` entry point

Deliverables
- Working `dp` CLI with state repo creation and basic commands.
- JSONL server responding to `repo.detect` and `state.show`.
- Docs: CLI-STATE.md (this sprint), TECH-SPEC mermaid sections updated (done).

Risks
- Hidden state confusion — mitigated with `dp state show` and commit sha (`state_ref`) on every result.

Traceability
- TASKLIST: add CLI stories `DP-F-30` (state & protocol) — or track under DP-F-20 during transition.

---

## Sprint 1 (2025-11-17 → 2025-11-21) — Repo & PR CLI

Goals
- Implement repo/pr flows via CLI.

Scope
- dp pr list/select/info commands
- Human table output + `--format json` parity

Deliverables
- `dp pr list/select/info` complete with state mutations and commits.

Drift Resolution
- Replace ad-hoc `ListView` usage with Scroll View in Title→next screens where applicable.

Risks
- Textual lifecycle (compose vs mount) — addressed by populate-after-mount pattern.

---

## Sprint 2 (2025-11-24 → 2025-11-26) — Threads CLI (short week)

Goals
- Implement thread list/select/show/resolve/reply with `--yes` gate.

Scope
- DP-F-02 Main Menu
  - DP-US-0201 Fetch+render PR list (icon, author, age, truncated title, `{ i, e }`).
  - DP-US-0202 PR Info modal, Merge shortcut stub, Settings shortcut, Dirty-stash banner & flow.
- DP-F-15 Status Bar & Key Hints (footer hints when list focused)
  - DP-US-1501

Deliverables
- `dp thread list/select/show/resolve/reply` with state commits and cache updates.

Drift Resolution
- Navigation becomes: Title → Main Menu → PR View (no longer Title → Comment Viewer).

Risks
- CI/merge data availability; mock if missing and gate merge flow to Sprint 6.

---

## Sprint 3 (2025-12-01 → 2025-12-05) — LLM Send (Debug + Real)

Note: US Thanksgiving (Nov 27–28) → 3-day sprint.

Goals
- `dp llm send` with Debug provider; wire real providers via template.

Scope
- DP-F-03 PR View
  - DP-US-0301 Render threads with filters `u` (unresolved) / `a` (all).
  - DP-US-0302 Toggle resolved with `r` (uses GitHub resolve/unresolve).
  - DP-US-0303 Kick off Automation with `A` (stub controller this sprint).

Deliverables
- Debug path (prompt preview, success/failure) and real path (provider template).

Drift Resolution
- Move Automation entry point from Comment Viewer to PR View.

---

## Sprint 4 (2025-12-08 → 2025-12-12) — Automation & Filters

Goals
- `dp llm send --auto pr|file` progressive automation + pause.

Scope
- DP-F-05 LLM Interaction
  - DP-US-0501 Confirm/send/edit & success/failure branching (we already have success/failure prompts; add editor path).
  - DP-US-0502 Automation mode mechanics + pause/resume with `Space`.
- DP-F-10 Prompt Editing & Templates
  - DP-US-1001 Editor integration; token substitution for basic context.

Deliverables
- Automation controller; progress; summary; journal entries.

Risks
- Cross-platform editor invocation; provide fallback and env override.

---

## Sprint 5 (2025-12-15 → 2025-12-19) — Settings, Logging, Release

Goals
- Settings via CLI; richer logs; v0.1 release tasks.

Scope
- DP-F-11 Settings & Persistence
  - DP-US-1101 Settings screen (provider, reply_on_success, force_json).
- DP-F-17 Logging & Diagnostics
  - DP-US-1701 In-app log sink; transcript capture (optional flag).
- DP-F-15 Status Bar & Key Hints
  - DP-US-1501 Persistent footer hints across screens.
- DP-F-16 Theming & Layout
  - DP-US-1601 Legibility audit and CSS tweaks.

Deliverables
- `dp llm provider/template set`, reply_on_success, force_json, and release notes.

---

## Backlog — Merge & Stash (post‑0.1)

Goals
- Merge and stash flows when needed.

Scope
- DP-F-12 Merge Flow
  - DP-US-1201 Merge with guardrails (CI passing, approvals, conflicts) via gh/GraphQL.
- DP-F-13 Stash Dirty Changes Flow
  - DP-US-1301 Detect dirty & stash/discard (complete integration with Main Menu banner).
- Close remaining gaps from `DRIFT_REPORT.md`.

Deliverables
- Merge/stash flows as follow‑ups.

---

## Backlog / Nice-to-Haves (Post-SPEC)
- DP-F-19 Image Splash (bunbun.webp) behind `DP_TUI_IMAGE` (polish).
- Advanced prompt templating (file hunk extraction; language hints).
- Multi-provider capability detection and auto-JSON flags.
- Telemetry (opt-in) for anonymized UX metrics.

---

## Cross-Cutting Tech Debt & Risks
- Textual API drift (OptionList, ListView): maintain compatibility shims; pin minimum version.
- GraphQL rate limiting/pagination: ensure paging cursors and progress callbacks surface in UI.
- Git operations safety: dry-run flags where possible; clear messaging on failures.
- Tests: add unit tests for pagination, age humanizer, prompt parsing; snapshot tests for key views.
- CI: add GitHub Actions to run tests on 3.11/3.12/3.14 and lint.

---

- Sprint 0: CLI‑STATE core (dp state/session/repo; serve scaffolding)
- Sprint 1: PR CLI
- Sprint 2: Threads CLI
- Sprint 3: LLM Send (debug+real)
- Sprint 4: Automation
- Sprint 5: Settings + Release

Use `TASKLIST.md` as the authoritative checklist; update it as stories move between states. Review `DRIFT_REPORT.md` at each sprint boundary to keep the implementation and SPEC aligned.

---

## Traceability (to TASKLIST.md)

For each sprint, the following TASKLIST entries (by ID) must be checked off to consider the sprint complete.

- Sprint 1
  - DP-US-0001 (all subtasks, including retrofitting Main Menu/PR View)
  - DP-US-0002 (renderer/keys/perf)
  - DP-US-0003 (empty/error states + reload)
  - DP-US-0101 (repo info on Title, Enter/Esc/Ctrl+C)
  - DP-US-0102 (logo overrides)
  - DP-US-1401 (help overlay portion)

- Sprint 2
  - DP-US-0201 (PR list render + Enter→PR View)
  - DP-US-0202 (PR info modal, settings shortcut, dirty banner & stash, merge shortcut stub)
  - DP-US-1501 (footer hints on list screens)

- Sprint 3
  - DP-US-0301 (thread list + filters)
  - DP-US-0302 (toggle resolved)
  - DP-US-0303 (automation entry, stub controller)

- Sprint 4
  - DP-US-0501 (confirm/send/edit, success/failure branching)
  - DP-US-0502 (automation mechanics with pause/resume)
  - DP-US-1001 (prompt editor + tokens)

- Sprint 5
  - DP-US-1101 (settings screen)
  - DP-US-1701 (log sink; optional transcript)
  - DP-US-1501 (persistent hints across screens)
  - DP-US-1601 (legibility)

- Sprint 6
  - DP-US-1201 (merge flow)
  - DP-US-1301 (stash dirty flow)
  - Any remaining drift items tied to above stories
