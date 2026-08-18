# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Optional, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, Field

from ...crm_api.models import CustomerProfile


class GetCustomerProfileInput(BaseModel):
    """Input model for retrieving a complete customer profile."""

    customer_id: Optional[str] = Field(
        None,
        description="Customer identifier in CUS-######## format.",
        examples=["CUS-00012345"],
    )
    email: Optional[str] = Field(
        None,
        description="Customer email address for lookup.",
        examples=["john.smith@example.com"],
    )


class GetCustomerProfileOutput(BaseModel):
    """Output model containing the full customer profile."""

    customer_data: CustomerProfile = Field(
        ..., description="Complete customer profile record loaded from the database."
    )


class CrmApiGetCustomerProfileTool(Tool):
    """Retrieve complete customer profile and history."""

    @property
    def name(self) -> str:
        return "get_customer_profile"

    @property
    def description(self) -> str:
        return (
            "Fetches comprehensive customer information including booking history "
            "metrics, lifetime value, loyalty status, preferences, and special notes."
            "Essential for personalizing support and applying customer-specific policies."
        )

    @property
    def summary(self) -> str:
        return "Retrieve complete customer profile and history."

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetCustomerProfileInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetCustomerProfileOutput

    async def run(
        self, db: InMemoryDatabase, request: GetCustomerProfileInput
    ) -> GetCustomerProfileOutput:
        """Retrieve full customer profile using customer_id or email."""

        customer_id = request.customer_id
        email = request.email

        if not customer_id and not email:
            raise self.ExecutionError(
                "Invalid parameters: provide customer_id or email."
            )

        profiles = db.get_all(CustomerProfile)

        profile = None
        if customer_id:
            profile = next((p for p in profiles if p.customer_id == customer_id), None)
        elif email:
            profile = next(
                (p for p in profiles if p.email.lower() == email.lower()), None
            )

        if profile is None:
            raise self.ExecutionError("Customer not found.")

        return GetCustomerProfileOutput(customer_data=profile)
