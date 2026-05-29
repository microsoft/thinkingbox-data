# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for charging customer additional amounts."""

from datetime import datetime, timezone
from typing import Any, Dict, Type

from tb_business_ops_servers_202606 import InMemoryDatabase, Tool, get_schema_without_refs
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.stripe.models import (
    ChargeReason,
    PaymentStatus,
    PaymentTransaction,
)
from pydantic import BaseModel, ConfigDict, Field

# Fixed time for testing purposes
FIXED_DATETIME = datetime(2025, 10, 1, 13, 0, 5, tzinfo=timezone.utc)


class ChargeCustomerInput(BaseModel):
    """Input for charge_customer tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ...,
        description="Order identifier associated with charge",
        examples=["ORD-00012345"],
    )
    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    amount: float = Field(..., description="Charge amount in dollars", examples=[29.99])
    charge_reason: ChargeReason = Field(
        ...,
        description=(
            "Reason for charge: shipping_upgrade, reship_fee, "
            "installation_cancelled_shipping"
        ),
        examples=["shipping_upgrade"],
    )


class ChargeCustomerOutput(BaseModel):
    """Output for charge_customer tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    transaction_id: str = Field(
        ..., description="Unique transaction identifier", examples=["TXN-00098765"]
    )
    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
    )
    amount: float = Field(..., description="Charge amount in dollars", examples=[29.99])
    status: PaymentStatus = Field(
        ..., description="Payment status", examples=["authorized"]
    )
    transaction_date: str = Field(
        ..., description="Transaction timestamp", examples=["2024-10-22T11:15:00Z"]
    )


class ChargeCustomerTool(Tool):
    """Tool implementation for charging customer additional amounts."""

    @property
    def name(self) -> str:
        return "charge_customer"

    @property
    def description(self) -> str:
        return (
            "Charge customer additional amount for shipping upgrades, fees, etc. Creates an "
            "additional charge transaction for customer."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ChargeCustomerInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ChargeCustomerOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return ChargeCustomerInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ChargeCustomerOutput

    async def run(
        self, db: InMemoryDatabase, request: ChargeCustomerInput
    ) -> ChargeCustomerOutput:
        """Create a charge transaction for customer."""
        try:
            # Get all existing payment transactions to generate deterministic ID
            all_transactions = db.get_all(PaymentTransaction)
            transaction_count = len(all_transactions)

            # Generate deterministic transaction ID
            new_transaction_id = f"TXN-2{transaction_count:07d}"

            # Create new payment transaction (simulating successful charge)
            current_time = FIXED_DATETIME
            new_transaction = PaymentTransaction(
                id=new_transaction_id,
                order_id=request.order_id,
                customer_id=request.customer_id,
                amount=request.amount,
                status=PaymentStatus.AUTHORIZED,  # Simulate successful charge
                payment_method="Card on file",
                transaction_date=current_time,
                charge_reason=request.charge_reason,
            )

            # Add to database
            db.create(new_transaction)

            # Return transaction details
            return ChargeCustomerOutput(
                transaction_id=new_transaction.id,
                order_id=new_transaction.order_id,
                amount=new_transaction.amount,
                status=new_transaction.status,
                transaction_date=new_transaction.transaction_date.isoformat(),
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to charge customer: {str(e)}"
            raise Tool.ExecutionError(error_message)
