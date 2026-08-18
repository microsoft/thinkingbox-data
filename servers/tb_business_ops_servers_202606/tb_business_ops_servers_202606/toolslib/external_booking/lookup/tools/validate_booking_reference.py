# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Optional, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, Field

from ...booking_api.models import Booking


class ValidateBookingReferenceInput(BaseModel):
    """Input model for validating booking reference format and existence."""

    booking_reference: str = Field(
        ...,
        description="Booking reference in BKG-######## format.",
        examples=["BKG-00012345"],
    )


class ValidateBookingReferenceOutput(BaseModel):
    """Output model: validity + internal booking ID if exists."""

    is_valid: bool = Field(
        ..., description="Indicates if booking reference exists and is valid."
    )

    booking_id: Optional[str] = Field(
        None, description="Internal booking ID if reference is valid."
    )


class ValidateBookingReferenceTool(Tool):
    """Validate booking reference format and existence."""

    @property
    def name(self) -> str:
        return "validate_booking_reference"

    @property
    def summary(self) -> str:
        return "Validate booking reference format and existence."

    @property
    def description(self) -> str:
        return (
            "Quickly validates that a booking reference exists in the system and "
            "returns the internal booking ID if valid. Used for early validation "
            "before retrieving full booking details."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return ValidateBookingReferenceInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ValidateBookingReferenceOutput

    async def run(
        self, db: InMemoryDatabase, request: ValidateBookingReferenceInput
    ) -> ValidateBookingReferenceOutput:

        ref = request.booking_reference

        import re

        if not re.fullmatch(r"BKG-\d{8}", ref):
            raise self.ExecutionError("Invalid booking reference format.")

        items = db.get_all(Booking)
        record = next((b for b in items if b.booking_reference == ref), None)

        if record is None:
            return ValidateBookingReferenceOutput(is_valid=False, booking_id=None)

        return ValidateBookingReferenceOutput(is_valid=True, booking_id=record.id)
