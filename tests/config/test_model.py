# tests/config/test_model.py

import pytest
from pydantic import ValidationError

from adqa.config import ADQAConfig, ExecutionMode, TraceStoreType


class TestADQAConfig:
    def test_valid_full_config(self):
        """Test a valid configuration with all features enabled."""
        config = ADQAConfig(
            tracing_enabled=True,
            lineage_enabled=True,
            ml_enabled=True,
            trace_store=TraceStoreType.IN_MEMORY,
            execution_mode=ExecutionMode.AUTOMATIC,
        )
        assert config.tracing_enabled is True
        assert config.lineage_enabled is True
        assert config.ml_enabled is True
        assert config.trace_store == TraceStoreType.IN_MEMORY
        assert config.execution_mode == ExecutionMode.AUTOMATIC

    def test_valid_minimal_config(self):
        """Test a valid minimal configuration (advisory, no tracing)."""
        config = ADQAConfig(
            tracing_enabled=False,
            lineage_enabled=False,
            ml_enabled=False,
            trace_store=None,
            execution_mode=ExecutionMode.ADVISORY,
        )
        assert config.tracing_enabled is False
        assert config.lineage_enabled is False
        assert config.execution_mode == ExecutionMode.ADVISORY

    def test_lineage_requires_tracing(self):
        """Test that enabling lineage without tracing raises an error."""
        with pytest.raises(ValidationError) as exc_info:
            ADQAConfig(
                tracing_enabled=False,
                lineage_enabled=True,
                ml_enabled=False,
                trace_store=None,
                execution_mode=ExecutionMode.ADVISORY,
            )
        assert "Lineage cannot be enabled without tracing" in str(exc_info.value)

    def test_automatic_requires_tracing(self):
        """Test that automatic execution mode requires tracing."""
        with pytest.raises(ValidationError) as exc_info:
            ADQAConfig(
                tracing_enabled=False,
                lineage_enabled=False,
                ml_enabled=False,
                trace_store=None,
                execution_mode=ExecutionMode.AUTOMATIC,
            )
        assert "Automatic execution requires tracing" in str(exc_info.value)

    def test_human_requires_tracing(self):
        """Test that human-in-loop execution mode requires tracing."""
        with pytest.raises(ValidationError) as exc_info:
            ADQAConfig(
                tracing_enabled=False,
                lineage_enabled=False,
                ml_enabled=False,
                trace_store=None,
                execution_mode=ExecutionMode.HUMAN_IN_LOOP,
            )
        assert "Human-in-loop execution requires tracing" in str(exc_info.value)

    def test_trace_store_required_if_tracing_enabled(self):
        """Test that enabling tracing requires a trace store."""
        with pytest.raises(ValidationError) as exc_info:
            ADQAConfig(
                tracing_enabled=True,
                lineage_enabled=False,
                ml_enabled=False,
                trace_store=None,
                execution_mode=ExecutionMode.ADVISORY,
            )
        assert "trace_store must be set when tracing is enabled" in str(exc_info.value)

    def test_trace_store_forbidden_if_tracing_disabled(self):
        """Test that trace store must be None if tracing is disabled."""
        with pytest.raises(ValidationError) as exc_info:
            ADQAConfig(
                tracing_enabled=False,
                lineage_enabled=False,
                ml_enabled=False,
                trace_store=TraceStoreType.IN_MEMORY,
                execution_mode=ExecutionMode.ADVISORY,
            )
        assert "trace_store must be None when tracing is disabled" in str(
            exc_info.value
        )

    def test_immutability(self):
        """Test that ADQAConfig is frozen/immutable."""
        config = ADQAConfig(
            tracing_enabled=True,
            lineage_enabled=False,
            ml_enabled=False,
            trace_store=TraceStoreType.IN_MEMORY,
            execution_mode=ExecutionMode.ADVISORY,
        )
        with pytest.raises(ValidationError):
            config.tracing_enabled = False
