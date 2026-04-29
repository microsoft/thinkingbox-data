# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for Approver Lookup Service."""

from typing import Any, Dict, Optional, Type

from ms_toloka_servers.toolslib.sandbox_consulting.workday.models import Employee
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class ApproverLookupGetContactInput(BaseModel):
    """Input for approver_lookup_get_contact tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    email: str = Field(
        ...,
        description="Approver email address",
        examples=["manager@msg.com"],
    )


class ApproverLookupGetContactOutput(BaseModel):
    """Output for approver_lookup_get_contact tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    email: str = Field(..., description="Approver email address")
    name: str = Field(..., description="Approver full name")
    availability_status: str = Field(
        ..., description="Current availability status (available or on_leave)"
    )
    backup_approver_email: Optional[str] = Field(
        ...,
        description="Backup approver email. Always returned (can be null if no backup assigned). Agent uses this when availability_status is on_leave.",
    )


class ApproverLookupGetContactTool(Tool):
    """Tool implementation for retrieving approver contact information."""

    @property
    def name(self) -> str:
        return "get_contact"

    @property
    def description(self) -> str:
        return (
            "Retrieve approver contact information and availability. "
            "Fetches approver details including availability status and backup approver information. "
            "Retrieves approver information and current availability from employees table including name, "
            "email, availability_status (available or on_leave), and backup_approver_email "
            "(always returned, can be null). Use this before creating approval requests to route to "
            "backup approver if primary approver is on leave."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ApproverLookupGetContactInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ApproverLookupGetContactOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return ApproverLookupGetContactInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ApproverLookupGetContactOutput

    async def run(
        self, db: InMemoryDatabase, request: ApproverLookupGetContactInput
    ) -> ApproverLookupGetContactOutput:
        """Retrieve approver contact information."""
        try:
            # Get employee by email from employees table
            employee = db.get_by_id(Employee, request.email)

            # If no employee found, raise 404 error
            if not employee:
                raise Tool.ExecutionError(f"Approver not found: {request.email}")

            # Return approver contact information
            return ApproverLookupGetContactOutput(
                email=employee.email,
                name=employee.name,
                availability_status=employee.availability_status.value,
                backup_approver_email=employee.backup_approver_email,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve approver contact: {str(e)}"
            raise Tool.ExecutionError(error_message)
