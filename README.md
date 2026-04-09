# ADQA: Autonomous Data Quality Agent

<div align="center">

[![Release - Linux](https://github.com/Mohammad-Talaat7/autonomous-data-quality-agent/actions/workflows/Release-Linux.yml/badge.svg)](https://github.com/Mohammad-Talaat7/autonomous-data-quality-agent/actions/workflows/Release-Linux.yml)
[![Release - Windows](https://github.com/Mohammad-Talaat7/autonomous-data-quality-agent/actions/workflows/Release-Windows.yml/badge.svg)](https://github.com/Mohammad-Talaat7/autonomous-data-quality-agent/actions/workflows/Release-Windows.yml)
[![Release - macOS](https://github.com/Mohammad-Talaat7/autonomous-data-quality-agent/actions/workflows/Release-MacOS.yml/badge.svg)](https://github.com/Mohammad-Talaat7/autonomous-data-quality-agent/actions/workflows/Release-MacOS.yml)
[![Tests](https://github.com/Mohammad-Talaat7/autonomous-data-quality-agent/actions/workflows/CI-Pipeline.yml/badge.svg)](https://github.com/Mohammad-Talaat7/autonomous-data-quality-agent/actions/workflows/CI-Pipeline.yml)
[![Docs](https://github.com/Mohammad-Talaat7/autonomous-data-quality-agent/actions/workflows/CD-Docs.yml/badge.svg)](https://Mohammad-Talaat7.github.io/autonomous-data-quality-agent/)
[![PyPI version](https://img.shields.io/pypi/v/adqa?include_prereleases&color=blue)](https://pypi.org/project/adqa/)
[![Crates.io](https://img.shields.io/crates/v/adqa-tui?color=orange)](https://crates.io/crates/adqa-tui)
[![Python versions](https://img.shields.io/pypi/pyversions/adqa)](https://pypi.org/project/adqa/)
<br />
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/Mohammad-Talaat7/autonomous-data-quality-agent/branch/main/graph/badge.svg)](https://codecov.io/gh/Mohammad-Talaat7/autonomous-data-quality-agent)

**The intelligent, autonomous agent for high-performance data quality inspection, risk detection, and automated remediation.**

[Getting Started](#-getting-started) • [Key Features](#-key-features) • [Documentation](https://Mohammad-Talaat7.github.io/autonomous-data-quality-agent/) • [Rust TUI](#-rust-tui) • [Contributing](#-contributing) • [Downloads](https://pypi.org/project/adqa/#files)

</div>

---

## 🧐 Why ADQA?

In the era of **Data-centric AI**, your models are only as good as your data. Yet, Data Scientists spend up to **80% of their time** cleaning data.

ADQA solves this by providing an **autonomous loop**:
1.  **Observe**: Deep multi-dimensional profiling of your dataset.
2.  **Orient**: Detect complex risks like PII leakage, statistical bias, and structural anomalies.
3.  **Decide**: Generate an execution plan with prioritized remediations.
4.  **Act**: Heal the data autonomously or with human oversight.

## 🚀 Vision

ADQA combines a robust **Python backend** for seamless pipeline integration with a high-performance **Rust-based TUI** for interactive observability. It bridges the gap between fully automated data engineering and the critical need for human intuition in data quality.

## 📚 Documentation

Detailed guides, architecture deep-dives, and full API references are available at:
**[Mohammad-Talaat7.github.io/autonomous-data-quality-agent](https://Mohammad-Talaat7.github.io/autonomous-data-quality-agent/)**

## ✨ Key Features

- **🔍 Multi-Source Ingress:** Direct support for CSV, Parquet, Excel, SQL (Postgres, MySQL, etc.), S3, and **300+ SaaS sources** via Airbyte.
- **🧠 Intelligent Profiling:** 
    - **Structural:** Automated type inference and null-ratio analysis.
    - **Behavioral:** Outlier detection (Z-score/IQR), skewness, and cardinality.
    - **Semantic:** ML classifiers identify PII (Emails, SSNs, CCs) and domain-specific types.
- **🚨 Hybrid Risk Detection:** 
    - **Rule-based:** Deterministic checks for drift, range violations, and duplicates.
    - **ML-based:** Advanced anomaly detection via **Isolation Forests** and bias identification.
- **🛠️ Autonomous Remediation:** 
    - **Advisory Mode:** Generate audit-ready reports of what *should* be fixed.
    - **Automatic Mode:** Fully autonomous healing (impute, drop, clip, mask).
    - **Human-in-the-Loop:** Interactive approval of fixes via CLI or TUI.
- **📜 Full Traceability:** Industry-standard data lineage and execution traces for every transformation.

## 📦 Installation

### Python Library & CLI
```bash
pip install adqa
# Or for full ML + Data Ingress capabilities:
pip install "adqa[all]"
```

### Rust TUI
The TUI is distributed as a standalone binary. Install via cargo:
```bash
cargo install adqa-tui
```
*Or download pre-compiled binaries from the [Releases](https://github.com/Mohammad-Talaat7/autonomous-data-quality-agent/releases) page.*

## 🛠 Usage

### Command Line Interface (CLI)
Quickly inspect any dataset:
```bash
adqa analyze my_data.parquet --mode advisory
```

### Python API
Integrate into your training or ETL pipelines:
```python
from adqa import ADQA, ADQAConfig

# High-performance profiling and detection
agent = ADQA.from_path("data.csv", config=ADQAConfig(execution_mode="automatic"))
result = agent.analyze()

# Access the healed dataframe immediately
clean_df = result.dataframe
print(result.summary())
```

## 🖥 Rust TUI

Monitor your agent's reasoning in real-time. The Rust TUI provides a zero-latency dashboard for exploring data lineages, trace events, and approving remediation plans.

```bash
adqa-tui
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) to get started with:
- Adding new **Detectors**.
- Improving the **Scoring Engine**.
- Enhancing the **Rust TUI**.

## 📄 License

ADQA is released under the **MIT License**. See [LICENSE](LICENSE) for details.
