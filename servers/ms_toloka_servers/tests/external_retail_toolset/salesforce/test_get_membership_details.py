# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_membership_details tool."""

import pytest
from ms_toloka_servers.toolslib.external_retail_toolset.salesforce.models import (
    MembershipRecord,
    MembershipStatus,
)
from ms_toloka_servers.toolslib.external_retail_toolset.salesforce.tools.get_membership_details import (
    GetMembershipDetailsTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestGetMembershipDetails:
    @pytest.fixture
    def test_db(self):
        """Create a test database with membership records."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"membership_record": MembershipRecord}
        db._model_cls_to_stem = {MembershipRecord: "membership_record"}

        # Create test membership records
        membership1 = MembershipRecord(
            id="MEM-10000001",
            customer_id="CUS-10000001",
            membership_type="plus",
            start_date="2024-01-01T00:00:00Z",
            end_date="2024-12-31T23:59:59Z",
            status=MembershipStatus.ACTIVE,
            points_balance=2500,
        )

        membership2 = MembershipRecord(
            id="MEM-10000002",
            customer_id="CUS-10000002",
            membership_type="plus",
            start_date="2024-01-01T00:00:00Z",
            end_date="2024-12-31T23:59:59Z",
            status=MembershipStatus.CANCELLED,
            points_balance=0,
        )

        membership3 = MembershipRecord(
            id="MEM-10000003",
            customer_id="CUS-10000003",
            membership_type="plus",
            start_date="2024-01-01T00:00:00Z",
            end_date="2024-12-31T23:59:59Z",
            status=MembershipStatus.ACTIVE,
            points_balance=8500,
        )

        db._store = {MembershipRecord: [membership1, membership2, membership3]}
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"membership_record": MembershipRecord}
        db._model_cls_to_stem = {MembershipRecord: "membership_record"}
        db._store = {MembershipRecord: []}
        return db

    @pytest.fixture
    def get_membership_details_tool(self):
        """Create an instance of GetMembershipDetailsTool."""
        return GetMembershipDetailsTool()

    @pytest.mark.anyio
    async def test_get_membership_details_success(
        self, get_membership_details_tool, test_db
    ):
        """Test successfully getting membership details."""
        # Arrange
        request_data = {"customer_id": "CUS-10000001"}

        # Act
        result = await get_membership_details_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["membership_id"] == "MEM-10000001"
        assert result["customer_id"] == "CUS-10000001"
        assert result["membership_type"] == "plus"
        assert result["status"] == "active"
        assert result["points_balance"] == 2500

    @pytest.mark.anyio
    async def test_get_membership_details_cancelled_not_returned(
        self, get_membership_details_tool, test_db
    ):
        """Test that cancelled memberships are not returned."""
        # Arrange
        request_data = {"customer_id": "CUS-10000002"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_membership_details_tool.run_with_validation(test_db, request_data)

        assert "No active membership found" in str(error.value)

    @pytest.mark.anyio
    async def test_get_membership_details_not_found(
        self, get_membership_details_tool, test_db
    ):
        """Test error when customer has no active membership."""
        # Arrange
        request_data = {"customer_id": "CUS-99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_membership_details_tool.run_with_validation(test_db, request_data)

        assert "No active membership found" in str(error.value)

    @pytest.mark.anyio
    async def test_get_membership_details_empty_database(
        self, get_membership_details_tool, empty_db
    ):
        """Test getting membership details from empty database."""
        # Arrange
        request_data = {"customer_id": "CUS-10000001"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_membership_details_tool.run_with_validation(
                empty_db, request_data
            )

        assert "No active membership found" in str(error.value)

    @pytest.mark.anyio
    async def test_get_membership_details_multiple_customers(
        self, get_membership_details_tool, test_db
    ):
        """Test getting membership details for different customers."""
        # Test customer 1
        result1 = await get_membership_details_tool.run_with_validation(
            test_db, {"customer_id": "CUS-10000001"}
        )
        assert result1["points_balance"] == 2500

        # Test customer 3
        result3 = await get_membership_details_tool.run_with_validation(
            test_db, {"customer_id": "CUS-10000003"}
        )
        assert result3["points_balance"] == 8500
