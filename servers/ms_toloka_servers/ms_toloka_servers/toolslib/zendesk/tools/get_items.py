# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Get items tool for Zendesk MCP server."""

from typing import Any, Dict, List, Optional, Type

from ms_toloka_servers import InMemoryDatabase, Tool
from odata_query.grammar import ODataLexer, ODataParser
from pydantic import BaseModel, ConfigDict, Field

from ..models import (
    SUPPORTED_CRUD_TABLES,
    Comment,
    Organization,
    TableName,
    Ticket,
    TicketComment,
    User,
)


class GetItemsInput(BaseModel):
    """Input model for get_items tool."""

    table: TableName = Field(
        ...,
        description="Zendesk item type (table name) to query.",
        examples=["tickets", "users", "organizations", "comments", "ticket_comments"],
    )
    filter: Optional[str] = Field(
        None,
        alias="$filter",
        description="OData filter query to restrict returned entries (e.g., 'status eq \"open\"').",
        examples=["status eq 'open'", "priority eq 'high'"],
    )
    orderby: Optional[str] = Field(
        None,
        alias="$orderby",
        description="OData orderBy query specifying entry sort order (e.g., 'created_at desc').",
        examples=["created_at desc", "priority asc"],
    )
    skip: Optional[int] = Field(
        None,
        alias="$skip",
        description="Number of entries to skip, for paging (default = 0).",
        ge=0,
        examples=[0, 10, 25],
    )
    top: Optional[int] = Field(
        None,
        alias="$top",
        description="Maximum number of entries to retrieve (default = 512, max 1000).",
        ge=1,
        le=1000,
        examples=[25, 50, 100],
    )
    select: Optional[str] = Field(
        None,
        alias="$select",
        description="Comma-separated list of specific fields to retrieve from entries (default = all fields).",
        examples=["id,subject,priority", "id,name,email"],
    )

    model_config = ConfigDict(populate_by_name=True)


class GetItemsOutput(BaseModel):
    """Output model for get_items tool."""

    model_config = ConfigDict(extra="forbid")

    items: List[Dict[str, Any]] = Field(
        ..., description="List of items matching the query, fields dynamic per table."
    )


class GetItemsTool(Tool):
    """Tool for retrieving multiple items from Zendesk tables with filtering and paging."""

    @property
    def name(self) -> str:
        return "get_items"

    @property
    def description(self) -> str:
        return (
            "Returns a list of items from a specified Zendesk table, supporting advanced querying via ODATA filters, "
            "sorting, paging, and field selection. This function is essential for displaying lists, supporting search "
            "results, and enabling business analytics. The output is dynamic and matches the fields of the selected table, "
            "returning only the items matching provided criteria."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetItemsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetItemsOutput

    async def run(self, db: InMemoryDatabase, request: GetItemsInput) -> GetItemsOutput:
        """Retrieve multiple items from the specified Zendesk table with filtering and paging."""
        # Check if table is supported for CRUD operations
        if request.table not in SUPPORTED_CRUD_TABLES:
            raise Tool.ExecutionError(
                f"Unsupported table: '{request.table.value}'. Only tickets, users, organizations, comments, and ticket_comments are supported."
            )

        # Map table names to models
        table_map = {
            TableName.TICKETS: Ticket,
            TableName.USERS: User,
            TableName.ORGANIZATIONS: Organization,
            TableName.COMMENTS: Comment,
            TableName.TICKET_COMMENTS: TicketComment,
        }

        model_class = table_map[request.table]

        # Get all items from the table
        all_items = db.get_all(model_class)

        # Apply filtering (simplified - real implementation would parse OData)
        filtered_items = all_items
        if request.filter:
            # Simple filter parsing (for demonstration)
            # In real implementation, use proper OData parser
            filtered_items = self._apply_simple_filter(all_items, request.filter)

        # Apply ordering (simplified)
        if request.orderby:
            filtered_items = self._apply_ordering(filtered_items, request.orderby)

        # Apply paging
        skip = request.skip or 0
        top = request.top or 512
        top = min(top, 1000)  # Max 1000

        paged_items = filtered_items[skip : skip + top]

        # Convert to dicts
        result_items = [item.model_dump() for item in paged_items]

        # Apply field selection
        if request.select:
            fields = [f.strip() for f in request.select.split(",")]
            result_items = [
                {k: v for k, v in item.items() if k in fields} for item in result_items
            ]

        return GetItemsOutput(items=result_items)

    def _apply_simple_filter(self, items: List[Any], filter_expr: str) -> List[Any]:
        """Apply OData filter expression to items."""
        if not filter_expr:
            return items

        try:
            # Parse the OData filter expression
            lexer = ODataLexer()
            parser = ODataParser()
            ast = parser.parse(lexer.tokenize(filter_expr))

            # Filter items based on the parsed expression
            filtered = []
            for item in items:
                if self._evaluate_filter(ast, item):
                    filtered.append(item)

            return filtered
        except Exception as e:
            # If parsing fails, raise an error instead of silently returning all items
            raise Tool.ExecutionError(f"Failed to parse OData filter: {str(e)}")

    def _evaluate_filter(self, ast: Any, item: Any) -> bool:
        """Evaluate a parsed OData filter AST against an item."""
        if ast is None:
            return True

        # Get AST class name for type detection
        ast_type = type(ast).__name__

        # Handle Compare operations (eq, ne, gt, ge, lt, le)
        if ast_type == "Compare":
            comparator_type = type(ast.comparator).__name__
            left = self._get_value(ast.left, item)
            right = self._get_value(ast.right, item)

            if comparator_type == "Eq":
                return left == right
            elif comparator_type == "Ne":
                return left != right
            elif comparator_type == "Gt":
                return left > right
            elif comparator_type == "Ge":
                return left >= right
            elif comparator_type == "Lt":
                return left < right
            elif comparator_type == "Le":
                return left <= right

        # Handle Boolean operations (and, or)
        elif ast_type == "BoolOp":
            operator_type = type(ast.op).__name__

            if operator_type == "And":
                # For 'and' operations, evaluate left and right
                return self._evaluate_filter(ast.left, item) and self._evaluate_filter(
                    ast.right, item
                )
            elif operator_type == "Or":
                # For 'or' operations, evaluate left and right
                return self._evaluate_filter(ast.left, item) or self._evaluate_filter(
                    ast.right, item
                )

        return True

    def _get_value(self, node: Any, item: Any) -> Any:
        """Get value from AST node or item attribute."""
        node_type = type(node).__name__

        # Handle Identifier (field reference)
        if node_type == "Identifier":
            value = getattr(item, node.name, None)
            # Convert enum to string for comparison
            if hasattr(value, "value"):
                return value.value
            return value

        # Handle literal values (String, Integer, Float, Boolean)
        elif node_type == "String":
            return node.val
        elif node_type == "Integer":
            return int(node.val)
        elif node_type == "Float":
            return float(node.val)
        elif node_type == "Boolean":
            return node.val

        # If node is a plain string (attribute name)
        elif isinstance(node, str):
            value = getattr(item, node, None)
            # Convert enum to string for comparison
            if hasattr(value, "value"):
                return value.value
            return value

        # Default
        return node

    def _apply_ordering(self, items: List[Any], orderby: str) -> List[Any]:
        """Apply ordering to items."""
        # Simplified ordering implementation
        # Real implementation would parse orderby properly

        parts = orderby.split()
        if len(parts) >= 1:
            field = parts[0]
            descending = len(parts) > 1 and parts[1].lower() == "desc"

            try:
                return sorted(
                    items, key=lambda x: getattr(x, field, ""), reverse=descending
                )
            except Exception:
                pass

        return items
