# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from ms_toloka_servers.toolslib.external_booking.lookup.tools.validate_booking_reference import (
    ValidateBookingReferenceTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def tool():
    return ValidateBookingReferenceTool()


@pytest.mark.anyio
async def test_validate_booking_reference_success(tool, db):
    """
    Positive case: booking_reference exists in initial_data/bookings.json.
    """
    request = {"booking_reference": "BKG-00012345"}
    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert result["is_valid"] is True
    assert isinstance(result["booking_id"], str)
    assert result["booking_id"].startswith("BKG-")


@pytest.mark.anyio
async def test_validate_booking_reference_not_found(tool, db):
    """
    If reference is correctly formatted but does not exist -> is_valid=False.
    """
    request = {"booking_reference": "BKG-99999999"}
    result = await tool.run_with_validation(db, request)

    assert result["is_valid"] is False
    assert "booking_id" not in result


@pytest.mark.anyio
async def test_validate_booking_reference_invalid_format(tool, db):
    """
    Format must match BKG-######## or raise 400-type ExecutionError.
    """
    with pytest.raises(tool.ExecutionError, match="Invalid booking reference format"):
        await tool.run_with_validation(db, {"booking_reference": "WRONG-123"})


@pytest.mark.anyio
async def test_validate_booking_reference_missing(tool, db):
    """
    Missing parameter should trigger Pydantic/MCP-core validation error.
    """
    with pytest.raises(tool.ExecutionError, match="Field required"):
        await tool.run_with_validation(db, {})
