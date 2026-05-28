# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get group booking tool for Booking Management System.

Retrieve group booking details and associated room reservations.

Fetches comprehensive group booking information including coordinator details, total room count,
and all associated individual booking references. Used for managing multi-room bookings for events,
conferences, or group travel.
"""

from typing import Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import GroupBooking


class GetGroupBookingInput(BaseModel):
    """Input model for get_group_booking tool."""

    group_booking_id: str = Field(
        ..., description="Group booking identifier", examples=["GRP-00012345"]
    )


class GetGroupBookingOutput(BaseModel):
    """Output model for get_group_booking tool."""

    model_config = ConfigDict(extra="forbid")

    group_booking_data: dict = Field(
        ...,
        description="Complete group booking record from group_bookings table including all fields",
    )


class GetGroupBookingTool(Tool):
    """Tool for retrieving group booking details and associated room reservations."""

    @property
    def name(self) -> str:
        return "get_group_booking"

    @property
    def description(self) -> str:
        return (
            "Fetches comprehensive group booking information including coordinator details, total room count, "
            "and all associated individual booking references. Used for managing multi-room bookings for events, "
            "conferences, or group travel."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetGroupBookingInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetGroupBookingOutput

    async def run(
        self, db: InMemoryDatabase, request: GetGroupBookingInput
    ) -> GetGroupBookingOutput:
        """Retrieve group booking details."""

        # Get all group bookings
        all_group_bookings = db.get_all(GroupBooking)

        # Search by group_booking_id
        for group_booking in all_group_bookings:
            if group_booking.group_booking_id == request.group_booking_id:
                return GetGroupBookingOutput(
                    group_booking_data=group_booking.model_dump()
                )

        raise Tool.ExecutionError(
            f"Group booking not found with group_booking_id '{request.group_booking_id}'"
        )
