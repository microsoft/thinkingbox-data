# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for software_catalog_search tool."""

import pytest
from ms_toloka_servers.toolslib.sandbox_consulting.software_catalog.models import (
    PoolType,
    SoftwareCatalog,
)
from ms_toloka_servers.toolslib.sandbox_consulting.software_catalog.tools.search import (
    SoftwareCatalogSearchTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestSoftwareCatalogSearch:
    @pytest.fixture
    def test_db(self):
        """Create a test database with software catalog entries."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "software_catalog": SoftwareCatalog,
        }
        db._model_cls_to_stem = {
            SoftwareCatalog: "software_catalog",
        }

        # Create test software catalog entries
        software1 = SoftwareCatalog(
            id="CAT-0012345",
            name="Tableau Desktop",
            annual_cost=840,
            pool_type=PoolType.STANDARD,
        )

        software2 = SoftwareCatalog(
            id="CAT-0023456",
            name="Tableau Creator",
            annual_cost=1680,
            pool_type=PoolType.STANDARD,
        )

        software3 = SoftwareCatalog(
            id="CAT-0034567",
            name="Microsoft Power BI Pro",
            annual_cost=120,
            pool_type=PoolType.ENTERPRISE,
        )

        software4 = SoftwareCatalog(
            id="CAT-0045678",
            name="Adobe Creative Cloud",
            annual_cost=600,
            pool_type=PoolType.STANDARD,
        )

        db._store = {
            SoftwareCatalog: [software1, software2, software3, software4],
        }
        return db

    @pytest.fixture
    def search_tool(self):
        """Create an instance of the search tool."""
        return SoftwareCatalogSearchTool()

    @pytest.mark.anyio
    async def test_search_success_single_match(self, search_tool, test_db):
        """Test successful search with single matching result."""
        # Arrange
        request_data = {"software_name": "Power BI"}

        # Act
        result = await search_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["id"] == "CAT-0034567"
        assert result["results"][0]["name"] == "Microsoft Power BI Pro"
        assert result["results"][0]["annual_cost"] == 120
        assert result["results"][0]["pool_type"] == "enterprise"

    @pytest.mark.anyio
    async def test_search_success_multiple_matches(self, search_tool, test_db):
        """Test successful search with multiple matching results."""
        # Arrange
        request_data = {"software_name": "Tableau"}

        # Act
        result = await search_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "results" in result
        assert len(result["results"]) == 2
        ids = {r["id"] for r in result["results"]}
        assert "CAT-0012345" in ids
        assert "CAT-0023456" in ids

    @pytest.mark.anyio
    async def test_search_case_insensitive(self, search_tool, test_db):
        """Test that search is case-insensitive."""
        # Arrange
        request_data = {"software_name": "TABLEAU"}

        # Act
        result = await search_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "results" in result
        assert len(result["results"]) == 2

    @pytest.mark.anyio
    async def test_search_partial_match(self, search_tool, test_db):
        """Test that search performs partial matching."""
        # Arrange
        request_data = {"software_name": "Adobe"}

        # Act
        result = await search_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["name"] == "Adobe Creative Cloud"

    @pytest.mark.anyio
    async def test_search_not_found(self, search_tool, test_db):
        """Test error when no matching software found."""
        # Arrange
        request_data = {"software_name": "NonExistentSoftware"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="No matching software found in catalog"
        ):
            await search_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_search_empty_database(self, search_tool):
        """Test search with empty database."""
        # Arrange
        empty_db = InMemoryDatabase.__new__(InMemoryDatabase)
        empty_db._stem_to_model_cls = {"software_catalog": SoftwareCatalog}
        empty_db._model_cls_to_stem = {SoftwareCatalog: "software_catalog"}
        empty_db._store = {SoftwareCatalog: []}
        request_data = {"software_name": "Tableau"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="No matching software found in catalog"
        ):
            await search_tool.run_with_validation(empty_db, request_data)
