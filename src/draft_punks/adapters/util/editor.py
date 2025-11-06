from __future__ import annotations
import os, tempfile, subprocess
from typing import Optional

def open_in_editor(initial: str) -> Optional[str]:
    editor = os.environ.get('VISUAL') or os.environ.get('EDITOR') or 'vi'
    with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.md') as f:
        f.write(initial)
        f.flush()
        path = f.name
    try:
        subprocess.run([editor, path])
        with open(path, 'r', encoding='utf-8', errors='ignore') as r:
            return r.read()
    except Exception:
        return None
