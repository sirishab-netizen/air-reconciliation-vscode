from pathlib import Path

import pandas as pd

from reconciliation.engine import reconcile_booking
from reconciliation.agent.investigator import ExceptionInvestigator
from reconciliation.agent.llm_reasoner import LLMReasoner
from reconciliation.agent.orchestrator import ExceptionOrchestrator
from reconciliation.agent.tools import ReconciliationTools


def load_data():
    data_dir = Path("data")

    return {
        "bookings": pd.read_csv(data_dir / "air_bookings.csv"),
        "tickets": pd.read_csv(data_dir / "air_tickets.csv"),
        "ticket_lines": pd.read_csv(data_dir / "air_ticket_lines.csv"),
        "invoices": pd.read_csv(data_dir / "air_invoices.csv"),
        "settlements": pd.read_csv(data_dir / "air_settlements.csv"),
        "refunds": pd.read_csv(data_dir / "air_refunds.csv"),
        "exchanges": pd.read_csv(data_dir / "air_exchanges.csv"),
        "fx_rates": pd.read_csv(data_dir / "fx_rates.csv"),
    }


def main():

    print("=" * 60)
    print("AGENTIC RECONCILIATION INVESTIGATION")
    print("=" * 60)

    data = load_data()

    booking_id = "BKG006"

    # ---------------------------------------------------------
    # 1. Deterministic reconciliation
    # ---------------------------------------------------------

    result = reconcile_booking(
        booking_id=booking_id,
        bookings=data["bookings"],
        tickets=data["tickets"],
        invoices=data["invoices"],
        settlements=data["settlements"],
        refunds=data["refunds"],
        exchanges=data["exchanges"],
        fx_rates=data["fx_rates"],
    )

    print("\nDETERMINISTIC RESULT")
    print("-" * 60)

    print(f"Booking:   {result.booking_id}")
    print(f"Status:    {result.status}")
    print(f"Exception: {result.exception_type}")

    if result.expected_amount is not None:
        print(f"Expected:  ${result.expected_amount}")

    if result.actual_amount is not None:
        print(f"Actual:    ${result.actual_amount}")

    if result.variance is not None:
        print(f"Variance:  ${result.variance}")

    # ---------------------------------------------------------
    # 2. Build investigation tools
    # ---------------------------------------------------------

    tools = ReconciliationTools(
        bookings=data["bookings"],
        tickets=data["tickets"],
        invoices=data["invoices"],
        settlements=data["settlements"],
        refunds=data["refunds"],
        exchanges=data["exchanges"],
    )

    # ---------------------------------------------------------
    # 3. Create investigation components
    # ---------------------------------------------------------

    investigator = ExceptionInvestigator(tools)

    reasoner = LLMReasoner(
        tools=tools
    )

    orchestrator = ExceptionOrchestrator(
        investigator=investigator,
        reasoner=reasoner,
    )

    # ---------------------------------------------------------
    # 4. Run agentic investigation
    # ---------------------------------------------------------

    case = orchestrator.process(result)

    if case is None:
        print("\nNo investigation required.")
        return

    # ---------------------------------------------------------
    # 5. Display investigation
    # ---------------------------------------------------------

    print("\nAGENT INVESTIGATION")
    print("-" * 60)

    print("Status:")
    print(f"  {case.status}")

    print("\nDeterministic Findings:")

    for finding in case.findings:
        print(f"  ✓ {finding}")

    print("\nHypothesis:")
    print(f"  {case.hypothesis}")

    print("\nConfidence:")
    print(f"  {case.confidence}")

    print("\nRecommendation:")
    print(f"  {case.recommendation}")

    print("\nHuman Approval Required:")
    print(f"  {'YES' if case.requires_human_approval else 'NO'}")

    print("\n" + "=" * 60)
    print("INVESTIGATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()