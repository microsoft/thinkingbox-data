# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import List, Optional, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ...hotel_partner_api.models import Hotel


class LookupHotelIdInput(BaseModel):
    """Input model for searching hotels by name or location."""

    hotel_name: Optional[str] = Field(
        None,
        description="Hotel name for search (case-insensitive contains match).",
        examples=["Grand Plaza Hotel"],
    )

    location: Optional[str] = Field(
        None, description="Hotel location / city for search.", examples=["New York"]
    )


class HotelLookupResult(BaseModel):
    """Single search result entry."""

    hotel_id: str = Field(..., description="Unique hotel ID (HTL-########).")
    hotel_name: str = Field(..., description="Hotel name.")
    location: str = Field(..., description="Hotel location / city.")


class LookupHotelIdOutput(BaseModel):
    """Output with all matching hotels."""

    results: List[HotelLookupResult] = Field(
        ..., description="Array of matching hotels."
    )


class LookupHotelIdTool(Tool):
    """Search hotels by name or location."""

    @property
    def name(self) -> str:
        return "lookup_hotel_id"

    @property
    def summary(self) -> str:
        return "Look up hotel ID from hotel name or location."

    @property
    def description(self) -> str:
        return (
            "Searches for hotels by name or location to retrieve hotel_id. "
            "Used when customer provides hotel name instead of ID for booking or modification requests."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return LookupHotelIdInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return LookupHotelIdOutput

    async def run(
        self, db: InMemoryDatabase, request: LookupHotelIdInput
    ) -> LookupHotelIdOutput:

        hotel_name = request.hotel_name
        location = request.location

        if not hotel_name and not location:
            raise self.ExecutionError(
                "Invalid parameters: provide hotel_name or location."
            )

        name_q = hotel_name.lower() if hotel_name else None
        loc_q = location.lower() if location else None

        hotels = db.get_all(Hotel)

        def match(h: Hotel) -> bool:
            name_ok = name_q and name_q in h.hotel_name.lower()
            loc_ok = loc_q and loc_q in h.location.lower()
            return name_ok or loc_ok

        matches = [h for h in hotels if match(h)]

        if not matches:
            raise self.ExecutionError("No hotels found matching criteria.")

        return LookupHotelIdOutput(
            results=[
                HotelLookupResult(
                    hotel_id=h.hotel_id, hotel_name=h.hotel_name, location=h.location
                )
                for h in matches
            ]
        )
