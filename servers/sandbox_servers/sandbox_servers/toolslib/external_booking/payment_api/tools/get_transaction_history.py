# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Retrieve complete transaction history for a customer or booking.

Fetches all payment transactions including charges, refunds, and disputes. Provides comprehensive
payment history for financial inquiries, dispute resolution, or audit purposes.
"""

from decimal import Decimal
from typing import Annotated, List, Optional, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Transaction


class GetTransactionHistoryInput(BaseModel):
    """Input model for get_transaction_history tool."""

    customer_id: Optional[str] = Field(
        None, description="Customer identifier", examples=["CUS-00012345"]
    )
    booking_reference: Optional[str] = Field(
        None, description="Booking reference number", examples=["BKG-00012345"]
    )


class TransactionRecord(BaseModel):
    """Transaction record in history."""

    id: str = Field(..., description="Unique identifier")
    transaction_id: str = Field(..., description="Transaction identifier")
    booking_reference: str = Field(..., description="Booking reference")
    customer_id: str = Field(..., description="Customer identifier")
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field(..., description="Currency code")
    transaction_type: str = Field(..., description="Type of transaction")
    payment_status: str = Field(..., description="Payment status")
    payment_method: Annotated[Optional[str], UnstableField()] = Field(
        None, description="Payment method (excluded from test case validation)."
    )
    reason: Optional[str] = Field(None, description="Transaction reason")
    processing_time_estimate: Optional[str] = Field(
        None, description="Processing time estimate"
    )
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class GetTransactionHistoryOutput(BaseModel):
    """Output model for get_transaction_history tool."""

    model_config = ConfigDict(extra="forbid")

    transactions: List[TransactionRecord] = Field(
        ..., description="Array of transaction records"
    )


class GetTransactionHistory(Tool):
    """Retrieve complete transaction history for a customer or booking."""

    @property
    def name(self) -> str:
        return "get_transaction_history"

    @property
    def description(self) -> str:
        return "Retrieve complete transaction history for a customer or booking"

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetTransactionHistoryInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetTransactionHistoryOutput

    async def run(
        self, db: InMemoryDatabase, request: GetTransactionHistoryInput
    ) -> GetTransactionHistoryOutput:
        """Execute the tool logic."""
        # Validate parameters
        if not request.customer_id and not request.booking_reference:
            raise Tool.ExecutionError(
                "Either customer_id or booking_reference must be provided"
            )

        # Get all transactions and filter
        all_transactions = db.get_all(Transaction)
        transactions = []

        for t in all_transactions:
            matches = True

            if request.customer_id:
                matches = matches and (t.customer_id == request.customer_id)

            if request.booking_reference:
                matches = matches and (t.booking_reference == request.booking_reference)

            if matches:
                transactions.append(t)

        # Sort by created_at DESC
        transactions.sort(key=lambda t: t.created_at, reverse=True)

        # Convert to output format
        transaction_records = [
            TransactionRecord(
                id=t.id,
                transaction_id=t.transaction_id,
                booking_reference=t.booking_reference,
                customer_id=t.customer_id,
                amount=t.amount,
                currency=t.currency,
                transaction_type=t.transaction_type.value,
                payment_status=t.payment_status.value,
                payment_method=t.payment_method,
                reason=t.reason,
                processing_time_estimate=t.processing_time_estimate,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in transactions
        ]

        return GetTransactionHistoryOutput(transactions=transaction_records)
