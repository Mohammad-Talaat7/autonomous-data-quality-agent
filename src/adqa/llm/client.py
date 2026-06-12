# adqa/llm/client.py
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from hashlib import sha256
from typing import Any, TypeVar

from pydantic import BaseModel

from .models import LLMRequest, LLMResponse

ResponseT = TypeVar("ResponseT", bound=BaseModel)


class BaseLLMClient(ABC):
    def __init__(self, tracer: Any = None) -> None:
        self._tracer = tracer

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError

    def complete_structured(
        self,
        request: LLMRequest,
        response_model: type[ResponseT],
    ) -> ResponseT:
        started = time.monotonic()
        try:
            response = self.complete(request)
            elapsed = time.monotonic() - started
            self._trace_llm_call(request, response, elapsed_seconds=elapsed)
        except Exception as exc:
            elapsed = time.monotonic() - started
            self._trace_llm_error(request, exc, elapsed_seconds=elapsed)
            raise

        payload = json.loads(response.content)
        # Coerce scalar-to-list for known response fields the LLM may flatten
        for field in ("why_decision", "recommended_next_steps", "top_issues",
                       "affected_columns", "proposals"):
            if field in payload and isinstance(payload[field], str):
                payload[field] = [payload[field]]
        data = {
            **payload,
            "provider": response.provider,
            "model": response.model,
            "prompt_version": response.prompt_version,
            "trace_id": response.trace_id,
            "input_hash": response.input_hash,
            "output_hash": response.output_hash,
            "confidence": response.confidence,
            "warnings": response.warnings,
        }
        return response_model.model_validate(data)

    def _trace_llm_call(
        self,
        request: LLMRequest,
        response: LLMResponse,
        *,
        elapsed_seconds: float,
    ) -> None:
        if getattr(self, "_tracer", None) is None:
            return
        self._tracer.trace(
            "LLM_CALL",
            {
                "request_type": request.metadata.get("task", "unknown"),
                "provider": request.provider,
                "model": request.model,
                "prompt_version": request.prompt_version,
                "input_hash": request.input_hash(),
                "output_hash": response.output_hash,
                "duration_seconds": round(elapsed_seconds, 3),
                "status": "success",
            },
        )

    def _trace_llm_error(
        self,
        request: LLMRequest,
        error: Exception,
        *,
        elapsed_seconds: float,
    ) -> None:
        if getattr(self, "_tracer", None) is None:
            return
        self._tracer.trace(
            "LLM_CALL_ERROR",
            {
                "request_type": request.metadata.get("task", "unknown"),
                "provider": request.provider,
                "model": request.model,
                "prompt_version": request.prompt_version,
                "duration_seconds": round(elapsed_seconds, 3),
                "status": "error",
                "error": str(error),
            },
        )


class LiteLLMClient(BaseLLMClient):
    def complete(self, request: LLMRequest) -> LLMResponse:
        try:
            # import litellm
            from litellm import completion
        except ImportError as exc:
            raise RuntimeError(
                "LiteLLM is not installed. Install the `llm` extra to enable it."
            ) from exc

        # litellm.set_verbose=True

        # Classification/remediation tasks use json_object; chat & explain use plain text.
        # Free-form chat uses plain text.
        use_json = request.metadata.get("task") not in ("chat", "explain")

        kwargs: dict[str, Any] = dict(
            model=request.model,
            messages=[message.model_dump(mode="json") for message in request.messages],
            temperature=request.temperature,
            timeout=request.timeout_seconds,
        )
        # Pass provider to litellm for routing (e.g. openrouter, openai, etc.)
        if request.provider and request.provider != "litellm":
            kwargs["custom_llm_provider"] = request.provider
        if request.api_key:
            kwargs["api_key"] = request.api_key
        if request.api_base:
            kwargs["api_base"] = request.api_base
        if request.service_tier:
            kwargs["service_tier"] = request.service_tier
        if use_json:
            kwargs["response_format"] = {"type": "json_object"}

        raw_response = completion(**kwargs)
        content = raw_response.choices[0].message.content or "{}"
        return LLMResponse(
            provider=request.provider,
            model=request.model,
            prompt_version=request.prompt_version,
            trace_id=request.trace_id,
            input_hash=request.input_hash(),
            output_hash=sha256(content.encode("utf-8")).hexdigest(),
            content=content,
        )
