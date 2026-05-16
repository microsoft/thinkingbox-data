# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for verify_availability tool."""

import pytest
from ms_toloka_servers.toolslib.external_booking.hotel_partner_api.tools.verify_availability import (
    VerifyAvailability,
    VerifyAvailabilityInput,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.mark.anyio
async def test_verify_availability_available(db):
    """Test verifying availability when rooms are available."""
    tool = VerifyAvailability()

    request = VerifyAvailabilityInput(
        hotel_id="HTL-00012345",
        check_in_date="2025-12-15",
        check_out_date="2025-12-17",
        room_type="deluxe_room",
        board_type="with_breakfast",
        adults_count=2,
        children_count=0,
    )

    result = await tool.run(db, request)

    assert result.availability_confirmed is True
    assert "5 rooms available" in result.confirmation_notes.lower()


@pytest.mark.anyio
async def test_verify_availability_limited(db):
    """Test verifying availability with limited rooms."""
    tool = VerifyAvailability()

    request = VerifyAvailabilityInput(
        hotel_id="HTL-00012346",
        check_in_date="2025-12-15",
        check_out_date="2025-12-16",
        room_type="deluxe_room",
        board_type="with_breakfast",
        adults_count=2,
        children_count=1,
    )

    result = await tool.run(db, request)

    assert result.availability_confirmed is True
    assert "3 rooms available" in result.confirmation_notes.lower()


@pytest.mark.anyio
async def test_verify_availability_unavailable(db):
    """Test verifying availability when no inventory data exists for dates."""
    tool = VerifyAvailability()

    request = VerifyAvailabilityInput(
        hotel_id="HTL-00012347",
        check_in_date="2025-12-20",
        check_out_date="2025-12-22",
        room_type="suite",
        board_type="all_inclusive",
        adults_count=2,
        children_count=0,
    )

    result = await tool.run(db, request)

    assert result.availability_confirmed is False
    assert "no inventory" in result.confirmation_notes.lower()


@pytest.mark.anyio
async def test_verify_availability_no_inventory_data(db):
    """Test verifying availability when no inventory data exists."""
    tool = VerifyAvailability()

    request = VerifyAvailabilityInput(
        hotel_id="HTL-00012349",
        check_in_date="2025-12-01",
        check_out_date="2025-12-03",
        room_type="standard_room",
        board_type="without_breakfast",
        adults_count=1,
        children_count=0,
    )

    result = await tool.run(db, request)

    assert result.availability_confirmed is False
    assert "no inventory data" in result.confirmation_notes.lower()


@pytest.mark.anyio
async def test_verify_availability_hotel_not_found(db):
    """Test error when hotel not found."""
    tool = VerifyAvailability()

    request = VerifyAvailabilityInput(
        hotel_id="HTL-INVALID",
        check_in_date="2025-12-01",
        check_out_date="2025-12-03",
        room_type="standard_room",
        board_type="with_breakfast",
        adults_count=2,
        children_count=0,
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "Hotel not found" in str(exc_info.value)


@pytest.mark.anyio
async def test_verify_availability_multiple_dates(db):
    """Test verifying availability across multiple dates."""
    tool = VerifyAvailability()

    # Test with HTL-00012345 which has 5 rooms for multiple dates
    request = VerifyAvailabilityInput(
        hotel_id="HTL-00012345",
        check_in_date="2025-12-15",
        check_out_date="2025-12-18",
        room_type="deluxe_room",
        board_type="with_breakfast",
        adults_count=2,
        children_count=2,
    )

    result = await tool.run(db, request)

    assert result.availability_confirmed is True
    assert "5 rooms available" in result.confirmation_notes.lower()
