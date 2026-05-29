# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_customer_profile tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.salesforce.models import (
    BehavioralSegment,
    CustomerProfile,
    CustomerTier,
)
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.salesforce.tools.get_customer_profile import (
    GetCustomerProfileTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestGetCustomerProfile:
    @pytest.fixture
    def test_db(self):
        """Create a test database with customer profiles."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"customer_profile": CustomerProfile}
        db._model_cls_to_stem = {CustomerProfile: "customer_profile"}

        # Create test customer profiles
        customer1 = CustomerProfile(
            id="CUS-10000001",
            email="john.smith@example.com",
            name="John Smith",
            phone="+1-555-0123",
            registration_date="2023-01-15T10:30:00Z",
            customer_tier=CustomerTier.PLUS_MEMBER,
            lifetime_value=1250.50,
            total_orders=8,
            customer_score=75,
            behavioral_segment=BehavioralSegment.REGULAR,
            acquisition_source="organic_search",
            discount_usage_rate=0.65,
        )

        customer2 = CustomerProfile(
            id="CUS-10000002",
            email="jane.doe@example.com",
            name="Jane Doe",
            phone="+1-555-0124",
            registration_date="2023-03-20T14:15:00Z",
            customer_tier=CustomerTier.STANDARD,
            lifetime_value=450.00,
            total_orders=3,
            customer_score=50,
            behavioral_segment=BehavioralSegment.OPPORTUNIST,
            acquisition_source="social_media",
            discount_usage_rate=0.85,
        )

        db._store = {CustomerProfile: [customer1, customer2]}
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"customer_profile": CustomerProfile}
        db._model_cls_to_stem = {CustomerProfile: "customer_profile"}
        db._store = {CustomerProfile: []}
        return db

    @pytest.fixture
    def get_customer_profile_tool(self):
        """Create an instance of GetCustomerProfileTool."""
        return GetCustomerProfileTool()

    @pytest.mark.anyio
    async def test_get_customer_profile_by_id_success(
        self, get_customer_profile_tool, test_db
    ):
        """Test successfully getting customer profile by ID."""
        # Arrange
        request_data = {"customer_id": "CUS-10000001"}

        # Act
        result = await get_customer_profile_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["id"] == "CUS-10000001"
        assert result["email"] == "john.smith@example.com"
        assert result["name"] == "John Smith"
        assert result["phone"] == "+1-555-0123"
        assert result["customer_tier"] == "plus_member"
        assert result["lifetime_value"] == 1250.50
        assert result["total_orders"] == 8
        assert result["customer_score"] == 75
        assert result["behavioral_segment"] == "regular"
        assert result["acquisition_source"] == "organic_search"
        assert result["discount_usage_rate"] == 0.65

    @pytest.mark.anyio
    async def test_get_customer_profile_by_email_success(
        self, get_customer_profile_tool, test_db
    ):
        """Test successfully getting customer profile by email."""
        # Arrange
        request_data = {"email": "jane.doe@example.com"}

        # Act
        result = await get_customer_profile_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["id"] == "CUS-10000002"
        assert result["email"] == "jane.doe@example.com"
        assert result["name"] == "Jane Doe"
        assert result["customer_tier"] == "standard"
        assert result["behavioral_segment"] == "opportunist"

    @pytest.mark.anyio
    async def test_get_customer_profile_no_identifier(
        self, get_customer_profile_tool, test_db
    ):
        """Test error when neither customer_id nor email is provided."""
        # Arrange
        request_data = {}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_customer_profile_tool.run_with_validation(test_db, request_data)

        assert "Either customer_id or email must be provided" in str(error.value)

    @pytest.mark.anyio
    async def test_get_customer_profile_not_found_by_id(
        self, get_customer_profile_tool, test_db
    ):
        """Test error when customer is not found by ID."""
        # Arrange
        request_data = {"customer_id": "CUS-99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_customer_profile_tool.run_with_validation(test_db, request_data)

        assert "Customer not found" in str(error.value)

    @pytest.mark.anyio
    async def test_get_customer_profile_not_found_by_email(
        self, get_customer_profile_tool, test_db
    ):
        """Test error when customer is not found by email."""
        # Arrange
        request_data = {"email": "nonexistent@example.com"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_customer_profile_tool.run_with_validation(test_db, request_data)

        assert "Customer not found" in str(error.value)

    @pytest.mark.anyio
    async def test_get_customer_profile_empty_database(
        self, get_customer_profile_tool, empty_db
    ):
        """Test getting customer profile from empty database."""
        # Arrange
        request_data = {"customer_id": "CUS-10000001"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_customer_profile_tool.run_with_validation(empty_db, request_data)

        assert "Customer not found" in str(error.value)
