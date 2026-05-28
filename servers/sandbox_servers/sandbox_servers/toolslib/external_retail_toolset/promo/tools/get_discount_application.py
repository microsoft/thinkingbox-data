# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for getting discount application details."""

from typing import Any, Dict, Optional, Type

from sandbox_servers import InMemoryDatabase, Tool, get_schema_without_refs
from sandbox_servers.toolslib.external_retail_toolset.promo.models import (
    DiscountApplication,
)
from pydantic import BaseModel, ConfigDict, Field


class GetDiscountApplicationInput(BaseModel):
    """Input for get_discount_application tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ...,
        description="Order identifier to retrieve discount application",
        examples=["ORD-00012345"],
    )


class GetDiscountApplicationOutput(BaseModel):
    """Output for get_discount_application tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    discount_app_id: str = Field(
        ...,
        description="Unique discount application identifier",
        examples=["DSC-00012345"],
    )
    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
    )
    promo_code_used: Optional[str] = Field(
        None, description="Promotion code used (if any)", examples=["SAVE20"]
    )
    points_used: int = Field(..., description="Number of points redeemed", examples=[0])
    loyalty_discount_applied: bool = Field(
        ..., description="Whether loyalty discount was applied", examples=[False]
    )
    total_discount_amount: float = Field(
        ..., description="Total discount amount applied", examples=[180.00]
    )
    stacking_rule_applied: Optional[str] = Field(
        None,
        description="Explanation of which stacking rule was applied",
        examples=["promo_code_and_points_do_not_stack_took_promo"],
    )


class GetDiscountApplicationTool(Tool):
    """Tool implementation for retrieving discount application details."""

    @property
    def name(self) -> str:
        return "get_discount_application"

    @property
    def description(self) -> str:
        return (
            "Retrieve applied discounts and stacking logic for an order. Fetches the "
            "actual discount application record for an order showing which promo code "
            "was used, points redeemed, loyalty discount applied, total discount amount, "
            "and which stacking rule was applied. Critical for resolving discount disputes "
            "by showing customer exactly what discounts were applied and why."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetDiscountApplicationInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetDiscountApplicationOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetDiscountApplicationInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetDiscountApplicationOutput

    async def run(
        self, db: InMemoryDatabase, request: GetDiscountApplicationInput
    ) -> GetDiscountApplicationOutput:
        """Retrieve discount application by order ID."""
        try:
            # Get all discount applications
            all_applications = db.get_all(DiscountApplication)

            # Find matching discount application
            matching_application = None
            for application in all_applications:
                if application.order_id == request.order_id:
                    matching_application = application
                    break

            # If no application found, return response indicating no discount
            if not matching_application:
                return GetDiscountApplicationOutput(
                    discount_app_id="",
                    order_id=request.order_id,
                    promo_code_used=None,
                    points_used=0,
                    loyalty_discount_applied=False,
                    total_discount_amount=0.0,
                    stacking_rule_applied=None,
                )

            # Return discount application details
            return GetDiscountApplicationOutput(
                discount_app_id=matching_application.id,
                order_id=matching_application.order_id,
                promo_code_used=matching_application.promo_code_used,
                points_used=matching_application.points_used,
                loyalty_discount_applied=matching_application.loyalty_discount_applied,
                total_discount_amount=matching_application.total_discount_amount,
                stacking_rule_applied=matching_application.stacking_rule_applied,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve discount application: {str(e)}"
            raise Tool.ExecutionError(error_message)
