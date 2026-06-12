# tests/llm/test_models.py
from adqa.llm.models import ExplanationRequest, ExplanationResponse, LLMMessage, LLMRequest


def test_llm_request_hash_is_stable():
    request = LLMRequest(
        model="gpt-4o-mini",
        prompt_version="v1",
        messages=[LLMMessage(role="system", content="hi")],
    )

    assert request.input_hash() == request.input_hash()


def test_explanation_models_validate():
    request = ExplanationRequest(
        decision="WARN",
        score=0.42,
        severity_level="MEDIUM",
        dimension_breakdown={"completeness": 0.42},
        issue_breakdown={"missing_values": 0.42},
        dominant_issues=["missing_values"],
        affected_columns=["email"],
        issue_map={"missing_values": ["email"]},
        reason_codes=["missing_values"],
        dataset_summary={
            "row_count": 10,
            "column_count": 2,
            "duplicate_row_ratio": 0.0,
            "total_null_ratio": 0.1,
            "columns": ["email", "age"],
            "correlations_present": False,
        },
    )

    response = ExplanationResponse(
        provider="litellm",
        model="gpt-4o-mini",
        prompt_version="v1",
        input_hash="abc",
        output_hash="def",
        short_summary="Summary",
        top_issues=["missing_values"],
        affected_columns=["email"],
        why_decision=["Null ratio exceeded threshold."],
        recommended_next_steps=["Inspect source ingestion."],
    )

    assert request.reason_codes == ["missing_values"]
    assert response.short_summary == "Summary"
