# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_hotel_info tool."""

import pytest
from sandbox_servers.toolslib.external_booking.hotel_partner_api.models import Hotel
from sandbox_servers.toolslib.external_booking.hotel_partner_api.tools.get_hotel_info import (
    GetHotelInfo,
)
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.mark.anyio
async def test_get_hotel_info_success(db):
    """Test successful retrieval of hotel information."""
    tool = GetHotelInfo()

    result = await tool.run_with_validation(db, {"hotel_id": "HTL-00012345"})

    assert result["hotel_data"]["hotel_id"] == "HTL-00012345"
    assert result["hotel_data"]["hotel_name"] == "Grand Plaza Hotel"
    assert result["hotel_data"]["location"] == "New York"


@pytest.mark.anyio
async def test_get_hotel_info_all_fields(db):
    """Test that all hotel fields are returned."""
    tool = GetHotelInfo()

    result = await tool.run_with_validation(db, {"hotel_id": "HTL-00012345"})

    hotel_data = result["hotel_data"]
    assert "id" in hotel_data
    assert "hotel_id" in hotel_data
    assert "hotel_name" in hotel_data
    assert "location" in hotel_data
    assert "partner_tier" in hotel_data
    assert "contact_name" in hotel_data
    assert "contact_email" in hotel_data
    assert "contact_phone" in hotel_data
    assert "escalation_contact" in hotel_data
    assert "amenities" in hotel_data
    assert "supports_pets" in hotel_data
    assert "accessible_rooms_available" in hotel_data
    assert "created_at" in hotel_data
    assert "updated_at" in hotel_data


@pytest.mark.anyio
async def test_get_hotel_info_premium_tier(db):
    """Test getting hotel with premium tier."""
    tool = GetHotelInfo()

    result = await tool.run_with_validation(db, {"hotel_id": "HTL-00012345"})

    assert result["hotel_data"]["partner_tier"] == "premium"
    assert result["hotel_data"]["escalation_contact"] == "director@grandplaza.com"
    assert result["hotel_data"]["supports_pets"] is True
    assert result["hotel_data"]["accessible_rooms_available"] is True


@pytest.mark.anyio
async def test_get_hotel_info_standard_tier(db):
    """Test getting hotel with standard tier."""
    tool = GetHotelInfo()

    result = await tool.run_with_validation(db, {"hotel_id": "HTL-00012346"})

    assert result["hotel_data"]["partner_tier"] == "standard"
    assert result["hotel_data"].get("escalation_contact") is None
    assert result["hotel_data"]["supports_pets"] is False


@pytest.mark.anyio
async def test_get_hotel_info_amenities(db):
    """Test that amenities array is returned correctly."""
    tool = GetHotelInfo()

    result = await tool.run_with_validation(db, {"hotel_id": "HTL-00012345"})

    amenities = result["hotel_data"]["amenities"]
    assert isinstance(amenities, list)
    assert "pool" in amenities
    assert "gym" in amenities
    assert "spa" in amenities


@pytest.mark.anyio
async def test_get_hotel_info_contact_details(db):
    """Test that contact details are returned correctly."""
    tool = GetHotelInfo()

    result = await tool.run_with_validation(db, {"hotel_id": "HTL-00012345"})

    assert result["hotel_data"]["contact_name"] == "Marcus Whitfield"
    assert result["hotel_data"]["contact_email"] == "manager@grandplaza.com"
    assert result["hotel_data"]["contact_phone"] == "+1-212-738-4501"


@pytest.mark.anyio
async def test_get_hotel_info_not_found(db):
    """Test getting non-existent hotel."""
    tool = GetHotelInfo()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(db, {"hotel_id": "HTL-99999999"})

    assert "hotel not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_get_hotel_info_from_fresh_db():
    """Test getting hotel from database without fixture."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)
    db._stem_to_model_cls["hotels"] = Hotel
    db._model_cls_to_stem[Hotel] = "hotels"

    hotel = Hotel(
        id="HTL-00000001",
        hotel_id="HTL-TEST-001",
        hotel_name="Test Hotel",
        location="Test City",
        partner_tier="budget",
        contact_name="Test Contact",
        contact_email="test@hotel.com",
        contact_phone="+1-555-9999",
        escalation_contact=None,
        amenities=["wifi"],
        supports_pets=False,
        accessible_rooms_available=False,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    db.create(hotel)

    tool = GetHotelInfo()
    result = await tool.run_with_validation(db, {"hotel_id": "HTL-TEST-001"})

    assert result["hotel_data"]["hotel_name"] == "Test Hotel"
    assert result["hotel_data"]["partner_tier"] == "budget"
