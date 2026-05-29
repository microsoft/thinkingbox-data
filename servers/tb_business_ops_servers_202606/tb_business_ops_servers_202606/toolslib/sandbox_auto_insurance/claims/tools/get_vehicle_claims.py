# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import List, Optional, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ...policy.models import Vehicle
from ..models import Claim


class GetVehicleClaimsInput(BaseModel):
    vehicle_id: str = Field(
        ...,
        description="Vehicle ID whose claims should be retrieved.",
        examples=["VEH-00012345"],
    )
    open_only: Optional[bool] = Field(
        False, description="If true, only return open claims.", examples=[True]
    )


class VehicleClaimItem(BaseModel):
    claim_id: str = Field(..., examples=["CLM-1234567890"])
    date_of_loss: str = Field(..., examples=["2024-11-01"])
    claim_type: str = Field(..., examples=["Collision – Multi-Vehicle"])
    claim_stage: str = Field(..., examples=["Open – Initial Review"])
    severity: str = Field(..., examples=["Moderate"])
    created_date: str = Field(..., examples=["2024-11-05"])


class GetVehicleClaimsOutput(BaseModel):
    claims: List[VehicleClaimItem] = Field(
        ..., description="List of claims associated with the vehicle."
    )
    has_open_claims: bool = Field(
        ..., description="Whether the vehicle has any open claims."
    )


class GetVehicleClaimsTool(Tool):

    @property
    def name(self) -> str:
        return "get_vehicle_claims"

    @property
    def description(self) -> str:
        return "Returns all claims associated with a given vehicle."

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetVehicleClaimsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetVehicleClaimsOutput

    async def run(
        self, db: InMemoryDatabase, request: GetVehicleClaimsInput
    ) -> GetVehicleClaimsOutput:

        vehicles = db.get_all(Vehicle)
        vehicle = next((v for v in vehicles if v.id == request.vehicle_id), None)

        if not vehicle:
            raise self.ExecutionError(f"Vehicle '{request.vehicle_id}' not found.")

        claims = [c for c in db.get_all(Claim) if c.vehicle_id == request.vehicle_id]

        if request.open_only:
            claims = [c for c in claims if c.claim_stage.value.startswith("Open")]

        claim_items: List[VehicleClaimItem] = []
        for c in claims:
            claim_items.append(
                VehicleClaimItem(
                    claim_id=c.id,
                    date_of_loss=c.date_of_loss,
                    claim_type=c.claim_type.value,
                    claim_stage=c.claim_stage.value,
                    severity=c.severity.value,
                    created_date=c.created_date,
                )
            )

        has_open_claims = any(c.claim_stage.value.startswith("Open") for c in claims)

        return GetVehicleClaimsOutput(
            claims=claim_items, has_open_claims=has_open_claims
        )
