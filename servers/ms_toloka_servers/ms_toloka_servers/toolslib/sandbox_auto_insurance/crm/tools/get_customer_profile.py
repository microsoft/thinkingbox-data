# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get customer profile tool for CRM."""

from typing import Type

from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ..models import Customer, CustomerProfile


class GetCustomerProfileInput(BaseModel):
    """Input model for get_customer_profile tool."""

    customer_id: str = Field(
        ..., description="Unique identifier of the customer.", examples=["CUS-00012345"]
    )


class GetCustomerProfileTool(Tool):
    """Tool for retrieving full customer profile by customer ID."""

    @property
    def name(self) -> str:
        return "get_customer_profile"

    @property
    def description(self) -> str:
        return (
            "Retrieve the full customer profile by customer ID. Fetches complete customer information "
            "including their service tier, account flags, and verification data. Does not return the "
            "security answer directly for security reasons."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetCustomerProfileInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CustomerProfile

    async def run(
        self, db: InMemoryDatabase, request: GetCustomerProfileInput
    ) -> CustomerProfile:
        """Retrieve full customer profile."""
        # Get customer by ID
        customer = db.get_by_id(Customer, request.customer_id)

        if customer is None:
            raise Tool.ExecutionError(
                f"Customer with ID '{request.customer_id}' not found"
            )

        # Return profile without sensitive data (security_answer, ssn_last_4)
        return CustomerProfile(
            customer_id=customer.id,
            email=customer.email,
            first_name=customer.first_name,
            last_name=customer.last_name,
            date_of_birth=customer.date_of_birth,
            phone=customer.phone,
            tier=customer.tier.value,
            fraud_flag=customer.fraud_flag,
            security_question=customer.security_question,
            has_ssn_on_file=customer.ssn_last_4 is not None,
        )
