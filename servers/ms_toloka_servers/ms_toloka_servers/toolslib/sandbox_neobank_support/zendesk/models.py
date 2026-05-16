# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Zendesk MCP server."""

from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional

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


# === Custom Field Enums (from IMPLEMENTATION_DETAILS.md) ===


class Owner(str, Enum):
    """Team assignment for escalation."""

    IT_SUPPORT = "it_support"
    IT_OPS_TEAM = "it_ops_team"
    IT_INF_TEAM = "it_inf_team"
    IT_SEC_TEAM = "it_sec_team"
    OPS_TEAM = "ops_team"
    COMP_TEAM = "comp_team"
    ENGIN_TEAM = "engin_team"


class ResolutionCategory(str, Enum):
    """How the ticket was resolved."""

    PROVISIONED = "provisioned"
    APPROVED = "approved"
    DENIED = "denied"
    INFORMATION_PROVIDED = "information_provided"
    ESCALATED_IT_OPS = "escalated_it_ops"
    ESCALATED_IT_INF = "escalated_it_inf"
    ESCALATED_IT_SEC = "escalated_it_sec"
    ESCALATED_OPS = "escalated_ops"
    ESCALATED_COMPL = "escalated_compl"
    ESCALATED_ENGIN = "escalated_engin"
    BACKLOGGED = "backlogged"
    DUPLICATE = "duplicate"
    CANCELLED = "cancelled"
    RESOLVED_BY_REQUESTER = "resolved_by_requester"


class ApprovalRequired(str, Enum):
    """Whether approval is needed."""

    YES = "yes"
    NO = "no"


class ApprovalStatus(str, Enum):
    """Approval state."""

    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class IncidentSeverity(str, Enum):
    """Severity level."""

    SEV1_CRITICAL = "sev1_critical"
    SEV2_HIGH = "sev2_high"
    SEV3_MEDIUM = "sev3_medium"
    SEV4_LOW = "sev4_low"


class CustomerImpact(str, Enum):
    """Customer impact."""

    YES_ACTIVE = "yes_active"
    YES_POTENTIAL = "yes_potential"
    NO_IMPACT = "no_impact"


class Ticket(BaseModel):
    """Zendesk ticket model."""

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
    # All custom fields must be optional

    # Ticket Resolution & Categorization
    resolution_category: Optional[ResolutionCategory] = Field(
        None, description="How the ticket was resolved"
    )
    owner: Optional[Owner] = Field(None, description="Team assignment for escalation")

    # Access & Duration Fields
    access_expiry_date: Annotated[Optional[str], UnstableField()] = Field(
        None,
        description="When temporary access expires (ISO 8601 format, excluded from test case validation)",
    )

    # Approval Workflow
    approval_required: Optional[ApprovalRequired] = Field(
        None, description="Whether approval is needed"
    )
    approval_status: Optional[ApprovalStatus] = Field(
        None, description="Approval state"
    )
    approver_id: Optional[str] = Field(None, description="ID of the approver")
    approval_request_ids: Optional[str] = Field(
        None, description="Comma-separated approval request IDs for tracking"
    )
    business_justification: Annotated[Optional[str], UnstableField()] = Field(
        None,
        description="Business reason for the request (excluded from test case validation)",
    )

    # Incident Management
    incident_severity: Optional[IncidentSeverity] = Field(
        None, description="Severity level"
    )
    customer_impact: Optional[CustomerImpact] = Field(
        None, description="Customer impact"
    )

    # Asset & Hardware
    asset_id: Optional[str] = Field(None, description="Related hardware asset ID")

    def get_id(self) -> str:
        """Return the unique identifier for this ticket."""
        return self.id


class TicketStatusViolation(BaseModel):
    """Record of ticket creation with incorrect status (not 'open')."""

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
