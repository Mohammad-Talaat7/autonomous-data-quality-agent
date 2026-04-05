# Detection

The Detection Engine evaluates the profiles generated in the previous step against a set of rules and models to identify quality issues.

## Hybrid Detection

ADQA uses a "Hybrid Engine" that combines deterministic rules with probabilistic ML models.

### Rule-Based Detectors
- **Missing Values**: Detects when null ratios exceed thresholds.
- **Constant Columns**: Identifies columns with no variance.
- **Duplicates**: Finds redundant rows or near-duplicates.
- **Outliers**: Uses Z-score or IQR to find behavioral anomalies.
- **Range Violations**: Checks if values fall within logical boundaries (e.g., Age 0-120).
- **Correlation**: Identifies redundant features.

### ML-Based Detectors
- **Isolation Forest**: Detects structural anomalies across the whole dataset.
- **PII Detector**: Identifies sensitive information (Privacy risk).
- **Bias Detector**: Identifies statistical bias in categorical distributions.
- **Semantic Boundary**: Uses ML to predict the expected range for a specific semantic type.

## Configuration

Detectors are highly configurable via `ADQAConfig`. You can adjust thresholds for each detector:

```python
config = ADQAConfig(
    detection={
        "thresholds": {
            "missing_values_threshold": 0.1,
            "outlier_ratio_threshold": 0.05
        }
    }
)
```
