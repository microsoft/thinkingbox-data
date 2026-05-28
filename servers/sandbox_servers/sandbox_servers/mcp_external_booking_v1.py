# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""MCP Server for External Booking V1 sandbox with integrated tools."""

import json
import logging

from fastmcp import FastMCP
from sandbox_servers import SandboxToolsSystem, ToolSet
from sandbox_servers.utils.db_utils import (
    apply_golden_set_to_database,
    calculate_database_hash,
    calculate_deep_diff,
    get_stable_database_state,
)
from sandbox_servers.utils.sandbox_tools_system import (
    get_typesense,
    initialize_typesense,
    make_function_tool,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

mcp = FastMCP("external_booking_v1")

# Global state
sandbox_system: SandboxToolsSystem | None = None
initial_db_state = None
current_data_patch = None
current_golden_test_case = None
rubrics = None
rubrics_yesno = None


def _create_toolsets() -> list[ToolSet]:
    """Create the list of toolsets for this domain."""
    return [
        ToolSet(
            path="sandbox_servers.toolslib.external_booking.zendesk",
            namespace="zendesk",
            db_namespace="zendesk",
        ),
        ToolSet(
            path="sandbox_servers.toolslib.external_booking.booking_api",
            namespace="booking_api",
            db_namespace="booking_api",
        ),
        ToolSet(
            path="sandbox_servers.toolslib.external_booking.corporate_api",
            namespace="corporate_api",
            db_namespace="corporate_api",
        ),
        ToolSet(
            path="sandbox_servers.toolslib.external_booking.crm_api",
            namespace="crm_api",
            db_namespace="crm_api",
        ),
        ToolSet(
            path="sandbox_servers.toolslib.external_booking.hotel_partner_api",
            namespace="hotel_partner_api",
            db_namespace="hotel_partner_api",
        ),
        ToolSet(
            path="sandbox_servers.toolslib.external_booking.payment_api",
            namespace="payment_api",
            db_namespace="payment_api",
        ),
        ToolSet(
            path="sandbox_servers.toolslib.connectors.typesense",
            namespace="knowledge_base",
            db_namespace="knowledge_base",
        ),
        ToolSet(
            path="sandbox_servers.toolslib.external_booking.lookup",
            namespace="lookup",
            db_namespace="lookup",
        ),
    ]


def initialize_sandbox_system():
    """Initialize the SandboxToolsSystem with all toolsets."""
    global sandbox_system

    if sandbox_system is not None:
        return sandbox_system

    # Configure toolsets
    toolsets = _create_toolsets()

    logger.info("Initializing SandboxToolsSystem...")
    sandbox_system = SandboxToolsSystem(toolsets=toolsets)
    logger.info(
        f"SandboxToolsSystem initialized with {len(sandbox_system._tool_map)} tools"
    )

    # Log available table names for debugging
    if sandbox_system.db:
        table_names = list(sandbox_system.db._model_cls_to_stem.values())
        logger.info(f"Available tables: {table_names}")

    return sandbox_system


@mcp.tool(name="__reserved__init")
async def initialize(config: dict):
    """
    Initialize sandbox with optional data patch and golden test case.

    Args:
        config: Dictionary containing:
            - data_patch: Optional data to add to database
            - golden_test_case: Optional golden test case for validation
            - rubrics: Optional rubrics for evaluation
            - rubrics_yesno: Optional yes/no rubrics for evaluation

    Returns:
        JSON with initialization status and database state
    """
    global initial_db_state, current_data_patch, current_golden_test_case, rubrics, rubrics_yesno

    logger.info("=== __reserved__init called ===")
    logger.info(f"Config keys: {list(config.keys())}")
    logger.info(f"Config type: {type(config)}")

    data_patch = config.get("data_patch") or {}
    golden_test_case = config.get("golden_test_case") or {}
    rubrics = config.get("rubrics") or {}
    rubrics_yesno = config.get("rubrics_yesno") or []
    sources = config.get("sources") or []

    # Store globally for __reserved__geteffects
    current_data_patch = data_patch
    current_golden_test_case = golden_test_case

    logger.info(f"Data patch present: {bool(data_patch)}, tables: {len(data_patch)}")
    logger.info(f"Golden test case present: {bool(golden_test_case)}")
    logger.info(f"Rubrics present: {bool(rubrics)}")
    logger.info(
        f"Rubrics yesno present: {bool(rubrics_yesno)}, count: {len(rubrics_yesno)}"
    )
    logger.info(f"Sources present: {bool(sources)}, count: {len(sources)}")

    try:
        # Initialize Typesense with sources if provided
        if sources:
            logger.info(f"Initializing Typesense with {len(sources)} sources...")
            initialize_typesense(sources)
            logger.info("Typesense initialization completed")

        # Initialize the sandbox system
        system = initialize_sandbox_system()

        # Log available table names before applying patch
        if system.db:
            table_names = list(system.db._model_cls_to_stem.values())
            # Show first 10 tables
            logger.info(f"Available tables ({len(table_names)}): {table_names[:10]}...")

        # Apply data patch if provided
        if data_patch:
            logger.info(f"Applying data patch with {len(data_patch)} tables...")
            patch_tables = list(data_patch.keys())
            logger.info(f"Data patch tables: {patch_tables}")

            # Check which tables will match
            if system.db:
                available_tables = list(system.db._model_cls_to_stem.values())
                logger.info(f"Available tables in DB: {available_tables}")

                # Find matches
                matched = [t for t in patch_tables if t in available_tables]
                unmatched = [t for t in patch_tables if t not in available_tables]
                logger.info(f"Matched tables: {matched}")
                if unmatched:
                    logger.warning(f"Unmatched tables in patch: {unmatched}")

            try:
                # Log sample data from patch
                for table_name, items in list(data_patch.items())[:3]:
                    logger.info(f"  Table '{table_name}': {len(items)} items")
                    if items and len(items) > 0:
                        first_item = items[0]
                        item_keys = (
                            list(first_item.keys())
                            if isinstance(first_item, dict)
                            else "N/A"
                        )
                        logger.info(f"    First item keys: {item_keys}")

                system.apply_data_patch(data_patch)
                logger.info("Data patch applied successfully")
            except Exception as e:
                logger.error(f"Failed to apply data patch: {e}", exc_info=True)
                raise

        # Store initial database state
        initial_db_state = system.get_database_state()
        logger.info(f"Initial DB state captured with {len(initial_db_state)} tables")

        # Return empty response (DB state is stored globally, not returned)
        logger.info("=== __reserved__init completed successfully ===")
        patch_table_count = len(data_patch)
        db_table_count = len(initial_db_state)
        logger.info(
            f"DEBUG: data_patch_tables={patch_table_count}, db_tables={db_table_count}"
        )
        sample_tables = list(initial_db_state.keys())[:5] if initial_db_state else []
        logger.info(f"DEBUG: sample_tables={sample_tables}")

        # Return empty dict (expected by is_init_ok_response)
        return json.dumps({})

    except Exception as e:
        import traceback

        tb_str = traceback.format_exc()
        logger.error(f"Initialization failed: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": str(e), "traceback": tb_str})


@mcp.tool(name="__reserved__geteffects")
async def geteffects():
    """
    Get effects of the test execution.

    Returns:
        - initial_db_state: DB state after init (before test execution)
        - result_db_state: DB state after test execution
        - result_db_hash: Hash of result DB
        - golden_db_state: Expected DB state (after applying golden test case)
        - golden_db_hash: Hash of golden DB
        - diff: List of differences between result and golden
    """
    logger.info("=== __reserved__geteffects called ===")

    try:
        # Get current database state (result after test execution)
        current_system = initialize_sandbox_system()
        result_db = current_system.db
        if result_db is None:
            raise Exception("Current system database is not initialized")
        result_db_state = result_db.to_state_dict()
        result_db_hash = calculate_database_hash(result_db)

        logger.info(f"Result DB hash: {result_db_hash}")

        # Calculate golden database from scratch
        logger.info("Calculating golden DB from initial state + golden test case")

        # Create fresh sandbox system for golden state
        golden_system = SandboxToolsSystem(toolsets=_create_toolsets())

        # Apply data patch to golden system (same as was applied to result system initially)
        if current_data_patch:
            patch_count = len(current_data_patch)
            logger.info(
                f"Applying data patch to golden system with {patch_count} tables"
            )
            golden_system.apply_data_patch(current_data_patch)

        # Apply golden test case to golden system
        if current_golden_test_case:
            logger.info("Applying golden test case to golden system")
            golden_db = await apply_golden_set_to_database(
                golden_system, current_golden_test_case
            )
        else:
            golden_db = golden_system.db

        if golden_db is None:
            raise Exception("Golden system database is not initialized")
        golden_db_state = golden_db.to_state_dict()
        golden_db_hash = calculate_database_hash(golden_db)
        logger.info(f"Golden DB hash: {golden_db_hash}")

        # Calculate diff
        diff_items = calculate_deep_diff(
            get_stable_database_state(result_db), get_stable_database_state(golden_db)
        )
        logger.info(f"Diff count: {len(diff_items)}")

        response = {
            "initial_db_state": initial_db_state,
            "result_db_state": result_db_state,
            "result_db_hash": result_db_hash,
            "golden_db_state": golden_db_state,
            "golden_db_hash": golden_db_hash,
            "diff": diff_items,
            "rubrics": rubrics,
            "rubrics_yesno": rubrics_yesno,
        }

        logger.info("=== __reserved__geteffects completed successfully ===")
        return json.dumps(response)

    except Exception as e:
        import traceback

        tb_str = traceback.format_exc()
        logger.error(f"Get effects failed: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": str(e), "traceback": tb_str})


@mcp.tool(name="__reserved__teardown")
async def teardown():
    get_typesense().teardown()
    return json.dumps({"status": "ok"})


# Mount all tools from SandboxToolsSystem dynamically
def register_sandbox_tools():
    """Register all tools from SandboxToolsSystem as MCP tools."""
    system = initialize_sandbox_system()
    tools = system.list_tools()

    logger.info(f"Registering {len(tools)} tools from SandboxToolsSystem...")

    for tool_def in tools:
        tool_name = tool_def["name"]
        tool_description = tool_def["description"]
        tool_input_schema = tool_def["input_schema"]

        # Create a closure to capture the tool name only
        # Use global sandbox_system to ensure state persistence
        def make_tool_func(name: str, schema: dict, desc: str):
            async def tool_func(**arguments) -> str:
                """Dynamic tool function."""
                global sandbox_system
                try:
                    # Use global sandbox_system, not one from closure
                    sys = (
                        sandbox_system
                        if sandbox_system
                        else initialize_sandbox_system()
                    )
                    result = await sys.call_tool(name, arguments)
                    return json.dumps(result)
                except Exception as e:
                    logger.error(f"Tool {name} failed: {e}", exc_info=True)
                    return json.dumps({"error": str(e), "tool": name})

            tool_func.__name__ = name
            tool_func.__doc__ = desc
            return make_function_tool(tool_func, name, desc, schema)

        # Create and register the tool
        function_tool = make_tool_func(tool_name, tool_input_schema, tool_description)
        mcp.add_tool(function_tool)

    logger.info(f"Successfully registered {len(tools)} tools")


# Initialize and register tools on module load
register_sandbox_tools()


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
