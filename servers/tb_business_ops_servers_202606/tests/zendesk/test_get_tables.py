# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for the get_tables tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.zendesk.tools.get_tables import GetTablesTool
from tb_business_ops_servers_202606.utils.sandbox_tools_system import InMemoryDatabase


class TestGetTables:
    @pytest.fixture
    def test_db(self):
        """Create a test database."""
        # Create an in-memory database for testing
        return InMemoryDatabase.__new__(InMemoryDatabase)

    @pytest.fixture
    def get_tables_tool(self):
        """Create an instance of GetTablesTool."""
        return GetTablesTool()

    @pytest.mark.anyio
    async def test_get_tables_returns_all_tables(self, get_tables_tool, test_db):
        """Test that get_tables returns all available tables."""
        # Act
        result = await get_tables_tool.run_with_validation(test_db, {})

        # Assert
        assert "value" in result
        tables = result["value"]

        # Verify we have tables
        assert len(tables) > 0

        # Verify expected tables are present
        table_names = [t["Name"] for t in tables]
        assert "tickets" in table_names
        assert "users" in table_names
        assert "organizations" in table_names
        assert "articles" in table_names
        assert "ticket_comments" in table_names

    @pytest.mark.anyio
    async def test_get_tables_structure(self, get_tables_tool, test_db):
        """Test that each table has required fields."""
        # Act
        result = await get_tables_tool.run_with_validation(test_db, {})

        # Assert
        tables = result["value"]

        for table in tables:
            assert "Name" in table
            assert "DisplayName" in table
            assert isinstance(table["Name"], str)
            assert isinstance(table["DisplayName"], str)
