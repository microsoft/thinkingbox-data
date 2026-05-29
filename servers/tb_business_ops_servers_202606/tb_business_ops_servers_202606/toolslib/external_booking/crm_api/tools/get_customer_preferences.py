# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import List, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ...crm_api.models import CustomerProfile


class GetCustomerPreferencesInput(BaseModel):
    """Input model for retrieving customer preferences and special notes."""

    customer_id: str = Field(
        ...,
        description="Customer identifier in CUS-######## format.",
        examples=["CUS-00012345"],
    )


class GetCustomerPreferencesOutput(BaseModel):
    """Output model containing preferences and special notes."""

    preferences: List[str] = Field(..., description="Array of customer preferences.")

    special_notes: List[str] = Field(
        ...,
        description="Array of special notes about customer needs or past service considerations.",
    )


class CrmApiGetCustomerPreferencesTool(Tool):
    """Retrieve customer preferences and special notes."""

    @property
    def name(self) -> str:
        return "get_customer_preferences"

    @property
    def summary(self) -> str:
        return "Retrieve customer preferences and special notes."

    @property
    def description(self) -> str:
        return (
            "Fetches customer preferences, special requests history, and service notes for "
            "personalized support. Used to proactively address customer needs and preferences "
            "in interactions."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetCustomerPreferencesInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetCustomerPreferencesOutput

    async def run(
        self, db: InMemoryDatabase, request: GetCustomerPreferencesInput
    ) -> GetCustomerPreferencesOutput:
        """Retrieve preferences and special notes for the given customer."""

        customer_id = request.customer_id

        if not isinstance(customer_id, str) or not customer_id.strip():
            raise self.ExecutionError("Invalid customer_id parameter.")

        profiles = db.get_all(CustomerProfile)
        profile = next((p for p in profiles if p.customer_id == customer_id), None)

        if profile is None:
            raise self.ExecutionError("Customer not found.")

        return GetCustomerPreferencesOutput(
            preferences=profile.preferences, special_notes=profile.special_notes
        )
