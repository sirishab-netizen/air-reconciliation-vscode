from pathlib import Path

import pandas as pd

from .engine import reconcile_booking


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def main() -> None:
    bookings = pd.read_csv(DATA_DIR / "air_bookings.csv")
    tickets = pd.read_csv(DATA_DIR / "air_tickets.csv")
    invoices = pd.read_csv(DATA_DIR / "air_invoices.csv")
    settlements = pd.read_csv(DATA_DIR / "air_settlements.csv")
    refunds = pd.read_csv(DATA_DIR / "air_refunds.csv")
    exchanges = pd.read_csv(DATA_DIR / "air_exchanges.csv")
    fx_rates = pd.read_csv(DATA_DIR / "fx_rates.csv")

    booking_ids = bookings["booking_id"].tolist()

    print("\nAIR RECONCILIATION RESULTS")
    print("=" * 80)

    for booking_id in booking_ids:

        result = reconcile_booking(
            booking_id,
            bookings,
            tickets,
            invoices,
            settlements,
            refunds,
            exchanges,
            fx_rates,
        )

        print(f"\nBooking: {result.booking_id}")
        print(f"Status: {result.status}")
        print(f"Exception: {result.exception_type}")
        print(f"Expected: {result.expected_amount}")
        print(f"Actual: {result.actual_amount}")
        print(f"Variance: {result.variance}")
        print(f"Message: {result.message}")

        if result.evidence:
            print("Evidence:")
            for item in result.evidence:
                print(f"  - {item}")


if __name__ == "__main__":
    main()