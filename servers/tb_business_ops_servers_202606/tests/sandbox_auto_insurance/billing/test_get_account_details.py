# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_auto_insurance.billing.models import (
    ArrangementType,
)
from tb_business_ops_servers_202606.toolslib.sandbox_auto_insurance.billing.tools.get_account_details import (
    GetAccountDetailsInput,
    GetAccountDetailsTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
)


@pytest.fixture
def db_with_data():
    """Load billing toolset initial data through additional_sources."""

    base_dir = pathlib.Path(__file__).parents[3]
    data_dir = (
        base_dir
        / "tb_business_ops_servers_202606"
        / "toolslib"
        / "sandbox_auto_insurance"
        / "billing"
        / "initial_data"
    )

    return InMemoryDatabase(
        additional_sources={
            "billing": (
                str(data_dir),
                "tb_business_ops_servers_202606.toolslib.sandbox_auto_insurance.billing.models",
            )
        },
    )


@pytest.fixture
def tool():
    """Instantiate the get_account_details tool."""
    return GetAccountDetailsTool()


@pytest.mark.anyio
async def test_get_account_details_success(db_with_data, tool):
    """Tool returns full billing account details when policy exists."""

    request = GetAccountDetailsInput(policy_id="POL-0012345678")

    result = await tool.run_with_validation(db_with_data, request)

    assert result["billing_account_id"] == "BILL-000001"
    assert result["policy_id"] == "POL-0012345678"
    assert result["monthly_payment"] == 25000
    assert result["past_due_amount"] == 30000
    assert result["payment_received"] is False

    # model_dump returns enum values as strings
    assert result["arrangement_type"] in [
        e.value
        for e in [
            ArrangementType.NONE,
            ArrangementType.EXTENSION,
            ArrangementType.INSTALLMENT_PLAN,
        ]
    ]


@pytest.mark.anyio
async def test_get_account_details_not_found(db_with_data, tool):
    """Tool raises an error when no billing account matches the policy."""

    request = GetAccountDetailsInput(policy_id="POL-NOT-EXIST")

    with pytest.raises(tool.ExecutionError, match="No billing account found"):
        await tool.run_with_validation(db_with_data, request)
