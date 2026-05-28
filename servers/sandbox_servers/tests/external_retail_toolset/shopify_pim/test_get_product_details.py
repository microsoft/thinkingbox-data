# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_product_details tool."""

import pytest
from sandbox_servers.toolslib.external_retail_toolset.shopify_pim.models import (
    ProductCategory,
    ProductDetails,
)
from sandbox_servers.toolslib.external_retail_toolset.shopify_pim.tools.get_product_details import (
    GetProductDetailsTool,
)
from sandbox_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestGetProductDetails:
    @pytest.fixture
    def test_db(self):
        """Create a test database with product details."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"product_details": ProductDetails}
        db._model_cls_to_stem = {ProductDetails: "product_details"}

        # Create test products
        # Appliance requiring installation
        product1 = ProductDetails(
            sku="SKU-10000001",
            name="Samsung 28 cu ft French Door Refrigerator",
            category=ProductCategory.APPLIANCES,
            brand="Samsung",
            base_price=1899.99,
            weight_lbs=285.0,
            is_refurbished=False,
            warranty_period_days=1095,
            points_redemption_eligible=True,
            requires_installation=True,
        )

        # Electronics - TV
        product2 = ProductDetails(
            sku="SKU-10000002",
            name="LG 65 inch OLED 4K Smart TV",
            category=ProductCategory.AUDIO_VIDEO,
            brand="LG",
            base_price=1299.99,
            weight_lbs=55.0,
            is_refurbished=False,
            warranty_period_days=365,
            points_redemption_eligible=True,
            requires_installation=False,
        )

        # Apple product - no points redemption
        product3 = ProductDetails(
            sku="SKU-10000004",
            name="Apple MacBook Pro 16-inch M3 Max",
            category=ProductCategory.COMPUTING,
            brand="Apple",
            base_price=2899.99,
            weight_lbs=4.8,
            is_refurbished=False,
            warranty_period_days=365,
            points_redemption_eligible=False,
            requires_installation=False,
        )

        # Refurbished product
        product4 = ProductDetails(
            sku="SKU-10000005",
            name="Dell XPS 15 Laptop (Certified Refurbished)",
            category=ProductCategory.COMPUTING,
            brand="Dell",
            base_price=1199.99,
            weight_lbs=4.5,
            is_refurbished=True,
            warranty_period_days=365,
            points_redemption_eligible=True,
            requires_installation=False,
        )

        db._store = {ProductDetails: [product1, product2, product3, product4]}
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"product_details": ProductDetails}
        db._model_cls_to_stem = {ProductDetails: "product_details"}
        db._store = {ProductDetails: []}
        return db

    @pytest.fixture
    def get_product_details_tool(self):
        """Create an instance of GetProductDetailsTool."""
        return GetProductDetailsTool()

    @pytest.mark.anyio
    async def test_get_product_details_appliance_success(
        self, get_product_details_tool, test_db
    ):
        """Test successfully getting product details for appliance."""
        # Arrange
        request_data = {"sku": "SKU-10000001"}

        # Act
        result = await get_product_details_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["sku"] == "SKU-10000001"
        assert result["name"] == "Samsung 28 cu ft French Door Refrigerator"
        assert result["category"] == "appliances"
        assert result["brand"] == "Samsung"
        assert result["base_price"] == 1899.99
        assert result["weight_lbs"] == 285.0
        assert result["is_refurbished"] is False
        assert result["points_redemption_eligible"] is True
        assert result["requires_installation"] is True

    @pytest.mark.anyio
    async def test_get_product_details_electronics_success(
        self, get_product_details_tool, test_db
    ):
        """Test successfully getting product details for electronics."""
        # Arrange
        request_data = {"sku": "SKU-10000002"}

        # Act
        result = await get_product_details_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["sku"] == "SKU-10000002"
        assert result["name"] == "LG 65 inch OLED 4K Smart TV"
        assert result["category"] == "audio_video"
        assert result["brand"] == "LG"
        assert result["base_price"] == 1299.99
        assert result["weight_lbs"] == 55.0
        assert result["is_refurbished"] is False
        assert result["points_redemption_eligible"] is True
        assert result["requires_installation"] is False

    @pytest.mark.anyio
    async def test_get_product_details_apple_no_points(
        self, get_product_details_tool, test_db
    ):
        """Test getting product details for Apple product (no points redemption)."""
        # Arrange
        request_data = {"sku": "SKU-10000004"}

        # Act
        result = await get_product_details_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["sku"] == "SKU-10000004"
        assert result["name"] == "Apple MacBook Pro 16-inch M3 Max"
        assert result["category"] == "computing"
        assert result["brand"] == "Apple"
        assert result["base_price"] == 2899.99
        assert result["points_redemption_eligible"] is False

    @pytest.mark.anyio
    async def test_get_product_details_refurbished(
        self, get_product_details_tool, test_db
    ):
        """Test getting product details for refurbished product."""
        # Arrange
        request_data = {"sku": "SKU-10000005"}

        # Act
        result = await get_product_details_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["sku"] == "SKU-10000005"
        assert result["name"] == "Dell XPS 15 Laptop (Certified Refurbished)"
        assert result["category"] == "computing"
        assert result["brand"] == "Dell"
        assert result["is_refurbished"] is True
        assert result["points_redemption_eligible"] is True

    @pytest.mark.anyio
    async def test_get_product_details_not_found(
        self, get_product_details_tool, test_db
    ):
        """Test error when product SKU is not found."""
        # Arrange
        request_data = {"sku": "SKU-99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_product_details_tool.run_with_validation(test_db, request_data)

        assert "Product SKU not found" in str(error.value)

    @pytest.mark.anyio
    async def test_get_product_details_empty_database(
        self, get_product_details_tool, empty_db
    ):
        """Test getting product details from empty database."""
        # Arrange
        request_data = {"sku": "SKU-10000001"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_product_details_tool.run_with_validation(empty_db, request_data)

        assert "Product SKU not found" in str(error.value)

    @pytest.mark.anyio
    async def test_get_product_details_installation_requirement(
        self, get_product_details_tool, test_db
    ):
        """Test that installation requirement is correctly identified."""
        # Arrange - Appliance requiring installation
        request_appliance = {"sku": "SKU-10000001"}
        # Arrange - Electronics not requiring installation
        request_electronics = {"sku": "SKU-10000002"}

        # Act
        result_appliance = await get_product_details_tool.run_with_validation(
            test_db, request_appliance
        )
        result_electronics = await get_product_details_tool.run_with_validation(
            test_db, request_electronics
        )

        # Assert
        assert result_appliance["requires_installation"] is True
        assert result_electronics["requires_installation"] is False
