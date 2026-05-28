# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field, model_serializer

from ..models import ArrangementType, BillingAccount, BillingAccountStatus


class GetAccountDetailsInput(BaseModel):
    """Input parameters for retrieving billing account details."""

    policy_id: str = Field(
        ...,
        description="Policy ID used to locate the associated billing account.",
        examples=["POL-0012345678"],
    )


class GetAccountDetailsOutput(BaseModel):
    """Output containing billing account details."""

    billing_account_id: str = Field(..., description="The billing account identifier.")
    policy_id: str = Field(..., description="The associated policy.")
    status: BillingAccountStatus = Field(..., description="Current billing status.")
    monthly_payment: int = Field(
        ..., description="Regular monthly payment amount in cents."
    )
    past_due_amount: int = Field(..., description="Amount currently past due in cents.")
    current_due_date: str = Field(..., description="Current payment due date.")
    payment_received: bool = Field(
        ..., description="Whether payment for the current cycle has been received."
    )
    arrangement_type: ArrangementType = Field(
        ..., description="Current arrangement type if applicable."
    )

    @model_serializer
    def serialize_model(self):
        """Serialize Enum fields to their string values."""
        return {
            "billing_account_id": self.billing_account_id,
            "policy_id": self.policy_id,
            "status": self.status.value,
            "monthly_payment": self.monthly_payment,
            "past_due_amount": self.past_due_amount,
            "current_due_date": self.current_due_date,
            "payment_received": self.payment_received,
            "arrangement_type": self.arrangement_type.value,
        }


class GetAccountDetailsTool(Tool):
    """Retrieve billing account information for a given policy."""

    @property
    def name(self) -> str:
        return "get_account_details"

    @property
    def description(self) -> str:
        return (
            "Fetches the billing account associated with a policy, including current "
            "balance and payment status."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetAccountDetailsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetAccountDetailsOutput

    async def run(
        self, db: InMemoryDatabase, request: GetAccountDetailsInput
    ) -> GetAccountDetailsOutput:
        """Return the billing account details for the given policy_id."""

        accounts = db.get_all(BillingAccount)
        account = next((a for a in accounts if a.policy_id == request.policy_id), None)

        if not account:
            raise self.ExecutionError(
                f"No billing account found for policy_id '{request.policy_id}'."
            )

        return GetAccountDetailsOutput(
            billing_account_id=account.id,
            policy_id=account.policy_id,
            status=account.status,
            monthly_payment=account.monthly_payment,
            past_due_amount=account.past_due_amount,
            current_due_date=account.current_due_date,
            payment_received=account.payment_received,
            arrangement_type=account.arrangement_type,
        )
