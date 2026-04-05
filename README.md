# ADQA: Autonomous Data Quality Agent

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/adqa.svg)](https://pypi.org/project/adqa/)
[![Crates.io](https://img.shields.io/crates/v/adqa-tui.svg)](https://crates.io/crates/adqa-tui)
[![Python versions](https://img.shields.io/pypi/pyversions/adqa.svg)](https://pypi.org/project/adqa/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-live-brightgreen.svg)](https://google.github.io/autonomous-data-quality-agent/)

**The intelligent, autonomous agent for high-performance data quality inspection, risk detection, and automated remediation.**

[Getting Started](#-getting-started) • [Key Features](#-key-features) • [Documentation](https://google.github.io/autonomous-data-quality-agent/) • [Rust TUI](#-rust-tui)

</div>

---

**ADQA** is built for the era of **Data-centric AI**. It helps Data Scientists and Engineers ensure their models are trained on clean, reliable, and safe data by automating the boring parts of data quality: profiling, detecting anomalies, explaining risks, and proposing (or applying) fixes.

## 🚀 Vision

Data quality is the #1 bottleneck in AI development. ADQA combines a powerful **Python library** for automated pipelines with a high-performance **Rust-based TUI** for interactive observability, providing a seamless bridge between automated remediation and human oversight.

## 📚 Documentation

For full documentation, architecture details, and API reference, visit:
**[google.github.io/autonomous-data-quality-agent](https://google.github.io/autonomous-data-quality-agent/)**

## ✨ Key Features

- **🔍 Multi-Source Ingress:** Seamlessly connect to CSV, Parquet, Excel, SQL databases, S3, and 300+ SaaS sources via **Airbyte**.
- **🧠 Intelligent Profiling:** 
    - **Structural:** Null ratios, cardinality, and type inference.
    - **Behavioral:** Outlier detection, skewness, and pattern identification.
    - **Semantic:** ML-driven classification of PII and domain-specific data types.
- **🚨 Hybrid Risk Detection:** 
    - **Rule-based:** Deterministic checks for missing values, range violations, and duplicates.
    - **ML-based:** Structural anomalies via **Isolation Forest**, PII leakage, and statistical bias.
- **🛠️ Autonomous Remediation:** 
    - **Advisory Mode:** Observe what would happen without modifying data.
    - **Automatic Mode:** Heal data autonomously (impute, drop, clip, mask).
    - **Human-in-the-Loop:** Interactive approval of proposed fixes via CLI or TUI.
- **📜 Full Traceability:** Detailed execution traces and data lineage for every decision made by the agent.

## 📦 Installation

### Python Library & CLI
```bash
pip install adqa
```
For full ML capabilities:
```bash
pip install "adqa[all]"
```

### Rust TUI
You can download the pre-compiled binaries from the [Releases](https://github.com/google/autonomous-data-quality-agent/releases) page, or install via cargo:
```bash
cargo install adqa-tui
```

## 🛠 Usage

### Command Line Interface (CLI)
```bash
# Basic advisory analysis
adqa analyze data.csv

# Run in automatic remediation mode and save results
adqa analyze data.csv --mode automatic --output cleaned_data.csv
```

### Python API
```python
from adqa import ADQA, DataSource

# Initialize and run
agent = ADQA.from_path("path/to/data.csv")
result = agent.analyze()

# View summary and get healed data
print(result.summary())
df_cleaned = result.dataframe
```

## 🖥 Rust TUI

Experience real-time data quality monitoring. The ADQA TUI provides an interactive dashboard to explore profiles, monitor detection events, and approve remediations.

```bash
adqa-tui
```

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
