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
from pydantic import BaseModel, Field, model_serializer

from ..models import ArrangementType, BillingAccount, BillingAccountStatus


class ResetAccountStatusInput(BaseModel):
    """Input parameters for resetting billing account status."""

    policy_id: str = Field(
        ...,
        description="Policy ID used to locate the associated billing account.",
        examples=["POL-0012345678"],
    )


class ResetAccountStatusOutput(BaseModel):
    """Output returned after resetting the billing account."""

    billing_account_id: str = Field(..., description="The billing account identifier.")
    status: BillingAccountStatus = Field(
        ..., description="Updated billing status, always 'Current'."
    )

    @model_serializer
    def serialize_model(self):
        """Serialize Enum fields to their string values."""
        return {
            "billing_account_id": self.billing_account_id,
            "status": self.status.value,
        }


class ResetAccountStatusTool(Tool):
    """Reset billing account status after receiving payment."""

    @property
    def name(self) -> str:
        return "reset_account_status"

    @property
    def description(self) -> str:
        return (
            "Resets a billing account to current status by clearing past-due amounts "
            "and removing any active arrangement or installment configuration."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return ResetAccountStatusInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ResetAccountStatusOutput

    async def run(
        self, db: InMemoryDatabase, request: ResetAccountStatusInput
    ) -> ResetAccountStatusOutput:
        """Clear past-due fields and reset the account to current status."""

        accounts = db.get_all(BillingAccount)
        account = next((a for a in accounts if a.policy_id == request.policy_id), None)

        if not account:
            raise self.ExecutionError(
                f"No billing account found for policy_id '{request.policy_id}'."
            )

        updated = account.model_copy(
            update={
                "status": BillingAccountStatus.CURRENT,
                "past_due_amount": 0,
                "arrangement_type": ArrangementType.NONE,
                "new_due_date": None,
                "installment_count": None,
                "installment_amount": None,
            }
        )

        db.update(updated)

        return ResetAccountStatusOutput(
            billing_account_id=updated.id,
            status=updated.status,
        )
