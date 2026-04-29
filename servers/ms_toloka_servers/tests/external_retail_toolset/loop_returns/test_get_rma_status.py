# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_rma_status tool."""

import pytest
from ms_toloka_servers.toolslib.external_retail_toolset.loop_returns.models import (
    RMARecord,
    RMAReturnReason,
    RMAStatus,
)
from ms_toloka_servers.toolslib.external_retail_toolset.loop_returns.tools.get_rma_status import (
    GetRMAStatusTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestGetRMAStatus:
    @pytest.fixture
    def test_db(self):
        """Create a test database with RMA records."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"rma_record": RMARecord}
        db._model_cls_to_stem = {RMARecord: "rma_record"}

        # Create test RMA records
        # Defective return - approved
        rma1 = RMARecord(
            id="RMA-10000001",
            order_id="ORD-10012345",
            line_item_id="LIN-10012345",
            customer_id="CUS-10000001",
            return_reason=RMAReturnReason.DEFECTIVE,
            is_defective=True,
            status=RMAStatus.APPROVED,
            created_date="2024-10-20T09:15:00Z",
            refund_amount=899.99,
            restocking_fee=0.00,
            return_shipping_cost=0.00,
            removal_fee=0.00,
        )

        # Non-defective return with fees - refunded
        rma2 = RMARecord(
            id="RMA-10000002",
            order_id="ORD-10012346",
            line_item_id="LIN-10012346",
            customer_id="CUS-10000002",
            return_reason=RMAReturnReason.CHANGED_MIND,
            is_defective=False,
            status=RMAStatus.REFUNDED,
            created_date="2024-10-18T14:30:00Z",
            refund_amount=416.01,
            restocking_fee=75.00,
            return_shipping_cost=8.99,
            removal_fee=0.00,
        )

        # Damaged in transit - shipped to warehouse
        rma3 = RMARecord(
            id="RMA-10000003",
            order_id="ORD-10012347",
            line_item_id="LIN-10012347",
            customer_id="CUS-10000003",
            return_reason=RMAReturnReason.DAMAGED_IN_TRANSIT,
            is_defective=True,
            status=RMAStatus.SHIPPED_TO_WAREHOUSE,
            created_date="2024-10-21T11:45:00Z",
            refund_amount=1299.99,
            restocking_fee=0.00,
            return_shipping_cost=0.00,
            removal_fee=0.00,
        )

        # Non-defective with removal fee - approved
        rma4 = RMARecord(
            id="RMA-10000004",
            order_id="ORD-10012348",
            line_item_id="LIN-10012348",
            customer_id="CUS-10000001",
            return_reason=RMAReturnReason.NOT_AS_EXPECTED,
            is_defective=False,
            status=RMAStatus.APPROVED,
            created_date="2024-10-22T10:00:00Z",
            refund_amount=1614.99,
            restocking_fee=285.00,
            return_shipping_cost=0.00,
            removal_fee=50.00,
        )

        db._store = {RMARecord: [rma1, rma2, rma3, rma4]}
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"rma_record": RMARecord}
        db._model_cls_to_stem = {RMARecord: "rma_record"}
        db._store = {RMARecord: []}
        return db

    @pytest.fixture
    def get_rma_status_tool(self):
        """Create an instance of GetRMAStatusTool."""
        return GetRMAStatusTool()

    @pytest.mark.anyio
    async def test_get_rma_status_defective_success(self, get_rma_status_tool, test_db):
        """Test successfully getting RMA status for defective return."""
        # Arrange
        request_data = {"rma_id": "RMA-10000001"}

        # Act
        result = await get_rma_status_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["rma_id"] == "RMA-10000001"
        assert result["order_id"] == "ORD-10012345"
        assert result["line_item_id"] == "LIN-10012345"
        assert result["customer_id"] == "CUS-10000001"
        assert result["return_reason"] == "defective"
        assert result["status"] == "approved"
        assert result["refund_amount"] == 899.99
        assert result["restocking_fee"] == 0.00
        assert result["return_shipping_cost"] == 0.00
        assert result["removal_fee"] == 0.00
        assert "created_date" in result

    @pytest.mark.anyio
    async def test_get_rma_status_with_fees_success(self, get_rma_status_tool, test_db):
        """Test getting RMA status for non-defective return with fees."""
        # Arrange
        request_data = {"rma_id": "RMA-10000002"}

        # Act
        result = await get_rma_status_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["rma_id"] == "RMA-10000002"
        assert result["order_id"] == "ORD-10012346"
        assert result["return_reason"] == "changed_mind"
        assert result["status"] == "refunded"
        assert result["refund_amount"] == 416.01
        assert result["restocking_fee"] == 75.00
        assert result["return_shipping_cost"] == 8.99
        assert result["removal_fee"] == 0.00

    @pytest.mark.anyio
    async def test_get_rma_status_shipped_to_warehouse(
        self, get_rma_status_tool, test_db
    ):
        """Test getting RMA status for item shipped to warehouse."""
        # Arrange
        request_data = {"rma_id": "RMA-10000003"}

        # Act
        result = await get_rma_status_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["rma_id"] == "RMA-10000003"
        assert result["return_reason"] == "damaged_in_transit"
        assert result["status"] == "shipped_to_warehouse"

    @pytest.mark.anyio
    async def test_get_rma_status_with_removal_fee(self, get_rma_status_tool, test_db):
        """Test getting RMA status for appliance with removal fee."""
        # Arrange
        request_data = {"rma_id": "RMA-10000004"}

        # Act
        result = await get_rma_status_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["rma_id"] == "RMA-10000004"
        assert result["return_reason"] == "not_as_expected"
        assert result["refund_amount"] == 1614.99
        assert result["restocking_fee"] == 285.00
        assert result["removal_fee"] == 50.00

    @pytest.mark.anyio
    async def test_get_rma_status_not_found(self, get_rma_status_tool, test_db):
        """Test error when RMA is not found."""
        # Arrange
        request_data = {"rma_id": "RMA-99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_rma_status_tool.run_with_validation(test_db, request_data)

        assert "RMA not found" in str(error.value)

    @pytest.mark.anyio
    async def test_get_rma_status_empty_database(self, get_rma_status_tool, empty_db):
        """Test getting RMA status from empty database."""
        # Arrange
        request_data = {"rma_id": "RMA-10000001"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_rma_status_tool.run_with_validation(empty_db, request_data)

        assert "RMA not found" in str(error.value)
