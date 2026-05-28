# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Models for hotel_partner_api."""

from decimal import Decimal
from enum import Enum
from typing import ClassVar, List, Optional

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


class EscalationReason(str, Enum):
    """Escalation reason values."""

    SAME_DAY_MODIFICATION = "same-day-modification"
    HOTEL_CONFIRMATION_REQUIRED = "hotel-confirmation-required"
    LARGE_GROUP_BOOKING = "large-group-booking"
    SYSTEM_ERROR = "system-error"
    HIGH_VALUE_DISPUTE = "high-value-dispute"
    GUEST_COMPLAINT = "guest-complaint"


class HotelData(BaseModel):
    """Hotel data output model."""

    id: str
    hotel_id: str
    hotel_name: str
    location: str
    partner_tier: str
    contact_name: str
    contact_email: str
    contact_phone: str
    escalation_contact: Optional[str]
    amenities: List[str]
    supports_pets: bool
    accessible_rooms_available: bool
    created_at: str
    updated_at: str

    def get_id(self) -> str:
        return self.id


# Database models
class Hotel(BaseModel):
    """Hotel record model."""

    table_name: ClassVar[str] = "hotels"

    id: str = Field(..., description="Unique identifier (HTL-########)")
    hotel_id: str = Field(..., description="Hotel identifier")
    hotel_name: str = Field(..., description="Hotel name")
    location: str = Field(..., description="Hotel location/city")
    partner_tier: HotelPartnerTier = Field(..., description="Partner tier level")
    contact_name: str = Field(..., description="Primary contact name")
    contact_email: str = Field(..., description="Primary contact email")
    contact_phone: str = Field(..., description="Primary contact phone")
    escalation_contact: Optional[str] = Field(
        None, description="Escalation contact for urgent issues"
    )
    amenities: List[str] = Field(default_factory=list, description="Hotel amenities")
    supports_pets: bool = Field(default=False, description="Whether hotel allows pets")
    accessible_rooms_available: bool = Field(
        default=False, description="Whether accessible rooms are available"
    )
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    def get_id(self) -> str:
        """Return the unique identifier for this hotel."""
        return self.id


__all__ = [
    "BookingStatus",
    "RoomType",
    "BoardType",
    "HotelPartnerTier",
    "EscalationReason",
    "Hotel",
    "HotelData",
]
