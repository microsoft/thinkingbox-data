# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Loop Returns (RMS) toolset."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RMAStatus(str, Enum):
    """RMA status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    SHIPPED_TO_WAREHOUSE = "shipped_to_warehouse"
    RECEIVED = "received"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class RMAReturnReason(str, Enum):
    """RMA return reason enumeration."""

    DEFECTIVE = "defective"
    WRONG_ITEM_RECEIVED = "wrong_item_received"
    CHANGED_MIND = "changed_mind"
    NOT_AS_EXPECTED = "not_as_expected"
    DAMAGED_IN_TRANSIT = "damaged_in_transit"


class RMARecord(BaseModel):
    """RMA record model from RMS."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique RMA identifier")
    order_id: str = Field(..., description="Associated order identifier")
    line_item_id: str = Field(..., description="Specific line item being returned")
    customer_id: str = Field(..., description="Customer identifier")
    return_reason: RMAReturnReason = Field(..., description="Reason for return")
    is_defective: bool = Field(
        ..., description="Whether return is for defect (affects fees)"
    )
    status: RMAStatus = Field(
        default=RMAStatus.PENDING, description="Current RMA status"
    )
    created_date: datetime = Field(..., description="Date RMA was created")
    refund_amount: float = Field(
        ..., description="Calculated refund amount after all fees"
    )
    restocking_fee: float = Field(
        default=0.0,
        description="15% fee for non-defective opened items (standard customers only)",
    )
    return_shipping_cost: float = Field(
        default=0.0,
        description="$8.99 for non-defective small items (standard customers only)",
    )
    removal_fee: float = Field(
        default=0.0, description="$50 for non-defective installed major appliances"
    )

    def get_id(self) -> str:
        """Return the ID of this RMA record."""
        return self.id
