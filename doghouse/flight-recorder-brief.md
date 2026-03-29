# Flight Recorder Brief

- **Status:** Design brief
- **Date:** 2026-03-26
- **Working name:** Doghouse 2.0
- **Lineage:** Draft Punks next-act concept, seeded from the Echo proving ground

## Problem Statement

PR review state becomes hard to reason about across pushes.

The operator sees:

- comments that may be historical or still live
- checks that reran, were superseded, or changed state
- a new head SHA with unclear effect on the blocker set
- automated reviewer behavior that is stateful, fragile, or both
- a GitHub UI that encourages rereading instead of reconstruction

The result is state drift, wasted cycles, and low-confidence next actions.

## Sponsor Users

### Primary sponsor user

The PR author inside a noisy multi-round review loop.

They need to understand what changed, what is still blocking merge, and what to do next
without rereading the full PR thread every time.

### Secondary sponsor user

The repo maintainer deciding whether the PR is actually merge-ready.

They need a trustworthy current-state summary that separates live blockers from historical
noise.

### Tertiary sponsor user

The coding agent resuming an interrupted PR workflow.

They need a local artifact that reconstructs the current review situation without depending
on memory or terminal scrollback.

## Jobs To Be Done

- When review state becomes confusing across pushes, help the author reconstruct what changed.
- When merge readiness is uncertain, show the current blocker set clearly.
- When a session is interrupted, provide a durable local recovery artifact.
- When the worksheet ritual begins, ensure it is grounded in the current review episode.

## Hills

### Hill 1: Restore situational awareness

After any push or review round, the operator can answer in under 60 seconds:

- what changed since the last meaningful state
- what is blocking merge now
- what action should happen next

### Hill 2: Separate historical noise from live danger

The operator can distinguish:

- newly opened unresolved threads
- still-open carry-over threads
- newly resolved threads
- superseded failures
- newly introduced failures

### Hill 3: Preserve durable evidence

An interrupted human or agent can recover:

- current head SHA
- current blocker set
- current unresolved thread set
- current check state
- recent state trajectory

without trusting memory or the GitHub UI alone.

## Non-Goals

- Not a generic GitHub analytics suite.
- Not a replacement for the full PR page.
- Not yet a complete worksheet replacement.
- Not yet organization-wide reporting across repositories.
- Not a sterile enterprise telemetry panel.

## Product Principles

- Trustworthy artifacts beat clever dashboards.
- Semantic deltas matter more than raw file diffs.
- Local durability matters because GitHub is not a memory system.
- The recorder should reduce mental load, not add another clerical ritual.
- Flavor is a feature, but only after the mechanic is sound.

## Core Concepts

### Snapshot

A point-in-time capture of PR state, written locally as JSONL plus supporting artifacts.

### Sortie

A meaningful review episode:

- a push
- a new automated review wave
- a merge-readiness check
- a fix-batch resolution pass
- a resume after interruption

### Delta

A semantic comparison between two snapshots that answers "what changed that implies action?"

### Blocker

A merge-relevant condition such as:

- unresolved review threads
- failing checks
- pending checks
- review decision not approved
- merge state not clean
- reviewer-specific gating, such as a paused CodeRabbit state

### Thread transition

A change in unresolved review thread state:

- opened
- resolved
- still open
- reopened, if detectable

### Check transition

A change in check state that affects decision-making:

- fail -> pass
- pending -> pass
- fail -> pending
- pass -> fail
- newly introduced check
- disappeared or superseded check

## What Makes A Delta Meaningful

Doghouse should not diff raw JSON and pretend that is insight.

The meaningful delta categories are:

- head transition
- blocker transition
- thread transition
- check transition
- reviewer-state transition
- merge-readiness transition

Doghouse should ignore, by default:

- reordered arrays
- timestamp churn
- unchanged blocker lists with different filenames
- unchanged thread previews
- raw field differences that do not imply action

## Output Surfaces

### First-class plumbing

- agent-native JSONL events
- timestamped local artifacts
- latest snapshot pointers
- latest delta pointers

### Human surfaces later

- a Draft Punks TUI playback
- worksheet seeding informed by the current sortie
- merge-readiness or review-state views with theatrical flavor

## Relationship To Draft Punks

Draft Punks already identified the core pain: GitHub review state becomes too noisy and too
large to manage directly.

Doghouse 2.0 should become the stronger structural backbone:

- worksheet system as the conductor's score
- Doghouse as the black box recorder

That means future Draft Punks should not abandon the original ritual. It should ground the
ritual in a better understanding of the current review episode.

## Immediate Design Decision

The next implementation slice should be designed against the playbacks in
[playbacks.md](./playbacks.md), not against a generic desire to "log more PR data."
