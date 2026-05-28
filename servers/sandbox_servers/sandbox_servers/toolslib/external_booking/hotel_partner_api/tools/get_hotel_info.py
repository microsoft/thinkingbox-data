# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Retrieve hotel partner information and details.

Fetches comprehensive hotel information including partner tier, contact details, amenities, and policies.
Essential for applying hotel-specific policies and determining escalation contacts.
"""

from typing import Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ..models import Hotel, HotelData


class GetHotelInfoInput(BaseModel):
    """Input model for get_hotel_info tool."""

    hotel_id: str = Field(
        ..., description="Hotel identifier", examples=["HTL-00012345"]
    )


class GetHotelInfoOutput(BaseModel):
    """Output model for get_hotel_info tool."""

    hotel_data: HotelData = Field(..., description="Complete hotel record")


class GetHotelInfo(Tool):
    """Retrieve hotel partner information and details."""

    @property
    def name(self) -> str:
        return "get_hotel_info"

    @property
    def description(self) -> str:
        return "Retrieve hotel partner information and details"

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetHotelInfoInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetHotelInfoOutput

    async def run(
        self, db: InMemoryDatabase, request: GetHotelInfoInput
    ) -> GetHotelInfoOutput:
        """Execute the tool logic."""
        # Get hotel from database
        all_hotels = db.get_all(Hotel)
        hotel = None
        for h in all_hotels:
            if h.hotel_id == request.hotel_id:
                hotel = h
                break

        if not hotel:
            raise Tool.ExecutionError(f"Hotel not found: {request.hotel_id}")

        # Convert to output format
        hotel_data = HotelData(
            id=hotel.id,
            hotel_id=hotel.hotel_id,
            hotel_name=hotel.hotel_name,
            location=hotel.location,
            partner_tier=hotel.partner_tier.value,
            contact_name=hotel.contact_name,
            contact_email=hotel.contact_email,
            contact_phone=hotel.contact_phone,
            escalation_contact=hotel.escalation_contact,
            amenities=hotel.amenities,
            supports_pets=hotel.supports_pets,
            accessible_rooms_available=hotel.accessible_rooms_available,
            created_at=hotel.created_at,
            updated_at=hotel.updated_at,
        )

        return GetHotelInfoOutput(hotel_data=hotel_data)
