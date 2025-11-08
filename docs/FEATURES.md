# Draft Punks — Feature Catalog (Expanded)

## Conventions

- Feature IDs: `DP-F-XX` (two digits); 
- Stories `DP-US-XXXX` (four digits).

## Each story lists

- Description
- Requirements
- Acceptance Criteria
- Definition of Ready (DoR)
- Test Plan

## Contents

- [ ] DP-F-00 Scroll View Widget
- [ ] DP-F-01 Title Screen
- [ ] DP-F-02 Main Menu — PR Selection
- [ ] DP-F-03 PR View — Comment Thread Selection
- [ ] DP-F-04 Comment View — Thread Traversal
- [ ] DP-F-05 LLM Interaction View
- [ ] DP-F-06 LLM Provider Management
- [ ] DP-F-07 GitHub Integration
- [ ] DP-F-08 Resolve/Reply Workflow
- [ ] DP-F-09 Automation Mode
- [ ] DP-F-10 Prompt Editing & Templates
- [ ] DP-F-11 Settings & Persistence
- [ ] DP-F-12 Merge Flow
- [ ] DP-F-13 Stash Dirty Changes Flow
- [ ] DP-F-14 Keyboard Navigation & Global Shortcuts
- [ ] DP-F-15 Status Bar & Key Hints
- [ ] DP-F-16 Theming & Layout
- [ ] DP-F-17 Logging & Diagnostics
- [ ] DP-F-18 Debug LLM (dev aid)
- [ ] DP-F-19 Image Splash (polish)

---

## DP-F-00 Scroll View Widget (Generic List/Picker)

### DP-US-0001 Scroll List With Footer

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to scroll List With Footer |
| **So that** | so I can reuse a consistent, performant list UX across screens. |


- [ ] Done

### Description

- [ ] A generic widget renders a titled, scrollable list and a footer like `Displaying [i–j] of N`.

#### Requirements

- [ ] Accepts items: 
- [ ] Sequence[T]; 
- [ ] item renderer: 
- [ ] (T)->Widget; 
- [ ] title str; 
- [ ] actions hint str.
- [ ] Up/Down move selection; 
- [ ] Home/End jump; 
- [ ] PgUp/PgDn paginate; 
- [ ] Enter selects item.
- [ ] Footer range reflects visible indices; 
- [ ] windowing handles long lists without perf issues.
- [ ] No child mounting during compose (populate in on_mount/on_show).

#### Acceptance Criteria

- [ ] With N=120 and a viewport of 8 lines, footer shows correct ranges as you scroll.
- [ ] Enter yields the selected item to a callback.
- [ ] No `MountError` during compose.

#### DoR

- [ ] API and lifecycle documented; 
- [ ] perf target: 
- [ ] 5k items < 50ms first paint.

#### Test Plan

- [ ] Unit: pagination math; range formatting; window boundaries.
- [ ] TUI: snapshot for header/footer; fuzz test with 2k items.

### DP-US-0002 Pluggable Item Renderer

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to use pluggable item renderer |
| **So that** | so I can reuse a consistent, performant list UX across screens. |


- [ ] Done

#### Requirements

- [ ] Renderer called only for visible items; 
- [ ] recycled when off-screen; 
- [ ] supports per-item key hooks.

#### Acceptance Criteria

- [ ] Rendering remains smooth for 1k items; 
- [ ] key hooks fire for the focused item.

#### DoR

- [ ] Hook interface; 
- [ ] event bubbling documented.

#### Test Plan

- [ ] Fake renderer counting calls; 
- [ ] key-hook assertion.

### DP-US-0003 Empty/Error States

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to use empty/error states |
| **So that** | so I can reuse a consistent, performant list UX across screens. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Show “(empty)” and “(failed to load)” variants with retry key.

#### Acceptance Criteria

- [ ] Press `r` calls reload callback.

#### Test Plan

- [ ] State transitions.

---

## DP-F-01 Title Screen

### DP-US-0101 Splash With Repo Info

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use splash with repo info |
| **So that** | so I land with context and clear next steps. |


- [ ] Done

#### Requirements

- [ ] Centered ASCII logo; 
- [ ] repo path; 
- [ ] remote URL; 
- [ ] branch; 
- [ ] dirty/clean status; 
- [ ] `[Enter] Continue  [Esc] Quit`.

#### Acceptance Criteria

- [ ] In a repo with dirty working tree, show 🚧; 
- [ ] outside a repo, show `unknown` placeholders;
- [ ] Enter→Main Menu; 
- [ ] Esc/Ctrl+C exit 0.

#### DoR

- [ ] Git helpers return (path, remote, branch, dirty) or safe fallbacks.

#### Test Plan

- [ ] Unit for git helpers (fake subprocess); 
- [ ] TUI snapshot with/without git.

### DP-US-0102 Logo Overrides

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use logo overrides |
| **So that** | so I land with context and clear next steps. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] DP_TUI_ASCII and DP_TUI_ASCII_FILE override the banner; 
- [ ] invalid file falls back to default.

#### Acceptance Criteria

- [ ] Given a valid file, banner equals file contents.

#### Test Plan

- [ ] Env-var injection tests.

---

## DP-F-02 Main Menu — PR Selection

### DP-US-0201 Fetch and Render PR List

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to fetch and Render PR List |
| **So that** | so I can choose the right PR quickly. |


- [ ] Done

#### Requirements

- [ ] Use GitHub Port to fetch open PRs; 
- [ ] render per SPEC: 
  - [ ] icon (✅🟡🛑🚫), 
  - [ ] number, 
  - [ ] `{ i, e }`, 
  - [ ] branch, 
  - [ ] author, 
  - [ ] age, 
  - [ ] truncated title (≤50 chars with `[…]`).

#### Acceptance Criteria

- [ ] Visuals match SPEC examples; 
- [ ] Enter on a PR navigates to PR View.

#### DoR

- [ ] Adapter returns head branch, 
- [ ] author login, 
- [ ] CI state, 
- [ ] issue/error counts or `None`.

#### Test Plan

- [ ] Fake adapter; 
- [ ] snapshot of three PRs; 
- [ ] age humanizer unit tests.

### DP-US-0202 PR Info Modal

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use pr info modal |
| **So that** | so I can choose the right PR quickly. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] `Space` shows full PR metadata incl. description/body; 
- [ ] close returns to list.

#### Acceptance Criteria

- [ ] Modal scrolls; 
- [ ] focus restoration on close.

#### Test Plan

- [ ] Modal open/close; 
- [ ] focus.

### DP-US-0203 Dirty Repo Banner & Stash Flow

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use dirty repo banner & stash flow |
| **So that** | so I can choose the right PR quickly. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] If dirty, show banner and `S` to stash; 
- [ ] flow: confirm → run git stash (or discard) → refresh list.

#### Acceptance Criteria

- [ ] After stash, banner disappears; 
- [ ] errors surfaced.

#### Test Plan

- [ ] Fake git runner; 
- [ ] error path.

### DP-US-0204 Settings Shortcut

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use settings shortcut |
| **So that** | so I can choose the right PR quickly. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] `s` opens settings screen; 
- [ ] saving persists and returns to list.

#### Acceptance Criteria

- [ ] Changes reflected in subsequent flows.

#### Test Plan

- [ ] Persistence read/write.

### DP-US-0205 Merge Shortcut

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to merge Shortcut |
| **So that** | so I can choose the right PR quickly. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] `m` triggers merge flow if mergeable; 
- [ ] guardrails per DP-F-12.

#### Acceptance Criteria

- [ ] Non-mergeable shows reason; 
- [ ] merge path succeeds via adapter.

#### Test Plan

- [ ] Fake merge adapter; 
- [ ] UI transitions.

---

## DP-F-03 PR View — Comment Thread Selection

### DP-US-0301 Render Threads With Filters

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to render Threads With Filters |
| **So that** | so I can focus on the relevant review threads. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Header with PR number/title/branches/author/status; list threads with path; 
- [ ] unresolved count per file; 
- [ ] filter `u` unresolved-only / `a` all.

#### Acceptance Criteria

- [ ] Filter toggles update list and counters.

#### Test Plan

- [ ] Fake threads; 
- [ ] filter logic.

### DP-US-0302 Toggle Resolved

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to toggle Resolved |
| **So that** | so I can focus on the relevant review threads. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] `r` toggles resolved flag for the focused thread via adapter.

#### Acceptance Criteria

- [ ] UI updates; 
- [ ] adapter resolve/unresolve call succeeds.

#### Test Plan

- [ ] Mutation calls captured.

### DP-US-0303 Start Automation

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to start Automation |
| **So that** | so I can focus on the relevant review threads. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] `A` starts automation mode across unresolved; progress bar; 
- [ ] `Space` pauses to manual.

#### Acceptance Criteria

- [ ] After completion, returns with summary.

#### Test Plan

- [ ] Fake LLM + step runner; 
- [ ] pause/resume.

## DP-F-04 Comment View — Thread Traversal

### DP-US-0401 Traverse and Inspect Thread

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use traverse and inspect thread |
| **So that** | so I can move through comments efficiently. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Show body (first line preview + full text panel), per-file and overall counters; 
- [ ] Left/Right prev/next; 
- [ ] Enter opens LLM Interaction.

#### Acceptance Criteria

- [ ] Counters correct; 
- [ ] traversal wraps within bounds; 
- [ ] Enter proceeds.

#### Test Plan

- [ ] Index math tests; 
- [ ] counter formatting.

### DP-US-0402 Context Blocks

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use context blocks |
| **So that** | so I can move through comments efficiently. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] If code context is available, show inline fenced blocks with language hints.

#### Acceptance Criteria

- [ ] Blocks render with scroll if long.

#### Test Plan

- [ ] Rendering snapshot.

## DP-F-05 LLM Interaction View

### DP-US-0501 Confirm/Send/Edit & Branching

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use confirm/send/edit & branching |
| **So that** | so feedback is acted on with minimal friction. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Confirm modal; 
- [ ] option to edit prompt; 
- [ ] send; 
- [ ] parse JSON tolerant to ```json fences.
- [ ] Success branch: “`LLM success is true. Mark as resolved? [Yes][No]`” → 
- [ ] call resolve when Yes → 
- [ ] auto-advance to next comment.
- [ ] Failure branch: “`LLM had an error: <err>. Continue? [Yes][No]`” → 
- [ ] Yes advances (unresolved); 
- [ ] No returns to Main Menu.

#### Acceptance Criteria

- [ ] Branching matches; 
- [ ] adapter resolve called with thread id.

#### Test Plan

- [ ] Fake LLM returning `success/failure/non-JSON`;
- [ ] flow assertions.

### DP-US-0502 Automation Mode

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use automation mode |
| **So that** | so feedback is acted on with minimal friction. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Auto send remaining (file/PR scope); 
- [ ] `Space` pauses; 
- [ ] progress bar;
- [ ] summary list of commits.

#### Acceptance Criteria

- [ ] Pause toggles; 
- [ ] summary lists SHAs.

#### Test Plan

- [ ] Simulated multi-thread run.

### DP-US-0503 Prompt Editor

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use prompt editor |
| **So that** | so feedback is acted on with minimal friction. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] `e` opens editor with prompt; upon save, send the edited prompt.

#### Acceptance Criteria

- [ ] `run()` receives edited content.

#### Test Plan

- [ ] Editor harness stub; 
- [ ] content compare.

---

## DP-F-06 LLM Provider Management

### DP-US-0601 Choose Provider

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to choose Provider |
| **So that** | so I can use my preferred LLM provider reliably. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Modal lists `Codex/Claude/Gemini/Debug/Other`; 
- [ ] persisted per repo under `~/.draft-punks/<repo>/config.json`.

#### Acceptance Criteria

- [ ] Setting survives restart; 
- [ ] reflected in command builder.

#### Test Plan

- [ ] Persistence test.

### DP-US-0602 “Other” Template

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to use “other” template |
| **So that** | so I can use my preferred LLM provider reliably. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Input accepts command template with `{prompt}` token.

#### Acceptance Criteria

- [ ] Builder substitutes token; 
- [ ] shell-escapes args.

#### Test Plan

- [ ] Builder unit tests.

### DP-US-0603 Flags

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to use flags |
| **So that** | so I can use my preferred LLM provider reliably. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] reply_on_success, force_json toggles (in Settings screen).

#### Acceptance Criteria

- [ ] reply_on_success posts reply; 
- [ ] force_json adds provider-appropriate flag.

#### Test Plan

- [ ] Mutation call; 
- [ ] argv inspection.

---

## DP-F-07 GitHub Integration

### DP-US-0701 PR List via HTTP/CLI

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to use pr list via http/cli |
| **So that** | so I can work against GitHub without manual copy/paste. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Use token HTTP GraphQL if `GH_TOKEN`/`GITHUB_TOKEN` present; 
- [ ] else fall back to gh CLI; 
- [ ] consistent objects.

#### Acceptance Criteria

- [ ] Both paths produce identical fields for list screen.

#### Test Plan

- [ ] Recorded fixtures; 
- [ ] CLI runner stub.

### DP-US-0702 Threads/Reply/Resolve

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to use threads/reply/resolve |
| **So that** | so I can work against GitHub without manual copy/paste. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Iterate review threads; 
- [ ] post replies with body; 
- [ ] resolve threads.

#### Acceptance Criteria

- [ ] Mutations succeed; 
- [ ] error surfaces.

#### Test Plan

- [ ] GraphQL tests; 
- [ ] error handling.

### DP-US-0703 Rate Limit & Paging

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to use rate limit & paging |
| **So that** | so I can work against GitHub without manual copy/paste. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Page through >100 threads; 
- [ ] honor API rate limits; 
- [ ] show progress callback.

#### Test Plan

- [ ] Paging loop unit tests.

---

## DP-F-08 Resolve/Reply Workflow

### DP-US-0801 reply_on_success

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to use reply_on_success |
| **So that** | so GitHub reflects the work I completed. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] When enabled, after a successful LLM response with commits, post a reply including the first SHA.

#### Acceptance Criteria

- [ ] Reply content includes SHA and attribution; 
- [ ] errors logged but non-fatal.

#### Test Plan

- [ ] Mutation assertions.

### DP-US-0802 Manual Resolve

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to use manual resolve |
| **So that** | so GitHub reflects the work I completed. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] On success branch, “Resolve?” modal drives resolve_thread call.

#### Acceptance Criteria

- [ ] Resolved threads disappear from unresolved filter lists.

#### Test Plan

- [ ] Adapter toggle/resolve verified.

---

## DP-F-09 Automation Mode

### DP-US-0901 Auto Remaining (PR/File scope)

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to auto Remaining (PR/File scope) |
| **So that** | so I can process large PRs efficiently. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Start from PR View; 
- [ ] mode selection; 
- [ ] progress bar; 
- [ ] pause; 
- [ ] summary.

#### Test Plan

- [ ] Controller tests.

---

## DP-F-10 Prompt Editing & Templates

### DP-US-1001 Editor & Tokens

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to use editor & tokens |
| **So that** | so I can tailor prompts to get better outcomes. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] External editor integration; 
- [ ] support tokens: {file_path},{lines},{author}.

#### Test Plan

- [ ] Token substitution tests; 
- [ ] golden prompt snapshot.

---

## DP-F-11 Settings & Persistence

### DP-US-1101 Settings Screen

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to use settings screen |
| **So that** | so settings persist per repo and affect behavior. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Manage provider, reply_on_success, force_json; 
- [ ] save per repo.

#### Test Plan

- [ ] Persistence and effect on flows.

---

## DP-F-12 Merge Flow

### DP-US-1201 Merge With Guardrails

#### User Story

|  |  |
|--|--|
| **As a** | Maintainer |
| **I want** | to merge With Guardrails |
| **So that** | so compliant and safe merges happen from within the tool. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] CI green; 
- [ ] approvals met; 
- [ ] fast-forward preference; 
- [ ] confirmation modal; 
- [ ] gh CLI path.

#### Test Plan

- [ ] Fake adapter; 
- [ ] error handling.

---

## DP-F-13 Stash Dirty Changes Flow

### DP-US-1301 Detect & Stash

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to detect & Stash |
| **So that** | so my workspace is clean before automated actions run. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Detect dirty; `S` to stash; 
- [ ] confirm; 
- [ ] show result.

#### Test Plan

- [ ] Git stub.

---

## DP-F-14 Keyboard Navigation & Global Shortcuts

### DP-US-1401 Global Quit & Navigation

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use global quit & navigation |
| **So that** | so the app feels predictable and fast to operate. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Esc/Ctrl+C quit anywhere; 
- [ ] Left/Right prev/next at Comment View; 
- [ ] help overlay key.

#### Test Plan

- [ ] Keybinding tests; 
- [ ] overlay snapshot.

---

## DP-F-15 Status Bar & Key Hints

### DP-US-1501 Context Hints

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use context hints |
| **So that** | so I always know what I can do next. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Persistent footer shows current keys (e.g., “↑/↓ pick • Enter select • Space info • Esc back”).

#### Test Plan

- [ ] Footer component snapshots.

---

## DP-F-16 Theming & Layout

### DP-US-1601 Legibility

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use legibility |
| **So that** | so the UI remains legible in any theme. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Dark/light palettes; 
- [ ] minimum contrast; centered title.

#### Test Plan

- [ ] Visual audit.

---

## DP-F-17 Logging & Diagnostics

### DP-US-1701 Log Sink & Non‑JSON Capture

#### User Story

|  |  |
|--|--|
| **As a** | Maintainer |
| **I want** | to use log sink & non‑json capture |
| **So that** | so we can diagnose issues without guesswork. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Log info/warn/error; 
- [ ] capture raw non‑JSON output in a fenced block.

#### Test Plan

- [ ] Logger stub assertions.

---

## DP-F-18 Debug LLM (dev aid)

### DP-US-1801 Prompt Preview & Simulation

#### User Story

|  |  |
|--|--|
| **As a** | Contributor |
| **I want** | to use prompt preview & simulation |
| **So that** | so I can test flows without external LLM dependencies. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Show prompt; 
- [ ] options to Emit success / Simulate failure; 
- [ ] use HEAD sha when emitting success; 
- [ ] ask Resolve? after success; 
- [ ] Continue? after failure.

#### Test Plan

- [ ] Modal branch tests; commit list update.

---

## DP-F-19 Image Splash (polish)

### DP-US-1901 bunbun.webp Splash

#### User Story

|  |  |
|--|--|
| **As a** | User |
| **I want** | to use bunbun.webp splash |
| **So that** | so the app feels polished and welcoming. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] When DP_TUI_IMAGE is set to a valid path, render image on splash; 
- [ ] fallback to ASCII.

#### Test Plan

- [ ] Feature flag test; 
- [ ] rendering smoke test.

---

## DP-F-20 Modularization & Packaging (Monorepo, Multi‑Package)

### DP-US-2001 Create multi‑package layout

#### User Story

|  |  |
|--|--|
| **As a** | Maintainer |
| **I want** | to use create multi‑package layout |
| **So that** | so development, testing, and releases scale cleanly. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

### Description

Restructure repo into packages: 

- `draft-punks-core`
- `draft-punks-llm`
- `draft-punks-cli`
- `draft-punks-tui`
- `draft-punks-automation`

#### Requirements

- [ ] Each package has its own `pyproject.toml`, `src/` layout, and tests.
- [ ] Root uses a workspace/dev env (Makefile or uv/hatch) to run all.
- [ ] Keep backward compatibility: provide shim imports or a metapackage so existing imports keep working during transition.
- [ ] Dev wrapper (`draft-punks-dev`) continues to function (prefers TUI package in workspace).

#### Acceptance Criteria

- [ ] `pipx install draft-punks-tui` installs a working TUI.
- [ ] `pipx install draft-punks-cli` installs a working CLI.
- [ ] In dev, `make dev-venv && draft-punks-dev tui` launches TUI across packages.
- [ ] DoR:
- [ ] Package boundaries decided; 
- [ ] mapping doc from old modules to new packages.
- [ ] Tooling choice (hatch/uv/poetry) agreed; 
- [ ] Makefile updated.

#### Test Plan

- [ ] Smoke tests for CLI/TUI packages; 
- [ ] import tests for shim modules; 
- [ ] CI matrix builds per package.

### DP-US-2002 Compatibility shims & metapackage

#### User Story

|  |  |
|--|--|
| **As a** | Maintainer |
| **I want** | to use compatibility shims & metapackage |
| **So that** | so development, testing, and releases scale cleanly. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Provide `draft_punks` top‑level shim that re‑exports from new packages; 
- [ ] add a metapackage `draft-punks` that depends on the split packages.

#### Acceptance Criteria

- [ ] Existing scripts/imports still run; 
- [ ] deprecation notices logged.

#### Test Plan

- [ ] Import path tests; 
- [ ] runtime warn capture.

### DP-US-2003 Packaging CI

#### User Story

|  |  |
|--|--|
| **As a** | Maintainer |
| **I want** | to use packaging ci |
| **So that** | so development, testing, and releases scale cleanly. |


#### DoR

- [ ] Stakeholders identified and story reviewed
- [ ] Dependencies and external APIs clarified
- [ ] Acceptance criteria finalized
- [ ] Test data/fixtures available
- [ ] Telemetry/logging needs defined (if applicable)


- [ ] Done

#### Requirements

- [ ] Add build/test workflows to build wheels/sdists for each package; 
- [ ] ensure `pipx install` smoke.

#### Test Plan

- [ ] CI green across Python 3.11/3.12/3.14; 
- [ ] artifact checks.