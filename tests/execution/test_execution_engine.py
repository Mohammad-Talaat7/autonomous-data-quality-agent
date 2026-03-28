from dataclasses import dataclass

import pytest

from adqa.execution.engine import ExecutionEngine
from adqa.execution.models import ExecutionMode
from adqa.scoring.models import QualityDecision


@dataclass
class MockConfig:
    execution_mode: str
    dominant_issues: list[str] = None


class MockTracer:
    def __init__(self):
        self.traces = []

    def trace(self, event, payload):
        self.traces.append((event, payload))


@pytest.fixture
def engine():
    return ExecutionEngine(tracer=MockTracer())


@pytest.fixture
def pass_decision():
    return QualityDecision(
        decision="PASS",
        score=0.95,
        severity_level="LOW",
        breakdown={},
        dimension_breakdown={},
        dominant_issues=[],
        affected_columns=[],
        thresholds_used={},
        explanation="OK",
    )


@pytest.fixture
def fail_decision():
    return QualityDecision(
        decision="FAIL",
        score=0.3,
        severity_level="HIGH",
        breakdown={},
        dimension_breakdown={},
        dominant_issues=["missing_values"],
        affected_columns=["col1"],
        thresholds_used={},
        explanation="FAIL",
    )


def test_advisory_mode_never_blocks(engine, fail_decision):
    config = MockConfig(execution_mode=ExecutionMode.ADVISORY)
    result = engine.run(fail_decision, config)

    assert not result.blocked
    assert not result.approval_requested
    # The FAIL should have been converted to WARN or started as WARN
    assert result.executed_actions[0].action_type == "WARN"
    assert "Advisory" in result.executed_actions[0].reason


def test_human_in_loop_requests_approval(engine, fail_decision):
    config = MockConfig(execution_mode=ExecutionMode.HUMAN_IN_LOOP)
    result = engine.run(fail_decision, config)

    assert result.approval_requested
    assert len(result.executed_actions) == 0
    assert result.plan.requires_human


def test_automatic_mode_blocks(engine, fail_decision):
    config = MockConfig(execution_mode=ExecutionMode.AUTOMATIC)
    result = engine.run(fail_decision, config)

    assert result.blocked
    assert not result.approval_requested
    assert result.executed_actions[0].action_type == "BLOCK"


def test_executor_handlers(engine, fail_decision):
    config = MockConfig(execution_mode=ExecutionMode.AUTOMATIC)

    handled_actions = []

    def my_handler(action, tracer):
        handled_actions.append(action)

    engine.executor.register_handler("BLOCK", my_handler)

    _ = engine.run(fail_decision, config)

    assert len(handled_actions) == 1
    assert handled_actions[0].action_type == "BLOCK"
