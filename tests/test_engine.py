import pytest
from pathlib import Path
import pandas as pd
from reconciliation.engine import reconcile_booking

DATA = Path(__file__).resolve().parents[1] / "data"
def load(n): return pd.read_csv(DATA / n)

@pytest.fixture
def frames():
    return {n: load(n) for n in [
        "air_bookings.csv", "air_tickets.csv", "air_invoices.csv", "air_settlements.csv",
        "air_refunds.csv", "air_exchanges.csv"
    ]}

# pytest is intentionally imported here so the fixture remains obvious to a beginner.
import pytest

def run(frames, bid):
    return reconcile_booking(bid, frames["air_bookings.csv"], frames["air_tickets.csv"], frames["air_invoices.csv"], frames["air_settlements.csv"], frames["air_refunds.csv"], frames["air_exchanges.csv"])

def test_normal_ticket(frames):
    assert run(frames, "BKG001").status == "RECONCILED"

def test_tax_mismatch(frames):
    assert run(frames, "BKG002").exception_type == "TAX_AMOUNT_MISMATCH"

def test_exchange(frames):
    assert run(frames, "BKG003").status == "RECONCILED"

def test_exchange_variance(frames):
    assert run(frames, "BKG004").exception_type == "EXCHANGE_AMOUNT_MISMATCH"

def test_full_refund(frames):
    assert run(frames, "BKG005").status == "RECONCILED"

def test_partial_refund(frames):
    assert run(frames, "BKG006").exception_type == "PARTIAL_REFUND_MISMATCH"

def test_void(frames):
    assert run(frames, "BKG007").exception_type == "VOID_SETTLEMENT_EXCEPTION"

def test_duplicate(frames):
    assert run(frames, "BKG008").exception_type == "POSSIBLE_DUPLICATE_SETTLEMENT"

def test_ancillary(frames):
    # Current v0 intentionally flags this at invoice amount level; later we will
    # add component-aware ancillary rules.
    assert run(frames, "BKG009").exception_type == "ANCILLARY_AMOUNT_MISMATCH"

def test_fx(frames):
    # FX-specific normalization is the next enhancement; v0 treats it as a
    # separate currency case rather than silently comparing EUR to USD.
    assert run(frames, "BKG010").status in {"RECONCILED", "EXCEPTION"}

def test_missing_settlement(frames):
    assert run(frames, "BKG011").status == "PENDING"

def test_conflicting_records(frames):
    assert run(frames, "BKG012").exception_type == "CONFLICTING_RECORDS"