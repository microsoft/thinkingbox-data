# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Common SearchPolicyTool implementation using Typesense semantic search.

This module provides a reusable SearchPolicyTool that can be used by any domain
that needs knowledge base search functionality via Typesense.

Usage:
    from sandbox_servers.toolslib.connectors.typesense import SearchPolicyTool

    # Use with default description
    tool = SearchPolicyTool()

    # Or customize description for domain-specific context
    tool = SearchPolicyTool(
        description="Search Banking Policy Knowledge Base for customer service guidelines..."
    )
"""

import logging
from typing import Any, Dict, List, Optional, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
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
    """Common tool for searching knowledge base with Typesense semantic search.

    This tool provides semantic search functionality for knowledge base articles
    using Typesense. It can be customized with a domain-specific description.

    The tool implements preflight_check to verify Typesense availability before
    tool execution, respecting strict mode settings.
    """

    def __init__(self, description: str | None = None):
        """Initialize SearchPolicyTool.

        Args:
            description: Custom description for domain-specific context.
                        If None, uses default generic description.
        """
        self._custom_description = description

    def _get_typesense_client(self) -> Optional[TypesenseIndex]:
        """Get the global Typesense client."""
        return get_typesense()

    def _search_with_typesense(
        self, query: str, max_results: int, client: TypesenseIndex
    ) -> List[Dict[str, Any]]:
        """Search using Typesense semantic search.

        Args:
            query: Search query
            max_results: Maximum number of results
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
        if self._custom_description:
            return self._custom_description
        return (
            "Search Policy Knowledge Base using natural language queries. "
            "Uses semantic search to find relevant information. "
            "Returns articles with titles, content, and relevance scores."
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

    async def preflight_check(self, db: InMemoryDatabase) -> None:
        """Verify Typesense service is available.

        Checks that:
        1. Typesense client is registered for the domain
        2. A test query can be executed successfully

        Raises ExternalServiceError when strict mode >= EXTERNAL.
        """

        client = self._get_typesense_client()
        domain = getattr(db, "domain", "unknown")

        if client is None:
            msg = f"Typesense client not available for domain '{domain}'"
            logger.error(msg)
            if is_strict(StrictMode.EXTERNAL):
                raise ExternalServiceError(msg)
            return

        # Verify with test query
        try:
            client.universal_search_with_full_text("preflight", keywords=[])
            logger.info(f"SearchPolicyTool preflight passed for domain '{domain}'")
        except Exception as e:
            msg = f"Typesense search failed: {e}"
            logger.error(msg)
            if is_strict(StrictMode.EXTERNAL):
                raise ExternalServiceError(msg)

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
            client = self._get_typesense_client()

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
