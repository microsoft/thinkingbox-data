# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for escalate_to_hotel tool."""

import pytest
from ms_toloka_servers.toolslib.external_booking.booking_api.models import Booking
from ms_toloka_servers.toolslib.external_booking.hotel_partner_api.models import (
    EscalationReason,
)
from ms_toloka_servers.toolslib.external_booking.hotel_partner_api.tools.escalate_to_hotel import (
    EscalateToHotelInput,
    EscalateToHotelTool,
)
from ms_toloka_servers.toolslib.external_booking.zendesk.models import Ticket
from ms_toloka_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.mark.anyio
async def test_escalate_to_hotel_success(db: InMemoryDatabase):
    """Test successful escalation creation."""
    tool = EscalateToHotelTool()

    request = EscalateToHotelInput(
        hotel_id="HTL-00012345",
        booking_reference="BKG-00012345",
        issue_type=EscalationReason.SAME_DAY_MODIFICATION,
        description="Customer needs to change check-in time to 2 PM today",
    )

    result = await tool.run(db, request)

    assert result.escalation_ticket_id.startswith("ZDSK-")
    # Premium hotel uses escalation_contact when available
    assert result.hotel_contact_email == "director@grandplaza.com"
    assert result.hotel_contact_phone == "+1-212-738-4501"


@pytest.mark.anyio
async def test_escalate_to_hotel_uses_escalation_contact(db: InMemoryDatabase):
    """Test that escalation uses escalation_contact when available."""
    tool = EscalateToHotelTool()

    request = EscalateToHotelInput(
        hotel_id="HTL-00012345",
        booking_reference="BKG-00012345",
        issue_type=EscalationReason.GUEST_COMPLAINT,
        description="Guest complaint about room cleanliness",
    )

    result = await tool.run(db, request)

    # Should use escalation_contact if available (premium hotel has it)
    assert result.hotel_contact_email == "director@grandplaza.com"


@pytest.mark.anyio
async def test_escalate_to_hotel_sequential_ticket_ids(db: InMemoryDatabase):
    """Test that ticket IDs are generated sequentially."""
    tool = EscalateToHotelTool()

    request = EscalateToHotelInput(
        hotel_id="HTL-00012345",
        booking_reference="BKG-00012345",
        issue_type=EscalationReason.SYSTEM_ERROR,
        description="System error during booking modification",
    )

    result1 = await tool.run(db, request)
    result2 = await tool.run(db, request)

    # Extract ticket numbers
    ticket_num1 = int(result1.escalation_ticket_id.split("-")[1])
    ticket_num2 = int(result2.escalation_ticket_id.split("-")[1])

    # Second ticket should be one higher than first
    assert ticket_num2 == ticket_num1 + 1


@pytest.mark.anyio
async def test_escalate_to_hotel_invalid_hotel(db: InMemoryDatabase):
    """Test escalation with invalid hotel ID."""
    tool = EscalateToHotelTool()

    request = EscalateToHotelInput(
        hotel_id="HTL-99999999",
        booking_reference="BKG-00012345",
        issue_type=EscalationReason.SAME_DAY_MODIFICATION,
        description="Test escalation",
    )

    with pytest.raises(tool.ExecutionError, match="Hotel 'HTL-99999999' not found"):
        await tool.run(db, request)


@pytest.mark.anyio
async def test_escalate_to_hotel_invalid_booking(db: InMemoryDatabase):
    """Test escalation with invalid booking reference."""
    tool = EscalateToHotelTool()

    request = EscalateToHotelInput(
        hotel_id="HTL-00012345",
        booking_reference="BKG-99999999",
        issue_type=EscalationReason.SAME_DAY_MODIFICATION,
        description="Test escalation",
    )

    with pytest.raises(tool.ExecutionError, match="Booking 'BKG-99999999' not found"):
        await tool.run(db, request)


@pytest.mark.anyio
async def test_escalate_to_hotel_ticket_stored_in_db(db: InMemoryDatabase):
    """Test that escalation ticket is stored in Zendesk database."""
    tool = EscalateToHotelTool()

    request = EscalateToHotelInput(
        hotel_id="HTL-00012345",
        booking_reference="BKG-00012345",
        issue_type=EscalationReason.LARGE_GROUP_BOOKING,
        description="Large group booking modification request",
    )

    result = await tool.run(db, request)

    # Verify ticket is in Zendesk database using get_all
    tickets = db.get_all(Ticket)

    # Find our ticket
    ticket = next((t for t in tickets if t.id == result.escalation_ticket_id), None)
    assert ticket is not None
    # Check Zendesk Ticket fields
    assert ticket.subject == "Hotel Escalation: large-group-booking"
    assert ticket.description == "Large group booking modification request"
    assert ticket.type.value == "incident"
    assert ticket.status.value == "open"
    assert ticket.priority.value == "high"
    # Check hotel escalation custom fields
    assert ticket.booking_reference == "BKG-00012345"
    assert ticket.hotel_id == "HTL-00012345"
    assert ticket.escalation_reason == "large-group-booking"


@pytest.mark.anyio
async def test_escalate_to_hotel_standard_tier_hotel(db: InMemoryDatabase):
    """Test escalation for standard tier hotel."""
    tool = EscalateToHotelTool()

    request = EscalateToHotelInput(
        hotel_id="HTL-00012346",
        booking_reference="BKG-00012345",
        issue_type=EscalationReason.HOTEL_CONFIRMATION_REQUIRED,
        description="Need confirmation for special request",
    )

    result = await tool.run(db, request)

    # Standard tier hotel should use regular contact (no escalation_contact)
    assert result.hotel_contact_email == "contact@citycenter.com"
    assert result.hotel_contact_phone == "+1-212-493-2817"
