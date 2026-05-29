# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_booking_history tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.booking_api.models import (
    BoardType,
    Booking,
    BookingStatus,
    RoomType,
)
from tb_business_ops_servers_202606.toolslib.external_booking.booking_api.tools import (
    GetBookingHistoryTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db():
    """Create database with multiple bookings for testing."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)

    # Manually register models
    db._stem_to_model_cls["bookings"] = Booking
    db._model_cls_to_stem[Booking] = "bookings"

    # Customer with multiple bookings
    bookings = [
        Booking(
            id="BKG-00000001",
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
            corporate_account_id=None,
            group_booking_id=None,
            modification_history=[],
            special_requests=["late checkout"],
            created_at="2025-11-01T10:00:00Z",
            updated_at="2025-11-01T10:00:00Z",
        ),
        Booking(
            id="BKG-00000002",
            booking_reference="BKG-00012346",
            customer_id="CUS-00012345",
            hotel_id="HTL-00012346",
            check_in_date="2025-10-10T15:00:00Z",
            check_out_date="2025-10-12T11:00:00Z",
            booking_value=300.00,
            room_type=RoomType.STANDARD_ROOM,
            board_type=BoardType.WITHOUT_BREAKFAST,
            adults_count=2,
            children_count=0,
            booking_status=BookingStatus.CHECKED_OUT,
            corporate_account_id=None,
            group_booking_id=None,
            modification_history=[],
            special_requests=[],
            created_at="2025-09-15T10:00:00Z",
            updated_at="2025-09-15T10:00:00Z",
        ),
        Booking(
            id="BKG-00000003",
            booking_reference="BKG-00012347",
            customer_id="CUS-00012345",
            hotel_id="HTL-00012345",
            check_in_date="2025-08-01T15:00:00Z",
            check_out_date="2025-08-05T11:00:00Z",
            booking_value=600.00,
            room_type=RoomType.SUITE,
            board_type=BoardType.HALF_BOARD,
            adults_count=2,
            children_count=2,
            booking_status=BookingStatus.CANCELLED,
            corporate_account_id=None,
            group_booking_id=None,
            modification_history=[],
            special_requests=[],
            created_at="2025-07-01T10:00:00Z",
            updated_at="2025-07-15T10:00:00Z",
        ),
        # Different customer
        Booking(
            id="BKG-00000004",
            booking_reference="BKG-00012348",
            customer_id="CUS-00067890",
            hotel_id="HTL-00012345",
            check_in_date="2025-12-20T15:00:00Z",
            check_out_date="2025-12-22T11:00:00Z",
            booking_value=250.00,
            room_type=RoomType.STANDARD_ROOM,
            board_type=BoardType.WITH_BREAKFAST,
            adults_count=1,
            children_count=0,
            booking_status=BookingStatus.CONFIRMED,
            corporate_account_id=None,
            group_booking_id=None,
            modification_history=[],
            special_requests=[],
            created_at="2025-11-20T10:00:00Z",
            updated_at="2025-11-20T10:00:00Z",
        ),
    ]

    for booking in bookings:
        db.create(booking)

    return db


@pytest.mark.anyio
async def test_get_booking_history_success(db):
    """Test retrieving booking history for customer with multiple bookings."""
    tool = GetBookingHistoryTool()

    result = await tool.run_with_validation(db, {"customer_id": "CUS-00012345"})

    # Should return 3 bookings for this customer
    assert len(result["bookings"]) == 3

    # Check bookings are ordered by created_at DESC (most recent first)
    assert result["bookings"][0]["booking_reference"] == "BKG-00012345"  # 2025-11-01
    assert result["bookings"][1]["booking_reference"] == "BKG-00012346"  # 2025-09-15
    assert result["bookings"][2]["booking_reference"] == "BKG-00012347"  # 2025-07-01

    # Verify complete booking data is returned
    first_booking = result["bookings"][0]
    assert first_booking["customer_id"] == "CUS-00012345"
    assert first_booking["hotel_id"] == "HTL-00012345"
    assert first_booking["booking_status"] == "confirmed"
    assert first_booking["booking_value"] == "450.0"  # Decimal serialized as string


@pytest.mark.anyio
async def test_get_booking_history_single_booking(db):
    """Test retrieving history for customer with single booking."""
    tool = GetBookingHistoryTool()

    result = await tool.run_with_validation(db, {"customer_id": "CUS-00067890"})

    # Should return 1 booking
    assert len(result["bookings"]) == 1
    assert result["bookings"][0]["booking_reference"] == "BKG-00012348"


@pytest.mark.anyio
async def test_get_booking_history_no_bookings(db):
    """Test retrieving history for customer with no bookings."""
    tool = GetBookingHistoryTool()

    result = await tool.run_with_validation(db, {"customer_id": "CUS-99999999"})

    # Should return empty array
    assert len(result["bookings"]) == 0


@pytest.mark.anyio
async def test_get_booking_history_includes_all_statuses(db):
    """Test that booking history includes all statuses (confirmed, cancelled, checked_out)."""
    tool = GetBookingHistoryTool()

    result = await tool.run_with_validation(db, {"customer_id": "CUS-00012345"})

    # Get all statuses from returned bookings
    statuses = [b["booking_status"] for b in result["bookings"]]

    # Should include confirmed, cancelled, and checked_out
    assert "confirmed" in statuses
    assert "cancelled" in statuses
    assert "checked_out" in statuses
