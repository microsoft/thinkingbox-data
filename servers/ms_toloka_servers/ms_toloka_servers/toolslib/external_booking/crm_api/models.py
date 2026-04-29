# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, ClassVar, List, Optional

from ms_toloka_servers.utils.sandbox_tools_system import UnstableField
from pydantic import BaseModel, Field


class VipTier(str, Enum):
    """Customer VIP tier classification."""

    STANDARD = "standard"
    VIP = "vip"
    PLATINUM = "platinum"


class CustomerProfile(BaseModel):
    """Customer profile record from Salesforce CRM."""

    table_name: ClassVar[str] = "customer_profiles"

    id: str = Field(
        ..., description="Unique internal identifier for this profile record."
    )
    customer_id: str = Field(
        ..., description="Customer identifier in CUS-######## format."
    )
    email: str = Field(..., description="Primary email address of the customer.")
    full_name: str = Field(..., description="Full name of the customer.")

    vip_tier: VipTier = Field(
        VipTier.STANDARD,
        description="VIP tier classification: standard, vip, or platinum.",
    )

    loyalty_program_status: Optional[str] = Field(
        None, description="Loyalty program enrollment and status details."
    )

    lifetime_value: Decimal = Field(
        0, description="Total lifetime spending value associated with the customer."
    )

    total_bookings_count: int = Field(
        0,
        description="Total number of completed bookings associated with the customer.",
    )

    preferences: Annotated[List[str], UnstableField()] = Field(
        default_factory=list,
        description="List of customer preferences used for personalization (excluded from test case validation).",
    )

    special_notes: Annotated[List[str], UnstableField()] = Field(
        default_factory=list,
        description="List of customer-specific service notes and historical considerations (excluded from test case validation).",
    )

    complaint_count: int = Field(
        0, description="Count of past complaints used for service recovery tracking."
    )

    last_booking_date: Optional[datetime] = Field(
        None, description="Timestamp of the customer's most recent booking."
    )

    created_at: datetime = Field(
        ..., description="Timestamp when the profile was created."
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the profile was last updated."
    )

    def get_id(self) -> str:
        """Return unique identifier for database operations."""
        return self.id
