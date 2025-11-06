# 🎼 Draft Punks — The TUI

> “Every comment is a note. Every note must be played.”  
> — P.R. PhiedBach (Kapellmeister of Commits), with BunBun at the console

Welcome, friend. You stand before a wall of review threads so vast that the browser wheezes. Breathe. Draft Punks turns that cacophony into a rehearsal you can actually conduct.

- Pull in your PR’s CodeRabbit threads.
- March through them one by one.
- Say “Yes”, “Rewrite”, “Apply the Suggestion”, or “Skip”.
- Summon the LLM when you want. Silence it when you don’t.
- Push only after you’re satisfied.

## Quickstart

- Run the TUI:

```bash
./cli/draft-punks tui
```

- Title screen secret (macOS only): type `B A C H` to let BunBun read coderabbitai comments aloud (Anna’s voice).  
  Toggle lives in `~/.draft-punks/{repo}/config.json`.

- Pick a PR, press Enter.
- Select a comment, press Enter for options:
  - Yes — send to the LLM now
  - Yes, but let me rewrite it — opens `$VISUAL`/`$EDITOR`
  - Apply suggested replacement (no LLM) — uses the fenced “Suggested replacement” block
  - Yes, and auto-send comments in this file
  - Yes, and auto-send comments everywhere
  - No, skip this comment
  - No, skip this file
  - I need to switch LLMs — pick Codex / Claude / Gemini / Other (template)
  - Quit

Press `s` for a Summary (and push). Press `h` for Help. Press `a` to batch‑send remaining.

## Config (outside your repo)

`~/.draft-punks/{repo}/config.json`

```json
{
  "llm": "claude",
  "llm_cmd": null,
  "force_json": true,
  "reply_on_success": false,
  "ui": { "theme": "auto" },
  "voice": { "osx_bonus": false, "voice": "Anna", "read_scope": "coderabbit_only" }
}
```

## Principles

- Append‑only: no rebase, no amend, no force.
- Tests first when changing behavior; tiny commits that tell the truth.
- LLM output must be JSON. Non‑JSON is politely ignored.
- Suggestions should be applied literally if possible (and committed).

Now—take your place at the console. BunBun is ready. PhiedBach raises his quill.  
Conduct.
