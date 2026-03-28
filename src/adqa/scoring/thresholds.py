class Thresholds:
    # Decision thresholds
    PASS: float = 0.2
    WARN: float = 0.5

    # Severity levels
    LEVELS: dict[str, float] = {
        "LOW": 0.0,
        "MEDIUM": 0.2,
        "HIGH": 0.4,
        "CRITICAL": 0.7,
    }

    # Default weights
    DEFAULT_WEIGHT: float = 1.0
