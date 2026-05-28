# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for modify_group_booking tool."""

from decimal import Decimal

import pytest
from sandbox_servers.toolslib.external_booking.booking_api.models import (
    BoardType,
    Booking,
    BookingStatus,
    GroupBooking,
    HotelInventory,
    RoomType,
)
from sandbox_servers.toolslib.external_booking.booking_api.tools.modify_group_booking import (
    ModifyGroupBookingTool,
)
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db_with_group_booking():
    """Create database with group booking and individual bookings."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)

    # Manually register models
    db._stem_to_model_cls["group_bookings"] = GroupBooking
    db._model_cls_to_stem[GroupBooking] = "group_bookings"

    db._stem_to_model_cls["bookings"] = Booking
    db._model_cls_to_stem[Booking] = "bookings"

    db._stem_to_model_cls["hotel_inventory"] = HotelInventory
    db._model_cls_to_stem[HotelInventory] = "hotel_inventory"

    # Create group booking
    group_booking = GroupBooking(
        id="GRP-00000001",
        group_booking_id="GRP-00012345",
        coordinator_name="Alice Johnson",
        coordinator_email="alice.johnson@acmecorp.com",
        coordinator_phone="(415) 892-3847",
        total_rooms=2,
        check_in_date="2025-12-15T15:00:00Z",
        check_out_date="2025-12-18T11:00:00Z",
        hotel_id="HTL-00012345",
        booking_references=["BKG-00012345", "BKG-00012346"],
        created_at="2025-11-01T10:00:00Z",
        updated_at="2025-11-01T10:00:00Z",
    )
    db.create(group_booking)

    # Create individual bookings
    bookings = [
        Booking(
            id="BKG-00012345",
            booking_reference="BKG-00012345",
            customer_id="CUS-00001",
            hotel_id="HTL-00012345",
            check_in_date="2025-12-15T15:00:00Z",
            check_out_date="2025-12-18T11:00:00Z",
            booking_value=Decimal("450.00"),
            room_type=RoomType.DELUXE_ROOM,
            board_type=BoardType.WITH_BREAKFAST,
            adults_count=2,
            children_count=0,
            booking_status=BookingStatus.CONFIRMED,
            group_booking_id="GRP-00012345",
            modification_history=[],
            created_at="2025-11-20T10:00:00Z",
            updated_at="2025-11-20T10:00:00Z",
        ),
        Booking(
            id="BKG-00012346",
            booking_reference="BKG-00012346",
            customer_id="CUS-00002",
            hotel_id="HTL-00012345",
            check_in_date="2025-12-15T15:00:00Z",
            check_out_date="2025-12-18T11:00:00Z",
            booking_value=Decimal("450.00"),
            room_type=RoomType.DELUXE_ROOM,
            board_type=BoardType.WITH_BREAKFAST,
            adults_count=2,
            children_count=0,
            booking_status=BookingStatus.CONFIRMED,
            group_booking_id="GRP-00012345",
            modification_history=[],
            created_at="2025-11-20T10:00:00Z",
            updated_at="2025-11-20T10:00:00Z",
        ),
    ]

    for booking in bookings:
        db.create(booking)

    # Create hotel inventory for price calculation
    dates = [
        "2025-12-15T00:00:00Z",
        "2025-12-16T00:00:00Z",
        "2025-12-17T00:00:00Z",
        "2025-12-18T00:00:00Z",
        "2025-12-19T00:00:00Z",
    ]
    for i, date in enumerate(dates):
        inventory = HotelInventory(
            id=f"INV-0000000{i+1}",
            hotel_id="HTL-00012345",
            room_type=RoomType.DELUXE_ROOM,
            board_type=BoardType.WITH_BREAKFAST,
            date=date,
            available_count=5,
            price_per_night=Decimal("150.00"),
            created_at="2025-11-01T10:00:00Z",
            updated_at="2025-11-01T10:00:00Z",
        )
        db.create(inventory)

    return db


@pytest.mark.anyio
async def test_modify_group_booking_dates_no_cascade(db_with_group_booking):
    """Test modifying group booking dates without cascading to individual bookings."""
    tool = ModifyGroupBookingTool()

    result = await tool.run_with_validation(
        db_with_group_booking,
        {
            "group_booking_id": "GRP-00012345",
            "modification_details": {
                "check_in_date": "2025-12-16T15:00:00Z",
                "check_out_date": "2025-12-19T11:00:00Z",
            },
            "cascade_to_individual_bookings": False,
        },
    )

    # Check group booking was updated
    assert result["updated_group_booking"]["check_in_date"] == "2025-12-16T15:00:00Z"
    assert result["updated_group_booking"]["check_out_date"] == "2025-12-19T11:00:00Z"

    # Check no individual bookings were modified
    assert len(result["modified_booking_references"]) == 0
    assert result["total_price_difference"] == "0.00"


@pytest.mark.anyio
async def test_modify_group_booking_dates_with_cascade(db_with_group_booking):
    """Test modifying group booking dates with cascade to individual bookings."""
    tool = ModifyGroupBookingTool()

    result = await tool.run_with_validation(
        db_with_group_booking,
        {
            "group_booking_id": "GRP-00012345",
            "modification_details": {
                "check_in_date": "2025-12-16T15:00:00Z",
                "check_out_date": "2025-12-19T11:00:00Z",
            },
            "cascade_to_individual_bookings": True,
        },
    )

    # Check group booking was updated
    assert result["updated_group_booking"]["check_in_date"] == "2025-12-16T15:00:00Z"
    assert result["updated_group_booking"]["check_out_date"] == "2025-12-19T11:00:00Z"

    # Check individual bookings were modified
    assert len(result["modified_booking_references"]) == 2
    assert "BKG-00012345" in result["modified_booking_references"]
    assert "BKG-00012346" in result["modified_booking_references"]

    # Check price difference was calculated
    assert (
        result["total_price_difference"] == "0.00"
    )  # Same number of nights (3 nights)


@pytest.mark.anyio
async def test_modify_group_booking_updates_timestamps(db_with_group_booking):
    """Test that modification updates timestamps."""
    tool = ModifyGroupBookingTool()

    result = await tool.run_with_validation(
        db_with_group_booking,
        {
            "group_booking_id": "GRP-00012345",
            "modification_details": {"check_in_date": "2025-12-16T15:00:00Z"},
            "cascade_to_individual_bookings": False,
        },
    )

    # Check updated_at was changed
    assert result["updated_group_booking"]["updated_at"] == "2025-11-25T10:00:00Z"


@pytest.mark.anyio
async def test_modify_group_booking_not_found(db_with_group_booking):
    """Test error when group booking doesn't exist."""
    tool = ModifyGroupBookingTool()

    with pytest.raises(Tool.ExecutionError) as exc_info:
        await tool.run_with_validation(
            db_with_group_booking,
            {
                "group_booking_id": "GRP-99999999",
                "modification_details": {"check_in_date": "2025-12-16T15:00:00Z"},
                "cascade_to_individual_bookings": False,
            },
        )

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_modify_group_booking_adds_modification_history(db_with_group_booking):
    """Test that individual bookings get modification history when cascaded."""
    tool = ModifyGroupBookingTool()

    await tool.run_with_validation(
        db_with_group_booking,
        {
            "group_booking_id": "GRP-00012345",
            "modification_details": {
                "check_in_date": "2025-12-16T15:00:00Z",
                "check_out_date": "2025-12-19T11:00:00Z",
            },
            "cascade_to_individual_bookings": True,
        },
    )

    # Verify modification history was added to individual bookings
    bookings = db_with_group_booking.get_all(Booking)
    for booking in bookings:
        if booking.booking_reference in ["BKG-00012345", "BKG-00012346"]:
            assert len(booking.modification_history) == 1
            assert "GRP-00012345" in booking.modification_history[0]


@pytest.mark.anyio
async def test_modify_group_booking_noop_does_not_update_history_or_timestamps(
    db_with_group_booking,
):
    """Test that setting the same dates does not create history entries or update timestamps."""
    tool = ModifyGroupBookingTool()

    # Capture original state
    original_group = db_with_group_booking.get_all(GroupBooking)[0]
    original_group_updated_at = original_group.updated_at
    original_bookings = {
        b.booking_reference: b for b in db_with_group_booking.get_all(Booking)
    }
    original_booking_updated_at = {
        ref: b.updated_at for ref, b in original_bookings.items()
    }
    original_booking_history_len = {
        ref: len(b.modification_history) for ref, b in original_bookings.items()
    }

    result = await tool.run_with_validation(
        db_with_group_booking,
        {
            "group_booking_id": "GRP-00012345",
            "modification_details": {
                # Same as existing values
                "check_in_date": "2025-12-15T15:00:00Z",
                "check_out_date": "2025-12-18T11:00:00Z",
            },
            "cascade_to_individual_bookings": True,
        },
    )

    assert result["modified_booking_references"] == []
    assert result["total_price_difference"] == "0.00"

    # Group booking should not be updated
    updated_group = db_with_group_booking.get_all(GroupBooking)[0]
    assert updated_group.updated_at == original_group_updated_at

    # Individual bookings should not be updated
    updated_bookings = {
        b.booking_reference: b for b in db_with_group_booking.get_all(Booking)
    }
    for ref in ["BKG-00012345", "BKG-00012346"]:
        assert updated_bookings[ref].updated_at == original_booking_updated_at[ref]
        assert (
            len(updated_bookings[ref].modification_history)
            == original_booking_history_len[ref]
        )


@pytest.mark.anyio
async def test_modify_group_booking_check_in_only(db_with_group_booking):
    """Test modifying only check-in date."""
    tool = ModifyGroupBookingTool()

    result = await tool.run_with_validation(
        db_with_group_booking,
        {
            "group_booking_id": "GRP-00012345",
            "modification_details": {"check_in_date": "2025-12-16T15:00:00Z"},
            "cascade_to_individual_bookings": True,
        },
    )

    # Check only check-in was updated
    assert result["updated_group_booking"]["check_in_date"] == "2025-12-16T15:00:00Z"
    assert (
        result["updated_group_booking"]["check_out_date"] == "2025-12-18T11:00:00Z"
    )  # Unchanged

    # Verify individual bookings updated
    bookings = db_with_group_booking.get_all(Booking)
    for booking in bookings:
        if booking.booking_reference in ["BKG-00012345", "BKG-00012346"]:
            assert booking.check_in_date == "2025-12-16T15:00:00Z"


@pytest.mark.anyio
async def test_modify_group_booking_check_out_only(db_with_group_booking):
    """Test modifying only check-out date."""
    tool = ModifyGroupBookingTool()

    result = await tool.run_with_validation(
        db_with_group_booking,
        {
            "group_booking_id": "GRP-00012345",
            "modification_details": {"check_out_date": "2025-12-19T11:00:00Z"},
            "cascade_to_individual_bookings": True,
        },
    )

    # Check only check-out was updated
    assert (
        result["updated_group_booking"]["check_in_date"] == "2025-12-15T15:00:00Z"
    )  # Unchanged
    assert result["updated_group_booking"]["check_out_date"] == "2025-12-19T11:00:00Z"

    # Verify individual bookings updated
    bookings = db_with_group_booking.get_all(Booking)
    for booking in bookings:
        if booking.booking_reference in ["BKG-00012345", "BKG-00012346"]:
            assert booking.check_out_date == "2025-12-19T11:00:00Z"


@pytest.mark.anyio
async def test_modify_group_booking_handles_missing_bookings(db_with_group_booking):
    """Test that tool gracefully handles missing individual bookings."""
    tool = ModifyGroupBookingTool()

    # Add a non-existent booking reference to the group
    group_bookings = db_with_group_booking.get_all(GroupBooking)
    group_bookings[0].booking_references.append("BKG-99999999")
    db_with_group_booking.update(group_bookings[0])

    result = await tool.run_with_validation(
        db_with_group_booking,
        {
            "group_booking_id": "GRP-00012345",
            "modification_details": {"check_in_date": "2025-12-16T15:00:00Z"},
            "cascade_to_individual_bookings": True,
        },
    )

    # Should only modify the 2 existing bookings, skip the missing one
    assert len(result["modified_booking_references"]) == 2
