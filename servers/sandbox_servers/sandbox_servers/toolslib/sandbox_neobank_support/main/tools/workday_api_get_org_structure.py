# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get organization structure tool for Workday HRIS."""

from typing import List, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Employee


class WorkdayGetOrgStructureInput(BaseModel):
    """Input model for workday_api.get_org_structure tool."""

    manager_email: str = Field(
        ...,
        description="Manager's corporate email address",
        examples=["sarah.jones@vdb.com"],
    )


class DirectReportRecord(BaseModel):
    """Single direct report record."""

    model_config = ConfigDict(extra="forbid")

    employee_id: str = Field(..., description="Employee's Workday ID")
    email: str = Field(..., description="Employee's corporate email")
    full_name: str = Field(..., description="Employee's full name")
    level: int = Field(..., description="Employee's level")
    department: str = Field(..., description="Employee's department")
    role: str = Field(..., description="Employee's role")
    office_location: str = Field(..., description="Employee's office location")
    employment_status: str = Field(..., description="Employee's employment status")


class WorkdayGetOrgStructureOutput(BaseModel):
    """Output model for workday_api.get_org_structure tool."""

    model_config = ConfigDict(extra="forbid")

    direct_reports: List[DirectReportRecord] = Field(
        ..., description="Array of employee records who report to this manager"
    )


class WorkdayGetOrgStructureTool(Tool):
    """Tool for retrieving all direct reports for a manager."""

    @property
    def name(self) -> str:
        return "workday_api_get_org_structure"

    @property
    def description(self) -> str:
        return (
            "Returns list of employees who report directly to the specified manager. "
            "Used for organizational context and team-based access provisioning."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return WorkdayGetOrgStructureInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return WorkdayGetOrgStructureOutput

    async def run(
        self, db: InMemoryDatabase, request: WorkdayGetOrgStructureInput
    ) -> WorkdayGetOrgStructureOutput:
        """Retrieve all direct reports for a manager."""
        # Get manager by email
        all_employees = db.get_all(Employee)
        managers = [e for e in all_employees if e.email == request.manager_email]

        if not managers:
            raise Tool.ExecutionError(f"Manager not found: {request.manager_email}")

        manager = managers[0]

        # Query employees WHERE manager_id = manager.id
        direct_reports_employees = [
            e for e in all_employees if e.manager_id == manager.id
        ]

        # Build direct reports list
        direct_reports = [
            DirectReportRecord(
                employee_id=emp.id,
                email=emp.email,
                full_name=emp.full_name,
                level=emp.level,
                department=emp.department.value,
                role=emp.role,
                office_location=emp.office_location.value,
                employment_status=emp.employment_status.value,
            )
            for emp in direct_reports_employees
        ]

        return WorkdayGetOrgStructureOutput(direct_reports=direct_reports)
