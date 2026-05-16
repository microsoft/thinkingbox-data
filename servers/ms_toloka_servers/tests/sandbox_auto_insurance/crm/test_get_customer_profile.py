# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for the get_customer_profile tool."""

import pytest
from ms_toloka_servers.toolslib.sandbox_auto_insurance.crm.models import Customer
from ms_toloka_servers.toolslib.sandbox_auto_insurance.crm.tools.get_customer_profile import (
    GetCustomerProfileTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestGetCustomerProfile:
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
            tier="Premium",
            fraud_flag=True,
            ssn_last_4=None,
            security_question=None,
            security_answer=None,
        )

        db._store = {Customer: [customer1, customer2]}
        return db

    @pytest.fixture
    def get_customer_profile_tool(self):
        """Create an instance of GetCustomerProfileTool."""
        return GetCustomerProfileTool()

    @pytest.mark.anyio
    async def test_get_customer_profile_success(
        self, get_customer_profile_tool, test_db
    ):
        """Test retrieving a complete customer profile."""
        # Arrange
        request_data = {"customer_id": "CUS-00012345"}

        # Act
        result = await get_customer_profile_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["customer_id"] == "CUS-00012345"
        assert result["email"] == "john.smith@email.com"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Smith"
        assert result["date_of_birth"] == "1985-03-15"
        assert result["phone"] == "+1-555-0123"
        assert result["tier"] == "Standard"
        assert result["fraud_flag"] is False
        assert result["security_question"] == "What is your pet's name?"
        assert result["has_ssn_on_file"] is True

    @pytest.mark.anyio
    async def test_get_customer_profile_without_ssn(
        self, get_customer_profile_tool, test_db
    ):
        """Test profile for customer without SSN on file."""
        # Arrange
        request_data = {"customer_id": "CUS-00023456"}

        # Act
        result = await get_customer_profile_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["has_ssn_on_file"] is False
        # security_question is None, so it's excluded from result due to exclude_none=True in Tool.run_with_validation
        assert (
            "security_question" not in result or result.get("security_question") is None
        )

    @pytest.mark.anyio
    async def test_get_customer_profile_with_fraud_flag(
        self, get_customer_profile_tool, test_db
    ):
        """Test profile for customer with fraud flag."""
        # Arrange
        request_data = {"customer_id": "CUS-00023456"}

        # Act
        result = await get_customer_profile_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["fraud_flag"] is True
        assert result["tier"] == "Premium"

    @pytest.mark.anyio
    async def test_get_customer_profile_not_found(
        self, get_customer_profile_tool, test_db
    ):
        """Test retrieving a non-existing customer raises an error."""
        # Arrange
        request_data = {"customer_id": "CUS-99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="not found"):
            await get_customer_profile_tool.run_with_validation(test_db, request_data)
