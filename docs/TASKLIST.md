# Draft Punks — User Story Checklist

Legend
- [ ] not started
- [~] in progress
- [x] done (implemented in codebase)

Note: Nested checklists under each story break down tasks required to ship the story.

## DP-F-00 Scroll View Widget

- [ ] DP-US-0001 Generic scroll list with title/footer
  - [ ] API: `ScrollView(items, render_item, title, footer_actions)`
  - [ ] Pagination math and footer (`Displaying [i-j] of N`)
  - [ ] Up/Down/Home/End/PgUp/PgDn/Enter handlers
  - [ ] Populate-after-mount lifecycle to avoid mount errors
  - [ ] Unit tests (pagination + range formatting)
  - [ ] Snapshot tests
  - [ ] Retrofit Main Menu to use Scroll View
  - [ ] Retrofit PR View to use Scroll View

- [ ] DP-US-0002 Pluggable item renderer
  - [ ] Item renderer protocol and docs
  - [ ] Performance sanity (>1k items)
  - [ ] Example renderers (PR item, Thread item)
  - [ ] Item-level key hook delegation

- [ ] DP-US-0003 Empty/Error states & reload
  - [ ] Render "(empty)" state when list is empty
  - [ ] Render "(failed to load)" with cause in log
  - [ ] `r` to reload callback
  - [ ] Snapshot tests for both states

## DP-F-01 Title Screen

- [~] DP-US-0101 Splash with repo info; Enter continue; Esc/Ctrl+C quit
  - [x] Centered logo (ASCII; override via env)
  - [ ] Repo details (path/remote/branch/status) shown
  - [x] Enter→Main Menu
  - [x] Esc/Ctrl+C quit with exit 0
  - [ ] Snapshot test
  
- [ ] DP-US-0102 Logo overrides
  - [x] DP_TUI_ASCII and DP_TUI_ASCII_FILE respected
  - [ ] Error fallback test

## DP-F-02 Main Menu — PR Selection

- [ ] DP-US-0201 List open PRs; Enter opens PR View
  - [x] Fetch open PRs (HTTP or gh CLI)
  - [ ] Render per spec fields (icon/status/author/age/truncated title/{i,e})
  - [ ] Scroll view integration (footer range)
  - [ ] Enter→PR View screen (not Comment View)
  - [ ] Age humanizer
  - [ ] Snapshot tests

- [ ] DP-US-0202 Space info; m merge; s settings; S stash
  - [ ] PR info modal
  - [ ] Merge flow (guards)
  - [ ] Dirty banner + stash flow
  - [ ] Settings open

## DP-F-03 PR View — Comment Thread Selection

- [ ] DP-US-0301 Threads list with filters and toggle resolved
  - [ ] Render threads (path, counts, resolved flag)
  - [ ] Filters: unresolved-only (u), all (a)
  - [ ] Toggle resolved (r)
  - [ ] Scroll view integration

- [ ] DP-US-0302 Automation on unresolved (A)
  - [ ] Launch automation controller
  - [ ] Pause/resume with Space

## DP-F-04 Comment View — Thread Traversal

- [~] DP-US-0401 Show thread; Left/Right traverse; Enter→LLM View
  - [x] Detail pane shows body
  - [x] Left/Right to prev/next
  - [x] Counters update (per-file and overall)
  - [ ] Enter→LLM View (currently opens prompt modal inside same screen)
  - [ ] Code/context blocks if available

## DP-F-05 LLM Interaction View

- [~] DP-US-0501 Confirm/send; edit prompt; branch on JSON
  - [x] Confirm send modal
  - [ ] Prompt editor path
  - [x] On success → Ask resolve?
  - [x] On failure → Continue? (No returns to PR list)
  - [x] Parser tolerant to code fences

- [~] DP-US-0502 Automation mode
  - [x] Batch send existing (`a`) with progress bar
  - [ ] Pause/resume with Space and return to manual mode
  - [ ] Scope to file/PR switches from PR View

## DP-F-06 LLM Provider Management

- [~] DP-US-0601 Choose provider and persist
  - [x] Modal with Codex/Claude/Gemini/Other/Debug
  - [x] ‘Debug LLM’ option for dev/testing
  - [x] Per-repo persistence
  - [x] Command builder honors config
  - [ ] Settings screen (centralized)

## DP-F-07 GitHub Integration

- [x] DP-US-0701 PR list via HTTP or gh
  - [x] HTTP adapter (GraphQL)
  - [x] gh CLI adapter
  - [x] Fallback selection
  - [ ] Robust error surfacing

- [~] DP-US-0702 Threads; reply; resolve
  - [x] iter_review_threads
  - [x] post_reply
  - [x] resolve_thread
  - [ ] Toggle resolved state from PR View
  - [ ] Paging progress callback surfaced in UI

## DP-F-08 Resolve/Reply Workflow

- [~] DP-US-0801 reply_on_success & resolve
  - [x] reply_on_success support
  - [x] Ask Resolve? modal
  - [ ] Settings toggle in UI

## DP-F-09 Automation Mode

- [ ] DP-US-0901 Auto process unresolved with progress and pause
  - [ ] Controller and UI in PR View
  - [ ] Pause/resume; end-of-run summary

## DP-F-10 Prompt Editing & Templates

- [ ] DP-US-1001 Edit prompt; template tokens
  - [ ] Editor integration
  - [ ] Token substitution (file path, snippet, author)

## DP-F-11 Settings & Persistence

- [ ] DP-US-1101 Settings screen
  - [ ] Toggle reply_on_success, force_json, provider

## DP-F-12 Merge Flow

- [ ] DP-US-1201 Merge with guardrails
  - [ ] Pre-conditions (CI passing, approvals)
  - [ ] Error handling

## DP-F-13 Stash Dirty Changes Flow

- [ ] DP-US-1301 Detect dirty and stash/discard
  - [ ] Dirty banner on Main Menu
  - [ ] Stash workflow (S)

## DP-F-14 Keyboard Navigation & Global Shortcuts

- [x] DP-US-1401 Global Esc/Ctrl+C; Left/Right; help overlay
  - [x] Esc and Ctrl+C quit anywhere
  - [x] Left/Right in comment view
  - [ ] Help overlay with key hints

## DP-F-15 Status Bar & Key Hints

- [ ] DP-US-1501 Persistent hints
  - [ ] Footer/status bar component

## DP-F-16 Theming & Layout

- [ ] DP-US-1601 Light/dark legibility; centered title
  - [x] Centered title CSS
  - [ ] Legibility audit

## DP-F-17 Logging & Diagnostics

- [~] DP-US-1701 In-app log sink; non-JSON capture
  - [x] TextualLogger adapter (App.log compatible)
  - [x] Non-JSON captured to log/markdown block
  - [ ] Optional transcript capture

## DP-F-18 Debug LLM (dev aid)

- [x] DP-US-1801 Show prompt; simulate success/failure
  - [x] Debug modal with prompt preview
  - [x] Emit success (uses HEAD sha) / simulate failure

## DP-F-19 Image Splash (polish)

- [ ] DP-US-1901 bunbun.webp splash via flag
  - [ ] Rich+Pillow rendering path

## DP-F-20 Modularization & Packaging (Monorepo, Multi‑Package)

- [ ] DP-US-2001 Create multi‑package layout
  - [ ] Decide boundaries and mapping (ARCHITECTURE.md)
  - [ ] Create `packages/draft-punks-core` with domain/services/ports
  - [ ] Create `packages/draft-punks-llm` with LLM port/adapters
  - [ ] Create `packages/draft-punks-cli` with entrypoint(s)
  - [ ] Create `packages/draft-punks-tui` with TUI app
  - [ ] Create `packages/draft-punks-automation` with batch mode
  - [ ] Root workspace tooling (Makefile, optional uv/hatch workspace)
  - [ ] Update dev wrapper to prefer TUI package in workspace
  - [ ] Smoke tests for CLI/TUI installs

- [ ] DP-US-2002 Compatibility shims & metapackage
  - [ ] Keep `src/draft_punks` as shims temporarily (re-export from packages)
  - [ ] Optional metapackage `draft-punks` depending on subpackages
  - [ ] Deprecation warnings on shim imports
  - [ ] Import path tests

- [ ] DP-US-2003 Packaging CI
  - [ ] CI builds wheels/sdists per package on 3.11/3.12/3.14
  - [ ] pipx install smoke for `draft-punks-cli` and `draft-punks-tui`
