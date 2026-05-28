# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get vehicle details tool for Policy Administration System."""

from typing import Optional, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Vehicle


class GetVehicleDetailsInput(BaseModel):
    """Input model for get_vehicle_details tool."""

    vehicle_id: str = Field(
        ...,
        description="The vehicle identifier (VEH-########)",
        examples=["VEH-00012345"],
    )


class GetVehicleDetailsOutput(BaseModel):
    """Output model for get_vehicle_details tool."""

    model_config = ConfigDict(extra="forbid")

    vehicle_id: str = Field(..., description="The vehicle identifier")
    policy_id: str = Field(..., description="The policy this vehicle belongs to")
    vin: str = Field(..., description="Vehicle Identification Number")
    year: int = Field(..., description="Model year")
    make: str = Field(..., description="Vehicle manufacturer")
    model: str = Field(..., description="Vehicle model")
    status: str = Field(..., description="Active or Removed")
    effective_date: str = Field(
        ..., description="Date vehicle coverage became effective"
    )
    date_added_to_policy: str = Field(
        ..., description="Original date added to this policy"
    )
    collision_coverage: bool = Field(
        ..., description="Whether collision coverage is active"
    )
    comprehensive_coverage: bool = Field(
        ..., description="Whether comprehensive coverage is active"
    )
    rental_coverage: bool = Field(
        ..., description="Whether rental car coverage is active"
    )
    uw_pending: bool = Field(..., description="Whether underwriting review is pending")


class GetVehicleDetailsTool(Tool):
    """Tool for getting detailed information for a specific vehicle including coverages."""

    @property
    def name(self) -> str:
        return "get_vehicle_details"

    @property
    def description(self) -> str:
        return "Retrieves complete vehicle record including all coverage flags and underwriting status."

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetVehicleDetailsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetVehicleDetailsOutput

    async def run(
        self, db: InMemoryDatabase, request: GetVehicleDetailsInput
    ) -> GetVehicleDetailsOutput:
        """Get detailed information for a specific vehicle."""
        # Get the vehicle
        vehicle = db.get_by_id(Vehicle, request.vehicle_id)

        if vehicle is None:
            raise Tool.ExecutionError(
                f"Vehicle with ID '{request.vehicle_id}' not found"
            )

        return GetVehicleDetailsOutput(
            vehicle_id=vehicle.id,
            policy_id=vehicle.policy_id,
            vin=vehicle.vin,
            year=vehicle.year,
            make=vehicle.make,
            model=vehicle.model,
            status=vehicle.status.value,
            effective_date=vehicle.effective_date,
            date_added_to_policy=vehicle.date_added_to_policy,
            collision_coverage=vehicle.collision_coverage,
            comprehensive_coverage=vehicle.comprehensive_coverage,
            rental_coverage=vehicle.rental_coverage,
            uw_pending=vehicle.uw_pending,
        )
