# tests/config/test_model.py

import pytest
from pydantic import ValidationError

from adqa.config import ADQAConfig, ExecutionMode, TraceStoreType
from adqa.data_ingress.datasource import DataSource


class TestADQAConfig:
    def test_valid_full_config(self):
        """Test a valid configuration with all features enabled."""
        config = ADQAConfig(
            tracing_enabled=True,
            lineage_enabled=True,
            ml_enabled=True,
            trace_store="in_memory",
            execution_mode="automatic",
            data_source=DataSource.csv(path="dummy.csv"),
        )
        assert config.tracing_enabled is True
        assert config.lineage_enabled is True
        assert config.ml_enabled is True
        assert config.trace_store == TraceStoreType.IN_MEMORY
        assert config.execution_mode == ExecutionMode.AUTOMATIC

    def test_valid_minimal_config(self):
        """Test a valid minimal configuration with defaults."""
        config = ADQAConfig(
            data_source=DataSource.csv(path="dummy.csv"),
        )
        assert config.tracing_enabled is False
        assert config.lineage_enabled is False
        assert config.ml_enabled is False
        assert config.trace_store is None
        assert config.execution_mode == ExecutionMode.ADVISORY

    def test_tracing_defaults_to_in_memory(self):
        """Test that enabling tracing without a store defaults to in_memory."""
        config = ADQAConfig(
            tracing_enabled=True,
            data_source=DataSource.csv(path="dummy.csv"),
        )
        assert config.trace_store == TraceStoreType.IN_MEMORY

    def test_tracing_disabled_clears_store(self):
        """Test that disabling tracing clears the trace_store even if provided."""
        config = ADQAConfig(
            tracing_enabled=False,
            trace_store="jsonl",
            data_source=DataSource.csv(path="dummy.csv"),
        )
        assert config.trace_store is None

    def test_lineage_requires_tracing(self):
        """Test that enabling lineage without tracing raises an error."""
        with pytest.raises(ValidationError) as exc_info:
            ADQAConfig(
                tracing_enabled=False,
                lineage_enabled=True,
                ml_enabled=False,
                trace_store=None,
                execution_mode=ExecutionMode.ADVISORY,
                data_source=DataSource.csv(path="dummy.csv"),
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
                data_source=DataSource.csv(path="dummy.csv"),
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
                data_source=DataSource.csv(path="dummy.csv"),
            )
        assert "Human-in-loop execution requires tracing" in str(exc_info.value)

    def test_immutability(self):
        """Test that ADQAConfig is frozen/immutable."""
        config = ADQAConfig(
            tracing_enabled=True,
            lineage_enabled=False,
            ml_enabled=False,
            trace_store=TraceStoreType.IN_MEMORY,
            execution_mode=ExecutionMode.ADVISORY,
            data_source=DataSource.csv(path="dummy.csv"),
        )
        with pytest.raises(ValidationError):
            config.tracing_enabled = False
