# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.corporate_api.tools.get_account_details import (
    GetAccountDetailsTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def tool():
    return GetAccountDetailsTool()


@pytest.fixture
def db():
    """Load corporate API mock data via initial_data loader."""
    base_dir = pathlib.Path(__file__).parents[3]
    data_dir = (
        base_dir
        / "tb_business_ops_servers_202606"
        / "toolslib"
        / "external_booking"
        / "corporate_api"
        / "initial_data"
    )

    return InMemoryDatabase(
        domain=STUB_DOMAIN,
        additional_sources={
            "corporate_api": (
                str(data_dir),
                "tb_business_ops_servers_202606.toolslib.external_booking.corporate_api.models",
            )
        },
    )


@pytest.mark.anyio
async def test_get_account_details_success(tool, db):
    request = {"corporate_account_id": "CRP-00012345"}

    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert "account_data" in result

    acc = result["account_data"]

    assert acc["corporate_account_id"] == "CRP-00012345"
    assert acc["company_name"] == "TechNova Solutions"
    assert acc["account_status"] == "active"

    assert "credit_limit" in acc
    assert "contact_email" in acc
    assert "booking_limit" in acc
    assert "created_at" in acc
    assert "updated_at" in acc


@pytest.mark.anyio
async def test_get_account_details_not_found(tool, db):
    with pytest.raises(tool.ExecutionError, match="not found"):
        await tool.run_with_validation(db, {"corporate_account_id": "CRP-99999999"})


@pytest.mark.anyio
async def test_get_account_details_invalid_param(tool, db):
    with pytest.raises(tool.ExecutionError):
        await tool.run_with_validation(db, {"corporate_account_id": ""})
