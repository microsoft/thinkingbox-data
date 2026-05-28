# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Verify customer identity tool for CRM."""

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

from ..models import Customer


class VerifyIdentityInput(BaseModel):
    """Input model for verify_identity tool."""

    customer_id: str = Field(
        ...,
        description="Unique identifier of the customer to verify.",
        examples=["CUS-00012345"],
    )
    ssn_last_4: Optional[str] = Field(
        None, description="Last 4 digits of SSN for verification.", examples=["1234"]
    )
    security_answer: Optional[str] = Field(
        None,
        description="Answer to the security question for verification.",
        examples=["Fluffy"],
    )


class VerifyIdentityOutput(BaseModel):
    """Output model for verify_identity tool."""

    model_config = ConfigDict(extra="forbid")

    verified: bool = Field(..., description="Whether the provided credentials match.")
    verification_method: str = Field(
        ..., description="Which method was used: 'ssn' or 'security_question'."
    )


class VerifyIdentityTool(Tool):
    """Tool for verifying customer identity using security credentials."""

    @property
    def name(self) -> str:
        return "verify_identity"

    @property
    def description(self) -> str:
        return (
            "Verify customer identity using security credentials. Validates customer-provided identity "
            "information against stored records. Supports verification via SSN last 4 digits or security "
            "question answer. Returns verification result."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return VerifyIdentityInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return VerifyIdentityOutput

    async def run(
        self, db: InMemoryDatabase, request: VerifyIdentityInput
    ) -> VerifyIdentityOutput:
        """Verify customer identity."""
        # Validate that at least one verification method is provided
        if not request.ssn_last_4 and not request.security_answer:
            raise Tool.ExecutionError(
                "Must provide either ssn_last_4 or security_answer for verification"
            )

        # Get customer by ID
        customer = db.get_by_id(Customer, request.customer_id)

        if customer is None:
            raise Tool.ExecutionError(
                f"Customer with ID '{request.customer_id}' not found"
            )

        # Try SSN verification first if provided
        if request.ssn_last_4:
            verified = customer.ssn_last_4 == request.ssn_last_4
            return VerifyIdentityOutput(verified=verified, verification_method="ssn")

        # Try security question verification
        if request.security_answer:
            # Case-insensitive comparison
            if customer.security_answer is None:
                verified = False
            else:
                verified = (
                    customer.security_answer.lower() == request.security_answer.lower()
                )

            return VerifyIdentityOutput(
                verified=verified, verification_method="security_question"
            )

        # This should not be reached due to the validation above
        raise Tool.ExecutionError(
            "Must provide either ssn_last_4 or security_answer for verification"
        )
