# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Check hotel availability tool for Booking Management System.

Check room availability for a specific hotel and date range.

Validates availability for specific hotel, dates, room type, and board type combination.
Returns available room count and supported board types for the requested configuration.
Essential for modification requests to verify feasibility before executing changes.
"""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
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

# Standard decimal precision for monetary amounts (2 decimal places)
TWO_PLACES = Decimal("0.01")
from ...hotel_partner_api.models import Hotel
from ..models import BoardType, HotelInventory, RoomType


class CheckHotelAvailabilityInput(BaseModel):
    """Input model for check_hotel_availability tool."""

    hotel_id: str = Field(
        ..., description="Hotel identifier", examples=["HTL-00012345"]
    )
    check_in_date: str = Field(
        ...,
        description="Check-in date (ISO 8601 format)",
        examples=["2025-12-15T15:00:00Z"],
    )
    check_out_date: str = Field(
        ...,
        description="Check-out date (ISO 8601 format)",
        examples=["2025-12-18T11:00:00Z"],
    )
    room_type: RoomType = Field(
        ..., description="Type of room requested", examples=["deluxe_room"]
    )
    board_type: BoardType = Field(
        ..., description="Board/meal plan type", examples=["with_breakfast"]
    )
    adults_count: int = Field(..., description="Number of adults", examples=[2])
    children_count: int = Field(..., description="Number of children", examples=[1])


class CheckHotelAvailabilityOutput(BaseModel):
    """Output model for check_hotel_availability tool."""

    model_config = ConfigDict(extra="forbid")

    available_count: int = Field(
        ...,
        description="Number of available rooms matching the criteria for the entire date range",
    )
    available_board_types: List[str] = Field(
        ...,
        description="Array of board type enums available for the requested room type during the date range",
    )
    price_per_night: Decimal = Field(
        ...,
        description="Price per night for the requested room_type and board_type combination at this hotel",
    )


class CheckHotelAvailabilityTool(Tool):
    """Tool for checking room availability for a specific hotel and date range."""

    @property
    def name(self) -> str:
        return "check_hotel_availability"

    @property
    def description(self) -> str:
        return (
            "Validates availability for specific hotel, dates, room type, and board type combination. "
            "Returns available room count and supported board types for the requested configuration. "
            "Essential for modification requests to verify feasibility before executing changes."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return CheckHotelAvailabilityInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CheckHotelAvailabilityOutput

    async def run(
        self, db: InMemoryDatabase, request: CheckHotelAvailabilityInput
    ) -> CheckHotelAvailabilityOutput:
        """Check hotel availability for the specified criteria."""

        # Verify hotel exists
        hotel = db.get_by_id(Hotel, request.hotel_id)
        if hotel is None:
            raise Tool.ExecutionError(
                f"Hotel not found with hotel_id '{request.hotel_id}'"
            )

        # Parse dates
        try:
            check_in = datetime.fromisoformat(
                request.check_in_date.replace("Z", "+00:00")
            )
            check_out = datetime.fromisoformat(
                request.check_out_date.replace("Z", "+00:00")
            )
        except ValueError as e:
            raise Tool.ExecutionError(f"Invalid date format: {str(e)}")

        # Compare on calendar dates to avoid off-by-one issues caused by differing check-in/check-out times
        check_in_d = check_in.date()
        check_out_d = check_out.date()

        if check_in_d >= check_out_d:
            raise Tool.ExecutionError("Check-in date must be before check-out date")

        # Get all inventory records for this hotel, room type, and date range
        all_inventory = db.get_all(HotelInventory)
        relevant_inventory = [
            inv
            for inv in all_inventory
            if inv.hotel_id == request.hotel_id and inv.room_type == request.room_type
        ]

        if not relevant_inventory:
            return CheckHotelAvailabilityOutput(
                available_count=0,
                available_board_types=[],
                price_per_night=Decimal("0.00"),
            )

        # Filter by date range and board type
        date_specific_inventory = []
        for inv in relevant_inventory:
            inv_date = datetime.fromisoformat(inv.date.replace("Z", "+00:00"))
            if (
                check_in_d <= inv_date.date() < check_out_d
                and inv.board_type == request.board_type
            ):
                date_specific_inventory.append(inv)

        # Calculate minimum available count across all dates in range
        if not date_specific_inventory:
            available_count = 0
            price_per_night = Decimal("0.00")
        else:
            available_count = min(
                inv.available_count for inv in date_specific_inventory
            )
            # Get price_per_night from the inventory (assume consistent pricing)
            price_per_night = date_specific_inventory[0].price_per_night.quantize(
                TWO_PLACES, rounding=ROUND_HALF_UP
            )

        # Get all available board types for this room type during the date range
        board_types_set = set()
        for inv in relevant_inventory:
            inv_date = datetime.fromisoformat(inv.date.replace("Z", "+00:00"))
            if check_in_d <= inv_date.date() < check_out_d and inv.available_count > 0:
                board_types_set.add(inv.board_type.value)

        available_board_types = sorted(list(board_types_set))

        return CheckHotelAvailabilityOutput(
            available_count=available_count,
            available_board_types=available_board_types,
            price_per_night=price_per_night,
        )
