# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Grant Okta application access tool."""

from datetime import datetime, timezone
from typing import Optional, Type

from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Employee, GenericAccessLevel, OktaAppAccess

# Fixed current time for deterministic behavior
FIXED_CURRENT_TIME = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)


class OktaProvisionAccessInput(BaseModel):
    """Input model for okta_api.provision_access tool."""

    email: str = Field(
        ..., description="Corporate email address", examples=["john.smith@vdb.com"]
    )
    app_name: str = Field(..., description="Application name", examples=["Salesforce"])
    access_level: GenericAccessLevel = Field(
        ..., description="Access level enum value", examples=["read_only"]
    )
    is_temporary: bool = Field(
        False, description="Whether this access is temporary", examples=[False]
    )
    access_expiry_date: Optional[str] = Field(
        None,
        description="Expiration date for temporary access in ISO 8601 format",
        examples=["2025-12-15T00:00:00Z"],
    )


class OktaProvisionAccessOutput(BaseModel):
    """Output model for okta_api.provision_access tool."""

    model_config = ConfigDict(extra="forbid")

    app_access_id: str = Field(
        ...,
        description="Unique identifier for the access record (format: OAA-########)",
    )


class OktaProvisionAccessTool(Tool):
    """Tool for granting application access to an employee via Okta SSO."""

    @property
    def name(self) -> str:
        return "okta_api_provision_access"

    @property
    def description(self) -> str:
        return (
            "Provisions access to a specified application for an employee through Okta. "
            "Covered systems and access levels: Slack (member), Confluence (user), Jira (user), "
            "Workday HRIS (standard), VPN (standard_employee), Salesforce CRM (user), Tableau (viewer), "
            "GitHub (read-only), GitHub (write), Quantivate (user), Actimize (user), Zoom (user), "
            "Workday HRIS (elevated), Splunk SIEM (user), VPN (engineer_prod), "
            "Snowflake depersonalized (viewer), Snowflake depersonalized (analyst), "
            "Snowflake raw replica (analyst), Admin Panel (read-only), Admin Panel (write non-PII only), "
            "Customer PII fields (read-only), AWS Production (user), Production database (read-only). "
            "Creates the appropriate SSO assignment with the specified access level."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return OktaProvisionAccessInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return OktaProvisionAccessOutput

    async def run(
        self, db: InMemoryDatabase, request: OktaProvisionAccessInput
    ) -> OktaProvisionAccessOutput:
        """Grant Okta application access."""
        # Get employee by email
        all_employees = db.get_all(Employee)
        employees = [e for e in all_employees if e.email == request.email]

        if not employees:
            raise Tool.ExecutionError(
                f"Employee not found in Okta directory: {request.email}"
            )

        employee = employees[0]

        # Check if employee already has active access to this application
        all_accesses = db.get_all(OktaAppAccess)
        existing_accesses = [
            a
            for a in all_accesses
            if a.employee_id == employee.id
            and a.app_name == request.app_name
            and a.is_active
        ]

        if existing_accesses:
            raise Tool.ExecutionError(
                f"Employee already has access to this application: {request.app_name}"
            )

        # Generate new access ID
        access_count = len(all_accesses)
        new_access_id = f"OAA-{access_count + 1:08d}"

        # Create new access record
        new_access = OktaAppAccess(
            id=new_access_id,
            employee_id=employee.id,
            app_name=request.app_name,
            access_level=request.access_level,
            granted_by="system",
            is_active=True,
            is_temporary=request.is_temporary,
            expires_at=request.access_expiry_date,
        )

        # Save to database
        db.create(new_access)

        return OktaProvisionAccessOutput(app_access_id=new_access_id)
