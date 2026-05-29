# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.lookup.tools.lookup_hotel_id import (
    LookupHotelIdTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def tool():
    return LookupHotelIdTool()


@pytest.mark.anyio
async def test_lookup_hotel_by_name_success(tool, db):
    """
    Provide hotel_name that exists in hotels.json.
    """
    request = {"hotel_name": "Grand Plaza Hotel"}
    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert "results" in result
    assert len(result["results"]) >= 1

    hotel = result["results"][0]
    assert "hotel_id" in hotel
    assert "hotel_name" in hotel
    assert "location" in hotel


@pytest.mark.anyio
async def test_lookup_hotel_by_location_success(tool, db):
    """
    Provide location that exists in hotels.json.
    """
    request = {"location": "New York"}
    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert "results" in result
    assert len(result["results"]) >= 1

    hotel = result["results"][0]
    assert "hotel_id" in hotel
    assert "hotel_name" in hotel
    assert "location" in hotel


@pytest.mark.anyio
async def test_lookup_hotel_missing_parameters(tool, db):
    """
    Neither hotel_name nor location → must raise 400-like error.
    """
    with pytest.raises(tool.ExecutionError, match="Invalid"):
        await tool.run_with_validation(db, {})


@pytest.mark.anyio
async def test_lookup_hotel_not_found(tool, db):
    """
    No hotels match → 404 behavior with ExecutionError.
    """
    with pytest.raises(tool.ExecutionError, match="No hotels found"):
        await tool.run_with_validation(db, {"hotel_name": "Unobtainium Hotel"})
