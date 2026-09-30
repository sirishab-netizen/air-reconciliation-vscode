
import json
import os

from dataclasses import dataclass
from typing import Any
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-5.6-luna"

@dataclass
class ReasoningResult:
    findings: list[str]
    hypothesis: str
    confidence: str
    recommendation: str
    requires_human_approval: bool


class LLMReasoner:

    def reason(
        self,
        exception_type: str,
        evidence: dict[str, Any],
    ) -> ReasoningResult:

        """
        Reason over already-validated evidence.

        Important:
        The LLM should NOT calculate financial truth.
        Financial amounts and variances come from deterministic code.
        """

        if exception_type == "PARTIAL_REFUND_MISMATCH":

            expected = evidence.get("expected_refund")
            actual = evidence.get("actual_refund")
            variance = evidence.get("variance")

            return ReasoningResult(
                findings=[
                    f"Expected refund: {expected}",
                    f"Actual refund: {actual}",
                    f"Variance: {variance}",
                ],
                hypothesis=(
                    "The actual refund is lower than the expected "
                    "refund. The available evidence confirms the "
                    "variance but does not establish its business cause."
                ),
                confidence="MEDIUM",
                recommendation=(
                    "Route the case for human review and determine "
                    "the business reason for the refund difference."
                ),
                requires_human_approval=True,
            )

        return ReasoningResult(
            findings=[
                "No specialized reasoning workflow exists "
                f"for {exception_type}."
            ],
            hypothesis="Insufficient evidence for automated explanation.",
            confidence="LOW",
            recommendation="Route to human review.",
            requires_human_approval=True,
        )