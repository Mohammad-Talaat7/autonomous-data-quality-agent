# Explanation module (`adqa.explanation`)

## Explanation Engine

`ExplanationEngine` takes ADQA's structured pipeline outputs and produces an
`ADQAExplanation`:

- `short_summary` — one-sentence decision description
- `top_issues` — ranked issue types
- `affected_columns` — columns requiring attention
- `why_decision` — reasons (deterministic reason codes explained)
- `recommended_next_steps` — actionable suggestions
- `uncertainty` — caveats or limitations

The engine only sees structured summaries — never raw DataFrames or row values.

## Root Cause Engine

`RootCauseEngine` assembles deterministic hypotheses from detection results:

- Missing values → ETL completeness check
- High correlation → domain logic review
- PII detected → masking recommendation
- …and more

Each hypothesis includes supporting evidence, confidence, and caveats.

## Remediation Engine

`RemediationProposalEngine` maps issue types to allowed executor operations:

| Issue Type       | Mapped Action        |
|------------------|----------------------|
| missing_values   | impute              |
| duplicate_rows   | remove_duplicates   |
| constant_column  | drop_column         |
| outliers         | clip                |
| high_skewness    | log_transform       |
| pii_detected     | mask_pii            |
| anomaly_score    | remove_anomalies    |
| type_mismatch    | cast_type           |

Proposals outside the allowed list are kept in `unsupported_suggestions`
and are never executed.
