
# Tracing System (ADQA)

## Overview

The ADQA tracing system provides **deterministic, structured, and backend-agnostic execution tracing** for data quality workflows.

It is designed to answer questions like:

- What happened?
- Why did it happen?
- What data and decisions led to this outcome?
- Can this be replayed or audited deterministically?

This system is **not a logger** and **not an observability tool**. It is execution-aware infrastructure that captures events, lineage, reasoning metadata, and audit-ready summaries.

## Design Principles

1. Tracing is structured, not textual
2. Lineage is first-class
3. Tracing is write-only at runtime
4. Interpretation happens later
5. No LLM dependency in core tracing
6. Backend-agnostic storage
7. Low coupling to user code

## Architecture

```
User Code
   |
Execution Hooks
   |
Trace Core
   |
Lineage + Store
   |
Audit Layer
```

## Core Concepts

### Trace Context
Defines execution boundaries and owns the trace lifecycle.

### Trace Events
Structured events such as START, END, and ERROR.

### Execution Hooks
Decorators that automatically manage tracing.

### Lineage
Captures data and decision flow.

### Trace Stores
Persist trace data (InMemory, JSON).

### Audit Layer
Produces deterministic human-readable reports.

## Happy Path

1. Function called
2. Trace context opened
3. START event emitted
4. Inputs recorded
5. Function executes
6. Outputs recorded
7. END event emitted
8. Context closed

# Full end-to-end example using ADQA tracing + lineage

## Setup

To use the tracing system, you first need to initialize the core components and set up the context.

```python
from adqa.trace.context import TraceContext
from adqa.trace.emitter import TraceEmitter
from adqa.trace.store.inmemory_store import InMemoryTraceStore
from adqa.trace.lineage.memory import InMemoryLineageAdapter
from adqa.trace.lineage.recorder import LineageRecorder
from adqa.trace.hooks.context import set_current_emitter
from adqa.trace.hooks.lineage_context import set_current_lineage_recorder

# 1. Initialize Storage
trace_store = InMemoryTraceStore()
lineage_adapter = InMemoryLineageAdapter()

# 2. Create Context
context = TraceContext()  # Generates a unique trace_id

# 3. Initialize Emitter and Recorder
emitter = TraceEmitter(context, store=trace_store, store_traces=True)
lineage = LineageRecorder(adapter=lineage_adapter, enabled=True)
lineage.start_trace(context.trace_id)

# 4. Set Implicit Context (Recommended)
# This allows decorators to work without manually passing 'emitter' or 'lineage'
set_current_emitter(emitter)
set_current_lineage_recorder(lineage)
```

## Execution Tracing (`@trace_*`)

Use decorators to trace specific types of logic. These hooks automatically record `start` (execution) and `success/failure` events, including arguments and return values.

### Available Decorators
- `@trace_metric`: For metric calculations.
- `@trace_rule`: For data quality checks.
- `@trace_fix`: For remediation proposals.

### Example

```python
from adqa.trace.hooks.decorators import trace_metric, trace_rule

@trace_metric()
def calculate_completeness(column_data: list) -> float:
    if not column_data:
        return 0.0
    return len([x for x in column_data if x is not None]) / len(column_data)

@trace_rule()
def check_threshold(metric_value: float, threshold: float) -> bool:
    return metric_value >= threshold

# Usage
score = calculate_completeness([1, 2, None, 4])  # Automatically traced
is_valid = check_threshold(score, 0.9)          # Automatically traced
```

## Lineage Tracing (`@trace_lineage`)

Use `@trace_lineage` to track data transformations. This records operations, inputs (arguments), outputs (return values), and metadata.

### Features
- **Automatic Input Capture**: Captures function arguments.
- **Automatic Output Capture**: Captures return values (can be disabled with `capture_output=False`).
- **Metadata**: Attach static metadata to the lineage node.
- **Implicit Context**: Works seamlessly with `set_current_lineage_recorder`.

### Example

```python
from adqa.trace.hooks.decorators import trace_lineage

@trace_lineage(
    operation="clean_text_column",
    metadata={"strategy": "lowercase_strip"}
)
def clean_names(names: list[str]) -> list[str]:
    return [n.strip().lower() for n in names]

# Usage
cleaned = clean_names(["  Alice ", "BOB"])

# Result in LineageRecorder:
# Node(
#   operation="clean_text_column",
#   inputs={"args": [["  Alice ", "BOB"]], "kwargs": {}},
#   outputs=["alice", "bob"],
#   metadata={"strategy": "lowercase_strip"}
# )
```

## Accessing Traces and Lineage

After execution, you can retrieve the recorded data from the stores.

```python
# 1. Retrieve Trace Events
events = trace_store.get(context.trace_id)
for event in events:
    print(f"[{event.timestamp}] {event.name} ({event.event_type}): {event.outputs}")

# 2. Retrieve Lineage Graph
nodes = lineage_adapter.get(context.trace_id)
for node in nodes:
    print(f"Op: {node.operation} -> Outputs: {node.outputs}")
```
