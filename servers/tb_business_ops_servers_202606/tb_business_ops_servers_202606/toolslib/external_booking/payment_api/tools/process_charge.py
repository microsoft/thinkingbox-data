# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Process a charge for modification fees or additional services.

Initiates a charge transaction through the payment processor for modification fees or other additional charges.
Returns transaction details and confirmation for customer communication.
"""

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)

# Standard decimal precision for monetary amounts (2 decimal places)
TWO_PLACES = Decimal("0.01")
from pydantic import BaseModel, ConfigDict, Field

from ...booking_api.models import Booking
from ..models import PaymentStatus, Transaction, TransactionType

# Fixed current time for deterministic behavior
FIXED_CURRENT_TIME = datetime(2025, 11, 25, 10, 0, 0, tzinfo=timezone.utc)


class ProcessChargeInput(BaseModel):
    """Input model for process_charge tool."""

    booking_reference: str = Field(
        ..., description="Booking reference number", examples=["BKG-00012345"]
    )
    charge_amount: float = Field(
        ...,
        description="Charge amount",
        examples=[50.00],
        allow_inf_nan=False,
    )
    reason: str = Field(
        ..., description="Reason for charge", examples=["modification_fee"]
    )


class ProcessChargeOutput(BaseModel):
    """Output model for process_charge tool."""

    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(
        ...,
        description="Unique transaction identifier for the charge in format TXN-########",
    )
    payment_status: str = Field(
        ..., description="Status of charge: successful, pending, or failed"
    )


class ProcessCharge(Tool):
    """Process a charge for modification fees or additional services."""

    @property
    def name(self) -> str:
        return "process_charge"

    @property
    def description(self) -> str:
        return "Process a charge for modification fees or additional services"

    @property
    def request_model(self) -> Type[BaseModel]:
        return ProcessChargeInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ProcessChargeOutput

    async def run(
        self, db: InMemoryDatabase, request: ProcessChargeInput
    ) -> ProcessChargeOutput:
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

        charge_amount = Decimal(str(request.charge_amount))

        # Validate charge amount
        if charge_amount <= 0:
            raise Tool.ExecutionError("Invalid charge amount - must be greater than 0")

        # Get existing transactions to generate sequential ID
        all_transactions = db.get_all(Transaction)
        transaction_num = len(all_transactions) + 1
        transaction_id = f"TXN-{transaction_num:08d}"

        # Create charge transaction
        transaction = Transaction(
            id=transaction_id,
            transaction_id=transaction_id,
            booking_reference=request.booking_reference,
            customer_id=booking.customer_id,
            amount=charge_amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
            currency="USD",
            transaction_type=TransactionType.CHARGE,
            payment_status=PaymentStatus.SUCCESSFUL,
            payment_method=None,
            reason=request.reason,
            processing_time_estimate=None,
            created_at=FIXED_CURRENT_TIME.isoformat(),
            updated_at=FIXED_CURRENT_TIME.isoformat(),
        )

        db.create(transaction)

        return ProcessChargeOutput(
            transaction_id=transaction_id, payment_status="successful"
        )
