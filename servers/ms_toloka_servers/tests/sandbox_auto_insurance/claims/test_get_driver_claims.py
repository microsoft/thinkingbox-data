# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from ms_toloka_servers.toolslib.sandbox_auto_insurance.claims.models import Claim
from ms_toloka_servers.toolslib.sandbox_auto_insurance.claims.tools.get_driver_claims import (
    GetDriverClaimsInput,
    GetDriverClaimsTool,
)
from ms_toloka_servers.toolslib.sandbox_auto_insurance.policy.models import Driver
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
    return GetDriverClaimsTool()


@pytest.mark.anyio
async def test_get_driver_claims_no_filter(db_with_data, tool):
    drivers = db_with_data.get_all(Driver)
    assert len(drivers) > 0

    driver_id = drivers[0].id

    input_data = GetDriverClaimsInput(driver_id=driver_id)

    result = await tool.run_with_validation(db_with_data, input_data)

    expected = [c for c in db_with_data.get_all(Claim) if c.driver_id == driver_id]

    assert isinstance(result, dict)
    assert len(result["claims"]) == len(expected)

    for c in result["claims"]:
        assert c["claim_id"].startswith("CLM-")

    expected_has_open = any(c.claim_stage.value.startswith("Open") for c in expected)
    assert result["has_open_claims"] == expected_has_open


@pytest.mark.anyio
async def test_get_driver_claims_open_only(db_with_data, tool):
    drivers = db_with_data.get_all(Driver)
    driver = drivers[0]

    input_data = GetDriverClaimsInput(
        driver_id=driver.id,
        open_only=True,
    )

    result = await tool.run_with_validation(db_with_data, input_data)

    assert isinstance(result, dict)

    for c in result["claims"]:
        assert c["claim_stage"].startswith("Open")

    assert result["has_open_claims"] == (len(result["claims"]) > 0)


@pytest.mark.anyio
async def test_get_driver_claims_not_found(db_with_data, tool):
    input_data = GetDriverClaimsInput(driver_id="DRV-DOES-NOT-EXIST")

    with pytest.raises(
        tool.ExecutionError, match="Driver 'DRV-DOES-NOT-EXIST' not found"
    ):
        await tool.run_with_validation(db_with_data, input_data)


@pytest.mark.anyio
async def test_get_driver_claims_empty(db_with_data, tool):
    """
    Create a fake driver in DB with no claims.
    """
    new_driver = Driver(
        id="DRV-99999999",
        policy_id="POL-0012345678",
        customer_id="CUST-00001",
        name="Test Driver",
        date_of_birth="1990-01-01",
        relationship="Self",
        effective_date="2025-01-01",
    )

    db_with_data.create(new_driver)

    input_data = GetDriverClaimsInput(driver_id="DRV-99999999")

    result = await tool.run_with_validation(db_with_data, input_data)

    assert result["claims"] == []
    assert result["has_open_claims"] is False
