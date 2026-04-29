# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for update_membership_status tool."""

import pytest
from ms_toloka_servers.toolslib.external_retail_toolset.salesforce.models import (
    BehavioralSegment,
    CustomerProfile,
    CustomerTier,
    MembershipRecord,
    MembershipStatus,
)
from ms_toloka_servers.toolslib.external_retail_toolset.salesforce.tools.update_membership_status import (
    UpdateMembershipStatusTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestUpdateMembershipStatus:
    @pytest.fixture
    def test_db(self):
        """Create a test database with customers and memberships."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "customer_profile": CustomerProfile,
            "membership_record": MembershipRecord,
        }
        db._model_cls_to_stem = {
            CustomerProfile: "customer_profile",
            MembershipRecord: "membership_record",
        }

        # Create test customers
        customer1 = CustomerProfile(
            id="CUS-10000001",
            email="john.smith@example.com",
            name="John Smith",
            phone="+1-555-0123",
            registration_date="2023-01-15T10:30:00Z",
            customer_tier=CustomerTier.STANDARD,
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
            customer_tier=CustomerTier.PLUS_MEMBER,
            lifetime_value=450.00,
            total_orders=3,
            customer_score=50,
            behavioral_segment=BehavioralSegment.OPPORTUNIST,
            acquisition_source="social_media",
            discount_usage_rate=0.85,
        )

        # Create active membership for customer2
        membership1 = MembershipRecord(
            id="MEM-10000001",
            customer_id="CUS-10000002",
            membership_type="plus",
            start_date="2024-01-01T00:00:00Z",
            end_date="2024-12-31T23:59:59Z",
            status=MembershipStatus.ACTIVE,
            points_balance=2500,
        )

        db._store = {
            CustomerProfile: [customer1, customer2],
            MembershipRecord: [membership1],
        }
        return db

    @pytest.fixture
    def update_membership_status_tool(self):
        """Create an instance of UpdateMembershipStatusTool."""
        return UpdateMembershipStatusTool()

    @pytest.mark.anyio
    async def test_upgrade_membership_success(
        self, update_membership_status_tool, test_db
    ):
        """Test successfully upgrading customer to Plus membership."""
        # Arrange
        request_data = {
            "customer_id": "CUS-10000001",
            "action": "upgrade",
            "membership_type": "plus",
        }

        # Act
        result = await update_membership_status_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["customer_id"] == "CUS-10000001"
        assert result["new_tier"] == "plus_member"
        assert result["action_completed"] == "upgraded"
        assert result["membership_id"] is not None
        assert result["start_date"] is not None
        assert result["end_date"] is not None

        # Verify customer tier was updated
        all_customers = test_db.get_all(CustomerProfile)
        customer = next(c for c in all_customers if c.id == "CUS-10000001")
        assert customer.customer_tier == CustomerTier.PLUS_MEMBER

        # Verify membership was created
        all_memberships = test_db.get_all(MembershipRecord)
        new_membership = next(
            m for m in all_memberships if m.customer_id == "CUS-10000001"
        )
        assert new_membership.status == MembershipStatus.ACTIVE
        assert new_membership.points_balance == 0

    @pytest.mark.anyio
    async def test_upgrade_membership_already_has_active(
        self, update_membership_status_tool, test_db
    ):
        """Test that upgrading customer who already has membership succeeds (policy guard removed)."""
        # Arrange
        request_data = {
            "customer_id": "CUS-10000002",
            "action": "upgrade",
            "membership_type": "plus",
        }

        # Act - should succeed even if customer already has membership
        result = await update_membership_status_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["customer_id"] == "CUS-10000002"
        assert result["action_completed"] == "upgraded"

    @pytest.mark.anyio
    async def test_upgrade_membership_missing_type(
        self, update_membership_status_tool, test_db
    ):
        """Test error when upgrading without membership_type."""
        # Arrange
        request_data = {
            "customer_id": "CUS-10000001",
            "action": "upgrade",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await update_membership_status_tool.run_with_validation(
                test_db, request_data
            )

        assert "membership_type is required" in str(error.value)

    @pytest.mark.anyio
    async def test_cancel_membership_success(
        self, update_membership_status_tool, test_db
    ):
        """Test successfully cancelling customer membership."""
        # Arrange
        request_data = {
            "customer_id": "CUS-10000002",
            "action": "cancel",
        }

        # Act
        result = await update_membership_status_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["customer_id"] == "CUS-10000002"
        assert result["new_tier"] == "standard"
        assert result["action_completed"] == "cancelled"
        # membership_id, start_date, and end_date are not included when None
        assert "membership_id" not in result or result["membership_id"] is None
        assert "start_date" not in result or result["start_date"] is None
        assert "end_date" not in result or result["end_date"] is None

        # Verify customer tier was updated
        all_customers = test_db.get_all(CustomerProfile)
        customer = next(c for c in all_customers if c.id == "CUS-10000002")
        assert customer.customer_tier == CustomerTier.STANDARD

        # Verify membership was cancelled
        all_memberships = test_db.get_all(MembershipRecord)
        membership = next(m for m in all_memberships if m.customer_id == "CUS-10000002")
        assert membership.status == MembershipStatus.CANCELLED

    @pytest.mark.anyio
    async def test_cancel_membership_no_active(
        self, update_membership_status_tool, test_db
    ):
        """Test error when cancelling membership for customer without membership record."""
        # Arrange
        request_data = {
            "customer_id": "CUS-10000001",
            "action": "cancel",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await update_membership_status_tool.run_with_validation(
                test_db, request_data
            )

        assert "No membership record found" in str(error.value)

    @pytest.mark.anyio
    async def test_update_membership_customer_not_found(
        self, update_membership_status_tool, test_db
    ):
        """Test error when customer is not found."""
        # Arrange
        request_data = {
            "customer_id": "CUS-99999999",
            "action": "upgrade",
            "membership_type": "plus",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await update_membership_status_tool.run_with_validation(
                test_db, request_data
            )

        assert "Customer not found" in str(error.value)
