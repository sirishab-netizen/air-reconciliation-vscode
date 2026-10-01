from dataclasses import dataclass, field


@dataclass
class ReasoningResult:
    findings: list[str]
    hypothesis: str
    finding_confidence: str
    root_cause_confidence: str
    recommendation: str
    requires_human_approval: bool


@dataclass
class EvidenceRequest:
    requested_by: str
    question: str
    status: str = "OPEN"
    response: str | None = None

@dataclass
class InvestigationCase:
    case_id: str
    booking_id: str
    exception_type: str

    expected_amount: str | None = None
    actual_amount: str | None = None
    variance: str | None = None

    evidence: list[str] = field(default_factory=list)

    investigation_steps: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    hypothesis: str | None = None
    finding_confidence: str | None = None
    root_cause_confidence: str | None = None
    recommendation: str | None = None

    requires_human_approval: bool = True

    status: str = "OPEN"

    approval_status: str = "PENDING"
    approved_by: str | None = None
    approval_comment: str | None = None

    evidence_requests: list[EvidenceRequest] = field(default_factory=list)

    def approve(self, approved_by: str, comment: str = ""):
         self.approval_status = "APPROVED"
         self.approved_by = approved_by
         self.approval_comment = comment
         self.status = "APPROVED"


    def reject(self, approved_by: str, comment: str = ""):
        self.approval_status = "REJECTED"
        self.approved_by = approved_by
        self.approval_comment = comment
        self.status = "CLOSED"


    def request_more_evidence(
        self,
        requested_by: str,
        comment: str = "",
    ):
        self.approval_status = "MORE_EVIDENCE_REQUIRED"
        self.approved_by = requested_by
        self.approval_comment = comment
        self.status = "INVESTIGATION_REQUIRED"

        self.evidence_requests.append(
            EvidenceRequest(
                requested_by=requested_by,
                question=comment or "Please provide additional evidence.",
            )
        )