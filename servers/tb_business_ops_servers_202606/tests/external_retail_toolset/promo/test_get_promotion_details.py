# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_promotion_details tool."""

from datetime import datetime, timedelta, timezone

import pytest
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.promo.models import (
    ActivePromotion,
    DiscountType,
)
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.promo.tools.get_promotion_details import (
    GetPromotionDetailsTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestGetPromotionDetails:
    @pytest.fixture
    def test_db(self):
        """Create a test database with active promotions."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"active_promotion": ActivePromotion}
        db._model_cls_to_stem = {ActivePromotion: "active_promotion"}

        # Create test promotions
        # Valid promotion
        promo1 = ActivePromotion(
            id="PRM-10000001",
            promo_code="SAVE20",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=20.00,
            stackable_with_points=False,
            stackable_with_loyalty=True,
            excluded_skus=["SKU-10099999", "SKU-10099998"],
            valid_from=datetime.now(timezone.utc) - timedelta(days=10),
            valid_until=datetime.now(timezone.utc) + timedelta(days=10),
        )

        # Another valid promotion
        promo2 = ActivePromotion(
            id="PRM-10000002",
            promo_code="TECH15",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=15.00,
            stackable_with_points=True,
            stackable_with_loyalty=True,
            excluded_skus=[],
            valid_from=datetime.now(timezone.utc) - timedelta(days=30),
            valid_until=datetime.now(timezone.utc) + timedelta(days=60),
        )

        # Expired promotion
        promo3 = ActivePromotion(
            id="PRM-10000003",
            promo_code="EXPIRED",
            discount_type=DiscountType.FIXED_AMOUNT,
            discount_value=50.00,
            stackable_with_points=False,
            stackable_with_loyalty=False,
            excluded_skus=[],
            valid_from=datetime.now(timezone.utc) - timedelta(days=60),
            valid_until=datetime.now(timezone.utc) - timedelta(days=30),
        )

        # Future promotion
        promo4 = ActivePromotion(
            id="PRM-10000004",
            promo_code="FUTURE",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=10.00,
            stackable_with_points=True,
            stackable_with_loyalty=True,
            excluded_skus=[],
            valid_from=datetime.now(timezone.utc) + timedelta(days=10),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
        )

        db._store = {ActivePromotion: [promo1, promo2, promo3, promo4]}
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"active_promotion": ActivePromotion}
        db._model_cls_to_stem = {ActivePromotion: "active_promotion"}
        db._store = {ActivePromotion: []}
        return db

    @pytest.fixture
    def get_promotion_details_tool(self):
        """Create an instance of GetPromotionDetailsTool."""
        return GetPromotionDetailsTool()

    @pytest.mark.anyio
    async def test_get_promotion_details_success(
        self, get_promotion_details_tool, test_db
    ):
        """Test successfully getting promotion details for valid promotion."""
        # Arrange
        request_data = {"promo_code": "SAVE20"}

        # Act
        result = await get_promotion_details_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["promo_id"] == "PRM-10000001"
        assert result["promo_code"] == "SAVE20"
        assert result["discount_type"] == "percentage"
        assert result["discount_value"] == 20.00
        assert result["stackable_with_points"] is False
        assert result["stackable_with_loyalty"] is True
        assert result["excluded_skus"] == ["SKU-10099999", "SKU-10099998"]
        assert "valid_from" in result
        assert "valid_until" in result

    @pytest.mark.anyio
    async def test_get_promotion_details_stackable_promotion(
        self, get_promotion_details_tool, test_db
    ):
        """Test getting promotion details for stackable promotion."""
        # Arrange
        request_data = {"promo_code": "TECH15"}

        # Act
        result = await get_promotion_details_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["promo_id"] == "PRM-10000002"
        assert result["promo_code"] == "TECH15"
        assert result["discount_type"] == "percentage"
        assert result["discount_value"] == 15.00
        assert result["stackable_with_points"] is True
        assert result["stackable_with_loyalty"] is True
        assert result.get("excluded_skus") is None or result.get("excluded_skus") == []

    @pytest.mark.anyio
    async def test_get_promotion_details_expired_promo(
        self, get_promotion_details_tool, test_db
    ):
        """Test error when promotion is expired."""
        # Arrange
        request_data = {"promo_code": "EXPIRED"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_promotion_details_tool.run_with_validation(test_db, request_data)

        assert "not found or expired" in str(error.value)

    @pytest.mark.anyio
    async def test_get_promotion_details_future_promo(
        self, get_promotion_details_tool, test_db
    ):
        """Test error when promotion has not started yet."""
        # Arrange
        request_data = {"promo_code": "FUTURE"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_promotion_details_tool.run_with_validation(test_db, request_data)

        assert "not found or expired" in str(error.value)

    @pytest.mark.anyio
    async def test_get_promotion_details_not_found(
        self, get_promotion_details_tool, test_db
    ):
        """Test error when promotion code does not exist."""
        # Arrange
        request_data = {"promo_code": "NONEXISTENT"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_promotion_details_tool.run_with_validation(test_db, request_data)

        assert "not found or expired" in str(error.value)

    @pytest.mark.anyio
    async def test_get_promotion_details_empty_database(
        self, get_promotion_details_tool, empty_db
    ):
        """Test getting promotion details from empty database."""
        # Arrange
        request_data = {"promo_code": "SAVE20"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_promotion_details_tool.run_with_validation(empty_db, request_data)

        assert "not found or expired" in str(error.value)
