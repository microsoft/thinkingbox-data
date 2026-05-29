# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for update_order_address tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.oms.models import (
    FulfillmentType,
    Order,
    OrderStatus,
    ShippingSpeed,
)
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.oms.tools.update_order_address import (
    UpdateOrderAddressTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestUpdateOrderAddress:
    @pytest.fixture
    def test_db(self):
        """Create a test database with orders."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"order": Order}
        db._model_cls_to_stem = {Order: "order"}

        order_processing = Order(
            id="ORD-10000001",
            customer_id="CUS-10000001",
            order_date="2024-10-20T12:00:00Z",
            status=OrderStatus.PROCESSING,
            subtotal_amount=500.00,
            discount_amount=0.00,
            points_used=0,
            points_value=0.00,
            shipping_cost=0.00,
            total_amount=500.00,
            shipping_address_line1="123 Main St",
            shipping_address_city="Memphis",
            shipping_address_state="TN",
            shipping_address_zip="38103",
            shipping_speed=ShippingSpeed.STANDARD,
            fulfillment_type=FulfillmentType.WAREHOUSE,
        )

        order_shipped = Order(
            id="ORD-10000002",
            customer_id="CUS-10000002",
            order_date="2024-10-15T10:00:00Z",
            status=OrderStatus.SHIPPED,
            subtotal_amount=600.00,
            discount_amount=0.00,
            points_used=0,
            points_value=0.00,
            shipping_cost=0.00,
            total_amount=600.00,
            shipping_address_line1="456 Oak Ave",
            shipping_address_city="Nashville",
            shipping_address_state="TN",
            shipping_address_zip="37201",
            shipping_speed=ShippingSpeed.STANDARD,
            fulfillment_type=FulfillmentType.WAREHOUSE,
        )

        db._store = {Order: [order_processing, order_shipped]}
        return db

    @pytest.fixture
    def update_order_address_tool(self):
        """Create an instance of UpdateOrderAddressTool."""
        return UpdateOrderAddressTool()

    @pytest.mark.anyio
    async def test_update_order_address_success(
        self, update_order_address_tool, test_db
    ):
        """Test successfully updating order address."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000001",
            "new_address_line1": "789 New Street",
            "new_address_city": "Knoxville",
            "new_address_state": "TN",
            "new_address_zip": "37901",
        }

        # Act
        result = await update_order_address_tool.run_with_validation(
            test_db, request_data
        )

        # Assert response
        assert result["order_id"] == "ORD-10000001"
        assert result["address_updated"] is True
        assert result["new_shipping_address_line1"] == "789 New Street"
        assert result["new_shipping_address_city"] == "Knoxville"
        assert result["new_shipping_address_state"] == "TN"
        assert result["new_shipping_address_zip"] == "37901"

        # Assert database state
        orders = test_db.get_all(Order)
        updated_order = next(o for o in orders if o.id == "ORD-10000001")
        assert updated_order.shipping_address_line1 == "789 New Street"
        assert updated_order.shipping_address_city == "Knoxville"

    @pytest.mark.anyio
    async def test_update_order_address_already_shipped(
        self, update_order_address_tool, test_db
    ):
        """Test that updating address for shipped order succeeds (policy guard removed)."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000002",
            "new_address_line1": "999 Another St",
            "new_address_city": "Chattanooga",
            "new_address_state": "TN",
            "new_address_zip": "37402",
        }

        # Act
        result = await update_order_address_tool.run_with_validation(
            test_db, request_data
        )

        # Assert - should succeed even for shipped orders
        assert result["order_id"] == "ORD-10000002"
        assert result["address_updated"] is True
        assert result["new_shipping_address_line1"] == "999 Another St"

    @pytest.mark.anyio
    async def test_update_order_address_not_found(
        self, update_order_address_tool, test_db
    ):
        """Test error when order is not found."""
        # Arrange
        request_data = {
            "order_id": "ORD-99999999",
            "new_address_line1": "999 Another St",
            "new_address_city": "Chattanooga",
            "new_address_state": "TN",
            "new_address_zip": "37402",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await update_order_address_tool.run_with_validation(test_db, request_data)

        assert "Order not found" in str(error.value)
