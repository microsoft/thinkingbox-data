# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for charge_customer tool."""

import pytest
from sandbox_servers.toolslib.external_retail_toolset.stripe.models import (
    ChargeReason,
    PaymentStatus,
    PaymentTransaction,
)
from sandbox_servers.toolslib.external_retail_toolset.stripe.tools.charge_customer import (
    ChargeCustomerTool,
)
from sandbox_servers.utils.sandbox_tools_system import InMemoryDatabase


class TestChargeCustomer:
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

        db._store = {PaymentTransaction: [transaction1, transaction2]}
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
    def charge_customer_tool(self):
        """Create an instance of ChargeCustomerTool."""
        return ChargeCustomerTool()

    @pytest.mark.anyio
    async def test_charge_customer_shipping_upgrade_success(
        self, charge_customer_tool, test_db
    ):
        """Test successfully charging customer for shipping upgrade."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000001",
            "customer_id": "CUS-10000001",
            "amount": 29.99,
            "charge_reason": "shipping_upgrade",
        }

        # Act
        result = await charge_customer_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["transaction_id"].startswith("TXN-2")
        assert result["order_id"] == "ORD-10000001"
        assert result["amount"] == 29.99
        assert result["status"] == "authorized"
        assert "transaction_date" in result

        # Verify database was updated
        all_transactions = test_db.get_all(PaymentTransaction)
        assert len(all_transactions) == 3
        new_transaction = [
            t for t in all_transactions if t.id == result["transaction_id"]
        ][0]
        assert new_transaction.charge_reason == ChargeReason.SHIPPING_UPGRADE

    @pytest.mark.anyio
    async def test_charge_customer_reship_fee(self, charge_customer_tool, test_db):
        """Test charging customer for reship fee."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000002",
            "customer_id": "CUS-10000002",
            "amount": 15.00,
            "charge_reason": "reship_fee",
        }

        # Act
        result = await charge_customer_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["transaction_id"].startswith("TXN-2")
        assert result["amount"] == 15.00
        assert result["status"] == "authorized"

        # Verify database
        all_transactions = test_db.get_all(PaymentTransaction)
        new_transaction = [
            t for t in all_transactions if t.id == result["transaction_id"]
        ][0]
        assert new_transaction.charge_reason == ChargeReason.RESHIP_FEE

    @pytest.mark.anyio
    async def test_charge_customer_installation_cancelled_shipping(
        self, charge_customer_tool, test_db
    ):
        """Test charging customer for installation cancellation shipping."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000001",
            "customer_id": "CUS-10000001",
            "amount": 55.00,
            "charge_reason": "installation_cancelled_shipping",
        }

        # Act
        result = await charge_customer_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["transaction_id"].startswith("TXN-2")
        assert result["amount"] == 55.00
        assert result["status"] == "authorized"

        # Verify database
        all_transactions = test_db.get_all(PaymentTransaction)
        new_transaction = [
            t for t in all_transactions if t.id == result["transaction_id"]
        ][0]
        assert (
            new_transaction.charge_reason
            == ChargeReason.INSTALLATION_CANCELLED_SHIPPING
        )

    @pytest.mark.anyio
    async def test_charge_customer_deterministic_id(
        self, charge_customer_tool, test_db
    ):
        """Test that transaction IDs are generated deterministically."""
        # Arrange
        request_data_1 = {
            "order_id": "ORD-10000001",
            "customer_id": "CUS-10000001",
            "amount": 29.99,
            "charge_reason": "shipping_upgrade",
        }

        # Act - Create first charge
        result1 = await charge_customer_tool.run_with_validation(
            test_db, request_data_1
        )

        # Assert - Check ID format
        assert result1["transaction_id"] == "TXN-20000002"

        # Act - Create second charge
        request_data_2 = {
            "order_id": "ORD-10000002",
            "customer_id": "CUS-10000002",
            "amount": 15.00,
            "charge_reason": "reship_fee",
        }
        result2 = await charge_customer_tool.run_with_validation(
            test_db, request_data_2
        )

        # Assert - Second ID should be sequential
        assert result2["transaction_id"] == "TXN-20000003"

    @pytest.mark.anyio
    async def test_charge_customer_empty_database(self, charge_customer_tool, empty_db):
        """Test charging customer with empty database creates first transaction."""
        # Arrange
        request_data = {
            "order_id": "ORD-10000001",
            "customer_id": "CUS-10000001",
            "amount": 29.99,
            "charge_reason": "shipping_upgrade",
        }

        # Act
        result = await charge_customer_tool.run_with_validation(empty_db, request_data)

        # Assert
        assert result["transaction_id"] == "TXN-20000000"
        assert result["status"] == "authorized"

        # Verify database
        all_transactions = empty_db.get_all(PaymentTransaction)
        assert len(all_transactions) == 1
