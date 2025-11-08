# git mind — Features & User Stories (v0.1)

## Conventions
- Feature IDs: GM-F-XX
- Stories: GM-US-XXXX
- Each story includes Description, Requirements, Acceptance, DoR, Test Plan

## GM-F-00 Snapshot Engine & JSONL

### GM-US-0001 Snapshot commits under refs/mind/sessions/*
#### User Story
|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to write state as snapshot commits with trailers |
| **So that** | I can time‑travel and audit every action in Git |

#### Requirements
- hash-object, mktree, commit-tree, update-ref CAS (no worktree/index)
- trailers: DP-Op, DP-Args, DP-Result, DP-State-Hash, DP-Version

#### Acceptance
- git show refs/mind/sessions/<name>:state.json round-trips
- trailers contain the required keys; blob hash matches DP-State-Hash

#### DoR
- [ ] Git plumbing patterns documented
- [ ] Trailer fields agreed

#### Test Plan
- Temp repo test: snapshot write + trailer parsing

### GM-US-0002 JSONL serve --stdio (hello, state.show, repo.detect, pr.list, pr.select)
#### User Story
|  |  |
|--|--|
| **As a** | Agent |
| **I want** | to converse via JSON Lines with expect_state guards |
| **So that** | I can drive deterministic flows without a TTY |

#### Requirements
- One JSON request per line; one response per line
- Responses include state_ref; errors include codes
- Mutations accept expect_state (CAS) and return STATE_MISMATCH on conflict

#### Acceptance
- Manual and automated JSONL sessions behave deterministically

#### DoR
- [ ] Error codes finalized; envelope schema documented

#### Test Plan
- Unit test handle_command for each verb; CAS mismatch case

## GM-F-01 PR & Threads

### GM-US-0101 PR list/select
#### User Story
|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to list and select PRs |
| **So that** | I can scope subsequent actions |

#### Requirements
- HTTP with GH_TOKEN or gh CLI fallback
- Cache pr_cache in state; selection.pr set on select

#### Acceptance
- Cache and selection are visible in state.json and via JSONL

#### DoR
- [ ] Adapters available; rate limits handled

#### Test Plan
- Fake adapters; list/select round-trips

## GM-F-02 LLM Debug & Real Template
- Stories to be filled as we land Sprint 2

## GM-F-03 Artifacts & Remotes
- Stories to be filled in Sprint 3

## GM-F-04 Locks & Consensus
- Stories to be filled in Sprints 4–5
