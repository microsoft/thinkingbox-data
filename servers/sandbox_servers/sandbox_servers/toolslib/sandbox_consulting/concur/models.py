# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for SAP Concur Travel & Expense toolset."""

from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field


class ExpenseCategory(str, Enum):
    """Expense category enumeration."""

    MEALS = "meals"
    HOTEL = "hotel"
    TRANSPORT = "transport"
    PARKING = "parking"
    CLIENT_ENTERTAINMENT = "client_entertainment"
    OTHER = "other"


class ReceiptStatus(str, Enum):
    """Receipt status enumeration."""

    ATTACHED = "attached"
    MISSING = "missing"
    ITEMIZED = "itemized"


class OverrideReason(str, Enum):
    """Override reason enumeration."""

    JUSTIFIED_EXCEPTION = "justified_exception"
    SYSTEM_ERROR = "system_error"
    RECEIPT_EXCEPTION = "receipt_exception"


class FlightClass(str, Enum):
    """Flight class enumeration."""

    ECONOMY = "economy"
    BUSINESS = "business"
    FIRST = "first"


class ExpenseReport(BaseModel):
    """Expense report model."""

    table_name: ClassVar[str] = "expense_reports"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(
        ..., description="Unique expense report identifier (e.g., EXP-0012345)"
    )
    employee_email: str = Field(..., description="Employee email address")
    amount: int = Field(..., description="Expense amount in dollars")
    category: ExpenseCategory = Field(..., description="Expense category")
    trip_location_city: Optional[str] = Field(None, description="Trip location city")
    trip_location_state: Optional[str] = Field(None, description="Trip location state")
    expense_date: datetime = Field(..., description="Expense date")
    receipt_status: ReceiptStatus = Field(..., description="Receipt status")
    rejection_reason: Optional[str] = Field(
        None, description="Rejection reason if rejected"
    )
    override_approved: bool = Field(
        False, description="Whether override was approved (default: false)"
    )
    override_approved_by: Optional[str] = Field(
        None, description="Email of person who approved override"
    )
    override_reason: Optional[OverrideReason] = Field(
        None, description="Reason for override approval"
    )

    def get_id(self) -> str:
        """Return the expense report ID."""
        return self.id


class TravelRequest(BaseModel):
    """Travel request model."""

    table_name: ClassVar[str] = "travel_requests"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(
        ..., description="Unique travel request identifier (e.g., TRV-1000001)"
    )
    employee_email: str = Field(..., description="Employee email address")
    destination: str = Field(..., description="Travel destination")
    departure_date: datetime = Field(..., description="Departure date")
    return_date: datetime = Field(..., description="Return date")
    flight_class: FlightClass = Field(
        FlightClass.ECONOMY, description="Flight class (default: economy)"
    )
    hotel_rate_per_night: Optional[int] = Field(
        None, description="Hotel rate per night in dollars"
    )

    def get_id(self) -> str:
        """Return the travel request ID."""
        return self.id
