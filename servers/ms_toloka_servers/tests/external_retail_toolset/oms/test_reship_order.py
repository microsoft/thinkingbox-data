# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for reship_order tool."""

import pytest
from ms_toloka_servers.toolslib.external_retail_toolset.oms.models import (
    CarrierTracking,
    FulfillmentType,
    Order,
    OrderStatus,
    Shipment,
    ShippingSpeed,
    TrackingStatus,
)
from ms_toloka_servers.toolslib.external_retail_toolset.oms.tools.reship_order import (
    ReshipOrderTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestReshipOrder:
    @pytest.fixture
    def test_db(self):
        """Create a test database with orders, shipments, and tracking."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "order": Order,
            "shipment": Shipment,
            "carrier_tracking": CarrierTracking,
        }
        db._model_cls_to_stem = {
            Order: "order",
            Shipment: "shipment",
            CarrierTracking: "carrier_tracking",
        }

        # Create test order
        order = Order(
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
            shipping_address_line1="123 Wrong Address",
            shipping_address_city="Memphis",
            shipping_address_state="TN",
            shipping_address_zip="38103",
            shipping_speed=ShippingSpeed.STANDARD,
            fulfillment_type=FulfillmentType.WAREHOUSE,
        )

        # Create shipment
        shipment = Shipment(
            id="SHP-10000001",
            order_id="ORD-10000001",
            carrier="FedEx",
            tracking_number="TRK-100000000001",
            ship_date="2024-10-16T08:15:00Z",
            estimated_delivery_date="2024-10-22T17:00:00Z",
        )

        # Create tracking - returned to sender
        tracking = CarrierTracking(
            tracking_number="TRK-100000000001",
            shipment_id="SHP-10000001",
            carrier="FedEx",
            status=TrackingStatus.RETURNED_TO_SENDER,
            current_location="Memphis, TN",
            estimated_delivery="2024-10-22T17:00:00Z",
            last_update="2024-10-20T10:15:00Z",
        )

        db._store = {
            Order: [order],
            Shipment: [shipment],
            CarrierTracking: [tracking],
        }
        return db

    @pytest.fixture
    def test_db_in_transit(self):
        """Create a test database with order still in transit."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "order": Order,
            "shipment": Shipment,
            "carrier_tracking": CarrierTracking,
        }
        db._model_cls_to_stem = {
            Order: "order",
            Shipment: "shipment",
            CarrierTracking: "carrier_tracking",
        }

        order = Order(
            id="ORD-10000002",
            customer_id="CUS-10000002",
            order_date="2024-10-18T10:00:00Z",
            status=OrderStatus.SHIPPED,
            subtotal_amount=500.00,
            discount_amount=0.00,
            points_used=0,
            points_value=0.00,
            shipping_cost=0.00,
            total_amount=500.00,
            shipping_address_line1="456 Oak Ave",
            shipping_address_city="Nashville",
            shipping_address_state="TN",
            shipping_address_zip="37201",
            shipping_speed=ShippingSpeed.STANDARD,
            fulfillment_type=FulfillmentType.WAREHOUSE,
        )

        shipment = Shipment(
            id="SHP-10000002",
            order_id="ORD-10000002",
            carrier="UPS",
            tracking_number="TRK-100000000002",
            ship_date="2024-10-19T09:00:00Z",
            estimated_delivery_date="2024-10-24T17:00:00Z",
        )

        tracking = CarrierTracking(
            tracking_number="TRK-100000000002",
            shipment_id="SHP-10000002",
            carrier="UPS",
            status=TrackingStatus.IN_TRANSIT,
            current_location="Knoxville, TN",
            estimated_delivery="2024-10-24T17:00:00Z",
            last_update="2024-10-21T08:00:00Z",
        )

        db._store = {
            Order: [order],
            Shipment: [shipment],
            CarrierTracking: [tracking],
        }
        return db

    @pytest.fixture
    def reship_order_tool(self):
        """Create an instance of ReshipOrderTool."""
        return ReshipOrderTool()

    @pytest.mark.anyio
    async def test_reship_order_customer_fault(self, reship_order_tool, test_db):
        """Test reshipping order when customer provided wrong address."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000001",
            "corrected_address_line1": "123 Main St Apt 5B",
            "corrected_address_city": "Memphis",
            "corrected_address_state": "TN",
            "corrected_address_zip": "38103",
            "customer_fault": True,
        }

        # Act
        result = await reship_order_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert result["order_id"] == "ORD-10000001"
        assert result["new_shipment_id"].startswith("SHP-2")
        assert result["new_tracking_number"].startswith("TRK-2")
        assert result["reship_cost"] == 15.00  # Customer fault
        assert result["reship_initiated"] is True

        # Assert database state - order address updated
        orders = test_db.get_all(Order)
        order = orders[0]
        assert order.shipping_address_line1 == "123 Main St Apt 5B"

        # Assert database state - new shipment created
        shipments = test_db.get_all(Shipment)
        assert len(shipments) == 2
        new_shipment = next(s for s in shipments if s.id == result["new_shipment_id"])
        assert new_shipment.order_id == "ORD-10000001"
        assert new_shipment.carrier == "FedEx"  # Same carrier

        # Assert database state - new tracking created
        trackings = test_db.get_all(CarrierTracking)
        assert len(trackings) == 2
        new_tracking = next(
            t for t in trackings if t.tracking_number == result["new_tracking_number"]
        )
        assert new_tracking.status == TrackingStatus.PENDING

    @pytest.mark.anyio
    async def test_reship_order_not_customer_fault(self, reship_order_tool, test_db):
        """Test reshipping order when error was not customer's fault."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000001",
            "corrected_address_line1": "123 Main St Apt 5B",
            "corrected_address_city": "Memphis",
            "corrected_address_state": "TN",
            "corrected_address_zip": "38103",
            "customer_fault": False,  # Not customer's fault
        }

        # Act
        result = await reship_order_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["reship_cost"] == 0.00  # No charge when not customer's fault

    @pytest.mark.anyio
    async def test_reship_order_not_returned_to_sender(
        self, reship_order_tool, test_db_in_transit
    ):
        """Test that reshipping an in-transit order succeeds (policy guard removed)."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000002",
            "corrected_address_line1": "456 Oak Ave Apt 2",
            "corrected_address_city": "Nashville",
            "corrected_address_state": "TN",
            "corrected_address_zip": "37201",
            "customer_fault": True,
        }

        # Act
        result = await reship_order_tool.run_with_validation(
            test_db_in_transit, request_data
        )

        # Assert - reship should succeed even for in-transit orders
        assert result["order_id"] == "ORD-10000002"
        assert result["reship_initiated"] is True
        assert result["reship_cost"] == 15.00  # Customer fault = $15

    @pytest.mark.anyio
    async def test_reship_order_not_found(self, reship_order_tool, test_db):
        """Test error when order is not found."""
        # Arrange
        request_data = {
            "order_id": "ORD-99999999",
            "corrected_address_line1": "999 Nowhere St",
            "corrected_address_city": "Memphis",
            "corrected_address_state": "TN",
            "corrected_address_zip": "38103",
            "customer_fault": True,
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await reship_order_tool.run_with_validation(test_db, request_data)

        assert "Order not found" in str(error.value)
