# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get tables tool for Zendesk MCP server."""

from typing import List, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class TableInfo(BaseModel):
    """Information about a Zendesk table."""

    Name: str = Field(..., description="Internal name of the table")
    DisplayName: str = Field(..., description="Display name of the table")


class GetTablesInput(BaseModel):
    """Input model for get_tables tool (no parameters required)."""

    pass


class GetTablesOutput(BaseModel):
    """Output model for get_tables tool."""

    model_config = ConfigDict(extra="forbid")

    value: List[TableInfo] = Field(
        ...,
        description="Array of available Zendesk tables, each with internal name and display name.",
    )


class GetTablesTool(Tool):
    """Tool for retrieving available Zendesk tables."""

    @property
    def name(self) -> str:
        return "get_tables"

    @property
    def description(self) -> str:
        return (
            "Returns a list of all Zendesk tables (such as tickets, users, organizations) supported by the site. "
            "This operation enables dynamic business logic by exposing available entity types for record operations, "
            "configuration, or reporting. The response includes both the internal table name and a display name for "
            "each table, allowing clients to present and select entity types."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetTablesInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetTablesOutput

    async def run(
        self, db: InMemoryDatabase, request: GetTablesInput
    ) -> GetTablesOutput:
        """Retrieve the list of available Zendesk tables."""

        # Define available tables (based on real Zendesk API response)
        tables = [
            TableInfo(Name="activities", DisplayName="Activities"),
            TableInfo(Name="articles", DisplayName="Articles"),
            TableInfo(Name="groups", DisplayName="Groups"),
            TableInfo(Name="group_memberships", DisplayName="Group Memberships"),
            TableInfo(Name="organizations", DisplayName="Organizations"),
            TableInfo(Name="requests", DisplayName="Requests"),
            TableInfo(Name="satisfaction_ratings", DisplayName="Satisfaction Ratings"),
            TableInfo(Name="sessions", DisplayName="Sessions"),
            TableInfo(Name="tags", DisplayName="Tags"),
            TableInfo(Name="targets", DisplayName="Targets"),
            TableInfo(Name="tickets", DisplayName="Tickets"),
            TableInfo(Name="ticket_audits", DisplayName="Ticket Audits"),
            TableInfo(Name="ticket_comments", DisplayName="Ticket Comments"),
            TableInfo(Name="ticket_fields", DisplayName="Ticket Fields"),
            TableInfo(Name="ticket_metrics", DisplayName="Ticket Metrics"),
            TableInfo(Name="triggers", DisplayName="Triggers"),
            TableInfo(Name="users", DisplayName="Users"),
            TableInfo(Name="views", DisplayName="Views"),
        ]

        return GetTablesOutput(value=tables)
