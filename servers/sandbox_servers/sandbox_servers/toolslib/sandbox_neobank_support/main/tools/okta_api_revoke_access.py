# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Revoke Okta application access tool."""

from datetime import datetime, timezone
from typing import Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Employee, OktaAppAccess

# Fixed current time for deterministic behavior
FIXED_CURRENT_TIME = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)


class OktaRevokeAccessInput(BaseModel):
    """Input model for okta_api_revoke_access tool."""

    email: str = Field(
        ..., description="Corporate email address", examples=["john.smith@vdb.com"]
    )
    app_name: str = Field(..., description="Application name", examples=["Salesforce"])


class OktaRevokeAccessOutput(BaseModel):
    """Output model for okta_api_revoke_access tool."""

    model_config = ConfigDict(extra="forbid")

    revoked: bool = Field(..., description="Whether access was successfully revoked")


class OktaRevokeAccessTool(Tool):
    """Tool for removing application access for an employee."""

    @property
    def name(self) -> str:
        return "okta_api_revoke_access"

    @property
    def description(self) -> str:
        return (
            "Revokes an employee's access to a specific application through Okta SSO. "
            "Covered systems: Slack, Confluence, Jira, Workday HRIS, VPN, Salesforce CRM, Tableau, "
            "GitHub, Quantivate, Actimize, Zoom, Splunk SIEM, Snowflake depersonalized, "
            "Snowflake raw replica, Admin Panel, Customer PII fields, AWS Production, Production database. "
            "Used for offboarding, role changes, or security-related access removal."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return OktaRevokeAccessInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return OktaRevokeAccessOutput

    async def run(
        self, db: InMemoryDatabase, request: OktaRevokeAccessInput
    ) -> OktaRevokeAccessOutput:
        """Revoke Okta application access."""
        # Get employee by email
        all_employees = db.get_all(Employee)
        employees = [e for e in all_employees if e.email == request.email]

        if not employees:
            raise Tool.ExecutionError(f"Employee not found: {request.email}")

        employee = employees[0]

        # Find active access to revoke
        all_accesses = db.get_all(OktaAppAccess)
        active_accesses = [
            a
            for a in all_accesses
            if a.employee_id == employee.id
            and a.app_name == request.app_name
            and a.is_active
        ]

        if not active_accesses:
            raise Tool.ExecutionError(
                f"No active access found to revoke for application: {request.app_name}"
            )

        # Revoke the access
        access = active_accesses[0]
        access.is_active = False

        # Save updated record
        db.update(access)

        return OktaRevokeAccessOutput(revoked=True)
