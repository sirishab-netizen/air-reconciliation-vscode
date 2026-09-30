from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

Status = Literal["RECONCILED", "EXCEPTION", "PENDING"]

@dataclass
class ReconciliationResult:
    booking_id: str
    status: Status
    exception_type: str | None = None
    expected_amount: Decimal | None = None
    actual_amount: Decimal | None = None
    variance: Decimal | None = None
    evidence: list[str] = field(default_factory=list)
    message: str = ""
