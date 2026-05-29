# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Search articles tool for Zendesk MCP server."""

import math
import re
from typing import Any, Dict, List, Optional, Tuple, Type

from tb_business_ops_servers_202606 import InMemoryDatabase, Tool
from pydantic import BaseModel, ConfigDict, Field

from ..models import Article


class SearchArticlesInput(BaseModel):
    """Input model for search_articles tool."""

    query: str = Field(
        ...,
        description="Search phrase or keywords to locate articles.",
        examples=["printer troubleshooting", "password reset", "vpn"],
    )
    locale: Optional[str] = Field(
        None,
        description="The locale (language/region) for displayed articles.",
        examples=["en-us", "es-es", "fr-fr"],
    )
    brand_id: Optional[int] = Field(
        None,
        description="Limit the search to articles in the specified brand id.",
        examples=[1001, 2001],
    )
    category: Optional[int] = Field(
        None,
        description="Limit the search to articles in the specified category id.",
        examples=[101, 102],
    )
    section: Optional[int] = Field(
        None,
        description="Limit the search to articles in the specified section id.",
        examples=[20, 30],
    )
    label_names: Optional[str] = Field(
        None,
        description="Comma-separated list of label names for filtering articles.",
        examples=["printer,error,setup", "password,security"],
    )
    multibrand: Optional[bool] = Field(
        None,
        description="Enable search across all brands if true.",
        examples=[True, False],
    )


class SearchArticlesOutput(BaseModel):
    """Output model for search_articles tool."""

    model_config = ConfigDict(extra="forbid")

    results: List[Dict[str, Any]] = Field(
        ..., description="Array of matching Zendesk articles with detailed fields."
    )


class SearchArticlesTool(Tool):
    """Tool for searching Zendesk help center articles."""

    @property
    def name(self) -> str:
        return "search_articles"

    @property
    def description(self) -> str:
        return (
            "Returns a paged list of Zendesk help center articles that match the search query, locale, brand, category, "
            "section, labels, and multibrand options. This operation supports customer self-service and support agent "
            "workflows by enabling knowledge base search and filtering. Returns up to 1000 results per query, and each "
            "article includes detailed metadata such as author, status, and content tags."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return SearchArticlesInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return SearchArticlesOutput

    async def run(
        self, db: InMemoryDatabase, request: SearchArticlesInput
    ) -> SearchArticlesOutput:
        """Search for articles matching the specified criteria."""

        # Get all articles
        all_articles = db.get_all(Article)

        # Parse the query to extract phrases, terms, and negatives
        phrases, terms, negatives = self._parse_query(request.query)

        # Filter articles by query using Zendesk-like matching
        filtered_articles = []
        for article in all_articles:
            if self._matches_query(article, phrases, terms, negatives):
                filtered_articles.append(article)

        # Filter by locale if specified
        if request.locale:
            filtered_articles = [
                article
                for article in filtered_articles
                if article.locale == request.locale
            ]

        # Filter by brand_id if specified (unless multibrand is True)
        if request.brand_id and not request.multibrand:
            filtered_articles = [
                article
                for article in filtered_articles
                if article.brand_id == request.brand_id
            ]

        # Filter by category if specified
        if request.category:
            filtered_articles = [
                article
                for article in filtered_articles
                if article.category_id == request.category
            ]

        # Filter by section if specified
        if request.section:
            filtered_articles = [
                article
                for article in filtered_articles
                if article.section_id == request.section
            ]

        # Filter by label_names if specified
        if request.label_names:
            label_list = [label.strip() for label in request.label_names.split(",")]
            filtered_articles = [
                article
                for article in filtered_articles
                if any(label in article.label_names for label in label_list)
            ]

        # Limit to 1000 results max
        filtered_articles = filtered_articles[:1000]

        # Convert to dicts
        results = [article.model_dump() for article in filtered_articles]

        return SearchArticlesOutput(results=results)

    def _parse_query(self, query: str) -> Tuple[List[str], List[str], List[str]]:
        """
        Parse search query into phrases, terms, and negatives.

        Returns:
            Tuple of (phrases, terms, negatives)
            - phrases: List of quoted phrases (mandatory matches)
            - terms: List of individual search terms
            - negatives: List of terms/phrases to exclude
        """
        phrases = []
        negatives = []
        terms = []

        # Extract all quoted phrases (both positive and negative)
        # Match -"phrase" or "phrase"
        phrase_pattern = r'(-?)"([^"]+)"'
        for match in re.finditer(phrase_pattern, query):
            is_negative = match.group(1) == "-"
            phrase_content = match.group(2).strip().lower()

            if is_negative:
                negatives.append(phrase_content)
            else:
                phrases.append(phrase_content)

        # Remove quoted phrases from query to get remaining terms
        remaining = re.sub(phrase_pattern, "", query)

        # Extract negative terms (words starting with -)
        negative_term_pattern = r"-(\w+)"
        for match in re.finditer(negative_term_pattern, remaining):
            negatives.append(match.group(1).strip().lower())

        # Remove negative terms from remaining text
        remaining = re.sub(negative_term_pattern, "", remaining)

        # Extract remaining terms (split by whitespace)
        for term in remaining.split():
            term = term.strip().lower()
            # Remove single quotes (they're ignored in Zendesk)
            term = term.replace("'", "")
            if term and len(term) > 0:
                terms.append(term)

        return phrases, terms, negatives

    def _matches_query(
        self,
        article: Article,
        phrases: List[str],
        terms: List[str],
        negatives: List[str],
    ) -> bool:
        """
        Check if article matches the query based on Zendesk logic.

        Rules:
        1. All phrases must be present (exact phrase match)
        2. If ≤2 terms: all must be present (AND logic)
        3. If >2 terms: ceil(0.4 * len(terms)) must be present
        4. Any negative term/phrase excludes the document
        """
        # Combine searchable text (title + body)
        searchable_text = (article.title + " " + article.body).lower()

        # Check negatives first (exclusion)
        for negative in negatives:
            if negative in searchable_text:
                return False

        # Check phrases (all must be present)
        for phrase in phrases:
            if phrase not in searchable_text:
                return False

        # Check terms
        if len(terms) == 0:
            # No terms, only phrases were specified (already matched above)
            return True
        elif len(terms) <= 2:
            # AND logic: all terms must be present
            for term in terms:
                if term not in searchable_text:
                    return False
            return True
        else:
            # >2 terms: need ceil(0.4 * len(terms)) matches
            required_matches = math.ceil(0.4 * len(terms))
            matches_found = sum(1 for term in terms if term in searchable_text)
            return matches_found >= required_matches
