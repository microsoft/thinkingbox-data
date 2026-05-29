# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Search hotels by location tool for Booking Management System.

Search for available hotels in a specific location.

Searches for hotels in a given location that have availability for specified dates, room type,
and guest configuration. Returns hotel details with availability information to present alternatives
when customers need to change hotels or find new accommodations.
"""

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

# Standard decimal precision for monetary amounts (2 decimal places)
TWO_PLACES = Decimal("0.01")
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ...hotel_partner_api.models import Hotel
from ..models import BoardType, HotelInventory, RoomType


class SearchHotelsByLocationInput(BaseModel):
    """Input model for search_hotels_by_location tool."""

    location: str = Field(
        ..., description="Location/city to search for hotels", examples=["New York"]
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


class HotelResult(BaseModel):
    """Hotel search result model."""

    model_config = ConfigDict(extra="forbid")

    hotel_id: str = Field(..., description="Hotel identifier")
    hotel_name: str = Field(..., description="Hotel name")
    location: str = Field(..., description="Hotel location")
    partner_tier: str = Field(..., description="Partner tier level")
    available_count: int = Field(
        ..., description="Number of available rooms for the date range"
    )
    price_per_night: Decimal = Field(..., description="Average price per night")


class SearchHotelsByLocationOutput(BaseModel):
    """Output model for search_hotels_by_location tool."""

    model_config = ConfigDict(extra="forbid")

    hotels: List[HotelResult] = Field(
        ..., description="Array of hotel records with availability data"
    )


class SearchHotelsByLocationTool(Tool):
    """Tool for searching available hotels in a specific location."""

    @property
    def name(self) -> str:
        return "search_hotels_by_location"

    @property
    def description(self) -> str:
        return (
            "Searches for hotels in a given location that have availability for specified dates, room type, "
            "and guest configuration. Returns hotel details with availability information to present alternatives "
            "when customers need to change hotels or find new accommodations."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return SearchHotelsByLocationInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return SearchHotelsByLocationOutput

    async def run(
        self, db: InMemoryDatabase, request: SearchHotelsByLocationInput
    ) -> SearchHotelsByLocationOutput:
        """Search for available hotels in the specified location."""

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

        # Get all hotels matching location (case-insensitive contains match)
        all_hotels = db.get_all(Hotel)
        matching_hotels = [
            hotel
            for hotel in all_hotels
            if request.location.lower() in hotel.location.lower()
        ]

        # Return empty result if no hotels found (not an error)
        if not matching_hotels:
            return SearchHotelsByLocationOutput(hotels=[])

        # Get all inventory
        all_inventory = db.get_all(HotelInventory)

        # Check availability for each hotel
        results = []
        for hotel in matching_hotels:
            # Get inventory for this hotel, room type, and board type
            hotel_inventory = [
                inv
                for inv in all_inventory
                if inv.hotel_id == hotel.hotel_id
                and inv.room_type == request.room_type
                and inv.board_type == request.board_type
            ]

            if not hotel_inventory:
                continue

            # Filter by date range
            date_specific_inventory = []
            for inv in hotel_inventory:
                inv_date = datetime.fromisoformat(inv.date.replace("Z", "+00:00"))
                if check_in_d <= inv_date.date() < check_out_d:
                    date_specific_inventory.append(inv)

            if not date_specific_inventory:
                continue

            # Calculate minimum available count across all dates
            min_available = min(inv.available_count for inv in date_specific_inventory)

            # Only include hotels with availability
            if min_available > 0:
                # Calculate average price per night
                avg_price = sum(
                    inv.price_per_night for inv in date_specific_inventory
                ) / len(date_specific_inventory)

                results.append(
                    HotelResult(
                        hotel_id=hotel.hotel_id,
                        hotel_name=hotel.hotel_name,
                        location=hotel.location,
                        partner_tier=hotel.partner_tier.value,
                        available_count=min_available,
                        price_per_night=avg_price.quantize(
                            TWO_PLACES, rounding=ROUND_HALF_UP
                        ),
                    )
                )

        # Return empty result if no availability (not an error)
        # This allows the client to handle "no availability" gracefully

        return SearchHotelsByLocationOutput(hotels=results)
