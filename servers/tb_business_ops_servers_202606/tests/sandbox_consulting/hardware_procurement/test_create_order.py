# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for Hardware Procurement create_order tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.hardware_procurement.tools.create_order import (
    HardwareProcurementCreateOrderTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)


class TestHardwareProcurementCreateOrderTool:
    """Test cases for Hardware Procurement Create Order tool."""

    @pytest.fixture
    def test_db(self):
        """Create a test database (empty, as this tool doesn't use database)."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {}
        db._model_cls_to_stem = {}
        db._store = {}
        return db

    @pytest.fixture
    def create_order_tool(self):
        """Create an instance of the create_order tool."""
        return HardwareProcurementCreateOrderTool()

    @pytest.mark.anyio
    async def test_create_order_laptop(self, create_order_tool, test_db):
        """Test creating order for a laptop."""
        request_data = {
            "device_model": "HP ZBook Fury 17 G9",
            "quantity": 1,
            "deliver_to": "New York",
        }

        result = await create_order_tool.run_with_validation(test_db, request_data)

        assert result["order_id"] == "HWO-0056435"

    @pytest.mark.anyio
    async def test_create_order_phone(self, create_order_tool, test_db):
        """Test creating order for a phone."""
        request_data = {
            "device_model": "Google Pixel 7a",
            "quantity": 1,
            "deliver_to": "San Francisco",
        }

        result = await create_order_tool.run_with_validation(test_db, request_data)

        assert result["order_id"] == "HWO-0056435"

    @pytest.mark.anyio
    async def test_create_order_multiple_quantity(self, create_order_tool, test_db):
        """Test creating order with multiple quantity."""
        request_data = {
            "device_model": "Framework Laptop 13 AMD",
            "quantity": 5,
            "deliver_to": "Chicago",
        }

        result = await create_order_tool.run_with_validation(test_db, request_data)

        assert result["order_id"] == "HWO-0056435"

    @pytest.mark.anyio
    async def test_create_order_different_locations(self, create_order_tool, test_db):
        """Test creating orders with different delivery locations."""
        locations = ["New York", "San Francisco", "Chicago", "Austin"]

        for location in locations:
            request_data = {
                "device_model": "Lenovo ThinkPad P16s Gen 2",
                "quantity": 1,
                "deliver_to": location,
            }

            result = await create_order_tool.run_with_validation(test_db, request_data)

            # All orders return the same order ID
            assert result["order_id"] == "HWO-0056435"

    @pytest.mark.anyio
    async def test_create_order_always_same_id(self, create_order_tool, test_db):
        """Test that the tool always returns the same order ID."""
        # Create multiple orders with different parameters
        orders = [
            {
                "device_model": "Google Pixel 7a",
                "quantity": 1,
                "deliver_to": "New York",
            },
            {
                "device_model": "HP ZBook Fury 17 G9",
                "quantity": 2,
                "deliver_to": "Chicago",
            },
            {
                "device_model": "ASUS ProArt Studiobook 16",
                "quantity": 1,
                "deliver_to": "Austin",
            },
        ]

        results = []
        for order in orders:
            result = await create_order_tool.run_with_validation(test_db, order)
            results.append(result["order_id"])

        # All results should be identical
        assert all(order_id == "HWO-0056435" for order_id in results)
        assert len(set(results)) == 1  # Only one unique ID

    @pytest.mark.anyio
    async def test_create_order_missing_device_model(self, create_order_tool, test_db):
        """Test error when device_model is missing."""
        request_data = {
            "quantity": 1,
            "deliver_to": "New York",
        }

        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await create_order_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_create_order_missing_quantity(self, create_order_tool, test_db):
        """Test error when quantity is missing."""
        request_data = {
            "device_model": "Google Pixel 7a",
            "deliver_to": "New York",
        }

        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await create_order_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_create_order_missing_deliver_to(self, create_order_tool, test_db):
        """Test error when deliver_to is missing."""
        request_data = {
            "device_model": "Google Pixel 7a",
            "quantity": 1,
        }

        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await create_order_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_create_order_invalid_location(self, create_order_tool, test_db):
        """Test error when invalid location is provided."""
        request_data = {
            "device_model": "Google Pixel 7a",
            "quantity": 1,
            "deliver_to": "Invalid Location",
        }

        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await create_order_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_create_order_invalid_quantity_type(self, create_order_tool, test_db):
        """Test error when quantity is not an integer."""
        request_data = {
            "device_model": "Google Pixel 7a",
            "quantity": "one",
            "deliver_to": "New York",
        }

        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await create_order_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_create_order_output_format(self, create_order_tool, test_db):
        """Test that output has correct format."""
        request_data = {
            "device_model": "Google Pixel 7a",
            "quantity": 1,
            "deliver_to": "New York",
        }

        result = await create_order_tool.run_with_validation(test_db, request_data)

        # Verify output structure
        assert "order_id" in result
        assert isinstance(result["order_id"], str)
        assert result["order_id"].startswith("HWO-")
        assert len(result["order_id"]) == 11  # HWO-XXXXXXX format
