# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get employee profile tool for Workday HRIS."""

from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, ConfigDict, Field

from ..models import Employee


class WorkdayGetEmployeeInput(BaseModel):
    """Input model for workday_api.get_employee tool."""

    email: str = Field(
        ..., description="Corporate email address", examples=["john.smith@vdb.com"]
    )


class WorkdayGetEmployeeOutput(BaseModel):
    """Output model for workday_api.get_employee tool."""

    model_config = ConfigDict(extra="forbid")

    employee_id: str = Field(..., description="Workday employee ID (format: WD-######)")
    email: str = Field(..., description="Corporate email address")
    full_name: str = Field(..., description="Employee's full name")
    level: int = Field(..., description="Employee level (1-8+)")
    department: str = Field(..., description="Department enum value")
    role: str = Field(..., description="Job title/role")
    office_location: str = Field(..., description="Office location or remote")
    start_date: str = Field(
        ...,
        description="Employment start date in ISO 8601 format (e.g., 2023-01-15T00:00:00Z)",
    )
    manager_id: str | None = Field(None, description="Manager's Workday ID")
    employment_status: str = Field(..., description="Current employment status")
    is_contractor: bool = Field(..., description="Whether employee is a contractor")
    remote_delivery_address: str | None = Field(
        None, description="For remote workers: Remote delivery address"
    )
    contract_end_date: str | None = Field(
        None,
        description="For contractors only: Contract end date in ISO 8601 format (e.g., 2023-01-15T00:00:00Z)",
    )


class WorkdayGetEmployeeTool(Tool):
    """Tool for retrieving employee profile and organizational details by email."""

    @property
    def name(self) -> str:
        return "workday_api_get_employee"

    @property
    def description(self) -> str:
        return (
            "Retrieves employee profile and direct manager id by email. "
            "Fetches complete employee profile data from Workday including level, department, role, "
            "manager relationship, office location, tenure, employment status, and delivery address for remote workers. "
            "Use as the first step in most workflows to retrieve employee context including level, department, and direct manager for standard approval workflows."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return WorkdayGetEmployeeInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return WorkdayGetEmployeeOutput

    async def run(
        self, db: InMemoryDatabase, request: WorkdayGetEmployeeInput
    ) -> WorkdayGetEmployeeOutput:
        """Retrieve employee profile by email."""
        # Get all employees and filter by email
        all_employees = db.get_all(Employee)
        employees = [e for e in all_employees if e.email == request.email]

        if not employees:
            raise Tool.ExecutionError(
                f"No employee found with the provided email: {request.email}"
            )

        employee = employees[0]

        # Map Employee fields to output
        return WorkdayGetEmployeeOutput(
            employee_id=employee.id,
            email=employee.email,
            full_name=employee.full_name,
            level=employee.level,
            department=employee.department.value,
            role=employee.role,
            office_location=employee.office_location.value,
            start_date=employee.start_date,
            manager_id=employee.manager_id,
            employment_status=employee.employment_status.value,
            is_contractor=employee.is_contractor,
            remote_delivery_address=employee.remote_delivery_address,
            contract_end_date=employee.contract_end_date,
        )
