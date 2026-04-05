# Configuration

ADQA is configured using Pydantic models for type safety and validation.

::: adqa.config.model.ADQAConfig
    options:
      show_root_heading: true
      members:
        - tracing_enabled
        - lineage_enabled
        - ml_enabled
        - execution_mode
        - profiling
        - detection
        - scoring
        - execution

::: adqa.config.model.ProfilingConfig
    options:
      show_root_heading: true

::: adqa.config.model.DetectionConfig
    options:
      show_root_heading: true
