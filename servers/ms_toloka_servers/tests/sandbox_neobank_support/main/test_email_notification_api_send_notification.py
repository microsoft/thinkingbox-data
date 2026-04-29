# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for Email Notification - Send Notification Tool."""

import pytest
from ms_toloka_servers.toolslib.sandbox_neobank_support.main.models import (
    EmailPriority,
    NotificationType,
)
from ms_toloka_servers.toolslib.sandbox_neobank_support.main.tools.email_notification_api_send_notification import (
    FIXED_CURRENT_TIME,
    EmailNotificationSendNotificationInput,
    EmailNotificationSendNotificationTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.mark.anyio
async def test_send_notification_post_facto_manager_alert(db: InMemoryDatabase):
    """Test sending post-facto manager alert notification (example from spec)."""
    tool = EmailNotificationSendNotificationTool()
    request = EmailNotificationSendNotificationInput(
        recipient_email="sarah.jones@vdb.com",
        notification_type=NotificationType.POST_FACTO_MANAGER_ALERT,
        subject="SEV1 Incident Access Granted: Production DB access for John Smith",
        body="John Smith was granted temporary production database access for SEV1 incident. Access expires in 24 hours.",
        ticket_id="TCK-00012345",
        priority=EmailPriority.URGENT,
    )

    result = await tool.run(db, request)

    assert result.notification_id.startswith("NTF-")
    assert result.delivery_status == "queued"


@pytest.mark.anyio
async def test_send_notification_access_provisioning(db: InMemoryDatabase):
    """Test sending access provisioning confirmation notification."""
    tool = EmailNotificationSendNotificationTool()
    request = EmailNotificationSendNotificationInput(
        recipient_email="marcus.thompson@vdb.com",
        notification_type=NotificationType.ACCESS_PROVISIONED,
        subject="AWS Access Granted",
        body="Your AWS production access request has been approved.",
        ticket_id="TCK-00012346",
    )

    result = await tool.run(db, request)

    assert result.notification_id.startswith("NTF-")
    assert result.delivery_status == "queued"


@pytest.mark.anyio
async def test_send_notification_breaking_glass_alert(db: InMemoryDatabase):
    """Test sending breaking glass alert notification."""
    tool = EmailNotificationSendNotificationTool()
    request = EmailNotificationSendNotificationInput(
        recipient_email="amanda.lee@vdb.com",
        notification_type=NotificationType.BREAKING_GLASS_ALERT,
        subject="Breaking Glass Access: Production Snowflake",
        body="Emergency access to production Snowflake warehouse was granted for incident INC-0001235.",
        ticket_id="TCK-00012347",
        priority=EmailPriority.URGENT,
        cc_emails="security@vdb.com,compliance@vdb.com",
    )

    result = await tool.run(db, request)

    assert result.notification_id.startswith("NTF-")
    assert result.delivery_status == "queued"


@pytest.mark.anyio
async def test_send_notification_hardware_assignment(db: InMemoryDatabase):
    """Test sending hardware assignment confirmation."""
    tool = EmailNotificationSendNotificationTool()
    request = EmailNotificationSendNotificationInput(
        recipient_email="maria.garcia@vdb.com",
        notification_type=NotificationType.HARDWARE_ASSIGNED,
        subject="Hardware Assignment: MacBook Pro 16",
        body="Your hardware request has been fulfilled. A MacBook Pro 16 has been assigned to you.",
        ticket_id="TCK-00012348",
        priority=EmailPriority.NORMAL,
    )

    result = await tool.run(db, request)

    assert result.notification_id.startswith("NTF-")
    assert result.delivery_status == "queued"


@pytest.mark.anyio
async def test_send_notification_escalation_notice(db: InMemoryDatabase):
    """Test sending escalation notice."""
    tool = EmailNotificationSendNotificationTool()
    request = EmailNotificationSendNotificationInput(
        recipient_email="jennifer.brown@vdb.com",
        notification_type=NotificationType.ESCALATION_NOTICE,
        subject="Ticket Escalation Required: High Priority Access Request",
        body="Ticket TCK-00012349 requires your immediate attention. The request has been pending for 48 hours.",
        ticket_id="TCK-00012349",
        priority=EmailPriority.URGENT,
        cc_emails="compliance@vdb.com",
    )

    result = await tool.run(db, request)

    assert result.notification_id.startswith("NTF-")
    assert result.delivery_status == "queued"


@pytest.mark.anyio
async def test_send_notification_without_ticket_id(db: InMemoryDatabase):
    """Test sending notification without ticket ID."""
    tool = EmailNotificationSendNotificationTool()
    request = EmailNotificationSendNotificationInput(
        recipient_email="alex.taylor@vdb.com",
        notification_type=NotificationType.TICKET_UPDATE,
        subject="System Maintenance Notification",
        body="Scheduled maintenance window this weekend from 2 AM to 6 AM UTC.",
        priority=EmailPriority.NORMAL,
    )

    result = await tool.run(db, request)

    assert result.notification_id.startswith("NTF-")
    assert result.delivery_status == "queued"


@pytest.mark.anyio
async def test_send_notification_default_priority(db: InMemoryDatabase):
    """Test sending notification with default priority (normal)."""
    tool = EmailNotificationSendNotificationTool()
    request = EmailNotificationSendNotificationInput(
        recipient_email="emma.wilson@vdb.com",
        notification_type=NotificationType.TICKET_UPDATE,
        subject="Account Update Confirmation",
        body="Your account settings have been updated successfully.",
    )

    result = await tool.run(db, request)

    assert result.notification_id.startswith("NTF-")
    assert result.delivery_status == "queued"


@pytest.mark.anyio
async def test_send_notification_recipient_not_found(db: InMemoryDatabase):
    """Test sending notification to non-existent employee."""
    tool = EmailNotificationSendNotificationTool()
    request = EmailNotificationSendNotificationInput(
        recipient_email="nonexistent@vdb.com",
        notification_type=NotificationType.TICKET_UPDATE,
        subject="Test Subject",
        body="Test Body",
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "Recipient email not found in employee directory" in str(exc_info.value)


@pytest.mark.anyio
async def test_send_notification_incremental_ids(db: InMemoryDatabase):
    """Test that notification IDs increment correctly."""
    tool = EmailNotificationSendNotificationTool()

    # Create first notification
    request1 = EmailNotificationSendNotificationInput(
        recipient_email="marcus.thompson@vdb.com",
        notification_type=NotificationType.TICKET_UPDATE,
        subject="Test Notification 1",
        body="Test body 1",
    )
    result1 = await tool.run(db, request1)

    # Create second notification
    request2 = EmailNotificationSendNotificationInput(
        recipient_email="maria.garcia@vdb.com",
        notification_type=NotificationType.TICKET_UPDATE,
        subject="Test Notification 2",
        body="Test body 2",
    )
    result2 = await tool.run(db, request2)

    # Extract numeric parts and verify increment
    id1_num = int(result1.notification_id.split("-")[-1])
    id2_num = int(result2.notification_id.split("-")[-1])
    assert id2_num == id1_num + 1
