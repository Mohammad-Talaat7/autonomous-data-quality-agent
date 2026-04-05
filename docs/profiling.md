# Profiling

The Profiling Engine is the first step in ADQA's analysis pipeline. It analyzes the dataset to understand its structure and content.

## Profiling Dimensions

ADQA profiles data across four main categories:

### 1. Structural Profiling
Captures basic properties of columns:
- Null counts and ratios.
- Uniqueness and cardinality.
- Memory usage.
- Data types (Physical and Logical).

### 2. Behavioral Profiling
Analyzes the distribution and patterns of values:
- Range (min, max).
- Central tendency (mean, median).
- Dispersion (std, variance).
- Outlier ratios.
- Skewness and Kurtosis.

### 3. Semantic Profiling
Identifies the *meaning* of the data:
- Uses a hybrid approach: Regex patterns + ML Classifiers.
- Common tags: `EMAIL`, `PHONE`, `ADDRESS`, `SSN`, `CREDIT_CARD`, etc.

### 4. Relational Profiling
Identifies relationships between columns:
- Correlation matrix (Pearson/Spearman).
- Functional dependencies (planned).

## ML-Enhanced Profiling

When `ml_enabled` is set to `True`, ADQA uses pre-trained models to:
- Predict logical types with higher accuracy.
- Detect complex semantic violations.
- Amplify anomaly signals.
