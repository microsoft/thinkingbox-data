# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for checking warranty coverage."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

from ms_toloka_servers import InMemoryDatabase, Tool, get_schema_without_refs
from ms_toloka_servers.toolslib.external_retail_toolset.extend.models import (
    WarrantyContract,
    WarrantyType,
)
from pydantic import BaseModel, ConfigDict, Field


class CheckWarrantyCoverageInput(BaseModel):
    """Input for check_warranty_coverage tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ...,
        description="Order identifier",
        examples=["ORD-00012345"],
    )
    sku: str = Field(
        ...,
        description="Product SKU to check warranty",
        examples=["SKU-00012345"],
    )


class CheckWarrantyCoverageOutput(BaseModel):
    """Output for check_warranty_coverage tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    has_coverage: bool = Field(
        ...,
        description="Whether active warranty exists",
        examples=[True],
    )
    contract_id: Optional[str] = Field(
        None,
        description="Warranty contract identifier",
        examples=["WCT-00012345"],
    )
    warranty_type: Optional[WarrantyType] = Field(
        None,
        description="Type of warranty: manufacturer, extended_warranty, or protection_plan",
        examples=["manufacturer"],
    )
    start_date: Optional[str] = Field(
        None,
        description="Warranty start date",
        examples=["2024-10-15T00:00:00Z"],
    )
    end_date: Optional[str] = Field(
        None,
        description="Warranty end date",
        examples=["2025-10-15T00:00:00Z"],
    )
    coverage_details: Optional[str] = Field(
        None,
        description="Coverage details description",
        examples=["Covers defects in materials and workmanship"],
    )


class CheckWarrantyCoverageTool(Tool):
    """Tool implementation for checking if a product has active warranty coverage."""

    @property
    def name(self) -> str:
        return "check_warranty_coverage"

    @property
    def description(self) -> str:
        return (
            "Check if a product has active warranty coverage. Queries warranty system to "
            "determine if a product is covered under manufacturer warranty, extended warranty, "
            "or protection plan. Returns warranty type, coverage period, and coverage details. "
            "Used for routing defective items to warranty claims vs returns."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CheckWarrantyCoverageInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CheckWarrantyCoverageOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return CheckWarrantyCoverageInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CheckWarrantyCoverageOutput

    async def run(
        self, db: InMemoryDatabase, request: CheckWarrantyCoverageInput
    ) -> CheckWarrantyCoverageOutput:
        """Check warranty coverage for a product."""
        try:
            # Get all warranty contracts
            all_contracts = db.get_all(WarrantyContract)

            # Get current date for checking validity
            # Use timezone-aware datetime to match DB dates (which have UTC timezone from JSON "Z" suffix)
            current_date = datetime.now(timezone.utc)

            # Find matching active warranty contract by order_id and sku
            matching_contract = None
            for contract in all_contracts:
                # Ensure dates are timezone-aware for comparison
                contract_start = contract.start_date
                contract_end = contract.end_date

                # If contract dates are naive, make them timezone-aware (UTC)
                if contract_start.tzinfo is None:
                    contract_start = contract_start.replace(tzinfo=timezone.utc)
                if contract_end.tzinfo is None:
                    contract_end = contract_end.replace(tzinfo=timezone.utc)

                if (
                    contract.order_id == request.order_id
                    and contract.sku == request.sku
                    and contract_start <= current_date <= contract_end
                ):
                    matching_contract = contract
                    break

            # If no active warranty found, return has_coverage=false
            if not matching_contract:
                return CheckWarrantyCoverageOutput(
                    has_coverage=False,
                    contract_id=None,
                    warranty_type=None,
                    start_date=None,
                    end_date=None,
                    coverage_details=None,
                )

            # Return warranty information
            return CheckWarrantyCoverageOutput(
                has_coverage=True,
                contract_id=matching_contract.id,
                warranty_type=matching_contract.warranty_type,
                start_date=matching_contract.start_date.isoformat(),
                end_date=matching_contract.end_date.isoformat(),
                coverage_details=matching_contract.coverage_details,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to check warranty coverage: {str(e)}"
            raise Tool.ExecutionError(error_message)
