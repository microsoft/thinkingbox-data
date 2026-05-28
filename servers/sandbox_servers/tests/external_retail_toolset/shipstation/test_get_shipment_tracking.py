# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_shipment_tracking tool."""

import pytest
from sandbox_servers.toolslib.external_retail_toolset.oms.models import (
    CarrierTracking,
    Shipment,
    TrackingStatus,
)
from sandbox_servers.toolslib.external_retail_toolset.oms.tools.get_shipment_tracking import (
    GetShipmentTrackingTool,
)
from sandbox_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestGetShipmentTracking:
    @pytest.fixture
    def test_db(self):
        """Create a test database with shipments and tracking."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "shipment": Shipment,
            "carrier_tracking": CarrierTracking,
        }
        db._model_cls_to_stem = {
            Shipment: "shipment",
            CarrierTracking: "carrier_tracking",
        }

        # Create test shipments
        shipment1 = Shipment(
            id="SHP-10000001",
            order_id="ORD-10000001",
            carrier="FedEx",
            tracking_number="TRK-100000001",
            ship_date="2024-10-16T08:15:00Z",
            estimated_delivery_date="2024-10-22T17:00:00Z",
            actual_delivery_date=None,
        )

        shipment2 = Shipment(
            id="SHP-10000002",
            order_id="ORD-10000002",
            carrier="UPS",
            tracking_number="TRK-100000002",
            ship_date="2024-10-10T10:30:00Z",
            estimated_delivery_date="2024-10-15T17:00:00Z",
            actual_delivery_date="2024-10-14T14:32:00Z",
        )

        shipment3 = Shipment(
            id="SHP-10000003",
            order_id="ORD-10000003",
            carrier="USPS",
            tracking_number="TRK-100000003",
            ship_date="2024-10-18T09:00:00Z",
            estimated_delivery_date="2024-10-25T17:00:00Z",
            actual_delivery_date=None,
        )

        # Create test tracking
        tracking1 = CarrierTracking(
            tracking_number="TRK-100000001",
            shipment_id="SHP-10000001",
            carrier="FedEx",
            status=TrackingStatus.IN_TRANSIT,
            current_location="Memphis, TN",
            estimated_delivery="2024-10-22T17:00:00Z",
            last_update="2024-10-20T14:22:00Z",
        )

        tracking2 = CarrierTracking(
            tracking_number="TRK-100000002",
            shipment_id="SHP-10000002",
            carrier="UPS",
            status=TrackingStatus.DELIVERED,
            current_location="Customer Address",
            estimated_delivery="2024-10-15T17:00:00Z",
            last_update="2024-10-14T14:32:00Z",
        )

        tracking3 = CarrierTracking(
            tracking_number="TRK-100000003",
            shipment_id="SHP-10000003",
            carrier="USPS",
            status=TrackingStatus.DELAYED,
            current_location="Chicago, IL",
            estimated_delivery="2024-10-25T17:00:00Z",
            last_update="2024-10-22T08:15:00Z",
        )

        db._store = {
            Shipment: [shipment1, shipment2, shipment3],
            CarrierTracking: [tracking1, tracking2, tracking3],
        }
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "shipment": Shipment,
            "carrier_tracking": CarrierTracking,
        }
        db._model_cls_to_stem = {
            Shipment: "shipment",
            CarrierTracking: "carrier_tracking",
        }
        db._store = {Shipment: [], CarrierTracking: []}
        return db

    @pytest.fixture
    def get_shipment_tracking_tool(self):
        """Create an instance of GetShipmentTrackingTool."""
        return GetShipmentTrackingTool()

    @pytest.mark.anyio
    async def test_get_shipment_tracking_in_transit_success(
        self, get_shipment_tracking_tool, test_db
    ):
        """Test successfully getting shipment tracking for in-transit package."""
        # Arrange
        request_data = {"order_id": "ORD-10000001"}

        # Act
        result = await get_shipment_tracking_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["shipment_id"] == "SHP-10000001"
        assert result["order_id"] == "ORD-10000001"
        assert result["carrier"] == "FedEx"
        assert result["tracking_number"] == "TRK-100000001"
        assert result["tracking_status"] == "in_transit"
        assert result["current_location"] == "Memphis, TN"
        assert (
            "actual_delivery_date" not in result
            or result["actual_delivery_date"] is None
        )

    @pytest.mark.anyio
    async def test_get_shipment_tracking_delivered_success(
        self, get_shipment_tracking_tool, test_db
    ):
        """Test successfully getting shipment tracking for delivered package."""
        # Arrange
        request_data = {"order_id": "ORD-10000002"}

        # Act
        result = await get_shipment_tracking_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["shipment_id"] == "SHP-10000002"
        assert result["order_id"] == "ORD-10000002"
        assert result["carrier"] == "UPS"
        assert result["tracking_status"] == "delivered"
        assert result["actual_delivery_date"] is not None

    @pytest.mark.anyio
    async def test_get_shipment_tracking_delayed_success(
        self, get_shipment_tracking_tool, test_db
    ):
        """Test successfully getting shipment tracking for delayed package."""
        # Arrange
        request_data = {"order_id": "ORD-10000003"}

        # Act
        result = await get_shipment_tracking_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["shipment_id"] == "SHP-10000003"
        assert result["order_id"] == "ORD-10000003"
        assert result["carrier"] == "USPS"
        assert result["tracking_status"] == "delayed"
        assert result["current_location"] == "Chicago, IL"

    @pytest.mark.anyio
    async def test_get_shipment_tracking_no_tracking_info(
        self, get_shipment_tracking_tool, test_db
    ):
        """Test getting shipment without tracking info (defaults to pending)."""
        # Add a shipment without tracking
        shipment_no_tracking = Shipment(
            id="SHP-10000004",
            order_id="ORD-10000004",
            carrier="DHL",
            tracking_number="TRK-100000004",
            ship_date="2024-10-23T08:00:00Z",
            estimated_delivery_date="2024-10-28T17:00:00Z",
            actual_delivery_date=None,
        )
        test_db._store[Shipment].append(shipment_no_tracking)

        # Arrange
        request_data = {"order_id": "ORD-10000004"}

        # Act
        result = await get_shipment_tracking_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["shipment_id"] == "SHP-10000004"
        assert result["tracking_status"] == "pending"
        assert "current_location" not in result or result["current_location"] is None

    @pytest.mark.anyio
    async def test_get_shipment_tracking_not_found(
        self, get_shipment_tracking_tool, test_db
    ):
        """Test error when shipment is not found for order."""
        # Arrange
        request_data = {"order_id": "ORD-99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_shipment_tracking_tool.run_with_validation(test_db, request_data)

        assert "No shipment found for order" in str(error.value)
        assert "may not be shipped yet" in str(error.value)

    @pytest.mark.anyio
    async def test_get_shipment_tracking_empty_database(
        self, get_shipment_tracking_tool, empty_db
    ):
        """Test getting shipment from empty database."""
        # Arrange
        request_data = {"order_id": "ORD-10000001"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_shipment_tracking_tool.run_with_validation(empty_db, request_data)

        assert "No shipment found for order" in str(error.value)
