# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Custom Promotions Engine toolset."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DiscountType(str, Enum):
    """Discount type enumeration."""

    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    BOGO = "bogo"
    BUNDLE = "bundle"
    LOYALTY_PRICING = "loyalty_pricing"


class ActivePromotion(BaseModel):
    """Active promotion model from Promotions Engine."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique promotion identifier")
    promo_code: str = Field(..., description="Promotion code")
    discount_type: DiscountType = Field(..., description="Type of discount")
    discount_value: float = Field(
        ..., description="Discount value (percentage or fixed amount)"
    )
    stackable_with_points: bool = Field(
        default=False, description="Whether this promotion can be stacked with points"
    )
    stackable_with_loyalty: bool = Field(
        default=True,
        description="Whether this promotion can be stacked with loyalty pricing",
    )
    excluded_skus: List[str] = Field(
        default_factory=list, description="List of SKUs excluded from this promotion"
    )
    valid_from: datetime = Field(..., description="Promotion valid from date")
    valid_until: datetime = Field(..., description="Promotion valid until date")

    def get_id(self) -> str:
        """Return the ID of this promotion."""
        return self.id


class DiscountApplication(BaseModel):
    """Discount application record model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique discount application identifier")
    order_id: str = Field(..., description="Order identifier")
    promo_code_used: Optional[str] = Field(
        None, description="Promotion code used (if any)"
    )
    points_used: int = Field(default=0, description="Number of points redeemed")
    loyalty_discount_applied: bool = Field(
        default=False, description="Whether loyalty discount was applied"
    )
    total_discount_amount: float = Field(
        ..., description="Total discount amount applied"
    )
    stacking_rule_applied: Optional[str] = Field(
        None, description="Explanation of which stacking rule was applied"
    )

    def get_id(self) -> str:
        """Return the ID of this discount application."""
        return self.id
