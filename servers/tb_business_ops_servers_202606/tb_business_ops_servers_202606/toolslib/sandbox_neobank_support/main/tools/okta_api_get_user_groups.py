# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get Okta user groups tool."""

from typing import List, Optional, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Employee, OktaGroupMembership


class OktaGetUserGroupsInput(BaseModel):
    """Input model for okta_api_get_user_groups tool."""

    email: str = Field(
        ..., description="Corporate email address", examples=["john.smith@vdb.com"]
    )


class GroupRecord(BaseModel):
    """Single group membership record."""

    model_config = ConfigDict(extra="forbid")

    group_name: str = Field(..., description="Group name")
    added_at: Optional[str] = Field(
        None, description="When added to group in ISO 8601 format"
    )


class OktaGetUserGroupsOutput(BaseModel):
    """Output model for okta_api_get_user_groups tool."""

    model_config = ConfigDict(extra="forbid")

    groups: List[GroupRecord] = Field(
        ..., description="Array of group membership records"
    )


class OktaGetUserGroupsTool(Tool):
    """Tool for listing all Okta group memberships for an employee."""

    @property
    def name(self) -> str:
        return "okta_api_get_user_groups"

    @property
    def description(self) -> str:
        return (
            "Returns all active Okta group memberships for an employee, including "
            "BI access groups, security groups, and department groups."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return OktaGetUserGroupsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return OktaGetUserGroupsOutput

    async def run(
        self, db: InMemoryDatabase, request: OktaGetUserGroupsInput
    ) -> OktaGetUserGroupsOutput:
        """Get all Okta group memberships for an employee."""
        # Get employee by email
        all_employees = db.get_all(Employee)
        employees = [e for e in all_employees if e.email == request.email]

        if not employees:
            raise Tool.ExecutionError(f"Employee not found: {request.email}")

        employee = employees[0]

        # Get all active group memberships
        all_memberships = db.get_all(OktaGroupMembership)
        active_memberships = [
            m for m in all_memberships if m.employee_id == employee.id and m.is_active
        ]

        # Build group records list
        groups = [
            GroupRecord(group_name=membership.group_name, added_at=membership.added_at)
            for membership in active_memberships
        ]

        return OktaGetUserGroupsOutput(groups=groups)
