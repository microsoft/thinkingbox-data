# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Update payment method for a customer.

Updates stored payment method information for future transactions. Used when payment fails
or customer wants to change their payment details.
"""

from typing import Optional, Type

from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ...booking_api.models import Booking


class UpdatePaymentMethodInput(BaseModel):
    """Input model for update_payment_method tool."""

    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    new_payment_method: str = Field(
        ..., description="New payment method token", examples=["card_1234567890"]
    )


class UpdatePaymentMethodOutput(BaseModel):
    """Output model for update_payment_method tool."""

    model_config = ConfigDict(extra="forbid")

    success: bool = Field(
        ..., description="Indicates whether payment method update was successful"
    )
    payment_method_last4: Optional[str] = Field(
        None, description="Last 4 digits of new payment method"
    )


class UpdatePaymentMethod(Tool):
    """Update payment method for a customer."""

    @property
    def name(self) -> str:
        return "update_payment_method"

    @property
    def description(self) -> str:
        return "Update payment method for a customer"

    @property
    def request_model(self) -> Type[BaseModel]:
        return UpdatePaymentMethodInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return UpdatePaymentMethodOutput

    async def run(
        self, db: InMemoryDatabase, request: UpdatePaymentMethodInput
    ) -> UpdatePaymentMethodOutput:
        """Execute the tool logic."""
        # Verify customer exists by checking if they have any bookings
        all_bookings = db.get_all(Booking)
        customer_exists = any(
            b.customer_id == request.customer_id for b in all_bookings
        )

        if not customer_exists:
            raise Tool.ExecutionError(f"Customer not found: {request.customer_id}")

        # This updates external payment system (Stripe), no direct database write
        # Extract last 4 digits from payment method token
        # Simulating successful update with mock last 4 digits
        last4 = (
            request.new_payment_method[-4:]
            if len(request.new_payment_method) >= 4
            else "****"
        )

        return UpdatePaymentMethodOutput(success=True, payment_method_last4=last4)
