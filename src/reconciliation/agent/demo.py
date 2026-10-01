from asyncio import tools
from inspect import trace
from pathlib import Path

import pandas as pd

from reconciliation.engine import reconcile_booking
from reconciliation.agent.investigator import ExceptionInvestigator
from reconciliation.agent.llm_reasoner import LLMReasoner
from reconciliation.agent.orchestrator import ExceptionOrchestrator
from reconciliation.agent.tools import ReconciliationTools
from reconciliation.agent.trace import AgentTrace


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


def main():
    booking_id = "BKG012"

    data = load_data()

    # Deterministic reconciliation engine
    result = reconcile_booking(
        booking_id=booking_id,
        bookings=data["bookings"],
        tickets=data["tickets"],
        invoices=data["invoices"],
        settlements=data["settlements"],
        refunds=data["refunds"],
        exchanges=data["exchanges"],
    )

    print("\nDETERMINISTIC RESULT")
    print("-" * 60)
    print(f"Booking:    {result.booking_id}")
    print(f"Status:     {result.status}")
    print(f"Exception:  {result.exception_type}")
    print(f"Expected:   ${result.expected_amount}")
    print(f"Actual:     ${result.actual_amount}")
    print(f"Variance:   ${result.variance}")

    if result.status != "EXCEPTION":
        print("\nNo agent investigation required.")
        return

    # Read-only tools
    trace = AgentTrace()

    tools = ReconciliationTools(
        bookings=data["bookings"],
        tickets=data["tickets"],
        invoices=data["invoices"],
        settlements=data["settlements"],
        refunds=data["refunds"],
        exchanges=data["exchanges"],
        trace=trace,
    )

    # Deterministic investigator
    investigator = ExceptionInvestigator(tools)

    # LLM reasoner
    reasoner = LLMReasoner(
        tools=tools,
        trace=trace,
    )
    # Agent orchestrator
    orchestrator = ExceptionOrchestrator(
        investigator=investigator,
        reasoner=reasoner,
        trace=trace,
    )

    case = orchestrator.process(result)

    print("\nAGENT INVESTIGATION")
    print("-" * 60)
    print(f"Case status:              {case.status}")

    print("\nFindings:")
    for finding in case.findings:
        print(f"- {finding}")

    print(f"\nHypothesis:")
    print(case.hypothesis)

    print(f"\nFinding confidence:       {case.finding_confidence}")
    print(f"Root-cause confidence:    {case.root_cause_confidence}")

    print("\nRecommendation:")
    print(case.recommendation)

    print(
        f"\nHuman approval required:  "
        f"{'YES' if case.requires_human_approval else 'NO'}"
    )

    print("\nHUMAN APPROVAL")
    print("-" * 60)
    print(f"Current approval status: {case.approval_status}")

    # Simulate a human reviewer requesting additional evidence.
    case.request_more_evidence(
        requested_by="finance.reviewer",
        comment="Please validate the invoice records before approving."
    )

    print("\nHuman decision: REQUEST MORE EVIDENCE")
    print(f"Approval status: {case.approval_status}")
    print(f"Case status:     {case.status}")
    print(f"Reviewer:        {case.approved_by}")
    print(f"Comment:         {case.approval_comment}")

    # Simulate the human approving the recommendation after review.
    case.approve(
        approved_by="finance.reviewer",
        comment="Reviewed the investigation and supporting evidence."
    )

    print("\nHuman decision: APPROVE")
    print(f"Approval status: {case.approval_status}")
    print(f"Case status:     {case.status}")
    print(f"Reviewer:        {case.approved_by}")
    print(f"Comment:         {case.approval_comment}")

    trace.add(
        "HUMAN",
        f"Case approved by {case.approved_by}"
    )

    trace.print()

if __name__ == "__main__":
    main()