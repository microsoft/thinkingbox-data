# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get item tool for Zendesk MCP server."""

from typing import Any, Dict, Type

from ms_toloka_servers import InMemoryDatabase, Tool
from pydantic import BaseModel, ConfigDict, Field

from ..models import (
    SUPPORTED_CRUD_TABLES,
    Comment,
    Organization,
    TableName,
    Ticket,
    TicketComment,
    User,
)


class GetItemInput(BaseModel):
    """Input model for get_item tool."""

    table: TableName = Field(
        ...,
        description="Zendesk item type (table name) to query.",
        examples=["tickets", "users", "organizations", "comments", "ticket_comments"],
    )
    id: str = Field(
        ...,
        description="Unique identifier of the item to retrieve.",
        examples=["12345", "1", "999999999"],
    )


class GetItemOutput(BaseModel):
    """Output model for get_item tool."""

    model_config = ConfigDict(extra="forbid")

    item: Dict[str, Any] = Field(
        ...,
        description="Details of the retrieved item, with fields determined by the table's schema.",
    )


class GetItemTool(Tool):
    """Tool for retrieving a single item from Zendesk tables."""

    @property
    def name(self) -> str:
        return "get_item"

    @property
    def description(self) -> str:
        return (
            "Fetches the details of a single item from a specified Zendesk table using its unique identifier. "
            "Commonly used for viewing customer support ticket data, user profiles, or other records, this function "
            "enables business processes that require accessing individual item information. Requires both table name "
            "and item id, returning all available fields for the item."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetItemInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetItemOutput

    async def run(self, db: InMemoryDatabase, request: GetItemInput) -> GetItemOutput:
        """Retrieve a single item from the specified Zendesk table."""
        # Check if table is supported for CRUD operations
        if request.table not in SUPPORTED_CRUD_TABLES:
            raise Tool.ExecutionError(
                f"Unsupported table: '{request.table.value}'. Only tickets, users, organizations, comments, and ticket_comments are supported."
            )

        # Map table names to models
        table_map = {
            TableName.TICKETS: Ticket,
            TableName.USERS: User,
            TableName.ORGANIZATIONS: Organization,
            TableName.COMMENTS: Comment,
            TableName.TICKET_COMMENTS: TicketComment,
        }

        model_class = table_map[request.table]

        # Get the item
        item = db.get_by_id(model_class, request.id)

        if item is None:
            raise Tool.ExecutionError(
                f"Item with ID '{request.id}' not found in table '{request.table}'"
            )

        return GetItemOutput(item=item.model_dump())
