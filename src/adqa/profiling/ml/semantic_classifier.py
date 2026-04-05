from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from ...config.model import ProfilingThresholds

from ..models.column_profile import ColumnProfile
from ..models.ml_profile import MLProfile

MODEL_NAME = "semantic_classifier"
MODEL_VERSION = "1.1"


@dataclass(frozen=True)
class SemanticRule:
    name: str
    pattern: Pattern[str]
    keywords: tuple[str, ...]
    weight_pattern: float = 0.7
    weight_keyword: float = 0.3


SEMANTIC_REGISTRY = [
    SemanticRule(
        name="email",
        pattern=re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
        keywords=("email", "mail", "contact"),
    ),
    SemanticRule(
        name="phone",
        pattern=re.compile(r"^\+?[\d\s\-\(\)]{7,20}$"),
        keywords=("phone", "tel", "mobile", "cell"),
    ),
    SemanticRule(
        name="credit_card",
        pattern=re.compile(
            r"^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})$"
        ),
        keywords=("credit", "card", "visa", "mastercard", "amex", "cc_number"),
    ),
    SemanticRule(
        name="ssn",
        pattern=re.compile(r"^\d{3}-\d{2}-\d{4}$|^\d{9}$"),
        keywords=("ssn", "social_security", "national_id", "tax_id"),
    ),
    SemanticRule(
        name="date_of_birth",
        pattern=re.compile(r"^\d{4}-\d{2}-\d{2}$|^\d{2}/\d{2}/\d{4}$"),
        keywords=("dob", "birth", "birthday", "born"),
    ),
    SemanticRule(
        name="ip_address",
        pattern=re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"),
        keywords=("ip", "address", "host"),
    ),
    SemanticRule(
        name="identifier",
        pattern=re.compile(r"^\d+$|^[0-9a-fA-F-]{8,36}$"),
        keywords=("id", "uuid", "pk", "key", "code"),
    ),
    SemanticRule(
        name="country_code",
        pattern=re.compile(r"^[A-Z]{2,3}$"),
        keywords=("country", "nation", "cc"),
    ),
]


def classify_column_semantic(
    series: pd.Series[Any],
    column_profile: ColumnProfile,
    thresholds: ProfilingThresholds | None = None,
) -> MLProfile | None:
    """
    Score column against semantic registry.
    """
    clean = series.dropna().astype(str)
    if clean.empty:
        return None

    sample_size = thresholds.semantic_sample_size if thresholds else 100
    min_conf = thresholds.semantic_min_confidence if thresholds else 0.4

    weight_pattern = thresholds.semantic_weight_pattern if thresholds else 0.7
    weight_keyword = thresholds.semantic_weight_keyword if thresholds else 0.3

    column_name = column_profile.name.lower()
    sample = clean.head(sample_size)

    scores: dict[str, float] = {}

    for rule in SEMANTIC_REGISTRY:
        # 1. Keyword match in name
        keyword_match = any(k in column_name for k in rule.keywords)
        keyword_score = 1.0 if keyword_match else 0.0

        # 2. Pattern match in sample values
        pattern_matches = sample.str.match(rule.pattern.pattern).mean()
        pattern_score = float(pattern_matches)

        # Combined score
        final_score = (pattern_score * weight_pattern) + (
            keyword_score * weight_keyword
        )

        if final_score > 0.1:
            scores[rule.name] = final_score

    if not scores:
        return None

    # Pick best match
    best_class = max(scores, key=lambda k: scores[k])
    confidence = scores[best_class]

    if confidence < min_conf:
        return None

    return MLProfile(
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        target=column_profile.name,
        outputs={
            "predicted_class": best_class,
            "confidence": confidence,
        },
    )
