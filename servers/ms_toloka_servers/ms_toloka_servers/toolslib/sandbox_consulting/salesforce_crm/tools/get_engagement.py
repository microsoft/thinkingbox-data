# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for retrieving engagement details from Salesforce CRM."""

from typing import Any, Dict, Optional, Type

from ms_toloka_servers.toolslib.sandbox_consulting.salesforce_crm.models import (
    SfEngagement,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class GetEngagementInput(BaseModel):
    """Input for salesforce_get_engagement tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    engagement_code: str = Field(
        ...,
        description="Unique engagement identifier",
        examples=["ENG-0012345"],
    )


class GetEngagementOutput(BaseModel):
    """Output for salesforce_get_engagement tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    engagement_code: str = Field(
        ..., description="Engagement identifier", examples=["ENG-0012345"]
    )
    client_id: str = Field(
        ..., description="Client identifier", examples=["CLT-0012345"]
    )
    engagement_manager_email: str = Field(
        ..., description="Engagement manager email", examples=["sarah.johnson@msg.com"]
    )
    status: str = Field(..., description="Engagement status", examples=["active"])
    start_date: str = Field(
        ..., description="Engagement start date", examples=["2024-01-15T00:00:00Z"]
    )
    end_date: Optional[str] = Field(
        None, description="Engagement end date", examples=["2024-12-31T00:00:00Z"]
    )


class GetEngagementTool(Tool):
    """Tool implementation for retrieving engagement details from Salesforce CRM."""

    @property
    def name(self) -> str:
        return "get_engagement"

    @property
    def description(self) -> str:
        return (
            "Retrieve engagement details from CRM. Fetches engagement information including "
            "client, engagement manager, status, and dates from the Salesforce CRM system. "
            "Use to validate engagement codes and retrieve client information for access requests."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetEngagementInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetEngagementOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetEngagementInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetEngagementOutput

    async def run(
        self, db: InMemoryDatabase, request: GetEngagementInput
    ) -> GetEngagementOutput:
        """Retrieve engagement details by engagement code."""
        try:
            # Get engagement by code
            engagement = db.get_by_id(SfEngagement, request.engagement_code)

            # If no engagement found, raise 404 error
            if not engagement:
                raise Tool.ExecutionError(
                    f"Engagement not found: {request.engagement_code}"
                )

            # Return engagement information
            return GetEngagementOutput(
                engagement_code=engagement.engagement_code,
                client_id=engagement.client_id,
                engagement_manager_email=engagement.engagement_manager_email,
                status=engagement.status.value,
                start_date=engagement.start_date.isoformat(),
                end_date=(
                    engagement.end_date.isoformat() if engagement.end_date else None
                ),
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve engagement details: {str(e)}"
            raise Tool.ExecutionError(error_message)
