# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for Mavenlink Resource Management API (master tool)."""

from enum import Enum
from typing import Any, Dict, List, Optional, Type

from sandbox_servers.toolslib.sandbox_consulting.mavenlink.models import (
    EmployeeAssignment,
    MvEngagement,
)
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class MavenlinkAction(str, Enum):
    """Mavenlink API action enumeration."""

    GET_ENGAGEMENT = "get_engagement"
    GET_EMPLOYEE_ASSIGNMENTS = "get_employee_assignments"
    VALIDATE_ENGAGEMENT_CODE = "validate_engagement_code"


class MavenlinkApiInput(BaseModel):
    """Input for mavenlink_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    action: MavenlinkAction = Field(
        ...,
        description="Action to perform",
        examples=["get_engagement"],
    )
    engagement_code: Optional[str] = Field(
        None,
        description="Engagement code (required for get_engagement, validate_engagement_code)",
        examples=["ENG-0012345"],
    )
    email: Optional[str] = Field(
        None,
        description="Employee email address (required for get_employee_assignments)",
        examples=["alice@msg.com"],
    )


class EngagementDataOutput(BaseModel):
    """Engagement data output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    engagement_code: str = Field(..., description="Engagement code")
    status: str = Field(..., description="Engagement status")
    start_date: str = Field(..., description="Engagement start date")
    end_date: Optional[str] = Field(None, description="Engagement end date")
    senior_manager_email: str = Field(..., description="Senior manager email address")


class AssignmentOutput(BaseModel):
    """Assignment output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    engagement_code: str = Field(..., description="Engagement code")
    assignment_status: str = Field(
        ..., description="Assignment status (active or booked)"
    )
    start_date: str = Field(..., description="Assignment start date")
    end_date: Optional[str] = Field(None, description="Assignment end date")
    senior_manager_email: str = Field(..., description="Senior manager email address")


class MavenlinkApiOutput(BaseModel):
    """Output for mavenlink_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    engagement_data: Optional[EngagementDataOutput] = Field(
        None,
        description="Engagement record from mv_engagements table (for action=get_engagement)",
    )
    assignments: Optional[List[AssignmentOutput]] = Field(
        None,
        description="Array of assignment records from employee_assignments table (for action=get_employee_assignments)",
    )
    valid: Optional[bool] = Field(
        None,
        description="Indicates if engagement code is valid (for action=validate_engagement_code)",
    )


class MavenlinkApiTool(Tool):
    """Master tool implementation for Mavenlink Resource Management API."""

    @property
    def name(self) -> str:
        return "api"

    @property
    def description(self) -> str:
        return (
            "Access engagement and employee assignment data. Retrieves engagement details and "
            "validates employee assignments to engagements. Use action parameter to specify the operation:\n\n"
            "- action='get_engagement': Fetches engagement details including status, start_date, end_date, "
            "and senior_manager_email. REQUIRES: engagement_code. Returns engagement_data object from "
            "mv_engagements table.\n\n"
            "- action='get_employee_assignments': Retrieves all active and booked engagement assignments for "
            "an employee. REQUIRES: email. Returns assignments array with engagement_code, assignment_status "
            "(active or booked), start_date, end_date, and senior_manager_email for each assignment from "
            "employee_assignments table.\n\n"
            "- action='validate_engagement_code': Checks if engagement code exists in the system. REQUIRES: "
            "engagement_code. Returns valid boolean.\n\n"
            "Use get_employee_assignments to retrieve all active and booked engagements for approval routing "
            "and training overlap checks. Use get_engagement to fetch engagement details and senior manager information."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(MavenlinkApiInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(MavenlinkApiOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return MavenlinkApiInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return MavenlinkApiOutput

    async def run(
        self, db: InMemoryDatabase, request: MavenlinkApiInput
    ) -> MavenlinkApiOutput:
        """Execute Mavenlink API action."""
        try:
            if request.action == MavenlinkAction.GET_ENGAGEMENT:
                return await self._get_engagement(db, request)
            elif request.action == MavenlinkAction.GET_EMPLOYEE_ASSIGNMENTS:
                return await self._get_employee_assignments(db, request)
            elif request.action == MavenlinkAction.VALIDATE_ENGAGEMENT_CODE:
                return await self._validate_engagement_code(db, request)
            else:
                raise Tool.ExecutionError(f"Invalid action: {request.action}")

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to execute Mavenlink API action: {str(e)}"
            raise Tool.ExecutionError(error_message)

    async def _get_engagement(
        self, db: InMemoryDatabase, request: MavenlinkApiInput
    ) -> MavenlinkApiOutput:
        """Get engagement by engagement code."""
        if not request.engagement_code:
            raise Tool.ExecutionError("Missing required parameter: engagement_code")

        # Get engagement by engagement code
        engagement = db.get_by_id(MvEngagement, request.engagement_code)

        # If no engagement found, raise 404 error
        if not engagement:
            raise Tool.ExecutionError(
                f"Engagement not found: {request.engagement_code}"
            )

        # Return engagement data
        engagement_data = EngagementDataOutput(
            engagement_code=engagement.engagement_code,
            status=engagement.status.value,
            start_date=engagement.start_date.isoformat(),
            end_date=engagement.end_date.isoformat() if engagement.end_date else None,
            senior_manager_email=engagement.senior_manager_email,
        )

        return MavenlinkApiOutput(engagement_data=engagement_data)

    async def _get_employee_assignments(
        self, db: InMemoryDatabase, request: MavenlinkApiInput
    ) -> MavenlinkApiOutput:
        """Get all active and booked assignments for an employee."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")

        # Get all assignments
        all_assignments = db.get_all(EmployeeAssignment)

        # Filter assignments for the employee with status 'active' or 'booked'
        employee_assignments = [
            assignment
            for assignment in all_assignments
            if assignment.employee_email == request.email
            and assignment.assignment_status.value in ["active", "booked"]
        ]

        # Convert to output format
        assignments = [
            AssignmentOutput(
                engagement_code=assignment.engagement_code,
                assignment_status=assignment.assignment_status.value,
                start_date=assignment.start_date.isoformat(),
                end_date=(
                    assignment.end_date.isoformat() if assignment.end_date else None
                ),
                senior_manager_email=assignment.senior_manager_email,
            )
            for assignment in employee_assignments
        ]

        return MavenlinkApiOutput(assignments=assignments)

    async def _validate_engagement_code(
        self, db: InMemoryDatabase, request: MavenlinkApiInput
    ) -> MavenlinkApiOutput:
        """Validate if engagement code exists."""
        if not request.engagement_code:
            raise Tool.ExecutionError("Missing required parameter: engagement_code")

        # Check if engagement exists (don't check status field - just check if record exists)
        engagement = db.get_by_id(MvEngagement, request.engagement_code)

        # Return valid boolean
        return MavenlinkApiOutput(valid=engagement is not None)
