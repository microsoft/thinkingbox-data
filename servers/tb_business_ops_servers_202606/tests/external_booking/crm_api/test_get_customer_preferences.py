# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.crm_api.tools.get_customer_preferences import (
    CrmApiGetCustomerPreferencesTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
)


@pytest.fixture
def tool():
    return CrmApiGetCustomerPreferencesTool()


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
async def test_get_customer_preferences_success(tool, db):
    request = {"customer_id": "CUS-00000001"}

    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert "preferences" in result
    assert "special_notes" in result

    assert result["preferences"] == ["high floor", "late checkout"]
    assert result["special_notes"] == ["requested quiet rooms in past stays"]


@pytest.mark.anyio
async def test_get_customer_preferences_no_notes(tool, db):
    """Customer exists but has empty arrays (CUS-00000004)."""
    request = {"customer_id": "CUS-00000004"}

    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert result["preferences"] == []
    assert result["special_notes"] == []


@pytest.mark.anyio
async def test_get_customer_preferences_not_found(tool, db):
    with pytest.raises(tool.ExecutionError, match="Customer not found"):
        await tool.run_with_validation(db, {"customer_id": "CUS-XXXXXXXX"})


@pytest.mark.anyio
async def test_get_customer_preferences_invalid_id(tool, db):
    with pytest.raises(tool.ExecutionError, match="Invalid customer_id"):
        await tool.run_with_validation(db, {"customer_id": ""})
