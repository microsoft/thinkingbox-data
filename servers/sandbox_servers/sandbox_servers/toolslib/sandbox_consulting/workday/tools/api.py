# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for Workday HCM API (master tool)."""

from enum import Enum
from typing import Any, Dict, Optional, Type

from sandbox_servers.toolslib.sandbox_consulting.workday.models import Employee
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class WorkdayAction(str, Enum):
    """Workday API action enumeration."""

    GET_EMPLOYEE = "get_employee"


class WorkdayApiInput(BaseModel):
    """Input for workday_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    action: WorkdayAction = Field(
        ...,
        description="Action to perform",
        examples=["get_employee"],
    )
    email: Optional[str] = Field(
        None,
        description="Employee email address (required for get_employee)",
        examples=["jane.doe@msg.com"],
    )


class EmployeeDataOutput(BaseModel):
    """Employee data output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    email: str = Field(..., description="Employee email address")
    name: str = Field(..., description="Employee full name")
    level: str = Field(..., description="Employee level")
    office_location: str = Field(..., description="Office location")
    start_date: str = Field(..., description="Employment start date")
    manager_email: Optional[str] = Field(None, description="Manager email address")
    partner_email: Optional[str] = Field(None, description="Partner email address")
    onboarding_phase: Optional[str] = Field(None, description="Onboarding phase")
    availability_status: str = Field(
        ..., description="Availability status for approvals"
    )
    backup_approver_email: Optional[str] = Field(
        None, description="Backup approver email address"
    )


class WorkdayApiOutput(BaseModel):
    """Output for workday_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    employee_data: Optional[EmployeeDataOutput] = Field(
        None,
        description="Employee record from employees table (for action=get_employee)",
    )


class WorkdayApiTool(Tool):
    """Master tool implementation for Workday HCM API."""

    @property
    def name(self) -> str:
        return "api"

    @property
    def description(self) -> str:
        return (
            "Access employee profile data. Retrieves employee profiles from the HR system. "
            "Use action parameter to specify the operation:\n\n"
            "- action='get_employee': Fetches complete employee record including name, email, "
            "level, office_location, manager_email, partner_email, start_date, onboarding_phase, "
            "availability_status, and backup_approver_email. REQUIRES: email. Returns employee_data "
            "object from employees table.\n\n"
            "Always fetch employee context at the start of workflows to retrieve level, manager_email, "
            "partner_email, office_location, and onboarding_phase for approval routing and business logic."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(WorkdayApiInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(WorkdayApiOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return WorkdayApiInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return WorkdayApiOutput

    async def run(
        self, db: InMemoryDatabase, request: WorkdayApiInput
    ) -> WorkdayApiOutput:
        """Execute Workday API action."""
        try:
            if request.action == WorkdayAction.GET_EMPLOYEE:
                return await self._get_employee(db, request)
            else:
                raise Tool.ExecutionError(f"Invalid action: {request.action}")

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to execute Workday API action: {str(e)}"
            raise Tool.ExecutionError(error_message)

    async def _get_employee(
        self, db: InMemoryDatabase, request: WorkdayApiInput
    ) -> WorkdayApiOutput:
        """Get employee by email."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")

        # Get employee by email
        employee = db.get_by_id(Employee, request.email)

        # If no employee found, raise 404 error
        if not employee:
            raise Tool.ExecutionError(f"Employee not found: {request.email}")

        # Return employee data
        employee_data = EmployeeDataOutput(
            email=employee.email,
            name=employee.name,
            level=employee.level.value,
            office_location=employee.office_location.value,
            start_date=employee.start_date.isoformat(),
            manager_email=employee.manager_email,
            partner_email=employee.partner_email,
            onboarding_phase=(
                employee.onboarding_phase.value if employee.onboarding_phase else None
            ),
            availability_status=employee.availability_status.value,
            backup_approver_email=employee.backup_approver_email,
        )

        return WorkdayApiOutput(employee_data=employee_data)
