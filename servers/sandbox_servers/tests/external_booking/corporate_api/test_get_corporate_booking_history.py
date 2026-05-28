# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from sandbox_servers.toolslib.external_booking.corporate_api.tools.get_corporate_booking_history import (
    GetCorporateBookingHistoryTool,
)
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def tool():
    return GetCorporateBookingHistoryTool()


@pytest.mark.anyio
async def test_get_booking_history_success(tool, db):
    request = {"corporate_account_id": "CRP-00012345"}

    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert "corporate_bookings" in result
    assert isinstance(result["corporate_bookings"], list)
    assert len(result["corporate_bookings"]) >= 1

    for b in result["corporate_bookings"]:
        assert "booking_reference" in b
        assert "hotel_id" in b

        # Verify booking has correct corporate_account_id
        from sandbox_servers.toolslib.external_booking.booking_api.models import (
            Booking,
        )

        original = next(
            ob
            for ob in db.get_all(Booking)
            if ob.booking_reference == b["booking_reference"]
        )
        assert original.corporate_account_id == "CRP-00012345"


@pytest.mark.anyio
async def test_get_booking_history_no_bookings(tool, db):
    result = await tool.run_with_validation(
        db, {"corporate_account_id": "CRP-00030000"}
    )
    assert result["corporate_bookings"] == []


@pytest.mark.anyio
async def test_get_booking_history_account_not_found(tool, db):
    with pytest.raises(tool.ExecutionError, match="not found"):
        await tool.run_with_validation(db, {"corporate_account_id": "CRP-404"})
