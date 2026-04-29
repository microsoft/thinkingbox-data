# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib
from datetime import date

import pytest
from ms_toloka_servers.toolslib.sandbox_auto_insurance.claims.models import Claim
from ms_toloka_servers.toolslib.sandbox_auto_insurance.claims.tools.get_vehicle_claims import (
    GetVehicleClaimsInput,
    GetVehicleClaimsTool,
)
from ms_toloka_servers.toolslib.sandbox_auto_insurance.policy.models import Vehicle
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
    return GetVehicleClaimsTool()


@pytest.mark.anyio
async def test_get_vehicle_claims_no_filter(db_with_data, tool):
    vehicles = db_with_data.get_all(Vehicle)
    assert len(vehicles) > 0

    vehicle_id = vehicles[0].id

    input_data = GetVehicleClaimsInput(vehicle_id=vehicle_id)
    result = await tool.run_with_validation(db_with_data, input_data)

    expected_claims = [
        c for c in db_with_data.get_all(Claim) if c.vehicle_id == vehicle_id
    ]

    assert isinstance(result, dict)
    assert len(result["claims"]) == len(expected_claims)

    assert all(c["claim_id"].startswith("CLM-") for c in result["claims"])

    expected_has_open = any(
        c.claim_stage.value.startswith("Open") for c in expected_claims
    )
    assert result["has_open_claims"] == expected_has_open


@pytest.mark.anyio
async def test_get_vehicle_claims_open_only(db_with_data, tool):
    vehicles = db_with_data.get_all(Vehicle)
    vehicle = vehicles[0]

    input_data = GetVehicleClaimsInput(
        vehicle_id=vehicle.id,
        open_only=True,
    )

    result = await tool.run_with_validation(db_with_data, input_data)

    assert isinstance(result, dict)

    for c in result["claims"]:
        assert c["claim_stage"].startswith("Open")

    assert result["has_open_claims"] == (len(result["claims"]) > 0)


@pytest.mark.anyio
async def test_get_vehicle_claims_vehicle_not_found(db_with_data, tool):
    input_data = GetVehicleClaimsInput(vehicle_id="VEH-DOES-NOT-EXIST")

    with pytest.raises(
        tool.ExecutionError, match="Vehicle 'VEH-DOES-NOT-EXIST' not found"
    ):
        await tool.run_with_validation(db_with_data, input_data)


@pytest.mark.anyio
async def test_get_vehicle_claims_empty(db_with_data, tool):
    """
    Create a fake vehicle in DB with no claims.
    Then ensure result.claims == [].
    """

    new_vehicle = Vehicle(
        id="VEH-99999999",
        vin="TESTVIN999",
        year=2025,
        make="Test",
        model="Test",
        policy_id="POL-0012345678",
        effective_date="2025-01-01",
        date_added_to_policy="2025-01-01",
    )

    db_with_data.create(new_vehicle)

    input_data = GetVehicleClaimsInput(vehicle_id="VEH-99999999")

    result = await tool.run_with_validation(db_with_data, input_data)

    assert result["claims"] == []
    assert result["has_open_claims"] is False
