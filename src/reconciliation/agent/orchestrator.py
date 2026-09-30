from reconciliation.models import ReconciliationResult

from .investigator import ExceptionInvestigator
from .models import InvestigationCase


class ExceptionOrchestrator:

    def __init__(self, investigator: ExceptionInvestigator):
        self.investigator = investigator

    def process(
        self,
        result: ReconciliationResult,
    ) -> InvestigationCase | None:

        # Only exceptions should be sent to the investigator.
        if result.status != "EXCEPTION":
            return None

        if not result.exception_type:
            return None

        return self.investigator.investigate(
            booking_id=result.booking_id,
            exception_type=result.exception_type,
            expected_amount=result.expected_amount,
            actual_amount=result.actual_amount,
            variance=result.variance,
        )