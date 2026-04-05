# Execution & Healing

The Execution Engine is responsible for generating and applying remediations to fix identified data quality issues.

## Execution Modes

ADQA operates in three distinct modes to balance autonomy with safety:

### 1. Advisory Mode
- **Behavior**: Profiles and detects issues, but only *proposes* actions.
- **Output**: An `ActionPlan` containing a list of recommended fixes.
- **Use Case**: Initial analysis or low-trust environments.

### 2. Human-in-the-loop (HIL)
- **Behavior**: Proposes an `ActionPlan` and waits for external approval.
- **Output**: Executes only the actions that have been explicitly approved.
- **Use Case**: Critical datasets where every change must be verified.

### 3. Automatic Mode
- **Behavior**: Fully autonomous. Detects and applies remediations immediately.
- **Output**: A new, healed DataFrame.
- **Use Case**: CI/CD pipelines, data pre-processing for ML.

## Common Remediations

- **DROP**: Removes constant columns or redundant features.
- **DEDUPE**: Removes duplicate rows.
- **IMPUTE**: Fills missing values using mean, median, or constant values.
- **CLIP**: Winsorizes outliers to a specific percentile.
- **MASK**: Anonymizes PII data.
- **TRANSFORM**: Applies mathematical transformations (e.g., Log scale for skewed data).

## Example: Automatic Healing

```python
from adqa import ADQA, ADQAConfig, ExecutionMode

config = ADQAConfig(execution_mode=ExecutionMode.AUTOMATIC)
agent = ADQA.from_path("dirty_data.csv", config=config)

# This will detect issues and apply fixes in one call
result = agent.analyze()

# result.dataframe now contains the healed data
healed_df = result.dataframe
```
