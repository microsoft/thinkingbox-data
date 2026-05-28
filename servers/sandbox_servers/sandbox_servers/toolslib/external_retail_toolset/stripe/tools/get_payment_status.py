# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for getting payment status."""

from typing import Any, Dict, Type

from sandbox_servers import InMemoryDatabase, Tool, get_schema_without_refs
from sandbox_servers.toolslib.external_retail_toolset.stripe.models import (
    PaymentStatus,
    PaymentTransaction,
)
from pydantic import BaseModel, ConfigDict, Field


class GetPaymentStatusInput(BaseModel):
    """Input for get_payment_status tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ...,
        description="Order identifier to retrieve payment status",
        examples=["ORD-00012345"],
    )


class GetPaymentStatusOutput(BaseModel):
    """Output for get_payment_status tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    transaction_id: str = Field(
        ..., description="Unique transaction identifier", examples=["TXN-00012345"]
    )
    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
    )
    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    amount: float = Field(
        ..., description="Transaction amount in dollars", examples=[784.99]
    )
    status: PaymentStatus = Field(
        ...,
        description="Current payment status: authorized, declined, pending_authorization, failed",
        examples=["authorized"],
    )
    payment_method: str = Field(
        ..., description="Payment method description", examples=["Visa ending in 4242"]
    )
    transaction_date: str = Field(
        ..., description="Transaction timestamp", examples=["2024-10-15T14:23:05Z"]
    )


class GetPaymentStatusTool(Tool):
    """Tool implementation for retrieving payment transaction status."""

    @property
    def name(self) -> str:
        return "get_payment_status"

    @property
    def description(self) -> str:
        return (
            "Retrieve payment transaction status for an order. Fetches payment "
            "authorization status including transaction ID, amount, payment method, "
            "and current status. Used for payment failure troubleshooting and billing inquiries."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetPaymentStatusInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetPaymentStatusOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetPaymentStatusInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetPaymentStatusOutput

    async def run(
        self, db: InMemoryDatabase, request: GetPaymentStatusInput
    ) -> GetPaymentStatusOutput:
        """Retrieve payment status by order_id."""
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
                    f"No payment transaction found for order: {request.order_id}"
                )

            # Return payment status
            return GetPaymentStatusOutput(
                transaction_id=matching_transaction.id,
                order_id=matching_transaction.order_id,
                customer_id=matching_transaction.customer_id,
                amount=matching_transaction.amount,
                status=matching_transaction.status,
                payment_method=matching_transaction.payment_method,
                transaction_date=matching_transaction.transaction_date.isoformat(),
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve payment status: {str(e)}"
            raise Tool.ExecutionError(error_message)
