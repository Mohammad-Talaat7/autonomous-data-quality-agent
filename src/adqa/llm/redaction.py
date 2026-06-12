# adqa/llm/redaction.py
from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[\s.\-]?)?(?:\(?\d{3}\)?[\s.\-]?)\d{3}[\s.\-]?\d{4}(?!\w)"
)
CC_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

ROW_SAMPLE_KEYS = {"rows", "samples", "row_samples", "examples"}


def redact_text(value: str) -> str:
    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    redacted = PHONE_RE.sub("[REDACTED_PHONE]", redacted)
    redacted = CC_RE.sub("[REDACTED_CARD]", redacted)
    redacted = SSN_RE.sub("[REDACTED_SSN]", redacted)
    return redacted


def _redact_value(value: Any, *, max_rows: int) -> Any:
    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, list):
        redacted = [_redact_value(item, max_rows=max_rows) for item in value]
        return redacted[:max_rows]

    if isinstance(value, dict):
        redacted = {
            key: _redact_value(item, max_rows=max_rows) for key, item in value.items()
        }
        for key in ROW_SAMPLE_KEYS:
            if key in redacted and isinstance(redacted[key], list):
                redacted[key] = redacted[key][:max_rows]
        return redacted

    return value


def sanitize_payload(
    payload: dict[str, Any],
    *,
    redact_samples: bool = True,
    max_rows: int = 5,
    max_chars: int = 12000,
) -> dict[str, Any]:
    sanitized = deepcopy(payload)
    if redact_samples:
        sanitized = _redact_value(sanitized, max_rows=max_rows)

    encoded = json.dumps(sanitized, sort_keys=True, ensure_ascii=False)
    if len(encoded) <= max_chars:
        return sanitized

    trimmed = deepcopy(sanitized)
    for key in ROW_SAMPLE_KEYS:
        if key in trimmed and isinstance(trimmed[key], list):
            trimmed[key] = trimmed[key][:1]

    encoded = json.dumps(trimmed, sort_keys=True, ensure_ascii=False)
    if len(encoded) <= max_chars:
        return trimmed

    trimmed["truncated"] = True
    trimmed["payload_preview"] = encoded[: max_chars - 32]
    return trimmed
