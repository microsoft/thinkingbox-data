# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from ms_toloka_servers.toolslib.external_booking.crm_api.tools.check_vip_status import (
    CrmApiCheckVipStatusTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def tool():
    return CrmApiCheckVipStatusTool()


@pytest.fixture
def db():
    """Load CRM API mock customer profile data."""
    base_dir = pathlib.Path(__file__).parents[3]
    data_dir = (
        base_dir
        / "ms_toloka_servers"
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
                "ms_toloka_servers.toolslib.external_booking.crm_api.models",
            )
        },
    )


@pytest.mark.anyio
async def test_check_vip_status_success_standard(tool, db):
    request = {"customer_id": "CUS-00000001"}

    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert result["vip_tier"] == "standard"
    assert result["loyalty_program_status"] == "member"


@pytest.mark.anyio
async def test_check_vip_status_success_vip(tool, db):
    request = {"customer_id": "CUS-00000002"}

    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert result["vip_tier"] == "vip"
    assert result["loyalty_program_status"] == "silver"


@pytest.mark.anyio
async def test_check_vip_status_not_found(tool, db):
    with pytest.raises(tool.ExecutionError, match="Customer not found"):
        await tool.run_with_validation(db, {"customer_id": "CUS-99999999"})


@pytest.mark.anyio
async def test_check_vip_status_invalid_id(tool, db):
    with pytest.raises(tool.ExecutionError, match="Invalid customer_id"):
        await tool.run_with_validation(db, {"customer_id": ""})
