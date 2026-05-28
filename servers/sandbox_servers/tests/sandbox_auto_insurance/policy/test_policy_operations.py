# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for policy operation tools."""

import pytest
from sandbox_servers.toolslib.sandbox_auto_insurance.policy import (
    AddDriverTool,
    CancellationReason,
    Driver,
    DriverStatus,
    GetPolicyDriversTool,
    GetPolicyVehiclesTool,
    GetVehicleDetailsTool,
    Policy,
    PolicyStatus,
    ReinstatePolicyTool,
    ScheduleCancellationTool,
    State,
    UpdateDriverStatusTool,
    UpdateVehicleStatusTool,
    Vehicle,
    VehicleStatus,
)
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db_with_data():
    """Create a database with test data."""
    db = InMemoryDatabase(data_dir=None)

    # Register models
    db._stem_to_model_cls["policies"] = Policy
    db._model_cls_to_stem[Policy] = "policies"
    db._stem_to_model_cls["vehicles"] = Vehicle
    db._model_cls_to_stem[Vehicle] = "vehicles"
    db._stem_to_model_cls["drivers"] = Driver
    db._model_cls_to_stem[Driver] = "drivers"

    # Create test policy
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

    # Create test vehicles
    vehicle1 = Vehicle(
        id="VEH-00012345",
        policy_id="POL-0012345678",
        vin="1HGCM82633A123456",
        year=2022,
        make="Honda",
        model="Accord",
        status=VehicleStatus.ACTIVE,
        effective_date="2024-01-01",
        date_added_to_policy="2024-01-01",
        collision_coverage=True,
        comprehensive_coverage=True,
        rental_coverage=False,
        uw_pending=False,
    )
    db.create(vehicle1)

    vehicle2 = Vehicle(
        id="VEH-00012346",
        policy_id="POL-0012345678",
        vin="2T1BURHE1HC123789",
        year=2020,
        make="Toyota",
        model="Camry",
        status=VehicleStatus.REMOVED,
        effective_date="2024-01-01",
        removal_date="2024-06-01",
        date_added_to_policy="2024-01-01",
        collision_coverage=True,
        comprehensive_coverage=True,
        rental_coverage=True,
        uw_pending=False,
    )
    db.create(vehicle2)

    # Create test drivers
    driver1 = Driver(
        id="DRV-00012345",
        policy_id="POL-0012345678",
        name="John Smith",
        date_of_birth="1985-03-15",
        license_number="D1234567",
        license_state="CA",
        relationship="Self",
        status=DriverStatus.RATED,
        effective_date="2024-01-01",
        is_named_insured=True,
        is_co_insured=False,
        uw_pending=False,
        exclusion_form_required=False,
    )
    db.create(driver1)

    driver2 = Driver(
        id="DRV-00012346",
        policy_id="POL-0012345678",
        name="Sarah Smith",
        date_of_birth="1987-07-22",
        license_number="D2345678",
        license_state="CA",
        relationship="Spouse",
        status=DriverStatus.EXCLUDED,
        effective_date="2024-01-01",
        is_named_insured=False,
        is_co_insured=True,
        uw_pending=False,
        exclusion_form_required=True,
    )
    db.create(driver2)

    return db


# Tests for get_policy_vehicles
@pytest.mark.anyio
async def test_get_policy_vehicles_all(db_with_data):
    """Test getting all vehicles on policy."""
    tool = GetPolicyVehiclesTool()

    result = await tool.run_with_validation(
        db_with_data, {"policy_id": "POL-0012345678"}
    )

    assert result["vehicle_count"] == 2
    assert len(result["vehicles"]) == 2


@pytest.mark.anyio
async def test_get_policy_vehicles_active_only(db_with_data):
    """Test getting only active vehicles."""
    tool = GetPolicyVehiclesTool()

    result = await tool.run_with_validation(
        db_with_data, {"policy_id": "POL-0012345678", "active_only": True}
    )

    assert result["vehicle_count"] == 1
    assert result["vehicles"][0]["status"] == "Active"


# Tests for get_vehicle_details
@pytest.mark.anyio
async def test_get_vehicle_details_success(db_with_data):
    """Test getting vehicle details."""
    tool = GetVehicleDetailsTool()

    result = await tool.run_with_validation(
        db_with_data, {"vehicle_id": "VEH-00012345"}
    )

    assert result["vehicle_id"] == "VEH-00012345"
    assert result["vin"] == "1HGCM82633A123456"
    assert result["collision_coverage"] is True
    assert result["comprehensive_coverage"] is True


# Tests for get_policy_drivers
@pytest.mark.anyio
async def test_get_policy_drivers_all(db_with_data):
    """Test getting all drivers on policy."""
    tool = GetPolicyDriversTool()

    result = await tool.run_with_validation(
        db_with_data, {"policy_id": "POL-0012345678"}
    )

    assert result["driver_count"] == 2
    assert len(result["drivers"]) == 2


@pytest.mark.anyio
async def test_get_policy_drivers_active_only(db_with_data):
    """Test getting only active drivers."""
    tool = GetPolicyDriversTool()

    result = await tool.run_with_validation(
        db_with_data, {"policy_id": "POL-0012345678", "active_only": True}
    )

    # Both Rated and Excluded are considered active
    assert result["driver_count"] == 2


# Tests for update_vehicle_status
@pytest.mark.anyio
async def test_update_vehicle_status(db_with_data):
    """Test updating vehicle status."""
    tool = UpdateVehicleStatusTool()

    result = await tool.run_with_validation(
        db_with_data,
        {
            "vehicle_id": "VEH-00012345",
            "new_status": "Removed",
            "effective_date": "2024-06-15",
        },
    )

    assert result["vehicle_id"] == "VEH-00012345"
    assert result["status"] == "Removed"

    # Verify removal_date was set
    vehicle = db_with_data.get_by_id(Vehicle, "VEH-00012345")
    assert vehicle.removal_date == "2024-06-15"


# Tests for add_driver
@pytest.mark.anyio
async def test_add_driver_success(db_with_data):
    """Test adding a new driver."""
    tool = AddDriverTool()

    result = await tool.run_with_validation(
        db_with_data,
        {
            "policy_id": "POL-0012345678",
            "name": "Michael Smith",
            "date_of_birth": "2005-08-10",
            "license_number": "D3456789",
            "license_state": "CA",
            "relationship": "Son",
            "status": "Rated",
            "effective_date": "2024-07-01",
        },
    )

    assert "driver_id" in result
    assert result["driver_id"].startswith("DRV-")
    assert result["status"] == "Rated"


@pytest.mark.anyio
async def test_add_driver_duplicate(db_with_data):
    """Test adding duplicate driver fails."""
    tool = AddDriverTool()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_data,
            {
                "policy_id": "POL-0012345678",
                "name": "John Smith",
                "date_of_birth": "1985-03-15",
                "relationship": "Self",
                "status": "Rated",
                "effective_date": "2024-07-01",
            },
        )

    assert "already exists" in str(exc_info.value).lower()


# Tests for update_driver_status
@pytest.mark.anyio
async def test_update_driver_status(db_with_data):
    """Test updating driver status."""
    tool = UpdateDriverStatusTool()

    result = await tool.run_with_validation(
        db_with_data,
        {
            "driver_id": "DRV-00012345",
            "new_status": "Removed",
            "effective_date": "2024-06-15",
        },
    )

    assert result["driver_id"] == "DRV-00012345"
    assert result["status"] == "Removed"

    # Verify removal_date was set
    driver = db_with_data.get_by_id(Driver, "DRV-00012345")
    assert driver.removal_date == "2024-06-15"


# Tests for schedule_cancellation
@pytest.mark.anyio
async def test_schedule_cancellation(db_with_data):
    """Test scheduling policy cancellation."""
    tool = ScheduleCancellationTool()

    result = await tool.run_with_validation(
        db_with_data,
        {
            "policy_id": "POL-0012345678",
            "cancellation_date": "2024-12-31",
            "cancellation_reason": "User Requested",
        },
    )

    assert result["policy_id"] == "POL-0012345678"
    assert result["status"] == "Pending Cancellation"

    # Verify policy was updated
    policy = db_with_data.get_by_id(Policy, "POL-0012345678")
    assert policy.status == PolicyStatus.PENDING_CANCELLATION
    assert policy.cancellation_date == "2024-12-31"


# Tests for reinstate_policy
@pytest.mark.anyio
async def test_reinstate_policy_with_lapse(db_with_data):
    """Test reinstating a policy with lapse."""
    # First cancel the policy
    policy = db_with_data.get_by_id(Policy, "POL-0012345678")
    policy.status = PolicyStatus.CANCELLED_FOR_NON_PAYMENT
    policy.cancellation_date = "2024-06-01"
    policy.cancellation_reason = CancellationReason.NON_PAYMENT
    db_with_data.update(policy)

    tool = ReinstatePolicyTool()

    result = await tool.run_with_validation(
        db_with_data,
        {
            "policy_id": "POL-0012345678",
            "lapse_flag": True,
            "lapse_start": "2024-06-01",
            "lapse_end": "2024-06-15",
        },
    )

    assert result["policy_id"] == "POL-0012345678"
    assert result["status"] == "Active"
    assert result["lapse_flag"] is True

    # Verify policy was updated
    policy = db_with_data.get_by_id(Policy, "POL-0012345678")
    assert policy.status == PolicyStatus.ACTIVE
    assert policy.cancellation_date is None
    assert policy.lapse_flag is True


@pytest.mark.anyio
async def test_reinstate_policy_no_lapse(db_with_data):
    """Test reinstating a policy without lapse."""
    # First cancel the policy
    policy = db_with_data.get_by_id(Policy, "POL-0012345678")
    policy.status = PolicyStatus.CANCELLED_FOR_NON_PAYMENT
    db_with_data.update(policy)

    tool = ReinstatePolicyTool()

    result = await tool.run_with_validation(
        db_with_data, {"policy_id": "POL-0012345678", "lapse_flag": False}
    )

    assert result["policy_id"] == "POL-0012345678"
    assert result["status"] == "Active"
    assert result["lapse_flag"] is False
