.PHONY: dev-venv test snapshot history playback watch export clean help

VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

help:
	@echo "Doghouse Makefile"
	@echo "  dev-venv: Create venv and install dependencies"
	@echo "  test: Run unit tests"
	@echo "  snapshot [PR=id]: Capture PR state"
	@echo "  history [PR=id]: View PR snapshot history"
	@echo "  playback NAME=name: Run a playback fixture"
	@echo "  watch [PR=id]: Monitor PR live"
	@echo "  export [PR=id]: Create repro bundle"

dev-venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]

test:
	PYTHONPATH=src $(PYTHON) -m pytest tests/doghouse

snapshot:
	@if [ -z "$(PR)" ]; then PYTHONPATH=src $(PYTHON) -m doghouse.cli.main snapshot; \
	else PYTHONPATH=src $(PYTHON) -m doghouse.cli.main snapshot --pr $(PR); fi

history:
	@if [ -z "$(PR)" ]; then PYTHONPATH=src $(PYTHON) -m doghouse.cli.main history; \
	else PYTHONPATH=src $(PYTHON) -m doghouse.cli.main history --pr $(PR); fi

playback:
	@if [ -z "$(NAME)" ]; then echo "Usage: make playback NAME=pb1_push_delta"; exit 1; fi
	PYTHONPATH=src $(PYTHON) -m doghouse.cli.main playback $(NAME)

watch:
	@if [ -z "$(PR)" ]; then PYTHONPATH=src $(PYTHON) -m doghouse.cli.main watch; \
	else PYTHONPATH=src $(PYTHON) -m doghouse.cli.main watch --pr $(PR); fi

export:
	@if [ -z "$(PR)" ]; then PYTHONPATH=src $(PYTHON) -m doghouse.cli.main export; \
	else PYTHONPATH=src $(PYTHON) -m doghouse.cli.main export --pr $(PR); fi

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
