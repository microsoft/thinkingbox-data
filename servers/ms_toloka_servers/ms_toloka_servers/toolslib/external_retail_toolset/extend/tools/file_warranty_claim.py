# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for filing warranty claims."""

from datetime import datetime, timezone
from typing import Any, Dict, Type

from ms_toloka_servers import InMemoryDatabase, Tool, get_schema_without_refs
from ms_toloka_servers.toolslib.external_retail_toolset.extend.models import (
    WarrantyClaim,
    WarrantyClaimStatus,
    WarrantyContract,
    WarrantyIssueType,
)
from pydantic import BaseModel, ConfigDict, Field

# Fixed time for testing purposes
FIXED_DATETIME = datetime(2025, 10, 1, 13, 0, 5, tzinfo=timezone.utc)


class FileWarrantyClaimInput(BaseModel):
    """Input for file_warranty_claim tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    contract_id: str = Field(
        ...,
        description="Warranty contract identifier",
        examples=["WCT-00012345"],
    )
    customer_id: str = Field(
        ...,
        description="Customer identifier",
        examples=["CUS-00012345"],
    )
    warranty_issue_type: WarrantyIssueType = Field(
        ...,
        description=(
            "Type of warranty issue: product_not_functioning, component_failed, "
            "performance_degradation, or accidental_damage"
        ),
        examples=["product_not_functioning"],
    )


class FileWarrantyClaimOutput(BaseModel):
    """Output for file_warranty_claim tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    claim_id: str = Field(
        ...,
        description="Generated warranty claim identifier",
        examples=["WCL-00012345"],
    )
    status: WarrantyClaimStatus = Field(
        ...,
        description="Claim status (always 'pending' for new claims)",
        examples=["pending"],
    )
    claim_date: str = Field(
        ...,
        description="Claim submission date",
        examples=["2024-10-22T11:15:00Z"],
    )


class FileWarrantyClaimTool(Tool):
    """Tool implementation for filing warranty claims with the external warranty provider."""

    @property
    def name(self) -> str:
        return "file_warranty_claim"

    @property
    def description(self) -> str:
        return (
            "File a warranty claim for defective product. Creates a "
            "warranty claim with the external warranty provider for products covered under "
            "manufacturer warranty, extended warranty, or protection plan."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(FileWarrantyClaimInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(FileWarrantyClaimOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return FileWarrantyClaimInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return FileWarrantyClaimOutput

    async def run(
        self, db: InMemoryDatabase, request: FileWarrantyClaimInput
    ) -> FileWarrantyClaimOutput:
        """File a warranty claim for a product."""
        try:
            # Verify contract_id exists
            all_contracts = db.get_all(WarrantyContract)
            contract_exists = False
            for contract in all_contracts:
                if contract.id == request.contract_id:
                    contract_exists = True
                    break

            if not contract_exists:
                raise Tool.ExecutionError(
                    f"Warranty contract not found: {request.contract_id}"
                )

            # Get all existing warranty claims to generate deterministic ID
            all_claims = db.get_all(WarrantyClaim)

            # Generate deterministic claim ID
            claim_counter = len(all_claims)
            while True:
                new_claim_id = f"WCL-2{claim_counter:07d}"
                # Check if ID already exists
                id_exists = False
                for claim in all_claims:
                    if claim.id == new_claim_id:
                        id_exists = True
                        break
                if not id_exists:
                    break
                claim_counter += 1

            # Map warranty issue type to readable description
            issue_descriptions = {
                WarrantyIssueType.product_not_functioning: "Product not functioning properly",
                WarrantyIssueType.component_failed: "Component failed",
                WarrantyIssueType.performance_degradation: "Performance degradation",
                WarrantyIssueType.accidental_damage: "Accidental damage",
            }

            issue_description = issue_descriptions.get(
                request.warranty_issue_type,
                request.warranty_issue_type.value,
            )

            # Create new warranty claim
            current_timestamp = FIXED_DATETIME
            new_claim = WarrantyClaim(
                id=new_claim_id,
                contract_id=request.contract_id,
                customer_id=request.customer_id,
                claim_date=current_timestamp,
                issue_description=issue_description,
                status=WarrantyClaimStatus.pending,
                resolution=None,
            )

            # Save to database
            db.create(new_claim)

            # Return claim information
            return FileWarrantyClaimOutput(
                claim_id=new_claim.id,
                status=new_claim.status,
                claim_date=new_claim.claim_date.isoformat(),
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to file warranty claim: {str(e)}"
            raise Tool.ExecutionError(error_message)
