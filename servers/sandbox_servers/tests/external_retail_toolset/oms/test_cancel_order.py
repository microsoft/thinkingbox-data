# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for cancel_order tool."""

import pytest
from sandbox_servers.toolslib.external_retail_toolset.oms.models import (
    FulfillmentType,
    Order,
    OrderStatus,
    ShippingSpeed,
)
from sandbox_servers.toolslib.external_retail_toolset.oms.tools.cancel_order import (
    CancelOrderTool,
)
from sandbox_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestCancelOrder:
    @pytest.fixture
    def test_db(self):
        """Create a test database with orders in various states."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"order": Order}
        db._model_cls_to_stem = {Order: "order"}

        # Create test orders in different statuses
        order_pending = Order(
            id="ORD-10000001",
            customer_id="CUS-10000001",
            order_date="2024-10-20T10:00:00Z",
            status=OrderStatus.PENDING_PAYMENT,
            subtotal_amount=100.00,
            discount_amount=0.00,
            points_used=0,
            points_value=0.00,
            shipping_cost=0.00,
            total_amount=100.00,
            shipping_address_line1="123 Main St",
            shipping_address_city="Memphis",
            shipping_address_state="TN",
            shipping_address_zip="38103",
            shipping_speed=ShippingSpeed.STANDARD,
            fulfillment_type=FulfillmentType.WAREHOUSE,
        )

        order_processing = Order(
            id="ORD-10000002",
            customer_id="CUS-10000002",
            order_date="2024-10-20T11:00:00Z",
            status=OrderStatus.PROCESSING,
            subtotal_amount=200.00,
            discount_amount=0.00,
            points_used=0,
            points_value=0.00,
            shipping_cost=0.00,
            total_amount=200.00,
            shipping_address_line1="456 Oak Ave",
            shipping_address_city="Nashville",
            shipping_address_state="TN",
            shipping_address_zip="37201",
            shipping_speed=ShippingSpeed.STANDARD,
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

        order_delivered = Order(
            id="ORD-10000004",
            customer_id="CUS-10000004",
            order_date="2024-10-10T10:00:00Z",
            status=OrderStatus.DELIVERED,
            subtotal_amount=400.00,
            discount_amount=0.00,
            points_used=0,
            points_value=0.00,
            shipping_cost=0.00,
            total_amount=400.00,
            shipping_address_line1="321 Pine Rd",
            shipping_address_city="Knoxville",
            shipping_address_state="TN",
            shipping_address_zip="37901",
            shipping_speed=ShippingSpeed.STANDARD,
            fulfillment_type=FulfillmentType.WAREHOUSE,
        )

        db._store = {
            Order: [order_pending, order_processing, order_shipped, order_delivered]
        }
        return db

    @pytest.fixture
    def cancel_order_tool(self):
        """Create an instance of CancelOrderTool."""
        return CancelOrderTool()

    @pytest.mark.anyio
    async def test_cancel_order_pending_payment_success(
        self, cancel_order_tool, test_db
    ):
        """Test successfully cancelling order with pending_payment status."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000001",
            "cancellation_reason": "customer_request",
        }

        # Act
        result = await cancel_order_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert result["order_id"] == "ORD-10000001"
        assert result["status"] == "cancelled"
        assert result["refund_initiated"] is False  # No payment yet

        # Assert database state
        orders = test_db.get_all(Order)
        cancelled_order = next(o for o in orders if o.id == "ORD-10000001")
        assert cancelled_order.status == OrderStatus.CANCELLED

    @pytest.mark.anyio
    async def test_cancel_order_processing_success(self, cancel_order_tool, test_db):
        """Test successfully cancelling order with processing status."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000002",
            "cancellation_reason": "customer_request",
        }

        # Act
        result = await cancel_order_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert result["order_id"] == "ORD-10000002"
        assert result["status"] == "cancelled"
        assert result["refund_initiated"] is True  # Payment was already authorized

        # Assert database state
        orders = test_db.get_all(Order)
        cancelled_order = next(o for o in orders if o.id == "ORD-10000002")
        assert cancelled_order.status == OrderStatus.CANCELLED

    @pytest.mark.anyio
    async def test_cancel_order_already_shipped(self, cancel_order_tool, test_db):
        """Test that cancelling a shipped order succeeds (policy guard removed)."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000003",
            "cancellation_reason": "customer_request",
        }

        # Act
        result = await cancel_order_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert result["order_id"] == "ORD-10000003"
        assert result["status"] == "cancelled"
        # Order was already shipped, so refund should be initiated
        assert (
            result["refund_initiated"] is False
        )  # Only PROCESSING orders initiate refund

        # Assert database state
        orders = test_db.get_all(Order)
        cancelled_order = next(o for o in orders if o.id == "ORD-10000003")
        assert cancelled_order.status == OrderStatus.CANCELLED

    @pytest.mark.anyio
    async def test_cancel_order_already_delivered(self, cancel_order_tool, test_db):
        """Test that cancelling a delivered order succeeds (policy guard removed)."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000004",
            "cancellation_reason": "customer_request",
        }

        # Act
        result = await cancel_order_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert result["order_id"] == "ORD-10000004"
        assert result["status"] == "cancelled"
        assert (
            result["refund_initiated"] is False
        )  # Only PROCESSING orders initiate refund

        # Assert database state
        orders = test_db.get_all(Order)
        cancelled_order = next(o for o in orders if o.id == "ORD-10000004")
        assert cancelled_order.status == OrderStatus.CANCELLED

    @pytest.mark.anyio
    async def test_cancel_order_not_found(self, cancel_order_tool, test_db):
        """Test error when order is not found."""
        # Arrange
        request_data = {
            "order_id": "ORD-99999999",
            "cancellation_reason": "customer_request",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await cancel_order_tool.run_with_validation(test_db, request_data)

        assert "Order not found" in str(error.value)
