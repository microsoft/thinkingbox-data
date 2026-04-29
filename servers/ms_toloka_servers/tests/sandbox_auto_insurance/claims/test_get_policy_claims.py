# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib
from datetime import date, datetime, timedelta

import pytest
from ms_toloka_servers.toolslib.sandbox_auto_insurance.claims.models import (
    Claim,
)
from ms_toloka_servers.toolslib.sandbox_auto_insurance.claims.tools.get_policy_claims import (
    GetPolicyClaimsInput,
    GetPolicyClaimsTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db_with_data():
    """Load data from all required namespaces using claims.models for consistency."""
    base_dir = pathlib.Path(__file__).parents[3]
    sa_dir = base_dir / "ms_toloka_servers" / "toolslib" / "sandbox_auto_insurance"

    return InMemoryDatabase(
        additional_sources={
            "policy": (
                str(sa_dir / "policy" / "initial_data"),
                "ms_toloka_servers.toolslib.sandbox_auto_insurance.policy.models",
            ),
            "billing": (
                str(sa_dir / "billing" / "initial_data"),
                "ms_toloka_servers.toolslib.sandbox_auto_insurance.billing.models",
            ),
            "crm": (
                str(sa_dir / "crm" / "initial_data"),
                "ms_toloka_servers.toolslib.sandbox_auto_insurance.crm.models",
            ),
            "claims": (
                str(sa_dir / "claims" / "initial_data"),
                "ms_toloka_servers.toolslib.sandbox_auto_insurance.claims.models",
            ),
        },
    )


@pytest.fixture
def tool():
    return GetPolicyClaimsTool()


@pytest.mark.anyio
async def test_get_policy_claims_no_filter(db_with_data, tool):
    input_data = GetPolicyClaimsInput(policy_id="POL-0012345678")

    result = await tool.run_with_validation(db_with_data, input_data)

    claims = [c for c in db_with_data.get_all(Claim) if c.policy_id == "POL-0012345678"]

    assert result["total_count"] == len(claims)
    assert result["total_count"] > 0
    assert all(item["claim_id"].startswith("CLM-") for item in result["claims"])


@pytest.mark.anyio
async def test_get_policy_claims_with_months_filter(db_with_data, tool):
    input_data = GetPolicyClaimsInput(
        policy_id="POL-0012345678",
        months_back=12,
    )

    # Calculate cutoff using the same deterministic logic as the tool
    all_claims = db_with_data.get_all(Claim)
    if all_claims:
        max_date_str = max(c.created_date for c in all_claims)
        max_date = datetime.strptime(max_date_str, "%Y-%m-%d")
    else:
        max_date = datetime(2099, 12, 31)

    cutoff = max_date - timedelta(days=30 * 12)
    cutoff_date_str = cutoff.strftime("%Y-%m-%d")

    result = await tool.run_with_validation(db_with_data, input_data)

    for item in result["claims"]:
        assert item["created_date"] >= cutoff_date_str


@pytest.mark.anyio
async def test_get_policy_claims_policy_not_found(db_with_data, tool):
    input_data = GetPolicyClaimsInput(policy_id="POL-DOES-NOT-EXIST")

    with pytest.raises(
        tool.ExecutionError, match="Policy 'POL-DOES-NOT-EXIST' not found"
    ):
        await tool.run_with_validation(db_with_data, input_data)


@pytest.mark.anyio
async def test_get_policy_claims_empty_after_filter(db_with_data, tool):
    input_data = GetPolicyClaimsInput(
        policy_id="POL-0012345678",
        months_back=1,
    )

    result = await tool.run_with_validation(db_with_data, input_data)

    assert result["total_count"] == len(result["claims"])
    assert all(
        item["created_date"] >= (date.today() - timedelta(days=30))
        for item in result["claims"]
    )
