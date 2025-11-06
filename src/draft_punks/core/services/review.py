from __future__ import annotations
import json
import re
from typing import List
from draft_punks.ports.logging import LoggingPort
from draft_punks.ports.llm import LlmPort
from draft_punks.ports.git import GitPort

_JSON_FENCE = re.compile(r"```json\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
_OBJ_ANY    = re.compile(r"(\{[\s\S]*\})")

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


def process_comment(*, pr_number: int, head_ref: str, body: str, llm: LlmPort, git: GitPort, log: LoggingPort) -> List[str]:
    """Send a single reviewer comment to the LLM; parse JSON; validate SHAs.
    Returns a list of accepted commit SHAs.
    Non-JSON is logged and ignored (warn), never raises.
    """
    # Craft minimal prompt now; richer later
    prompt = (
        f"We are processing code review feedback for PR #{pr_number} ({head_ref}).\n"
        "Respond only with JSON: {\"success\": true|false, \"git_commits\": [\"<sha1>\", ...], \"error\": \"...\"}.\n"
        f"Feedback:\n{body}\n"
    )
    try:
        out = llm.run(prompt)
    except Exception as e:
        log.error(f"LLM invocation failed: {e}")
        return []
    js = _extract_json(out or "")
    if not js:
        log.warn("LLM returned non-JSON; ignoring output")
        if out:
            head = out[:4000]
            log.markdown(f"```text\n{head}\n```")
        return []
    commits = []
    if bool(js.get("success")):
        for s in js.get("git_commits", []) or []:
            if isinstance(s, str) and git.is_commit(s):
                commits.append(s)
    else:
        err = js.get("error") or "unknown error"
        log.error(f"LLM reported failure: {err}")
    return commits
