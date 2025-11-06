from pathlib import Path
from draft_punks.core.services.suggest import parse_suggestion_pairs, apply_suggestions

BODY = """
path/to/file.c
```code
if (bad) {
  do_bad();
}
```

Suggested replacement
```code
if (good) {
  do_good();
}
```
"""

def test_parse_suggestion_pairs_extracts_before_after():
    pairs = parse_suggestion_pairs(BODY)
    assert len(pairs) == 1
    before, after = pairs[0]
    assert 'do_bad();' in before
    assert 'do_good();' in after


def test_apply_suggestions_replaces_once(tmp_path: Path):
    p = tmp_path / 'file.c'
    p.write_text('''\nvoid f(){\nif (bad) {\n  do_bad();\n}\n}\n''')
    pairs = parse_suggestion_pairs(BODY)
    n = apply_suggestions(str(p), pairs)
    assert n == 1
    t = p.read_text()
    assert 'do_good();' in t and 'do_bad();' not in t
