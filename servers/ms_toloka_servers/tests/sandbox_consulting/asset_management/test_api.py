# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for asset_management_api master tool."""

from datetime import datetime

import pytest
from ms_toloka_servers.toolslib.sandbox_consulting.asset_management.models import (
    Device,
    DeviceAssignment,
    DeviceType,
    InventoryStatus,
    OfficeLocation,
)
from ms_toloka_servers.toolslib.sandbox_consulting.asset_management.tools.api import (
    AssetManagementApiTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestAssetManagementApi:
    @pytest.fixture
    def test_db(self):
        """Create a test database with devices and assignments."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "devices": Device,
            "device_assignments": DeviceAssignment,
        }
        db._model_cls_to_stem = {
            Device: "devices",
            DeviceAssignment: "device_assignments",
        }

        # Create test devices
        device1 = Device(
            id="MSG00001001",
            device_type=DeviceType.LAPTOP,
            model="HP ZBook Fury 17 G9",
            age_months=12,
            inventory_status=InventoryStatus.AVAILABLE,
            location=OfficeLocation.NEW_YORK,
        )

        device2 = Device(
            id="MSG00001002",
            device_type=DeviceType.LAPTOP,
            model="HP ZBook Fury 17 G9",
            age_months=18,
            inventory_status=InventoryStatus.AVAILABLE,
            location=OfficeLocation.NEW_YORK,
        )

        device3 = Device(
            id="MSG00001003",
            device_type=DeviceType.LAPTOP,
            model="Framework Laptop 13 AMD",
            age_months=6,
            inventory_status=InventoryStatus.ASSIGNED,
            location=OfficeLocation.SAN_FRANCISCO,
        )

        device4 = Device(
            id="MSG00002001",
            device_type=DeviceType.PHONE,
            model="Google Pixel 7a",
            age_months=24,
            inventory_status=InventoryStatus.AVAILABLE,
            location=OfficeLocation.CHICAGO,
        )

        device5 = Device(
            id="MSG00002002",
            device_type=DeviceType.PHONE,
            model="Sony Xperia 1 V",
            age_months=8,
            inventory_status=InventoryStatus.RESERVED,
            location=OfficeLocation.AUSTIN,
        )

        # Create test assignments
        assignment1 = DeviceAssignment(
            id="ASMT-1000001",
            asset_id="MSG00001003",
            employee_email="john.smith@msg.com",
            returned_at=None,
        )

        assignment2 = DeviceAssignment(
            id="ASMT-1000002",
            asset_id="MSG00003001",
            employee_email="jane.doe@msg.com",
            returned_at=datetime(2024, 10, 1),
        )

        db._store = {
            Device: [device1, device2, device3, device4, device5],
            DeviceAssignment: [assignment1, assignment2],
        }
        return db

    @pytest.fixture
    def asset_tool(self):
        """Create an instance of the Asset Management API tool."""
        return AssetManagementApiTool()

    # Tests for get_employee_devices action
    @pytest.mark.anyio
    async def test_get_employee_devices_success(self, asset_tool, test_db):
        """Test successful retrieval of employee devices."""
        # Arrange
        request_data = {"action": "get_employee_devices", "email": "john.smith@msg.com"}

        # Act
        result = await asset_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("devices") is not None
        devices = result["devices"]
        assert len(devices) == 1
        assert devices[0]["asset_id"] == "MSG00001003"
        assert devices[0]["employee_email"] == "john.smith@msg.com"
        assert devices[0].get("returned_at") is None

    @pytest.mark.anyio
    async def test_get_employee_devices_empty_result(self, asset_tool, test_db):
        """Test retrieval when employee has no devices."""
        # Arrange
        request_data = {"action": "get_employee_devices", "email": "nodevices@msg.com"}

        # Act
        result = await asset_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("devices") is not None
        assert len(result["devices"]) == 0

    @pytest.mark.anyio
    async def test_get_employee_devices_excludes_returned(self, asset_tool, test_db):
        """Test that returned devices are not included."""
        # Arrange
        request_data = {"action": "get_employee_devices", "email": "jane.doe@msg.com"}

        # Act
        result = await asset_tool.run_with_validation(test_db, request_data)

        # Assert - jane.doe has a returned device, should not be included
        assert result.get("devices") is not None
        assert len(result["devices"]) == 0

    @pytest.mark.anyio
    async def test_get_employee_devices_missing_email(self, asset_tool, test_db):
        """Test error when email is missing."""
        # Arrange
        request_data = {"action": "get_employee_devices"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await asset_tool.run_with_validation(test_db, request_data)

    # Tests for get_device_details action
    @pytest.mark.anyio
    async def test_get_device_details_success(self, asset_tool, test_db):
        """Test successful device details retrieval."""
        # Arrange
        request_data = {"action": "get_device_details", "asset_id": "MSG00001001"}

        # Act
        result = await asset_tool.run_with_validation(test_db, request_data)

        # Assert - verify ALL fields are present
        assert result.get("device_data") is not None
        device = result["device_data"]
        assert device["id"] == "MSG00001001"
        assert device["device_type"] == "laptop"
        assert device["model"] == "HP ZBook Fury 17 G9"
        assert device["age_months"] == 12
        assert device["inventory_status"] == "available"
        assert device["location"] == "New York"

    @pytest.mark.anyio
    async def test_get_device_details_not_found(self, asset_tool, test_db):
        """Test error when device not found."""
        # Arrange
        request_data = {"action": "get_device_details", "asset_id": "MSG99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Device not found"):
            await asset_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_device_details_missing_asset_id(self, asset_tool, test_db):
        """Test error when asset_id is missing."""
        # Arrange
        request_data = {"action": "get_device_details"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: asset_id"
        ):
            await asset_tool.run_with_validation(test_db, request_data)

    # Tests for check_inventory action
    @pytest.mark.anyio
    async def test_check_inventory_success(self, asset_tool, test_db):
        """Test successful inventory check."""
        # Arrange
        request_data = {
            "action": "check_inventory",
            "device_type": "laptop",
            "location": "New York",
        }

        # Act
        result = await asset_tool.run_with_validation(test_db, request_data)

        # Assert - Two available laptops with same model
        assert result.get("available_count_by_model") == {"HP ZBook Fury 17 G9": 2}

    @pytest.mark.anyio
    async def test_check_inventory_zero_available(self, asset_tool, test_db):
        """Test inventory check when no devices available."""
        # Arrange
        request_data = {
            "action": "check_inventory",
            "device_type": "phone",
            "location": "New York",
        }

        # Act
        result = await asset_tool.run_with_validation(test_db, request_data)

        # Assert - Empty dict when no devices available
        assert result.get("available_count_by_model") == {}

    @pytest.mark.anyio
    async def test_check_inventory_excludes_non_available(self, asset_tool, test_db):
        """Test that only available devices are counted."""
        # Arrange - Austin has 1 reserved phone, should not be counted
        request_data = {
            "action": "check_inventory",
            "device_type": "phone",
            "location": "Austin",
        }

        # Act
        result = await asset_tool.run_with_validation(test_db, request_data)

        # Assert - Empty dict since reserved is not counted
        assert (
            result.get("available_count_by_model") == {}
        )  # Reserved device not counted

    @pytest.mark.anyio
    async def test_check_inventory_missing_device_type(self, asset_tool, test_db):
        """Test error when device_type is missing."""
        # Arrange
        request_data = {"action": "check_inventory", "location": "New York"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: device_type"
        ):
            await asset_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_check_inventory_missing_location(self, asset_tool, test_db):
        """Test error when location is missing."""
        # Arrange
        request_data = {"action": "check_inventory", "device_type": "laptop"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: location"
        ):
            await asset_tool.run_with_validation(test_db, request_data)

    # Tests for reserve_device action
    @pytest.mark.anyio
    async def test_reserve_device_success_fifo(self, asset_tool, test_db):
        """Test successful device reservation using FIFO."""
        # Arrange - Two available laptops: MSG00001001 and MSG00001002
        request_data = {
            "action": "reserve_device",
            "device_type": "laptop",
            "location": "New York",
        }

        # Act
        result = await asset_tool.run_with_validation(test_db, request_data)

        # Assert - Should reserve first device by ID (FIFO)
        assert result.get("reserved_asset_id") == "MSG00001001"

        # Verify device status was updated
        device = test_db.get_by_id(Device, "MSG00001001")
        assert device.inventory_status == InventoryStatus.RESERVED

    @pytest.mark.anyio
    async def test_reserve_device_no_available(self, asset_tool, test_db):
        """Test error when no devices available."""
        # Arrange
        request_data = {
            "action": "reserve_device",
            "device_type": "laptop",
            "location": "Chicago",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="No available laptop devices at Chicago"
        ):
            await asset_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_reserve_device_missing_device_type(self, asset_tool, test_db):
        """Test error when device_type is missing."""
        # Arrange
        request_data = {"action": "reserve_device", "location": "New York"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: device_type"
        ):
            await asset_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_reserve_device_missing_location(self, asset_tool, test_db):
        """Test error when location is missing."""
        # Arrange
        request_data = {"action": "reserve_device", "device_type": "laptop"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: location"
        ):
            await asset_tool.run_with_validation(test_db, request_data)

    # Tests for assign_device action
    @pytest.mark.anyio
    async def test_assign_device_success(self, asset_tool, test_db):
        """Test successful device assignment."""
        # Arrange
        request_data = {
            "action": "assign_device",
            "email": "newuser@msg.com",
            "asset_id": "MSG00001001",
        }

        # Act
        result = await asset_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert result.get("success") is True

        # Verify assignment was created
        assignments = test_db.get_all(DeviceAssignment)
        new_assignment = [a for a in assignments if a.asset_id == "MSG00001001"]
        assert len(new_assignment) == 1
        assert new_assignment[0].employee_email == "newuser@msg.com"
        assert new_assignment[0].returned_at is None

        # Verify device status was updated
        device = test_db.get_by_id(Device, "MSG00001001")
        assert device.inventory_status == InventoryStatus.ASSIGNED

    @pytest.mark.anyio
    async def test_assign_device_not_found(self, asset_tool, test_db):
        """Test error when device not found."""
        # Arrange
        request_data = {
            "action": "assign_device",
            "email": "user@msg.com",
            "asset_id": "MSG99999999",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Device not found"):
            await asset_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_assign_device_missing_email(self, asset_tool, test_db):
        """Test error when email is missing."""
        # Arrange
        request_data = {"action": "assign_device", "asset_id": "MSG00001001"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await asset_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_assign_device_missing_asset_id(self, asset_tool, test_db):
        """Test error when asset_id is missing."""
        # Arrange
        request_data = {"action": "assign_device", "email": "user@msg.com"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: asset_id"
        ):
            await asset_tool.run_with_validation(test_db, request_data)

    # Tests for retire_device action
    @pytest.mark.anyio
    async def test_retire_device_success(self, asset_tool, test_db):
        """Test successful device retirement."""
        # Arrange
        request_data = {"action": "retire_device", "asset_id": "MSG00001001"}

        # Act
        result = await asset_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert result.get("success") is True

        # Verify device status was updated
        device = test_db.get_by_id(Device, "MSG00001001")
        assert device.inventory_status == InventoryStatus.RETIRED

    @pytest.mark.anyio
    async def test_retire_device_not_found(self, asset_tool, test_db):
        """Test error when device not found."""
        # Arrange
        request_data = {"action": "retire_device", "asset_id": "MSG99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Device not found"):
            await asset_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_retire_device_missing_asset_id(self, asset_tool, test_db):
        """Test error when asset_id is missing."""
        # Arrange
        request_data = {"action": "retire_device"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: asset_id"
        ):
            await asset_tool.run_with_validation(test_db, request_data)

    # General tests
    @pytest.mark.anyio
    async def test_invalid_action(self, asset_tool, test_db):
        """Test error with invalid action."""
        # Arrange
        request_data = {"action": "invalid_action"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await asset_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_device_details_empty_database(self, asset_tool):
        """Test get_device_details with empty database."""
        # Arrange
        empty_db = InMemoryDatabase.__new__(InMemoryDatabase)
        empty_db._stem_to_model_cls = {"devices": Device}
        empty_db._model_cls_to_stem = {Device: "devices"}
        empty_db._store = {Device: []}

        request_data = {"action": "get_device_details", "asset_id": "MSG00001001"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Device not found"):
            await asset_tool.run_with_validation(empty_db, request_data)
