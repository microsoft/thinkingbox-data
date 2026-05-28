# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Retrieve hotel partner contact information.

Fetches primary and escalation contact details for a hotel partner. Used when agent needs
to contact hotel directly or provide contact information to customer.
"""

from typing import Optional, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ..models import Hotel


class GetHotelContactInput(BaseModel):
    """Input model for get_hotel_contact tool."""

    hotel_id: str = Field(
        ..., description="Hotel identifier", examples=["HTL-00012345"]
    )


class GetHotelContactOutput(BaseModel):
    """Output model for get_hotel_contact tool."""

    contact_name: str = Field(..., description="Primary contact name at hotel")
    contact_email: str = Field(..., description="Primary contact email")
    contact_phone: str = Field(..., description="Primary contact phone number")
    escalation_contact: Optional[str] = Field(
        None,
        description="Escalation contact for urgent issues (typically manager or supervisor)",
    )


class GetHotelContact(Tool):
    """Retrieve hotel partner contact information."""

    @property
    def name(self) -> str:
        return "get_hotel_contact"

    @property
    def description(self) -> str:
        return "Retrieve hotel partner contact information"

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetHotelContactInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetHotelContactOutput

    async def run(
        self, db: InMemoryDatabase, request: GetHotelContactInput
    ) -> GetHotelContactOutput:
        """Execute the tool logic."""
        # Get hotel from database
        all_hotels = db.get_all(Hotel)
        hotel = next((h for h in all_hotels if h.hotel_id == request.hotel_id), None)

        if not hotel:
            raise Tool.ExecutionError(f"Hotel not found: {request.hotel_id}")

        return GetHotelContactOutput(
            contact_name=hotel.contact_name,
            contact_email=hotel.contact_email,
            contact_phone=hotel.contact_phone,
            escalation_contact=hotel.escalation_contact,
        )
