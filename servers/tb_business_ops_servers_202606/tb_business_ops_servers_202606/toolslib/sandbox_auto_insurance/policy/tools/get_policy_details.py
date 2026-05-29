# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get policy details tool for Policy Administration System."""

from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Policy


class GetPolicyDetailsInput(BaseModel):
    """Input model for get_policy_details tool."""

    policy_id: str = Field(
        ...,
        description="The policy identifier (POL-##########)",
        examples=["POL-0012345678"],
    )


class GetPolicyDetailsOutput(BaseModel):
    """Output model for get_policy_details tool."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., description="The policy identifier")
    customer_id: str = Field(..., description="The customer who owns this policy")
    status: str = Field(..., description="Current policy status")
    state: str = Field(..., description="State where policy is issued")
    effective_date: str = Field(..., description="Policy effective date (YYYY-MM-DD)")
    expiration_date: str = Field(..., description="Policy expiration date (YYYY-MM-DD)")
    renewal_date: str = Field(..., description="Next renewal date (YYYY-MM-DD)")
    cancellation_date: str | None = Field(
        None, description="Scheduled or actual cancellation date if applicable"
    )
    cancellation_reason: str | None = Field(
        None, description="Reason for cancellation if applicable"
    )
    named_insured_id: str = Field(..., description="Customer ID of the named insured")
    co_insured_id: str | None = Field(
        None, description="Customer ID of the co-insured if any"
    )
    automatic_extension_days: int = Field(
        ..., description="Days of automatic coverage for newly acquired vehicles"
    )
    at_fault_claims_3_years: int = Field(
        ..., description="Number of at-fault claims in last 3 years"
    )
    lapse_flag: bool = Field(..., description="Whether policy has had a coverage lapse")


class GetPolicyDetailsTool(Tool):
    """Tool for retrieving core policy information."""

    @property
    def name(self) -> str:
        return "get_policy_details"

    @property
    def description(self) -> str:
        return (
            "Fetches the main policy record including status, state, key dates, and insured party references. "
            "Does not include vehicles or drivers - use separate calls for those."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetPolicyDetailsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetPolicyDetailsOutput

    async def run(
        self, db: InMemoryDatabase, request: GetPolicyDetailsInput
    ) -> GetPolicyDetailsOutput:
        """Retrieve core policy information."""
        # Get the policy
        policy = db.get_by_id(Policy, request.policy_id)

        if policy is None:
            raise Tool.ExecutionError(f"Policy with ID '{request.policy_id}' not found")

        # Map Policy fields to output (exclude lapse_start/lapse_end as they're not in output schema)
        policy_dict = policy.model_dump(exclude={"lapse_start", "lapse_end"})
        # Rename 'id' to 'policy_id' for output
        policy_dict["policy_id"] = policy_dict.pop("id")

        return GetPolicyDetailsOutput(**policy_dict)
