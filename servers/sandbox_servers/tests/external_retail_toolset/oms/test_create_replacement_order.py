# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for create_replacement_order tool."""

import pytest
from sandbox_servers.toolslib.external_retail_toolset.netsuite.models import (
    InventoryRecord,
)
from sandbox_servers.toolslib.external_retail_toolset.oms.models import (
    FulfillmentType,
    Order,
    OrderLineItem,
    OrderStatus,
    ShippingSpeed,
)
from sandbox_servers.toolslib.external_retail_toolset.oms.tools.create_replacement_order import (
    CreateReplacementOrderTool,
)
from sandbox_servers.toolslib.external_retail_toolset.shopify_pim.models import (
    ProductDetails,
)
from sandbox_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestCreateReplacementOrder:
    @pytest.fixture
    def test_db(self):
        """Create a test database with orders, inventory, and products."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "order": Order,
            "order_line_item": OrderLineItem,
            "inventory_record": InventoryRecord,
            "product_details": ProductDetails,
        }
        db._model_cls_to_stem = {
            Order: "order",
            OrderLineItem: "order_line_item",
            InventoryRecord: "inventory_record",
            ProductDetails: "product_details",
        }

        # Create test inventory
        inventory_in_stock = InventoryRecord(
            sku="SKU-10000001",
            available_quantity=10,
            reserved_quantity=2,
            warehouse_location="Memphis-A12",
        )

        inventory_out_of_stock = InventoryRecord(
            sku="SKU-10000002",
            available_quantity=0,
            reserved_quantity=0,
            warehouse_location="Memphis-B05",
            restock_date="2024-11-05T00:00:00Z",
            expected_restock_quantity=50,
        )

        # Create test products
        product1 = ProductDetails(
            sku="SKU-10000001",
            name="Samsung 28 cu ft French Door Refrigerator",
            category="appliances",
            brand="Samsung",
            base_price=899.99,
            weight_lbs=285.0,
            is_refurbished=False,
            warranty_period_days=1095,
            points_redemption_eligible=True,
            requires_installation=True,
        )

        product2 = ProductDetails(
            sku="SKU-10000002",
            name="LG 65 inch OLED 4K Smart TV",
            category="audio_video",
            brand="LG",
            base_price=1299.99,
            weight_lbs=55.0,
            is_refurbished=False,
            warranty_period_days=365,
            points_redemption_eligible=True,
            requires_installation=False,
        )

        # Create existing orders
        order1 = Order(
            id="ORD-10000001",
            customer_id="CUS-10000001",
            order_date="2024-10-15T14:23:00Z",
            status=OrderStatus.SHIPPED,
            subtotal_amount=899.99,
            discount_amount=0.00,
            points_used=0,
            points_value=0.00,
            shipping_cost=0.00,
            total_amount=899.99,
            shipping_address_line1="123 Main St",
            shipping_address_city="Memphis",
            shipping_address_state="TN",
            shipping_address_zip="38103",
            shipping_speed=ShippingSpeed.STANDARD,
            fulfillment_type=FulfillmentType.WAREHOUSE,
        )

        db._store = {
            Order: [order1],
            OrderLineItem: [],
            InventoryRecord: [inventory_in_stock, inventory_out_of_stock],
            ProductDetails: [product1, product2],
        }
        return db

    @pytest.fixture
    def create_replacement_order_tool(self):
        """Create an instance of CreateReplacementOrderTool."""
        return CreateReplacementOrderTool()

    @pytest.mark.anyio
    async def test_create_replacement_order_success(
        self, create_replacement_order_tool, test_db
    ):
        """Test successfully creating a replacement order."""
        # Arrange
        request_data = {
            "original_order_id": "ORD-10000001",
            "customer_id": "CUS-10000001",
            "sku": "SKU-10000001",
            "quantity": 1,
            "shipping_speed": "standard",
            "shipping_address_line1": "123 Main St",
            "shipping_address_city": "Memphis",
            "shipping_address_state": "TN",
            "shipping_address_zip": "38103",
        }

        # Act
        result = await create_replacement_order_tool.run_with_validation(
            test_db, request_data
        )

        # Assert response
        assert result["replacement_order_id"].startswith("ORD-2")
        assert result["status"] == "processing"
        assert result["total_amount"] == 0.00

        # Assert database state - inventory decremented
        inventory = test_db.get_all(InventoryRecord)
        inventory_record = next(inv for inv in inventory if inv.sku == "SKU-10000001")
        assert inventory_record.available_quantity == 9  # Was 10, now 9

        # Assert database state - new order created
        orders = test_db.get_all(Order)
        new_order = next(o for o in orders if o.id == result["replacement_order_id"])
        assert new_order.customer_id == "CUS-10000001"
        assert new_order.status == OrderStatus.PROCESSING
        assert new_order.total_amount == 0.00
        assert new_order.shipping_address_city == "Memphis"

        # Assert database state - line item created
        line_items = test_db.get_all(OrderLineItem)
        assert len(line_items) == 1
        assert line_items[0].order_id == result["replacement_order_id"]
        assert line_items[0].sku == "SKU-10000001"
        assert line_items[0].product_name == "Samsung 28 cu ft French Door Refrigerator"

    @pytest.mark.anyio
    async def test_create_replacement_order_vip_expedited(
        self, create_replacement_order_tool, test_db
    ):
        """Test creating replacement order with expedited shipping for VIP."""
        # Arrange
        request_data = {
            "original_order_id": "ORD-10000001",
            "customer_id": "CUS-10000001",
            "sku": "SKU-10000001",
            "quantity": 1,
            "shipping_speed": "expedited",  # VIP gets expedited
            "shipping_address_line1": "123 Main St",
            "shipping_address_city": "Memphis",
            "shipping_address_state": "TN",
            "shipping_address_zip": "38103",
        }

        # Act
        result = await create_replacement_order_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        orders = test_db.get_all(Order)
        new_order = next(o for o in orders if o.id == result["replacement_order_id"])
        assert new_order.shipping_speed == ShippingSpeed.EXPEDITED

    @pytest.mark.anyio
    async def test_create_replacement_order_out_of_stock(
        self, create_replacement_order_tool, test_db
    ):
        """Test error when product is out of stock."""
        # Arrange
        request_data = {
            "original_order_id": "ORD-10000001",
            "customer_id": "CUS-10000001",
            "sku": "SKU-10000002",  # Out of stock
            "quantity": 1,
            "shipping_speed": "standard",
            "shipping_address_line1": "123 Main St",
            "shipping_address_city": "Memphis",
            "shipping_address_state": "TN",
            "shipping_address_zip": "38103",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await create_replacement_order_tool.run_with_validation(
                test_db, request_data
            )

        assert "out of stock" in str(error.value).lower()
        assert "SKU-10000002" in str(error.value)

    @pytest.mark.anyio
    async def test_create_replacement_order_sku_not_found(
        self, create_replacement_order_tool, test_db
    ):
        """Test error when SKU is not found."""
        # Arrange
        request_data = {
            "original_order_id": "ORD-10000001",
            "customer_id": "CUS-10000001",
            "sku": "SKU-99999999",
            "quantity": 1,
            "shipping_speed": "standard",
            "shipping_address_line1": "123 Main St",
            "shipping_address_city": "Memphis",
            "shipping_address_state": "TN",
            "shipping_address_zip": "38103",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await create_replacement_order_tool.run_with_validation(
                test_db, request_data
            )

        # Either inventory not found (out of stock) or product not found
        error_msg = str(error.value).lower()
        assert "not found" in error_msg or "out of stock" in error_msg
