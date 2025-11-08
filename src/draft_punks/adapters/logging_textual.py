from __future__ import annotations
from typing import Callable, Any
from draft_punks.ports.logging import LoggingPort

class TextualLogger(LoggingPort):
    """Minimal adapter that can write to either a Textual Log widget or App.log.

    Accepts either an object with a ``write(str)`` method (e.g. ``textual.widgets.Log``)
    or a callable like ``App.log``.
    """
    def __init__(self, sink: Any):
        if hasattr(sink, "write"):
            self._write: Callable[[str], None] = getattr(sink, "write")
        elif callable(sink):
            self._write = sink  # App.log(str)
        else:
            self._write = lambda s: None

    def info(self, msg: str) -> None:
        try:
            self._write(f"INFO: {msg}")
        except Exception:
            pass

    def warn(self, msg: str) -> None:
        try:
            self._write(f"WARN: {msg}")
        except Exception:
            pass

    def error(self, msg: str) -> None:
        try:
            self._write(f"ERROR: {msg}")
        except Exception:
            pass

    def markdown(self, md: str) -> None:
        # Fallback to plain text; avoids needing Rich Markdown in the TUI.
        try:
            self._write(md)
        except Exception:
            pass
