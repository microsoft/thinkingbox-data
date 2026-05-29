# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Update item tool for Zendesk MCP server."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import (
    SUPPORTED_CRUD_TABLES,
    Comment,
    Organization,
    TableName,
    Ticket,
    TicketComment,
    TicketPriority,
    TicketStatus,
    TicketType,
    User,
    UserRole,
)


class TicketUpdateInput(BaseModel):
    """Input schema for updating a ticket."""

    subject: Optional[str] = Field(
        None,
        description="Subject of the ticket",
        min_length=1,
        examples=["Updated printer issue"],
    )
    description: Optional[str] = Field(
        None,
        description="Description of the ticket",
        examples=["Printer now completely unresponsive"],
    )
    status: Optional[TicketStatus] = Field(
        None, description="Status of the ticket", examples=["solved"]
    )
    priority: Optional[TicketPriority] = Field(
        None, description="Priority of the ticket", examples=["urgent"]
    )
    type: Optional[TicketType] = Field(
        None, description="Type of the ticket", examples=["problem"]
    )
    requester_id: Optional[str] = Field(
        None, description="ID of the user who requested the ticket", examples=["1"]
    )
    assignee_id: Optional[str] = Field(
        None, description="ID of the user assigned to the ticket", examples=["3"]
    )
    organization_id: Optional[str] = Field(
        None, description="ID of the organization", examples=["2"]
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Tags associated with the ticket",
        examples=[["printer", "hardware", "urgent"]],
    )
    due_at: Optional[str] = Field(
        None,
        description="Due date for the ticket (ISO 8601 format)",
        examples=["2025-01-25T17:00:00Z"],
    )
    request_category: Optional[str] = Field(
        None, description="Custom fields for Request Category", examples=["Claims"]
    )
    claims_action_type: Optional[str] = Field(
        None,
        description="Custom fields for Claims Action Type",
        examples=["FNOL – Collision"],
    )
    effective_date_of_change: Optional[str] = Field(
        None,
        description="Custom fields for Effective Date of Change",
        examples=["2025-01-14"],
    )
    internal_review_type: Optional[str] = Field(
        None,
        description="Custom fields for Internal Review Type",
        examples=["Underwriting"],
    )
    outcome_summary: Optional[str] = Field(
        None, description="Custom fields for Outcome Summary", examples=["Completed"]
    )
    escalation_level: Optional[str] = Field(
        None, description="Custom fields for Escalation Level", examples=["Standard"]
    )
    user_type: Optional[str] = Field(
        None,
        description="Type of user creating the ticket",
        examples=["Named Insured", "Third-Party Claimant"],
    )


class UserUpdateInput(BaseModel):
    """Input schema for updating a user."""

    name: Optional[str] = Field(
        None, description="Name of the user", min_length=1, examples=["Jane Doe"]
    )
    email: Optional[str] = Field(
        None, description="Email address of the user", examples=["jane.doe@example.com"]
    )
    role: Optional[UserRole] = Field(
        None, description="Role of the user", examples=["agent"]
    )
    organization_id: Optional[str] = Field(
        None, description="ID of the organization the user belongs to", examples=["2"]
    )
    phone: Optional[str] = Field(
        None, description="Phone number of the user", examples=["+1-555-0102"]
    )
    verified: Optional[bool] = Field(
        None, description="Whether the user is verified", examples=[True]
    )
    active: Optional[bool] = Field(
        None, description="Whether the user is active", examples=[False]
    )


class OrganizationUpdateInput(BaseModel):
    """Input schema for updating an organization."""

    name: Optional[str] = Field(
        None,
        description="Name of the organization",
        min_length=1,
        examples=["Updated Corporation"],
    )
    domain_names: Optional[List[str]] = Field(
        None,
        description="Domain names associated with the organization",
        examples=[["example.com", "example.net"]],
    )
    details: Optional[str] = Field(
        None,
        description="Details about the organization",
        examples=["Updated organization details"],
    )
    notes: Optional[str] = Field(
        None, description="Notes about the organization", examples=["VIP customer"]
    )


class CommentUpdateInput(BaseModel):
    """Input schema for updating a comment."""

    ticket_id: Optional[str] = Field(
        None, description="ID of the ticket this comment belongs to", examples=["2"]
    )
    author_id: Optional[str] = Field(
        None, description="ID of the user who authored the comment", examples=["3"]
    )
    body: Optional[str] = Field(
        None,
        description="Body content of the comment",
        min_length=1,
        examples=["Updated comment: Issue has been resolved"],
    )
    public: Optional[bool] = Field(
        None, description="Whether the comment is public", examples=[False]
    )


class UpdateItemInput(BaseModel):
    """Input model for update_item tool."""

    table: TableName = Field(
        ...,
        description="Zendesk item type (table name) containing the item to update. Note: ticket_comments cannot be modified.",
        examples=["tickets", "users", "organizations", "comments"],
    )
    id: str = Field(
        ...,
        description="Unique identifier of the item to update.",
        examples=["12345", "1"],
    )
    item: Union[
        TicketUpdateInput, UserUpdateInput, OrganizationUpdateInput, CommentUpdateInput
    ] = Field(
        ...,
        description="Fields and values to update in the item. The structure depends on the table type. Only provided fields will be updated.",
        examples=[{"priority": "urgent", "status": "solved"}],
    )


class UpdateItemOutput(BaseModel):
    """Output model for update_item tool."""

    model_config = ConfigDict(extra="forbid")

    item: Dict[str, Any] = Field(
        ...,
        description="Details of the updated item, with all fields after modification.",
    )


class UpdateItemTool(Tool):
    """Tool for updating existing items in Zendesk tables."""

    @property
    def name(self) -> str:
        return "update_item"

    @property
    def description(self) -> str:
        return (
            "Modifies the data for an existing item in a Zendesk table by applying updated field values. "
            "This function is used for ticket editing, user data changes, or other record updates as part of "
            "business workflows. Requires the target table name, item id, and the new item data; returns the "
            "updated item. Supports partial updates based on provided fields in the item payload."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return UpdateItemInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return UpdateItemOutput

    async def run(
        self, db: InMemoryDatabase, request: UpdateItemInput
    ) -> UpdateItemOutput:
        """Update an existing item in the specified Zendesk table."""
        # Check if table is supported for CRUD operations
        if request.table not in SUPPORTED_CRUD_TABLES:
            raise Tool.ExecutionError(
                f"Unsupported table: '{request.table.value}'. Only tickets, users, organizations, comments, and ticket_comments are supported."
            )

        # Check if table supports updates
        if request.table == TableName.TICKET_COMMENTS:
            raise Tool.ExecutionError(
                "The value is not updatable. Ticket comments cannot be modified."
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

        # Get the existing item
        existing_item = db.get_by_id(model_class, request.id)

        if existing_item is None:
            raise Tool.ExecutionError(
                f"Item with ID '{request.id}' not found in table '{request.table.value}'"
            )

        # Convert existing item to dict and update with new values
        updated_data = existing_item.model_dump()
        # Convert item to dict, excluding unset values for partial updates
        item_updates = request.item.model_dump(exclude_unset=True)

        # Handle None values: skip them to preserve existing values
        # When a client sends null for a field, it means "don't change this field"
        # This is critical for UI workflows where only changed fields are sent
        filtered_updates = {}
        for field_name, value in item_updates.items():
            if value is not None:
                filtered_updates[field_name] = value
            # If value is None, skip it entirely - keep existing value

        updated_data.update(filtered_updates)

        # Update the updated_at timestamp
        # Always use fixed timestamp instead of real-time
        # For tickets table, use a different timestamp to differentiate from creation time
        if request.table == TableName.TICKETS:
            updated_data["updated_at"] = "2025-10-01T13:00:10Z"
        else:
            updated_data["updated_at"] = "2025-10-01T13:00:05Z"

        # Create updated item
        try:
            updated_item = model_class(**updated_data)
        except Exception as e:
            raise Tool.ExecutionError(f"Failed to update item: {str(e)}")

        # Save to database
        db.update(updated_item)

        return UpdateItemOutput(item=updated_item.model_dump())
