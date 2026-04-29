# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib
from datetime import date

import pytest
from ms_toloka_servers.toolslib.sandbox_auto_insurance.claims.models import (
    Claim,
    ClaimStage,
)
from ms_toloka_servers.toolslib.sandbox_auto_insurance.claims.tools.create_fnol import (
    CreateFNOLInput,
    CreateFNOLTool,
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
    return CreateFNOLTool()


@pytest.mark.anyio
async def test_create_fnol_success(db_with_data, tool):
    initial_count = len(db_with_data.get_all(Claim))

    req = CreateFNOLInput(
        policy_id="POL-0012345678",
        vehicle_id="VEH-00012345",
        driver_id="DRV-00012345",
        date_of_loss="2025-01-14",
        loss_location="Los Angeles, CA",
        claim_type="Collision – Multi-Vehicle",
        severity="Moderate",
        siu_flag="None",
        unlisted_driver_flag=False,
        has_bodily_injury=False,
        police_report_required=False,
        police_report_number=None,
        other_party_name=None,
        other_party_phone=None,
        other_party_insurance=None,
        vehicle_vin="1HGCM82633A123456",
    )

    result = await tool.run_with_validation(db_with_data, req)

    assert result["claim_stage"] == ClaimStage.OPEN_INITIAL
    assert result["claim_id"].startswith("CLM-")

    claims = db_with_data.get_all(Claim)
    assert len(claims) == initial_count + 1

    new_claim = claims[-1]
    assert new_claim.policy_id == "POL-0012345678"
    assert new_claim.date_of_loss == "2025-01-14"


@pytest.mark.anyio
async def test_create_fnol_policy_not_found(db_with_data, tool):
    req = CreateFNOLInput(
        policy_id="POL-DOES-NOT-EXIST",
        date_of_loss="2025-01-14",
        loss_location="LA",
        claim_type="Collision – Multi-Vehicle",
        severity="Moderate",
    )

    with pytest.raises(
        tool.ExecutionError, match="Policy 'POL-DOES-NOT-EXIST' not found"
    ):
        await tool.run_with_validation(db_with_data, req)
