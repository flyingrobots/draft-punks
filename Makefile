.PHONY: dev-venv test snapshot history playback clean

VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

dev-venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]

test:
	PYTHONPATH=src $(PYTHON) -m pytest tests/doghouse

snapshot:
	PYTHONPATH=src $(PYTHON) -m doghouse.cli.main snapshot

history:
	PYTHONPATH=src $(PYTHON) -m doghouse.cli.main history

playback:
	@if [ -z "$(NAME)" ]; then echo "Usage: make playback NAME=pb1_push_delta"; exit 1; fi
	PYTHONPATH=src $(PYTHON) -m doghouse.cli.main playback $(NAME)

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
