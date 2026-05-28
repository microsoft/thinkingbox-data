# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from sandbox_servers.toolslib.sandbox_auto_insurance.billing.models import (
    ArrangementType,
    BillingAccount,
)
from sandbox_servers.toolslib.sandbox_auto_insurance.billing.tools.create_installment_plan import (
    CreateInstallmentPlanInput,
    CreateInstallmentPlanTool,
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
    """Instantiate the create_installment_plan tool."""
    return CreateInstallmentPlanTool()


@pytest.mark.anyio
async def test_create_installment_plan_success(db_with_data, tool):
    """Installment plan is created and fields update correctly."""

    request = CreateInstallmentPlanInput(
        policy_id="POL-0012345678",
        installment_count=2,
        installment_amount=15000,
    )

    result = await tool.run_with_validation(db_with_data, request)

    assert result["billing_account_id"] == "BILL-000001"
    assert result["arrangements_12_months"] == 2

    updated = db_with_data.get_by_id(BillingAccount, "BILL-000001")

    assert updated.arrangement_type == ArrangementType.INSTALLMENT_PLAN
    assert updated.installment_count == 2
    assert updated.installment_amount == 15000
    assert updated.arrangements_12_months == 2

    assert updated.past_due_amount == 30000
    assert updated.monthly_payment == 25000
    assert updated.policy_id == "POL-0012345678"


@pytest.mark.anyio
async def test_create_installment_plan_not_found(db_with_data, tool):
    """Error is raised when policy_id does not match any account."""

    request = CreateInstallmentPlanInput(
        policy_id="POL-DOES-NOT-EXIST",
        installment_count=2,
        installment_amount=15000,
    )

    with pytest.raises(tool.ExecutionError, match="No billing account found"):
        await tool.run_with_validation(db_with_data, request)
