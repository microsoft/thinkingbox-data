# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for getting customer profile from CDP."""

from typing import Any, Dict, Optional, Type

from sandbox_servers import InMemoryDatabase, Tool, get_schema_without_refs
from sandbox_servers.toolslib.external_retail_toolset.salesforce.models import (
    BehavioralSegment,
    CustomerProfile,
    CustomerTier,
)
from pydantic import BaseModel, ConfigDict, Field


class GetCustomerProfileInput(BaseModel):
    """Input for get_customer_profile tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    customer_id: Optional[str] = Field(
        None,
        description="Unique customer identifier. Either customer_id or email must be provided",
        examples=["CUS-00012345"],
    )
    email: Optional[str] = Field(
        None,
        description="Customer email address. Either customer_id or email must be provided",
        examples=["customer@email.com"],
    )


class GetCustomerProfileOutput(BaseModel):
    """Output for get_customer_profile tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(
        ..., description="Unique customer identifier", examples=["CUS-00012345"]
    )
    email: str = Field(
        ..., description="Customer email address", examples=["customer@email.com"]
    )
    name: str = Field(..., description="Customer full name", examples=["John Smith"])
    phone: Optional[str] = Field(
        None, description="Customer phone number", examples=["+1-555-0123"]
    )
    registration_date: str = Field(
        ..., description="Date customer registered", examples=["2023-01-15T10:30:00Z"]
    )
    customer_tier: CustomerTier = Field(
        ...,
        description="Customer tier level. One of: standard, plus_member, vip",
        examples=["plus_member"],
    )
    lifetime_value: float = Field(
        ..., description="Total lifetime value", examples=[1250.50]
    )
    total_orders: int = Field(..., description="Total number of orders", examples=[8])
    customer_score: int = Field(
        ...,
        description="Internal score 0-100. Never disclose to customer",
        examples=[75],
    )
    behavioral_segment: BehavioralSegment = Field(
        ...,
        description="Behavioral segment: regular, opportunist, bonus_hunter. Never disclose to customer",
        examples=["regular"],
    )
    acquisition_source: Optional[str] = Field(
        None, description="How customer was acquired", examples=["organic_search"]
    )
    discount_usage_rate: float = Field(
        ..., description="Rate of discount code usage", examples=[0.65]
    )


class GetCustomerProfileTool(Tool):
    """Tool implementation for retrieving customer profile from CDP."""

    @property
    def name(self) -> str:
        return "get_customer_profile"

    @property
    def description(self) -> str:
        return (
            "Retrieve complete customer profile including tier, score, and "
            "behavioral segment. Fetches detailed customer information from the "
            "Customer Data Platform including customer tier, lifetime value, "
            "total orders, internal customer score (0-100), and behavioral segment. "
            "This data is critical for determining policy enforcement, agent "
            "discretion levels, and personalized service. Customer score and "
            "behavioral segment must never be disclosed to the customer."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetCustomerProfileInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetCustomerProfileOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetCustomerProfileInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetCustomerProfileOutput

    async def run(
        self, db: InMemoryDatabase, request: GetCustomerProfileInput
    ) -> GetCustomerProfileOutput:
        """Retrieve customer profile by ID or email."""
        try:
            # Validate that at least one identifier is provided
            if not request.customer_id and not request.email:
                raise Tool.ExecutionError(
                    "Either customer_id or email must be provided"
                )

            # Get all customer profiles
            all_profiles = db.get_all(CustomerProfile)

            # Find matching profile
            matching_profile = None
            if request.customer_id:
                for profile in all_profiles:
                    if profile.id == request.customer_id:
                        matching_profile = profile
                        break
            elif request.email:
                for profile in all_profiles:
                    if profile.email == request.email:
                        matching_profile = profile
                        break

            # If no profile found, raise 404 error
            if not matching_profile:
                identifier = request.customer_id or request.email
                raise Tool.ExecutionError(
                    f"Customer not found with provided identifier: {identifier}"
                )

            # Return customer profile
            return GetCustomerProfileOutput(
                id=matching_profile.id,
                email=matching_profile.email,
                name=matching_profile.name,
                phone=matching_profile.phone,
                registration_date=matching_profile.registration_date.isoformat(),
                customer_tier=matching_profile.customer_tier,
                lifetime_value=matching_profile.lifetime_value,
                total_orders=matching_profile.total_orders,
                customer_score=matching_profile.customer_score,
                behavioral_segment=matching_profile.behavioral_segment,
                acquisition_source=matching_profile.acquisition_source,
                discount_usage_rate=matching_profile.discount_usage_rate,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve customer profile: {str(e)}"
            raise Tool.ExecutionError(error_message)
