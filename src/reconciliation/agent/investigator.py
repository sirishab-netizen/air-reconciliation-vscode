from asyncio import tools
from decimal import Decimal

from .models import InvestigationCase
from .tools import ReconciliationTools
from reconciliation.agent import tools
from .llm_reasoner import LLMReasoner


class ExceptionInvestigator:

    def __init__(
            self,
            tools,
            reasoner=None,
        ):
            self.tools = tools
            self.reasoner = reasoner

    def investigate(
        self,
        booking_id: str,
        exception_type: str,
        expected_amount=None,
        actual_amount=None,
        variance=None,
    ) -> InvestigationCase:

        case = InvestigationCase(
            case_id=f"CASE-{booking_id}",
            booking_id=booking_id,
            exception_type=exception_type,
            expected_amount=(
                str(expected_amount)
                if expected_amount is not None
                else None
            ),
            actual_amount=(
                str(actual_amount)
                if actual_amount is not None
                else None
            ),
            variance=(
                str(variance)
                if variance is not None
                else None
            ),
        )

        case.investigation_steps.append(
            f"Started investigation for {booking_id}"
        )

        if exception_type == "PARTIAL_REFUND_MISMATCH":
            self._investigate_partial_refund(case)

        elif exception_type == "TAX_AMOUNT_MISMATCH":
            self._investigate_tax_mismatch(case)

        elif exception_type == "ANCILLARY_AMOUNT_MISMATCH":
            self._investigate_ancillary(case)

        elif exception_type == "EXCHANGE_AMOUNT_MISMATCH":
            self._investigate_exchange(case)

        elif exception_type == "CONFLICTING_RECORDS":
            self._investigate_conflict(case)

        else:
            case.findings.append(
                "No specialized investigation workflow exists "
                f"for {exception_type}"
            )

            case.hypothesis = (
                "Exception requires manual investigation."
            )

            case.confidence = "LOW"
            case.recommendation = "Route to human review."

        case.status = "INVESTIGATED"

        return case

    # ---------------------------------------------------------------
    # PARTIAL REFUND
    # ---------------------------------------------------------------

    def _investigate_partial_refund(
        self,
        case: InvestigationCase,
    ):

        booking = self.tools.get_booking(case.booking_id)
        ticket = self.tools.get_ticket(case.booking_id)
        refund = self.tools.get_refund(case.booking_id)
        invoice = self.tools.get_invoice(case.booking_id)

        case.investigation_steps.extend(
            [
                "Retrieved booking record",
                "Retrieved ticket records",
                "Retrieved refund records",
                "Retrieved invoice records",
            ]
        )

        if not booking:
            case.findings.append(
                "Booking record could not be found."
            )
            case.confidence = "LOW"
            case.hypothesis = "Insufficient evidence."
            case.recommendation = "Route to human review."
            return

        if not refund:
            case.findings.append(
                "Refund record could not be found."
            )
            case.confidence = "LOW"
            case.hypothesis = "Refund evidence is missing."
            case.recommendation = "Route to human review."
            return

        expected = sum(
            Decimal(str(r["expected_refund"]))
            for r in refund
        )

        actual = sum(
            Decimal(str(r["actual_refund"]))
            for r in refund
        )

        difference = actual - expected

        case.findings.append(
            f"Expected refund = ${expected:.2f}"
        )

        case.findings.append(
            f"Actual refund = ${actual:.2f}"
        )

        case.findings.append(
            f"Refund difference = ${difference:.2f}"
        )

        if invoice:
            invoice_total = sum(
                Decimal(str(r["amount"]))
                for r in invoice
            )

            case.findings.append(
                f"Invoice financial lines total = "
                f"${invoice_total:.2f}"
            )

        if ticket:
            ticket_total = sum(
                Decimal(str(r["ticket_total"]))
                for r in ticket
            )

            case.findings.append(
                f"Ticket total = ${ticket_total:.2f}"
            )

        case.hypothesis = (
            f"The refund is ${abs(difference):.2f} lower "
            "than the expected refund. The available records "
            "confirm the variance but do not independently "
            "establish its business reason."
        )

        case.confidence = "MEDIUM"

        case.recommendation = (
            "Route the refund discrepancy to human review "
            "before making any financial adjustment."
        )

        case.requires_human_approval = True

    # ---------------------------------------------------------------
    # TAX MISMATCH
    # ---------------------------------------------------------------

    def _investigate_tax_mismatch(
        self,
        case: InvestigationCase,
    ):

        booking = self.tools.get_booking(case.booking_id)
        invoice = self.tools.get_invoice(case.booking_id)
        ticket = self.tools.get_ticket(case.booking_id)

        case.investigation_steps.extend(
            [
                "Retrieved booking record",
                "Retrieved ticket records",
                "Retrieved invoice records",
            ]
        )

        booking_tax = Decimal(
            str(booking["taxes"])
        ) if booking else Decimal("0")

        invoice_tax = sum(
            Decimal(str(row["amount"]))
            for row in invoice
            if str(row["line_type"]).upper() == "TAX"
        )

        ticket_tax = sum(
            Decimal(str(row["tax_amount"]))
            for row in ticket
        )

        case.findings.extend(
            [
                f"Booking tax = ${booking_tax:.2f}",
                f"Ticket tax = ${ticket_tax:.2f}",
                f"Invoice tax = ${invoice_tax:.2f}",
            ]
        )

        case.hypothesis = (
            "Invoice tax differs from the booking/ticket tax "
            "and requires component-level investigation."
        )

        case.confidence = "HIGH"

        case.recommendation = (
            "Review invoice tax components and route for "
            "human approval before any financial adjustment."
        )

        case.requires_human_approval = True

    # ---------------------------------------------------------------
    # ANCILLARY
    # ---------------------------------------------------------------

    def _investigate_ancillary(
        self,
        case: InvestigationCase,
    ):

        invoice = self.tools.get_invoice(case.booking_id)
        ticket = self.tools.get_ticket(case.booking_id)

        case.investigation_steps.extend(
            [
                "Retrieved invoice records",
                "Retrieved ticket records",
            ]
        )

        invoice_ancillary = sum(
            Decimal(str(row["amount"]))
            for row in invoice
            if str(row["line_type"]).upper() == "ANCILLARY"
        )

        ticket_ancillary = sum(
            Decimal(str(row["ticket_total"]))
            for row in ticket
            if str(row["ticket_type"]).upper() == "ANCILLARY"
        )

        case.findings.extend(
            [
                f"Invoice ancillary amount = "
                f"${invoice_ancillary:.2f}",
                f"Ticket ancillary amount = "
                f"${ticket_ancillary:.2f}",
            ]
        )

        case.hypothesis = (
            "The ancillary financial representation differs "
            "between invoice and ticket records."
        )

        case.confidence = "HIGH"

        case.recommendation = (
            "Review ancillary transaction details and "
            "route for human approval."
        )

        case.requires_human_approval = True

    # ---------------------------------------------------------------
    # EXCHANGE
    # ---------------------------------------------------------------

    def _investigate_exchange(
        self,
        case: InvestigationCase,
    ):

        exchange = self.tools.get_exchange(case.booking_id)
        settlement = self.tools.get_settlement(case.booking_id)

        case.investigation_steps.extend(
            [
                "Retrieved exchange record",
                "Retrieved settlement records",
            ]
        )

        expected = sum(
            Decimal(str(row["expected_additional_collection"]))
            for row in exchange
        )

        actual = sum(
            Decimal(str(row["amount"]))
            for row in settlement
        )

        variance = actual - expected

        case.findings.extend(
            [
                f"Expected additional collection = "
                f"${expected:.2f}",
                f"Actual settlement = ${actual:.2f}",
                f"Variance = ${variance:.2f}",
            ]
        )

        case.hypothesis = (
            "Exchange settlement does not match the expected "
            "additional collection."
        )

        case.confidence = "HIGH"

        case.recommendation = (
            "Review exchange calculation and settlement "
            "before approving any adjustment."
        )

        case.requires_human_approval = True

    # ---------------------------------------------------------------
    # CONFLICTING RECORDS
    # ---------------------------------------------------------------

    def _investigate_conflict(
        self,
        case: InvestigationCase,
    ) -> InvestigationCase:
        booking = self.tools.get_booking(case.booking_id)
        tickets = self.tools.get_ticket(case.booking_id)
        invoices = self.tools.get_invoice(case.booking_id)
        settlements = self.tools.get_settlement(case.booking_id)

        case.investigation_steps.extend(
            [
                "Retrieved booking record",
                "Retrieved ticket records",
                "Retrieved invoice records",
                "Retrieved settlement records",
            ]
        )

        booking_total = (
            Decimal(str(booking["booking_total"]))
            if booking and booking.get("booking_total") is not None
            else None
        )
        ticket_total = (
            Decimal(str(tickets[0]["ticket_total"]))
            if tickets and tickets[0].get("ticket_total") is not None
            else None
        )
        settlement_total = (
            sum(
                (Decimal(str(row["amount"])) for row in settlements),
                Decimal("0.00"),
            )
            if settlements
            else None
        )

        invoice_totals: dict[str, Decimal] = {}
        for row in invoices:
            invoice_id = str(row.get("invoice_id", "UNKNOWN"))
            invoice_totals[invoice_id] = invoice_totals.get(
                invoice_id, Decimal("0.00")
            ) + Decimal(str(row.get("amount", 0) or 0))

        case.evidence.extend(
            [
                f"Booking total: {booking_total}",
                f"Ticket total: {ticket_total}",
                f"Invoice totals: {invoice_totals}",
                f"Settlement total: {settlement_total}",
            ]
        )

        if booking_total is not None:
            case.findings.append(f"Booking total is ${booking_total:.2f}.")
        if ticket_total is not None:
            case.findings.append(f"Ticket total is ${ticket_total:.2f}.")
        if settlement_total is not None:
            case.findings.append(
                f"Settlement total is ${settlement_total:.2f}."
            )
        for invoice_id, invoice_total in invoice_totals.items():
            case.findings.append(
                f"Invoice {invoice_id} component total is ${invoice_total:.2f}."
            )

        distinct_invoice_totals = set(invoice_totals.values())
        if len(distinct_invoice_totals) > 1:
            case.hypothesis = (
                "The booking has multiple invoices with different financial "
                "totals. The available evidence does not identify which "
                "invoice is authoritative."
            )
            case.finding_confidence = "HIGH"
        else:
            case.hypothesis = (
                "Conflicting financial records were identified, but the "
                "available evidence is insufficient to determine their source."
            )
            case.finding_confidence = "MEDIUM"

        case.root_cause_confidence = "LOW"
        case.recommendation = (
            "Verify the invoice records against the authoritative invoicing "
            "system and route for human review before any financial adjustment."
        )
        case.requires_human_approval = True

        return case