# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, Field

from ..models import ArrangementType, BillingAccount


class GrantExtensionInput(BaseModel):
    """Input parameters for granting a payment extension."""

    policy_id: str = Field(
        ...,
        description="Policy ID used to locate the associated billing account.",
        examples=["POL-0012345678"],
    )
    new_due_date: str = Field(
        ...,
        description="New due date applied to the billing account.",
        examples=["2025-02-15"],
    )


class GrantExtensionOutput(BaseModel):
    """Output returned after granting the extension."""

    billing_account_id: str = Field(..., description="The billing account identifier.")
    arrangements_12_months: int = Field(
        ..., description="Updated number of arrangements in the last 12 months."
    )


class GrantExtensionTool(Tool):
    """Grant a payment extension on a billing account."""

    @property
    def name(self) -> str:
        return "grant_extension"

    @property
    def description(self) -> str:
        return (
            "Extends the payment due date and increments the arrangement count for the "
            "billing account."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GrantExtensionInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GrantExtensionOutput

    async def run(
        self, db: InMemoryDatabase, request: GrantExtensionInput
    ) -> GrantExtensionOutput:
        """Apply a new due date and update the arrangement history."""

        accounts = db.get_all(BillingAccount)
        account = next((a for a in accounts if a.policy_id == request.policy_id), None)

        if not account:
            raise self.ExecutionError(
                f"No billing account found for policy_id '{request.policy_id}'."
            )

        # Update billing account fields
        updated = account.model_copy(
            update={
                "current_due_date": request.new_due_date,
                "new_due_date": request.new_due_date,
                "arrangement_type": ArrangementType.EXTENSION,
                "arrangements_12_months": account.arrangements_12_months + 1,
                "installment_count": None,
                "installment_amount": None,
            }
        )

        db.update(updated)

        return GrantExtensionOutput(
            billing_account_id=updated.id,
            arrangements_12_months=updated.arrangements_12_months,
        )
