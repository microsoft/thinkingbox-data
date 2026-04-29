# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_discount_application tool."""

import pytest
from ms_toloka_servers.toolslib.external_retail_toolset.promo.models import (
    DiscountApplication,
)
from ms_toloka_servers.toolslib.external_retail_toolset.promo.tools.get_discount_application import (
    GetDiscountApplicationTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestGetDiscountApplication:
    @pytest.fixture
    def test_db(self):
        """Create a test database with discount applications."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"discount_application": DiscountApplication}
        db._model_cls_to_stem = {DiscountApplication: "discount_application"}

        # Create test discount applications
        # Promo code only
        app1 = DiscountApplication(
            id="DSC-10000001",
            order_id="ORD-10012345",
            promo_code_used="SAVE20",
            points_used=0,
            loyalty_discount_applied=False,
            total_discount_amount=180.00,
            stacking_rule_applied="promo_code_only",
        )

        # Points only
        app2 = DiscountApplication(
            id="DSC-10000002",
            order_id="ORD-10012346",
            promo_code_used=None,
            points_used=500,
            loyalty_discount_applied=False,
            total_discount_amount=25.00,
            stacking_rule_applied="points_redemption_only",
        )

        # All stacked
        app3 = DiscountApplication(
            id="DSC-10000003",
            order_id="ORD-10012347",
            promo_code_used="TECH15",
            points_used=200,
            loyalty_discount_applied=True,
            total_discount_amount=95.00,
            stacking_rule_applied="promo_code_and_points_and_loyalty_stacked",
        )

        # Loyalty only
        app4 = DiscountApplication(
            id="DSC-10000004",
            order_id="ORD-10012348",
            promo_code_used=None,
            points_used=0,
            loyalty_discount_applied=True,
            total_discount_amount=45.00,
            stacking_rule_applied="loyalty_pricing_only",
        )

        # Promo vs points conflict - promo won
        app5 = DiscountApplication(
            id="DSC-10000005",
            order_id="ORD-10012349",
            promo_code_used="SAVE20",
            points_used=0,
            loyalty_discount_applied=False,
            total_discount_amount=180.00,
            stacking_rule_applied="promo_code_and_points_do_not_stack_took_promo",
        )

        db._store = {DiscountApplication: [app1, app2, app3, app4, app5]}
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"discount_application": DiscountApplication}
        db._model_cls_to_stem = {DiscountApplication: "discount_application"}
        db._store = {DiscountApplication: []}
        return db

    @pytest.fixture
    def get_discount_application_tool(self):
        """Create an instance of GetDiscountApplicationTool."""
        return GetDiscountApplicationTool()

    @pytest.mark.anyio
    async def test_get_discount_application_promo_only(
        self, get_discount_application_tool, test_db
    ):
        """Test getting discount application with promo code only."""
        # Arrange
        request_data = {"order_id": "ORD-10012345"}

        # Act
        result = await get_discount_application_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["discount_app_id"] == "DSC-10000001"
        assert result["order_id"] == "ORD-10012345"
        assert result["promo_code_used"] == "SAVE20"
        assert result["points_used"] == 0
        assert result["loyalty_discount_applied"] is False
        assert result["total_discount_amount"] == 180.00
        assert result["stacking_rule_applied"] == "promo_code_only"

    @pytest.mark.anyio
    async def test_get_discount_application_points_only(
        self, get_discount_application_tool, test_db
    ):
        """Test getting discount application with points only."""
        # Arrange
        request_data = {"order_id": "ORD-10012346"}

        # Act
        result = await get_discount_application_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["discount_app_id"] == "DSC-10000002"
        assert result["order_id"] == "ORD-10012346"
        assert result.get("promo_code_used") is None
        assert result["points_used"] == 500
        assert result["loyalty_discount_applied"] is False
        assert result["total_discount_amount"] == 25.00
        assert result["stacking_rule_applied"] == "points_redemption_only"

    @pytest.mark.anyio
    async def test_get_discount_application_all_stacked(
        self, get_discount_application_tool, test_db
    ):
        """Test getting discount application with all discounts stacked."""
        # Arrange
        request_data = {"order_id": "ORD-10012347"}

        # Act
        result = await get_discount_application_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["discount_app_id"] == "DSC-10000003"
        assert result["order_id"] == "ORD-10012347"
        assert result["promo_code_used"] == "TECH15"
        assert result["points_used"] == 200
        assert result["loyalty_discount_applied"] is True
        assert result["total_discount_amount"] == 95.00
        assert (
            result["stacking_rule_applied"]
            == "promo_code_and_points_and_loyalty_stacked"
        )

    @pytest.mark.anyio
    async def test_get_discount_application_loyalty_only(
        self, get_discount_application_tool, test_db
    ):
        """Test getting discount application with loyalty pricing only."""
        # Arrange
        request_data = {"order_id": "ORD-10012348"}

        # Act
        result = await get_discount_application_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["discount_app_id"] == "DSC-10000004"
        assert result["order_id"] == "ORD-10012348"
        assert result.get("promo_code_used") is None
        assert result["points_used"] == 0
        assert result["loyalty_discount_applied"] is True
        assert result["total_discount_amount"] == 45.00
        assert result["stacking_rule_applied"] == "loyalty_pricing_only"

    @pytest.mark.anyio
    async def test_get_discount_application_stacking_conflict(
        self, get_discount_application_tool, test_db
    ):
        """Test getting discount application with stacking conflict resolution."""
        # Arrange
        request_data = {"order_id": "ORD-10012349"}

        # Act
        result = await get_discount_application_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["discount_app_id"] == "DSC-10000005"
        assert result["order_id"] == "ORD-10012349"
        assert result["promo_code_used"] == "SAVE20"
        assert result["points_used"] == 0
        assert result["loyalty_discount_applied"] is False
        assert result["total_discount_amount"] == 180.00
        assert (
            result["stacking_rule_applied"]
            == "promo_code_and_points_do_not_stack_took_promo"
        )

    @pytest.mark.anyio
    async def test_get_discount_application_not_found(
        self, get_discount_application_tool, test_db
    ):
        """Test response when discount application is not found (no discount applied)."""
        # Arrange
        request_data = {"order_id": "ORD-99999999"}

        # Act
        result = await get_discount_application_tool.run_with_validation(
            test_db, request_data
        )

        # Assert - should return success with empty/default values
        assert result["discount_app_id"] == ""
        assert result["order_id"] == "ORD-99999999"
        assert result.get("promo_code_used") is None
        assert result["points_used"] == 0
        assert result["loyalty_discount_applied"] is False
        assert result["total_discount_amount"] == 0.0
        assert result.get("stacking_rule_applied") is None

    @pytest.mark.anyio
    async def test_get_discount_application_empty_database(
        self, get_discount_application_tool, empty_db
    ):
        """Test getting discount application from empty database (no discount applied)."""
        # Arrange
        request_data = {"order_id": "ORD-10012345"}

        # Act
        result = await get_discount_application_tool.run_with_validation(
            empty_db, request_data
        )

        # Assert - should return success with empty/default values
        assert result["discount_app_id"] == ""
        assert result["order_id"] == "ORD-10012345"
        assert result.get("promo_code_used") is None
        assert result["points_used"] == 0
        assert result["loyalty_discount_applied"] is False
        assert result["total_discount_amount"] == 0.0
        assert result.get("stacking_rule_applied") is None
