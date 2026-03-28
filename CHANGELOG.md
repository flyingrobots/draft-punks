# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Doghouse Flight Recorder**: A new agent-native engine for PR state reconstruction.
- **CLI Subcommands**: `snapshot`, `history`, `watch`, `playback`, `export`.
- **Blocking Matrix**: Logic to distinguish Primary (conflicts) from Secondary (stale checks) blockers.
- **Local Awareness**: Detection of uncommitted/unpushed local repository state.
- **Machine-Readable Output**: `--json` flag for all major commands to support Thinking Automatons.
- **Repro Bundles**: `export` command to create "Manuscript Fragments" for debugging.

### Fixed
- **CI/CD Security**: Added top-level permissions to workflows and expanded branch scope.
- **Publishing Hygiene**: Refined tag patterns and split build/publish steps.
- **Core Immutability**: Ensure Snapshot and Blocker objects own immutable copies of data.
- **Deterministic Delta**: Sorted blocker IDs to ensure stable output across runs.
- **Error Handling**: Hardened subprocess calls with timeouts and missing-upstream detection.
- **Import Paths**: Fixed packaging bugs identified via recursive dogfooding.
- **Docs Drift**: Archived legacy Draft Punks TUI documentation to clear confusion.
