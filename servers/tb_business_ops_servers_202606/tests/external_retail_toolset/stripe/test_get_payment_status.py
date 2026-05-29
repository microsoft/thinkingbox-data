# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_payment_status tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.stripe.models import (
    PaymentStatus,
    PaymentTransaction,
)
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.stripe.tools.get_payment_status import (
    GetPaymentStatusTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestGetPaymentStatus:
    @pytest.fixture
    def test_db(self):
        """Create a test database with payment transactions."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"payment_transaction": PaymentTransaction}
        db._model_cls_to_stem = {PaymentTransaction: "payment_transaction"}

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

        transaction3 = PaymentTransaction(
            id="TXN-10000003",
            order_id="ORD-10000003",
            customer_id="CUS-10000003",
            amount=2499.99,
            status=PaymentStatus.DECLINED,
            payment_method="Visa ending in 5678",
            transaction_date="2024-10-18T16:45:00Z",
            charge_reason=None,
        )

        db._store = {PaymentTransaction: [transaction1, transaction2, transaction3]}
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"payment_transaction": PaymentTransaction}
        db._model_cls_to_stem = {PaymentTransaction: "payment_transaction"}
        db._store = {PaymentTransaction: []}
        return db

    @pytest.fixture
    def get_payment_status_tool(self):
        """Create an instance of GetPaymentStatusTool."""
        return GetPaymentStatusTool()

    @pytest.mark.anyio
    async def test_get_payment_status_authorized_success(
        self, get_payment_status_tool, test_db
    ):
        """Test successfully getting payment status for authorized transaction."""
        # Arrange
        request_data = {"order_id": "ORD-10000001"}

        # Act
        result = await get_payment_status_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["transaction_id"] == "TXN-10000001"
        assert result["order_id"] == "ORD-10000001"
        assert result["customer_id"] == "CUS-10000001"
        assert result["amount"] == 1899.99
        assert result["status"] == "authorized"
        assert result["payment_method"] == "Visa ending in 4242"

    @pytest.mark.anyio
    async def test_get_payment_status_declined(self, get_payment_status_tool, test_db):
        """Test getting payment status for declined transaction."""
        # Arrange
        request_data = {"order_id": "ORD-10000003"}

        # Act
        result = await get_payment_status_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["transaction_id"] == "TXN-10000003"
        assert result["order_id"] == "ORD-10000003"
        assert result["status"] == "declined"
        assert result["amount"] == 2499.99

    @pytest.mark.anyio
    async def test_get_payment_status_not_found(self, get_payment_status_tool, test_db):
        """Test error when payment transaction is not found."""
        # Arrange
        request_data = {"order_id": "ORD-99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_payment_status_tool.run_with_validation(test_db, request_data)

        assert "No payment transaction found for order" in str(error.value)

    @pytest.mark.anyio
    async def test_get_payment_status_empty_database(
        self, get_payment_status_tool, empty_db
    ):
        """Test getting payment status from empty database."""
        # Arrange
        request_data = {"order_id": "ORD-10000001"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_payment_status_tool.run_with_validation(empty_db, request_data)

        assert "No payment transaction found for order" in str(error.value)
