# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get booking tool for Booking Management System.

Retrieve complete booking details by booking reference or customer identifier.

Fetches comprehensive booking information including dates, hotel details, room configuration,
guest counts, booking status, and modification history. Used as the first step in most
booking-related workflows to gather context before taking action.
"""

from typing import Optional, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Booking


class GetBookingInput(BaseModel):
    """Input model for get_booking tool."""

    booking_reference: Optional[str] = Field(
        None, description="Booking reference number", examples=["BKG-00012345"]
    )
    customer_id: Optional[str] = Field(
        None, description="Customer identifier", examples=["CUS-00012345"]
    )


class GetBookingOutput(BaseModel):
    """Output model for get_booking tool."""

    model_config = ConfigDict(extra="forbid")

    booking_data: dict = Field(
        ...,
        description="Complete booking record from bookings table including all fields",
    )


class GetBookingTool(Tool):
    """Tool for retrieving complete booking details by booking reference or customer identifier."""

    @property
    def name(self) -> str:
        return "get_booking"

    @property
    def description(self) -> str:
        return (
            "Fetches comprehensive booking information including dates, hotel details, room configuration, "
            "guest counts, booking status, and modification history. Used as the first step in most "
            "booking-related workflows to gather context before taking action."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetBookingInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetBookingOutput

    async def run(
        self, db: InMemoryDatabase, request: GetBookingInput
    ) -> GetBookingOutput:
        """Retrieve complete booking details."""

        # Validate that at least one identifier is provided
        if not request.booking_reference and not request.customer_id:
            raise Tool.ExecutionError(
                "Either booking_reference or customer_id must be provided"
            )

        # Get all bookings
        all_bookings = db.get_all(Booking)

        # Search by booking_reference if provided
        if request.booking_reference:
            for booking in all_bookings:
                if booking.booking_reference == request.booking_reference:
                    return GetBookingOutput(booking_data=booking.model_dump())
            raise Tool.ExecutionError(
                f"Booking not found with booking_reference '{request.booking_reference}'"
            )

        # Search by customer_id if provided (returns first match)
        if request.customer_id:
            for booking in all_bookings:
                if booking.customer_id == request.customer_id:
                    return GetBookingOutput(booking_data=booking.model_dump())
            raise Tool.ExecutionError(
                f"Booking not found with customer_id '{request.customer_id}'"
            )

        # Should never reach here due to validation above
        raise Tool.ExecutionError("Invalid request parameters")
