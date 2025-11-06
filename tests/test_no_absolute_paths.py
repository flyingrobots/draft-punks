import re
from pathlib import Path

PATTERNS = [
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
    re.compile(r"[A-Za-z]:\\\\"),  # Windows drive prefix
]

IGNORES = {'.git', 'assets', '.venv', 'build', 'dist', '.pytest_cache', '__pycache__'}


def scan_paths(root: Path):
    for p in root.rglob('*'):
        if any(part in IGNORES for part in p.parts):
            continue
        if p.is_file() and p.suffix in {'.py', '', '.md', '.toml', '.sh'}:
            yield p


def test_no_absolute_paths_in_repo_root():
    root = Path(__file__).resolve().parents[1]
    offenders = []
    for p in scan_paths(root):
        try:
            text = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for pat in PATTERNS:
            if pat.search(text):
                offenders.append((p, pat.pattern))
                break
    assert not offenders, "Absolute path patterns found: " + ", ".join(f"{p}:{pat}" for p, pat in offenders)
