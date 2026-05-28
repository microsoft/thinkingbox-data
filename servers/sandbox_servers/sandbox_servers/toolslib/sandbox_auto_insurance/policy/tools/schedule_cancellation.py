# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Schedule cancellation tool for Policy Administration System."""

from typing import Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import CancellationReason, Policy, PolicyStatus


class ScheduleCancellationInput(BaseModel):
    """Input model for schedule_cancellation tool."""

    policy_id: str = Field(
        ..., description="The policy identifier", examples=["POL-0012345678"]
    )
    cancellation_date: str = Field(
        ...,
        description="Date cancellation becomes effective (YYYY-MM-DD)",
        examples=["2025-01-31"],
    )
    cancellation_reason: CancellationReason = Field(
        ..., description="Reason for cancellation", examples=["User Requested"]
    )


class ScheduleCancellationOutput(BaseModel):
    """Output model for schedule_cancellation tool."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., description="The policy identifier")
    status: str = Field(..., description="Will be 'Pending Cancellation'")


class ScheduleCancellationTool(Tool):
    """Tool for scheduling a policy for cancellation."""

    @property
    def name(self) -> str:
        return "schedule_cancellation"

    @property
    def description(self) -> str:
        return "Sets a policy to pending cancellation status with the specified effective date and reason."

    @property
    def request_model(self) -> Type[BaseModel]:
        return ScheduleCancellationInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ScheduleCancellationOutput

    async def run(
        self, db: InMemoryDatabase, request: ScheduleCancellationInput
    ) -> ScheduleCancellationOutput:
        """Schedule a policy for cancellation."""
        # Get the policy
        policy = db.get_by_id(Policy, request.policy_id)

        if policy is None:
            raise Tool.ExecutionError(f"Policy with ID '{request.policy_id}' not found")

        # Update policy status and cancellation details
        policy.status = PolicyStatus.PENDING_CANCELLATION
        policy.cancellation_date = request.cancellation_date
        policy.cancellation_reason = request.cancellation_reason

        # Save changes
        db.update(policy)

        return ScheduleCancellationOutput(
            policy_id=policy.id, status=policy.status.value
        )
