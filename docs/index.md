# ADQA - Autonomous Data Quality Agent

ADQA is a modern, autonomous data quality agent designed to profile datasets, detect multi-dimensional quality risks, and execute automated remediations.

## Core Pillars

- **🔍 Multi-Dimensional Profiling**: Deep analysis of structural, behavioral, and semantic characteristics.
- **🚨 Intelligent Detection**: Hybrid engine combining rule-based heuristics with ML-driven risk identification.
- **⚖️ Quality Scoring**: Aggregated scoring across dimensions like Validity, Completeness, Consistency, and Privacy.
- **🛠️ Autonomous Healing**: Automated remediation engine with Advisory, Human-in-the-loop, and Automatic modes.
- **📜 Full Traceability**: Complete audit logs and data lineage for every decision and transformation.

## Installation

ADQA is built with Python and leverages `poetry` for dependency management.

```bash
pip install .
```

For full ML capabilities:

```bash
pip install ".[ml]"
```

## Quick Start

### Using the Python API

```python
from adqa import ADQA, ADQAConfig, DataSource

# 1. Initialize with a data source
agent = ADQA.from_path("sample_data.csv")

# 2. Run analysis
result = agent.analyze()

# 3. View quality decision
print(result.summary())

# 4. If in automatic mode, remediated data is available
if result.dataframe is not None:
    result.dataframe.to_csv("healed_data.csv")
```

### Using the CLI

```bash
adqa analyze sample_data.csv --mode advisory
```

## Documentation Structure

- [Guide](ingress.md): Conceptual overview of how ADQA works.
- [API Reference](api/core.md): Technical documentation of classes and methods.
- [Trace & Lineage](trace.md): Understanding how decisions are tracked.
