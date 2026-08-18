# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, Field

from ...policy.models import Policy
from ..models import Claim, ClaimSeverity, ClaimStage, ClaimType


class GetPolicyClaimsInput(BaseModel):
    """Input parameters for retrieving claims for a policy."""

    policy_id: str = Field(
        ...,
        description="Policy ID whose claims should be retrieved.",
        examples=["POL-0012345678"],
    )

    months_back: int | None = Field(
        None,
        description="How many months back to include when filtering by created_date.",
        examples=[24],
    )


class PolicyClaimRecord(BaseModel):
    """Projection of claim fields returned in the response."""

    claim_id: str = Field(
        ...,
        description="Claim identifier.",
        examples=["CLM-1000000001"],
    )
    date_of_loss: str = Field(
        ...,
        description="Date when the loss occurred (YYYY-MM-DD).",
        examples=["2024-05-10"],
    )
    claim_type: ClaimType = Field(
        ...,
        description="Type of the claim.",
        examples=[ClaimType.COLLISION_MULTI],
    )
    claim_stage: ClaimStage = Field(
        ...,
        description="Current stage of the claim.",
        examples=[ClaimStage.OPEN_INVESTIGATION],
    )
    severity: ClaimSeverity = Field(
        ...,
        description="Severity of the claim.",
        examples=[ClaimSeverity.MODERATE],
    )
    created_date: str = Field(
        ...,
        description="When the claim was created (YYYY-MM-DD).",
        examples=["2024-05-11"],
    )


class GetPolicyClaimsOutput(BaseModel):
    """Output returned after retrieving policy claims."""

    claims: List[PolicyClaimRecord] = Field(
        ..., description="List of claims matching the filter."
    )
    total_count: int = Field(
        ...,
        description="Total number of claims returned.",
    )


class GetPolicyClaimsTool(Tool):
    """Retrieve claims associated with a policy."""

    @property
    def name(self) -> str:
        return "get_policy_claims"

    @property
    def description(self) -> str:
        return "Returns all claims associated with a policy, optionally filtered by months_back."

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetPolicyClaimsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetPolicyClaimsOutput

    async def run(
        self,
        db: InMemoryDatabase,
        input: GetPolicyClaimsInput,
    ) -> GetPolicyClaimsOutput:

        policy = db.get_by_id(Policy, input.policy_id)
        if not policy:
            raise self.ExecutionError(f"Policy '{input.policy_id}' not found.")

        claims = db.get_all(Claim)
        claims = [c for c in claims if c.policy_id == input.policy_id]

        if input.months_back:
            # Find the latest created_date in the database to use as reference point
            # This makes the filtering deterministic instead of using datetime.now()
            all_claims = db.get_all(Claim)
            if all_claims:
                max_date_str = max(c.created_date for c in all_claims)
                max_date = datetime.strptime(max_date_str, "%Y-%m-%d")
            else:
                # If no claims exist, use a far future date
                max_date = datetime(2099, 12, 31)

            cutoff = max_date - timedelta(days=30 * input.months_back)
            cutoff_date_str = cutoff.strftime("%Y-%m-%d")

            claims = [c for c in claims if c.created_date >= cutoff_date_str]

        output_records = [
            PolicyClaimRecord(
                claim_id=c.id,
                date_of_loss=c.date_of_loss,
                claim_type=c.claim_type,
                claim_stage=c.claim_stage,
                severity=c.severity,
                created_date=c.created_date,
            )
            for c in claims
        ]

        return GetPolicyClaimsOutput(
            claims=output_records,
            total_count=len(output_records),
        )
