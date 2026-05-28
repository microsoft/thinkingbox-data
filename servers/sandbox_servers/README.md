# Sandbox Servers

This package contains MCP servers for ThinkingBox sandbox environments, including the External Retail integration.

## Structure

```
servers/sandbox_servers/
├── pyproject.toml          # Package configuration
├── README.md              # This file
└── sandbox_servers/       # Python package
    ├── __init__.py
    ├── mcp_sandbox_external_retail.py  # Main MCP server
    ├── sandbox_tools_system.py         # Core sandbox system
    ├── db_utils.py                     # Database utilities
    ├── external_retail_toolset/        # External retail tools
    │   ├── oms/                        # Order Management System
    │   ├── stripe/                     # Payment processing
    │   ├── extend/                     # Warranty management
    │   ├── jobber/                     # Installation scheduling
    │   ├── loop_returns/               # Returns management
    │   ├── netsuite/                   # Inventory management
    │   ├── promo/                      # Promotions
    │   ├── salesforce/                 # Customer profiles
    │   ├── shopify_pim/                # Product information
    │   └── knowledge_base/             # Policy search
    └── zendesk/                        # Zendesk integration
```

## Installation

From the `servers/sandbox_servers` directory:

```bash
pip install -e .
```

Or using uv:

```bash
uv pip install -e .
```

## Usage

### Running the MCP Server

```bash
python -m sandbox_servers.mcp_sandbox_external_retail
```

### Running via ThinkingBox

The server is configured in `servers.yaml` and can be started via ThinkingBox:

```bash
uv run tb mcp-start --servers servers.yaml
```

## Features

The External Retail Sandbox provides:

- **35+ tools** for customer service scenarios
- **In-memory database** with transaction support
- **Multiple integration systems**: OMS, Stripe, Extend, Jobber, Loop Returns, NetSuite, Promotions, Salesforce, Shopify PIM, Knowledge Base, Zendesk
- **Golden test case support** for automated validation
- **Database state tracking** and diff calculation

## Unstable Fields

Fields that should be excluded from hash-based grading comparisons (e.g. timestamps, AI-generated text,
user-provided free-form content) can be marked as **unstable**. Two mechanisms are provided:

### UnstableField — per-field annotation

Use `UnstableField()` as a Pydantic field metadata annotation to mark individual fields:

```python
from typing import Annotated
from pydantic import BaseModel, Field
from sandbox_servers import UnstableField

class MyModel(BaseModel):
    id: str = Field(...)
    name: str = Field(...)
    created_at: Annotated[str, UnstableField()] = Field(...)  # excluded from hash
```

### UnstableExtraFields — model-level marker for dynamic fields

For models with `extra="allow"` (e.g. items with arbitrary columns), all extra
(non-schema) fields are treated as unstable when the class variable `unstable_extra_fields` is set:

```python
from typing import ClassVar
from pydantic import BaseModel, ConfigDict, Field

class DynamicItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    unstable_extra_fields: ClassVar[bool] = True

    id: str = Field(...)        # schema field — included in hash
    name: str = Field(...)      # schema field — included in hash
    # Any extra field set at runtime (Status, Priority, etc.) is excluded from hash
```

Both mechanisms are applied automatically by `get_stable_database_state()` and
`calculate_database_hash()` when `exclude_unstable_fields=True` (the default).

## Development

### Testing imports

```bash
cd servers/sandbox_servers
python3 -c "from sandbox_servers import SandboxToolsSystem; print('OK')"
```

### Running tests

```bash
cd servers/sandbox_servers
pytest
```
