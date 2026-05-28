# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for check_hotel_availability tool."""

import pytest
from sandbox_servers.toolslib.external_booking.booking_api.models import (
    BoardType,
    HotelInventory,
    HotelPartnerTier,
    RoomType,
)
from sandbox_servers.toolslib.external_booking.booking_api.tools import (
    CheckHotelAvailabilityTool,
)
from sandbox_servers.toolslib.external_booking.hotel_partner_api.models import Hotel
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db_with_hotel_and_inventory():
    """Create a database with test hotel and inventory."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)

    # Register models
    db._stem_to_model_cls["hotels"] = Hotel
    db._model_cls_to_stem[Hotel] = "hotels"
    db._stem_to_model_cls["hotel_inventory"] = HotelInventory
    db._model_cls_to_stem[HotelInventory] = "hotel_inventory"

    # Add test hotel
    hotel = Hotel(
        id="HTL-00012345",
        hotel_id="HTL-00012345",
        hotel_name="Grand Plaza Hotel",
        location="New York",
        partner_tier=HotelPartnerTier.PREMIUM,
        contact_name="John Manager",
        contact_email="manager@grandplaza.com",
        contact_phone="+1-555-0123",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    db.create(hotel)

    # Add inventory for multiple dates and room/board combinations
    dates = ["2025-12-15T00:00:00Z", "2025-12-16T00:00:00Z", "2025-12-17T00:00:00Z"]

    for i, date_str in enumerate(dates):
        # Deluxe room with breakfast
        inv1 = HotelInventory(
            id=f"INV-{i:08d}01",
            hotel_id="HTL-00012345",
            room_type=RoomType.DELUXE_ROOM,
            board_type=BoardType.WITH_BREAKFAST,
            date=date_str,
            available_count=5,
            price_per_night=150.00,
            created_at="2025-11-01T00:00:00Z",
            updated_at="2025-11-01T00:00:00Z",
        )
        db.create(inv1)

        # Deluxe room without breakfast
        inv2 = HotelInventory(
            id=f"INV-{i:08d}02",
            hotel_id="HTL-00012345",
            room_type=RoomType.DELUXE_ROOM,
            board_type=BoardType.WITHOUT_BREAKFAST,
            date=date_str,
            available_count=3,
            price_per_night=120.00,
            created_at="2025-11-01T00:00:00Z",
            updated_at="2025-11-01T00:00:00Z",
        )
        db.create(inv2)

        # Suite with half board
        inv3 = HotelInventory(
            id=f"INV-{i:08d}03",
            hotel_id="HTL-00012345",
            room_type=RoomType.SUITE,
            board_type=BoardType.HALF_BOARD,
            date=date_str,
            available_count=2,
            price_per_night=250.00,
            created_at="2025-11-01T00:00:00Z",
            updated_at="2025-11-01T00:00:00Z",
        )
        db.create(inv3)

    return db


@pytest.mark.anyio
async def test_check_availability_success(db_with_hotel_and_inventory):
    """Test successful availability check."""
    tool = CheckHotelAvailabilityTool()

    result = await tool.run_with_validation(
        db_with_hotel_and_inventory,
        {
            "hotel_id": "HTL-00012345",
            "check_in_date": "2025-12-15T15:00:00Z",
            "check_out_date": "2025-12-18T11:00:00Z",
            "room_type": "deluxe_room",
            "board_type": "with_breakfast",
            "adults_count": 2,
            "children_count": 1,
        },
    )

    assert result["available_count"] == 5
    assert "available_board_types" in result
    assert len(result["available_board_types"]) > 0


@pytest.mark.anyio
async def test_check_availability_multiple_board_types(db_with_hotel_and_inventory):
    """Test that available_board_types includes all options for the room type."""
    tool = CheckHotelAvailabilityTool()

    result = await tool.run_with_validation(
        db_with_hotel_and_inventory,
        {
            "hotel_id": "HTL-00012345",
            "check_in_date": "2025-12-15T15:00:00Z",
            "check_out_date": "2025-12-18T11:00:00Z",
            "room_type": "deluxe_room",
            "board_type": "with_breakfast",
            "adults_count": 2,
            "children_count": 0,
        },
    )

    # Should include both with_breakfast and without_breakfast
    assert "with_breakfast" in result["available_board_types"]
    assert "without_breakfast" in result["available_board_types"]


@pytest.mark.anyio
async def test_check_availability_no_inventory(db_with_hotel_and_inventory):
    """Test checking availability when no inventory exists."""
    tool = CheckHotelAvailabilityTool()

    result = await tool.run_with_validation(
        db_with_hotel_and_inventory,
        {
            "hotel_id": "HTL-00012345",
            "check_in_date": "2025-12-15T15:00:00Z",
            "check_out_date": "2025-12-18T11:00:00Z",
            "room_type": "presidential_suite",  # No inventory for this room type
            "board_type": "all_inclusive",
            "adults_count": 2,
            "children_count": 0,
        },
    )

    assert result["available_count"] == 0
    assert result["available_board_types"] == []


@pytest.mark.anyio
async def test_check_availability_hotel_not_found(db_with_hotel_and_inventory):
    """Test checking availability for non-existent hotel."""
    tool = CheckHotelAvailabilityTool()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_hotel_and_inventory,
            {
                "hotel_id": "HTL-99999999",
                "check_in_date": "2025-12-15T15:00:00Z",
                "check_out_date": "2025-12-18T11:00:00Z",
                "room_type": "deluxe_room",
                "board_type": "with_breakfast",
                "adults_count": 2,
                "children_count": 0,
            },
        )

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_check_availability_invalid_dates(db_with_hotel_and_inventory):
    """Test that check-in must be before check-out."""
    tool = CheckHotelAvailabilityTool()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_hotel_and_inventory,
            {
                "hotel_id": "HTL-00012345",
                "check_in_date": "2025-12-18T15:00:00Z",
                "check_out_date": "2025-12-15T11:00:00Z",  # Before check-in
                "room_type": "deluxe_room",
                "board_type": "with_breakfast",
                "adults_count": 2,
                "children_count": 0,
            },
        )

    assert "before" in str(exc_info.value).lower()
