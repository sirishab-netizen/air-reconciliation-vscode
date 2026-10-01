import pandas as pd
from time import perf_counter


class ReconciliationTools:
    def __init__(
        self,
        bookings,
        tickets,
        invoices,
        settlements,
        refunds,
        exchanges,
        trace=None,
    ):
        self.bookings = bookings
        self.tickets = tickets
        self.invoices = invoices
        self.settlements = settlements
        self.refunds = refunds
        self.exchanges = exchanges
        self.trace = trace

    def _record_tool_call(
        self,
        tool_name: str,
        booking_id: str,
        duration_ms: float,
    ):
        if self.trace:
            self.trace.add(
                "TOOL",
                f"{tool_name}({booking_id})",
                duration_ms=duration_ms,
            )

    def get_booking(self, booking_id: str) -> dict:
        start = perf_counter()

        rows = self.bookings[
            self.bookings["booking_id"] == booking_id
        ]

        duration_ms = (perf_counter() - start) * 1000

        self._record_tool_call(
            "get_booking",
            booking_id,
            duration_ms,
        )

        if rows.empty:
            return {}

        return rows.iloc[0].to_dict()

    def get_ticket(self, booking_id: str) -> list[dict]:
        start = perf_counter()

        rows = self.tickets[
            self.tickets["booking_id"] == booking_id
        ]

        duration_ms = (perf_counter() - start) * 1000

        self._record_tool_call(
            "get_ticket",
            booking_id,
            duration_ms,
        )

        return rows.to_dict("records")

    def get_invoice(self, booking_id: str) -> list[dict]:
        start = perf_counter()

        rows = self.invoices[
            self.invoices["booking_id"] == booking_id
        ]

        duration_ms = (perf_counter() - start) * 1000

        self._record_tool_call(
            "get_invoice",
            booking_id,
            duration_ms,
        )

        return rows.to_dict("records")

    def get_settlement(self, booking_id: str) -> list[dict]:
        start = perf_counter()

        rows = self.settlements[
            self.settlements["booking_id"] == booking_id
        ]

        duration_ms = (perf_counter() - start) * 1000

        self._record_tool_call(
            "get_settlement",
            booking_id,
            duration_ms,
        )

        return rows.to_dict("records")

    def get_refund(self, booking_id: str) -> list[dict]:
        start = perf_counter()

        rows = self.refunds[
            self.refunds["booking_id"] == booking_id
        ]

        duration_ms = (perf_counter() - start) * 1000

        self._record_tool_call(
            "get_refund",
            booking_id,
            duration_ms,
        )

        return rows.to_dict("records")

    def get_exchange(self, booking_id: str) -> list[dict]:
        start = perf_counter()

        rows = self.exchanges[
            self.exchanges["booking_id"] == booking_id
        ]

        duration_ms = (perf_counter() - start) * 1000

        self._record_tool_call(
            "get_exchange",
            booking_id,
            duration_ms,
        )

        return rows.to_dict("records")

    def get_tool_definitions(self):
        return [
            {
                "type": "function",
                "name": "get_booking",
                "description": (
                    "Retrieve the booking record for a booking ID. "
                    "Read-only."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "The booking ID.",
                        }
                    },
                    "required": ["booking_id"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
            {
                "type": "function",
                "name": "get_ticket",
                "description": (
                    "Retrieve ticket records for a booking ID. "
                    "Read-only."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "The booking ID.",
                        }
                    },
                    "required": ["booking_id"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
            {
                "type": "function",
                "name": "get_invoice",
                "description": (
                    "Retrieve invoice records for a booking ID. "
                    "Read-only."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "The booking ID.",
                        }
                    },
                    "required": ["booking_id"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
            {
                "type": "function",
                "name": "get_settlement",
                "description": (
                    "Retrieve settlement records for a booking ID. "
                    "Read-only."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "The booking ID.",
                        }
                    },
                    "required": ["booking_id"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
            {
                "type": "function",
                "name": "get_refund",
                "description": (
                    "Retrieve refund records for a booking ID. "
                    "Read-only."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "The booking ID.",
                        }
                    },
                    "required": ["booking_id"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
            {
                "type": "function",
                "name": "get_exchange",
                "description": (
                    "Retrieve exchange records for a booking ID. "
                    "Read-only."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "The booking ID.",
                        }
                    },
                    "required": ["booking_id"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        ]