# Draft Punks — CLI State & Protocol

This document defines the stateful CLI design for Draft Punks and the JSONL stdio protocol for LLM-driven or programmatic use. We intentionally pivot away from a TUI toward a powerful, scriptable CLI that is pleasant for humans and machines.

---

## Goals
- Human-friendly subcommands with useful table output.
- Machine-friendly JSON/JSONL with deterministic behavior.
- Stateful sessions backed by Git for time travel, branching, and audit.
- Clear, explicit side effects (GitHub replies/resolves) gated by flags.

## State: Git-Backed

- Location: `~/.draft-punks/state/<owner>/<repo>` (separate repo; never nested in the project repo).
- Pointer file in your project: `.draft-punks/state` contains an absolute path to the state repo for convenience.
- Branches: `sess/<name>` (default `sess/main`).
- Snapshots: annotated tags `snap/YYYYMMDD-HHMMSS`.

### Tree contents at HEAD
- `state.json` — canonical state summary (repo, filters, selection, options, llm provider)
- `selection.json` — `{ "pr": <num>, "thread_id": "..." }`
- `filters.json` — current filters
- `cache/pr/<number>/threads.json` — lazily cached thread lists per PR
- `llm/config.json` — provider, template, flags (non-secret)
- `journal/YYYY/MM/DD/<hhmmssZ>_<op>.json` — optional append-only input/output record

### Commit trailers (journal/index)
Use `git interpret-trailers` format in commit messages:

- `DP-Op: pr.list`
- `DP-Args: author=coderabbitai&unresolved=true`
- `DP-Result: ok|fail`
- `DP-State-Hash: <blob sha of state.json>`
- `DP-Idempotency: <uuid>` (optional)
- `DP-Version: 0`

This keeps state human-diffable (files) and the log searchable (trailers).

### State Integrity
- Atomic writes: temp file + rename before staging.
- Locking: `.lock` file to serialize mutating commands.
- No secrets: GH tokens remain env/OS keychain; config stores booleans and templates only.

---

## CLI Shape

```
# Sessions
$ dp session new [--id NAME]
$ dp session use NAME
$ dp session list
$ dp session show
$ dp session clear

# Repo
$ dp repo detect [--path .]
$ dp repo set --owner ORG --repo NAME

# PR
$ dp pr list [--author USER] [--unresolved] [--format json|table]
$ dp pr select NUMBER
$ dp pr info [NUMBER]

# Threads
$ dp thread list [--unresolved] [--author coderabbitai]
$ dp thread select ID
$ dp thread show [ID]
$ dp thread resolve ID [--yes]
$ dp thread reply ID --body "..." [--yes]

# LLM
$ dp llm provider set codex|claude|gemini|debug|other
$ dp llm template set "myllm -f json -p {prompt}"
$ dp llm send [--thread ID] [--debug success|fail] [--auto file|pr]

# State
$ dp state show [--format json|table]
$ dp state export <file.json>
$ dp state import <file.json>
$ dp state undo | redo | branch <name> | snapshot -m "..."

# Machine mode
$ dp serve --stdio                # JSON Lines (see below)
```

- Every command mutates state (when applicable) and commits a change with trailers.
- Non-mutating commands still read state and can output JSON with `--format json`.
- Destructive/remote side-effects require `--yes` or config defaults.

### Output format
- Default human table output for humans.
- `--format json` returns a single JSON object describing the result and including `state_ref` (commit sha).

---

## JSONL Protocol: `dp serve --stdio`

Send one JSON command per line; receive exactly one JSON response per line.

Example session

```
{ "id": "1", "cmd": "repo.detect", "args": {"path": "."}}
{ "id": "2", "cmd": "pr.list", "args": {"unresolved": true, "author": "coderabbitai"}}
{ "id": "3", "cmd": "pr.select", "args": {"number": 123}}
{ "id": "4", "cmd": "thread.list", "args": {"unresolved": true}}
{ "id": "5", "cmd": "llm.send", "args": {"thread_id": "MDEx...", "debug": "success"}}
```

Responses include `ok`, `result`, and `state_ref`:

```
{ "id": "1", "ok": true,  "result": {"owner": "flyingrobots", "repo": "draft-punks"}, "state_ref": "3ac2b11" }
{ "id": "2", "ok": true,  "result": {"total": 3, "items": [...]},                  "state_ref": "3b02af7", "event": "state.updated" }
{ "id": "3", "ok": true,  "result": {"current_pr": 123},                           "state_ref": "5c8707f" }
{ "id": "4", "ok": true,  "result": {"total": 12, "unresolved": 9, "items": [...]}, "state_ref": "2b71c10" }
{ "id": "5", "ok": true,  "result": {"success": true, "commits": ["a1b2c3"]},     "state_ref": "59fd7a4" }
```

Errors:
```
{ "id": "2", "ok": false, "error": {"code": "NO_PR", "message": "No PR matches filters"}, "state_ref": "3b02af7" }
```

### Mermaid — Serve Protocol

```mermaid
sequenceDiagram
  participant C as Client (LLM)
  participant D as dp serve --stdio
  participant S as State Repo

  C->>D: {cmd:"repo.detect"}
  D->>S: read/write state; commit
  S-->>D: HEAD sha
  D-->>C: {ok:true, result:{...}, state_ref:sha}

  C->>D: {cmd:"pr.list", args:{unresolved:true}}
  D->>S: update filters, cache; commit
  D-->>C: {ok:true, result:{items:[...]}, state_ref:sha, event:"state.updated"}
```

---

## Mermaid — State Commit Flow

```mermaid
flowchart LR
  A[CLI command] --> V[Validate args]
  V --> R[Acquire lock]
  R --> W[Write files (state.json, etc.)]
  W --> C[git add + commit with trailers]
  C --> U[Release lock]
  U --> O[Output result with state_ref]
```

---

## Idempotency & Concurrency
- `--idempotency-key` accepted by mutating commands; duplicates are no‑ops (detected via trailers in recent history).
- Locking prevents concurrent mutations; commands backoff and retry briefly.

## Security
- No tokens saved; only non-secret config in files.
- Replies/resolves require `--yes` or prior configuration.

## Migration from TUI
- TUI postponed to backlog. All SPEC flows map to CLI commands with deterministic outputs.
- Future: a minimal TUI could read/write the same Git‑backed state for a hybrid experience.

### Supported Commands (v0.1)
- `hello` / `mind.hello` — returns version + repo context
- `state.show` — returns current state.json
- `repo.detect` — detects owner/repo and writes snapshot
- `pr.list` — caches list of open PRs
- `pr.select { number:int }` — sets current PR
- `thread.list` — lists threads for the selected PR; caches minimal projection `{id, path, comment_count}`
- `thread.select { id:str }` — sets current thread id
- `thread.show [{ id:str }]` — shows details for selected or given thread from cache
- `llm.send { debug:success|fail, prompt?:str }` — Debug LLM path; success returns `{ success:true, commits:["deadbeef"], error:"", prompt }`; fail returns error `LLM_DEBUG_FAIL`

### Error Schema
```
{ "id": "...", "ok": false, "error": { "code": "...", "message": "...", "details"?: {...} }, "state_ref": "<sha>" }
```

Common codes:
- `STATE_MISMATCH` — CAS guard failed (pass `expect_state`)
- `INVALID_ARGS` — missing/invalid args or no selection
- `NOT_FOUND` — referent missing (e.g., thread not in cache)
- `UNKNOWN_COMMAND` — unrecognized command
- `LLM_DEBUG_FAIL` — simulated LLM failure (debug path)
