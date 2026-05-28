# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from datetime import datetime
from typing import List, Optional, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ...crm_api.models import CustomerProfile


class UpdateCustomerInfoInput(BaseModel):
    """Input model for update_customer_info tool."""

    model_config = ConfigDict(extra="forbid")

    customer_id: str = Field(
        ...,
        description="Customer identifier in CUS-######## format.",
        examples=["CUS-00012345"],
    )

    # Optional update fields (flat structure)
    email: Optional[str] = Field(
        None,
        description="Updated email address.",
        examples=["new.email@example.com"],
    )

    full_name: Optional[str] = Field(
        None,
        description="Updated full customer name.",
        examples=["Alice Wonderland"],
    )

    preferences: Optional[List[str]] = Field(
        None,
        description="Updated list of customer preferences.",
        examples=[["quiet room", "high floor"]],
    )

    special_notes: Optional[List[str]] = Field(
        None,
        description="Additional internal notes.",
        examples=[["requested late checkout"]],
    )

    complaint_count: Optional[int] = Field(
        None,
        description="Updated complaint counter.",
        examples=[2],
    )

    loyalty_program_status: Optional[str] = Field(
        None,
        description="Updated loyalty program tier or status.",
        examples=["gold"],
    )

    last_booking_date: Optional[datetime] = Field(
        None,
        description="Timestamp of the customer's most recent booking.",
        examples=["2025-02-15T12:00:00Z"],
    )


class UpdateCustomerInfoOutput(BaseModel):
    success: bool = Field(
        ..., description="Indicates whether profile update was successful."
    )
    updated_fields: List[str] = Field(
        ..., description="List of fields that were successfully updated."
    )


class CrmApiUpdateCustomerInfoTool(Tool):
    @property
    def name(self) -> str:
        return "update_customer_info"

    @property
    def summary(self) -> str:
        return "Update customer profile information."

    @property
    def description(self) -> str:
        return (
            "Updates customer profile fields including preferences, special notes, "
            "or contact information. Used to maintain accurate customer records and "
            "track service interactions."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return UpdateCustomerInfoInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return UpdateCustomerInfoOutput

    async def run(
        self, db: InMemoryDatabase, request: UpdateCustomerInfoInput
    ) -> UpdateCustomerInfoOutput:

        if not isinstance(request.customer_id, str) or not request.customer_id.strip():
            raise self.ExecutionError("Invalid customer_id parameter.")

        # Get only the fields that were provided (exclude None values)
        # This follows the Zendesk gold standard pattern
        updates = request.model_dump(exclude_none=True, exclude={"customer_id"})

        if not updates:
            raise self.ExecutionError("Invalid update_fields parameter.")

        profiles = db.get_all(CustomerProfile)
        profile = next(
            (p for p in profiles if p.customer_id == request.customer_id), None
        )

        if profile is None:
            raise self.ExecutionError("Customer not found.")

        updated_fields = []

        for field_name, value in updates.items():
            if field_name in {"preferences", "special_notes"}:
                if not isinstance(value, list) or not all(
                    isinstance(x, str) for x in value
                ):
                    raise self.ExecutionError(
                        f"Field '{field_name}' must be an array of strings."
                    )

            if field_name == "complaint_count" and not isinstance(value, int):
                raise self.ExecutionError("Field 'complaint_count' must be an integer.")

            if field_name == "last_booking_date" and not isinstance(value, datetime):
                raise self.ExecutionError(
                    "Field 'last_booking_date' must be a datetime object."
                )

            if field_name in {"email", "full_name", "loyalty_program_status"}:
                if not isinstance(value, str):
                    raise self.ExecutionError(f"Field '{field_name}' must be a string.")

            setattr(profile, field_name, value)
            updated_fields.append(field_name)

        profile.updated_at = datetime.fromisoformat("2025-01-01T00:00:00+00:00")

        db.update(profile)

        return UpdateCustomerInfoOutput(success=True, updated_fields=updated_fields)
