# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Check payment status for a booking.

Retrieves current payment status and transaction details for a booking. Used to verify payment completion,
identify failed transactions, or check refund processing status.
"""

from typing import Annotated, Optional, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Transaction


class CheckPaymentStatusInput(BaseModel):
    """Input model for check_payment_status tool."""

    booking_reference: str = Field(
        ..., description="Booking reference number", examples=["BKG-00012345"]
    )


class CheckPaymentStatusOutput(BaseModel):
    """Output model for check_payment_status tool."""

    model_config = ConfigDict(extra="forbid")

    payment_status: str = Field(
        ..., description="Current payment status: successful, pending, or failed"
    )
    transaction_id: str = Field(
        ..., description="Most recent transaction ID for the booking"
    )
    payment_method: Annotated[Optional[str], UnstableField()] = Field(
        None, description="Payment method used (excluded from test case validation)."
    )


class CheckPaymentStatus(Tool):
    """Check payment status for a booking."""

    @property
    def name(self) -> str:
        return "check_payment_status"

    @property
    def description(self) -> str:
        return "Check payment status for a booking"

    @property
    def request_model(self) -> Type[BaseModel]:
        return CheckPaymentStatusInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CheckPaymentStatusOutput

    async def run(
        self, db: InMemoryDatabase, request: CheckPaymentStatusInput
    ) -> CheckPaymentStatusOutput:
        """Execute the tool logic."""
        # Get all transactions for this booking
        all_transactions = db.get_all(Transaction)
        transactions = [
            t
            for t in all_transactions
            if t.booking_reference == request.booking_reference
        ]

        if not transactions:
            raise Tool.ExecutionError(
                f"No transactions found for booking: {request.booking_reference}"
            )

        # Get most recent transaction (sort by created_at DESC)
        recent_transaction = max(transactions, key=lambda t: t.created_at)

        return CheckPaymentStatusOutput(
            payment_status=recent_transaction.payment_status.value,
            transaction_id=recent_transaction.transaction_id,
            payment_method=recent_transaction.payment_method,
        )
