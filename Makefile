PREFIX ?= $(HOME)/.local
BINDIR ?= $(PREFIX)/bin

.PHONY: install uninstall install-dev install-pipx help dev-venv run tui clean-venv bootstrap-git-mind

	help:
	@echo "Targets:"
	@echo "  make install        # install source wrapper to $(BINDIR)/draft-punks"
	@echo "  make install-dev    # install dev wrapper as ~/bin/draft-punks-dev (uses repo .venv)"
	@echo "  make uninstall      # remove wrapper from $(BINDIR)"
	@echo "  make install-pipx   # install package into isolated pipx venv"
	@echo "  make dev-venv       # create .venv and editable-install for fast iteration"
	@echo "  make tui            # run TUI from .venv (editable)"
	@echo "  make run ARGS=...   # run 'draft-punks $(ARGS)' from .venv"
	@echo "  make bootstrap-git-mind DEST=~/git-mind  # export git-mind skeleton to a new repo"

install:
	@mkdir -p "$(BINDIR)"
	@WRAP="$(BINDIR)/draft-punks"; \
	  echo '#!/usr/bin/env bash'                            >  $$WRAP; \
	  echo 'set -euo pipefail'                              >> $$WRAP; \
	  echo 'REPO="$${DP_DRAFT_PUNKS_REPO:-$(HOME)/git/draft-punks}"' >> $$WRAP; \
	  echo 'SCRIPT="$$REPO/cli/draft-punks"'              >> $$WRAP; \
	  echo 'SRC="$$REPO/src"'                             >> $$WRAP; \
	  echo 'VENV_PY="$$REPO/.venv/bin/python"'            >> $$WRAP; \
	  echo 'PY="$${DP_PYTHON:-python3}"'                  >> $$WRAP; \
	  echo '[[ -x "$$VENV_PY" ]] && PY="$$VENV_PY"'      >> $$WRAP; \
	  echo 'if [[ ! -x "$$SCRIPT" ]]; then'               >> $$WRAP; \
	  echo '  echo "draft-punks: source script not found at $$SCRIPT" >&2' >> $$WRAP; \
	  echo '  echo "Set DP_DRAFT_PUNKS_REPO or use pipx install ." >&2'   >> $$WRAP; \
	  echo '  exit 1'                                       >> $$WRAP; \
	  echo 'fi'                                             >> $$WRAP; \
	  echo 'export PYTHONPATH="$$SRC:$${PYTHONPATH:-}"'    >> $$WRAP; \
	  echo 'exec "$$PY" "$$SCRIPT" "$$@"'               >> $$WRAP; \
	  chmod +x "$$WRAP"; \
	  echo "Installed wrapper: $$WRAP"; \
	  case :$${PATH}: in *:$(BINDIR):*) echo "$(BINDIR) is on PATH";; *) echo "NOTE: add $(BINDIR) to your PATH";; esac

uninstall:
	@rm -f "$(BINDIR)/draft-punks" && echo "Removed $(BINDIR)/draft-punks" || true

install-pipx:
	@command -v pipx >/dev/null 2>&1 || { echo "pipx not found. Install with 'brew install pipx && pipx ensurepath' or see https://pypa.github.io/pipx/." >&2; exit 1; }
	@pipx install . && echo "Installed draft-punks via pipx. Run: draft-punks tui"

# --- developer convenience --------------------------------------------------

dev-venv:
	@python3 -m venv .venv
	@. .venv/bin/activate; python -m pip -q install -U pip
	@. .venv/bin/activate; pip -q install -e .[dev]
	@echo "Dev venv ready: source .venv/bin/activate"

tui:
	@. .venv/bin/activate >/dev/null 2>&1 || { echo "Run 'make dev-venv' first" >&2; exit 1; }
	@. .venv/bin/activate; draft-punks tui || PYTHONPATH=src .venv/bin/python cli/draft-punks tui

run:
	@. .venv/bin/activate >/dev/null 2>&1 || { echo "Run 'make dev-venv' first" >&2; exit 1; }
	@. .venv/bin/activate; draft-punks $(ARGS)

clean-venv:
	rm -rf .venv
	@echo "Removed .venv"

bootstrap-git-mind:
	@bash tools/bootstrap-git-mind.sh "$${DEST:-$$HOME/git-mind}"
install-dev:
	@BINDIR="$(HOME)/bin"; mkdir -p "$$BINDIR"; \
	  WRAP="$$BINDIR/draft-punks-dev"; \
	  echo '#!/usr/bin/env bash'                            >  $$WRAP; \
	  echo 'set -euo pipefail'                              >> $$WRAP; \
	  echo 'REPO="$${DP_DRAFT_PUNKS_REPO:-$(HOME)/git/draft-punks}"' >> $$WRAP; \
	  echo 'SCRIPT="$$REPO/cli/draft-punks"'              >> $$WRAP; \
	  echo 'SRC="$$REPO/src"'                             >> $$WRAP; \
	  echo 'VENV_PY="$$REPO/.venv/bin/python"'            >> $$WRAP; \
	  echo 'PIPX_PY="$(HOME)/.local/pipx/venvs/draft-punks/bin/python"' >> $$WRAP; \
	  echo 'PY="$${DP_PYTHON:-python3}"'                  >> $$WRAP; \
	  echo 'if [[ -x "$$VENV_PY" ]]; then PY="$$VENV_PY"; elif [[ -x "$$PIPX_PY" ]]; then PY="$$PIPX_PY"; fi' >> $$WRAP; \
	  echo 'if [[ ! -x "$$SCRIPT" ]]; then'               >> $$WRAP; \
	  echo '  echo "draft-punks-dev: source script not found at $$SCRIPT" >&2' >> $$WRAP; \
	  echo '  echo "Set DP_DRAFT_PUNKS_REPO or run from a checkout." >&2'      >> $$WRAP; \
	  echo '  exit 1'                                       >> $$WRAP; \
	  echo 'fi'                                             >> $$WRAP; \
	  echo 'export PYTHONPATH="$$SRC:$${PYTHONPATH:-}"'    >> $$WRAP; \
	  echo 'exec "$$PY" "$$SCRIPT" "$$@"'               >> $$WRAP; \
	  chmod +x "$$WRAP"; \
	  echo "Installed dev wrapper: $$WRAP"; \
	  case :$${PATH}: in *:$$BINDIR:*) echo "$$BINDIR is on PATH";; *) echo "NOTE: add $$BINDIR to your PATH";; esac
