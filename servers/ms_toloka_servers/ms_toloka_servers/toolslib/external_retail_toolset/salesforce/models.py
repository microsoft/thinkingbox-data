# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Salesforce Customer 360 (CDP) toolset."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomerTier(str, Enum):
    """Customer tier enumeration."""

    STANDARD = "standard"
    PLUS_MEMBER = "plus_member"
    VIP = "vip"


class BehavioralSegment(str, Enum):
    """Customer behavioral segment enumeration."""

    REGULAR = "regular"
    OPPORTUNIST = "opportunist"
    BONUS_HUNTER = "bonus_hunter"


class MembershipStatus(str, Enum):
    """Membership status enumeration."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PointsAdjustmentReason(str, Enum):
    """Points adjustment reason enumeration."""

    REFUND_RETURN = "refund_return"
    SERVICE_RECOVERY = "service_recovery"
    MANUAL_ADJUSTMENT = "manual_adjustment"


class CustomerProfile(BaseModel):
    """Customer profile model from CDP."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique customer identifier")
    email: str = Field(..., description="Customer email address")
    name: str = Field(..., description="Customer full name")
    phone: Optional[str] = Field(None, description="Customer phone number")
    registration_date: datetime = Field(..., description="Date customer registered")
    customer_tier: CustomerTier = Field(
        default=CustomerTier.STANDARD, description="Customer tier level"
    )
    lifetime_value: float = Field(default=0.0, description="Total lifetime value")
    total_orders: int = Field(default=0, description="Total number of orders")
    customer_score: int = Field(
        default=50,
        description="Internal customer score (0-100). Never disclose to customer",
    )
    behavioral_segment: BehavioralSegment = Field(
        default=BehavioralSegment.OPPORTUNIST,
        description="Behavioral segment. Never disclose to customer",
    )
    acquisition_source: Optional[str] = Field(
        None, description="How customer was acquired"
    )
    discount_usage_rate: float = Field(
        default=0.0, description="Rate of discount code usage"
    )

    def get_id(self) -> str:
        """Return the ID of this customer profile."""
        return self.id


class MembershipRecord(BaseModel):
    """Membership record model from CDP."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique membership identifier")
    customer_id: str = Field(..., description="Customer identifier")
    membership_type: str = Field(default="plus", description="Membership type")
    start_date: datetime = Field(..., description="Membership start date")
    end_date: datetime = Field(..., description="Membership end date")
    status: MembershipStatus = Field(
        default=MembershipStatus.ACTIVE, description="Membership status"
    )
    points_balance: int = Field(default=0, description="Current reward points balance")

    def get_id(self) -> str:
        """Return the ID of this membership record."""
        return self.id
