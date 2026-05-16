# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for searching knowledge base articles."""

import logging
from typing import Any, Dict, List, Optional, Type

from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class SearchPolicyInput(BaseModel):
    """Input for search_policy tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    query: str = Field(
        ...,
        description="Natural language search query to find relevant articles",
        examples=["how to return a product", "shipping costs and delivery time"],
    )
    max_results: Optional[int] = Field(
        default=3,
        description="Maximum number of articles to return (default: 3, max: 10)",
        examples=[3, 5],
    )


class SearchPolicyOutput(BaseModel):
    """Output for search_policy tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    snippets: List[Dict[str, Any]] = Field(
        ..., description="List of matching snippets from the knowledge base"
    )


class SearchPolicyTool(Tool):
    """Tool implementation for searching knowledge base articles with semantic search."""

    def _get_typesense_client(self, db: InMemoryDatabase) -> Optional[TypesenseIndex]:
        """Get the Typesense client for this database's domain."""
        return get_typesense()

    def _search_with_typesense(
        self, query: str, max_results: int, client: TypesenseIndex
    ) -> List[Dict[str, Any]]:
        """Search using Typesense semantic search.

        Args:
            query: Search query
            max_results: Maximum number of results
            client: Typesense client to use

        Returns:
            List of search result dictionaries with full text content
        """
        logger.info(f"Searching Typesense: query='{query}', max_results={max_results}")

        # Clear any source filters
        client.set_allowed_search_sources([])

        # Perform search with full text (not snippets)
        typesense_results = client.universal_search_with_full_text(query, keywords=[])
        logger.info(f"Typesense returned {len(typesense_results)} raw results")

        # Limit results
        limited_results = typesense_results[:max_results]
        logger.info(f"Returning {len(limited_results)} results")

        return limited_results

    @property
    def name(self) -> str:
        return "search_policy"

    @property
    def description(self) -> str:
        return (
            "Search Policy Knowledge Base using natural language queries. "
            "Uses semantic search to find relevant information "
            "based on customer questions. Returns Policy articles with titles, content, categories, "
            "and relevance scores."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(SearchPolicyInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(SearchPolicyOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return SearchPolicyInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return SearchPolicyOutput

    async def run(
        self, db: InMemoryDatabase, request: SearchPolicyInput
    ) -> SearchPolicyOutput:
        """Search for articles using natural language query."""
        try:
            logger.info(f"=== Starting article search: query='{request.query}' ===")

            # Validate max_results
            max_results = request.max_results or 3
            if max_results < 1:
                max_results = 3
            if max_results > 10:
                max_results = 10

            # Get Typesense client
            logger.info("Checking Typesense availability...")
            client = self._get_typesense_client(db)

            if not client:
                logger.error("Typesense client not available")
                raise Tool.ExecutionError("Search service is not available")

            logger.info("Typesense is available, performing search...")

            # Perform search
            snippets = self._search_with_typesense(request.query, max_results, client)
            logger.info(f"Typesense search completed, found {len(snippets)} results")

            return SearchPolicyOutput(snippets=snippets)

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to search articles: {str(e)}"
            logger.error(error_message)
            raise Tool.ExecutionError(error_message)
