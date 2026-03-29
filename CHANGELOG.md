# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Doghouse Flight Recorder**: A new agent-native engine for PR state reconstruction.
- **CLI Subcommands**: `snapshot`, `watch`, `playback`, `export`.
- **Blocking Matrix**: Logic to distinguish merge conflicts from secondary blockers.
- **Local Awareness**: Detection of uncommitted/unpushed local repository state.
- **Machine-Readable Output**: `--json` flag on `snapshot` for Thinking Automatons.
- **Repro Bundles**: `export` command to create "Manuscript Fragments" for debugging.
- **Snapshot Equivalence**: `Snapshot.is_equivalent_to()` for meaningful-change detection.

### Fixed
- **Merge-Readiness Semantics**: Formal approval state (`CHANGES_REQUESTED`, `REVIEW_REQUIRED`) is now separated from unresolved thread state. Stale `CHANGES_REQUESTED` no longer masquerades as active unresolved work when all threads are resolved.
- **Verdict Priority Chain**: Fixed dead-code bug where `is_primary` default caused Priority 0 to swallow all BLOCKER-severity items. Merge-conflict check now uses explicit type match. Added approval-needed verdict at Priority 4.
- **Repo-Context Consistency**: `watch` and `export` now honor `--repo owner/name` via centralized `resolve_repo_context()`. Previously they silently ignored `--repo` and queried the wrong repository.
- **Packaging**: Fixed `pyproject.toml` readme path (`cli/README.md` → `README.md`). Editable install now works.
- **Watch Snapshot Spam**: `record_sortie()` no longer persists duplicate snapshots on identical polls. Only meaningful state transitions (head SHA change, blocker set change) create new ledger entries.
- **Missing Import**: Added `Blocker` import to `recorder_service.py` (blocker merge would have crashed at runtime).
- **CI/CD Security**: Added top-level permissions to workflows and expanded branch scope.
- **Publishing Hygiene**: Refined tag patterns and split build/publish steps.
- **Core Immutability**: Ensure Snapshot and Blocker objects own immutable copies of data.
- **Deterministic Delta**: Sorted blocker IDs to ensure stable output across runs.
- **Error Handling**: Hardened subprocess calls with timeouts and missing-upstream detection.
- **Import Paths**: Fixed packaging bugs identified via recursive dogfooding.
- **Docs Drift**: Archived legacy Draft Punks TUI documentation to clear confusion.

### Tests
- Added blocker-semantics tests (review/thread interaction, verdict priority chain).
- Added repo-context consistency tests (all commands use `resolve_repo_context`).
- Added watch persistence tests (dedup on identical polls, persist on meaningful change).
- Added snapshot equivalence tests.
- Added packaging smoke tests (readme path, metadata, entry point).
