# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ...policy.models import Policy
from ..models import Claim, ClaimSeverity


class CheckOpenMajorClaimsInput(BaseModel):
    policy_id: str = Field(
        ...,
        description="Policy ID to check for major open claims.",
        examples=["POL-0012345678"],
    )


class CheckOpenMajorClaimsOutput(BaseModel):
    has_major_claim: bool = Field(
        ...,
        description="True if at least one open major-severity claim exists.",
        examples=[True],
    )
    major_claim_count: int = Field(
        ...,
        description="Number of open major-severity claims.",
        examples=[2],
    )


class CheckOpenMajorClaimsTool(Tool):

    @property
    def name(self) -> str:
        return "check_open_major_claims"

    @property
    def description(self) -> str:
        return "Checks if the policy has open claims with major severity."

    @property
    def request_model(self) -> Type[BaseModel]:
        return CheckOpenMajorClaimsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CheckOpenMajorClaimsOutput

    async def run(
        self,
        db: InMemoryDatabase,
        request: CheckOpenMajorClaimsInput,
    ) -> CheckOpenMajorClaimsOutput:

        policies = db.get_all(Policy)
        policy = next((p for p in policies if p.id == request.policy_id), None)

        if not policy:
            raise self.ExecutionError(f"Policy '{request.policy_id}' not found.")

        major_claims = [
            c
            for c in db.get_all(Claim)
            if c.policy_id == request.policy_id
            and c.claim_stage.value.startswith("Open")
            and c.severity == ClaimSeverity.MAJOR
        ]

        count = len(major_claims)

        return CheckOpenMajorClaimsOutput(
            has_major_claim=(count > 0),
            major_claim_count=count,
        )
