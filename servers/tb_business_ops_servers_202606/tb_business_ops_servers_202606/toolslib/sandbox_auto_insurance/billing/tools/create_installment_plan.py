# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ..models import ArrangementType, BillingAccount


class CreateInstallmentPlanInput(BaseModel):
    """Input parameters for creating a payment installment plan."""

    policy_id: str = Field(
        ...,
        description="Policy ID used to locate the associated billing account.",
        examples=["POL-0012345678"],
    )

    installment_count: int = Field(
        ...,
        description="Number of installments to split the past-due amount into.",
        examples=[3],
    )

    installment_amount: int = Field(
        ...,
        description="Amount of each installment in cents.",
        examples=[10000],  # $100.00
    )


class CreateInstallmentPlanOutput(BaseModel):
    """Output returned after creating the installment plan."""

    billing_account_id: str = Field(
        ...,
        description="The billing account identifier.",
    )

    arrangements_12_months: int = Field(
        ...,
        description="Updated number of arrangements in the last 12 months.",
    )


class CreateInstallmentPlanTool(Tool):
    """Create a payment installment plan for the past-due balance."""

    @property
    def name(self) -> str:
        return "create_installment_plan"

    @property
    def description(self) -> str:
        return (
            "Sets up a structured payment plan to split the past-due balance into "
            "multiple payments and increments the arrangement count."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return CreateInstallmentPlanInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CreateInstallmentPlanOutput

    async def run(
        self, db: InMemoryDatabase, request: CreateInstallmentPlanInput
    ) -> CreateInstallmentPlanOutput:
        """Create an installment plan on the billing account."""

        accounts = db.get_all(BillingAccount)
        account = next((a for a in accounts if a.policy_id == request.policy_id), None)

        if not account:
            raise self.ExecutionError(
                f"No billing account found for policy_id '{request.policy_id}'."
            )

        # Update billing account fields
        updated = account.model_copy(
            update={
                "arrangement_type": ArrangementType.INSTALLMENT_PLAN,
                "installment_count": request.installment_count,
                "installment_amount": request.installment_amount,
                "arrangements_12_months": account.arrangements_12_months + 1,
            }
        )

        db.update(updated)

        return CreateInstallmentPlanOutput(
            billing_account_id=updated.id,
            arrangements_12_months=updated.arrangements_12_months,
        )
