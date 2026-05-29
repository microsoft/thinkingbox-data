# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for generate_invoice tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.booking_api.models import (
    BoardType,
    Booking,
    BookingStatus,
    RoomType,
)
from tb_business_ops_servers_202606.toolslib.external_booking.payment_api.tools.generate_invoice import (
    GenerateInvoice,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db_with_booking():
    """Create a database with test booking."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)

    # Manually register models
    db._stem_to_model_cls["bookings"] = Booking
    db._model_cls_to_stem[Booking] = "bookings"

    # Add test booking
    booking = Booking(
        id="BKG-00012345",
        booking_reference="BKG-00012345",
        customer_id="CUS-00012345",
        hotel_id="HTL-00012345",
        check_in_date="2025-12-15T15:00:00Z",
        check_out_date="2025-12-18T11:00:00Z",
        booking_value=450.00,
        room_type=RoomType.DELUXE_ROOM,
        board_type=BoardType.WITH_BREAKFAST,
        adults_count=2,
        children_count=1,
        booking_status=BookingStatus.CONFIRMED,
        created_at="2025-11-20T10:00:00Z",
        updated_at="2025-11-20T10:00:00Z",
    )
    db.create(booking)

    return db


@pytest.mark.anyio
async def test_generate_invoice_receipt(db_with_booking):
    """Test generating a receipt."""
    tool = GenerateInvoice()

    result = await tool.run_with_validation(
        db_with_booking,
        {"booking_reference": "BKG-00012345", "invoice_type": "receipt"},
    )

    assert "invoice_url" in result
    assert "invoice_id" in result
    assert "staybridge.com/invoices/" in result["invoice_url"]
    assert "BKG-00012345" in result["invoice_url"]


@pytest.mark.anyio
async def test_generate_invoice_invoice_type(db_with_booking):
    """Test generating an invoice."""
    tool = GenerateInvoice()

    result = await tool.run_with_validation(
        db_with_booking,
        {"booking_reference": "BKG-00012345", "invoice_type": "invoice"},
    )

    assert "invoice_url" in result
    assert "invoice_id" in result


@pytest.mark.anyio
async def test_generate_invoice_url_format(db_with_booking):
    """Test invoice URL format."""
    tool = GenerateInvoice()

    result = await tool.run_with_validation(
        db_with_booking,
        {"booking_reference": "BKG-00012345", "invoice_type": "receipt"},
    )

    # URL should contain booking reference and timestamp
    assert result["invoice_url"].startswith(
        "https://staybridge.com/invoices/BKG-00012345-"
    )
    assert result["invoice_url"].endswith(".pdf")


@pytest.mark.anyio
async def test_generate_invoice_id_format(db_with_booking):
    """Test invoice ID format."""
    tool = GenerateInvoice()

    result = await tool.run_with_validation(
        db_with_booking,
        {"booking_reference": "BKG-00012345", "invoice_type": "receipt"},
    )

    # Invoice ID should start with INV- and contain booking reference
    assert result["invoice_id"].startswith("INV-BKG-00012345-")


@pytest.mark.anyio
async def test_generate_invoice_not_found(db_with_booking):
    """Test generating invoice for non-existent booking."""
    tool = GenerateInvoice()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_booking,
            {"booking_reference": "BKG-99999999", "invoice_type": "receipt"},
        )

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_generate_invoice_multiple_calls(db_with_booking):
    """Test that multiple calls generate unique invoice IDs."""
    tool = GenerateInvoice()

    result1 = await tool.run_with_validation(
        db_with_booking,
        {"booking_reference": "BKG-00012345", "invoice_type": "receipt"},
    )

    result2 = await tool.run_with_validation(
        db_with_booking,
        {"booking_reference": "BKG-00012345", "invoice_type": "invoice"},
    )

    # Since they use same timestamp, they should be identical
    assert result1["invoice_id"] == result2["invoice_id"]
    assert result1["invoice_url"] == result2["invoice_url"]
