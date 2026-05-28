# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from sandbox_servers.toolslib.sandbox_auto_insurance.billing.models import (
    ArrangementType,
    BillingAccount,
    BillingAccountStatus,
)
from sandbox_servers.toolslib.sandbox_auto_insurance.billing.tools.reset_account_status import (
    ResetAccountStatusInput,
    ResetAccountStatusTool,
)
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db_with_data():
    """Load billing toolset initial data through additional_sources."""

    base_dir = pathlib.Path(__file__).parents[3]
    data_dir = (
        base_dir
        / "sandbox_servers"
        / "toolslib"
        / "sandbox_auto_insurance"
        / "billing"
        / "initial_data"
    )

    return InMemoryDatabase(
        additional_sources={
            "billing": (
                str(data_dir),
                "sandbox_servers.toolslib.sandbox_auto_insurance.billing.models",
            )
        },
    )


@pytest.fixture
def tool():
    """Instantiate the reset_account_status tool."""
    return ResetAccountStatusTool()


@pytest.mark.anyio
async def test_reset_account_status_success(db_with_data, tool):
    """Verify that account is fully reset to current status."""

    request = ResetAccountStatusInput(policy_id="POL-0012345678")

    result = await tool.run_with_validation(db_with_data, request)

    assert result["billing_account_id"] == "BILL-000001"
    assert result["status"] == BillingAccountStatus.CURRENT.value

    updated = db_with_data.get_by_id(BillingAccount, "BILL-000001")

    assert updated.status == BillingAccountStatus.CURRENT
    assert updated.past_due_amount == 0
    assert updated.arrangement_type == ArrangementType.NONE
    assert updated.new_due_date is None
    assert updated.installment_count is None
    assert updated.installment_amount is None

    assert updated.monthly_payment == 25000
    assert updated.policy_id == "POL-0012345678"
    assert updated.current_due_date == "2025-01-15"
    assert updated.payment_received is False


@pytest.mark.anyio
async def test_reset_account_status_not_found(db_with_data, tool):
    """Error is raised when no billing account matches the provided policy."""

    request = ResetAccountStatusInput(policy_id="POL-NOT-EXIST")

    with pytest.raises(tool.ExecutionError, match="No billing account found"):
        await tool.run_with_validation(db_with_data, request)
