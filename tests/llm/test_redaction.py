# tests/llm/test_redaction.py
from adqa.llm.redaction import redact_text, sanitize_payload


def test_redact_text_masks_common_pii():
    text = "Email me at user@example.com or call 555-123-4567 with SSN 123-45-6789."
    redacted = redact_text(text)

    assert "user@example.com" not in redacted
    assert "555-123-4567" not in redacted
    assert "123-45-6789" not in redacted


def test_sanitize_payload_limits_row_samples_and_marks_truncation():
    payload = {
        "row_samples": [{"email": "user@example.com"} for _ in range(10)],
        "notes": "x" * 200,
    }

    sanitized = sanitize_payload(payload, max_rows=3, max_chars=120)

    assert len(sanitized["row_samples"]) <= 3
    assert "[REDACTED_EMAIL]" in str(sanitized)
