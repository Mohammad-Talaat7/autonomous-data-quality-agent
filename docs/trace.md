# Trace System

The `adqa.trace` package provides the core infrastructure for tracing, lineage, reasoning, and auditing. It is designed to be deterministic, replayable, and backend-agnostic.

## Key Concepts

- **TraceContext**: Identifies a single execution scope (trace ID, user, dataset).
- **TraceEvent**: An atomic unit of observability (start, end, result, error).
- **TraceStore**: Persistent storage for events (Memory, JSON, DB).
- **TraceEmitter**: Handles the emission of events to the store.
- **LineageRecorder**: Tracks data transformation graphs.

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
