# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get booking history tool for Booking Management System.

Retrieve customer's complete booking history.

Fetches all past and current bookings for a specific customer, ordered by booking date.
Returns comprehensive booking details for each reservation to analyze customer patterns and history.
"""

from typing import List, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Booking


class GetBookingHistoryInput(BaseModel):
    """Input model for get_booking_history tool."""

    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )


class GetBookingHistoryOutput(BaseModel):
    """Output model for get_booking_history tool."""

    model_config = ConfigDict(extra="forbid")

    bookings: List[dict] = Field(
        ...,
        description="Array of booking records from bookings table, each containing full booking details",
    )


class GetBookingHistoryTool(Tool):
    """Tool for retrieving customer's complete booking history."""

    @property
    def name(self) -> str:
        return "get_booking_history"

    @property
    def description(self) -> str:
        return (
            "Fetches all past and current bookings for a specific customer, ordered by booking date. "
            "Returns comprehensive booking details for each reservation to analyze customer patterns and history."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetBookingHistoryInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetBookingHistoryOutput

    async def run(
        self, db: InMemoryDatabase, request: GetBookingHistoryInput
    ) -> GetBookingHistoryOutput:
        """Retrieve customer's complete booking history."""

        # Get all bookings for the customer
        all_bookings = db.get_all(Booking)
        customer_bookings = [
            booking
            for booking in all_bookings
            if booking.customer_id == request.customer_id
        ]

        # Return empty list if no bookings found (not an error)
        if not customer_bookings:
            return GetBookingHistoryOutput(bookings=[])

        # Sort by created_at descending (most recent first)
        customer_bookings.sort(key=lambda b: b.created_at, reverse=True)

        # Convert to list of dicts
        bookings_data = [booking.model_dump() for booking in customer_bookings]

        return GetBookingHistoryOutput(bookings=bookings_data)
