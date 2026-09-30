from decimal import Decimal
import pandas as pd

from .models import ReconciliationResult


TOLERANCE = Decimal("0.01")


def money(value) -> Decimal:
    """Convert a value into a 2-decimal Decimal."""
    if pd.isna(value):
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"))


def reconcile_booking(
    booking_id: str,
    bookings: pd.DataFrame,
    tickets: pd.DataFrame,
    invoices: pd.DataFrame,
    settlements: pd.DataFrame,
    refunds: pd.DataFrame,
    exchanges: pd.DataFrame,
    fx_rates: pd.DataFrame | None = None,
) -> ReconciliationResult:

    # ------------------------------------------------------------------
    # 1. LOAD BOOKING
    # ------------------------------------------------------------------
    booking_rows = bookings[bookings["booking_id"] == booking_id]

    if booking_rows.empty:
        return ReconciliationResult(
            booking_id=booking_id,
            status="EXCEPTION",
            exception_type="BOOKING_NOT_FOUND",
            message="Booking record was not found",
        )

    booking = booking_rows.iloc[0]

    transaction_type = str(booking["transaction_type"]).strip().upper()
    booking_currency = str(booking["currency"]).strip().upper()

    booking_total = money(booking["booking_total"])
    booking_tax = money(booking["taxes"])

    evidence = [
        f"booking_total:{booking_total}",
        f"booking_tax:{booking_tax}",
        f"transaction_type:{transaction_type}",
        f"currency:{booking_currency}",
    ]

    # ------------------------------------------------------------------
    # 2. GET RELATED RECORDS
    # ------------------------------------------------------------------
    tk = tickets[tickets["booking_id"] == booking_id].copy()
    inv = invoices[invoices["booking_id"] == booking_id].copy()
    st = settlements[settlements["booking_id"] == booking_id].copy()
    rf = refunds[refunds["booking_id"] == booking_id].copy()
    ex = exchanges[exchanges["booking_id"] == booking_id].copy()

    # ------------------------------------------------------------------
    # 3. MISSING TICKET
    # ------------------------------------------------------------------
    if tk.empty:
        return ReconciliationResult(
            booking_id=booking_id,
            status="EXCEPTION",
            exception_type="MISSING_TICKET",
            expected_amount=booking_total,
            actual_amount=None,
            variance=None,
            evidence=evidence,
            message="No ticket was found for the booking",
        )

    # ------------------------------------------------------------------
    # 4. VOID
    # ------------------------------------------------------------------
    if transaction_type == "VOID":
        if not st.empty:
            settlement_total = money(st["amount"].sum())

            return ReconciliationResult(
                booking_id=booking_id,
                status="EXCEPTION",
                exception_type="VOID_SETTLEMENT_EXCEPTION",
                expected_amount=Decimal("0.00"),
                actual_amount=settlement_total,
                variance=settlement_total,
                evidence=evidence
                + [f"settlement_total:{settlement_total}"],
                message="A settlement exists for a voided booking",
            )

        return ReconciliationResult(
            booking_id=booking_id,
            status="RECONCILED",
            expected_amount=Decimal("0.00"),
            actual_amount=Decimal("0.00"),
            variance=Decimal("0.00"),
            evidence=evidence,
            message="Void booking has no settlement",
        )

    # ------------------------------------------------------------------
    # 5. MISSING SETTLEMENT
    # ------------------------------------------------------------------
    if st.empty:
        return ReconciliationResult(
            booking_id=booking_id,
            status="PENDING",
            exception_type="MISSING_SETTLEMENT",
            expected_amount=booking_total,
            actual_amount=None,
            variance=None,
            evidence=evidence,
            message="Settlement has not yet been received",
        )

    # ------------------------------------------------------------------
    # 6. DUPLICATE SETTLEMENT
    # ------------------------------------------------------------------
    # Refunds, partial refunds and exchanges can legitimately have
    # multiple financial movements, so we don't treat them as duplicate
    # settlement scenarios here.
    if transaction_type not in {
        "REFUND",
        "PARTIAL_REFUND",
        "EXCHANGE",
    }:
        settlement_count = len(st)

        if settlement_count > 1:
            settlement_total = money(st["amount"].sum())

            return ReconciliationResult(
                booking_id=booking_id,
                status="EXCEPTION",
                exception_type="POSSIBLE_DUPLICATE_SETTLEMENT",
                expected_amount=booking_total,
                actual_amount=settlement_total,
                variance=settlement_total - booking_total,
                evidence=evidence
                + [
                    f"settlement_count:{settlement_count}",
                    f"settlement_total:{settlement_total}",
                ],
                message="Multiple settlement records were found",
            )

    # ------------------------------------------------------------------
    # 7. REFUND / PARTIAL REFUND
    # ------------------------------------------------------------------
    if transaction_type in {"REFUND", "PARTIAL_REFUND"}:
        if rf.empty:
            return ReconciliationResult(
                booking_id=booking_id,
                status="EXCEPTION",
                exception_type="MISSING_REFUND_RECORD",
                expected_amount=None,
                actual_amount=None,
                variance=None,
                evidence=evidence,
                message="Refund transaction has no refund record",
            )

        expected_refund = money(rf["expected_refund"].sum())
        actual_refund = money(rf["actual_refund"].sum())
        refund_variance = actual_refund - expected_refund

        evidence.extend(
            [
                f"expected_refund:{expected_refund}",
                f"actual_refund:{actual_refund}",
            ]
        )

        if abs(refund_variance) > TOLERANCE:
            return ReconciliationResult(
                booking_id=booking_id,
                status="EXCEPTION",
                exception_type="PARTIAL_REFUND_MISMATCH",
                expected_amount=expected_refund,
                actual_amount=actual_refund,
                variance=refund_variance,
                evidence=evidence,
                message="Expected refund does not match actual refund",
            )

        return ReconciliationResult(
            booking_id=booking_id,
            status="RECONCILED",
            expected_amount=expected_refund,
            actual_amount=actual_refund,
            variance=Decimal("0.00"),
            evidence=evidence,
            message="Refund reconciled successfully",
        )

    # ------------------------------------------------------------------
    # 8. EXCHANGE
    # ------------------------------------------------------------------
    if transaction_type == "EXCHANGE":
        if ex.empty:
            return ReconciliationResult(
                booking_id=booking_id,
                status="EXCEPTION",
                exception_type="MISSING_EXCHANGE_RECORD",
                expected_amount=None,
                actual_amount=None,
                variance=None,
                evidence=evidence,
                message="Exchange transaction has no exchange record",
            )

        expected_collection = money(
            ex["expected_additional_collection"].sum()
        )

        settlement_total = money(st["amount"].sum())
        exchange_variance = settlement_total - expected_collection

        evidence.extend(
            [
                f"expected_additional_collection:{expected_collection}",
                f"settlement_total:{settlement_total}",
            ]
        )

        if abs(exchange_variance) > TOLERANCE:
            return ReconciliationResult(
                booking_id=booking_id,
                status="EXCEPTION",
                exception_type="EXCHANGE_AMOUNT_MISMATCH",
                expected_amount=expected_collection,
                actual_amount=settlement_total,
                variance=exchange_variance,
                evidence=evidence,
                message="Exchange settlement does not match expected additional collection",
            )

        return ReconciliationResult(
            booking_id=booking_id,
            status="RECONCILED",
            expected_amount=expected_collection,
            actual_amount=settlement_total,
            variance=Decimal("0.00"),
            evidence=evidence,
            message="Exchange reconciled successfully",
        )

    # ------------------------------------------------------------------
    # 9. CONFLICTING RECORDS
    # ------------------------------------------------------------------
    # A booking can legitimately have several invoice rows because one
    # invoice is represented by multiple FARE/TAX/ANCILLARY lines.
    #
    # Therefore, we first look for multiple invoice IDs for the same
    # booking. If different invoices have different financial totals,
    # this is a source-record conflict rather than a simple tax mismatch.
    invoice_ids = (
        inv["invoice_id"]
        .dropna()
        .astype(str)
        .unique()
    )

    if len(invoice_ids) > 1:
        invoice_totals = (
            inv.groupby("invoice_id")["amount"]
            .sum()
            .apply(money)
        )

        if invoice_totals.nunique() > 1:
            return ReconciliationResult(
                booking_id=booking_id,
                status="EXCEPTION",
                exception_type="CONFLICTING_RECORDS",
                expected_amount=booking_total,
                actual_amount=None,
                variance=None,
                evidence=evidence
                + [
                    f"invoice_totals:{invoice_totals.to_dict()}",
                    f"invoice_count:{len(invoice_ids)}",
                ],
                message="Multiple invoices for the booking contain conflicting financial totals",
            )

    # ------------------------------------------------------------------
    # 10. TAX MISMATCH
    # ------------------------------------------------------------------
    invoice_tax_total = money(
        inv.loc[inv["line_type"].astype(str).str.upper() == "TAX", "amount"].sum()
    )

    tax_variance = invoice_tax_total - booking_tax

    evidence.extend(
        [
            f"invoice_tax_total:{invoice_tax_total}",
            f"tax_variance:{tax_variance}",
        ]
    )

    if abs(tax_variance) > TOLERANCE:
        return ReconciliationResult(
            booking_id=booking_id,
            status="EXCEPTION",
            exception_type="TAX_AMOUNT_MISMATCH",
            expected_amount=booking_tax,
            actual_amount=invoice_tax_total,
            variance=tax_variance,
            evidence=evidence,
            message="Invoice tax amount does not match booking tax amount",
        )

    # ------------------------------------------------------------------
    # 11. ANCILLARY MISMATCH
    # ------------------------------------------------------------------
    ancillary_invoice_total = money(
        inv.loc[
            inv["line_type"].astype(str).str.upper() == "ANCILLARY",
            "amount",
        ].sum()
    )

    ancillary_ticket_total = money(
        tk.loc[
            tk["ticket_type"].astype(str).str.upper() == "ANCILLARY",
            "ticket_total",
        ].sum()
    )

    if ancillary_invoice_total > Decimal("0.00"):
        ancillary_variance = (
            ancillary_invoice_total - ancillary_ticket_total
        )

        evidence.extend(
            [
                f"ancillary_invoice_total:{ancillary_invoice_total}",
                f"ancillary_ticket_total:{ancillary_ticket_total}",
            ]
        )

        if abs(ancillary_variance) > TOLERANCE:
            return ReconciliationResult(
                booking_id=booking_id,
                status="EXCEPTION",
                exception_type="ANCILLARY_AMOUNT_MISMATCH",
                expected_amount=ancillary_ticket_total,
                actual_amount=ancillary_invoice_total,
                variance=ancillary_variance,
                evidence=evidence,
                message="Ancillary amount does not match between invoice and ticket records",
            )

    # ------------------------------------------------------------------
    # 12. FX
    # ------------------------------------------------------------------
    if fx_rates is not None and not fx_rates.empty:
        ticket_ids = tk["ticket_id"].dropna().astype(str).unique()

        for ticket_id in ticket_ids:
            fx = fx_rates[
                fx_rates["ticket_id"].astype(str) == ticket_id
            ]

            if not fx.empty:
                evidence.append(
                    f"fx_rate_found_for_ticket:{ticket_id}"
                )

    # ------------------------------------------------------------------
    # 13. TICKET TOTAL
    # ------------------------------------------------------------------
    ticket_total = money(tk["ticket_total"].sum())

    ticket_variance = ticket_total - booking_total

    evidence.extend(
        [
            f"ticket_total:{ticket_total}",
            f"ticket_variance:{ticket_variance}",
        ]
    )

    if abs(ticket_variance) > TOLERANCE:
        return ReconciliationResult(
            booking_id=booking_id,
            status="EXCEPTION",
            exception_type="TICKET_AMOUNT_MISMATCH",
            expected_amount=booking_total,
            actual_amount=ticket_total,
            variance=ticket_variance,
            evidence=evidence,
            message="Ticket total does not match booking total",
        )

    # ------------------------------------------------------------------
    # 14. SETTLEMENT TOTAL
    # ------------------------------------------------------------------
    settlement_total = money(st["amount"].sum())

    settlement_variance = settlement_total - booking_total

    evidence.extend(
        [
            f"settlement_total:{settlement_total}",
            f"settlement_variance:{settlement_variance}",
        ]
    )

    if abs(settlement_variance) > TOLERANCE:
        return ReconciliationResult(
            booking_id=booking_id,
            status="EXCEPTION",
            exception_type="SETTLEMENT_AMOUNT_MISMATCH",
            expected_amount=booking_total,
            actual_amount=settlement_total,
            variance=settlement_variance,
            evidence=evidence,
            message="Settlement amount does not match booking total",
        )

    # ------------------------------------------------------------------
    # 15. FINAL RECONCILIATION
    # ------------------------------------------------------------------
    return ReconciliationResult(
        booking_id=booking_id,
        status="RECONCILED",
        expected_amount=booking_total,
        actual_amount=settlement_total,
        variance=Decimal("0.00"),
        evidence=evidence,
        message="Booking reconciled successfully",
    )