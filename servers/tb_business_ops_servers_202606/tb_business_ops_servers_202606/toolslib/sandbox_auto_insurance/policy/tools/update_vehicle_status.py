# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Update vehicle status tool for Policy Administration System."""

from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, ConfigDict, Field

from ..models import Vehicle, VehicleStatus


class UpdateVehicleStatusInput(BaseModel):
    """Input model for update_vehicle_status tool."""

    vehicle_id: str = Field(
        ..., description="The vehicle identifier", examples=["VEH-00012345"]
    )
    new_status: VehicleStatus = Field(
        ..., description="The new status for the vehicle", examples=["Removed"]
    )
    effective_date: str = Field(
        ...,
        description="Date the status change becomes effective (YYYY-MM-DD)",
        examples=["2025-01-15"],
    )


class UpdateVehicleStatusOutput(BaseModel):
    """Output model for update_vehicle_status tool."""

    model_config = ConfigDict(extra="forbid")

    vehicle_id: str = Field(..., description="The updated vehicle identifier")
    status: str = Field(..., description="The new status")


class UpdateVehicleStatusTool(Tool):
    """Tool for updating the status of a vehicle on a policy."""

    @property
    def name(self) -> str:
        return "update_vehicle_status"

    @property
    def description(self) -> str:
        return "Changes a vehicle's status, typically used to mark a vehicle as removed from the policy."

    @property
    def request_model(self) -> Type[BaseModel]:
        return UpdateVehicleStatusInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return UpdateVehicleStatusOutput

    async def run(
        self, db: InMemoryDatabase, request: UpdateVehicleStatusInput
    ) -> UpdateVehicleStatusOutput:
        """Update the status of a vehicle."""
        # Get the vehicle
        vehicle = db.get_by_id(Vehicle, request.vehicle_id)

        if vehicle is None:
            raise Tool.ExecutionError(
                f"Vehicle with ID '{request.vehicle_id}' not found"
            )

        # Update status
        vehicle.status = request.new_status

        # If status is Removed, set removal_date
        if request.new_status == VehicleStatus.REMOVED:
            vehicle.removal_date = request.effective_date

        # Save changes
        db.update(vehicle)

        return UpdateVehicleStatusOutput(
            vehicle_id=vehicle.id, status=vehicle.status.value
        )
