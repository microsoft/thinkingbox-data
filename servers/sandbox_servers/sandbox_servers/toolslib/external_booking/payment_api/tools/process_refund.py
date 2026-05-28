# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Process a full or partial refund for a booking.

Initiates refund transaction through the payment processor. Handles both full and partial refunds
with reason tracking. Returns transaction details and estimated processing timeline for customer communication.
"""

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex

# Standard decimal precision for monetary amounts (2 decimal places)
TWO_PLACES = Decimal("0.01")
from pydantic import BaseModel, ConfigDict, Field

from ...booking_api.models import Booking
from ..models import PaymentStatus, Transaction, TransactionType

# Fixed current time for deterministic behavior
FIXED_CURRENT_TIME = datetime(2025, 11, 25, 10, 0, 0, tzinfo=timezone.utc)


class ProcessRefundInput(BaseModel):
    """Input model for process_refund tool."""

    booking_reference: str = Field(
        ..., description="Booking reference number", examples=["BKG-00012345"]
    )
    refund_amount: Decimal = Field(
        ..., description="Refund amount", examples=["250.00"]
    )
    reason: str = Field(..., description="Reason for refund", examples=["cancellation"])


class ProcessRefundOutput(BaseModel):
    """Output model for process_refund tool."""

    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(
        ..., description="Unique transaction identifier in format TXN-########"
    )
    refund_status: str = Field(
        ..., description="Status of refund: successful, pending, or failed"
    )
    processing_time_estimate: str = Field(
        ..., description="Estimated time for refund to appear"
    )


class ProcessRefund(Tool):
    """Process a full or partial refund for a booking."""

    @property
    def name(self) -> str:
        return "process_refund"

    @property
    def description(self) -> str:
        return "Process a full or partial refund for a booking"

    @property
    def request_model(self) -> Type[BaseModel]:
        return ProcessRefundInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ProcessRefundOutput

    async def run(
        self, db: InMemoryDatabase, request: ProcessRefundInput
    ) -> ProcessRefundOutput:
        """Execute the tool logic."""
        # Get booking to retrieve customer_id
        all_bookings = db.get_all(Booking)
        booking = None
        for b in all_bookings:
            if b.booking_reference == request.booking_reference:
                booking = b
                break

        if not booking:
            raise Tool.ExecutionError(f"Booking not found: {request.booking_reference}")

        # Get existing transactions to generate sequential ID
        all_transactions = db.get_all(Transaction)
        transaction_num = len(all_transactions) + 1
        transaction_id = f"TXN-{transaction_num:08d}"

        # Create refund transaction
        transaction = Transaction(
            id=transaction_id,
            transaction_id=transaction_id,
            booking_reference=request.booking_reference,
            customer_id=booking.customer_id,
            amount=request.refund_amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
            currency="USD",
            transaction_type=TransactionType.REFUND,
            payment_status=PaymentStatus.SUCCESSFUL,
            payment_method=None,
            reason=request.reason,
            processing_time_estimate="3-5 business days",
            created_at=FIXED_CURRENT_TIME.isoformat(),
            updated_at=FIXED_CURRENT_TIME.isoformat(),
        )

        db.create(transaction)

        return ProcessRefundOutput(
            transaction_id=transaction_id,
            refund_status="successful",
            processing_time_estimate="3-5 business days",
        )
