# adqa/llm/prompts.py
from __future__ import annotations

import json
from typing import Any

from .models import LLMMessage


def build_json_messages(
    *,
    system_instruction: str,
    payload: dict[str, Any],
) -> list[LLMMessage]:
    return [
        LLMMessage(role="system", content=system_instruction),
        LLMMessage(
            role="user",
            content=json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2),
        ),
    ]
