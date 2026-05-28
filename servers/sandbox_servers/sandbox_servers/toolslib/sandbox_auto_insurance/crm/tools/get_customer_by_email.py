# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get customer by email tool for CRM."""

from typing import Type

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


class GetCustomerByEmailInput(BaseModel):
    """Input model for get_customer_by_email tool."""

    email: str = Field(
        ...,
        description="Email address of the customer to look up.",
        examples=["john.smith@email.com"],
    )


class GetCustomerByEmailOutput(BaseModel):
    """Output model for get_customer_by_email tool."""

    model_config = ConfigDict(extra="forbid")

    customer_id: str = Field(
        ..., description="The unique customer identifier (CUS-########)."
    )
    first_name: str = Field(..., description="Customer's first name.")
    last_name: str = Field(..., description="Customer's last name.")


class GetCustomerByEmailTool(Tool):
    """Tool for looking up a customer by email address."""

    @property
    def name(self) -> str:
        return "get_customer_by_email"

    @property
    def description(self) -> str:
        return (
            "Look up a customer record by email address. Searches the CRM system for a customer using "
            "their email address. Returns basic customer identification if found. Use this as the first "
            "step to identify a customer before retrieving their full profile."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetCustomerByEmailInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetCustomerByEmailOutput

    async def run(
        self, db: InMemoryDatabase, request: GetCustomerByEmailInput
    ) -> GetCustomerByEmailOutput:
        """Look up a customer by email address."""
        # Get all customers
        all_customers = db.get_all(Customer)

        # Find customer by email
        customer = None
        for c in all_customers:
            if c.email.lower() == request.email.lower():
                customer = c
                break

        if customer is None:
            raise Tool.ExecutionError(f"No customer found with email '{request.email}'")

        return GetCustomerByEmailOutput(
            customer_id=customer.id,
            first_name=customer.first_name,
            last_name=customer.last_name,
        )
