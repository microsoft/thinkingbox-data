# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Email Notification - Send Notification Tool."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sandbox_servers.toolslib.sandbox_neobank_support.main.models import (
    EmailDeliveryStatus,
    EmailNotification,
    EmailPriority,
    Employee,
    NotificationType,
)
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

FIXED_CURRENT_TIME = datetime(2025, 12, 18, 10, 0, 0, tzinfo=timezone.utc)


class EmailNotificationSendNotificationInput(BaseModel):
    """Input model for email notification send notification."""

    model_config = ConfigDict(extra="forbid")

    recipient_email: str = Field(
        ..., description="Recipient employee email", examples=["sarah.jones@vdb.com"]
    )
    notification_type: NotificationType = Field(
        ..., description="Type of notification", examples=["post_facto_manager_alert"]
    )
    subject: str = Field(
        ...,
        description="Email subject line",
        examples=["SEV1 Incident Access Granted: Production DB access for John Smith"],
    )
    body: str = Field(
        ...,
        description="Email body content",
        examples=[
            "John Smith (Product Engineering) was granted temporary production database read-only access for SEV1 incident INC-0001234."
        ],
    )
    ticket_id: Optional[str] = Field(
        None, description="Associated ticket ID", examples=["TCK-00012345"]
    )
    priority: Optional[EmailPriority] = Field(
        None, description="Email priority level", examples=["urgent"]
    )
    cc_emails: Optional[str] = Field(
        None,
        description="CC email addresses as comma-separated string with no spaces (e.g., 'email1@example.com,email2@example.com')",
        examples=["it.support@vdb.com,security@vdb.com"],
    )


class EmailNotificationSendNotificationOutput(BaseModel):
    """Output model for email notification send notification."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    notification_id: str = Field(
        ..., description="Unique notification identifier (format: NTF-########)"
    )
    delivery_status: EmailDeliveryStatus = Field(
        ..., description="Initial delivery status (queued, sent, failed)"
    )


class EmailNotificationSendNotificationTool(Tool):
    """Tool for sending email notifications to employees."""

    @property
    def name(self) -> str:
        return "email_notification_api_send_notification"

    @property
    def description(self) -> str:
        return "Send email notifications to VDB employees for support-related communications including access provisioning confirmations, incident notifications, post-facto manager alerts, and breaking glass alerts. All sent emails are logged for audit compliance."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(EmailNotificationSendNotificationInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(EmailNotificationSendNotificationOutput)

    @property
    def request_model(self) -> type[BaseModel]:
        return EmailNotificationSendNotificationInput

    @property
    def output_model(self) -> type[BaseModel]:
        return EmailNotificationSendNotificationOutput

    async def run(
        self, db: InMemoryDatabase, request: EmailNotificationSendNotificationInput
    ) -> EmailNotificationSendNotificationOutput:
        """Send an email notification."""
        # Validate recipient exists
        all_employees = db.get_all(Employee)
        recipients = [e for e in all_employees if e.email == request.recipient_email]

        if not recipients:
            raise Tool.ExecutionError(
                f"Recipient email not found in employee directory: {request.recipient_email}"
            )

        recipient = recipients[0]

        # Check if recipient is active
        if recipient.employment_status not in ["active", "on_leave"]:
            raise Tool.ExecutionError(
                f"Recipient is inactive or on extended leave; notification not sent: {request.recipient_email}"
            )

        # Generate new notification ID
        all_existing = db.get_all(EmailNotification)
        next_id = len(all_existing) + 1
        notification_id = f"NTF-{next_id:08d}"

        # Set default priority if not provided
        priority = request.priority if request.priority else EmailPriority.NORMAL

        # Parse cc_emails from comma-separated string to list
        cc_emails_list = None
        if request.cc_emails:
            cc_emails_list = [email.strip() for email in request.cc_emails.split(",")]

        # Create new email notification (sent_at is now optional)
        new_notification = EmailNotification(
            id=notification_id,
            recipient_id=recipient.id,
            recipient_email=request.recipient_email,
            notification_type=request.notification_type,
            subject=request.subject,
            body=request.body,
            ticket_id=request.ticket_id,
            priority=priority,
            cc_emails=cc_emails_list,
            sent_at=None,
            delivery_status=EmailDeliveryStatus.QUEUED,
            delivered_at=None,
            sent_by="system",
        )

        db.create(new_notification)

        return EmailNotificationSendNotificationOutput(
            notification_id=notification_id, delivery_status=EmailDeliveryStatus.QUEUED
        )
