# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for searching software in catalog."""

from typing import Any, Dict, List, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.software_catalog.models import (
    SoftwareCatalog,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    get_schema_without_refs,
)
from pydantic import BaseModel, ConfigDict, Field


class SoftwareCatalogSearchInput(BaseModel):
    """Input for software_catalog_search tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    software_name: str = Field(
        ...,
        description="Software name to search for (case-insensitive, partial match)",
        examples=["Tableau"],
    )


class SoftwareCatalogSearchResultItem(BaseModel):
    """Single search result item."""

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


class SoftwareCatalogSearchOutput(BaseModel):
    """Output for software_catalog_search tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    results: List[SoftwareCatalogSearchResultItem] = Field(
        ..., description="Array of matching software catalog entries"
    )


class SoftwareCatalogSearchTool(Tool):
    """Tool implementation for searching software in catalog."""

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return (
            "Search for software in the approved catalog by name. Performs case-insensitive "
            "partial match search on software names and returns matching entries with basic "
            "information including catalog ID, name, annual cost, and pool type. Use as first "
            "step in software access requests to find catalog_id for the requested software."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(SoftwareCatalogSearchInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(SoftwareCatalogSearchOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return SoftwareCatalogSearchInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return SoftwareCatalogSearchOutput

    async def run(
        self, db: InMemoryDatabase, request: SoftwareCatalogSearchInput
    ) -> SoftwareCatalogSearchOutput:
        """Search for software in catalog by name."""
        try:
            # Get all software catalog entries
            all_software = db.get_all(SoftwareCatalog)

            # Perform case-insensitive partial match search
            search_term = request.software_name.lower()
            matching_software = [
                software
                for software in all_software
                if search_term in software.name.lower()
            ]

            # If no matches found, raise 404 error
            if not matching_software:
                raise Tool.ExecutionError(
                    f"No matching software found in catalog for: {request.software_name}"
                )

            # Convert to output format
            results = [
                SoftwareCatalogSearchResultItem(
                    id=software.id,
                    name=software.name,
                    annual_cost=software.annual_cost,
                    pool_type=software.pool_type.value,
                )
                for software in matching_software
            ]

            return SoftwareCatalogSearchOutput(results=results)

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to search software catalog: {str(e)}"
            raise Tool.ExecutionError(error_message)
