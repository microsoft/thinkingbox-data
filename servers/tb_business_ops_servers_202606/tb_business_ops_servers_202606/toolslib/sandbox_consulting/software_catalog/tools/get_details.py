# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for retrieving detailed software information."""

from typing import Any, Dict, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.software_catalog.models import (
    SoftwareCatalog,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    get_schema_without_refs,
)
from pydantic import BaseModel, ConfigDict, Field


class SoftwareCatalogGetDetailsInput(BaseModel):
    """Input for software_catalog_get_details tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    catalog_id: str = Field(
        ...,
        description="Unique catalog identifier",
        examples=["CAT-0012345"],
    )


class SoftwareCatalogGetDetailsOutput(BaseModel):
    """Output for software_catalog_get_details tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    id: str = Field(..., description="Catalog identifier", examples=["CAT-0012345"])
    name: str = Field(..., description="Software name", examples=["Tableau Desktop"])
    annual_cost: int = Field(..., description="Annual cost in dollars", examples=[840])
    pool_type: str = Field(
        ...,
        description="License pool type (standard or enterprise)",
        examples=["standard"],
    )


class SoftwareCatalogGetDetailsTool(Tool):
    """Tool implementation for retrieving detailed software information."""

    @property
    def name(self) -> str:
        return "get_details"

    @property
    def description(self) -> str:
        return (
            "Retrieve detailed software information from catalog. Fetches complete software "
            "details including name, annual cost, and pool type. Use after catalog search to "
            "retrieve full details including annual cost for approval threshold calculations "
            "and pool_type for license allocation."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(SoftwareCatalogGetDetailsInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(SoftwareCatalogGetDetailsOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return SoftwareCatalogGetDetailsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return SoftwareCatalogGetDetailsOutput

    async def run(
        self, db: InMemoryDatabase, request: SoftwareCatalogGetDetailsInput
    ) -> SoftwareCatalogGetDetailsOutput:
        """Retrieve software details by catalog ID."""
        try:
            # Get software by ID
            software = db.get_by_id(SoftwareCatalog, request.catalog_id)

            # If no software found, raise 404 error
            if not software:
                raise Tool.ExecutionError(
                    f"Software not found in catalog: {request.catalog_id}"
                )

            # Return software information
            return SoftwareCatalogGetDetailsOutput(
                id=software.id,
                name=software.name,
                annual_cost=software.annual_cost,
                pool_type=software.pool_type.value,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve software details: {str(e)}"
            raise Tool.ExecutionError(error_message)
