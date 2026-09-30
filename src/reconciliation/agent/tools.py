import pandas as pd


class ReconciliationTools:

    def __init__(
        self,
        bookings: pd.DataFrame,
        tickets: pd.DataFrame,
        invoices: pd.DataFrame,
        settlements: pd.DataFrame,
        refunds: pd.DataFrame,
        exchanges: pd.DataFrame,
    ):
        self.bookings = bookings
        self.tickets = tickets
        self.invoices = invoices
        self.settlements = settlements
        self.refunds = refunds
        self.exchanges = exchanges

    def get_booking(self, booking_id: str) -> dict:
        rows = self.bookings[
            self.bookings["booking_id"] == booking_id
        ]

        if rows.empty:
            return {}

        return rows.iloc[0].to_dict()

    def get_ticket(self, booking_id: str) -> list[dict]:
        rows = self.tickets[
            self.tickets["booking_id"] == booking_id
        ]

        return rows.to_dict("records")

    def get_invoice(self, booking_id: str) -> list[dict]:
        rows = self.invoices[
            self.invoices["booking_id"] == booking_id
        ]

        return rows.to_dict("records")

    def get_settlement(self, booking_id: str) -> list[dict]:
        rows = self.settlements[
            self.settlements["booking_id"] == booking_id
        ]

        return rows.to_dict("records")

    def get_refund(self, booking_id: str) -> list[dict]:
        rows = self.refunds[
            self.refunds["booking_id"] == booking_id
        ]

        return rows.to_dict("records")

    def get_exchange(self, booking_id: str) -> list[dict]:
        rows = self.exchanges[
            self.exchanges["booking_id"] == booking_id
        ]

        return rows.to_dict("records")