# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Generate invoice or receipt document for a booking.

Creates downloadable invoice or receipt document for customer records, expense reporting, or tax purposes.
Returns document URL for customer access.
"""

from datetime import datetime, timezone
from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ...booking_api.models import Booking

# Fixed current time for deterministic behavior
FIXED_CURRENT_TIME = datetime(2025, 11, 25, 10, 0, 0, tzinfo=timezone.utc)


class GenerateInvoiceInput(BaseModel):
    """Input model for generate_invoice tool."""

    booking_reference: str = Field(
        ..., description="Booking reference number", examples=["BKG-00012345"]
    )
    invoice_type: str = Field(
        ..., description="Type of invoice: receipt or invoice", examples=["receipt"]
    )


class GenerateInvoiceOutput(BaseModel):
    """Output model for generate_invoice tool."""

    model_config = ConfigDict(extra="forbid")

    invoice_url: str = Field(
        ..., description="URL to download the generated invoice or receipt document"
    )
    invoice_id: str = Field(
        ..., description="Unique identifier for the generated invoice"
    )


class GenerateInvoice(Tool):
    """Generate invoice or receipt document for a booking."""

    @property
    def name(self) -> str:
        return "generate_invoice"

    @property
    def description(self) -> str:
        return "Generate invoice or receipt document for a booking"

    @property
    def request_model(self) -> Type[BaseModel]:
        return GenerateInvoiceInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GenerateInvoiceOutput

    async def run(
        self, db: InMemoryDatabase, request: GenerateInvoiceInput
    ) -> GenerateInvoiceOutput:
        """Execute the tool logic."""
        # Verify booking exists
        all_bookings = db.get_all(Booking)
        booking_found = False
        for b in all_bookings:
            if b.booking_reference == request.booking_reference:
                booking_found = True
                break

        if not booking_found:
            raise Tool.ExecutionError(f"Booking not found: {request.booking_reference}")

        # Generate invoice URL and ID (no database write)
        timestamp = FIXED_CURRENT_TIME.strftime("%Y%m%d%H%M%S")
        invoice_url = f"https://staybridge.com/invoices/{request.booking_reference}-{timestamp}.pdf"
        invoice_id = f"INV-{request.booking_reference}-{timestamp}"

        return GenerateInvoiceOutput(invoice_url=invoice_url, invoice_id=invoice_id)
