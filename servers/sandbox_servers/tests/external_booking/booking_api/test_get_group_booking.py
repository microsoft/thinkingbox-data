# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_group_booking tool."""

import pytest
from sandbox_servers.toolslib.external_booking.booking_api.models import GroupBooking
from sandbox_servers.toolslib.external_booking.booking_api.tools import (
    GetGroupBookingTool,
)
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db_with_group_bookings():
    """Create database with group bookings for testing."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)

    # Manually register models
    db._stem_to_model_cls["group_bookings"] = GroupBooking
    db._model_cls_to_stem[GroupBooking] = "group_bookings"

    # Create group bookings
    group_bookings = [
        GroupBooking(
            id="GRP-00000001",
            group_booking_id="GRP-00012345",
            coordinator_name="Alice Johnson",
            coordinator_email="alice.johnson@company.com",
            coordinator_phone="+1-555-0001",
            total_rooms=5,
            check_in_date="2025-12-15T15:00:00Z",
            check_out_date="2025-12-18T11:00:00Z",
            hotel_id="HTL-00012345",
            booking_references=[
                "BKG-00012345",
                "BKG-00012346",
                "BKG-00012347",
                "BKG-00012348",
                "BKG-00012349",
            ],
            created_at="2025-11-01T10:00:00Z",
            updated_at="2025-11-01T10:00:00Z",
        ),
        GroupBooking(
            id="GRP-00000002",
            group_booking_id="GRP-00067890",
            coordinator_name="Bob Smith",
            coordinator_email="bob.smith@event.com",
            coordinator_phone="+1-555-0002",
            total_rooms=10,
            check_in_date="2025-12-20T15:00:00Z",
            check_out_date="2025-12-22T11:00:00Z",
            hotel_id="HTL-00012346",
            booking_references=[f"BKG-000123{i:02d}" for i in range(50, 60)],
            created_at="2025-11-10T10:00:00Z",
            updated_at="2025-11-10T10:00:00Z",
        ),
    ]

    for group_booking in group_bookings:
        db.create(group_booking)

    return db


@pytest.mark.anyio
async def test_get_group_booking_success(db_with_group_bookings):
    """Test retrieving group booking details."""
    tool = GetGroupBookingTool()

    result = await tool.run_with_validation(
        db_with_group_bookings, {"group_booking_id": "GRP-00012345"}
    )

    # Check all required fields are present
    assert result["group_booking_data"]["id"] == "GRP-00000001"
    assert result["group_booking_data"]["group_booking_id"] == "GRP-00012345"
    assert result["group_booking_data"]["coordinator_name"] == "Alice Johnson"
    assert (
        result["group_booking_data"]["coordinator_email"] == "alice.johnson@company.com"
    )
    assert result["group_booking_data"]["coordinator_phone"] == "+1-555-0001"
    assert result["group_booking_data"]["total_rooms"] == 5
    assert result["group_booking_data"]["hotel_id"] == "HTL-00012345"
    assert result["group_booking_data"]["check_in_date"] == "2025-12-15T15:00:00Z"
    assert result["group_booking_data"]["check_out_date"] == "2025-12-18T11:00:00Z"

    # Check booking references array
    assert len(result["group_booking_data"]["booking_references"]) == 5
    assert "BKG-00012345" in result["group_booking_data"]["booking_references"]
    assert "BKG-00012349" in result["group_booking_data"]["booking_references"]


@pytest.mark.anyio
async def test_get_group_booking_large_group(db_with_group_bookings):
    """Test retrieving large group booking with multiple rooms."""
    tool = GetGroupBookingTool()

    result = await tool.run_with_validation(
        db_with_group_bookings, {"group_booking_id": "GRP-00067890"}
    )

    # Check total rooms count
    assert result["group_booking_data"]["total_rooms"] == 10

    # Check all booking references are included
    assert len(result["group_booking_data"]["booking_references"]) == 10
    assert "BKG-00012350" in result["group_booking_data"]["booking_references"]
    assert "BKG-00012359" in result["group_booking_data"]["booking_references"]


@pytest.mark.anyio
async def test_get_group_booking_not_found(db_with_group_bookings):
    """Test error when group booking doesn't exist."""
    tool = GetGroupBookingTool()

    with pytest.raises(Tool.ExecutionError) as exc_info:
        await tool.run_with_validation(
            db_with_group_bookings, {"group_booking_id": "GRP-99999999"}
        )

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_get_group_booking_coordinator_details(db_with_group_bookings):
    """Test that coordinator contact information is complete."""
    tool = GetGroupBookingTool()

    result = await tool.run_with_validation(
        db_with_group_bookings, {"group_booking_id": "GRP-00012345"}
    )

    # Verify all coordinator contact fields
    data = result["group_booking_data"]
    assert data["coordinator_name"] is not None
    assert data["coordinator_email"] is not None
    assert data["coordinator_phone"] is not None
    assert "@" in data["coordinator_email"]  # Valid email format


@pytest.mark.anyio
async def test_get_group_booking_timestamps(db_with_group_bookings):
    """Test that timestamps are included in response."""
    tool = GetGroupBookingTool()

    result = await tool.run_with_validation(
        db_with_group_bookings, {"group_booking_id": "GRP-00012345"}
    )

    # Check timestamps exist
    assert "created_at" in result["group_booking_data"]
    assert "updated_at" in result["group_booking_data"]
    assert result["group_booking_data"]["created_at"] == "2025-11-01T10:00:00Z"
    assert result["group_booking_data"]["updated_at"] == "2025-11-01T10:00:00Z"
