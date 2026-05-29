# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for getting promotion details."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from tb_business_ops_servers_202606 import InMemoryDatabase, Tool, get_schema_without_refs
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.promo.models import (
    ActivePromotion,
    DiscountType,
)
from pydantic import BaseModel, ConfigDict, Field


class GetPromotionDetailsInput(BaseModel):
    """Input for get_promotion_details tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    promo_code: str = Field(
        ...,
        description="Promotion code to retrieve details",
        examples=["SAVE20"],
    )


class GetPromotionDetailsOutput(BaseModel):
    """Output for get_promotion_details tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    promo_id: str = Field(
        ..., description="Unique promotion identifier", examples=["PRM-00012345"]
    )
    promo_code: str = Field(..., description="Promotion code", examples=["SAVE20"])
    discount_type: DiscountType = Field(
        ...,
        description="Type of discount. One of: percentage, fixed_amount, bogo, bundle, loyalty_pricing",
        examples=["percentage"],
    )
    discount_value: float = Field(
        ..., description="Discount value (percentage or fixed amount)", examples=[20.00]
    )
    stackable_with_points: bool = Field(
        ...,
        description="Whether this promotion can be stacked with points",
        examples=[False],
    )
    stackable_with_loyalty: bool = Field(
        ...,
        description="Whether this promotion can be stacked with loyalty pricing",
        examples=[True],
    )
    excluded_skus: Optional[List[str]] = Field(
        None,
        description="List of SKUs excluded from this promotion",
        examples=[["SKU-00099999", "SKU-00099998"]],
    )
    valid_from: str = Field(
        ..., description="Promotion valid from date", examples=["2024-10-01T00:00:00Z"]
    )
    valid_until: str = Field(
        ..., description="Promotion valid until date", examples=["2024-10-31T23:59:59Z"]
    )


class GetPromotionDetailsTool(Tool):
    """Tool implementation for retrieving promotion details."""

    @property
    def name(self) -> str:
        return "get_promotion_details"

    @property
    def description(self) -> str:
        return (
            "Retrieve promotion code details and stacking rules. Fetches promotion "
            "information including discount type, value, stacking rules with points "
            "and loyalty pricing, and excluded SKUs. Used for discount dispute "
            "resolution to verify if promotion was applied correctly and explain "
            "stacking behavior."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetPromotionDetailsInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetPromotionDetailsOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetPromotionDetailsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetPromotionDetailsOutput

    async def run(
        self, db: InMemoryDatabase, request: GetPromotionDetailsInput
    ) -> GetPromotionDetailsOutput:
        """Retrieve promotion details by promo code."""
        try:
            # Get all active promotions
            all_promotions = db.get_all(ActivePromotion)

            # Current timestamp for validation
            current_time = datetime.now(timezone.utc)

            # Find matching promotion that is currently valid
            matching_promotion = None
            for promotion in all_promotions:
                if promotion.promo_code == request.promo_code:
                    # Check if promotion is currently valid
                    if promotion.valid_from <= current_time <= promotion.valid_until:
                        matching_promotion = promotion
                        break

            # If no valid promotion found, raise 404 error
            if not matching_promotion:
                raise Tool.ExecutionError(
                    f"Promotion code not found or expired: {request.promo_code}"
                )

            # Return promotion details
            # Ensure empty list is converted to None for excluded_skus
            excluded_skus_value = (
                matching_promotion.excluded_skus
                if matching_promotion.excluded_skus
                else None
            )

            return GetPromotionDetailsOutput(
                promo_id=matching_promotion.id,
                promo_code=matching_promotion.promo_code,
                discount_type=matching_promotion.discount_type,
                discount_value=matching_promotion.discount_value,
                stackable_with_points=matching_promotion.stackable_with_points,
                stackable_with_loyalty=matching_promotion.stackable_with_loyalty,
                excluded_skus=excluded_skus_value,
                valid_from=matching_promotion.valid_from.isoformat(),
                valid_until=matching_promotion.valid_until.isoformat(),
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve promotion details: {str(e)}"
            raise Tool.ExecutionError(error_message)
