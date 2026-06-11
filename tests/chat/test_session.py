"""Tests for ChatSession."""

import json
from hashlib import sha256

from adqa.chat.session import ChatSession
from adqa.llm.client import BaseLLMClient
from adqa.llm.models import LLMRequest, LLMResponse


class EchoLLMClient(BaseLLMClient):
    def complete(self, request: LLMRequest) -> LLMResponse:
        last_msg = request.messages[-1].content if request.messages else ""
        return LLMResponse(
            provider=request.provider,
            model=request.model,
            prompt_version=request.prompt_version,
            trace_id=request.trace_id,
            input_hash=request.input_hash(),
            output_hash=sha256(f"Echo: {last_msg}".encode("utf-8")).hexdigest(),
            content=f"Echo: {last_msg}",
        )


class MockResult:
    decision = None
    error = None
    warnings = []
    explanation = None

    def summary(self):
        return "mock summary"


def test_no_result_returns_guidance():
    session = ChatSession(client=EchoLLMClient())
    response = session.send("hello")
    assert "No analysis result available" in response


def test_send_receives_response():
    result = MockResult()
    session = ChatSession(client=EchoLLMClient(), result=result)
    response = session.send("hello")
    assert response.startswith("Echo:")


def test_history_grows():
    result = MockResult()
    session = ChatSession(client=EchoLLMClient(), result=result)
    assert len(session._history) == 0
    session.send("q1")
    assert len(session._history) == 2
    session.send("q2")
    assert len(session._history) == 4


def test_inject_result_updates():
    session = ChatSession(client=EchoLLMClient())
    r1 = MockResult()
    session.inject_result(r1)
    response = session.send("hello")
    assert response.startswith("Echo:")
