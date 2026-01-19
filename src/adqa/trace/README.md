# ADQA Trace System

This package contains the core tracing, lineage, reasoning, and audit
infrastructure for ADQA.

Design principles:

- Trace is a system, not a logger
- Deterministic & replayable
- Backend-agnostic
- No LLM dependency at this layer
