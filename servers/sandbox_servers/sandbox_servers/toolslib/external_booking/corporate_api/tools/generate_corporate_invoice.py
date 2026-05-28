# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from decimal import Decimal
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

from ...booking_api.models import Booking
from ..models import CorporateAccount


class GenerateCorporateInvoiceInput(BaseModel):
    booking_reference: str = Field(
        ..., description="Corporate booking reference.", examples=["BKG-00012345"]
    )
    corporate_account_id: str = Field(
        ..., description="Corporate account ID.", examples=["CRP-00012345"]
    )


class GenerateCorporateInvoiceOutput(BaseModel):
    invoice_url: str = Field(
        ...,
        description="URL to download corporate invoice document.",
        examples=[
            "https://staybridge.com/corporate-invoices/CRP-00012345-BKG-00012345.pdf"
        ],
    )
    invoice_id: str = Field(
        ..., description="Generated invoice identifier.", examples=["INV-000000001"]
    )
    payment_terms: str = Field(
        ...,
        description="Payment terms from corporate account, e.g. 'Net 30'.",
        examples=["Net 60"],
    )


class GenerateCorporateInvoiceTool(Tool):

    @property
    def name(self) -> str:
        return "generate_corporate_invoice"

    @property
    def description(self) -> str:
        return (
            "Generate corporate invoice for a booking. "
            "Creates corporate invoice with specific formatting, billing codes, and payment terms required for corporate reimbursement and accounting systems. "
            "Different from standard invoice format."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GenerateCorporateInvoiceInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GenerateCorporateInvoiceOutput

    def _generate_invoice_id(
        self, booking_reference: str, corporate_account_id: str
    ) -> str:
        """
        Generate deterministic invoice ID based on booking reference and corporate account ID.

        Format: INV-{booking_number}-{account_number}
        Example: BKG-00012345 + CRP-00012345 -> INV-00012345-00012345
        """
        booking_num = booking_reference.replace("BKG-", "")
        account_num = corporate_account_id.replace("CRP-", "")
        return f"INV-{booking_num}-{account_num}"

    async def run(self, db: InMemoryDatabase, request: GenerateCorporateInvoiceInput):
        if not request.corporate_account_id.startswith("CRP-"):
            raise self.ExecutionError("Invalid corporate_account_id parameter.")
        if not request.booking_reference.startswith("BKG-"):
            raise self.ExecutionError("Invalid booking_reference parameter.")

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
        booking = next(
            (b for b in bookings if b.booking_reference == request.booking_reference),
            None,
        )
        if not booking:
            raise self.ExecutionError("Booking not found.")

        if booking.corporate_account_id != account.corporate_account_id:
            raise self.ExecutionError(
                "Booking is not associated with this corporate account."
            )

        invoice_id = self._generate_invoice_id(
            request.booking_reference, request.corporate_account_id
        )

        invoice_url = (
            f"https://staybridge.com/corporate-invoices/"
            f"{request.corporate_account_id}-{request.booking_reference}.pdf"
        )

        return GenerateCorporateInvoiceOutput(
            invoice_url=invoice_url,
            invoice_id=invoice_id,
            payment_terms=account.payment_terms,
        )
