# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from sandbox_servers.toolslib.sandbox_auto_insurance.claims.models import (
    Claim,
    ClaimSeverity,
    ClaimStage,
)
from sandbox_servers.toolslib.sandbox_auto_insurance.claims.tools.check_open_major_claims import (
    CheckOpenMajorClaimsInput,
    CheckOpenMajorClaimsTool,
)
from sandbox_servers.toolslib.sandbox_auto_insurance.policy.models import Policy
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db_with_data():
    """Load data from all required namespaces using claims.models for consistency."""
    base_dir = pathlib.Path(__file__).parents[3]
    sa_dir = base_dir / "sandbox_servers" / "toolslib" / "sandbox_auto_insurance"

    return InMemoryDatabase(
        additional_sources={
            "policy": (
                str(sa_dir / "policy" / "initial_data"),
                "sandbox_servers.toolslib.sandbox_auto_insurance.policy.models",
            ),
            "billing": (
                str(sa_dir / "billing" / "initial_data"),
                "sandbox_servers.toolslib.sandbox_auto_insurance.billing.models",
            ),
            "crm": (
                str(sa_dir / "crm" / "initial_data"),
                "sandbox_servers.toolslib.sandbox_auto_insurance.crm.models",
            ),
            "claims": (
                str(sa_dir / "claims" / "initial_data"),
                "sandbox_servers.toolslib.sandbox_auto_insurance.claims.models",
            ),
        },
    )


@pytest.fixture
def tool():
    return CheckOpenMajorClaimsTool()


@pytest.mark.anyio
async def test_check_open_major_claims_has_major(db_with_data, tool):
    claims = db_with_data.get_all(Claim)
    assert len(claims) > 0

    target_claim = claims[0]
    target_claim.claim_stage = ClaimStage.OPEN_INITIAL
    target_claim.severity = ClaimSeverity.MAJOR

    db_with_data.update(target_claim)

    input_data = CheckOpenMajorClaimsInput(policy_id=target_claim.policy_id)
    result = await tool.run_with_validation(db_with_data, input_data)

    assert isinstance(result, dict)
    assert result["has_major_claim"] is True
    assert result["major_claim_count"] >= 1


@pytest.mark.anyio
async def test_check_open_major_claims_none(db_with_data, tool):
    claims = db_with_data.get_all(Claim)

    for c in claims:
        c.claim_stage = ClaimStage.CLOSED_PAID
        c.severity = ClaimSeverity.MINOR
        db_with_data.update(c)

    policies = db_with_data.get_all(Policy)
    assert len(policies) > 0
    policy_id = policies[0].id

    input_data = CheckOpenMajorClaimsInput(policy_id=policy_id)
    result = await tool.run_with_validation(db_with_data, input_data)

    assert isinstance(result, dict)
    assert result["has_major_claim"] is False
    assert result["major_claim_count"] == 0


@pytest.mark.anyio
async def test_check_open_major_claims_policy_not_found(db_with_data, tool):
    input_data = CheckOpenMajorClaimsInput(policy_id="POL-DOES-NOT-EXIST")

    with pytest.raises(
        tool.ExecutionError, match="Policy 'POL-DOES-NOT-EXIST' not found"
    ):
        await tool.run_with_validation(db_with_data, input_data)


@pytest.mark.anyio
async def test_check_open_major_claims_policy_with_zero_claims(db_with_data, tool):
    """
    Remove all claims for a specific policy.
    """
    policies = db_with_data.get_all(Policy)
    assert len(policies) > 0

    policy_id = policies[0].id

    for c in db_with_data.get_all(Claim):
        if c.policy_id == policy_id:
            db_with_data.delete(c)

    input_data = CheckOpenMajorClaimsInput(policy_id=policy_id)
    result = await tool.run_with_validation(db_with_data, input_data)

    assert result["has_major_claim"] is False
    assert result["major_claim_count"] == 0
