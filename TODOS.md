# TODOS.md

## Autonomous Data Quality Agent — AI Systems–First Agile Plan

---

## Project Overview

**Goal**  
Build an **Autonomous Data Quality Agent** that profiles datasets, detects data quality issues, explains findings via controlled LLM reasoning, proposes safe fixes, and provides full **traceability, evaluation, and governance** across all components.

**Timeline:** 2–4 weeks  
**Methodology:** SCRUM-inspired Agile  
**Sprint Length:** 4–5 days  
**Execution Philosophy:** Advisory-first, explainable, human-in-the-loop

---

## Core Principles

- Deterministic logic before probabilistic reasoning
- AI outputs are advisory, never authoritative
- Confidence ≠ correctness
- Every decision must be traceable
- Every component must be evaluable
- Safety, explainability, and governance are functional requirements

---

## High-Level Timeline

| Phase | Name                              | Duration |
| ----- | --------------------------------- | -------- |
| 0     | Research & Gap Analysis           | 3–4 days |
| 1     | Foundation & CI Setup             | 3–4 days |
| 2     | Trace System & Observability      | 2–3 days |
| 3     | Profiling, Detection & Scoring    | 4–6 days |
| 4     | LLM Reasoning Layer (LiteLLM)     | 4–5 days |
| 5     | Execution, Safety & HITL          | 3–4 days |
| 6     | Evaluation, Testing & Calibration | 3–5 days |
| 7     | Documentation & Wiki              | 2–3 days |
| 8     | Packaging & Publishing            | 2–3 days |

**Total:** ~24–32 days (parallelizable)

---

## Phase 0 — Research & Gap Analysis

**Duration:** 3–4 days  
**Sprint Goal:** Identify architectural, AI, and governance gaps in existing tools.

### To-Do

- [x] Study SmartDataAI, PandasAI, llm4data, pandas-llm, LLM4EDA, LIDA, llm-auto-eda, klar-EDA
- [x] Document architecture, LLM dependency, explainability, safety gaps
- [x] Identify differentiators (advisory-first, traceability, confidence)
- [x] Write `RESEARCH.md`

---

## Phase 1 — Foundation & CI Setup

**Duration:** 3–4 days

### To-Do

- [x] Core abstractions (DataSource, DatasetProfile, Rule, Metric, Issue)
- [x] pyproject.toml
- [x] GitHub Actions (lint, type-check, tests)
- [x] Determine the frameworks used in the project (sqlmodel, astor, litellm, poetry, [langchain,streamlit])
- [x] Check Datatracer, DVC

---

## Phase 2 — Trace System & Observability

**Duration:** 2–3 days

### Trace System Components

- TraceEvent
- TraceEmitter
- TraceRecorder
- TraceStore

### To-Do

- [ ] Define Trace schema
- [ ] Implement Trace system
- [ ] Integrate tracing hooks

---

## Phase 3 — Profiling, Detection & Scoring

**Duration:** 4–6 days

### To-Do

- [ ] Profiling & detectors
- [ ] Severity scoring & confidence
- [ ] Emit traces

---

## Phase 4 — LLM Reasoning Layer (LiteLLM)

**Duration:** 4–5 days

### To-Do

- [ ] LiteLLM integration
- [ ] Multi-provider support
- [ ] Agent implementation
- [ ] Prompt versioning & tracing

---

## Phase 5 — Execution, Safety & HITL

**Duration:** 3–4 days

### To-Do

- [ ] Execution modes
- [ ] Approval & rollback
- [ ] Safety boundaries

---

## Phase 6 — Evaluation, Testing & Calibration

**Duration:** 3–5 days

### To-Do

- [ ] Tests
- [ ] Hyperparameter experiments
- [ ] Evaluation via TraceStore

---

## Phase 7 — Documentation & Wiki

**Duration:** 2–3 days

### To-Do

- [ ] README
- [ ] PROJECT.md
- [ ] Wiki

---

## Phase 8 — Packaging & Publishing

**Duration:** 2–3 days

### To-Do

- [ ] PyPI
- [ ] Docker
- [ ] AUR

---

## Definition of Done (DoD)

- CI passes
- Trace coverage exists
- Evaluations documented
- Hyperparameters justified
- Docs updated
