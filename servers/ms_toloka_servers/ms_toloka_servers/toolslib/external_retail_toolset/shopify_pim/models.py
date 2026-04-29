# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Shopify Product Database + PIM toolset."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ProductCategory(str, Enum):
    """Product category enumeration."""

    ELECTRONICS = "electronics"
    APPLIANCES = "appliances"
    SMART_HOME = "smart_home"
    AUDIO_VIDEO = "audio_video"
    COMPUTING = "computing"
    GAMING = "gaming"
    WEARABLES = "wearables"
    NETWORKING = "networking"


class ProductDetails(BaseModel):
    """Complete product details model from PIM."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    sku: str = Field(..., description="Product SKU identifier (primary key)")
    name: str = Field(..., description="Product name")
    category: ProductCategory = Field(..., description="Product category")
    brand: str = Field(..., description="Brand name")
    base_price: float = Field(..., description="Base price in dollars")
    weight_lbs: float = Field(..., description="Product weight in pounds")
    is_refurbished: bool = Field(
        default=False,
        description="Whether product is refurbished. If true, can only be returned for defects",
    )
    warranty_period_days: int = Field(
        ...,
        description="Warranty period in days. 365 for electronics, 1095 for appliances",
    )
    points_redemption_eligible: bool = Field(
        default=True,
        description="Whether points can be redeemed. False for Apple products, laptops >$1500, premium brands",
    )
    requires_installation: bool = Field(
        default=False, description="Whether product requires installation service"
    )

    def get_id(self) -> str:
        """Return the SKU as ID."""
        return self.sku
