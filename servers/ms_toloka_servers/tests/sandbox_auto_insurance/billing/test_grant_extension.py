# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from ms_toloka_servers.toolslib.sandbox_auto_insurance.billing.models import (
    ArrangementType,
    BillingAccount,
)
from ms_toloka_servers.toolslib.sandbox_auto_insurance.billing.tools.grant_extension import (
    GrantExtensionInput,
    GrantExtensionTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
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
        / "ms_toloka_servers"
        / "toolslib"
        / "sandbox_auto_insurance"
        / "billing"
        / "initial_data"
    )

    return InMemoryDatabase(
        additional_sources={
            "billing": (
                str(data_dir),
                "ms_toloka_servers.toolslib.sandbox_auto_insurance.billing.models",
            )
        },
    )


@pytest.fixture
def tool():
    """Instantiate the grant_extension tool."""
    return GrantExtensionTool()


@pytest.mark.anyio
async def test_grant_extension_success(db_with_data, tool):
    """Extension is granted, due date is updated, and arrangement count increments."""

    request = GrantExtensionInput(
        policy_id="POL-0012345678",
        new_due_date="2025-01-25",
    )

    result = await tool.run_with_validation(db_with_data, request)

    assert result["billing_account_id"] == "BILL-000001"
    assert result["arrangements_12_months"] == 2

    updated = db_with_data.get_by_id(BillingAccount, "BILL-000001")

    assert updated.current_due_date == "2025-01-25"
    assert updated.new_due_date == "2025-01-25"
    assert updated.arrangement_type == ArrangementType.EXTENSION
    assert updated.arrangements_12_months == 2

    assert updated.installment_count is None
    assert updated.installment_amount is None


@pytest.mark.anyio
async def test_grant_extension_not_found(db_with_data, tool):
    """Error is raised when attempting to grant extension for a missing policy."""

    request = GrantExtensionInput(
        policy_id="POL-NOT-EXIST",
        new_due_date="2025-01-25",
    )

    with pytest.raises(tool.ExecutionError, match="No billing account found"):
        await tool.run_with_validation(db_with_data, request)
