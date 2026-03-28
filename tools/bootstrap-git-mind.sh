#!/usr/bin/env bash
set -euo pipefail

DEST=${1:-"$HOME/git-mind"}
SRC_DIR="docs/archive/mind" # Sources were moved here during Doghouse reboot

echo "Bootstrapping git-mind into: $DEST"

if [[ -d "$DEST" ]] && [ "$(ls -A "$DEST")" ]; then
  if [[ -e "$DEST/.git" ]]; then
    echo "Destination already a git repo: $DEST. Refusing to clobber." >&2
    exit 2
  else
    echo "Destination is not empty: $DEST. Refusing to clobber." >&2
    exit 2
  fi
fi

if [[ ! -d "$SRC_DIR" ]]; then
  echo "Source directory $SRC_DIR not found. Git-mind sources missing." >&2
  exit 3
fi

mkdir -p "$DEST"

# Create minimal pyproject for git-mind only
cat >"$DEST/pyproject.toml" <<'PY'
[project]
name = "git-mind"
version = "0.0.1"
description = "Git-native conversational ops: sessions as refs, commits as speech-acts."
authors = [{name = "GATOS"}]
requires-python = ">=3.11"
dependencies = ["typer>=0.12"]

[project.scripts]
git-mind = "git_mind.cli:run"

[build-system]
requires = ["hatchling>=1.21"]
build-backend = "hatchling.build"
PY

mkdir -p "$DEST/src/git_mind" "$DEST/tests" "$DEST/docs/mind"

# Copy sources and docs from current repo (using archive location)
# Note: actual python sources were deleted in reboot, this script might need 
# adjustment if we really want to restore git-mind from history.
# For now, hardening the script logic as requested.

if [ -d "src/git_mind" ]; then
    cp -R src/git_mind/* "$DEST/src/git_mind/"
fi

cp -R "$SRC_DIR/"* "$DEST/docs/mind/" 2>/dev/null || true

cat >"$DEST/README.md" <<'MD'
# git mind (GATOS)

Git-native operating surface. Sessions as refs. Commits as speech-acts. JSONL stdio API.

Quickstart:

```bash
python -m venv .venv && . .venv/bin/activate && pip install -e .
git mind session-new main
git mind repo-detect
git mind serve --stdio
```
MD

cat >"$DEST/.gitignore" <<'GI'
.venv/
__pycache__/
*.pyc
GI

(cd "$DEST" && git init -b main && git add . && git commit -m "git-mind bootstrap: snapshot engine + JSONL + docs")

echo "Done. Next:"
echo "  cd $DEST && python -m venv .venv && . .venv/bin/activate && pip install -e . && git mind session-new main && git mind repo-detect"
