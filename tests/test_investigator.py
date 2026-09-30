import pandas as pd

from reconciliation.agent.tools import ReconciliationTools
from reconciliation.agent.investigator import ExceptionInvestigator
from reconciliation.engine import reconcile_booking
from reconciliation.agent.orchestrator import ExceptionOrchestrator


def test_reconciliation_to_investigation():

    bookings = pd.read_csv("data/air_bookings.csv")
    tickets = pd.read_csv("data/air_tickets.csv")
    invoices = pd.read_csv("data/air_invoices.csv")
    settlements = pd.read_csv("data/air_settlements.csv")
    refunds = pd.read_csv("data/air_refunds.csv")
    exchanges = pd.read_csv("data/air_exchanges.csv")

    tools = ReconciliationTools(
        bookings,
        tickets,
        invoices,
        settlements,
        refunds,
        exchanges,
    )

    investigator = ExceptionInvestigator(tools)

    orchestrator = ExceptionOrchestrator(investigator)

    result = reconcile_booking(
        "BKG006",
        bookings,
        tickets,
        invoices,
        settlements,
        refunds,
        exchanges,
    )

    assert result.status == "EXCEPTION"

    assert result.exception_type == "PARTIAL_REFUND_MISMATCH"

    case = orchestrator.process(result)

    assert case is not None

    assert case.booking_id == "BKG006"

    assert case.exception_type == "PARTIAL_REFUND_MISMATCH"

    assert case.status == "INVESTIGATED"