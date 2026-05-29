# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.crm_api.tools.get_customer_profile import (
    CrmApiGetCustomerProfileTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def tool():
    return CrmApiGetCustomerProfileTool()


@pytest.fixture
def db():
    """Load CRM API mock customer profile data."""
    base_dir = pathlib.Path(__file__).parents[3]
    data_dir = (
        base_dir
        / "tb_business_ops_servers_202606"
        / "toolslib"
        / "external_booking"
        / "crm_api"
        / "initial_data"
    )

    return InMemoryDatabase(
        domain=STUB_DOMAIN,
        additional_sources={
            "crm_api": (
                str(data_dir),
                "tb_business_ops_servers_202606.toolslib.external_booking.crm_api.models",
            )
        },
    )


@pytest.mark.anyio
async def test_get_customer_profile_success(tool, db):
    request = {"customer_id": "CUS-00000001"}

    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert "customer_data" in result

    data = result["customer_data"]

    assert data["customer_id"] == "CUS-00000001"
    assert data["full_name"] == "Alice Thompson"
    assert data["vip_tier"] == "standard"
    assert data["total_bookings_count"] == 5
    assert data["preferences"] == ["high floor", "late checkout"]


@pytest.mark.anyio
async def test_get_customer_profile_not_found(tool, db):
    with pytest.raises(tool.ExecutionError, match="Customer not found"):
        await tool.run_with_validation(db, {"customer_id": "CUS-99999999"})


@pytest.mark.anyio
async def test_get_customer_profile_invalid_id(tool, db):
    with pytest.raises(tool.ExecutionError, match="Invalid parameters"):
        await tool.run_with_validation(db, {"customer_id": ""})


@pytest.mark.anyio
async def test_get_customer_profile_by_email_success(tool, db):
    """Lookup customer profile using email address."""
    request = {"email": "alice.thompson@gmail.com"}  # Use email from test data
    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert "customer_data" in result
    assert result["customer_data"]["customer_id"].startswith("CUS-")


@pytest.mark.anyio
async def test_get_customer_profile_email_case_insensitive(tool, db):
    """Email lookup should be case-insensitive."""
    request = {"email": "ALICE.THOMPSON@GMAIL.COM"}
    result = await tool.run_with_validation(db, request)

    assert result["customer_data"]["customer_id"].startswith("CUS-")


@pytest.mark.anyio
async def test_get_customer_profile_missing_parameters(tool, db):
    """Neither customer_id nor email provided."""
    with pytest.raises(tool.ExecutionError, match="Invalid parameters"):
        await tool.run_with_validation(db, {})


@pytest.mark.anyio
async def test_get_customer_profile_email_not_found(tool, db):
    """Email does not exist in system."""
    with pytest.raises(tool.ExecutionError, match="Customer not found"):
        await tool.run_with_validation(db, {"email": "nonexistent@nowhere.com"})
