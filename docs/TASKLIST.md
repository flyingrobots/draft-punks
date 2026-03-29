# Doghouse — Project Tasklist

Legend
- [ ] not started
- [~] in progress
- [x] done

## Phase 1: Core Engine & CLI (The Reboot)

- [x] DP-F-21 Doghouse Flight Recorder
  - [x] Implement `Blocker`, `Snapshot`, `Delta` domain models
  - [x] Implement `DeltaEngine` with semantic comparison logic
  - [x] Implement `RecorderService` orchestrator
  - [x] Implement `GhCliAdapter` with GraphQL support for threads
  - [x] Implement `JSONLStorageAdapter` for durable local state
  - [x] Implement CLI `snapshot` and `history` commands
  - [x] Implement machine-readable `--json` output
  - [x] Implement `playback` command for deterministic testing
  - [x] Seed initial playbacks (PB1, PB2)

## Phase 2: Intelligence & Polish

- [ ] DP-F-22 CodeRabbit Awareness
  - [ ] Detect "paused" or "cooldown" state from top-level comments
  - [ ] Identify "Duplicate" vs "Additional" comment clusters
- [ ] DP-F-23 Agent-Native Enhancements
  - [ ] `LATEST` pointer/symlink for easy context recovery
  - [ ] Summary verdict in commit-trailer-compatible format
- [ ] DP-F-24 Playback Expansion
  - [ ] Implement PB3 (Interruption), PB4 (Tiny Follow-up), PB5 (New vs Carry-over)
- [ ] DP-F-25 TUI Playback (PhiedBach's Theater)
  - [ ] Textual-based visualization of deltas and blockers

## Phase 3: Integration (The Score)

- [ ] DP-F-26 Worksheet Seeding
  - [ ] Seed Draft Punks worksheets based on Doghouse delta insights
- [ ] DP-F-27 Pre-push Blocker Gate
  - [ ] Gate pushes based on Doghouse blocker set
