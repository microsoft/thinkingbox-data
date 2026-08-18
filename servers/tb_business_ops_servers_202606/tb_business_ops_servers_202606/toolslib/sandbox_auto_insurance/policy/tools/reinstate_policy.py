# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Reinstate policy tool for Policy Administration System."""

from typing import Optional, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, ConfigDict, Field

from ..models import Policy, PolicyStatus


class ReinstatePolicyInput(BaseModel):
    """Input model for reinstate_policy tool."""

    policy_id: str = Field(
        ..., description="The policy identifier", examples=["POL-0012345678"]
    )
    lapse_flag: bool = Field(
        ..., description="Whether a coverage lapse occurred", examples=[True]
    )
    lapse_start: Optional[str] = Field(
        None,
        description="Start date of coverage lapse (YYYY-MM-DD)",
        examples=["2025-01-15"],
    )
    lapse_end: Optional[str] = Field(
        None,
        description="End date of coverage lapse (YYYY-MM-DD)",
        examples=["2025-01-20"],
    )


class ReinstatePolicyOutput(BaseModel):
    """Output model for reinstate_policy tool."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., description="The policy identifier")
    status: str = Field(..., description="Will be 'Active'")
    lapse_flag: bool = Field(..., description="Whether a lapse was recorded")


class ReinstatePolicyTool(Tool):
    """Tool for reinstating a cancelled policy."""

    @property
    def name(self) -> str:
        return "reinstate_policy"

    @property
    def description(self) -> str:
        return (
            "Restores a policy that was cancelled for non-payment back to active status. "
            "Records any coverage lapse if applicable."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return ReinstatePolicyInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ReinstatePolicyOutput

    async def run(
        self, db: InMemoryDatabase, request: ReinstatePolicyInput
    ) -> ReinstatePolicyOutput:
        """Reinstate a cancelled policy."""
        # Get the policy
        policy = db.get_by_id(Policy, request.policy_id)

        if policy is None:
            raise Tool.ExecutionError(f"Policy with ID '{request.policy_id}' not found")

        # Update policy status to Active
        policy.status = PolicyStatus.ACTIVE

        # Clear cancellation details
        policy.cancellation_date = None
        policy.cancellation_reason = None

        # Set lapse information
        policy.lapse_flag = request.lapse_flag
        if request.lapse_flag:
            policy.lapse_start = request.lapse_start
            policy.lapse_end = request.lapse_end

        # Save changes
        db.update(policy)

        return ReinstatePolicyOutput(
            policy_id=policy.id,
            status=policy.status.value,
            lapse_flag=policy.lapse_flag,
        )
