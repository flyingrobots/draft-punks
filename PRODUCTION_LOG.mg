# Draft Punks — Production Log

Guideline: Append an entry for any unexpected/unanticipated work, dependency, requirement, or risk we discover during implementation and testing.

Template

````markdown
## Incident: <title>

Timestamp: <YYYY-MM-DD HH:MM:SS local>

Task: <current task id>

### Problem

<problem description>

### Resolution

<resolution>

### What could we have done differently

<how could this have been anticipated? how should we have planned for this? what can we do better next time to avoid this sort of issue again?>
````

Initial Entries

- (none yet)

## Incident: Product Pivot to CLI-Only (Git-backed State)

Timestamp: 2025-11-07 19:07:32

Task: DP-F-20 / Sprint 0 planning

### Problem
TUI cannot be driven programmatically in our harness and is slower to iterate for both humans and LLMs.

### Resolution
Pivot to a CLI-only experience with a Git-backed state repo and JSONL stdio server. Update SPRINTS.md, add CLI-STATE.md, and refocus FEATURES/TASKLIST over time.

### What could we have done differently
Call out environment constraints earlier and consider dual-mode from day one. Favor CLI-first for automation-heavy tools; treat TUI as an optional skin over the same state engine.

## Incident: Local test runner missing (pytest not installed)

Timestamp: 2025-11-08 00:00:00

Task: DP-F-30 / Thread verbs + Debug LLM (tests-first)

### Problem
The environment lacks `pytest`, so tests could not be executed immediately after adding failing tests.

### Resolution
Committed failing tests first, then implemented the features. Left tests in place for local/CI execution. Next dev step is `make dev-venv && . .venv/bin/activate && pip install -e .[dev] && pytest`.

### What could we have done differently
Include a lightweight script or Makefile target that ensures a dev venv with pytest is provisioned before test steps, or run tests inside CI where the toolchain is guaranteed.
