# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RoomType(str, Enum):
    standard_room = "standard_room"
    deluxe_room = "deluxe_room"
    suite = "suite"
    executive_suite = "executive_suite"
    presidential_suite = "presidential_suite"
    family_room = "family_room"
    accessible_room = "accessible_room"


class BoardType(str, Enum):
    without_breakfast = "without_breakfast"
    with_breakfast = "with_breakfast"
    half_board = "half_board"
    full_board = "full_board"
    all_inclusive = "all_inclusive"


class BookingStatus(str, Enum):
    confirmed = "confirmed"
    cancelled = "cancelled"
    checked_in = "checked_in"
    checked_out = "checked_out"


class HotelPartnerTier(str, Enum):
    premium = "premium"
    standard = "standard"
    budget = "budget"


class CorporateAccountTier(str, Enum):
    enterprise = "enterprise"
    mid_market = "mid_market"
    small_business = "small_business"


class AccountStatus(str, Enum):
    active = "active"
    expired = "expired"
    pending = "pending"


class Booking(BaseModel):
    """Booking record from Booking Management System."""

    table_name: str = "bookings"

    id: str = Field(..., description="Internal unique ID (BKG-########).")
    booking_reference: str = Field(
        ..., description="External booking reference (BKG-########)."
    )
    customer_id: str = Field(..., description="Customer ID (CUS-########).")
    hotel_id: str = Field(..., description="Hotel ID (HTL-########).")

    check_in_date: datetime = Field(..., description="Check-in date.")
    check_out_date: datetime = Field(..., description="Check-out date.")

    booking_value: Decimal = Field(..., description="Total booking cost.")
    room_type: RoomType = Field(..., description="Room type.")
    board_type: BoardType = Field(..., description="Board type (meal plan).")

    adults_count: int = Field(..., description="Number of adults.")
    children_count: int = Field(0, description="Number of children.")

    booking_status: BookingStatus = Field(
        BookingStatus.confirmed, description="Current status of booking."
    )

    corporate_account_id: Optional[str] = Field(
        None, description="Corporate account ID if booking belongs to corporate client."
    )

    group_booking_id: Optional[str] = Field(
        None, description="Group booking ID if booking is part of a group."
    )

    modification_history: List[str] = Field(
        default_factory=list, description="List of modification events."
    )

    special_requests: List[str] = Field(
        default_factory=list, description="List of customer special requests."
    )

    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last modification timestamp.")

    def get_id(self) -> str:
        """Return unique identifier for this booking."""
        return self.id


class Hotel(BaseModel):
    """Hotel record from Hotel Partner Portal."""

    table_name: str = "hotels"

    id: str = Field(..., description="Internal unique ID.")
    hotel_id: str = Field(..., description="Hotel ID (HTL-########).")
    hotel_name: str = Field(..., description="Hotel name.")
    location: str = Field(..., description="Geographical location (city).")

    partner_tier: HotelPartnerTier = Field(..., description="Hotel partner tier.")

    contact_name: str = Field(..., description="Primary contact name.")
    contact_email: str = Field(..., description="Primary contact email.")
    contact_phone: str = Field(..., description="Primary contact phone.")

    escalation_contact: Optional[str] = Field(
        None, description="Escalation contact email or phone."
    )

    amenities: List[str] = Field(
        default_factory=list, description="List of hotel amenities."
    )

    supports_pets: bool = Field(False, description="Hotel supports pets.")
    accessible_rooms_available: bool = Field(
        False, description="Accessible rooms available."
    )

    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last modification timestamp.")

    def get_id(self) -> str:
        """Return unique identifier for this hotel."""
        return self.id


class CorporateAccount(BaseModel):
    """Corporate account record."""

    table_name: str = "corporate_accounts"

    id: str = Field(..., description="Internal unique ID.")
    corporate_account_id: str = Field(
        ..., description="Corporate account ID (CRP-########)."
    )
    company_name: str = Field(..., description="Company name.")
    account_tier: CorporateAccountTier = Field(
        ..., description="Corporate account tier."
    )

    account_status: AccountStatus = Field(
        ..., description="Account status: active, expired, pending."
    )

    contact_name: str = Field(..., description="Main contact name.")
    contact_email: str = Field(..., description="Main contact email.")
    contact_phone: str = Field(..., description="Main contact phone.")

    booking_limit: int = Field(..., description="Maximum allowed number of bookings.")
    credit_limit: Decimal = Field(..., description="Credit limit amount.")
    payment_terms: str = Field(..., description="Payment terms description.")

    expiration_date: Optional[datetime] = Field(
        None, description="Expiration date if applicable."
    )

    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last modification timestamp.")

    def get_id(self) -> str:
        """Return unique identifier for this corporate account."""
        return self.id


class GroupBooking(BaseModel):
    """Group booking record from Booking Management System."""

    table_name: str = "group_bookings"

    id: str = Field(..., description="Internal unique ID.")
    group_booking_id: str = Field(..., description="Group booking ID (GRP-########).")

    coordinator_name: str = Field(..., description="Coordinator full name.")
    coordinator_email: str = Field(..., description="Coordinator email.")
    coordinator_phone: str = Field(..., description="Coordinator phone.")

    total_rooms: int = Field(..., description="Total number of rooms in group booking.")

    check_in_date: datetime = Field(..., description="Group check-in date.")
    check_out_date: datetime = Field(..., description="Group check-out date.")

    hotel_id: str = Field(..., description="Hotel ID (HTL-########).")

    booking_references: List[str] = Field(
        ..., description="List of booking references belonging to this group."
    )

    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last modification timestamp.")

    def get_id(self) -> str:
        """Return unique identifier for this group booking."""
        return self.id
