# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Verify availability directly with hotel partner system.

Performs real-time availability verification with hotel partner for critical modifications.
Used when standard inventory check needs hotel confirmation, typically for same-day changes
or high-value bookings.
"""

from typing import Optional, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ...booking_api.models import BoardType, HotelInventory, RoomType
from ..models import Hotel


class VerifyAvailabilityInput(BaseModel):
    """Input model for verify_availability tool."""

    hotel_id: str = Field(
        ..., description="Hotel identifier", examples=["HTL-00012345"]
    )
    check_in_date: str = Field(
        ..., description="Check-in date (ISO 8601)", examples=["2025-12-15T00:00:00Z"]
    )
    check_out_date: str = Field(
        ..., description="Check-out date (ISO 8601)", examples=["2025-12-20T00:00:00Z"]
    )
    room_type: RoomType = Field(..., description="Type of room", examples=["standard"])
    board_type: BoardType = Field(
        ..., description="Board/meal plan type", examples=["breakfast"]
    )
    adults_count: int = Field(..., description="Number of adults", examples=[2])
    children_count: int = Field(..., description="Number of children", examples=[0])


class VerifyAvailabilityOutput(BaseModel):
    """Output model for verify_availability tool."""

    availability_confirmed: bool = Field(
        ...,
        description="Hotel partner confirmation of availability for requested configuration",
    )
    confirmation_notes: Optional[str] = Field(
        None, description="Additional notes or conditions from hotel partner"
    )


class VerifyAvailability(Tool):
    """Verify availability directly with hotel partner system."""

    @property
    def name(self) -> str:
        return "verify_availability"

    @property
    def description(self) -> str:
        return "Verify availability directly with hotel partner system"

    @property
    def request_model(self) -> Type[BaseModel]:
        return VerifyAvailabilityInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return VerifyAvailabilityOutput

    async def run(
        self, db: InMemoryDatabase, request: VerifyAvailabilityInput
    ) -> VerifyAvailabilityOutput:
        """Execute the tool logic."""
        # Verify hotel exists
        all_hotels = db.get_all(Hotel)
        hotel = next((h for h in all_hotels if h.hotel_id == request.hotel_id), None)

        if not hotel:
            raise Tool.ExecutionError(f"Hotel not found: {request.hotel_id}")

        # Query hotel_inventory for availability
        all_inventory = db.get_all(HotelInventory)

        # Filter inventory for this hotel, room type, and board type
        # Check if we have availability for all dates in the range
        check_in = request.check_in_date.split("T")[0]  # Extract date part
        check_out = request.check_out_date.split("T")[0]

        # Find matching inventory records
        matching_inventory = [
            inv
            for inv in all_inventory
            if inv.hotel_id == request.hotel_id
            and inv.room_type == request.room_type
            and inv.board_type == request.board_type
            and check_in <= inv.date < check_out  # Date range check
        ]

        # If we have inventory records and they all have available rooms
        if matching_inventory:
            # Check if all dates have availability
            min_available = min(inv.available_count for inv in matching_inventory)
            availability_confirmed = min_available > 0

            if availability_confirmed:
                confirmation_notes = (
                    f"Confirmed availability for {len(matching_inventory)} nights. "
                    f"Minimum {min_available} rooms available."
                )
            else:
                confirmation_notes = "No availability for requested dates."
        else:
            # No inventory data - cannot confirm availability
            availability_confirmed = False
            confirmation_notes = (
                "No inventory data available for this hotel/room combination."
            )

        return VerifyAvailabilityOutput(
            availability_confirmed=availability_confirmed,
            confirmation_notes=confirmation_notes,
        )
