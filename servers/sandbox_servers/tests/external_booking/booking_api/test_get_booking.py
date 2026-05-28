# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_booking tool."""

import pytest
from sandbox_servers.toolslib.external_booking.booking_api.models import (
    BoardType,
    Booking,
    BookingStatus,
    RoomType,
)
from sandbox_servers.toolslib.external_booking.booking_api.tools import GetBookingTool
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db():
    """Create a database with test bookings."""
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
async def test_get_booking_by_reference(db):
    """Test successfully retrieving booking by booking_reference."""
    tool = GetBookingTool()

    result = await tool.run_with_validation(db, {"booking_reference": "BKG-00012345"})

    assert "booking_data" in result
    booking_data = result["booking_data"]
    assert booking_data["booking_reference"] == "BKG-00012345"
    assert booking_data["customer_id"] == "CUS-00012345"
    assert booking_data["hotel_id"] == "HTL-00012345"
    assert booking_data["booking_value"] == "450.0"  # Decimal serialized as string


@pytest.mark.anyio
async def test_get_booking_by_customer_id(db):
    """Test successfully retrieving booking by customer_id."""
    tool = GetBookingTool()

    result = await tool.run_with_validation(db, {"customer_id": "CUS-00012345"})

    assert "booking_data" in result
    booking_data = result["booking_data"]
    assert booking_data["customer_id"] == "CUS-00012345"


@pytest.mark.anyio
async def test_get_booking_not_found(db):
    """Test retrieving non-existent booking."""
    tool = GetBookingTool()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(db, {"booking_reference": "BKG-99999999"})

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_get_booking_missing_parameters(db):
    """Test that missing both parameters raises an error."""
    tool = GetBookingTool()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(db, {})

    assert "must be provided" in str(exc_info.value).lower()
