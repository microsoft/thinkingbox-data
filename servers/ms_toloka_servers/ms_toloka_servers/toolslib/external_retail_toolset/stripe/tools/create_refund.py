# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for creating refunds."""

from datetime import datetime, timezone
from typing import Any, Dict, Type

from ms_toloka_servers import InMemoryDatabase, Tool, get_schema_without_refs
from ms_toloka_servers.toolslib.external_retail_toolset.stripe.models import (
    PaymentTransaction,
    Refund,
    RefundReason,
)
from pydantic import BaseModel, ConfigDict, Field

# Fixed time for testing purposes
FIXED_DATETIME = datetime(2025, 10, 1, 13, 0, 5, tzinfo=timezone.utc)


class CreateRefundInput(BaseModel):
    """Input for create_refund tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ..., description="Order identifier for refund", examples=["ORD-00012345"]
    )
    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    amount: float = Field(..., description="Refund amount in dollars", examples=[50.00])
    refund_reason: RefundReason = Field(
        ...,
        description=(
            "Reason for refund: rma_processed, discount_correction, "
            "late_delivery_compensation, partial_refund_minor_defect, "
            "shipping_downgrade, order_cancelled"
        ),
        examples=["partial_refund_minor_defect"],
    )


class CreateRefundOutput(BaseModel):
    """Output for create_refund tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    refund_id: str = Field(
        ..., description="Unique refund identifier", examples=["RFD-00012345"]
    )
    transaction_id: str = Field(
        ...,
        description="Original payment transaction being refunded",
        examples=["TXN-00012345"],
    )
    amount: float = Field(..., description="Refund amount in dollars", examples=[50.00])
    status: str = Field(..., description="Refund status", examples=["pending"])
    refund_date: str = Field(
        ..., description="Refund creation timestamp", examples=["2024-10-22T11:00:00Z"]
    )


class CreateRefundTool(Tool):
    """Tool implementation for creating refunds."""

    @property
    def name(self) -> str:
        return "create_refund"

    @property
    def description(self) -> str:
        return (
            "Issue a refund to customer for various reasons. Creates a refund transaction "
            "for full or partial refund."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CreateRefundInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CreateRefundOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return CreateRefundInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CreateRefundOutput

    async def run(
        self, db: InMemoryDatabase, request: CreateRefundInput
    ) -> CreateRefundOutput:
        """Create a refund transaction."""
        try:
            # Get all payment transactions
            all_transactions = db.get_all(PaymentTransaction)

            # Find matching transaction by order_id
            matching_transaction = None
            for transaction in all_transactions:
                if transaction.order_id == request.order_id:
                    matching_transaction = transaction
                    break

            # If no transaction found, raise 404 error
            if not matching_transaction:
                raise Tool.ExecutionError(
                    f"Original payment transaction not found for order: {request.order_id}"
                )

            # Get all existing refunds to generate deterministic ID
            all_refunds = db.get_all(Refund)
            refund_count = len(all_refunds)

            # Generate deterministic refund ID
            new_refund_id = f"RFD-2{refund_count:07d}"

            # Create new refund record
            current_time = FIXED_DATETIME
            new_refund = Refund(
                id=new_refund_id,
                transaction_id=matching_transaction.id,
                order_id=request.order_id,
                amount=request.amount,
                refund_reason=request.refund_reason,
                status="pending",
                refund_date=current_time,
            )

            # Add to database
            db.create(new_refund)

            # Return refund details
            return CreateRefundOutput(
                refund_id=new_refund.id,
                transaction_id=new_refund.transaction_id,
                amount=new_refund.amount,
                status=new_refund.status,
                refund_date=new_refund.refund_date.isoformat(),
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to create refund: {str(e)}"
            raise Tool.ExecutionError(error_message)
