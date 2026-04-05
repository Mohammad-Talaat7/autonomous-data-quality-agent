# ADQA: Autonomous Data Quality Agent

[![PyPI version](https://img.shields.io/pypi/v/adqa.svg)](https://pypi.org/project/adqa/)
[![Python versions](https://img.shields.io/pypi/pyversions/adqa.svg)](https://pypi.org/project/adqa/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ADQA** is an intelligent, autonomous agent designed for high-performance data quality inspection, risk detection, and automated remediation. Built for the era of **Data-centric AI**, ADQA helps you ensure your models are trained on clean, reliable, and safe data.

## 🚀 Vision

Automating data quality and risk inspection to make the work of data scientists and engineers easier, safer, and more productive. ADQA combines a powerful Python library for automated pipelines with a high-performance Rust-based TUI for interactive observability.

## 📚 Documentation

For full documentation, architecture details, and API reference, visit:
**[google.github.io/autonomous-data-quality-agent](https://google.github.io/autonomous-data-quality-agent/)**

## ✨ Key Features

- **Multi-Source Ingress:** Support for CSV, Parquet, Excel, SQL databases, S3, Airbyte, and more.
- **Intelligent Profiling:** Structural, relational, and ML-based profiling with deterministic caching.
- **Risk Inspection:** 
    - **PII Detection:** Automated identification of emails, phone numbers, credit cards, SSNs, etc.
    - **Bias Detection:** Spotting extreme class imbalances in sensitive demographic columns.
    - **Quality Checks:** Missing values, outliers, skewness, pattern violations, and more.
- **Autonomous Remediation:** 
    - **Advisory Mode:** Observe what would happen without modifying data.
    - **Automatic Mode:** Heal data autonomously (impute, drop, clip, mask).
    - **Human-in-the-Loop:** Interactive approval of proposed fixes via CLI or TUI.
- **Full Traceability:** Detailed execution traces and data lineage for every decision made by the agent.

## 📦 Installation

```bash
pip install adqa
```

## 🛠 Usage

### Command Line Interface (CLI)

ADQA comes with a powerful CLI for quick inspections:

```bash
# Basic advisory analysis
adqa analyze data.csv

# Run in automatic remediation mode and save results
adqa analyze data.csv --mode automatic --output cleaned_data.csv

# Human-in-the-loop mode
adqa analyze data.csv --mode human_in_loop
```

### Python API

Integrate ADQA into your existing data pipelines:

```python
from adqa import ADQA, DataSource, ADQAConfig

# Load data
source = DataSource.csv("path/to/data.csv")

# Configure agent
config = ADQAConfig(execution_mode="automatic")

# Run analysis
agent = ADQA(data_source=source, config=config)
result = agent.analyze()

# Get the healed dataframe
df_cleaned = result.dataframe

# See the summary
print(result.summary())
```

## 🖥 Rust TUI

For an interactive, real-time view of the ADQA agent's reasoning and trace events, use the ADQA TUI:

```bash
cd adqa-tui
cargo run
```

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
