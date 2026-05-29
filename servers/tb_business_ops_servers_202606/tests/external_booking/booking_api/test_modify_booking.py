# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for modify_booking tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.booking_api.models import (
    BoardType,
    Booking,
    BookingStatus,
    HotelInventory,
    RoomType,
)
from tb_business_ops_servers_202606.toolslib.external_booking.booking_api.tools import (
    ModifyBookingTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db_with_booking_and_inventory():
    """Create a database with test booking and inventory."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)

    # Register models
    db._stem_to_model_cls["bookings"] = Booking
    db._model_cls_to_stem[Booking] = "bookings"
    db._stem_to_model_cls["hotel_inventory"] = HotelInventory
    db._model_cls_to_stem[HotelInventory] = "hotel_inventory"

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

    # Add inventory for price calculation
    dates = ["2025-12-15T00:00:00Z", "2025-12-16T00:00:00Z", "2025-12-17T00:00:00Z"]
    for i, date_str in enumerate(dates):
        inv = HotelInventory(
            id=f"INV-{i:08d}",
            hotel_id="HTL-00012345",
            room_type=RoomType.SUITE,
            board_type=BoardType.HALF_BOARD,
            date=date_str,
            available_count=5,
            price_per_night=200.00,
            created_at="2025-11-01T00:00:00Z",
            updated_at="2025-11-01T00:00:00Z",
        )
        db.create(inv)

    return db


@pytest.mark.anyio
async def test_modify_booking_room_type(db_with_booking_and_inventory):
    """Test modifying room type."""
    tool = ModifyBookingTool()

    result = await tool.run_with_validation(
        db_with_booking_and_inventory,
        {"booking_reference": "BKG-00012345", "room_type": "suite"},
    )

    assert "updated_booking" in result
    assert result["updated_booking"]["room_type"] == "suite"
    assert "price_difference" in result
    assert len(result["updated_booking"]["modification_history"]) > 0


@pytest.mark.anyio
async def test_modify_booking_board_type(db_with_booking_and_inventory):
    """Test modifying board type."""
    tool = ModifyBookingTool()

    result = await tool.run_with_validation(
        db_with_booking_and_inventory,
        {"booking_reference": "BKG-00012345", "board_type": "half_board"},
    )

    assert result["updated_booking"]["board_type"] == "half_board"
    assert "price_difference" in result


@pytest.mark.anyio
async def test_modify_booking_guest_counts(db_with_booking_and_inventory):
    """Test modifying guest counts."""
    tool = ModifyBookingTool()

    result = await tool.run_with_validation(
        db_with_booking_and_inventory,
        {"booking_reference": "BKG-00012345", "adults_count": 3, "children_count": 0},
    )

    assert result["updated_booking"]["adults_count"] == 3
    assert result["updated_booking"]["children_count"] == 0


@pytest.mark.anyio
async def test_modify_booking_special_requests(db_with_booking_and_inventory):
    """Test modifying special requests."""
    tool = ModifyBookingTool()

    result = await tool.run_with_validation(
        db_with_booking_and_inventory,
        {
            "booking_reference": "BKG-00012345",
            "special_requests": ["late checkout", "quiet room"],
        },
    )

    assert "late checkout" in result["updated_booking"]["special_requests"]
    assert "quiet room" in result["updated_booking"]["special_requests"]


@pytest.mark.anyio
async def test_modify_booking_not_confirmed(db_with_booking_and_inventory):
    """Test that cancelled booking cannot be modified."""
    # Change booking status to cancelled
    bookings = db_with_booking_and_inventory.get_all(Booking)
    bookings[0].booking_status = BookingStatus.CANCELLED
    db_with_booking_and_inventory.update(bookings[0])

    tool = ModifyBookingTool()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_booking_and_inventory,
            {"booking_reference": "BKG-00012345", "adults_count": 3},
        )

    assert "cannot be modified" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_modify_booking_not_found(db_with_booking_and_inventory):
    """Test modifying non-existent booking."""
    tool = ModifyBookingTool()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_booking_and_inventory,
            {"booking_reference": "BKG-99999999", "adults_count": 3},
        )

    assert "not found" in str(exc_info.value).lower()
