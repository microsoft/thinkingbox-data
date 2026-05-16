# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Zendesk MCP server."""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, ClassVar, Dict, List, Optional

from ms_toloka_servers.utils.sandbox_tools_system import UnstableField
from pydantic import BaseModel, Field


class TableName(str, Enum):
    """Zendesk table names."""

    ACTIVITIES = "activities"
    ARTICLES = "articles"
    GROUPS = "groups"
    GROUP_MEMBERSHIPS = "group_memberships"
    ORGANIZATIONS = "organizations"
    REQUESTS = "requests"
    SATISFACTION_RATINGS = "satisfaction_ratings"
    SESSIONS = "sessions"
    TAGS = "tags"
    TARGETS = "targets"
    TICKETS = "tickets"
    TICKET_AUDITS = "ticket_audits"
    TICKET_COMMENTS = "ticket_comments"
    TICKET_FIELDS = "ticket_fields"
    TICKET_METRICS = "ticket_metrics"
    TRIGGERS = "triggers"
    USERS = "users"
    VIEWS = "views"
    # Legacy
    COMMENTS = "comments"


# Tables supported for CRUD operations
SUPPORTED_CRUD_TABLES = {
    TableName.TICKETS,
    TableName.USERS,
    TableName.ORGANIZATIONS,
    TableName.COMMENTS,
    TableName.TICKET_COMMENTS,
}


class TicketStatus(str, Enum):
    """Zendesk ticket status values."""

    NEW = "new"
    OPEN = "open"
    PENDING = "pending"
    HOLD = "hold"
    SOLVED = "solved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Zendesk ticket priority values."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TicketType(str, Enum):
    """Zendesk ticket type values."""

    PROBLEM = "problem"
    INCIDENT = "incident"
    QUESTION = "question"
    TASK = "task"


class Ticket(BaseModel):
    """Zendesk ticket model."""

    table_name: ClassVar[str] = "tickets"

    id: str = Field(..., description="Unique identifier for the ticket")
    subject: Annotated[str, UnstableField()] = Field(
        ...,
        description="Subject of the ticket (excluded from test case validation)",
        min_length=1,
    )
    description: Annotated[Optional[str], UnstableField()] = Field(
        None,
        description="Description of the ticket (excluded from test case validation)",
    )
    status: TicketStatus = Field(
        default=TicketStatus.NEW, description="Status of the ticket"
    )
    priority: Optional[TicketPriority] = Field(
        None, description="Priority of the ticket"
    )
    type: Optional[TicketType] = Field(None, description="Type of the ticket")
    requester_id: Optional[str] = Field(
        None, description="ID of the user who requested the ticket"
    )
    assignee_id: Optional[str] = Field(
        None, description="ID of the user assigned to the ticket"
    )
    organization_id: Optional[str] = Field(None, description="ID of the organization")
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with the ticket"
    )
    created_at: str = Field(..., description="Timestamp when the ticket was created")
    updated_at: str = Field(
        ..., description="Timestamp when the ticket was last updated"
    )
    due_at: Optional[str] = Field(
        None, description="Due date for the ticket (ISO 8601 format)"
    )
    request_category: Optional[str] = Field(
        None,
        description="Custom field for Request Category",
        examples=["Claims", "Policy Servicing"],
    )
    claims_action_type: Optional[str] = Field(
        None,
        description="Custom field for Claims Action Type",
        examples=["FNOL – Collision"],
    )
    effective_date_of_change: Optional[str] = Field(
        None,
        description="Custom field for Effective Date of Change",
        examples=["2025-01-14"],
    )
    internal_review_type: Optional[str] = Field(
        None,
        description="Custom field for Internal Review Type",
        examples=["Underwriting", "Not Required"],
    )
    outcome_summary: Optional[str] = Field(
        None, description="Custom field for Outcome Summary", examples=["Completed"]
    )
    escalation_level: Optional[str] = Field(
        None, description="Custom field for Escalation Level", examples=["Standard"]
    )
    user_type: Optional[str] = Field(
        None,
        description="Type of user creating the ticket",
        examples=["Named Insured", "Third-Party Claimant"],
    )

    def get_id(self) -> str:
        """Return the unique identifier for this ticket."""
        return self.id


class TicketStatusViolation(BaseModel):
    """Record of ticket creation with incorrect status (not 'open')."""

    table_name: ClassVar[str] = "ticket_status_violations"

    id: str = Field(..., description="Unique identifier for the violation record")
    ticket_id: str = Field(..., description="ID of the ticket that was created")
    created_status: TicketStatus = Field(
        ..., description="The status used when creating the ticket"
    )
    created_at: str = Field(
        ..., description="Timestamp when the violation was recorded"
    )

    def get_id(self) -> str:
        """Return the unique identifier for this violation."""
        return self.id


class UserRole(str, Enum):
    """Zendesk user role values."""

    END_USER = "end-user"
    AGENT = "agent"
    ADMIN = "admin"


class User(BaseModel):
    """Zendesk user model."""

    table_name: ClassVar[str] = "users"

    id: str = Field(..., description="Unique identifier for the user")
    name: str = Field(..., description="Name of the user", min_length=1)
    email: str = Field(..., description="Email address of the user")
    role: UserRole = Field(default=UserRole.END_USER, description="Role of the user")
    organization_id: Optional[str] = Field(
        None, description="ID of the organization the user belongs to"
    )
    phone: Optional[str] = Field(None, description="Phone number of the user")
    verified: bool = Field(default=False, description="Whether the user is verified")
    active: bool = Field(default=True, description="Whether the user is active")
    created_at: Annotated[str, UnstableField()] = Field(
        ...,
        description="Timestamp when the user was created (excluded from test case validation)",
    )
    updated_at: Annotated[str, UnstableField()] = Field(
        ...,
        description="Timestamp when the user was last updated (excluded from test case validation)",
    )

    def get_id(self) -> str:
        """Return the unique identifier for this user."""
        return self.id


class Organization(BaseModel):
    """Zendesk organization model."""

    table_name: ClassVar[str] = "organizations"

    id: str = Field(..., description="Unique identifier for the organization")
    name: str = Field(..., description="Name of the organization", min_length=1)
    domain_names: List[str] = Field(
        default_factory=list,
        description="Domain names associated with the organization",
    )
    details: Optional[str] = Field(None, description="Details about the organization")
    notes: Optional[str] = Field(None, description="Notes about the organization")
    created_at: Annotated[str, UnstableField()] = Field(
        ...,
        description="Timestamp when the organization was created (excluded from test case validation)",
    )
    updated_at: Annotated[str, UnstableField()] = Field(
        ...,
        description="Timestamp when the organization was last updated (excluded from test case validation)",
    )

    def get_id(self) -> str:
        """Return the unique identifier for this organization."""
        return self.id


class Comment(BaseModel):
    """Zendesk ticket comment model."""

    table_name: ClassVar[str] = "comments"

    id: str = Field(..., description="Unique identifier for the comment")
    ticket_id: str = Field(..., description="ID of the ticket this comment belongs to")
    author_id: str = Field(..., description="ID of the user who authored the comment")
    body: str = Field(..., description="Body content of the comment", min_length=1)
    public: bool = Field(default=True, description="Whether the comment is public")
    created_at: Annotated[str, UnstableField()] = Field(
        ...,
        description="Timestamp when the comment was created (excluded from test case validation)",
    )

    def get_id(self) -> str:
        """Return the unique identifier for this comment."""
        return self.id


class Article(BaseModel):
    """Zendesk help center article model."""

    table_name: ClassVar[str] = "articles"

    id: int = Field(..., description="Unique identifier for the article")
    url: str = Field(..., description="API URL of the article")
    html_url: str = Field(..., description="Help Center URL of the article")
    title: str = Field(..., description="Title of the article")
    body: str = Field(..., description="HTML body of the article")
    snippet: Optional[str] = Field(None, description="HTML snippet of the article")
    author_id: int = Field(..., description="ID of the article author")
    section_id: int = Field(..., description="ID of the section the article belongs to")
    category_id: Optional[int] = Field(
        None, description="ID of the category the article belongs to"
    )
    brand_id: Optional[int] = Field(
        None, description="ID of the brand the article belongs to"
    )
    locale: str = Field(..., description="Locale of the article")
    source_locale: str = Field(..., description="Source locale of the article")
    draft: bool = Field(default=False, description="Whether the article is a draft")
    promoted: bool = Field(default=False, description="Whether the article is promoted")
    position: int = Field(default=0, description="Position of the article in the list")
    vote_sum: int = Field(default=0, description="Sum of upvotes and downvotes")
    vote_count: int = Field(default=0, description="Total number of votes")
    comments_disabled: bool = Field(
        default=False, description="Whether comments are disabled"
    )
    outdated: bool = Field(default=False, description="Whether the article is outdated")
    outdated_locales: List[str] = Field(
        default_factory=list, description="Locales where article is outdated"
    )
    label_names: List[str] = Field(
        default_factory=list, description="Label names associated with the article"
    )
    content_tag_ids: List[str] = Field(
        default_factory=list, description="Content tag IDs attached to the article"
    )
    user_segment_id: Optional[int] = Field(
        None, description="User segment ID defining visibility"
    )
    permission_group_id: Optional[int] = Field(
        None, description="Permission group ID for editing"
    )
    created_at: Annotated[str, UnstableField()] = Field(
        ...,
        description="Timestamp when the article was created (excluded from test case validation)",
    )
    updated_at: Annotated[str, UnstableField()] = Field(
        ...,
        description="Timestamp when the article was last updated (excluded from test case validation)",
    )
    edited_at: Optional[str] = Field(
        None, description="Timestamp when the article was last edited"
    )
    result_type: str = Field(default="article", description="Type of result")

    def get_id(self) -> str:
        """Return the unique identifier for this article."""
        return str(self.id)


class TicketComment(BaseModel):
    """Zendesk ticket comment model (from ticket_comments table)."""

    table_name: ClassVar[str] = "ticket_comments"

    id: int = Field(..., description="Unique identifier for the ticket comment")
    ticket_id: int = Field(..., description="ID of the ticket this comment belongs to")
    author_id: int = Field(..., description="ID of the user who authored the comment")
    body: str = Field(..., description="Body content of the comment", min_length=1)
    html_body: Optional[str] = Field(None, description="HTML body of the comment")
    public: bool = Field(default=True, description="Whether the comment is public")
    created_at: Annotated[str, UnstableField()] = Field(
        ...,
        description="Timestamp when the comment was created (excluded from test case validation)",
    )
    ItemInternalId: Optional[str] = Field(None, description="Internal item ID (UUID)")
    key: Optional[str] = Field(
        None, description="Key field (typically same as id as string)"
    )

    def get_id(self) -> str:
        """Return the unique identifier for this ticket comment."""
        return str(self.id)


class Table(BaseModel):
    """Zendesk table metadata model."""

    Name: str = Field(..., description="Internal name of the table")
    DisplayName: str = Field(..., description="Display name of the table")

    def get_id(self) -> str:
        """Return the unique identifier for this table."""
        return self.Name
