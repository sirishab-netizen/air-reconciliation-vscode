from reconciliation.models import ReconciliationResult

from .investigator import ExceptionInvestigator
from .llm_reasoner import LLMReasoner
from .models import InvestigationCase
from .trace import AgentTrace
from time import perf_counter


class ExceptionOrchestrator:

    def __init__(
        self,
        investigator: ExceptionInvestigator,
        reasoner: LLMReasoner,
        trace: AgentTrace | None = None,
    ):
        self.investigator = investigator
        self.reasoner = reasoner
        self.trace = trace

    def process(
        self,
        result: ReconciliationResult,
    ) -> InvestigationCase | None:

        start_time = perf_counter()

        if result.status != "EXCEPTION":
            return None

        if not result.exception_type:
            return None

        if self.trace:
            self.trace.add(
                "AGENT",
                f"Investigation started for {result.booking_id}",
            )
            self.trace.add("EXCEPTION", str(result.exception_type))

        # Step 1: deterministic investigation
        case = self.investigator.investigate(
            booking_id=result.booking_id,
            exception_type=result.exception_type,
            expected_amount=result.expected_amount,
            actual_amount=result.actual_amount,
            variance=result.variance,
        )

        if self.trace:
            if case.findings:
                for finding in case.findings:
                    self.trace.add(
                    "EVIDENCE",
                    finding
                )
            else:
                self.trace.add(
                "EVIDENCE",
                "No deterministic findings were produced"
        )

        # Step 2: build compact evidence for the LLM
        evidence = {
            "booking_id": result.booking_id,
            "exception_type": result.exception_type,
            "expected_amount": (
                str(result.expected_amount)
                if result.expected_amount is not None
                else None
            ),
            "actual_amount": (
                str(result.actual_amount)
                if result.actual_amount is not None
                else None
            ),
            "variance": (
                str(result.variance)
                if result.variance is not None
                else None
            ),
            "deterministic_evidence": case.evidence,
            "deterministic_findings": case.findings,
        }

        if self.trace:
            self.trace.add(
                "REASONING",
                "LLM reasoner started",
            )

        # Step 3: agentic investigation
        reasoning = self.reasoner.reason(
            exception_type=result.exception_type,
            evidence=evidence,
        )

        if self.trace:
            self.trace.add(
                "REASONING",
                (
                    "Reasoning completed with finding confidence "
                    f"{reasoning.finding_confidence} and root-cause confidence "
                    f"{reasoning.root_cause_confidence}"
                ),
            )

        if self.trace:
            self.trace.add(
                "RECOMMENDATION",
                reasoning.recommendation,
            )

        # Step 4: combine deterministic investigation
        # with probabilistic reasoning
        case.findings.extend(reasoning.findings)

        case.hypothesis = reasoning.hypothesis
        case.finding_confidence = reasoning.finding_confidence
        case.root_cause_confidence = reasoning.root_cause_confidence
        case.recommendation = reasoning.recommendation

        # Financial changes always require approval.
        case.requires_human_approval = True

        case.status = "INVESTIGATED"

        if self.trace:
            self.trace.add(
                "CASE",
                f"Case status changed to {case.status}",
            )

        total_duration_ms = (perf_counter() - start_time) * 1000

        if self.trace:
            self.trace.add(
            "METRIC",
            "Investigation completed",
            duration_ms=total_duration_ms,
        )

        return case

    def reinvestigate(
        self,
        case: InvestigationCase,
        ) -> InvestigationCase:
        if case.approval_status != "MORE_EVIDENCE_REQUIRED":
            return case

        if not case.evidence_requests:
            return case

        request = case.evidence_requests[-1]

        if self.trace:
            self.trace.add(
                "HUMAN",
                f"Additional evidence requested: {request.question}"
            )

        # Re-run the deterministic investigation against the same
        # authoritative sources.
        updated_case = self.investigator.investigate(
            booking_id=case.booking_id,
            exception_type=case.exception_type,
            expected_amount=None,
            actual_amount=None,
            variance=None,
        )

        # Preserve the original case history.
        updated_case.evidence_requests = case.evidence_requests
        updated_case.investigation_steps = (
            case.investigation_steps
            + updated_case.investigation_steps
        )

        updated_case.approval_status = "PENDING"
        updated_case.status = "INVESTIGATED"
        updated_case.requires_human_approval = True

        request.status = "FULFILLED"
        request.response = (
             "Additional authoritative records were re-evaluated "
            "against the original reconciliation exception."
        )

        if self.trace:
            self.trace.add(
                "EVIDENCE",
                "Additional evidence investigation completed"
            )
            self.trace.add(
                "CASE",
                "Case returned to INVESTIGATED for human review"
            )

        return updated_case