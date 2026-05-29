# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for create_rma tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.loop_returns.models import (
    RMARecord,
    RMAReturnReason,
    RMAStatus,
)
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.loop_returns.tools.create_rma import (
    CreateRMATool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import InMemoryDatabase


class TestCreateRMA:
    @pytest.fixture
    def test_db(self):
        """Create a test database with existing RMA records."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"rma_record": RMARecord}
        db._model_cls_to_stem = {RMARecord: "rma_record"}

        # Create some existing RMA records
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

        db._store = {RMARecord: [rma1]}
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
    def create_rma_tool(self):
        """Create an instance of CreateRMATool."""
        return CreateRMATool()

    @pytest.mark.anyio
    async def test_create_rma_defective_success(self, create_rma_tool, test_db):
        """Test successfully creating RMA for defective item."""
        # Arrange
        request_data = {
            "order_id": "ORD-10012350",
            "line_item_id": "LIN-10012350",
            "customer_id": "CUS-10000002",
            "return_reason": "defective",
            "is_defective": True,
            "refund_amount": 1299.99,
            "restocking_fee": 0.00,
            "return_shipping_cost": 0.00,
            "removal_fee": 0.00,
        }

        # Act
        result = await create_rma_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert "rma_id" in result
        assert result["rma_id"].startswith("RMA-20")
        assert result["status"] == "approved"
        assert "created_date" in result

        # Assert database state
        all_rmas = test_db.get_all(RMARecord)
        assert len(all_rmas) == 2  # Original + new one

        # Find the new RMA
        new_rma = None
        for rma in all_rmas:
            if rma.id == result["rma_id"]:
                new_rma = rma
                break

        assert new_rma is not None
        assert new_rma.order_id == "ORD-10012350"
        assert new_rma.line_item_id == "LIN-10012350"
        assert new_rma.customer_id == "CUS-10000002"
        assert new_rma.return_reason == RMAReturnReason.DEFECTIVE
        assert new_rma.is_defective is True
        assert new_rma.status == RMAStatus.APPROVED
        assert new_rma.refund_amount == 1299.99
        assert new_rma.restocking_fee == 0.00

    @pytest.mark.anyio
    async def test_create_rma_non_defective_with_fees(self, create_rma_tool, test_db):
        """Test creating RMA for non-defective item with fees."""
        # Arrange
        request_data = {
            "order_id": "ORD-10012351",
            "line_item_id": "LIN-10012351",
            "customer_id": "CUS-10000003",
            "return_reason": "changed_mind",
            "is_defective": False,
            "refund_amount": 416.01,
            "restocking_fee": 75.00,
            "return_shipping_cost": 8.99,
            "removal_fee": 0.00,
        }

        # Act
        result = await create_rma_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert "rma_id" in result
        assert result["status"] == "approved"

        # Assert database state
        all_rmas = test_db.get_all(RMARecord)
        new_rma = None
        for rma in all_rmas:
            if rma.id == result["rma_id"]:
                new_rma = rma
                break

        assert new_rma is not None
        assert new_rma.return_reason == RMAReturnReason.CHANGED_MIND
        assert new_rma.is_defective is False
        assert new_rma.refund_amount == 416.01
        assert new_rma.restocking_fee == 75.00
        assert new_rma.return_shipping_cost == 8.99

    @pytest.mark.anyio
    async def test_create_rma_with_removal_fee(self, create_rma_tool, test_db):
        """Test creating RMA for appliance with removal fee."""
        # Arrange
        request_data = {
            "order_id": "ORD-10012352",
            "line_item_id": "LIN-10012352",
            "customer_id": "CUS-10000001",
            "return_reason": "not_as_expected",
            "is_defective": False,
            "refund_amount": 1614.99,
            "restocking_fee": 285.00,
            "return_shipping_cost": 0.00,
            "removal_fee": 50.00,
        }

        # Act
        result = await create_rma_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert "rma_id" in result

        # Assert database state
        all_rmas = test_db.get_all(RMARecord)
        new_rma = None
        for rma in all_rmas:
            if rma.id == result["rma_id"]:
                new_rma = rma
                break

        assert new_rma is not None
        assert new_rma.removal_fee == 50.00

    @pytest.mark.anyio
    async def test_create_rma_in_empty_database(self, create_rma_tool, empty_db):
        """Test creating first RMA in empty database."""
        # Arrange
        request_data = {
            "order_id": "ORD-10012345",
            "line_item_id": "LIN-10012345",
            "customer_id": "CUS-10000001",
            "return_reason": "defective",
            "is_defective": True,
            "refund_amount": 899.99,
            "restocking_fee": 0.00,
            "return_shipping_cost": 0.00,
            "removal_fee": 0.00,
        }

        # Act
        result = await create_rma_tool.run_with_validation(empty_db, request_data)

        # Assert response
        assert "rma_id" in result
        assert result["rma_id"].startswith("RMA-20")
        assert result["status"] == "approved"

        # Assert database state
        all_rmas = empty_db.get_all(RMARecord)
        assert len(all_rmas) == 1
        assert all_rmas[0].id == result["rma_id"]

    @pytest.mark.anyio
    async def test_create_rma_unique_id_generation(self, create_rma_tool, test_db):
        """Test that multiple RMAs get unique IDs."""
        # Arrange
        request_data1 = {
            "order_id": "ORD-10012350",
            "line_item_id": "LIN-10012350",
            "customer_id": "CUS-10000002",
            "return_reason": "defective",
            "is_defective": True,
            "refund_amount": 500.00,
            "restocking_fee": 0.00,
            "return_shipping_cost": 0.00,
            "removal_fee": 0.00,
        }

        request_data2 = {
            "order_id": "ORD-10012351",
            "line_item_id": "LIN-10012351",
            "customer_id": "CUS-10000003",
            "return_reason": "changed_mind",
            "is_defective": False,
            "refund_amount": 400.00,
            "restocking_fee": 75.00,
            "return_shipping_cost": 8.99,
            "removal_fee": 0.00,
        }

        # Act
        result1 = await create_rma_tool.run_with_validation(test_db, request_data1)
        result2 = await create_rma_tool.run_with_validation(test_db, request_data2)

        # Assert
        assert result1["rma_id"] != result2["rma_id"]
        all_rmas = test_db.get_all(RMARecord)
        assert len(all_rmas) == 3  # Original + 2 new ones

    @pytest.mark.anyio
    async def test_create_rma_without_is_defective_defaults_to_false(
        self, create_rma_tool, test_db
    ):
        """Test that is_defective defaults to False when not provided."""
        # Arrange - omit is_defective field to test default behavior
        request_data = {
            "order_id": "ORD-10012353",
            "line_item_id": "LIN-10012353",
            "customer_id": "CUS-10000004",
            "return_reason": "changed_mind",
            "refund_amount": 400.00,
            "restocking_fee": 60.00,
            "return_shipping_cost": 8.99,
            "removal_fee": 0.00,
        }

        # Act
        result = await create_rma_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert "rma_id" in result
        assert result["status"] == "approved"

        # Assert database state - verify is_defective defaulted to False
        all_rmas = test_db.get_all(RMARecord)
        new_rma = None
        for rma in all_rmas:
            if rma.id == result["rma_id"]:
                new_rma = rma
                break

        assert new_rma is not None
        assert new_rma.is_defective is False
        assert new_rma.return_reason == RMAReturnReason.CHANGED_MIND
