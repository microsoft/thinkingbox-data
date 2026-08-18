# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Add employee to Okta group tool."""

from datetime import datetime, timezone
from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, ConfigDict, Field

from ..models import Employee, OktaGroupMembership

# Fixed current time for deterministic behavior
FIXED_CURRENT_TIME = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)


class OktaAddToGroupInput(BaseModel):
    """Input model for okta_api_add_to_group tool."""

    email: str = Field(
        ..., description="Corporate email address", examples=["john.smith@vdb.com"]
    )
    group_name: str = Field(
        ..., description="Group name", examples=["bi_marketing_viewers"]
    )


class OktaAddToGroupOutput(BaseModel):
    """Output model for okta_api_add_to_group tool."""

    model_config = ConfigDict(extra="forbid")

    membership_id: str = Field(
        ...,
        description="Unique identifier for the group membership (format: OGM-########)",
    )


class OktaAddToGroupTool(Tool):
    """Tool for adding an employee to an Okta group."""

    @property
    def name(self) -> str:
        return "okta_api_add_to_group"

    @property
    def description(self) -> str:
        return (
            "Adds an employee to a specified Okta group, commonly used for BI dashboard "
            "access groups and role-based access control."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return OktaAddToGroupInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return OktaAddToGroupOutput

    async def run(
        self, db: InMemoryDatabase, request: OktaAddToGroupInput
    ) -> OktaAddToGroupOutput:
        """Add employee to Okta group."""
        # Get employee by email
        all_employees = db.get_all(Employee)
        employees = [e for e in all_employees if e.email == request.email]

        if not employees:
            raise Tool.ExecutionError(f"Employee not found: {request.email}")

        employee = employees[0]

        # Check if employee is already a member of this group
        all_memberships = db.get_all(OktaGroupMembership)
        existing_memberships = [
            m
            for m in all_memberships
            if m.employee_id == employee.id
            and m.group_name == request.group_name
            and m.is_active
        ]

        if existing_memberships:
            raise Tool.ExecutionError(
                f"Employee is already a member of this group: {request.group_name}"
            )

        # Generate new membership ID
        membership_count = len(all_memberships)
        new_membership_id = f"OGM-{membership_count + 1:08d}"

        # Create new membership record
        new_membership = OktaGroupMembership(
            id=new_membership_id,
            employee_id=employee.id,
            group_name=request.group_name,
            added_by="system",
            is_active=True,
        )

        # Save to database
        db.create(new_membership)

        return OktaAddToGroupOutput(membership_id=new_membership_id)
