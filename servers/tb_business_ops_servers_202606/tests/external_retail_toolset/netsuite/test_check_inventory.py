# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for check_inventory tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.netsuite.models import (
    InventoryRecord,
)
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.netsuite.tools.check_inventory import (
    CheckInventoryTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestCheckInventory:
    @pytest.fixture
    def test_db(self):
        """Create a test database with inventory records."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"inventory_record": InventoryRecord}
        db._model_cls_to_stem = {InventoryRecord: "inventory_record"}

        # Create test inventory records
        inventory1 = InventoryRecord(
            sku="SKU-10000001",
            available_quantity=15,
            reserved_quantity=3,
            warehouse_location="Memphis-A12",
            restock_date=None,
            expected_restock_quantity=None,
        )

        inventory2 = InventoryRecord(
            sku="SKU-10000002",
            available_quantity=0,
            reserved_quantity=0,
            warehouse_location="Memphis-B05",
            restock_date="2024-11-05T00:00:00Z",
            expected_restock_quantity=50,
        )

        inventory3 = InventoryRecord(
            sku="SKU-10000003",
            available_quantity=8,
            reserved_quantity=2,
            warehouse_location="Chicago-C18",
            restock_date=None,
            expected_restock_quantity=None,
        )

        inventory4 = InventoryRecord(
            sku="SKU-10000004",
            available_quantity=2,
            reserved_quantity=1,
            warehouse_location="Memphis-A12",
            restock_date=None,
            expected_restock_quantity=None,
        )

        inventory5 = InventoryRecord(
            sku="SKU-10000005",
            available_quantity=0,
            reserved_quantity=0,
            warehouse_location="Dallas-D22",
            restock_date="2024-11-15T00:00:00Z",
            expected_restock_quantity=25,
        )

        db._store = {
            InventoryRecord: [
                inventory1,
                inventory2,
                inventory3,
                inventory4,
                inventory5,
            ]
        }
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"inventory_record": InventoryRecord}
        db._model_cls_to_stem = {InventoryRecord: "inventory_record"}
        db._store = {InventoryRecord: []}
        return db

    @pytest.fixture
    def check_inventory_tool(self):
        """Create an instance of CheckInventoryTool."""
        return CheckInventoryTool()

    @pytest.mark.anyio
    async def test_check_inventory_in_stock_success(
        self, check_inventory_tool, test_db
    ):
        """Test successfully checking inventory for in-stock product."""
        # Arrange
        request_data = {"sku": "SKU-10000001"}

        # Act
        result = await check_inventory_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["sku"] == "SKU-10000001"
        assert result["available_quantity"] == 15
        assert result["reserved_quantity"] == 3
        assert result["warehouse_location"] == "Memphis-A12"
        assert "restock_date" not in result or result["restock_date"] is None
        assert (
            "expected_restock_quantity" not in result
            or result["expected_restock_quantity"] is None
        )

    @pytest.mark.anyio
    async def test_check_inventory_out_of_stock_with_restock(
        self, check_inventory_tool, test_db
    ):
        """Test checking inventory for out-of-stock product with restock info."""
        # Arrange
        request_data = {"sku": "SKU-10000002"}

        # Act
        result = await check_inventory_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["sku"] == "SKU-10000002"
        assert result["available_quantity"] == 0
        assert result["reserved_quantity"] == 0
        assert result["warehouse_location"] == "Memphis-B05"
        assert result["restock_date"] is not None
        assert "2024-11-05" in result["restock_date"]
        assert result["expected_restock_quantity"] == 50

    @pytest.mark.anyio
    async def test_check_inventory_low_stock(self, check_inventory_tool, test_db):
        """Test checking inventory for low-stock product."""
        # Arrange
        request_data = {"sku": "SKU-10000004"}

        # Act
        result = await check_inventory_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["sku"] == "SKU-10000004"
        assert result["available_quantity"] == 2
        assert result["reserved_quantity"] == 1
        assert result["warehouse_location"] == "Memphis-A12"

    @pytest.mark.anyio
    async def test_check_inventory_different_warehouse(
        self, check_inventory_tool, test_db
    ):
        """Test checking inventory for product in different warehouse."""
        # Arrange
        request_data = {"sku": "SKU-10000003"}

        # Act
        result = await check_inventory_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["sku"] == "SKU-10000003"
        assert result["available_quantity"] == 8
        assert result["reserved_quantity"] == 2
        assert result["warehouse_location"] == "Chicago-C18"

    @pytest.mark.anyio
    async def test_check_inventory_out_of_stock_future_restock(
        self, check_inventory_tool, test_db
    ):
        """Test checking inventory for out-of-stock product with future restock."""
        # Arrange
        request_data = {"sku": "SKU-10000005"}

        # Act
        result = await check_inventory_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["sku"] == "SKU-10000005"
        assert result["available_quantity"] == 0
        assert result["restock_date"] is not None
        assert "2024-11-15" in result["restock_date"]
        assert result["expected_restock_quantity"] == 25

    @pytest.mark.anyio
    async def test_check_inventory_not_found(self, check_inventory_tool, test_db):
        """Test error when SKU is not found."""
        # Arrange
        request_data = {"sku": "SKU-99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await check_inventory_tool.run_with_validation(test_db, request_data)

        assert "SKU not found in inventory system" in str(error.value)

    @pytest.mark.anyio
    async def test_check_inventory_empty_database(self, check_inventory_tool, empty_db):
        """Test checking inventory from empty database."""
        # Arrange
        request_data = {"sku": "SKU-10000001"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await check_inventory_tool.run_with_validation(empty_db, request_data)

        assert "SKU not found in inventory system" in str(error.value)
