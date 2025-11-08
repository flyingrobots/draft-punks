#!/usr/bin/env bash
set -euo pipefail

DEST=${1:-"$HOME/git-mind"}

echo "Bootstrapping git-mind into: $DEST"
if [[ -e "$DEST/.git" ]]; then
  echo "Destination already a git repo: $DEST" >&2
  exit 2
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

# Copy sources and docs from current repo
cp -R src/git_mind/* "$DEST/src/git_mind/"
cp -R docs/mind/* "$DEST/docs/mind/" 2>/dev/null || true
cp tests/test_git_mind_snapshot.py "$DEST/tests/" 2>/dev/null || true

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

