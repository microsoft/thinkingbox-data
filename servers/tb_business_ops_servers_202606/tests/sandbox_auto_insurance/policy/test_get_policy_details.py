# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_policy_details tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_auto_insurance.policy import (
    GetPolicyDetailsTool,
    Policy,
    PolicyStatus,
    State,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
)


@pytest.fixture
def db_with_policies():
    """Create a database with test policies."""
    db = InMemoryDatabase(data_dir=None)

    # Manually register models
    db._stem_to_model_cls["policies"] = Policy
    db._model_cls_to_stem[Policy] = "policies"

    # Add test policy
    policy = Policy(
        id="POL-0012345678",
        customer_id="CUS-00012345",
        state=State.CA,
        status=PolicyStatus.ACTIVE,
        effective_date="2024-01-01",
        expiration_date="2024-12-31",
        renewal_date="2025-01-01",
        named_insured_id="CUS-00012345",
        automatic_extension_days=14,
        at_fault_claims_3_years=0,
        lapse_flag=False,
    )
    db.create(policy)

    return db


@pytest.mark.anyio
async def test_get_policy_details_success(db_with_policies):
    """Test successfully retrieving policy details."""
    tool = GetPolicyDetailsTool()

    result = await tool.run_with_validation(
        db_with_policies, {"policy_id": "POL-0012345678"}
    )

    assert result["policy_id"] == "POL-0012345678"
    assert result["customer_id"] == "CUS-00012345"
    assert result["status"] == "Active"
    assert result["state"] == "CA"
    assert result["effective_date"] == "2024-01-01"
    assert result["lapse_flag"] is False


@pytest.mark.anyio
async def test_get_policy_details_not_found(db_with_policies):
    """Test retrieving non-existent policy."""
    tool = GetPolicyDetailsTool()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_policies, {"policy_id": "POL-9999999999"}
        )

    assert "not found" in str(exc_info.value).lower()
