from typing import Any

from .models import NormalizedDetection


def normalize_detection_results(
    detection_results: Any, ml_evidence: Any = None
) -> list[NormalizedDetection]:
    """
    Convert detection outputs into normalized scoring inputs.
    """

    normalized = []

    # -------- Rules --------
    if detection_results:
        for r in detection_results:
            normalized.append(
                NormalizedDetection(
                    detector_id=getattr(r, "detector_name", "unknown"),
                    # Map issue_type to rule_id for simple mapping
                    rule_id=r.issue_type,
                    issue_type=r.issue_type,
                    dimension=getattr(r, "dimension", "unknown"),
                    column=getattr(r, "column", None),
                    severity=getattr(r, "severity_hint", 0.0),
                    confidence=getattr(r, "confidence", 1.0),
                    metadata=getattr(r, "metrics", {}),
                )
            )

    # -------- ML Signals --------
    if ml_evidence:
        for e in ml_evidence:
            # In ML, 'score' is the severity of the signal
            severity = getattr(e, "score", 0.0)

            normalized.append(
                NormalizedDetection(
                    detector_id=getattr(e, "model_name", "ml_model"),
                    rule_id=e.signal_type,
                    issue_type=e.signal_type,
                    dimension=getattr(e, "dimension", "accuracy"),
                    column=getattr(e, "column", None),
                    severity=severity,
                    confidence=getattr(e, "confidence", 1.0),
                    metadata=getattr(e, "metadata", {}),
                )
            )

    return normalized
