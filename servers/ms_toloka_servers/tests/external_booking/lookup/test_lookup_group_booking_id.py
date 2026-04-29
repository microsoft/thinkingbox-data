# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from ms_toloka_servers.toolslib.external_booking.lookup.tools.lookup_hotel_id import (
    LookupHotelIdTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
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
    Test lookup by valid hotel_name.
    The hotel_name must exist in initial_data/hotels.json.
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
    assert hotel["hotel_name"] == "Grand Plaza Hotel"


@pytest.mark.anyio
async def test_lookup_hotel_by_location_success(tool, db):
    """
    Test lookup by valid location.
    Location must exist in initial_data/hotels.json.
    """
    request = {"location": "New York"}
    result = await tool.run_with_validation(db, request)

    assert "results" in result
    assert len(result["results"]) >= 1

    for hotel in result["results"]:
        assert "hotel_id" in hotel
        assert "hotel_name" in hotel
        assert "location" in hotel


@pytest.mark.anyio
async def test_lookup_hotel_no_params(tool, db):
    """
    Must fail: at least one parameter required.
    """
    with pytest.raises(tool.ExecutionError, match="Invalid parameters"):
        await tool.run_with_validation(db, {})


@pytest.mark.anyio
async def test_lookup_hotel_not_found(tool, db):
    request = {"hotel_name": "Nonexistent Hotel XYZ"}
    with pytest.raises(tool.ExecutionError, match="No hotels found"):
        await tool.run_with_validation(db, request)
