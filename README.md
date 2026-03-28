# 🐕 Doghouse (formerly Draft Punks)

**Doghouse** is a PR flight recorder. It captures trustworthy snapshots of Pull Request state, computes semantic deltas across pushes, and identifies the exact blocker set preventing a merge.

It is designed to be **agent-native**: providing a durable context memory for AI agents and humans navigating noisy, multi-round review loops.

## The Core Concept

- **Snapshot**: A point-in-time capture of head SHA, unresolved threads, and check statuses.
- **Sortie**: A meaningful review episode (a push, a new review wave, a resume after interruption).
- **Delta**: A semantic comparison that answers: *What changed? What matters now? What is the next action?*

## Installation

```bash
# Clone the repo
git clone https://github.com/flyingrobots/draft-punks.git
cd draft-punks

# Install in editable mode
pip install -e .
```

## Quick Start

### 📡 Capture a Sortie
Run this inside a git repo with an open PR to see what has changed since your last snapshot.

```bash
doghouse snapshot
```

### 🎬 Run a Playback
Verify the delta engine logic against offline fixtures.

```bash
doghouse playback pb1_push_delta
```

### 📜 View History
See the trajectory of your PR state over time.

```bash
doghouse history
```

## Why Doghouse?

GitHub's UI is a timeline, but it's not a memory. When a PR has been through 5 pushes and 3 CodeRabbit waves:
- Which comments are historical noise?
- Which checks actually regressed vs. just reran?
- Are we *actually* ready to merge?

Doghouse reconstructs the answer so you don't have to.

---

## Technical Architecture

- **Hexagonal Core**: Technology-agnostic domain models (`Blocker`, `Snapshot`, `Delta`).
- **Git-Native Storage**: Snapshots are persisted locally as JSONL in `~/.doghouse/snapshots/`.
- **GH-CLI Adapter**: Uses the `gh` CLI and GraphQL for high-fidelity state retrieval.

## Playbacks

We develop against concrete scenarios defined in `doghouse/playbacks.md`. If a feature doesn't improve a playback, we don't build it.

---

*“Every PR is a flight. Doghouse is the black box.”*
