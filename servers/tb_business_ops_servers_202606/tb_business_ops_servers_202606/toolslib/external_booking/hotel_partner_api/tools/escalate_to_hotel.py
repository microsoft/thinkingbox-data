# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Escalate to hotel partner tool."""

from datetime import datetime, timezone
from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, ConfigDict, Field

from ...booking_api.models import Booking
from ...zendesk.models import Ticket, TicketPriority, TicketStatus, TicketType
from ..models import EscalationReason, Hotel

PREFIX_FOR_NEW_TICKETS = "ZDSK-"
FIXED_CURRENT_TIME = datetime(2025, 11, 30, 10, 0, 0, tzinfo=timezone.utc)


def generate_ticket_id(existing_tickets) -> str:
    """Generate sequential Zendesk ticket ID."""
    existing_ids = {t.id for t in existing_tickets}
    count = 0

    while True:
        new_id = f"{PREFIX_FOR_NEW_TICKETS}{count + 1:08d}"
        if new_id not in existing_ids:
            return new_id
        count += 1


class EscalateToHotelInput(BaseModel):
    """Input model for escalate_to_hotel."""

    model_config = ConfigDict(extra="forbid")

    hotel_id: str = Field(
        ..., description="Hotel identifier to escalate to", examples=["HTL-00012345"]
    )
    booking_reference: str = Field(
        ..., description="Booking reference number", examples=["BKG-00012345"]
    )
    issue_type: EscalationReason = Field(
        ...,
        description="Type of issue requiring escalation",
        examples=["same-day-modification"],
    )
    description: str = Field(
        ...,
        description="Detailed description of the issue",
        examples=["Customer needs to change check-in time to 2 PM today"],
    )


class EscalateToHotelOutput(BaseModel):
    """Output model for escalate_to_hotel."""

    escalation_ticket_id: str = Field(..., description="Generated escalation ticket ID")
    hotel_contact_email: str = Field(
        ..., description="Hotel contact email for follow-up"
    )
    hotel_contact_phone: str = Field(
        ..., description="Hotel contact phone for urgent matters"
    )


class EscalateToHotelTool(Tool):
    """Tool to escalate booking issues directly to hotel partner."""

    @property
    def name(self) -> str:
        return "escalate_to_hotel"

    @property
    def description(self) -> str:
        return "Escalates complex booking modifications or issues that require direct hotel partner coordination (same-day changes, large group bookings, system errors, guest complaints)."

    @property
    def request_model(self) -> Type[BaseModel]:
        return EscalateToHotelInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return EscalateToHotelOutput

    async def run(
        self, db: InMemoryDatabase, request: EscalateToHotelInput
    ) -> EscalateToHotelOutput:
        """Execute escalation to hotel partner."""

        # Find the target hotel
        hotels = db.get_all(Hotel)
        hotel = next((h for h in hotels if h.hotel_id == request.hotel_id), None)

        if not hotel:
            raise self.ExecutionError(f"Hotel '{request.hotel_id}' not found.")

        # Find the target booking
        bookings = db.get_all(Booking)
        booking = next(
            (b for b in bookings if b.booking_reference == request.booking_reference),
            None,
        )

        if not booking:
            raise self.ExecutionError(
                f"Booking '{request.booking_reference}' not found."
            )

        # Generate ticket ID
        existing_tickets = db.get_all(Ticket)
        ticket_id = generate_ticket_id(existing_tickets)

        # Create Zendesk ticket with hotel escalation custom fields
        created_at = FIXED_CURRENT_TIME.isoformat().replace("+00:00", "Z")

        ticket = Ticket(
            id=ticket_id,
            subject=f"Hotel Escalation: {request.issue_type.value}",
            description=request.description,
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH,
            type=TicketType.INCIDENT,
            created_at=created_at,
            updated_at=created_at,
            requester_id=booking.customer_id,
            # Hotel escalation custom fields
            hotel_id=request.hotel_id,
            booking_reference=request.booking_reference,
            escalation_reason=request.issue_type.value,
        )

        # Store ticket in database
        db.create(ticket)

        # Determine contact information
        # Use escalation_contact if available, otherwise use regular contact
        contact_email = hotel.escalation_contact or hotel.contact_email
        contact_phone = hotel.contact_phone

        return EscalateToHotelOutput(
            escalation_ticket_id=ticket_id,
            hotel_contact_email=contact_email,
            hotel_contact_phone=contact_phone,
        )
