from reconciliation.agent.llm_reasoner import LLMReasoner


def test_llm_reasoner():
    reasoner = LLMReasoner()

    evidence = {
        "booking_id": "BKG006",
        "exception_type": "PARTIAL_REFUND_MISMATCH",
        "booking_total": "476.10",
        "ticket_total": "476.10",
        "expected_refund": "200.00",
        "actual_refund": "180.00",
        "variance": "-20.00",
    }

    result = reasoner.reason(
        exception_type="PARTIAL_REFUND_MISMATCH",
        evidence=evidence,
    )

    assert result.findings
    assert result.hypothesis
    assert result.confidence in {"HIGH", "MEDIUM", "LOW"}
    assert result.recommendation
    assert result.requires_human_approval is True