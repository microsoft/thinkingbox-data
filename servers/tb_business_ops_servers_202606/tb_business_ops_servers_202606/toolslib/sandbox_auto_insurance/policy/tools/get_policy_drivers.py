# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get policy drivers tool for Policy Administration System."""

from typing import List, Optional, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, ConfigDict, Field

from ..models import Driver, Policy


class GetPolicyDriversInput(BaseModel):
    """Input model for get_policy_drivers tool."""

    policy_id: str = Field(
        ...,
        description="The policy identifier (POL-##########)",
        examples=["POL-0012345678"],
    )
    active_only: Optional[bool] = Field(
        None,
        description="Filter to only active drivers (Rated/Excluded) if true",
        examples=[True],
    )


class DriverInfo(BaseModel):
    """Basic driver information."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Driver identifier")
    name: str = Field(..., description="Driver's full name")
    date_of_birth: str = Field(..., description="Driver's date of birth")
    status: str = Field(..., description="Driver status")
    effective_date: str = Field(..., description="Effective date")
    is_named_insured: bool = Field(
        ..., description="Whether driver is the named insured"
    )
    is_co_insured: bool = Field(..., description="Whether driver is the co-insured")


class GetPolicyDriversOutput(BaseModel):
    """Output model for get_policy_drivers tool."""

    model_config = ConfigDict(extra="forbid")

    drivers: List[DriverInfo] = Field(
        ..., description="List of driver objects with basic information"
    )
    driver_count: int = Field(..., description="Total number of drivers returned")


class GetPolicyDriversTool(Tool):
    """Tool for listing all drivers on a policy."""

    @property
    def name(self) -> str:
        return "get_policy_drivers"

    @property
    def description(self) -> str:
        return (
            "Returns all drivers associated with the policy including their status and role "
            "(named insured, co-insured, or listed driver)."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetPolicyDriversInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetPolicyDriversOutput

    async def run(
        self, db: InMemoryDatabase, request: GetPolicyDriversInput
    ) -> GetPolicyDriversOutput:
        """List all drivers on a policy."""
        # Check if policy exists
        policy = db.get_by_id(Policy, request.policy_id)
        if policy is None:
            raise Tool.ExecutionError(f"Policy with ID '{request.policy_id}' not found")

        # Get all drivers for this policy
        all_drivers = db.get_all(Driver)
        policy_drivers = [d for d in all_drivers if d.policy_id == request.policy_id]

        # Filter by active status if requested (Rated or Excluded, not Removed)
        if request.active_only:
            policy_drivers = [
                d for d in policy_drivers if d.status.value in ["Rated", "Excluded"]
            ]

        # Return driver info
        drivers_data = [
            DriverInfo(
                id=d.id,
                name=d.name,
                date_of_birth=d.date_of_birth,
                status=d.status.value,
                effective_date=d.effective_date,
                is_named_insured=d.is_named_insured,
                is_co_insured=d.is_co_insured,
            )
            for d in policy_drivers
        ]

        return GetPolicyDriversOutput(
            drivers=drivers_data, driver_count=len(drivers_data)
        )
