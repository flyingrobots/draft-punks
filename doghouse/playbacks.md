# Playbacks

This document defines the situations Doghouse 2.0 must handle well.

If a future slice does not improve one of these playbacks, it is probably the wrong slice.

## Playback 1: "What changed since my push?"

### Situation

The author pushes a fix batch and checks back later.

### Current pain

- new CI runs exist, but old failed runs are still visible
- some review threads are resolved, some are new, some are historical noise
- the operator cannot immediately tell whether the PR improved

### Success condition

Doghouse can tell the operator:

- old head -> new head
- blockers removed
- blockers added
- threads newly opened
- threads newly resolved
- checks that improved
- checks that regressed

## Playback 2: "Are we actually ready to merge?"

### Situation

The PR feels done, but GitHub still says blocked.

### Current pain

- some blockers are formal state only
- some blockers are real unresolved work
- the operator has to reconstruct the answer manually

### Success condition

Doghouse can separate:

- live merge blockers
- resolved historical noise
- formal approval-state blockers
- pending automation blockers

## Playback 3: "I got interrupted. What state was I in?"

### Situation

An agent or human leaves mid-review cycle and comes back later.

### Current pain

- terminal output is gone or noisy
- GitHub comments are too large to reread quickly
- memory is unreliable

### Success condition

The latest snapshot plus prior delta can reconstruct:

- current head SHA
- current unresolved thread count
- current check state
- current blocker set
- what changed since the last sortie

## Playback 4: "Did this tiny follow-up actually matter?"

### Situation

A tiny docs or wording follow-up push restarts the suite and review bots.

### Current pain

- the author knows the push was small
- GitHub still creates the impression of a whole new storm
- it is hard to distinguish superficial reruns from substantive new problems

### Success condition

Doghouse can show that:

- the head changed
- the blocker set did or did not change
- no new unresolved threads appeared, or exactly which ones did
- failing checks were merely rerun, not substantively regressed

## Playback 5: "Which complaints are actually new?"

### Situation

The PR has been through several rounds and the same themes keep reappearing.

### Current pain

- the author rereads historical comments as if they are current
- GitHub makes old major comments feel live
- the review loop burns time on reconstruction

### Success condition

Doghouse can distinguish:

- newly opened threads
- old unresolved carry-over threads
- resolved threads that stayed resolved
- reopened or reintroduced issues, if detectable

## Playback 6: "What is CodeRabbit doing now, exactly?"

### Situation

CodeRabbit is active, paused, cooling down, or waiting for a manual checkbox or comment nudge.

### Current pain

- the top summary comment is stateful and weird
- GitHub does not make the actual actionable state obvious
- the operator can mistake a paused Rabbit for a broken Rabbit

### Success condition

Doghouse can distinguish:

- actively reviewing
- cooled down and requestable
- rate-limited
- paused behind manual rearm controls
- "weird but not blocking" top-comment state

without eclipsing human or other reviewer state.

## Playback 7: "Can this still feel like Draft Punks?"

### Situation

The mechanic is strong, but the repo risks losing its original identity.

### Current pain

- product ideas can drift into generic tooling
- the original ritual and voice can get flattened

### Success condition

Doghouse answers a general problem:

- state reconstruction
- semantic review deltas
- merge-readiness clarity

while still leaving room for BunBun, PhiedBach, and the worksheet ritual to remain the
public face of the product.

## Anti-Playbacks

Do not optimize for these first:

- organization-wide reviewer scorecards
- generic executive reporting
- full GitHub analytics warehousing
- replacing the PR page entirely
- adjudicating every thread inside the recorder itself
