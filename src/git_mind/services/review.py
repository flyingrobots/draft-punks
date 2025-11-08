from __future__ import annotations

try:
    # Reuse existing prompt builder and JSON parser
    from draft_punks.core.services.review import build_prompt, _extract_json  # type: ignore
except Exception:  # pragma: no cover
    import json, re
    _JSON_FENCE = re.compile(r"```json\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
    _OBJ_ANY = re.compile(r"(\{[\s\S]*\})")

    def build_prompt(pr_number: int, head_ref: str, body: str) -> str:
        return (
            f"We are processing code review feedback for PR #{pr_number} ({head_ref}).\n"
            "Respond only with JSON: {\"success\": true|false, \"git_commits\": [\"<sha1>\", ...], \"error\": \"...\"}.\n"
            f"Feedback:\n{body}\n"
        )

    def _extract_json(blob: str):
        m = _JSON_FENCE.search(blob)
        raw = m.group(1) if m else None
        if not raw:
            m2 = _OBJ_ANY.search(blob)
            raw = m2.group(1) if m2 else None
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

