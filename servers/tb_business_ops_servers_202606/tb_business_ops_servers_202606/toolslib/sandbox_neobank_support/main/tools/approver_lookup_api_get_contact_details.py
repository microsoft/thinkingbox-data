# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for checking approver availability."""

from typing import Any, Dict, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
    AvailabilityStatus,
    Employee,
    EmploymentStatus,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class GetContactDetailsInput(BaseModel):
    """Input for get_contact_details tool."""

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, validate_assignment=True
    )

    email: str = Field(
        ...,
        description="Email of the approver to check availability for",
        examples=["sarah.jones@vdb.com"],
    )


class GetContactDetailsOutput(BaseModel):
    """Output for get_contact_details tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    name: str = Field(..., description="Approver's full name", examples=["Sarah Jones"])
    availability_status: str = Field(
        ...,
        description="Whether approver is available or on leave",
        examples=["available"],
    )
    backup_approver_email: Optional[str] = Field(
        None,
        description="Backup approver email (approver's manager) if primary is on leave",
        examples=["michael.chen@vdb.com"],
    )


class GetContactDetailsTool(Tool):
    """Tool implementation for checking approver availability."""

    @property
    def name(self) -> str:
        return "approver_lookup_api_get_contact_details"

    @property
    def description(self) -> str:
        return (
            "Check approver availability and get backup contact if needed. "
            "Returns availability status for an approver and provides backup approver contact "
            "if the primary approver is on leave. Queries the employees table for employment status "
            "and manager information. Use after identifying the approver to check availability and "
            "route to backup if primary approver is on leave."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetContactDetailsInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetContactDetailsOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetContactDetailsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetContactDetailsOutput

    async def run(
        self, db: InMemoryDatabase, request: GetContactDetailsInput
    ) -> GetContactDetailsOutput:
        """Get approver contact details and availability."""
        try:
            # Get all employees
            all_employees = db.get_all(Employee)

            # Find the approver by email
            approver = None
            for emp in all_employees:
                if emp.email == request.email:
                    approver = emp
                    break

            if not approver:
                raise Tool.ExecutionError(f"Approver not found: {request.email}")

            # Map employment_status to availability_status:
            # - active → available
            # - on_leave → on_leave
            # - departing → available
            if approver.employment_status == EmploymentStatus.ON_LEAVE:
                availability = AvailabilityStatus.ON_LEAVE
            elif approver.employment_status == EmploymentStatus.ACTIVE:
                availability = AvailabilityStatus.AVAILABLE
            elif approver.employment_status == EmploymentStatus.DEPARTING:
                availability = AvailabilityStatus.AVAILABLE
            else:
                availability = AvailabilityStatus.UNAVAILABLE

            # Get backup approver (approver's manager) if on leave
            backup_email = None
            if availability == AvailabilityStatus.ON_LEAVE and approver.manager_id:
                # Find the backup approver (manager)
                for emp in all_employees:
                    if emp.id == approver.manager_id:
                        backup_email = emp.email
                        break

            # Return contact details
            return GetContactDetailsOutput(
                name=approver.full_name,
                availability_status=availability.value,
                backup_approver_email=backup_email,
            )

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to get contact details: {str(e)}"
            raise Tool.ExecutionError(error_message)
