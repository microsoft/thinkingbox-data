# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Process and track charge dispute or chargeback.

Creates dispute case for customer charge disputes or chargebacks. Tracks dispute details, status,
and resolution. Used for investigating billing discrepancies and customer charge challenges.
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

from ..models import PaymentStatus, Transaction, TransactionType

# Fixed current time for deterministic behavior
FIXED_CURRENT_TIME = datetime(2025, 11, 30, 10, 0, 0, tzinfo=timezone.utc)


class ProcessChargeDisputeInput(BaseModel):
    """Input model for process_charge_dispute tool."""

    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(
        ..., description="Original transaction identifier", examples=["TXN-00012345"]
    )
    dispute_reason: str = Field(
        ..., description="Reason for the dispute", examples=["unauthorized_charge"]
    )
    dispute_amount: Decimal = Field(
        ..., description="Amount being disputed", examples=["150.00"]
    )


class ProcessChargeDisputeOutput(BaseModel):
    """Output model for process_charge_dispute tool."""

    model_config = ConfigDict(extra="forbid")

    dispute_case_id: str = Field(
        ..., description="Unique identifier for the dispute case"
    )
    dispute_status: str = Field(
        ...,
        description="Current status of dispute: under_review, resolved, or escalated",
    )


class ProcessChargeDispute(Tool):
    """Process and track charge dispute or chargeback."""

    @property
    def name(self) -> str:
        return "process_charge_dispute"

    @property
    def description(self) -> str:
        return "Process and track charge dispute or chargeback"

    @property
    def request_model(self) -> Type[BaseModel]:
        return ProcessChargeDisputeInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ProcessChargeDisputeOutput

    async def run(
        self, db: InMemoryDatabase, request: ProcessChargeDisputeInput
    ) -> ProcessChargeDisputeOutput:
        """Execute the tool logic."""
        # Get original transaction
        all_transactions = db.get_all(Transaction)
        original_transaction = None
        for t in all_transactions:
            if t.transaction_id == request.transaction_id:
                original_transaction = t
                break

        if not original_transaction:
            raise Tool.ExecutionError(
                f"Transaction not found: {request.transaction_id}"
            )

        # Get existing disputes to generate sequential ID
        dispute_transactions = [
            t for t in all_transactions if t.transaction_type == TransactionType.DISPUTE
        ]
        dispute_num = len(dispute_transactions) + 1
        dispute_case_id = f"DSP-{dispute_num:08d}"

        # Create dispute transaction
        dispute_transaction = Transaction(
            id=dispute_case_id,
            transaction_id=dispute_case_id,
            booking_reference=original_transaction.booking_reference,
            customer_id=original_transaction.customer_id,
            amount=request.dispute_amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
            currency="USD",
            transaction_type=TransactionType.DISPUTE,
            payment_status=PaymentStatus.PENDING,
            payment_method=None,
            reason=request.dispute_reason,
            processing_time_estimate=None,
            created_at=FIXED_CURRENT_TIME.isoformat(),
            updated_at=FIXED_CURRENT_TIME.isoformat(),
        )

        db.create(dispute_transaction)

        return ProcessChargeDisputeOutput(
            dispute_case_id=dispute_case_id, dispute_status="under_review"
        )
