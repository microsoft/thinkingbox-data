# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_hotel_contact tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.hotel_partner_api.tools.get_hotel_contact import (
    GetHotelContact,
    GetHotelContactInput,
)


@pytest.mark.anyio
async def test_get_hotel_contact_success(db):
    """Test getting hotel contact information successfully."""
    tool = GetHotelContact()

    request = GetHotelContactInput(hotel_id="HTL-00012345")

    result = await tool.run(db, request)

    assert result.contact_name == "Marcus Whitfield"
    assert result.contact_email == "manager@grandplaza.com"
    assert result.contact_phone == "+1-212-738-4501"
    assert result.escalation_contact == "director@grandplaza.com"


@pytest.mark.anyio
async def test_get_hotel_contact_with_escalation(db):
    """Test getting hotel contact with escalation contact."""
    tool = GetHotelContact()

    request = GetHotelContactInput(hotel_id="HTL-00012348")

    result = await tool.run(db, request)

    assert result.contact_name == "Nina Caldwell"
    assert result.contact_email == "contact@beachresort.com"
    assert result.contact_phone == "+1-786-421-7063"
    assert result.escalation_contact == "manager@beachresort.com"


@pytest.mark.anyio
async def test_get_hotel_contact_without_escalation(db):
    """Test getting hotel contact without escalation contact."""
    tool = GetHotelContact()

    request = GetHotelContactInput(hotel_id="HTL-00012346")

    result = await tool.run(db, request)

    assert result.contact_name == "Linda Vasquez"
    assert result.contact_email == "contact@citycenter.com"
    assert result.contact_phone == "+1-212-493-2817"
    assert result.escalation_contact is None


@pytest.mark.anyio
async def test_get_hotel_contact_not_found(db):
    """Test error when hotel not found."""
    tool = GetHotelContact()

    request = GetHotelContactInput(hotel_id="HTL-INVALID")

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "Hotel not found" in str(exc_info.value)


@pytest.mark.anyio
async def test_get_hotel_contact_all_hotels(db):
    """Test getting contact info for all hotels."""
    tool = GetHotelContact()

    # Test all 5 hotels
    hotel_ids = [
        "HTL-00012345",
        "HTL-00012346",
        "HTL-00012347",
        "HTL-00012348",
        "HTL-00012349",
    ]

    for hotel_id in hotel_ids:
        request = GetHotelContactInput(hotel_id=hotel_id)
        result = await tool.run(db, request)

        # Verify all required fields are present
        assert result.contact_name
        assert result.contact_email
        assert result.contact_phone
        # escalation_contact is optional
