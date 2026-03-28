# Draft Punks — Drift Report

Date: 2025-11-07

Purpose
- Identify gaps between docs/SPEC.md and the current implementation.
- List features present in code but not in SPEC (positive drift).
- Call out conflicts or divergences that need decisions.

Summary
- The project implements a working Title → PR list → Comment viewer → LLM send flow with partial success/failure handling and thread resolution. However, several screens and widgets in SPEC (custom Scroll View, dedicated PR View screen, status/key hint bar, merge/stash flows) are not yet implemented. Some flows currently live as modals inside the Comment Viewer rather than separate screens as specified.

Positive Drift (implemented but not in SPEC)
- DP-F-18 Debug LLM: A developer-facing LLM that previews the prompt and simulates success/failure for interactive testing.
- Dev convenience: `draft-punks-dev` wrapper targeting the repo’s `.venv`, and Make targets (`dev-venv`, `install-dev`, `tui`).
- Batch send (Comment Viewer) with progress bar existed prior; SPEC defines Automation Mode primarily from PR View.

Negative Drift (specified but missing/partial)
1) DP-F-00 Scroll View Widget
   - Missing: Generic scroll widget with footer (`Displaying [i-j] of N]`) and per-item key hints.
   - Current: Using Textual `ListView` directly; no footer range.

2) DP-F-01 Title Screen
   - Missing: Repo info (path/remote/branch/dirty) not shown yet.
   - Implemented: ASCII logo, Enter→continue, Esc/Ctrl+C quit.

3) DP-F-02 Main Menu — PR Selection
   - Missing: Rich PR list item (icon/status, author, age, {i,e}); info modal; merge flow; stash flow; settings shortcut.
   - Current: Basic PR list with `- #num (branch) title`; Enter opens Comment Viewer (bypasses PR View).

4) DP-F-03 PR View — Comment Thread Selection
   - Missing: Separate screen with unresolved/all filters, toggle resolved, Automation (A), and header with PR summary.
   - Current: Not implemented as a separate screen; we go straight to Comment Viewer.

5) DP-F-04 Comment View — Thread Traversal
   - Partial: Body display, counters, Left/Right prev/next are implemented; “Go to previous” option exists in send prompt.
   - Missing: Code/context blocks, richer formatting.

6) DP-F-05 LLM Interaction View
   - Partial: Confirm/send prompt modal; success→Resolve?; failure→Continue? with return-to-main.
   - Missing: Dedicated screen (currently modal); prompt editor mode.

7) DP-F-06 LLM Provider Management
   - Partial: Provider chooser modal + per-repo persistence.
   - Missing: Central Settings screen to manage flags.

8) DP-F-07 GitHub Integration
   - Implemented: list PRs (HTTP/gh), iterate threads, post replies, resolve thread.
   - Missing: Toggle resolved state from PR View screen (since screen not yet implemented).

9) DP-F-08 Resolve/Reply Workflow
   - Partial: reply_on_success posts a reply; “Resolve?” step implemented on success.
   - Missing: UI toggle in Settings.

10) DP-F-09 Automation Mode
   - Partial: Batch send from Comment Viewer.
   - Missing: Start from PR View; pause/resume; scope selection UI.

11) DP-F-10 Prompt Editing & Templates
   - Missing: Editor flow; template tokens for context.

12) DP-F-11 Settings & Persistence
   - Missing: Dedicated Settings screen (reply_on_success, force_json, provider, etc.).

13) DP-F-12 Merge Flow
   - Missing completely.

14) DP-F-13 Stash Dirty Changes Flow
   - Missing completely (no dirty banner/flow).

15) DP-F-15 Status Bar & Key Hints
   - Missing persistent hints; Help overlay exists but not context bar.

16) DP-F-16 Theming & Layout
   - Partial: Centered title; no legibility audit yet.

Conflicts / Decisions Needed
- Screen structure: SPEC defines four primary screens including PR View; current app navigates Title → PR list → Comment Viewer (no PR View). Decision: implement PR View per spec and rewire navigation, or keep combined view and update SPEC.
- Automation locus: SPEC starts Automation from PR View; we currently have batch from Comment Viewer. Decision: move to PR View and deprecate viewer batch, or keep both with consistent semantics.
- Quit behavior: We bound Esc/Ctrl+C to quit globally (spec aligns). Confirm if Esc should close modals first or always exit the app.
- Status/key hints: SPEC expects persistent hints; we only have a Help modal. Decision: add status bar component.

Recommended Next Steps
1) Implement Scroll View widget (DP-F-00) and retrofit Main Menu & PR View to it.
2) Add PR View screen with filters/toggles; move Automation there; wire “Resolve” toggle.
3) Title repo info section; Main Menu item renderer per spec (author/age/status).
4) Settings screen (reply_on_success, force_json, provider); integrate into flows.
5) Prompt editor path; optional template tokens.
6) Optional: status bar with context-specific key hints.

