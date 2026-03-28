
# ML Reproducibility Policy — ADQA Phase 3

## Goal
Ensure that any ML used in ADQA Phase 3 is deterministic, auditable, replayable, and explainable.

This policy applies to:
- ML in profiling
- ML in detection
- Any ML signal influencing scoring (indirectly)

---

## Core Principles

### 1. ML produces signals, not decisions
- ML must never output PASS / WARN / FAIL
- ML must never override deterministic scoring
- ML outputs are evidence only

---

### 2. Fixed and explicit configuration
- All hyperparameters must be explicitly defined
- No reliance on library defaults
- Randomness must be controlled via fixed seeds

---

### 3. Stateless execution
- No online learning
- No cross-run memory
- No warm starts
- Each analyze() call is isolated

---

### 4. Model identity traceability
Every ML execution must record:
- Model name
- Model version
- Hyperparameter hash
- Input profile hash
- Output evidence

---

### 5. Structured numeric evidence
- No free-text explanations
- No opaque objects
- Outputs must be serializable

Example:
MLEvidence(
    model="isolation_forest",
    score=0.83,
    threshold=0.6,
    sample_size=120000
)

---

### 6. Deterministic integration
- ML may influence severity or confidence scaling only
- No ML-defined thresholds
- No ML-based final decisions

---

### 7. Mandatory tracing
- ML_MODEL_RUN trace is required
- ML_PROFILE_RUN trace is required for profiling
- Lineage must be recorded
- If tracing disabled, tracing becomes NOOP but logic still executes

---

## PR Checklist for ML Changes

- [ ] Hyperparameters explicit
- [ ] Randomness controlled
- [ ] Stateless execution
- [ ] Structured evidence
- [ ] Trace emission implemented
- [ ] Replayable execution verified

Failure on any item → PR rejected.
