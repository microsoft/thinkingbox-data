# Zendesk MCP Server

Mock tools server for Zendesk connector, providing realistic simulation of Zendesk API operations.

## Overview

This MCP server provides a comprehensive set of tools for interacting with Zendesk data, including:

- **CRUD operations** on Zendesk tables (tickets, users, organizations, comments, etc.)
- **Advanced article search** with Zendesk-like query syntax (phrases, negative terms, thresholds)
- **OData v4 filtering** for complex queries
- **Table management** and metadata

## Quick Start

### Installation

```bash
cd mcp_servers/zendesk
uv sync
```

### Running the Server

```bash
# Development server
uv run uvicorn src.main:app --reload --port 8000

# Or using the standard entry point
uv run python -m src.main
```

### Running Tests

```bash
# Run all tests
uv run pytest -v

# Run specific test file
uv run pytest tests/tools/test_search_articles.py -v

# From repository root
./scripts/pytest-wrapper.sh mcp_servers/zendesk
```

## Available Tools

| Tool | Description |
|------|-------------|
| `get_tables` | Returns list of all available Zendesk tables |
| `get_items` | Retrieves items from a table with OData filtering |
| `get_item` | Retrieves a single item by ID |
| `create_item` | Creates a new item in a table |
| `update_item` | Updates an existing item |
| `delete_item` | Deletes an item from a table |
| `search_articles` | Searches help center articles with advanced query syntax |

## Key Features

### 1. Advanced Article Search

The `search_articles` tool mimics Zendesk's end-user search behavior:

- **Exact phrases** with double quotes: `"password reset"`
- **Negative terms/phrases**: `printer -installation`
- **Term thresholds**: For >2 terms, requires 40% match
- **Multiple filters**: locale, brand_id, category, section, labels
- **Multi-brand search**: Search across all brands

Example:
```json
{
  "query": "\"two factor\" authentication -deprecated",
  "locale": "en-us",
  "brand_id": 1001,
  "category": 12
}
```

### 2. OData v4 Filtering

The `get_items` tool supports OData filtering for complex queries:

- **Comparison operators**: `eq`, `ne`, `gt`, `ge`, `lt`, `le`
- **Logical operators**: `and`, `or`
- **Field selection**: `select` parameter
- **Sorting**: `orderby` parameter
- **Pagination**: `top` and `skip` parameters

Example:
```json
{
  "table": "tickets",
  "filter": "status eq 'open' and priority gt 2",
  "select": "id,subject,status,priority",
  "orderby": "created_at desc",
  "top": 50
}
```

### 3. Special Handling for Ticket Comments

The `ticket_comments` table has special restrictions:

- ✅ **Can CREATE** new comments
- ✅ **Can READ** comments
- ❌ **Cannot UPDATE** comments (read-only after creation)
- ❌ **Cannot DELETE** comments (permanent once created)

This mimics Zendesk's real behavior where comments are immutable audit records.

## Supported Tables

The server supports 18 Zendesk tables:

- activities
- articles
- groups
- group_memberships
- organizations
- requests
- satisfaction_ratings
- sessions
- tags
- targets
- **tickets**
- ticket_audits
- **ticket_comments** (read-only for updates/deletes)
- ticket_fields
- ticket_metrics
- triggers
- **users**
- views

## Documentation

For detailed usage instructions, query syntax, and OData filtering examples, see:

📖 **[USAGE.md](./USAGE.md)** - Comprehensive usage guide with examples

Topics covered:
- Query syntax for article search (phrases, negatives, thresholds)
- OData filtering operators and examples
- CRUD operations and restrictions
- Best practices and error handling

## Project Structure

```
zendesk/
├── src/
│   ├── db/              # Data models and initial data
│   │   ├── models.py    # Pydantic models (Article, Ticket, User, etc.)
│   │   ├── articles.json
│   │   ├── tickets.json
│   │   ├── users.json
│   │   └── ...
│   ├── tools/           # Tool implementations
│   │   ├── get_tables.py
│   │   ├── get_items.py      # OData filtering
│   │   ├── get_item.py
│   │   ├── create_item.py
│   │   ├── update_item.py
│   │   ├── delete_item.py
│   │   └── search_articles.py # Advanced query parsing
│   ├── app.py           # MCP server setup
│   └── main.py          # Entry point
├── tests/
│   ├── tools/           # Tool tests
│   │   ├── test_search_articles.py  # Query syntax tests
│   │   ├── test_get_items.py        # OData filtering tests
│   │   └── ...
│   └── test_tool_schemas.py
├── USAGE.md             # Detailed usage guide
├── README.md            # This file
└── pyproject.toml       # Dependencies
```

## Implementation Details

### Query Parser (search_articles)

The search query parser implements Zendesk's search syntax:

1. **Phrase extraction**: Identifies `"quoted phrases"` and `-"negative phrases"`
2. **Negative term extraction**: Identifies `-term` patterns
3. **Term tokenization**: Splits remaining text into individual terms
4. **Matching logic**:
   - Phrases: ALL must be present (exact, consecutive)
   - Terms (≤2): ALL must be present (AND logic)
   - Terms (>2): ≥40% must be present (ceil(0.4 * count))
   - Negatives: ANY presence excludes the document

### OData Parser (get_items)

The OData filter parser uses the `odata-query` library:

1. **Lexical analysis**: Tokenizes filter expressions
2. **Parsing**: Builds Abstract Syntax Tree (AST)
3. **Evaluation**: Traverses AST and applies comparisons
4. **Type handling**: Correctly handles strings, integers, booleans, enums

## Testing

The test suite includes:

- **Schema validation tests**: Ensure all tools have proper schemas
- **Query parsing tests**: Verify phrase/term/negative extraction
- **Search matching tests**: Verify Zendesk-like matching logic
- **OData filtering tests**: Verify comparison and logical operators
- **CRUD operation tests**: Verify create, read, update, delete
- **Restriction tests**: Verify ticket_comments cannot be modified/deleted

Run tests with:
```bash
uv run pytest -v
```

## Dependencies

Key dependencies:
- `mcp_core` - Shared MCP server infrastructure
- `fastapi` - Web framework
- `pydantic` - Data validation
- `odata-query` - OData v4 parser
- `pytest` - Testing framework

## Contributing

When adding new features:

1. Update data models in `src/db/models.py`
2. Add tool implementation in `src/tools/`
3. Add comprehensive tests in `tests/tools/`
4. Update `USAGE.md` with examples
5. Run full test suite

## License

See repository root for license information.
