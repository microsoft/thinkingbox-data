# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import List, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ...booking_api.models import Booking
from ..models import CorporateAccount


class GetCorporateBookingHistoryInput(BaseModel):
    corporate_account_id: str = Field(
        ..., description="Corporate account ID.", examples=["CRP-00012345"]
    )


class GetCorporateBookingHistoryOutput(BaseModel):
    corporate_bookings: List[Booking] = Field(
        ...,
        description="List of Booking objects associated with the corporate account.",
    )


class GetCorporateBookingHistoryTool(Tool):

    @property
    def name(self):
        return "get_corporate_booking_history"

    @property
    def description(self) -> str:
        return (
            "Retrieve booking history for a corporate account. "
            "Fetches all bookings associated with a corporate account for reporting, analysis, or billing purposes. "
            "Returns comprehensive booking details across all corporate travelers."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetCorporateBookingHistoryInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetCorporateBookingHistoryOutput

    async def run(self, db: InMemoryDatabase, request: GetCorporateBookingHistoryInput):

        if not request.corporate_account_id.startswith("CRP-"):
            raise self.ExecutionError("Invalid corporate_account_id parameter.")

        accounts = db.get_all(CorporateAccount)
        account = next(
            (
                a
                for a in accounts
                if a.corporate_account_id == request.corporate_account_id
            ),
            None,
        )
        if not account:
            raise self.ExecutionError("Corporate account not found.")

        bookings = db.get_all(Booking)
        filtered = [
            b
            for b in bookings
            if b.corporate_account_id == request.corporate_account_id
        ]

        sorted_bookings = sorted(filtered, key=lambda b: b.created_at, reverse=True)

        return GetCorporateBookingHistoryOutput(corporate_bookings=sorted_bookings)
