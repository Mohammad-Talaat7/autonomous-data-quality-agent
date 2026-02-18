
# Phase 3 — MCP Feature Descriptions (ADQA)

This document defines the **Machine Control Protocol (MCP)** descriptions for all Phase 3 features, in **development order**.
It is intended for contributors and agents to understand scope, responsibilities, constraints, and integration points.

---

## Feature 3.1 — Configuration System

### 🎯 Objective
Provide a single, immutable source of truth controlling tracing, lineage, ML usage, storage backend, and execution semantics.

### 📥 Inputs
- User configuration parameters

### 📤 Outputs
- Validated ADQAConfig
- Configuration snapshot for tracing

### 🔒 Constraints
- Immutable after initialization
- Fail fast on invalid combinations
- No business logic

### 🔗 Integration
- Consumed by all Phase 3 features
- Emits CONFIG_SNAPSHOT trace

---

## Feature 3.2 — Data Ingress

### 🎯 Objective
Standardize reading data from external sources into ADQA.

### 📥 Inputs
- CSV, DataFrame, database, warehouse sources

### 📤 Outputs
- pandas.DataFrame

### 🔒 Constraints
- Pandas is canonical internal format
- No profiling or validation
- Stateless readers

### 🔗 Integration
- Feeds profiling engine
- Emits READ_DATA trace
- Records lineage (source → dataframe)

---

## Feature 3.3 — Profiling Engine (Rule + ML)

### 🎯 Objective
Generate descriptive statistics and ML-based summaries for datasets.

### 📥 Inputs
- pandas.DataFrame
- Configuration (ML enabled/disabled)

### 📤 Outputs
- DatasetProfile
- ColumnProfile[]
- MLProfile[] (optional)

### 🔒 Constraints
- No decisions or scoring
- Deterministic and reproducible
- No data mutation

### 🔗 Integration
- Feeds detection engine
- Emits PROFILE_* and ML_PROFILE_RUN traces
- Records lineage (dataframe → profile)

---

## Feature 3.4 — Detection Engine (Rule + ML)

### 🎯 Objective
Identify potential data quality issues using profiles and ML signals.

### 📥 Inputs
- Profiles
- ML profiles
- Detector definitions

### 📤 Outputs
- DetectionResult[]
- MLEvidence[]

### 🔒 Constraints
- No final decisions
- ML produces signals only
- Structured evidence required

### 🔗 Integration
- Feeds scoring engine
- Emits RUN_DETECTOR and ML_MODEL_RUN traces
- Records lineage (profile → detection)

---

## Feature 3.5 — Scoring & Aggregation

### 🎯 Objective
Produce deterministic, explainable quality decisions.

### 📥 Inputs
- Detection results
- ML evidence

### 📤 Outputs
- Score[]
- QualityDecision

### 🔒 Constraints
- Deterministic formulas only
- No ML usage
- Centralized thresholds

### 🔗 Integration
- Feeds execution semantics
- Emits COMPUTE_SCORE and QUALITY_DECISION traces
- Records lineage (detection → decision)

---

## Feature 3.6 — Execution Semantics

### 🎯 Objective
Define what actions ADQA takes based on the quality decision.

### 📥 Inputs
- QualityDecision
- Execution mode

### 📤 Outputs
- Advisory output
- Human approval request
- Executed actions

### 🔒 Constraints
- No silent side effects
- Explicit human confirmation
- Fully traceable actions

### 🔗 Integration
- Final pipeline stage
- Emits ACTION_* traces
- Records lineage (decision → action)

---

## Feature 3.7 — Public ADQA API

### 🎯 Objective
Expose a stable public interface for end users.

### 📥 Inputs
- Data source
- ADQAConfig

### 📤 Outputs
- ADQAResult

### 🔒 Constraints
- No analytical logic
- Must orchestrate defined pipeline
- Must respect config and tracing

### 🔗 Integration
- Coordinates all Phase 3 features
- Emits ADQA_ANALYZE trace

---

## Summary

Phase 3 delivers a deterministic, trace-governed, ML-assisted data quality analysis pipeline with a stable public API.
