# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Optional, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ...crm_api.models import CustomerProfile, VipTier


class CheckVipStatusInput(BaseModel):
    """Input model for retrieving customer VIP tier and loyalty status."""

    customer_id: str = Field(
        ...,
        description="Customer identifier in CUS-######## format.",
        examples=["CUS-00012345"],
    )


class CheckVipStatusOutput(BaseModel):
    """Output model containing the VIP tier and loyalty program status."""

    vip_tier: VipTier = Field(
        ..., description="Customer tier: standard, vip, or platinum."
    )

    loyalty_program_status: Optional[str] = Field(
        None, description="Loyalty program enrollment and status details."
    )


class CrmApiCheckVipStatusTool(Tool):
    """Check customer VIP tier and loyalty status."""

    @property
    def name(self) -> str:
        return "check_vip_status"

    @property
    def description(self) -> str:
        return (
            "Quick lookup of customer tier level for policy application. "
            "Returns VIP status and loyalty program information without full profile details."
        )

    @property
    def summary(self) -> str:
        return "Check customer VIP tier and loyalty status."

    @property
    def request_model(self) -> Type[BaseModel]:
        return CheckVipStatusInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CheckVipStatusOutput

    async def run(
        self, db: InMemoryDatabase, request: CheckVipStatusInput
    ) -> CheckVipStatusOutput:
        """Retrieve the VIP tier and loyalty program status for the given customer."""

        customer_id = request.customer_id

        if not isinstance(customer_id, str) or not customer_id.strip():
            raise self.ExecutionError("Invalid customer_id parameter.")

        profiles = db.get_all(CustomerProfile)
        profile = next((p for p in profiles if p.customer_id == customer_id), None)

        if profile is None:
            raise self.ExecutionError("Customer not found.")

        return CheckVipStatusOutput(
            vip_tier=profile.vip_tier,
            loyalty_program_status=profile.loyalty_program_status,
        )
