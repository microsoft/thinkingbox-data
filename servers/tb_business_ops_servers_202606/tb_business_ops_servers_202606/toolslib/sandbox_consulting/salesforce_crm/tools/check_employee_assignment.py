# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for checking employee assignment to engagement."""

from typing import Any, Dict, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.mavenlink.models import (
    EmployeeAssignment,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    get_schema_without_refs,
)
from pydantic import BaseModel, ConfigDict, Field


class CheckEmployeeAssignmentInput(BaseModel):
    """Input for salesforce_check_employee_assignment tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    email: str = Field(
        ...,
        description="Employee email address",
        examples=["user@msg.com"],
    )
    engagement_code: str = Field(
        ...,
        description="Engagement code to check assignment for",
        examples=["ENG-0012345"],
    )


class CheckEmployeeAssignmentOutput(BaseModel):
    """Output for salesforce_check_employee_assignment tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    assigned: bool = Field(
        ..., description="Indicates if employee is assigned to the engagement"
    )
    assignment_status: Optional[str] = Field(
        None,
        description="Status of assignment (active, booked) if assigned",
        examples=["active"],
    )
    start_date: Optional[str] = Field(
        None,
        description="Assignment start date if assigned",
        examples=["2024-01-15T00:00:00Z"],
    )
    end_date: Optional[str] = Field(
        None,
        description="Assignment end date if assigned",
        examples=["2024-12-31T00:00:00Z"],
    )


class CheckEmployeeAssignmentTool(Tool):
    """Tool implementation for checking employee assignment to engagement."""

    @property
    def name(self) -> str:
        return "check_employee_assignment"

    @property
    def description(self) -> str:
        return (
            "Validate employee assignment to engagement. Checks if an employee is assigned to "
            "a specific engagement and returns assignment details including status, start date, "
            "and end date. Use to validate that employee is authorized to request resources for "
            "an engagement before provisioning."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CheckEmployeeAssignmentInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CheckEmployeeAssignmentOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return CheckEmployeeAssignmentInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CheckEmployeeAssignmentOutput

    async def run(
        self, db: InMemoryDatabase, request: CheckEmployeeAssignmentInput
    ) -> CheckEmployeeAssignmentOutput:
        """Check employee assignment to engagement."""
        try:
            # Get all employee assignments
            all_assignments = db.get_all(EmployeeAssignment)

            # Find matching assignment
            matching_assignment = None
            for assignment in all_assignments:
                if (
                    assignment.employee_email == request.email
                    and assignment.engagement_code == request.engagement_code
                ):
                    matching_assignment = assignment
                    break

            # If no assignment found, return assigned=false
            if not matching_assignment:
                return CheckEmployeeAssignmentOutput(
                    assigned=False,
                    assignment_status=None,
                    start_date=None,
                    end_date=None,
                )

            # Return assignment details
            return CheckEmployeeAssignmentOutput(
                assigned=True,
                assignment_status=matching_assignment.assignment_status.value,
                start_date=matching_assignment.start_date.isoformat(),
                end_date=(
                    matching_assignment.end_date.isoformat()
                    if matching_assignment.end_date
                    else None
                ),
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to check employee assignment: {str(e)}"
            raise Tool.ExecutionError(error_message)
