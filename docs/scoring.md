# Quality Scoring

The Scoring Engine aggregates individual detections into a unified quality score and decision.

## Quality Dimensions

ADQA categorizes every detection into one of several standard quality dimensions:

| Dimension | Description |
|-----------|-------------|
| **Validity** | Conformity to logical rules and semantic ranges. |
| **Completeness** | Presence of required values (null-free). |
| **Uniqueness** | Freedom from redundancy and duplicates. |
| **Consistency** | Statistical stability and lack of drift. |
| **Privacy** | Absence of sensitive or non-compliant PII. |

## Scoring Logic

1. **Detection Scoring**: Each issue is assigned a severity score (0.0 to 1.0).
2. **Dimension Aggregation**: Scores are aggregated within each dimension using a weighted average or maximum severity.
3. **Global Score**: A final quality score is calculated for the entire dataset.

## Quality Decision

Based on the global score and configured thresholds, ADQA makes one of three decisions:

- **✅ PASS**: No critical issues found. Global score is above the "Pass" threshold.
- **⚠️ WARN**: Potential issues detected. Score is below "Pass" but above "Fail".
- **❌ FAIL**: Critical quality risks identified. Score is below the "Fail" threshold.
