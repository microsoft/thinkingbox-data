# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Delete item tool for Zendesk MCP server."""

from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
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


class DeleteItemInput(BaseModel):
    """Input model for delete_item tool."""

    table: TableName = Field(
        ...,
        description="Zendesk item type (table name) from which to delete the item. Note: ticket_comments cannot be deleted.",
        examples=["tickets", "users", "organizations", "comments"],
    )
    id: str = Field(
        ...,
        description="Unique identifier of the item to delete.",
        examples=["12345", "1", "999999999"],
    )


class DeleteItemOutput(BaseModel):
    """Output model for delete_item tool."""

    model_config = ConfigDict(extra="forbid")

    success: bool = Field(..., description="Indicates if the deletion was successful.")


class DeleteItemTool(Tool):
    """Tool for deleting items from Zendesk tables."""

    @property
    def name(self) -> str:
        return "delete_item"

    @property
    def description(self) -> str:
        return (
            "Removes an existing item from a Zendesk table, such as tickets, users, or organizations, using its unique identifier. "
            "This operation is crucial for business processes requiring removal of data, such as resolving or cleaning up outdated "
            "support tickets or user records. The operation requires both the table name and the item id, and upon success, the item "
            "is removed from the system."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return DeleteItemInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return DeleteItemOutput

    async def run(
        self, db: InMemoryDatabase, request: DeleteItemInput
    ) -> DeleteItemOutput:
        """Delete an item from the specified Zendesk table."""
        # Check if table is supported for CRUD operations
        if request.table not in SUPPORTED_CRUD_TABLES:
            raise Tool.ExecutionError(
                f"Unsupported table: '{request.table.value}'. Only tickets, users, organizations, comments, and ticket_comments are supported."
            )

        # Check if table supports deletion
        if request.table == TableName.TICKET_COMMENTS:
            raise Tool.ExecutionError(
                "The value is not updatable. Ticket comments cannot be deleted."
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

        # Try to get the item
        item = db.get_by_id(model_class, request.id)

        if item is None:
            raise Tool.ExecutionError(
                f"Item with ID '{request.id}' not found in table '{request.table}'"
            )

        # Delete the item
        db.delete(item)

        return DeleteItemOutput(success=True)
