# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from sandbox_servers.toolslib.sandbox_auto_insurance.billing.tools.get_arrangement_history import (
    GetArrangementHistoryInput,
    GetArrangementHistoryTool,
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
    """Instantiate the get_arrangement_history tool."""
    return GetArrangementHistoryTool()


@pytest.mark.anyio
async def test_get_arrangement_history_success(db_with_data, tool):
    """Tool returns arrangement count for the matching policy."""

    request = GetArrangementHistoryInput(policy_id="POL-0012345678")

    result = await tool.run_with_validation(db_with_data, request)

    assert result["arrangements_12_months"] == 1


@pytest.mark.anyio
async def test_get_arrangement_history_not_found(db_with_data, tool):
    """Tool raises an error when policy is missing."""

    request = GetArrangementHistoryInput(policy_id="POL-DOES-NOT-EXIST")

    with pytest.raises(tool.ExecutionError, match="No billing account found"):
        await tool.run_with_validation(db_with_data, request)
