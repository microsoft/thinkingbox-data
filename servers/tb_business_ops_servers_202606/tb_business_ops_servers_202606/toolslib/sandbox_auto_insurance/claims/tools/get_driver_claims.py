# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import List, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, Field

from ...policy.models import Driver
from ..models import Claim


class GetDriverClaimsInput(BaseModel):
    """Input parameters for retrieving claims where this driver was at loss."""

    driver_id: str = Field(
        ...,
        description="Driver ID whose claims should be retrieved.",
        examples=["DRV-00012345"],
    )
    open_only: bool = Field(
        False,
        description="If true, returns only claims in an open stage.",
        examples=[True],
    )


class DriverClaimItem(BaseModel):
    claim_id: str = Field(..., examples=["CLM-9876543210"])
    date_of_loss: str = Field(..., examples=["2025-01-14"])
    claim_type: str = Field(..., examples=["Collision – Multi-Vehicle"])
    claim_stage: str = Field(..., examples=["Open – Initial Review"])
    severity: str = Field(..., examples=["Moderate"])
    created_date: str = Field(..., examples=["2025-01-15"])


class GetDriverClaimsOutput(BaseModel):
    """Output containing claims involving this driver."""

    claims: List[DriverClaimItem] = Field(
        ...,
        description="List of claims where this driver was the operator at time of loss.",
    )
    has_open_claims: bool = Field(
        ...,
        description="True if any returned claims are open.",
    )


class GetDriverClaimsTool(Tool):

    @property
    def name(self) -> str:
        return "get_driver_claims"

    @property
    def description(self) -> str:
        return "Returns all claims where the specified driver was at loss."

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetDriverClaimsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetDriverClaimsOutput

    async def run(
        self,
        db: InMemoryDatabase,
        request: GetDriverClaimsInput,
    ) -> GetDriverClaimsOutput:

        drivers = db.get_all(Driver)
        driver = next((d for d in drivers if d.id == request.driver_id), None)

        if not driver:
            raise self.ExecutionError(f"Driver '{request.driver_id}' not found.")

        claims = [c for c in db.get_all(Claim) if c.driver_id == request.driver_id]

        if request.open_only:
            claims = [c for c in claims if c.claim_stage.value.startswith("Open")]

        claim_items = []
        for c in claims:
            claim_items.append(
                DriverClaimItem(
                    claim_id=c.id,
                    date_of_loss=c.date_of_loss,
                    claim_type=c.claim_type.value,
                    claim_stage=c.claim_stage.value,
                    severity=c.severity.value,
                    created_date=c.created_date,
                )
            )

        has_open = any(ci.claim_stage.startswith("Open") for ci in claim_items)

        return GetDriverClaimsOutput(
            claims=claim_items,
            has_open_claims=has_open,
        )
