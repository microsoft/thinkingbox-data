# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for getting product details from PIM."""

from typing import Any, Dict, Type

from ms_toloka_servers import InMemoryDatabase, Tool, get_schema_without_refs
from ms_toloka_servers.toolslib.external_retail_toolset.shopify_pim.models import (
    ProductCategory,
    ProductDetails,
)
from pydantic import BaseModel, ConfigDict, Field


class GetProductDetailsInput(BaseModel):
    """Input for get_product_details tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    sku: str = Field(
        ...,
        description="Product SKU to retrieve details",
        examples=["SKU-00012345"],
    )


class GetProductDetailsOutput(BaseModel):
    """Output for get_product_details tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    sku: str = Field(
        ..., description="Product SKU identifier", examples=["SKU-00012345"]
    )
    name: str = Field(
        ...,
        description="Product name",
        examples=["Samsung 28 cu ft French Door Refrigerator"],
    )
    category: ProductCategory = Field(
        ...,
        description=(
            "Product category. One of: electronics, appliances, smart_home, "
            "audio_video, computing, gaming, wearables, networking"
        ),
        examples=["appliances"],
    )
    brand: str = Field(..., description="Brand name", examples=["Samsung"])
    base_price: float = Field(
        ..., description="Base price in dollars", examples=[1899.99]
    )
    weight_lbs: float = Field(
        ..., description="Product weight in pounds", examples=[285.0]
    )
    is_refurbished: bool = Field(
        ...,
        description="Whether product is refurbished. If true, can only be returned for defects",
        examples=[False],
    )
    points_redemption_eligible: bool = Field(
        ...,
        description="Whether points can be redeemed.",
        examples=[True],
    )
    requires_installation: bool = Field(
        ...,
        description="Whether product requires installation service",
        examples=[True],
    )


class GetProductDetailsTool(Tool):
    """Tool implementation for retrieving product details from PIM."""

    @property
    def name(self) -> str:
        return "get_product_details"

    @property
    def description(self) -> str:
        return (
            "Retrieve product specifications, pricing, and attributes. Fetches detailed "
            "product information including name, category, brand, pricing, weight, "
            "refurbished status, points redemption eligibility, and installation requirement."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetProductDetailsInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetProductDetailsOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetProductDetailsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetProductDetailsOutput

    async def run(
        self, db: InMemoryDatabase, request: GetProductDetailsInput
    ) -> GetProductDetailsOutput:
        """Retrieve product details by SKU."""
        try:
            # Get all products
            all_products = db.get_all(ProductDetails)

            # Find matching product
            matching_product = None
            for product in all_products:
                if product.sku == request.sku:
                    matching_product = product
                    break

            # If no product found, raise 404 error
            if not matching_product:
                raise Tool.ExecutionError(f"Product SKU not found: {request.sku}")

            # Return product details
            return GetProductDetailsOutput(
                sku=matching_product.sku,
                name=matching_product.name,
                category=matching_product.category,
                brand=matching_product.brand,
                base_price=matching_product.base_price,
                weight_lbs=matching_product.weight_lbs,
                is_refurbished=matching_product.is_refurbished,
                points_redemption_eligible=matching_product.points_redemption_eligible,
                requires_installation=matching_product.requires_installation,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve product details: {str(e)}"
            raise Tool.ExecutionError(error_message)
