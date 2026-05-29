# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Create item tool for Zendesk MCP server."""

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
    EscalationReason,
    Organization,
    RequestTypeDetail,
    ResolutionAction,
    TableName,
    Ticket,
    TicketComment,
    TicketPriority,
    TicketStatus,
    TicketType,
    User,
    UserRole,
)

_IGNORED_TICKET_TAGS_LOWER = {
    "vip-customer",
    "repeat-issue",
    "hotel-partner-escalation",
}


def _normalize_ticket_tags(tags: Any) -> List[str]:
    """Filter ignored tags (case-insensitive) and sort for stable storage.

    Keeps original tag case and does not deduplicate.
    """
    if tags is None:
        return []
    if not isinstance(tags, list):
        return []
    filtered: List[str] = []
    for t in tags:
        if isinstance(t, str) and t.lower() not in _IGNORED_TICKET_TAGS_LOWER:
            filtered.append(t)
    filtered.sort(key=lambda s: (s.lower(), s))
    return filtered


class TicketCreateInput(BaseModel):
    """Input schema for creating a ticket."""

    subject: str = Field(
        ...,
        description="Subject of the ticket",
        min_length=1,
        examples=["Printer not working"],
    )
    description: Optional[str] = Field(
        None,
        description="Description of the ticket",
        examples=["Office printer stopped responding"],
    )
    status: Optional[TicketStatus] = Field(
        None, description="Status of the ticket", examples=["open"]
    )
    priority: Optional[TicketPriority] = Field(
        None, description="Priority of the ticket", examples=["high"]
    )
    type: Optional[TicketType] = Field(
        None, description="Type of the ticket", examples=["problem"]
    )
    requester_id: Optional[str] = Field(
        None, description="ID of the user who requested the ticket", examples=["1"]
    )
    assignee_id: Optional[str] = Field(
        None, description="ID of the user assigned to the ticket", examples=["2"]
    )
    organization_id: Optional[str] = Field(
        None, description="ID of the organization", examples=["1"]
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Tags associated with the ticket",
        examples=[["printer", "hardware"]],
    )
    due_at: Optional[str] = Field(
        None,
        description="Due date for the ticket (ISO 8601 format)",
        examples=["2025-01-20T17:00:00Z"],
    )
    # Booking domain custom fields
    booking_reference: Optional[str] = Field(
        None, description="Reference ID for the booking", examples=["BKG-12345678"]
    )
    hotel_id: Optional[str] = Field(
        None, description="ID of the hotel", examples=["HTL-87654321"]
    )
    check_in_date: Optional[str] = Field(
        None,
        description="Check-in date for the booking (ISO 8601 format)",
        examples=["2025-01-15T14:00:00Z"],
    )
    booking_value: Optional[float] = Field(
        None, description="Monetary value of the booking", examples=[1250.00]
    )
    request_type_detail: Optional[RequestTypeDetail] = Field(
        None, description="Detailed type of booking request", examples=["modify-dates"]
    )
    corporate_account_id: Optional[str] = Field(
        None, description="ID of the corporate account", examples=["CRP-12345678"]
    )
    group_booking_id: Optional[str] = Field(
        None, description="ID of the group booking", examples=["GRP-12345678"]
    )
    resolution_action: Optional[ResolutionAction] = Field(
        None,
        description="Action taken to resolve the ticket",
        examples=["refund-partial"],
    )
    refund_amount: Optional[float] = Field(
        None, description="Amount refunded to customer", examples=[250.00]
    )
    escalation_reason: Optional[EscalationReason] = Field(
        None,
        description="Reason for escalation",
        examples=["hotel-confirmation-required"],
    )


class UserCreateInput(BaseModel):
    """Input schema for creating a user."""

    name: str = Field(
        ..., description="Name of the user", min_length=1, examples=["John Doe"]
    )
    email: str = Field(
        ..., description="Email address of the user", examples=["john.doe@example.com"]
    )
    role: Optional[UserRole] = Field(
        None, description="Role of the user", examples=["end-user"]
    )
    organization_id: Optional[str] = Field(
        None, description="ID of the organization the user belongs to", examples=["1"]
    )
    phone: Optional[str] = Field(
        None, description="Phone number of the user", examples=["+1-555-0101"]
    )
    verified: Optional[bool] = Field(
        None, description="Whether the user is verified", examples=[True]
    )
    active: Optional[bool] = Field(
        None, description="Whether the user is active", examples=[True]
    )


class OrganizationCreateInput(BaseModel):
    """Input schema for creating an organization."""

    name: str = Field(
        ...,
        description="Name of the organization",
        min_length=1,
        examples=["Example Corporation"],
    )
    domain_names: Optional[List[str]] = Field(
        None,
        description="Domain names associated with the organization",
        examples=[["example.com"]],
    )
    details: Optional[str] = Field(
        None,
        description="Details about the organization",
        examples=["Main support organization"],
    )
    notes: Optional[str] = Field(
        None, description="Notes about the organization", examples=["Premium customer"]
    )


class CommentCreateInput(BaseModel):
    """Input schema for creating a comment."""

    ticket_id: str = Field(
        ..., description="ID of the ticket this comment belongs to", examples=["1"]
    )
    author_id: str = Field(
        ..., description="ID of the user who authored the comment", examples=["2"]
    )
    body: str = Field(
        ...,
        description="Body content of the comment",
        min_length=1,
        examples=["I've checked the printer and it seems to be offline"],
    )
    public: Optional[bool] = Field(
        None, description="Whether the comment is public", examples=[True]
    )


class TicketCommentCreateInput(BaseModel):
    """Input schema for creating a ticket comment."""

    ticket_id: int = Field(
        ..., description="ID of the ticket this comment belongs to", examples=[1, 23]
    )
    author_id: int = Field(
        ...,
        description="ID of the user who authored the comment",
        examples=[22677105199388],
    )
    body: str = Field(
        ...,
        description="Body content of the comment",
        min_length=1,
        examples=["Testing request creation"],
    )
    html_body: Optional[str] = Field(
        None,
        description="HTML body of the comment",
        examples=[
            '<div class="zd-comment" dir="auto"><p dir="auto">Testing request creation</p></div>'
        ],
    )
    public: Optional[bool] = Field(
        None, description="Whether the comment is public", examples=[True]
    )
    ItemInternalId: Optional[str] = Field(
        None,
        description="Internal item ID (UUID)",
        examples=["123d7175-2bb9-41d9-9131-d5f2e57af9f7"],
    )


class CreateItemInput(BaseModel):
    """Input model for create_item tool."""

    table: TableName = Field(
        ...,
        description="Zendesk item type (table name) to create the item in.",
        examples=["tickets", "users", "organizations", "comments", "ticket_comments"],
    )
    item: Union[
        TicketCreateInput,
        UserCreateInput,
        OrganizationCreateInput,
        CommentCreateInput,
        TicketCommentCreateInput,
    ] = Field(
        ...,
        description="The item to create. The structure depends on the table type.",
        examples=[
            {
                "subject": "Printer not working",
                "priority": "high",
                "description": "Printer stopped responding.",
            }
        ],
    )


class CreateItemOutput(BaseModel):
    """Output model for create_item tool."""

    model_config = ConfigDict(extra="forbid")

    item: Dict[str, Any] = Field(
        ...,
        description="Details of the created item, with fields based on the table schema.",
    )


class CreateItemTool(Tool):
    """Tool for creating items in Zendesk tables."""

    @property
    def name(self) -> str:
        return "create_item"

    @property
    def description(self) -> str:
        return (
            "Creates a new item within a Zendesk table, such as tickets, users, or organizations, using provided item data. "
            "This function is essential for adding records to Zendesk, enabling business workflows such as customer support "
            "ticket creation or user onboarding. The function requires the target table name and the item content and returns "
            "the created item's details. Item schema is dynamic depending on the chosen Zendesk table and should be validated accordingly."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return CreateItemInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CreateItemOutput

    async def run(
        self, db: InMemoryDatabase, request: CreateItemInput
    ) -> CreateItemOutput:
        """Create a new item in the specified Zendesk table."""
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

        # Get existing items to generate new ID
        existing_items = db.get_all(model_class)

        # Generate deterministic ID
        # For ticket_comments, use large numeric IDs like in real system
        if request.table == TableName.TICKET_COMMENTS:
            base_id = 23118465221916
            new_id = base_id + len(existing_items)
        else:
            new_id = str(len(existing_items) + 1)

        # Convert item to dict
        item_data = request.item.model_dump(exclude_unset=True)
        item_data["id"] = new_id

        # Booking domain: preserve original tags for output, but store normalized tags in DB
        original_tags = None
        if request.table == TableName.TICKETS:
            original_tags = item_data.get("tags")

        # Booking domain: normalize refund_amount for ticket creation
        # Treat missing/null/None/0 as 0.0 so the table never stores None
        if request.table == TableName.TICKETS:
            refund_amount = item_data.get("refund_amount", None)
            if refund_amount is None:
                item_data["refund_amount"] = 0.0
            else:
                # Canonicalize zero-ish values to float 0.0
                try:
                    if float(refund_amount) == 0.0:
                        item_data["refund_amount"] = 0.0
                except (TypeError, ValueError):
                    # If something unexpected comes through, fall back to 0.0
                    item_data["refund_amount"] = 0.0

        # Booking domain: normalize tags for ticket creation
        if request.table == TableName.TICKETS:
            item_data["tags"] = _normalize_ticket_tags(item_data.get("tags"))

        # Handle None values for list fields - convert to empty lists
        # This ensures compatibility when clients explicitly pass null for optional list fields
        list_fields_by_table = {
            TableName.TICKETS: ["tags"],
            TableName.ORGANIZATIONS: ["domain_names"],
            TableName.COMMENTS: [],
            TableName.TICKET_COMMENTS: [],
            TableName.USERS: [],
        }

        for field_name in list_fields_by_table.get(request.table, []):
            if field_name in item_data and item_data[field_name] is None:
                item_data[field_name] = []

        # Add timestamps if not present
        # Always use fixed timestamp instead of real-time
        fixed_time = "2025-10-01T13:00:05Z"
        if "created_at" not in item_data:
            item_data["created_at"] = fixed_time
        if "updated_at" not in item_data and request.table != TableName.TICKET_COMMENTS:
            item_data["updated_at"] = fixed_time

        # For ticket_comments, add key field if not present
        if request.table == TableName.TICKET_COMMENTS:
            if "key" not in item_data:
                item_data["key"] = str(new_id)
            # Generate html_body if not provided
            if "html_body" not in item_data and "body" in item_data:
                item_data["html_body"] = (
                    f'<div class="zd-comment" dir="auto"><p dir="auto">{item_data["body"]}</p></div>'
                )

        # Create the new item
        try:
            new_item = model_class(**item_data)
        except Exception as e:
            raise Tool.ExecutionError(f"Failed to create item: {str(e)}")

        # Save to database
        db.create(new_item)

        # Return the created item as dict, with original tags if they were provided
        output_data = new_item.model_dump()
        if request.table == TableName.TICKETS and original_tags is not None:
            # Return original unfiltered tags in output, even though DB has filtered tags
            output_data["tags"] = (
                original_tags if isinstance(original_tags, list) else []
            )

        return CreateItemOutput(item=output_data)
