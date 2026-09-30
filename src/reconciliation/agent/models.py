from dataclasses import dataclass, field


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
    confidence: str | None = None

    recommendation: str | None = None

    requires_human_approval: bool = True

    status: str = "OPEN"