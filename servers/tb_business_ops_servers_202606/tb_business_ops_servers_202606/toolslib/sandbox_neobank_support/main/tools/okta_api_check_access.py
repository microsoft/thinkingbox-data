# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Check Okta application access tool."""

from typing import Optional, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, ConfigDict, Field

from ..models import Employee, GenericAccessLevel, OktaAppAccess


class OktaCheckAccessInput(BaseModel):
    """Input model for okta_api.check_access tool."""

    email: str = Field(
        ..., description="Corporate email address", examples=["john.smith@vdb.com"]
    )
    app_name: str = Field(..., description="Application name", examples=["Salesforce"])


class OktaCheckAccessOutput(BaseModel):
    """Output model for okta_api.check_access tool."""

    model_config = ConfigDict(extra="forbid")

    has_access: bool = Field(
        ..., description="Whether the employee currently has active access"
    )
    access_level: Optional[GenericAccessLevel] = Field(
        None, description="Current access level if access exists"
    )
    granted_at: Optional[str] = Field(
        None, description="When access was granted in ISO 8601 format"
    )


class OktaCheckAccessTool(Tool):
    """Tool for verifying current application access status for an employee."""

    @property
    def name(self) -> str:
        return "okta_api_check_access"

    @property
    def description(self) -> str:
        return (
            "Checks whether an employee has access to a specific application through Okta SSO "
            "and returns the current access level if granted. "
            "Covered systems: Slack, Confluence, Jira, Workday HRIS, VPN, Salesforce CRM, Tableau, "
            "GitHub, Quantivate, Actimize, Zoom, Splunk SIEM, Snowflake depersonalized, "
            "Snowflake raw replica, Admin Panel, Customer PII fields, AWS Production, Production database."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return OktaCheckAccessInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return OktaCheckAccessOutput

    async def run(
        self, db: InMemoryDatabase, request: OktaCheckAccessInput
    ) -> OktaCheckAccessOutput:
        """Check Okta application access status."""
        # Get employee by email
        all_employees = db.get_all(Employee)
        employees = [e for e in all_employees if e.email == request.email]

        if not employees:
            raise Tool.ExecutionError(f"Employee not found: {request.email}")

        employee = employees[0]

        # Check if employee has active access to this application
        all_accesses = db.get_all(OktaAppAccess)
        active_accesses = [
            a
            for a in all_accesses
            if a.employee_id == employee.id
            and a.app_name == request.app_name
            and a.is_active
        ]

        if active_accesses:
            access = active_accesses[0]
            return OktaCheckAccessOutput(
                has_access=True,
                access_level=access.access_level,
                granted_at=access.granted_at,
            )
        else:
            return OktaCheckAccessOutput(
                has_access=False, access_level=None, granted_at=None
            )
