# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Add vehicle tool for Policy Administration System."""

import hashlib
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

from ..models import Policy, Vehicle, VehicleStatus


class AddVehicleInput(BaseModel):
    """Input model for add_vehicle tool."""

    policy_id: str = Field(
        ..., description="The policy identifier", examples=["POL-0012345678"]
    )
    vin: str = Field(
        ...,
        description="Vehicle Identification Number (17 characters)",
        examples=["1HGCM82633A123456"],
    )
    year: int = Field(..., description="Model year", examples=[2022])
    make: str = Field(..., description="Vehicle manufacturer", examples=["Honda"])
    model: str = Field(..., description="Vehicle model", examples=["Accord"])
    effective_date: str = Field(
        ...,
        description="Date coverage becomes effective (YYYY-MM-DD)",
        examples=["2025-01-15"],
    )
    uw_pending: Optional[bool] = Field(
        None, description="Whether underwriting review is required", examples=[False]
    )


class AddVehicleOutput(BaseModel):
    """Output model for add_vehicle tool."""

    model_config = ConfigDict(extra="forbid")

    vehicle_id: str = Field(..., description="The newly created vehicle identifier")


class AddVehicleTool(Tool):
    """Tool for adding a new vehicle to an existing policy."""

    @property
    def name(self) -> str:
        return "add_vehicle"

    @property
    def description(self) -> str:
        return (
            "Creates a new vehicle record on the policy with the specified details. "
            "Sets initial coverage defaults."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return AddVehicleInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return AddVehicleOutput

    async def run(
        self, db: InMemoryDatabase, request: AddVehicleInput
    ) -> AddVehicleOutput:
        """Add a new vehicle to a policy."""
        # Check if policy exists
        policy = db.get_by_id(Policy, request.policy_id)
        if policy is None:
            raise Tool.ExecutionError(f"Policy with ID '{request.policy_id}' not found")

        # Check if VIN already exists on this policy
        all_vehicles = db.get_all(Vehicle)
        for v in all_vehicles:
            if v.policy_id == request.policy_id and v.vin == request.vin:
                raise Tool.ExecutionError(
                    f"VIN '{request.vin}' already exists on this policy"
                )

        # Generate deterministic vehicle ID based on policy_id and VIN
        id_seed = f"{request.policy_id}_{request.vin}"
        id_hash = hashlib.sha256(id_seed.encode()).hexdigest()[:8].upper()
        new_id = f"VEH-2-{id_hash}"

        # Check if this vehicle was already added (idempotency)
        existing_vehicle = db.get_by_id(Vehicle, new_id)
        if existing_vehicle is not None:
            return AddVehicleOutput(vehicle_id=existing_vehicle.id)

        # Create new vehicle with default coverages
        new_vehicle = Vehicle(
            id=new_id,
            policy_id=request.policy_id,
            vin=request.vin,
            year=request.year,
            make=request.make,
            model=request.model,
            status=VehicleStatus.ACTIVE,
            effective_date=request.effective_date,
            date_added_to_policy=request.effective_date,
            collision_coverage=True,
            comprehensive_coverage=True,
            rental_coverage=False,
            uw_pending=request.uw_pending if request.uw_pending is not None else False,
        )

        # Save to database
        db.create(new_vehicle)

        return AddVehicleOutput(vehicle_id=new_id)
