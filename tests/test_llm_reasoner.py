from pathlib import Path
from unittest import result

import pandas as pd

from reconciliation.agent.llm_reasoner import LLMReasoner
from reconciliation.agent.tools import ReconciliationTools


def load_data():
    data_dir = Path("data")

    return {
        "bookings": pd.read_csv(data_dir / "air_bookings.csv"),
        "tickets": pd.read_csv(data_dir / "air_tickets.csv"),
        "invoices": pd.read_csv(data_dir / "air_invoices.csv"),
        "settlements": pd.read_csv(data_dir / "air_settlements.csv"),
        "refunds": pd.read_csv(data_dir / "air_refunds.csv"),
        "exchanges": pd.read_csv(data_dir / "air_exchanges.csv"),
    }


def test_llm_reasoner():

    data = load_data()

    tools = ReconciliationTools(
        bookings=data["bookings"],
        tickets=data["tickets"],
        invoices=data["invoices"],
        settlements=data["settlements"],
        refunds=data["refunds"],
        exchanges=data["exchanges"],
    )

    reasoner = LLMReasoner(tools=tools)

    evidence = {
        "booking_id": "BKG006",
        "exception_type": "PARTIAL_REFUND_MISMATCH",
        "expected_amount": "200.00",
        "actual_amount": "180.00",
        "variance": "-20.00",
    }

    result = reasoner.reason(
        exception_type="PARTIAL_REFUND_MISMATCH",
        evidence=evidence,
    )

    assert result.findings
    assert result.hypothesis
    assert result.finding_confidence in {"HIGH", "MEDIUM", "LOW"}
    assert result.root_cause_confidence in {"HIGH", "MEDIUM", "LOW"}
    assert result.recommendation
    assert result.requires_human_approval is True