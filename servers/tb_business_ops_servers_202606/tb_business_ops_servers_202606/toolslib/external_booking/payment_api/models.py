# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Models for payment_api tools."""

from decimal import Decimal
from enum import Enum
from typing import Annotated, ClassVar, Optional

from tb_business_ops_servers_202606.utils.sandbox_tools_system import UnstableField
from pydantic import BaseModel, Field


# Enums from database schema
class TransactionType(str, Enum):
    """Transaction type values."""

    CHARGE = "charge"
    REFUND = "refund"
    DISPUTE = "dispute"


class PaymentStatus(str, Enum):
    """Payment status values."""

    SUCCESSFUL = "successful"
    PENDING = "pending"
    FAILED = "failed"


# Database models
class Transaction(BaseModel):
    """Transaction record model."""

    table_name: ClassVar[str] = "transactions"

    id: str = Field(..., description="Unique identifier (TXN-########)")
    transaction_id: str = Field(..., description="Transaction identifier")
    booking_reference: str = Field(..., description="Booking reference")
    customer_id: str = Field(..., description="Customer identifier")
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field(default="USD", description="Currency code")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    payment_status: PaymentStatus = Field(..., description="Payment status")
    payment_method: Optional[str] = Field(None, description="Payment method used")
    reason: Annotated[Optional[str], UnstableField()] = Field(
        None, description="Transaction reason (excluded from test case validation)"
    )
    processing_time_estimate: Optional[str] = Field(
        None, description="Processing time estimate"
    )
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    def get_id(self) -> str:
        """Return the unique identifier for this transaction."""
        return self.id


__all__ = [
    "TransactionType",
    "PaymentStatus",
    "Transaction",
]
