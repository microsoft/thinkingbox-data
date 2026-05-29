# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.corporate_api.tools.verify_account_status import (
    VerifyAccountStatusTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def tool():
    return VerifyAccountStatusTool()


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
async def test_verify_account_status_active(tool, db):
    request = {"corporate_account_id": "CRP-00012345"}

    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert result["is_active"] is True
    assert "expiration_date" in result
    assert "booking_limit_remaining" in result


@pytest.mark.anyio
async def test_verify_account_status_expired(tool, db):
    request = {"corporate_account_id": "CRP-00024680"}

    result = await tool.run_with_validation(db, request)

    assert result["is_active"] is False
    assert "expiration_date" in result
    assert "booking_limit_remaining" in result


@pytest.mark.anyio
async def test_verify_account_status_not_found(tool, db):
    with pytest.raises(tool.ExecutionError, match="not found"):
        await tool.run_with_validation(db, {"corporate_account_id": "CRP-NOPE"})
