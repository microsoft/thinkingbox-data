# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import typesense


class TypesenseIndexError(Exception):
    pass


HIGHLIGHT_SETTINGS = {
    "highlight_fields": "text",
    "highlight_full_fields": "text",
    "highlight_affix_num_tokens": 20,  # More tokens before and after match for better context
    "highlight_num_snippets": 5,  # Get up to 5 best snippets per document - too many?
    "highlight_snippet_threshold": 5,  # Minimum match score for snippet quality - too strict?
    "highlight_start_tag": "<mark>",
    "highlight_end_tag": "</mark>",
}


SCHEMA_FIELDS = [
    {"name": "id", "type": "string"},  # unique per chunk
    {
        "name": "source",
        "type": "string",
        "facet": True,
    },
    {"name": "chunk_index", "type": "int32"},  # 0..N-1
    {"name": "num_tokens", "type": "int32"},
    {"name": "content", "type": "string"},  # human-readable copy of chunk
    {"name": "text", "type": "string"},  # used for embedding/search
    {
        "name": "embedding",
        "type": "float[]",
        "embed": {
            "from": ["text"],
            "model_config": {
                "model_name": "ts/e5-small",
            },
        },
    },
]


def get_api_key(api_key_file: str | Path | None = None):
    if api_key_file is not None:
        try:
            with open(api_key_file, "r", encoding="utf8") as f:
                return f.read().strip()
        except FileNotFoundError:
            raise TypesenseIndexError(f"API key file {api_key_file} does not exist.")
    return os.environ.get("TYPESENSE_API_KEY", "Fake")


class TypesenseIndex:
    def __init__(
        self,
        collection_name: str,
        host: str = "127.0.0.1",
        port: int = 8108,
        timeout: float = 300.0,
        api_key_file: str | Path | None = None,
        read_only: bool = True,
        delete_on_exit: bool = False,
    ):
        self.collection_name = collection_name
        self.allowed_sources: list[str] = []
        self.read_only = read_only
        self.delete_on_exit = delete_on_exit
        if self.read_only and self.delete_on_exit:
            raise ValueError("delete_on_exit must be False when read_only is True")
        try:
            typesense_api_key = get_api_key(api_key_file)
            self.client = typesense.Client(
                {
                    "api_key": typesense_api_key,
                    "nodes": [{"host": host, "port": str(port), "protocol": "http"}],
                    # Extended timeouts and retries for reliability under high load
                    "connection_timeout_seconds": timeout,
                    "num_retries": 5,
                    "retry_interval_seconds": 2.0,
                }
            )
        except Exception as e:
            raise TypesenseIndexError("Failed to initialize Typesense client.") from e
        self._call_with_backoff(
            self._ensure_collection,
            error_message="Failed to ensure collection",
            base_delay=3.0,
        )
        self.documents = self.client.collections[self.collection_name].documents

    @staticmethod
    def _call_with_backoff(
        fn,
        *,
        error_message: str = "Operation failed",
        max_attempts: int = 5,
        base_delay: float = 2.0,
    ):
        """Call *fn* with exponential-backoff retry on Typesense 503 errors."""
        last_error = None
        for attempt in range(max_attempts):
            try:
                return fn()
            except typesense.exceptions.ServiceUnavailable as e:
                last_error = e
                delay = base_delay * (2**attempt)
                print(
                    f"Typesense 503, attempt {attempt + 1}/{max_attempts}, "
                    f"retrying in {delay:.1f}s...",
                    file=sys.stderr,
                )
                time.sleep(delay)
        raise TypesenseIndexError(
            f"{error_message} after {max_attempts} attempts"
        ) from last_error

    def _ensure_collection(self):
        collection_exists = True
        try:
            self.client.collections[self.collection_name].retrieve()
        except typesense.exceptions.ObjectNotFound:
            collection_exists = False
        if collection_exists:
            # collection exists, nothing to do
            return

        # create collection
        if self.read_only:
            raise TypesenseIndexError("Client is configured as read-only")
        try:
            self.client.collections.create(
                {
                    "name": self.collection_name,
                    "fields": SCHEMA_FIELDS,
                }
            )
        except typesense.exceptions.ObjectAlreadyExists:
            # Collection was created by a retry of a timed-out request.
            # The typesense client has built-in retry logic,
            # so if the initial create request times out but succeeds server-side,
            # a retry will hit this exception. This is safe to ignore.
            pass
        _ = self.client.collections[self.collection_name].retrieve()

    def add_source(self, source_data: dict[str, Any]):
        if self.read_only:
            raise TypesenseIndexError("Client is configured as read-only")
        name = source_data["name"]
        for snippet in source_data["snippets"]:
            doc = {
                "source": name,
                "id": "s" + uuid.uuid4().hex,
                "chunk_index": 0,
                "num_tokens": 0,
                "content": snippet,
                "text": snippet,
            }
            self._call_with_backoff(
                lambda: self.documents.create(doc),
                error_message="Failed to create document",
            )

    def set_allowed_search_sources(self, allowed_sources: list[str]):
        self.allowed_sources = allowed_sources.copy()

    def get_document_count(self) -> int:
        """Get total number of documents in collection.

        Returns:
            Number of documents in collection

        Raises:
            TypesenseIndexError: If operation fails
        """
        # Use search with empty query to get count
        result = self.documents.search(
            {
                "q": "*",
                "query_by": "text",
                "per_page": 0,
            }
        )
        count = result.get("found", 0)
        return count

    def _get_allowed_sources_filter_config(self) -> dict[str, str]:
        source_settings = {}
        if self.allowed_sources:
            # Create filter for allowed sources
            source_filters = [f"source:={source}" for source in self.allowed_sources]
            source_settings["filter_by"] = " || ".join(source_filters)
        return source_settings

    def teardown(self):
        if self.delete_on_exit and not self.read_only:
            try:
                self.client.collections[self.collection_name].delete()
            except Exception as e:
                print(f"Error deleting collection: {e}", file=sys.stderr)
                pass

    def _typesense_multi_search(self, query: str, keywords: list[str]):
        common_search_params = {
            "collection": self.collection_name,
            "group_by": "source",
            "exclude_fields": "embedding",
            "per_page": 10,
            **HIGHLIGHT_SETTINGS,
            **self._get_allowed_sources_filter_config(),
        }
        vector_search_settings = {
            "q": query,
            "query_by": "embedding,text",
            "sort_by": "_text_match:desc,_vector_distance:asc",
        }
        kw_query = " ".join([f'"{x}"' for x in keywords])
        text_search_settings = {
            "q": kw_query,
            "query_by": "text",
            "sort_by": "_text_match:desc",
        }
        multisearch_settings = {
            "searches": [vector_search_settings, text_search_settings]
        }
        return self.client.multi_search.perform(
            multisearch_settings, common_search_params
        )

    def universal_search(self, query: str, keywords: list[str]):
        try:
            result = self._typesense_multi_search(query, keywords)
            merged_results = merge_typesense_results(result, query, keywords)

            merged_results = sorted(merged_results, key=lambda x: x["vector_distance"])
            return merged_results
        except Exception as e:
            raise TypesenseIndexError(
                "Error performing universal search. Please check your query and keywords and try again."
            ) from e

    def universal_search_with_full_text(
        self, query: str, keywords: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Perform universal search combining vector and text search, returning full text instead of snippets.

        Args:
            query: Natural language search query
            keywords: Optional list of keywords for text search

        Returns:
            List of search results with source, score, vector_distance, and full text content

        Raises:
            TypesenseIndexError: If search fails
        """
        if keywords is None:
            keywords = []

        result = self._typesense_multi_search(query, keywords)
        merged_results = merge_typesense_results_with_full_text(result, query, keywords)
        merged_results = sorted(merged_results, key=lambda x: x["vector_distance"])
        return merged_results


def merge_typesense_results(result: dict, query: str, keywords: list[str]):
    merged_results = []
    for res in result.get("results", []):
        for grouped_hit in res.get("grouped_hits", []):
            hits = grouped_hit.get("hits", [])
            for hit in hits:
                source = hit["document"]["source"]
                snippet = extract_snippet_from_typesense_result(hit, query, keywords)
                if any(
                    r["source"] == source and r["text"] == snippet
                    for r in merged_results
                ):
                    continue
                res = {
                    "source": source,
                    "score": hit["text_match"],
                    "vector_distance": hit.get("vector_distance", 2.0),
                    "text": snippet,
                }
                merged_results.append(res)
    return merged_results


def merge_typesense_results_with_full_text(
    result: dict[str, Any], query: str, keywords: list[str]
) -> list[dict[str, Any]]:
    """Merge results from vector and text search, returning full text instead of snippets."""
    merged_results = []
    for res in result.get("results", []):
        for grouped_hit in res.get("grouped_hits", []):
            hits = grouped_hit.get("hits", [])
            for hit in hits:
                document = hit["document"]
                source = document["source"]
                # Get full text from document - prefer "text" field, fallback to "content"
                full_text = document.get("text") or document.get("content", "")
                if any(
                    r["source"] == source and r["text"] == full_text
                    for r in merged_results
                ):
                    continue
                res_dict = {
                    "source": source,
                    "score": hit["text_match"],
                    "vector_distance": hit.get("vector_distance", 2.0),
                    "text": full_text,
                }
                merged_results.append(res_dict)
    return merged_results


def extract_snippet_from_typesense_result(
    hit: dict, query: str, keywords: list[str]
) -> str:
    """Extract a contextual snippet from search hit, similar to SharePoint/Bing search"""
    document = hit["document"]

    # Check if Typesense provided highlights
    highlights: list[dict] = hit.get("highlights", [])
    if highlights:
        for highlight in highlights:
            if highlight.get("field") == "text":
                highlighted_snippets: list[str] = highlight.get("snippets", [])
                if highlighted_snippets:
                    if len(highlighted_snippets) > 1:
                        # Take the best 2 snippets and join them
                        combined_snippet = " ... ".join(highlighted_snippets[:2])
                        return substring_word_trim(combined_snippet, end=400)
                    else:
                        # Use the first highlighted snippet
                        snippet = highlighted_snippets[0]
                        return substring_word_trim(snippet, end=300)

    # Fallback
    # If typesense does not provide highlighted snippets for any reason,
    # try to extract snippets manually with more context
    text: str = document["text"]
    all_terms = [query.lower()] + [kw.lower() for kw in keywords]

    snippet_start = find_best_snippet_position(text, all_terms)

    snippet_length = 300  # Increased length for better readability
    snippet_start = max(0, snippet_start - 75)  # More context before
    snippet = substring_word_trim(
        text,
        start=snippet_start,
        end=snippet_start + snippet_length,
    )
    snippet = highlight_terms(snippet, all_terms)
    return snippet


def find_best_snippet_position(
    text: str, terms: list[str], window_size: int = 200
) -> int:
    """Find the best position to start snippet extraction based on term matches using clustering."""
    text_lower = text.lower()
    positions = []

    # Find all positions of all terms
    for term in terms:
        if not term:
            continue
        start = 0
        while True:
            idx = text_lower.find(term, start)
            if idx == -1:
                break
            positions.append(idx)
            start = idx + 1

    if not positions:
        return 0

    positions.sort()
    best_count = 0
    best_start = positions[0]

    left = 0
    for right in range(len(positions)):
        # Move left pointer to maintain window size
        while positions[right] - positions[left] > window_size:
            left += 1
        count = right - left + 1
        if count > best_count:
            best_count = count
            best_start = positions[left]

    return best_start


def highlight_terms(snippet: str, terms: list[str]) -> str:
    """Add highlighting to search terms in snippet"""
    for term in terms:
        if len(term) > 2:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            snippet = pattern.sub(lambda m: f"<mark>{m.group()}</mark>", snippet)

    return snippet


def substring_word_trim(
    text: str,
    start: int = 0,
    end: int | None = None,
    ellipsis: bool = True,
    max_trim: int = 30,
):
    if end is None:
        end = len(text)
    out = text[start:end]
    if start > 0:
        out = left_word_trim(out, ellipsis=ellipsis, max_trim=max_trim)
    if end < len(text):
        out = right_word_trim(out, ellipsis=ellipsis, max_trim=max_trim)
    return out


WORD_SEPARATORS = r"[ \t\n,;.!?:]"


def left_word_trim(
    text: str,
    ellipsis: bool = True,
    max_trim: int = 30,
):
    pos = left_find_pattern(WORD_SEPARATORS, text, max_trim)
    if pos == -1:
        return text
    text = text[pos + 1 :]
    if ellipsis:
        text = "..." + text
    return text


def right_word_trim(
    text: str,
    ellipsis: bool = True,
    max_trim: int = 30,
):
    pos = right_find_pattern(WORD_SEPARATORS, text, max_trim)
    if pos == -1:
        return text
    text = text[:pos]
    if ellipsis:
        text += "..."
    return text


def left_find_pattern(pattern: str, s: str, limit: int | None = None) -> int:
    """
    Search for the first occurrence of a regex pattern in the first `limit` characters of `s`.
    Returns the index of the match, or -1 if not found.
    """
    if limit is None:
        limit = len(s)
    head = s[:limit]
    match = re.search(pattern, head)
    if match:
        return match.start()
    return -1


def right_find_pattern(pattern: str, s: str, limit: int | None = None) -> int:
    """
    Search for the last occurrence of a regex pattern in the last `limit` characters of `s`.
    Returns the index of the match, or -1 if not found.
    """
    if limit is None:
        limit = len(s)
    tail = s[-limit:][::-1]
    match = re.search(pattern, tail)
    if match:
        # Position in the reversed tail, so convert to position in original string
        return len(s) - limit + (limit - match.start() - 1)
    return -1


def cli_main():
    import argparse
    import json

    def string_list(s):
        return [x.strip() for x in s.split(",")]

    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", default=8108)
    p.add_argument("--collection", default="search_tool")
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("-q", "--query", type=str)
    p.add_argument("-k", "--keywords", type=string_list, default=[])
    p.add_argument("-n", "--count", type=int, default=3)
    args = p.parse_args()

    client = TypesenseIndex(
        collection_name=args.collection,
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        read_only=True,
    )
    results = client.universal_search(args.query, args.keywords)
    for i, result in enumerate(results[: args.count]):
        print(f"RESULT {i}")
        print(json.dumps(result, indent=2))
        print("")


if __name__ == "__main__":
    cli_main()
