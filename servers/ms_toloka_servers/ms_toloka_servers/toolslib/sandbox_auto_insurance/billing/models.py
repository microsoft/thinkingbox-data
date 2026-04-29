# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, Field


class BillingAccountStatus(Enum):
    """Represents the current billing status of an account."""

    CURRENT = "Current"
    PAST_DUE = "Past Due"
    IN_GRACE_PERIOD = "In Grace Period"
    PENDING_CANCELLATION = "Pending Cancellation"
    CANCELLED = "Cancelled"
    LAPSED = "Lapsed"


class ArrangementType(Enum):
    """Represents the type of payment arrangement applied to a billing account."""

    NONE = "None"
    EXTENSION = "Extension"
    INSTALLMENT_PLAN = "Installment Plan"


class BillingAccount(BaseModel):
    """
    Represents a billing account associated with an insurance policy.
    Includes financial details, arrangement data, and due dates.
    """

    table_name: ClassVar[str] = "billing_accounts"

    id: str = Field(..., description="Billing account identifier.")
    policy_id: str = Field(..., description="ID of the associated policy.")
    customer_id: str = Field(
        ..., description="ID of the customer who owns the account."
    )

    status: BillingAccountStatus = Field(
        default=BillingAccountStatus.CURRENT,
        description="Current billing status of the account.",
    )
    monthly_payment: int = Field(
        ..., description="Regular monthly payment amount in cents."
    )
    past_due_amount: int = Field(
        default=0, description="Amount currently past due in cents."
    )
    current_due_date: str = Field(..., description="Current payment due date.")
    payment_received: bool = Field(
        default=False,
        description="Whether payment for the current cycle has been received.",
    )

    arrangement_type: ArrangementType = Field(
        default=ArrangementType.NONE,
        description="Type of active payment arrangement, if any.",
    )
    arrangements_12_months: int = Field(
        default=0, description="Number of granted arrangements in the last 12 months."
    )
    new_due_date: Optional[str] = Field(
        None, description="New due date if an arrangement has been applied."
    )

    installment_count: Optional[int] = Field(
        None, description="Number of installments if an installment plan is active."
    )
    installment_amount: Optional[int] = Field(
        None, description="Amount for each installment if applicable."
    )

    def get_id(self) -> str:
        """Return the unique identifier for this billing account."""
        return self.id


__all__ = [
    "BillingAccount",
    "ArrangementType",
    "BillingAccountStatus",
]
