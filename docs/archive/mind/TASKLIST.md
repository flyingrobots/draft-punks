# git mind — Task List (v0.1)

Legend: [ ] not started, [~] in progress, [x] done

## GM-F-00 Snapshot & JSONL
- [x] GM-US-0001 snapshot commits under refs/mind/sessions/*
  - [x] plumbing helpers (hash-object, mktree, commit-tree, update-ref)
  - [x] write/read state.json; trailers; CAS
  - [x] tests (temp repo) — ready to run locally
- [~] GM-US-0002 JSONL serve --stdio
  - [x] hello, state.show, repo.detect
  - [x] pr.list, pr.select
  - [ ] error schema doc; unit tests for dispatcher

## GM-F-01 PR & Threads
- [~] GM-US-0101 PR list/select
  - [x] adapters (HTTP/gh) selection
  - [x] pr-list/pr-pick CLI; cache+selection in state
  - [ ] JSONL tests; rate limit handling
- [ ] GM-US-0102 Thread list/select/show
  - [ ] adapters thread iteration
  - [ ] CLI + JSONL verbs; state selection.thread_id

## GM-F-02 LLM Debug & Real Template
- [ ] GM-US-0201 debug path (prompt preview; success/fail)
- [ ] GM-US-0202 real template via command runner

## GM-F-03 Artifacts & Remotes
- [ ] GM-US-0301 local blob store + descriptors
- [ ] GM-US-0302 mind remote init/sync
- [ ] GM-US-0303 optional LFS publish

## GM-F-04 Locks & Consensus
- [ ] GM-US-0401 refs backend for locks + pre-commit/CI scripts
- [ ] GM-US-0402 LFS lock backend (mirror)
- [ ] GM-US-0403 proposals/approvals/grants; signed approvals; verifier
