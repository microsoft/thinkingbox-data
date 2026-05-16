# Knowledge Base Toolset

This toolset provides semantic search functionality for knowledge base articles using Typesense search engine with automatic fallback to database search.

## Features

- **Semantic Search**: Uses Typesense for vector-based semantic search when available
- **Fallback Search**: Automatically falls back to keyword-based database search when Typesense is unavailable
- **Category Filtering**: Filter articles by category (employee_onboarding, hardware_policies, travel_policies, etc.)
- **Relevance Scoring**: Returns articles with relevance scores for better result ranking

## Models

### Article
Represents a knowledge base article with:
- `id`: Unique identifier
- `title`: Article title
- `content`: Full article content
- `category`: Article category (enum)
- `tags`: List of tags for filtering
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `view_count`: Number of views
- `helpful_count`: Number of helpful votes

### ArticleCategory
Enum of available categories:
- `employee_onboarding`
- `offboarding`
- `hardware_policies`
- `software_licensing`
- `travel_policies`
- `expense_management`
- `time_tracking`
- `project_management`
- `client_access`
- `security_policies`
- `training_development`
- `hr_policies`
- `it_support`
- `general_faq`

## Tools

### search_policy

Search knowledge base articles using natural language queries.

**Input:**
- `query` (required): Natural language search query
- `max_results` (optional): Maximum number of results (default: 3, max: 10)

**Output:**
- `snippets`: List of matching snippets from the knowledge base

**Example:**
```python
request = {
    "query": "how to request new hardware",
    "max_results": 3
}
```

## Configuration

### Typesense Configuration

Set environment variables to enable Typesense search:

```bash
TYPESENSE_HOST=127.0.0.1
TYPESENSE_PORT=8108
TYPESENSE_COLLECTION=knowledge_base
TYPESENSE_API_KEY=your_api_key
```

### Fallback Behavior

When Typesense is unavailable (not configured, connection failed, or collection doesn't exist), the tool automatically falls back to database search using simple keyword matching:

- Title matches are weighted highest (2.0)
- Tag matches are weighted medium (1.0)
- Content matches are weighted lowest (0.5)

Results are sorted by relevance score descending.

## Integration

To integrate this toolset into an MCP server:

```python
from mcp_core import create_mcp_app

app = create_mcp_app(
    # ... other config ...
    extra_tools={
        "knowledge_base": "mcp_tools_library.consulting.knowledge_base",
        # ... other tools ...
    },
)
```

The tool will be available as `knowledge_base_search_policy`.

## Initial Data

The toolset includes sample articles covering various consulting topics. You can customize the articles by modifying the `initial_data/articles.json` file.

## Testing

Run tests with:
```bash
cd mcp-tools-library
uv run pytest tests/consulting/knowledge_base -v
```

All tests include both success and error cases, including:
- Basic article search
- Category filtering
- Result limiting
- Empty results
- Empty database handling
