# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for add_points_to_balance tool."""

import pytest
from ms_toloka_servers.toolslib.external_retail_toolset.salesforce.models import (
    MembershipRecord,
    MembershipStatus,
)
from ms_toloka_servers.toolslib.external_retail_toolset.salesforce.tools.add_points_to_balance import (
    AddPointsToBalanceTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestAddPointsToBalance:
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
            points_balance=0,
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
    def add_points_to_balance_tool(self):
        """Create an instance of AddPointsToBalanceTool."""
        return AddPointsToBalanceTool()

    @pytest.mark.anyio
    async def test_add_points_success(self, add_points_to_balance_tool, test_db):
        """Test successfully adding points to customer balance."""
        # Arrange
        request_data = {
            "customer_id": "CUS-10000001",
            "points_to_add": 500,
            "points_reason": "refund_return",
        }

        # Act
        result = await add_points_to_balance_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["customer_id"] == "CUS-10000001"
        assert result["old_balance"] == 2500
        assert result["points_added"] == 500
        assert result["new_balance"] == 3000

        # Verify database was updated
        all_memberships = test_db.get_all(MembershipRecord)
        membership = next(m for m in all_memberships if m.customer_id == "CUS-10000001")
        assert membership.points_balance == 3000

    @pytest.mark.anyio
    async def test_add_points_to_zero_balance(
        self, add_points_to_balance_tool, test_db
    ):
        """Test adding points to customer with zero balance."""
        # Arrange
        request_data = {
            "customer_id": "CUS-10000003",
            "points_to_add": 1000,
            "points_reason": "service_recovery",
        }

        # Act
        result = await add_points_to_balance_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["customer_id"] == "CUS-10000003"
        assert result["old_balance"] == 0
        assert result["points_added"] == 1000
        assert result["new_balance"] == 1000

    @pytest.mark.anyio
    async def test_add_points_no_active_membership(
        self, add_points_to_balance_tool, test_db
    ):
        """Test that adding points to cancelled membership succeeds (policy guard removed)."""
        # Arrange
        request_data = {
            "customer_id": "CUS-10000002",
            "points_to_add": 500,
            "points_reason": "refund_return",
        }

        # Act - should succeed even for cancelled membership
        result = await add_points_to_balance_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["customer_id"] == "CUS-10000002"
        assert result["old_balance"] == 0
        assert result["points_added"] == 500
        assert result["new_balance"] == 500

    @pytest.mark.anyio
    async def test_add_points_customer_not_found(
        self, add_points_to_balance_tool, test_db
    ):
        """Test error when customer is not found."""
        # Arrange
        request_data = {
            "customer_id": "CUS-99999999",
            "points_to_add": 500,
            "points_reason": "refund_return",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await add_points_to_balance_tool.run_with_validation(test_db, request_data)

        assert "No membership record found" in str(error.value)

    @pytest.mark.anyio
    async def test_add_points_empty_database(
        self, add_points_to_balance_tool, empty_db
    ):
        """Test adding points to empty database."""
        # Arrange
        request_data = {
            "customer_id": "CUS-10000001",
            "points_to_add": 500,
            "points_reason": "refund_return",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await add_points_to_balance_tool.run_with_validation(empty_db, request_data)

        assert "No membership record found" in str(error.value)

    @pytest.mark.anyio
    async def test_add_large_points_amount(self, add_points_to_balance_tool, test_db):
        """Test adding large amount of points."""
        # Arrange
        request_data = {
            "customer_id": "CUS-10000001",
            "points_to_add": 10000,
            "points_reason": "manual_adjustment",
        }

        # Act
        result = await add_points_to_balance_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["customer_id"] == "CUS-10000001"
        assert result["old_balance"] == 2500
        assert result["points_added"] == 10000
        assert result["new_balance"] == 12500
