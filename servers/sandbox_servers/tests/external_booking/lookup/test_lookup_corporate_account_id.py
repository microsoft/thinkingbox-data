# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from sandbox_servers.toolslib.external_booking.lookup.tools.lookup_corporate_account_id import (
    LookupCorporateAccountIdTool,
)
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def tool():
    return LookupCorporateAccountIdTool()


@pytest.mark.anyio
async def test_lookup_corporate_by_company_name_success(tool, db):
    """
    Provide company_name that exists in corporate_accounts.json.
    """
    request = {"company_name": "TechNova Solutions"}
    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert result["corporate_account_id"].startswith("CRP-")
    assert result["company_name"] == "TechNova Solutions"
    assert result["account_tier"] in ("enterprise", "mid_market", "small_business")


@pytest.mark.anyio
async def test_lookup_corporate_by_customer_email_success(tool, db):
    """
    Email domain matches known corporate account.
    """
    request = {"customer_email": "alice.johnson@technova.com"}
    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)
    assert result["corporate_account_id"].startswith("CRP-")
    assert "company_name" in result
    assert result["account_tier"] in ("enterprise", "mid_market", "small_business")


@pytest.mark.anyio
async def test_lookup_corporate_missing_parameters(tool, db):
    """
    Neither company_name nor email provided.
    """
    with pytest.raises(tool.ExecutionError, match="Invalid"):
        await tool.run_with_validation(db, {})


@pytest.mark.anyio
async def test_lookup_corporate_not_found(tool, db):
    """
    No corporate account found.
    """
    with pytest.raises(tool.ExecutionError, match="No corporate account found"):
        await tool.run_with_validation(
            db,
            {"company_name": "Nonexistent Global Holdings"},
        )
