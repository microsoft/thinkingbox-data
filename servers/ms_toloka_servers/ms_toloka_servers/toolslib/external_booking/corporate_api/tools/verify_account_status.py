# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from datetime import datetime
from typing import Optional, Type

from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ...booking_api.models import Booking, BookingStatus
from ..models import CorporateAccount


class VerifyAccountStatusInput(BaseModel):
    corporate_account_id: str = Field(
        ...,
        description="Corporate account identifier used internally for reference.",
        examples=["CRP-00012345"],
    )


class VerifyAccountStatusOutput(BaseModel):
    is_active: bool = Field(..., description="Whether the account is currently active.")
    expiration_date: Optional[datetime] = Field(
        None, description="Expiration date of corporate account, if any."
    )
    booking_limit_remaining: int = Field(
        ...,
        description="Remaining number of bookings allowed under the corporate booking_limit.",
    )


class VerifyAccountStatusTool(Tool):

    @property
    def name(self):
        return "verify_account_status"

    @property
    def description(self) -> str:
        return (
            "Verify corporate account status and entitlements. "
            "Validates corporate account is active and within booking limits. "
            "Quick verification for booking eligibility without retrieving full account details."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return VerifyAccountStatusInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return VerifyAccountStatusOutput

    async def run(self, db: InMemoryDatabase, request: VerifyAccountStatusInput):

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
        active_bookings_count = sum(
            1
            for b in bookings
            if b.corporate_account_id == account.corporate_account_id
            and b.booking_status == BookingStatus.CONFIRMED
        )

        booking_limit_remaining = max(0, account.booking_limit - active_bookings_count)

        return VerifyAccountStatusOutput(
            is_active=(account.account_status.value == "active"),
            expiration_date=account.expiration_date,
            booking_limit_remaining=booking_limit_remaining,
        )
