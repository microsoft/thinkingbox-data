# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for provisioning application access via Okta SSO."""

from typing import Any, Dict, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.okta.models import (
    AccessType,
    ApplicationAccessLog,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    get_schema_without_refs,
)
from pydantic import BaseModel, ConfigDict, Field


class OktaProvisionAccessInput(BaseModel):
    """Input for okta_provision_access tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    email: str = Field(
        ...,
        description="Employee email address",
        examples=["john@msg.com"],
    )
    app_name: str = Field(
        ...,
        description="Application name to provision access for",
        examples=["Tableau"],
    )
    access_type: Optional[AccessType] = Field(
        None,
        description="Access type (full_access, read_only, contributor, admin). Defaults to full_access if not specified",
        examples=["full_access"],
    )


class OktaProvisionAccessOutput(BaseModel):
    """Output for okta_provision_access tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    success: bool = Field(..., description="Indicates if provisioning was successful")


class OktaProvisionAccessTool(Tool):
    """Tool implementation for provisioning application access via Okta SSO."""

    @property
    def name(self) -> str:
        return "provision_access"

    @property
    def description(self) -> str:
        return (
            "Provision application access for a user in the identity management system. "
            "Grants or modifies user access to applications via single sign-on. "
            "Use after license allocation to grant actual application access. "
            "Always pair with license_management_api to ensure license is allocated before provisioning."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(OktaProvisionAccessInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(OktaProvisionAccessOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return OktaProvisionAccessInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return OktaProvisionAccessOutput

    async def run(
        self, db: InMemoryDatabase, request: OktaProvisionAccessInput
    ) -> OktaProvisionAccessOutput:
        """Provision application access for a user."""
        try:
            # Default access_type to full_access if not specified
            access_type = request.access_type or AccessType.FULL_ACCESS

            # Get all existing access logs to determine next ID
            existing_logs = db.get_all(ApplicationAccessLog)

            # Generate deterministic ID
            PREFIX_FOR_NEW_IDS = "AAL-2"
            count = 0
            existing_ids = {log.id for log in existing_logs}

            while True:
                new_id = f"{PREFIX_FOR_NEW_IDS}-{count:06d}"
                if new_id not in existing_ids:
                    break
                count += 1

            # Create new access log entry
            new_log = ApplicationAccessLog(
                id=new_id,
                employee_email=request.email,
                app_name=request.app_name,
                access_type=access_type,
            )

            # Insert into database
            db.create(new_log)

            return OktaProvisionAccessOutput(success=True)

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to provision access: {str(e)}"
            raise Tool.ExecutionError(error_message)
