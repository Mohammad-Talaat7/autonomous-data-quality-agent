## Comparative Research on AI-Powered Data Analysis Libraries

This document summarizes research on several AI-powered data analysis and EDA libraries.  
The goal is to identify architectural patterns, limitations, and gaps that inform the design
of the **ADQA** project.

---

## 1. DockerSandbox (PandasAI Docker Sandbox Extension)

### Features

- Secure execution of LLM-generated Python code
- Isolation from host system
- Custom Docker images for execution
- Protection against prompt-injection and malicious code

### Frameworks Used

- Docker Engine
- PandasAI core framework

### Platforms

- PyPI (`pandasai-docker`)
- GitHub (part of `sinaptik-ai/pandas-ai`)

### Input Stream Types

- Generated Python code (executed in isolation)
- No direct data input (data handled upstream by PandasAI)

### AI Providers

- None (execution sandbox only)

### Architecture Overview

```text
[User Query + DataFrame]
          |
       PandasAI
          |
        [LLM]
          |
   Generated Python Code
          |
   DockerSandbox Container
          |
       Safe Results
```

---

## 2. PandasAI

### Features

- Natural language querying of DataFrames
- Automatic chart generation
- Multi-DataFrame analysis
- Conversational agents with memory
- Safer execution via sandboxing

### Frameworks Used

- Pandas
- Matplotlib / Plotly
- LiteLLM
- Docker (optional sandbox)

### Platforms

- PyPI (`pandasai`)
- GitHub
- Official documentation website

### Input Stream Types

- Pandas DataFrames
- CSV / Excel files
- SQL and MongoDB connectors
- Snowflake, BigQuery,Databricks, and another datastacks from data bases to SaaS tools (list available at the [package website](https://pandas-ai.com/))

### AI Providers

- OpenAI
- HuggingFace models
- Google PaLM / Gemini
- Anthropic
- VertexAI

### Architecture Overview

```text
[User Query + DataFrame]
          |
       PandasAI
          |
  [Construct LLM Prompt with df info]
          |
        [LLM]
          |
   [Python code (via LLM) is returned]
          |
  (Optional Docker Sandbox)
          |
      Results / Charts
```

---

## 3. Pandas-LLM

### Features

- Simple natural language querying
- Privacy (send schema, not full data)
- Lightweight API
- Minimal setup

### Frameworks Used

- Pandas
- OpenAI Python SDK

### Platforms

- PyPI (`pandas-llm`)
- GitHub
- Tar.GZ / Wheel release

### Input Stream Types

- Pandas DataFrames
- CSV / JSON files
- Python lists and dictionaries

### AI Providers

- OpenAI (GPT-3.5 / GPT-4)

### Architecture Overview

```text
[User Query + DataFrame]
          |
       PandasLLM
          |
   Send Schema Only
          |
        [OpenAI]
          |
  Pandas Code Returned
          |
   Local Code Execution
          |
        Result
```

---

## 4. LLM Auto EDA

### Features

- Fully automated EDA
- Interactive HTML reports
- Domain-aware analysis
- Visualizations + narrative

### Frameworks Used

- Pandas
- NumPy
- Plotly
- SciPy / Statsmodels
- OpenAI SDK

### Platforms

- PyPI (`llm-auto-eda`)
- GitHub
- [ReadyTensor Blog](app.readytensor.ai)

### Input Stream Types

- CSV files
- Pandas DataFrames

### AI Providers

- OpenAI (GPT-4 variants)

### Architecture Overview

```text
      [AutoEDA Instance]
             |
      load data (DataLoader)
             |
    run basic EDA (Analyzer)
             |
   compute stats (StatisticalAnalyzer)
             |
   generate plots (Visualizer)
             |
    interpret results (LLMAnalyzer)
             |
 compile report (ReportGenerator)
             |
    [Interactive HTML report]
```

---

## 5. SmartDataAI

### Features

- Conversational data analysis
- Automated data cleaning
- Chart generation
- Multi-turn Q&A
- API / dashboard integration using Streamlit / FastAPI

### Frameworks Used

- Pandas
- Matplotlib
- LangChain

### Platforms

- PyPI (`smartdataai`)
- GitHub

### Input Stream Types

- Pandas DataFrames
- Multiple DataFrames

### AI Providers

- OpenAI (default)
- Any LangChain-compatible LLM

### Architecture Overview

```text
   SmartData(df)
        |
    LLM Agent
        |
  +-------------+
  | Clean Data  |
  | Answer Q&A  |
  | Generate Plots |
  +-------------+
        |
   Updated Data / Charts
```

---

## Cross-Library Observations & Gaps

### Common Patterns

- Heavy reliance on LLM-generated Python code
- Limited traceability and evaluation
- Minimal confidence calibration
- Weak safety and governance mechanisms

### Identified Gaps

- No advisory-first execution model
- No unified trace or audit system
- No systematic evaluation or hyperparameter tuning
- Limited AI governance and explainability

### Key Takeaway

Most existing libraries focus on **convenience and speed**, while lacking the **AI systems rigor**
required for production-grade data quality and AI-assisted decision-making.

Only `PandasAI` Package got good focus on AI systems rigor,
but at the same time it lacked the advisory-first execution mentality and the needed evaluation metrics for silent LLM agent failure.

Each Package nearly got it's own method to return results to the user.
We can combine these methods as the different options for ADQA output, while using the speed tricks discovered by them.

These gaps directly motivate the design choices of the Autonomous Data-Quality Agent (ADQA).
