# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Common data models for external booking system."""

from decimal import Decimal
from enum import Enum
from typing import Annotated, ClassVar, List, Optional

from sandbox_servers.utils.sandbox_tools_system import UnstableField
from pydantic import BaseModel, Field


# Enums from database schema
class BookingStatus(str, Enum):
    """Booking status values."""

    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"


class RoomType(str, Enum):
    """Room type values."""

    STANDARD_ROOM = "standard_room"
    DELUXE_ROOM = "deluxe_room"
    SUITE = "suite"
    EXECUTIVE_SUITE = "executive_suite"
    PRESIDENTIAL_SUITE = "presidential_suite"
    FAMILY_ROOM = "family_room"
    ACCESSIBLE_ROOM = "accessible_room"


class BoardType(str, Enum):
    """Board type (meal plan) values."""

    WITHOUT_BREAKFAST = "without_breakfast"
    WITH_BREAKFAST = "with_breakfast"
    HALF_BOARD = "half_board"
    FULL_BOARD = "full_board"
    ALL_INCLUSIVE = "all_inclusive"


class HotelPartnerTier(str, Enum):
    """Hotel partner tier values."""

    PREMIUM = "premium"
    STANDARD = "standard"
    BUDGET = "budget"


# Database models
class Booking(BaseModel):
    """Booking record model."""

    table_name: ClassVar[str] = "bookings"

    id: str = Field(..., description="Unique identifier (BKG-########)")
    booking_reference: str = Field(..., description="Booking reference number")
    customer_id: str = Field(..., description="Customer identifier")
    hotel_id: str = Field(..., description="Hotel identifier")
    check_in_date: str = Field(..., description="Check-in date (ISO 8601)")
    check_out_date: str = Field(..., description="Check-out date (ISO 8601)")
    booking_value: Decimal = Field(..., description="Total booking value")
    room_type: RoomType = Field(..., description="Type of room booked")
    board_type: BoardType = Field(..., description="Board/meal plan type")
    adults_count: int = Field(..., description="Number of adults")
    children_count: int = Field(default=0, description="Number of children")
    booking_status: BookingStatus = Field(
        default=BookingStatus.CONFIRMED, description="Current booking status"
    )
    corporate_account_id: Optional[str] = Field(
        None, description="Corporate account ID if applicable"
    )
    group_booking_id: Optional[str] = Field(
        None, description="Group booking ID if part of a group"
    )
    modification_history: List[str] = Field(
        default_factory=list, description="History of modifications"
    )
    special_requests: Annotated[List[str], UnstableField()] = Field(
        default_factory=list,
        description="Special requests (excluded from test case validation)",
    )
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    def get_id(self) -> str:
        """Return the unique identifier for this booking."""
        return self.id


class GroupBooking(BaseModel):
    """Group booking record model."""

    table_name: ClassVar[str] = "group_bookings"

    id: str = Field(..., description="Unique identifier (GRP-########)")
    group_booking_id: str = Field(..., description="Group booking identifier")
    coordinator_name: str = Field(..., description="Group coordinator name")
    coordinator_email: str = Field(..., description="Group coordinator email")
    coordinator_phone: str = Field(..., description="Group coordinator phone")
    total_rooms: int = Field(..., description="Total number of rooms in group")
    check_in_date: str = Field(..., description="Check-in date for group")
    check_out_date: str = Field(..., description="Check-out date for group")
    hotel_id: str = Field(..., description="Hotel identifier")
    booking_references: List[str] = Field(
        ..., description="Array of individual booking references"
    )
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    def get_id(self) -> str:
        """Return the unique identifier for this group booking."""
        return self.id


class HotelInventory(BaseModel):
    """Hotel inventory record model."""

    table_name: ClassVar[str] = "hotel_inventory"

    id: str = Field(..., description="Unique identifier (INV-########)")
    hotel_id: str = Field(..., description="Hotel identifier")
    room_type: RoomType = Field(..., description="Type of room")
    board_type: BoardType = Field(..., description="Board/meal plan type")
    date: str = Field(..., description="Date for this inventory record")
    available_count: int = Field(..., description="Number of available rooms")
    price_per_night: Decimal = Field(..., description="Price per night")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    def get_id(self) -> str:
        """Return the unique identifier for this inventory record."""
        return self.id


__all__ = [
    "BookingStatus",
    "RoomType",
    "BoardType",
    "HotelPartnerTier",
    "Booking",
    "GroupBooking",
    "HotelInventory",
]
