# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Optional, Type

from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ...booking_api.models import Booking, GroupBooking


class LookupGroupBookingIdInput(BaseModel):
    """Input for looking up group booking information."""

    booking_reference: Optional[str] = Field(
        None,
        description="Booking reference for lookup in BKG-######## format.",
        examples=["BKG-00012345"],
    )

    coordinator_email: Optional[str] = Field(
        None,
        description="Coordinator email for group booking lookup.",
        examples=["coordinator@company.com"],
    )


class LookupGroupBookingIdOutput(BaseModel):
    """Output for group booking lookup."""

    group_booking_id: Optional[str] = Field(
        None, description="Group booking ID if found."
    )

    total_rooms: Optional[int] = Field(
        None, description="Total number of rooms in group booking."
    )

    coordinator_contact: Optional[str] = Field(
        None, description="Coordinator name and email formatted as 'Name <email>'."
    )


class LookupGroupBookingIdTool(Tool):
    """Lookup group booking details via booking reference or coordinator email."""

    @property
    def name(self) -> str:
        return "lookup_group_booking_id"

    @property
    def summary(self) -> str:
        return "Look up group booking ID from booking reference or coordinator contact."

    @property
    def description(self) -> str:
        return (
            "Searches for group booking via individual booking reference or coordinator "
            "email. Returns group booking context for group-related policies."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return LookupGroupBookingIdInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return LookupGroupBookingIdOutput

    async def run(
        self, db: InMemoryDatabase, request: LookupGroupBookingIdInput
    ) -> LookupGroupBookingIdOutput:

        booking_reference = request.booking_reference
        coordinator_email = request.coordinator_email

        if not booking_reference and not coordinator_email:
            raise self.ExecutionError(
                "Invalid parameters: provide booking_reference or coordinator_email."
            )

        group_bookings = db.get_all(GroupBooking)
        bookings = db.get_all(Booking)

        found_group = None

        if booking_reference:
            booking = next(
                (b for b in bookings if b.booking_reference == booking_reference), None
            )

            if booking and booking.group_booking_id:
                found_group = next(
                    (
                        g
                        for g in group_bookings
                        if g.group_booking_id == booking.group_booking_id
                    ),
                    None,
                )

        if not found_group and coordinator_email:
            found_group = next(
                (
                    g
                    for g in group_bookings
                    if g.coordinator_email.lower() == coordinator_email.lower()
                ),
                None,
            )

        if not found_group:
            raise self.ExecutionError(
                "No group booking found matching criteria or booking is not part of a group."
            )

        coordinator_contact = (
            f"{found_group.coordinator_name} <{found_group.coordinator_email}>"
        )

        return LookupGroupBookingIdOutput(
            group_booking_id=found_group.group_booking_id,
            total_rooms=found_group.total_rooms,
            coordinator_contact=coordinator_contact,
        )
