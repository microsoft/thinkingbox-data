# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for software_catalog_get_details tool."""

import pytest
from sandbox_servers.toolslib.sandbox_consulting.software_catalog.models import (
    PoolType,
    SoftwareCatalog,
)
from sandbox_servers.toolslib.sandbox_consulting.software_catalog.tools.get_details import (
    SoftwareCatalogGetDetailsTool,
)
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestSoftwareCatalogGetDetails:
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

        db._store = {
            SoftwareCatalog: [software1, software2, software3],
        }
        return db

    @pytest.fixture
    def get_details_tool(self):
        """Create an instance of the get_details tool."""
        return SoftwareCatalogGetDetailsTool()

    @pytest.mark.anyio
    async def test_get_details_success(self, get_details_tool, test_db):
        """Test successful retrieval of software details."""
        # Arrange
        request_data = {"catalog_id": "CAT-0012345"}

        # Act
        result = await get_details_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["id"] == "CAT-0012345"
        assert result["name"] == "Tableau Desktop"
        assert result["annual_cost"] == 840
        assert result["pool_type"] == "standard"

    @pytest.mark.anyio
    async def test_get_details_enterprise_pool(self, get_details_tool, test_db):
        """Test retrieval of software with enterprise pool type."""
        # Arrange
        request_data = {"catalog_id": "CAT-0034567"}

        # Act
        result = await get_details_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["id"] == "CAT-0034567"
        assert result["name"] == "Microsoft Power BI Pro"
        assert result["annual_cost"] == 120
        assert result["pool_type"] == "enterprise"

    @pytest.mark.anyio
    async def test_get_details_not_found(self, get_details_tool, test_db):
        """Test error when software not found."""
        # Arrange
        request_data = {"catalog_id": "CAT-9999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Software not found in catalog"):
            await get_details_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_details_empty_database(self, get_details_tool):
        """Test get_details with empty database."""
        # Arrange
        empty_db = InMemoryDatabase.__new__(InMemoryDatabase)
        empty_db._stem_to_model_cls = {"software_catalog": SoftwareCatalog}
        empty_db._model_cls_to_stem = {SoftwareCatalog: "software_catalog"}
        empty_db._store = {SoftwareCatalog: []}
        request_data = {"catalog_id": "CAT-0012345"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Software not found in catalog"):
            await get_details_tool.run_with_validation(empty_db, request_data)

    @pytest.mark.anyio
    async def test_get_details_all_fields_present(self, get_details_tool, test_db):
        """Test that all expected fields are present in the output."""
        # Arrange
        request_data = {"catalog_id": "CAT-0023456"}

        # Act
        result = await get_details_tool.run_with_validation(test_db, request_data)

        # Assert - verify all expected fields are present
        assert "id" in result
        assert "name" in result
        assert "annual_cost" in result
        assert "pool_type" in result
        # Verify values
        assert result["id"] == "CAT-0023456"
        assert result["name"] == "Tableau Creator"
        assert result["annual_cost"] == 1680
        assert result["pool_type"] == "standard"
