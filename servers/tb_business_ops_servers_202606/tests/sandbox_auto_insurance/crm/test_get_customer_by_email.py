# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for the get_customer_by_email tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_auto_insurance.crm.models import Customer
from tb_business_ops_servers_202606.toolslib.sandbox_auto_insurance.crm.tools.get_customer_by_email import (
    GetCustomerByEmailTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestGetCustomerByEmail:
    @pytest.fixture
    def test_db(self):
        """Create a test database with sample data."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"customers": Customer}
        db._model_cls_to_stem = {Customer: "customers"}

        # Create sample customers
        customer1 = Customer(
            id="CUS-00012345",
            email="john.smith@email.com",
            first_name="John",
            last_name="Smith",
            date_of_birth="1985-03-15",
            phone="+1-555-0123",
            tier="Standard",
            fraud_flag=False,
            ssn_last_4="1234",
            security_question="What is your pet's name?",
            security_answer="Fluffy",
        )
        customer2 = Customer(
            id="CUS-00023456",
            email="jane.doe@email.com",
            first_name="Jane",
            last_name="Doe",
            date_of_birth="1990-07-22",
            tier="Preferred",
        )

        db._store = {Customer: [customer1, customer2]}
        return db

    @pytest.fixture
    def get_customer_by_email_tool(self):
        """Create an instance of GetCustomerByEmailTool."""
        return GetCustomerByEmailTool()

    @pytest.mark.anyio
    async def test_get_customer_by_email_success(
        self, get_customer_by_email_tool, test_db
    ):
        """Test retrieving a customer by email."""
        # Arrange
        request_data = {"email": "john.smith@email.com"}

        # Act
        result = await get_customer_by_email_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert "customer_id" in result
        assert "first_name" in result
        assert "last_name" in result
        assert result["customer_id"] == "CUS-00012345"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Smith"

    @pytest.mark.anyio
    async def test_get_customer_by_email_case_insensitive(
        self, get_customer_by_email_tool, test_db
    ):
        """Test that email lookup is case-insensitive."""
        # Arrange
        request_data = {"email": "JOHN.SMITH@EMAIL.COM"}

        # Act
        result = await get_customer_by_email_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["customer_id"] == "CUS-00012345"
        assert result["first_name"] == "John"

    @pytest.mark.anyio
    async def test_get_customer_by_email_not_found(
        self, get_customer_by_email_tool, test_db
    ):
        """Test retrieving a non-existing customer raises an error."""
        # Arrange
        request_data = {"email": "nonexistent@email.com"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="No customer found"):
            await get_customer_by_email_tool.run_with_validation(test_db, request_data)
