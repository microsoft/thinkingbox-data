# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for update_shipping_speed tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.oms.models import (
    FulfillmentType,
    Order,
    OrderStatus,
    ShippingSpeed,
)
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.oms.tools.update_shipping_speed import (
    UpdateShippingSpeedTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestUpdateShippingSpeed:
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
            discount_amount=50.00,
            points_used=0,
            points_value=0.00,
            shipping_cost=0.00,  # Standard shipping
            total_amount=450.00,
            shipping_address_line1="123 Main St",
            shipping_address_city="Memphis",
            shipping_address_state="TN",
            shipping_address_zip="38103",
            shipping_speed=ShippingSpeed.STANDARD,
            fulfillment_type=FulfillmentType.WAREHOUSE,
        )

        order_expedited = Order(
            id="ORD-10000002",
            customer_id="CUS-10000002",
            order_date="2024-10-20T11:00:00Z",
            status=OrderStatus.PROCESSING,
            subtotal_amount=600.00,
            discount_amount=0.00,
            points_used=0,
            points_value=0.00,
            shipping_cost=15.00,  # Expedited shipping
            total_amount=615.00,
            shipping_address_line1="456 Oak Ave",
            shipping_address_city="Nashville",
            shipping_address_state="TN",
            shipping_address_zip="37201",
            shipping_speed=ShippingSpeed.EXPEDITED,
            fulfillment_type=FulfillmentType.WAREHOUSE,
        )

        order_shipped = Order(
            id="ORD-10000003",
            customer_id="CUS-10000003",
            order_date="2024-10-15T10:00:00Z",
            status=OrderStatus.SHIPPED,
            subtotal_amount=300.00,
            discount_amount=0.00,
            points_used=0,
            points_value=0.00,
            shipping_cost=0.00,
            total_amount=300.00,
            shipping_address_line1="789 Elm St",
            shipping_address_city="Chattanooga",
            shipping_address_state="TN",
            shipping_address_zip="37402",
            shipping_speed=ShippingSpeed.STANDARD,
            fulfillment_type=FulfillmentType.WAREHOUSE,
        )

        db._store = {Order: [order_processing, order_expedited, order_shipped]}
        return db

    @pytest.fixture
    def update_shipping_speed_tool(self):
        """Create an instance of UpdateShippingSpeedTool."""
        return UpdateShippingSpeedTool()

    @pytest.mark.anyio
    async def test_upgrade_to_expedited(self, update_shipping_speed_tool, test_db):
        """Test upgrading from standard to expedited shipping."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000001",
            "new_shipping_speed": "expedited",
        }

        # Act
        result = await update_shipping_speed_tool.run_with_validation(
            test_db, request_data
        )

        # Assert response
        assert result["order_id"] == "ORD-10000001"
        assert result["old_shipping_speed"] == "standard"
        assert result["new_shipping_speed"] == "expedited"
        assert result["cost_difference"] == 15.00  # Standard=0, Expedited=15
        assert result["updated"] is True

        # Assert database state
        orders = test_db.get_all(Order)
        updated_order = next(o for o in orders if o.id == "ORD-10000001")
        assert updated_order.shipping_speed == ShippingSpeed.EXPEDITED
        assert updated_order.shipping_cost == 15.00
        assert updated_order.total_amount == 465.00  # 500 - 50 + 15

    @pytest.mark.anyio
    async def test_upgrade_to_next_day(self, update_shipping_speed_tool, test_db):
        """Test upgrading from expedited to next-day shipping."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000002",
            "new_shipping_speed": "next_day",
        }

        # Act
        result = await update_shipping_speed_tool.run_with_validation(
            test_db, request_data
        )

        # Assert response
        assert result["order_id"] == "ORD-10000002"
        assert result["old_shipping_speed"] == "expedited"
        assert result["new_shipping_speed"] == "next_day"
        assert result["cost_difference"] == pytest.approx(
            14.99, abs=0.01
        )  # Expedited=15, Next-day=29.99
        assert result["updated"] is True

        # Assert database state
        orders = test_db.get_all(Order)
        updated_order = next(o for o in orders if o.id == "ORD-10000002")
        assert updated_order.shipping_speed == ShippingSpeed.NEXT_DAY
        assert updated_order.shipping_cost == 29.99

    @pytest.mark.anyio
    async def test_downgrade_to_standard(self, update_shipping_speed_tool, test_db):
        """Test downgrading from expedited to standard shipping."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000002",
            "new_shipping_speed": "standard",
        }

        # Act
        result = await update_shipping_speed_tool.run_with_validation(
            test_db, request_data
        )

        # Assert response
        assert result["order_id"] == "ORD-10000002"
        assert result["old_shipping_speed"] == "expedited"
        assert result["new_shipping_speed"] == "standard"
        assert result["cost_difference"] == -15.00  # Negative means refund
        assert result["updated"] is True

    @pytest.mark.anyio
    async def test_update_shipping_already_shipped(
        self, update_shipping_speed_tool, test_db
    ):
        """Test that updating shipping for shipped order succeeds (policy guard removed)."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000003",
            "new_shipping_speed": "expedited",
        }

        # Act
        result = await update_shipping_speed_tool.run_with_validation(
            test_db, request_data
        )

        # Assert - should succeed even for shipped orders
        assert result["order_id"] == "ORD-10000003"
        assert result["updated"] is True
        assert result["new_shipping_speed"] == "expedited"

    @pytest.mark.anyio
    async def test_update_shipping_not_found(self, update_shipping_speed_tool, test_db):
        """Test error when order is not found."""
        # Arrange
        request_data = {
            "order_id": "ORD-99999999",
            "new_shipping_speed": "expedited",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await update_shipping_speed_tool.run_with_validation(test_db, request_data)

        assert "Order not found" in str(error.value)
