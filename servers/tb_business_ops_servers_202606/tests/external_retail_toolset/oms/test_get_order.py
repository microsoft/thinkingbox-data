# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_order tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.oms.models import (
    FulfillmentType,
    Order,
    OrderLineItem,
    OrderStatus,
    ShippingSpeed,
)
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.oms.tools.get_order import (
    GetOrderTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestGetOrder:
    @pytest.fixture
    def test_db(self):
        """Create a test database with orders and line items."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "order": Order,
            "order_line_item": OrderLineItem,
        }
        db._model_cls_to_stem = {
            Order: "order",
            OrderLineItem: "order_line_item",
        }

        # Create test orders
        order1 = Order(
            id="ORD-10000001",
            customer_id="CUS-10000001",
            order_date="2024-10-15T14:23:00Z",
            status=OrderStatus.SHIPPED,
            subtotal_amount=899.99,
            discount_amount=90.00,
            points_used=500,
            points_value=25.00,
            shipping_cost=0.00,
            total_amount=784.99,
            shipping_address_line1="123 Main St",
            shipping_address_city="Memphis",
            shipping_address_state="TN",
            shipping_address_zip="38103",
            shipping_speed=ShippingSpeed.STANDARD,
            fulfillment_type=FulfillmentType.WAREHOUSE,
            installation_service_id="JOB-10000001",
        )

        order2 = Order(
            id="ORD-10000002",
            customer_id="CUS-10000002",
            order_date="2024-10-20T10:30:00Z",
            status=OrderStatus.PROCESSING,
            subtotal_amount=1299.99,
            discount_amount=0.00,
            points_used=0,
            points_value=0.00,
            shipping_cost=15.00,
            total_amount=1314.99,
            shipping_address_line1="456 Oak Avenue",
            shipping_address_city="Nashville",
            shipping_address_state="TN",
            shipping_address_zip="37201",
            shipping_speed=ShippingSpeed.EXPEDITED,
            fulfillment_type=FulfillmentType.WAREHOUSE,
            installation_service_id=None,
        )

        # Create test line items
        line_item1 = OrderLineItem(
            id="LIN-10000001",
            order_id="ORD-10000001",
            sku="SKU-10000001",
            product_name="Samsung 28 cu ft French Door Refrigerator",
            quantity=1,
            base_price=899.99,
            discount_amount=90.00,
            final_price=809.99,
        )

        line_item2 = OrderLineItem(
            id="LIN-10000002",
            order_id="ORD-10000002",
            sku="SKU-10000002",
            product_name="LG 65 inch OLED 4K Smart TV",
            quantity=1,
            base_price=1299.99,
            discount_amount=0.00,
            final_price=1299.99,
        )

        db._store = {
            Order: [order1, order2],
            OrderLineItem: [line_item1, line_item2],
        }
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "order": Order,
            "order_line_item": OrderLineItem,
        }
        db._model_cls_to_stem = {
            Order: "order",
            OrderLineItem: "order_line_item",
        }
        db._store = {Order: [], OrderLineItem: []}
        return db

    @pytest.fixture
    def get_order_tool(self):
        """Create an instance of GetOrderTool."""
        return GetOrderTool()

    @pytest.mark.anyio
    async def test_get_order_success(self, get_order_tool, test_db):
        """Test successfully getting order with line items."""
        # Arrange
        request_data = {"order_id": "ORD-10000001"}

        # Act
        result = await get_order_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["id"] == "ORD-10000001"
        assert result["customer_id"] == "CUS-10000001"
        assert result["status"] == "shipped"
        assert result["subtotal_amount"] == 899.99
        assert result["discount_amount"] == 90.00
        assert result["points_used"] == 500
        assert result["points_value"] == 25.00
        assert result["total_amount"] == 784.99
        assert result["shipping_address_city"] == "Memphis"
        assert result["installation_service_id"] == "JOB-10000001"
        assert len(result["line_items"]) == 1
        assert result["line_items"][0]["sku"] == "SKU-10000001"
        assert (
            result["line_items"][0]["product_name"]
            == "Samsung 28 cu ft French Door Refrigerator"
        )

    @pytest.mark.anyio
    async def test_get_order_no_installation(self, get_order_tool, test_db):
        """Test getting order without installation service."""
        # Arrange
        request_data = {"order_id": "ORD-10000002"}

        # Act
        result = await get_order_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["id"] == "ORD-10000002"
        assert result["status"] == "processing"
        assert result["shipping_speed"] == "expedited"
        assert result["shipping_cost"] == 15.00
        # Note: installation_service_id is None, so it's excluded from output (exclude_none=True)
        assert "installation_service_id" not in result

    @pytest.mark.anyio
    async def test_get_order_not_found(self, get_order_tool, test_db):
        """Test error when order is not found."""
        # Arrange
        request_data = {"order_id": "ORD-99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_order_tool.run_with_validation(test_db, request_data)

        assert "Order not found" in str(error.value)

    @pytest.mark.anyio
    async def test_get_order_empty_database(self, get_order_tool, empty_db):
        """Test getting order from empty database."""
        # Arrange
        request_data = {"order_id": "ORD-10000001"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_order_tool.run_with_validation(empty_db, request_data)

        assert "Order not found" in str(error.value)
