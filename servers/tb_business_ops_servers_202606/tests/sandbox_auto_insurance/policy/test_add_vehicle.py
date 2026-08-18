# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for add_vehicle tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_auto_insurance.policy import (
    AddVehicleTool,
    Policy,
    PolicyStatus,
    State,
    Vehicle,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
)


@pytest.fixture
def db_with_policy():
    """Create a database with a test policy."""
    db = InMemoryDatabase(data_dir=None)

    # Manually register models
    db._stem_to_model_cls["policies"] = Policy
    db._model_cls_to_stem[Policy] = "policies"
    db._stem_to_model_cls["vehicles"] = Vehicle
    db._model_cls_to_stem[Vehicle] = "vehicles"

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
async def test_add_vehicle_success(db_with_policy):
    """Test successfully adding a vehicle to a policy."""
    tool = AddVehicleTool()

    result = await tool.run_with_validation(
        db_with_policy,
        {
            "policy_id": "POL-0012345678",
            "vin": "1HGCM82633A123456",
            "year": 2022,
            "make": "Honda",
            "model": "Accord",
            "effective_date": "2025-01-15",
        },
    )

    assert "vehicle_id" in result
    assert result["vehicle_id"].startswith("VEH-")

    # Verify vehicle was created in database
    vehicles = db_with_policy.get_all(Vehicle)
    assert len(vehicles) == 1
    assert vehicles[0].vin == "1HGCM82633A123456"
    assert vehicles[0].collision_coverage is True
    assert vehicles[0].comprehensive_coverage is True


@pytest.mark.anyio
async def test_add_vehicle_duplicate_vin(db_with_policy):
    """Test adding a vehicle with duplicate VIN fails."""
    tool = AddVehicleTool()

    # Add first vehicle
    await tool.run_with_validation(
        db_with_policy,
        {
            "policy_id": "POL-0012345678",
            "vin": "1HGCM82633A123456",
            "year": 2022,
            "make": "Honda",
            "model": "Accord",
            "effective_date": "2025-01-15",
        },
    )

    # Try to add duplicate
    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_policy,
            {
                "policy_id": "POL-0012345678",
                "vin": "1HGCM82633A123456",
                "year": 2022,
                "make": "Honda",
                "model": "Accord",
                "effective_date": "2025-01-15",
            },
        )

    assert "already exists" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_add_vehicle_policy_not_found(db_with_policy):
    """Test adding vehicle to non-existent policy fails."""
    tool = AddVehicleTool()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_policy,
            {
                "policy_id": "POL-9999999999",
                "vin": "1HGCM82633A123456",
                "year": 2022,
                "make": "Honda",
                "model": "Accord",
                "effective_date": "2025-01-15",
            },
        )

    assert "not found" in str(exc_info.value).lower()
