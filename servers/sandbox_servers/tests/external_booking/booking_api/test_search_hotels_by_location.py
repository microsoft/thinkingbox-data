# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for search_hotels_by_location tool."""

import pytest
from sandbox_servers.toolslib.external_booking.booking_api.models import (
    BoardType,
    HotelInventory,
    HotelPartnerTier,
    RoomType,
)
from sandbox_servers.toolslib.external_booking.booking_api.tools import (
    SearchHotelsByLocationTool,
)
from sandbox_servers.toolslib.external_booking.hotel_partner_api.models import Hotel
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db():
    """Create database with hotels and inventory for testing."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)

    # Manually register models
    db._stem_to_model_cls["hotels"] = Hotel
    db._model_cls_to_stem[Hotel] = "hotels"
    db._stem_to_model_cls["hotel_inventory"] = HotelInventory
    db._model_cls_to_stem[HotelInventory] = "hotel_inventory"

    # Hotels in different locations
    hotels = [
        Hotel(
            id="HTL-00000001",
            hotel_id="HTL-00012345",
            hotel_name="Grand Plaza Hotel",
            location="New York",
            partner_tier=HotelPartnerTier.PREMIUM,
            contact_name="John Manager",
            contact_email="manager@grandplaza.com",
            contact_phone="+1-555-0001",
            escalation_contact="director@grandplaza.com",
            amenities=["pool", "gym", "spa"],
            supports_pets=True,
            accessible_rooms_available=True,
            created_at="2025-01-01T10:00:00Z",
            updated_at="2025-01-01T10:00:00Z",
        ),
        Hotel(
            id="HTL-00000002",
            hotel_id="HTL-00012346",
            hotel_name="City Center Inn",
            location="New York",
            partner_tier=HotelPartnerTier.STANDARD,
            contact_name="Jane Smith",
            contact_email="contact@citycenter.com",
            contact_phone="+1-555-0002",
            escalation_contact=None,
            amenities=["wifi", "parking"],
            supports_pets=False,
            accessible_rooms_available=True,
            created_at="2025-01-01T10:00:00Z",
            updated_at="2025-01-01T10:00:00Z",
        ),
        Hotel(
            id="HTL-00000003",
            hotel_id="HTL-00012347",
            hotel_name="Downtown Budget Hotel",
            location="New York",
            partner_tier=HotelPartnerTier.BUDGET,
            contact_name="Bob Johnson",
            contact_email="info@budgethotel.com",
            contact_phone="+1-555-0003",
            escalation_contact=None,
            amenities=["wifi"],
            supports_pets=False,
            accessible_rooms_available=False,
            created_at="2025-01-01T10:00:00Z",
            updated_at="2025-01-01T10:00:00Z",
        ),
        Hotel(
            id="HTL-00000004",
            hotel_id="HTL-00012348",
            hotel_name="Beach Resort Hotel",
            location="Miami",
            partner_tier=HotelPartnerTier.PREMIUM,
            contact_name="Alice Brown",
            contact_email="contact@beachresort.com",
            contact_phone="+1-555-0004",
            escalation_contact="manager@beachresort.com",
            amenities=["pool", "beach", "restaurant"],
            supports_pets=True,
            accessible_rooms_available=True,
            created_at="2025-01-01T10:00:00Z",
            updated_at="2025-01-01T10:00:00Z",
        ),
    ]

    for hotel in hotels:
        db.create(hotel)

    # Inventory for hotels (availability for search dates)
    # Grand Plaza Hotel - has availability
    for day in range(15, 19):  # Dec 15-18
        db.create(
            HotelInventory(
                id=f"INV-{day:08d}",
                hotel_id="HTL-00012345",
                room_type=RoomType.DELUXE_ROOM,
                board_type=BoardType.WITH_BREAKFAST,
                date=f"2025-12-{day}T00:00:00Z",
                available_count=5,
                price_per_night=150.00,
                created_at="2025-01-01T10:00:00Z",
                updated_at="2025-01-01T10:00:00Z",
            )
        )

    # City Center Inn - has availability
    for day in range(15, 19):  # Dec 15-18
        db.create(
            HotelInventory(
                id=f"INV-1{day:07d}",
                hotel_id="HTL-00012346",
                room_type=RoomType.DELUXE_ROOM,
                board_type=BoardType.WITH_BREAKFAST,
                date=f"2025-12-{day}T00:00:00Z",
                available_count=3,
                price_per_night=120.00,
                created_at="2025-01-01T10:00:00Z",
                updated_at="2025-01-01T10:00:00Z",
            )
        )

    # Downtown Budget Hotel - NO availability (0 rooms)
    for day in range(15, 19):  # Dec 15-18
        db.create(
            HotelInventory(
                id=f"INV-2{day:07d}",
                hotel_id="HTL-00012347",
                room_type=RoomType.DELUXE_ROOM,
                board_type=BoardType.WITH_BREAKFAST,
                date=f"2025-12-{day}T00:00:00Z",
                available_count=0,
                price_per_night=80.00,
                created_at="2025-01-01T10:00:00Z",
                updated_at="2025-01-01T10:00:00Z",
            )
        )

    # Beach Resort Hotel - different location, has availability
    for day in range(15, 19):  # Dec 15-18
        db.create(
            HotelInventory(
                id=f"INV-3{day:07d}",
                hotel_id="HTL-00012348",
                room_type=RoomType.DELUXE_ROOM,
                board_type=BoardType.WITH_BREAKFAST,
                date=f"2025-12-{day}T00:00:00Z",
                available_count=10,
                price_per_night=200.00,
                created_at="2025-01-01T10:00:00Z",
                updated_at="2025-01-01T10:00:00Z",
            )
        )

    return db


@pytest.mark.anyio
async def test_search_hotels_success(db):
    """Test searching for hotels in New York with availability."""
    tool = SearchHotelsByLocationTool()

    result = await tool.run_with_validation(
        db,
        {
            "location": "New York",
            "check_in_date": "2025-12-15T15:00:00Z",
            "check_out_date": "2025-12-18T11:00:00Z",
            "room_type": "deluxe_room",
            "board_type": "with_breakfast",
            "adults_count": 2,
            "children_count": 1,
        },
    )

    # Should return 2 hotels (Grand Plaza and City Center Inn)
    # Downtown Budget Hotel has 0 availability, so it's excluded
    assert len(result["hotels"]) == 2

    # Check hotel details are included
    hotel_ids = [h["hotel_id"] for h in result["hotels"]]
    assert "HTL-00012345" in hotel_ids
    assert "HTL-00012346" in hotel_ids
    assert "HTL-00012347" not in hotel_ids  # No availability

    # Check required fields are present
    first_hotel = result["hotels"][0]
    assert "hotel_id" in first_hotel
    assert "hotel_name" in first_hotel
    assert "location" in first_hotel
    assert "partner_tier" in first_hotel
    assert "available_count" in first_hotel
    assert "price_per_night" in first_hotel


@pytest.mark.anyio
async def test_search_hotels_case_insensitive(db):
    """Test that location search is case-insensitive."""
    tool = SearchHotelsByLocationTool()

    # Search with lowercase
    result = await tool.run_with_validation(
        db,
        {
            "location": "new york",
            "check_in_date": "2025-12-15T15:00:00Z",
            "check_out_date": "2025-12-18T11:00:00Z",
            "room_type": "deluxe_room",
            "board_type": "with_breakfast",
            "adults_count": 2,
            "children_count": 0,
        },
    )

    # Should still find hotels
    assert len(result["hotels"]) == 2


@pytest.mark.anyio
async def test_search_hotels_partial_match(db):
    """Test that location search supports partial matching."""
    tool = SearchHotelsByLocationTool()

    # Search with partial location
    result = await tool.run_with_validation(
        db,
        {
            "location": "York",
            "check_in_date": "2025-12-15T15:00:00Z",
            "check_out_date": "2025-12-18T11:00:00Z",
            "room_type": "deluxe_room",
            "board_type": "with_breakfast",
            "adults_count": 2,
            "children_count": 0,
        },
    )

    # Should find New York hotels
    assert len(result["hotels"]) == 2


@pytest.mark.anyio
async def test_search_hotels_different_location(db):
    """Test searching in different location."""
    tool = SearchHotelsByLocationTool()

    result = await tool.run_with_validation(
        db,
        {
            "location": "Miami",
            "check_in_date": "2025-12-15T15:00:00Z",
            "check_out_date": "2025-12-18T11:00:00Z",
            "room_type": "deluxe_room",
            "board_type": "with_breakfast",
            "adults_count": 2,
            "children_count": 0,
        },
    )

    # Should return 1 hotel (Beach Resort)
    assert len(result["hotels"]) == 1
    assert result["hotels"][0]["hotel_id"] == "HTL-00012348"
    assert result["hotels"][0]["location"] == "Miami"


@pytest.mark.anyio
async def test_search_hotels_no_match(db):
    """Test searching for location with no hotels."""
    tool = SearchHotelsByLocationTool()

    result = await tool.run_with_validation(
        db,
        {
            "location": "Los Angeles",
            "check_in_date": "2025-12-15T15:00:00Z",
            "check_out_date": "2025-12-18T11:00:00Z",
            "room_type": "deluxe_room",
            "board_type": "with_breakfast",
            "adults_count": 2,
            "children_count": 0,
        },
    )

    # Should return empty array
    assert len(result["hotels"]) == 0


@pytest.mark.anyio
async def test_search_hotels_no_availability(db):
    """Test that hotels without availability are excluded."""
    tool = SearchHotelsByLocationTool()

    # Search for dates with no inventory
    result = await tool.run_with_validation(
        db,
        {
            "location": "New York",
            "check_in_date": "2025-12-20T15:00:00Z",
            "check_out_date": "2025-12-22T11:00:00Z",
            "room_type": "deluxe_room",
            "board_type": "with_breakfast",
            "adults_count": 2,
            "children_count": 0,
        },
    )

    # Should return empty array (no inventory for these dates)
    assert len(result["hotels"]) == 0


@pytest.mark.anyio
async def test_search_hotels_price_included(db):
    """Test that average price per night is included in results."""
    tool = SearchHotelsByLocationTool()

    result = await tool.run_with_validation(
        db,
        {
            "location": "New York",
            "check_in_date": "2025-12-15T15:00:00Z",
            "check_out_date": "2025-12-18T11:00:00Z",
            "room_type": "deluxe_room",
            "board_type": "with_breakfast",
            "adults_count": 2,
            "children_count": 0,
        },
    )

    # Check prices are included
    for hotel in result["hotels"]:
        assert "price_per_night" in hotel
        # Decimal serialized as string, check it's a valid positive number
        from decimal import Decimal

        assert Decimal(hotel["price_per_night"]) > 0

    # Grand Plaza should have higher price
    grand_plaza = next(h for h in result["hotels"] if h["hotel_id"] == "HTL-00012345")
    city_center = next(h for h in result["hotels"] if h["hotel_id"] == "HTL-00012346")

    assert (
        grand_plaza["price_per_night"] == "150.00"
    )  # Decimal serialized as string with 2 decimal places
    assert (
        city_center["price_per_night"] == "120.00"
    )  # Decimal serialized as string with 2 decimal places
