# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import hashlib
from typing import Optional, Type

from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ...policy.models import Policy
from ..models import (
    Claim,
    ClaimSeverity,
    ClaimStage,
    ClaimType,
    SIUFlag,
)

PREFIX_FOR_PREGENERATED_IDS = "CLM-1"
PREFIX_FOR_NEW_IDS = "CLM-2"


def generate_claim_id(request: "CreateFNOLInput") -> str:
    """Generate deterministic claim ID based on input parameters."""
    # Use policy_id, date_of_loss, and vehicle info to create unique deterministic ID
    id_seed = f"{request.policy_id}_{request.date_of_loss}_{request.vehicle_id or request.vehicle_vin or 'no_vehicle'}"
    id_hash = hashlib.sha256(id_seed.encode()).hexdigest()[:9].upper()
    return f"{PREFIX_FOR_NEW_IDS}{id_hash}"


class CreateFNOLInput(BaseModel):
    policy_id: str = Field(
        ...,
        description="Policy ID associated with the claim.",
        examples=["POL-0012345678"],
    )
    vehicle_id: Optional[str] = Field(
        None,
        description="Vehicle ID involved in the loss event.",
        examples=["VEH-00012345"],
    )
    vehicle_vin: Optional[str] = Field(
        None,
        description="VIN of the vehicle involved.",
        examples=["1HGCM82633A123456"],
    )
    driver_id: Optional[str] = Field(
        None,
        description="Driver ID of person operating the vehicle.",
        examples=["DRV-00012345"],
    )

    date_of_loss: str = Field(
        ...,
        description="Date the loss occurred (YYYY-MM-DD).",
        examples=["2025-01-14"],
    )
    loss_location: str = Field(
        ...,
        description="Location of the incident.",
        examples=["Los Angeles, CA"],
    )

    claim_type: ClaimType = Field(
        ...,
        description="Type of the claim.",
        examples=["Collision – Multi-Vehicle"],
    )
    severity: ClaimSeverity = Field(
        ...,
        description="Claim severity level.",
        examples=["Moderate"],
    )
    siu_flag: Optional[SIUFlag] = Field(
        None,
        description="SIU (Special Investigation Unit) flag.",
        examples=["None"],
    )

    unlisted_driver_flag: Optional[bool] = Field(
        None,
        description="Indicates if the driver was unlisted.",
        examples=[False],
    )
    has_bodily_injury: Optional[bool] = Field(
        None,
        description="Indicates if bodily injury occurred.",
        examples=[False],
    )

    police_report_required: Optional[bool] = Field(
        None,
        description="Whether a police report is required.",
        examples=[False],
    )
    police_report_number: Optional[str] = Field(
        None,
        description="Police report number if applicable.",
        examples=["2025-12345"],
    )

    other_party_name: Optional[str] = Field(
        None,
        description="Name of the other party involved.",
        examples=["Jane Doe"],
    )
    other_party_phone: Optional[str] = Field(
        None,
        description="Phone number of the other party.",
        examples=["555-123-4567"],
    )
    other_party_insurance: Optional[str] = Field(
        None,
        description="Other party's insurance carrier.",
        examples=["State Farm"],
    )


class CreateFNOLOutput(BaseModel):
    claim_id: str = Field(
        ...,
        description="Generated claim identifier.",
    )
    claim_stage: ClaimStage = Field(
        ...,
        description="Initial stage of the claim.",
    )


class CreateFNOLTool(Tool):

    @property
    def name(self) -> str:
        return "create_fnol"

    @property
    def description(self) -> str:
        return "Creates a First Notice of Loss (FNOL) claim record."

    @property
    def request_model(self) -> Type[BaseModel]:
        return CreateFNOLInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CreateFNOLOutput

    async def run(
        self, db: InMemoryDatabase, request: CreateFNOLInput
    ) -> CreateFNOLOutput:

        policies = db.get_all(Policy)
        target_policy = next((p for p in policies if p.id == request.policy_id), None)
        if not target_policy:
            raise self.ExecutionError(f"Policy '{request.policy_id}' not found.")

        # Generate deterministic claim ID based on input parameters
        claim_id = generate_claim_id(request)

        # Check if this claim was already created (idempotency)
        existing_claim = db.get_by_id(Claim, claim_id)
        if existing_claim is not None:
            return CreateFNOLOutput(
                claim_id=existing_claim.id,
                claim_stage=existing_claim.claim_stage,
            )

        # Use date_of_loss as created_date (both are now strings)
        created_date = request.date_of_loss

        claim = Claim(
            id=claim_id,
            policy_id=request.policy_id,
            vehicle_id=request.vehicle_id,
            vehicle_vin=request.vehicle_vin,
            driver_id=request.driver_id,
            date_of_loss=request.date_of_loss,
            loss_location=request.loss_location,
            claim_type=request.claim_type,
            severity=request.severity,
            claim_stage=ClaimStage.OPEN_INITIAL,
            siu_flag=request.siu_flag or SIUFlag.NONE,
            unlisted_driver_flag=request.unlisted_driver_flag or False,
            has_bodily_injury=request.has_bodily_injury or False,
            police_report_required=request.police_report_required or False,
            police_report_number=request.police_report_number,
            other_party_name=request.other_party_name,
            other_party_phone=request.other_party_phone,
            other_party_insurance=request.other_party_insurance,
            created_date=created_date,
        )

        db.create(claim)

        return CreateFNOLOutput(
            claim_id=claim_id,
            claim_stage=ClaimStage.OPEN_INITIAL,
        )
