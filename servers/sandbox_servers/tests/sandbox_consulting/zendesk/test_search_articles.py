# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for search_articles tool."""

import pytest
from sandbox_servers.toolslib.sandbox_consulting.zendesk.tools.search_articles import (
    SearchArticlesTool,
)
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestSearchArticlesTool:
    """Test cases for SearchArticlesTool."""

    @pytest.fixture
    def mock_db(self, tmp_path):
        """Create a mock database with test articles."""
        from sandbox_servers.toolslib.sandbox_consulting.zendesk.models import Article

        # Create database without data directory
        db = InMemoryDatabase(data_dir=None)

        # Manually register the Article model
        db._stem_to_model_cls["articles"] = Article
        db._model_cls_to_stem[Article] = "articles"

        # Create test articles
        articles = [
            Article(
                id=1,
                url="https://example.zendesk.com/api/v2/help_center/articles/1.json",
                html_url="https://example.zendesk.com/hc/en-us/articles/1",
                title="How to troubleshoot printer issues",
                body="<p>Follow these steps to troubleshoot printer problems</p>",
                snippet="<p>Follow these steps...</p>",
                author_id=2,
                section_id=100,
                category_id=10,
                brand_id=1001,
                locale="en-us",
                source_locale="en-us",
                draft=False,
                promoted=True,
                position=1,
                vote_sum=15,
                vote_count=20,
                comments_disabled=False,
                outdated=False,
                outdated_locales=[],
                label_names=["printer", "troubleshooting"],
                content_tag_ids=[],
                user_segment_id=None,
                permission_group_id=None,
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-12-01T00:00:00Z",
                edited_at="2024-12-01T00:00:00Z",
                result_type="article",
            ),
            Article(
                id=2,
                url="https://example.zendesk.com/api/v2/help_center/articles/2.json",
                html_url="https://example.zendesk.com/hc/en-us/articles/2",
                title="VPN Connection Guide",
                body="<p>Guide for connecting to VPN</p>",
                snippet="<p>Guide for...</p>",
                author_id=5,
                section_id=101,
                category_id=11,
                brand_id=1001,
                locale="en-us",
                source_locale="en-us",
                draft=False,
                promoted=True,
                position=2,
                vote_sum=25,
                vote_count=30,
                comments_disabled=False,
                outdated=False,
                outdated_locales=[],
                label_names=["vpn", "network"],
                content_tag_ids=[],
                user_segment_id=None,
                permission_group_id=None,
                created_at="2024-01-15T00:00:00Z",
                updated_at="2024-11-20T00:00:00Z",
                edited_at="2024-11-20T00:00:00Z",
                result_type="article",
            ),
            Article(
                id=3,
                url="https://example.zendesk.com/api/v2/help_center/articles/3.json",
                html_url="https://example.zendesk.com/hc/en-us/articles/3",
                title="Email Configuration Guide",
                body="<p>Complete guide for configuring email</p>",
                snippet="<p>Complete guide...</p>",
                author_id=2,
                section_id=103,
                category_id=11,
                brand_id=2001,
                locale="en-us",
                source_locale="en-us",
                draft=False,
                promoted=True,
                position=3,
                vote_sum=18,
                vote_count=22,
                comments_disabled=False,
                outdated=False,
                outdated_locales=[],
                label_names=["email", "configuration"],
                content_tag_ids=[],
                user_segment_id=None,
                permission_group_id=None,
                created_at="2024-03-10T00:00:00Z",
                updated_at="2024-09-20T00:00:00Z",
                edited_at="2024-09-20T00:00:00Z",
                result_type="article",
            ),
        ]

        # Add articles to database store
        db._store[Article] = articles

        return db

    @pytest.fixture
    def search_articles_tool(self):
        """Create an instance of SearchArticlesTool."""
        return SearchArticlesTool()

    @pytest.mark.anyio
    async def test_search_articles_by_query(self, search_articles_tool, mock_db):
        """Test searching articles by query."""
        request_data = {"query": "printer"}

        result = await search_articles_tool.run_with_validation(mock_db, request_data)

        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "How to troubleshoot printer issues"

    @pytest.mark.anyio
    async def test_search_articles_by_query_vpn(self, search_articles_tool, mock_db):
        """Test searching articles for VPN."""
        request_data = {"query": "vpn"}

        result = await search_articles_tool.run_with_validation(mock_db, request_data)

        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "VPN Connection Guide"

    @pytest.mark.anyio
    async def test_search_articles_no_results(self, search_articles_tool, mock_db):
        """Test searching with no matching results."""
        request_data = {"query": "nonexistent"}

        result = await search_articles_tool.run_with_validation(mock_db, request_data)

        assert len(result["results"]) == 0

    @pytest.mark.anyio
    async def test_search_articles_with_locale(self, search_articles_tool, mock_db):
        """Test searching articles with locale filter."""
        request_data = {"query": "printer", "locale": "en-us"}

        result = await search_articles_tool.run_with_validation(mock_db, request_data)

        assert len(result["results"]) == 1

    @pytest.mark.anyio
    async def test_search_articles_with_section(self, search_articles_tool, mock_db):
        """Test searching articles with section filter."""
        request_data = {"query": "guide", "section": 101}

        result = await search_articles_tool.run_with_validation(mock_db, request_data)

        assert len(result["results"]) == 1
        assert result["results"][0]["section_id"] == 101

    @pytest.mark.anyio
    async def test_search_articles_with_labels(self, search_articles_tool, mock_db):
        """Test searching articles with label filter."""
        request_data = {"query": "troubleshoot", "label_names": "printer"}

        result = await search_articles_tool.run_with_validation(mock_db, request_data)

        assert len(result["results"]) == 1
        assert "printer" in result["results"][0]["label_names"]

    @pytest.mark.anyio
    async def test_search_articles_with_brand_id(self, search_articles_tool, mock_db):
        """Test searching articles with brand_id filter."""
        request_data = {"query": "guide", "brand_id": 1001}

        result = await search_articles_tool.run_with_validation(mock_db, request_data)

        # Should find only VPN article (brand_id 1001), not Email (brand_id 2001)
        assert len(result["results"]) == 1
        assert result["results"][0]["brand_id"] == 1001
        assert result["results"][0]["title"] == "VPN Connection Guide"

    @pytest.mark.anyio
    async def test_search_articles_with_category(self, search_articles_tool, mock_db):
        """Test searching articles with category filter."""
        request_data = {"query": "guide", "category": 11}

        result = await search_articles_tool.run_with_validation(mock_db, request_data)

        # Should find VPN and Email articles (both have category_id 11)
        assert len(result["results"]) == 2
        assert all(article["category_id"] == 11 for article in result["results"])

    @pytest.mark.anyio
    async def test_search_articles_with_multibrand(self, search_articles_tool, mock_db):
        """Test searching articles with multibrand enabled."""
        request_data = {"query": "guide", "brand_id": 1001, "multibrand": True}

        result = await search_articles_tool.run_with_validation(mock_db, request_data)

        # multibrand=True should ignore brand_id filter, so find all guides (VPN + Email)
        assert len(result["results"]) == 2
        # Results should include articles from different brands
        brand_ids = {article["brand_id"] for article in result["results"]}
        assert len(brand_ids) > 1  # Should have multiple brands (1001 and 2001)

    # Tests for query parsing functionality

    def test_parse_query_simple_terms(self, search_articles_tool):
        """Test parsing simple terms."""
        phrases, terms, negatives = search_articles_tool._parse_query("reset password")

        assert phrases == []
        assert terms == ["reset", "password"]
        assert negatives == []

    def test_parse_query_exact_phrase(self, search_articles_tool):
        """Test parsing exact phrase in quotes."""
        phrases, terms, negatives = search_articles_tool._parse_query(
            '"reset password"'
        )

        assert phrases == ["reset password"]
        assert terms == []
        assert negatives == []

    def test_parse_query_phrase_and_term(self, search_articles_tool):
        """Test parsing phrase with additional term."""
        phrases, terms, negatives = search_articles_tool._parse_query(
            '"reset password" authentication'
        )

        assert phrases == ["reset password"]
        assert terms == ["authentication"]
        assert negatives == []

    def test_parse_query_negative_term(self, search_articles_tool):
        """Test parsing query with negative term."""
        phrases, terms, negatives = search_articles_tool._parse_query(
            "reset password -mobile"
        )

        assert phrases == []
        assert terms == ["reset", "password"]
        assert negatives == ["mobile"]

    def test_parse_query_negative_phrase(self, search_articles_tool):
        """Test parsing query with negative phrase."""
        phrases, terms, negatives = search_articles_tool._parse_query(
            '"create user" -"admin panel"'
        )

        assert phrases == ["create user"]
        assert terms == []
        assert negatives == ["admin panel"]

    @pytest.mark.anyio
    async def test_search_two_terms_and_logic(self, search_articles_tool, mock_db):
        """Test that two terms require both to be present (AND logic)."""
        # Search for "troubleshoot printer" - need both terms
        result = await search_articles_tool.run_with_validation(
            mock_db, {"query": "troubleshoot printer"}
        )

        # Should only find the printer article that has both words
        assert len(result["results"]) == 1
        assert "printer" in result["results"][0]["title"].lower()
        assert "troubleshoot" in result["results"][0]["title"].lower()
