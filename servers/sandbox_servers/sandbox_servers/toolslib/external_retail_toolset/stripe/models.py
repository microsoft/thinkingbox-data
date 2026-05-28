# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Stripe payment toolset."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    AUTHORIZED = "authorized"
    DECLINED = "declined"
    PENDING_AUTHORIZATION = "pending_authorization"
    FAILED = "failed"


class RefundReason(str, Enum):
    """Refund reason enumeration."""

    RMA_PROCESSED = "rma_processed"
    DISCOUNT_CORRECTION = "discount_correction"
    LATE_DELIVERY_COMPENSATION = "late_delivery_compensation"
    PARTIAL_REFUND_MINOR_DEFECT = "partial_refund_minor_defect"
    SHIPPING_DOWNGRADE = "shipping_downgrade"
    ORDER_CANCELLED = "order_cancelled"


class ChargeReason(str, Enum):
    """Charge reason enumeration."""

    SHIPPING_UPGRADE = "shipping_upgrade"
    RESHIP_FEE = "reship_fee"
    INSTALLATION_CANCELLED_SHIPPING = "installation_cancelled_shipping"


class PaymentTransaction(BaseModel):
    """Payment transaction model from Stripe."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique transaction identifier")
    order_id: str = Field(..., description="Associated order identifier")
    customer_id: str = Field(..., description="Customer identifier")
    amount: float = Field(..., description="Transaction amount in dollars")
    status: PaymentStatus = Field(..., description="Current payment status")
    payment_method: str = Field(..., description="Payment method description")
    transaction_date: datetime = Field(..., description="Transaction timestamp")
    charge_reason: Optional[ChargeReason] = Field(
        None, description="Reason for additional charge (if applicable)"
    )

    def get_id(self) -> str:
        """Return the transaction ID."""
        return self.id


class Refund(BaseModel):
    """Refund record model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique refund identifier")
    transaction_id: str = Field(
        ..., description="Original payment transaction being refunded"
    )
    order_id: str = Field(..., description="Order identifier")
    amount: float = Field(..., description="Refund amount in dollars")
    refund_reason: RefundReason = Field(..., description="Reason for refund")
    status: str = Field(default="pending", description="Refund status")
    refund_date: datetime = Field(..., description="Refund creation timestamp")

    def get_id(self) -> str:
        """Return the refund ID."""
        return self.id
