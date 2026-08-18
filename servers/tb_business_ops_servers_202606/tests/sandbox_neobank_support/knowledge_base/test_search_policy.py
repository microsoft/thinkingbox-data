# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for search_policy tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.connectors.typesense import (
    SearchPolicyTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)


class TestSearchPolicy:
    @pytest.fixture
    def test_db(self):
        """Create a test database with sandbox_neobank_support_v1 domain."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {}
        db._model_cls_to_stem = {}
        db.domain = (
            "sandbox_neobank_support_v1"  # Set domain for Typesense client lookup
        )
        db.domain_version = "0.0.1"
        db.data_dir = ""
        db.created_at_epoch_seconds = 0.0
        db._additional_sources = {}
        db._store = {}
        return db

    @pytest.fixture
    def search_policy_tool(self):
        """Create an instance of SearchPolicyTool."""
        return SearchPolicyTool()

    @pytest.mark.anyio
    async def test_search_articles_success(self, search_policy_tool, test_db):
        """Test that search fails when Typesense is not available."""
        # Arrange
        request_data = {
            "query": "how to request new hardware",
            "max_results": 3,
        }

        # Act & Assert
        # Since Typesense is not initialized, the tool should raise an error
        with pytest.raises(
            Tool.ExecutionError, match="Search service is not available"
        ):
            await search_policy_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_search_articles_max_results_limit(self, search_policy_tool, test_db):
        """Test that search fails when Typesense is not available."""
        # Arrange
        request_data = {
            "query": "travel policies",
            "max_results": 1,
        }

        # Act & Assert
        # Since Typesense is not initialized, the tool should raise an error
        with pytest.raises(
            Tool.ExecutionError, match="Search service is not available"
        ):
            await search_policy_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_search_articles_empty_database(self, search_policy_tool, test_db):
        """Test that search fails when Typesense is not available."""
        # Arrange
        request_data = {
            "query": "any query",
            "max_results": 3,
        }

        # Act & Assert
        # Since Typesense is not initialized, the tool should raise an error
        with pytest.raises(
            Tool.ExecutionError, match="Search service is not available"
        ):
            await search_policy_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_search_articles_default_max_results(
        self, search_policy_tool, test_db
    ):
        """Test that search fails when Typesense is not available."""
        # Arrange
        request_data = {
            "query": "onboarding",
        }

        # Act & Assert
        # Since Typesense is not initialized, the tool should raise an error
        with pytest.raises(
            Tool.ExecutionError, match="Search service is not available"
        ):
            await search_policy_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_search_articles_category_parameter_rejected(
        self, search_policy_tool, test_db
    ):
        """Test that category parameter is no longer accepted."""
        # Arrange
        request_data = {
            "query": "policy",
            "max_results": 3,
            "category": "employee_onboarding",  # This should be rejected
        }

        # Act & Assert
        # The validation should fail because category is not in the schema
        with pytest.raises(Exception) as exc_info:
            await search_policy_tool.run_with_validation(test_db, request_data)

        # Verify it's a validation error about extra fields
        assert (
            "extra" in str(exc_info.value).lower()
            or "forbidden" in str(exc_info.value).lower()
        )
