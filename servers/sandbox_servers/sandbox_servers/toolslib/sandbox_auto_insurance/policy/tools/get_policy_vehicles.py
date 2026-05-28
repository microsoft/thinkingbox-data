# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get policy vehicles tool for Policy Administration System."""

from typing import List, Optional, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Policy, Vehicle


class GetPolicyVehiclesInput(BaseModel):
    """Input model for get_policy_vehicles tool."""

    policy_id: str = Field(
        ...,
        description="The policy identifier (POL-##########)",
        examples=["POL-0012345678"],
    )
    active_only: Optional[bool] = Field(
        None, description="Filter to only active vehicles if true", examples=[True]
    )


class VehicleInfo(BaseModel):
    """Basic vehicle information."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Vehicle identifier")
    vin: str = Field(..., description="Vehicle Identification Number")
    year: int = Field(..., description="Model year")
    make: str = Field(..., description="Vehicle manufacturer")
    model: str = Field(..., description="Vehicle model")
    status: str = Field(..., description="Vehicle status")
    effective_date: str = Field(..., description="Effective date")


class GetPolicyVehiclesOutput(BaseModel):
    """Output model for get_policy_vehicles tool."""

    model_config = ConfigDict(extra="forbid")

    vehicles: List[VehicleInfo] = Field(
        ..., description="List of vehicle objects with basic information"
    )
    vehicle_count: int = Field(..., description="Total number of vehicles returned")


class GetPolicyVehiclesTool(Tool):
    """Tool for listing all vehicles on a policy."""

    @property
    def name(self) -> str:
        return "get_policy_vehicles"

    @property
    def description(self) -> str:
        return (
            "Returns a list of all vehicles currently or previously on the policy. "
            "Includes basic vehicle information but not detailed coverage data."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetPolicyVehiclesInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetPolicyVehiclesOutput

    async def run(
        self, db: InMemoryDatabase, request: GetPolicyVehiclesInput
    ) -> GetPolicyVehiclesOutput:
        """List all vehicles on a policy."""
        # Check if policy exists
        policy = db.get_by_id(Policy, request.policy_id)
        if policy is None:
            raise Tool.ExecutionError(f"Policy with ID '{request.policy_id}' not found")

        # Get all vehicles for this policy
        all_vehicles = db.get_all(Vehicle)
        policy_vehicles = [v for v in all_vehicles if v.policy_id == request.policy_id]

        # Filter by active status if requested
        if request.active_only:
            policy_vehicles = [v for v in policy_vehicles if v.status.value == "Active"]

        # Return basic vehicle info
        vehicles_data = [
            VehicleInfo(
                id=v.id,
                vin=v.vin,
                year=v.year,
                make=v.make,
                model=v.model,
                status=v.status.value,
                effective_date=v.effective_date,
            )
            for v in policy_vehicles
        ]

        return GetPolicyVehiclesOutput(
            vehicles=vehicles_data, vehicle_count=len(vehicles_data)
        )
