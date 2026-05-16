# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get manager chain tool for Workday HRIS."""

from typing import List, Type

from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Employee


class WorkdayGetManagerChainInput(BaseModel):
    """Input model for workday_api.get_manager_chain tool."""

    email: str = Field(
        ..., description="Corporate email address", examples=["john.smith@vdb.com"]
    )


class ManagerRecord(BaseModel):
    """Single manager record in the chain."""

    model_config = ConfigDict(extra="forbid")

    employee_id: str = Field(..., description="Manager's Workday ID")
    email: str = Field(..., description="Manager's corporate email")
    full_name: str = Field(..., description="Manager's full name")
    level: int = Field(..., description="Manager's level")
    department: str = Field(..., description="Manager's department")
    role: str = Field(..., description="Manager's role")


class WorkdayGetManagerChainOutput(BaseModel):
    """Output model for workday_api.get_manager_chain tool."""

    model_config = ConfigDict(extra="forbid")

    manager_chain: List[ManagerRecord] = Field(
        ...,
        description="Array of manager records in hierarchical order, from direct manager upward",
    )


class WorkdayGetManagerChainTool(Tool):
    """Tool for retrieving the reporting hierarchy for an employee."""

    @property
    def name(self) -> str:
        return "workday_api_get_manager_chain"

    @property
    def description(self) -> str:
        return (
            "Returns the management chain for a given employee including direct manager, skip-level manager, "
            "and department head. Used to determine approval routing for multi-level approval workflows."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return WorkdayGetManagerChainInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return WorkdayGetManagerChainOutput

    async def run(
        self, db: InMemoryDatabase, request: WorkdayGetManagerChainInput
    ) -> WorkdayGetManagerChainOutput:
        """Retrieve the manager chain for an employee."""
        # Get the employee
        all_employees = db.get_all(Employee)
        employees = [e for e in all_employees if e.email == request.email]

        if not employees:
            raise Tool.ExecutionError(f"Employee not found: {request.email}")

        employee = employees[0]

        # Build manager chain by traversing manager_id relationships
        manager_chain: List[ManagerRecord] = []
        current_manager_id = employee.manager_id

        while current_manager_id:
            # Get manager by ID - filter from all employees
            all_employees_for_manager = db.get_all(Employee)
            managers = [
                e for e in all_employees_for_manager if e.id == current_manager_id
            ]
            manager = managers[0] if managers else None

            if manager is None:
                break

            manager_chain.append(
                ManagerRecord(
                    employee_id=manager.id,
                    email=manager.email,
                    full_name=manager.full_name,
                    level=manager.level,
                    department=manager.department.value,
                    role=manager.role,
                )
            )

            # Move to next level
            current_manager_id = manager.manager_id

        return WorkdayGetManagerChainOutput(manager_chain=manager_chain)
