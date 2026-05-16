# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for create_refund tool."""

import pytest
from ms_toloka_servers.toolslib.external_retail_toolset.stripe.models import (
    PaymentStatus,
    PaymentTransaction,
    Refund,
    RefundReason,
)
from ms_toloka_servers.toolslib.external_retail_toolset.stripe.tools.create_refund import (
    CreateRefundTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestCreateRefund:
    @pytest.fixture
    def test_db(self):
        """Create a test database with payment transactions and refunds."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "payment_transaction": PaymentTransaction,
            "refund": Refund,
        }
        db._model_cls_to_stem = {
            PaymentTransaction: "payment_transaction",
            Refund: "refund",
        }

        # Create test payment transactions
        transaction1 = PaymentTransaction(
            id="TXN-10000001",
            order_id="ORD-10000001",
            customer_id="CUS-10000001",
            amount=1899.99,
            status=PaymentStatus.AUTHORIZED,
            payment_method="Visa ending in 4242",
            transaction_date="2024-10-15T14:23:05Z",
            charge_reason=None,
        )

        transaction2 = PaymentTransaction(
            id="TXN-10000002",
            order_id="ORD-10000002",
            customer_id="CUS-10000002",
            amount=499.99,
            status=PaymentStatus.AUTHORIZED,
            payment_method="Mastercard ending in 1234",
            transaction_date="2024-10-10T10:15:00Z",
            charge_reason=None,
        )

        # Create existing refund
        refund1 = Refund(
            id="RFD-10000001",
            transaction_id="TXN-10000002",
            order_id="ORD-10000002",
            amount=50.00,
            refund_reason=RefundReason.PARTIAL_REFUND_MINOR_DEFECT,
            status="pending",
            refund_date="2024-10-22T11:00:00Z",
        )

        db._store = {
            PaymentTransaction: [transaction1, transaction2],
            Refund: [refund1],
        }
        return db

    @pytest.fixture
    def empty_transaction_db(self):
        """Create a test database without payment transactions."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "payment_transaction": PaymentTransaction,
            "refund": Refund,
        }
        db._model_cls_to_stem = {
            PaymentTransaction: "payment_transaction",
            Refund: "refund",
        }
        db._store = {PaymentTransaction: [], Refund: []}
        return db

    @pytest.fixture
    def create_refund_tool(self):
        """Create an instance of CreateRefundTool."""
        return CreateRefundTool()

    @pytest.mark.anyio
    async def test_create_refund_success(self, create_refund_tool, test_db):
        """Test successfully creating a refund."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000001",
            "customer_id": "CUS-10000001",
            "amount": 100.00,
            "refund_reason": "late_delivery_compensation",
        }

        # Act
        result = await create_refund_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["refund_id"].startswith("RFD-2")
        assert result["transaction_id"] == "TXN-10000001"
        assert result["amount"] == 100.00
        assert result["status"] == "pending"
        assert "refund_date" in result

        # Verify database was updated
        all_refunds = test_db.get_all(Refund)
        assert len(all_refunds) == 2
        new_refund = [r for r in all_refunds if r.id == result["refund_id"]][0]
        assert new_refund.order_id == "ORD-10000001"
        assert new_refund.amount == 100.00

    @pytest.mark.anyio
    async def test_create_partial_refund(self, create_refund_tool, test_db):
        """Test creating a partial refund."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000001",
            "customer_id": "CUS-10000001",
            "amount": 50.00,
            "refund_reason": "partial_refund_minor_defect",
        }

        # Act
        result = await create_refund_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["refund_id"].startswith("RFD-2")
        assert result["amount"] == 50.00
        assert result["status"] == "pending"

    @pytest.mark.anyio
    async def test_create_refund_discount_correction(self, create_refund_tool, test_db):
        """Test creating a refund for discount correction."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000002",
            "customer_id": "CUS-10000002",
            "amount": 25.00,
            "refund_reason": "discount_correction",
        }

        # Act
        result = await create_refund_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["refund_id"].startswith("RFD-2")
        assert result["transaction_id"] == "TXN-10000002"
        assert result["amount"] == 25.00

    @pytest.mark.anyio
    async def test_create_refund_transaction_not_found(
        self, create_refund_tool, empty_transaction_db
    ):
        """Test error when payment transaction is not found."""
        # Arrange
        request_data = {
            "order_id": "ORD-99999999",
            "customer_id": "CUS-99999999",
            "amount": 50.00,
            "refund_reason": "late_delivery_compensation",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await create_refund_tool.run_with_validation(
                empty_transaction_db, request_data
            )

        assert "Original payment transaction not found" in str(error.value)

    @pytest.mark.anyio
    async def test_create_refund_deterministic_id(self, create_refund_tool, test_db):
        """Test that refund IDs are generated deterministically."""
        # Arrange
        request_data_1 = {
            "order_id": "ORD-10000001",
            "customer_id": "CUS-10000001",
            "amount": 50.00,
            "refund_reason": "late_delivery_compensation",
        }

        # Act - Create first refund
        result1 = await create_refund_tool.run_with_validation(test_db, request_data_1)

        # Assert - Check ID format
        assert result1["refund_id"] == "RFD-20000001"

        # Act - Create second refund
        request_data_2 = {
            "order_id": "ORD-10000001",
            "customer_id": "CUS-10000001",
            "amount": 30.00,
            "refund_reason": "discount_correction",
        }
        result2 = await create_refund_tool.run_with_validation(test_db, request_data_2)

        # Assert - Second ID should be sequential
        assert result2["refund_id"] == "RFD-20000002"
