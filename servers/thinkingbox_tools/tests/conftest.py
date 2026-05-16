# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import contextlib
import importlib
from typing import Any, Generator
import json

import pytest_asyncio
from fastmcp import Client


class MCPProxyClient:
    """Wrapper to mimic MCPProxyClient interface using fastmcp.Client."""

    def __init__(self, name: str, client: Client):
        self._name = name
        self._client = client

    async def call_tool(self, tool_name: str, **kwargs) -> str:
        """Call a tool and return the response as a string."""
        result = await self._client.call_tool(tool_name, kwargs)

        # If result has text attribute, return it (fastmcp response format)
        if hasattr(result, 'text'):
            return result.text
        # If result has content attribute with text items
        elif hasattr(result, 'content') and result.content:
            # Concatenate all text content
            return ''.join(item.text for item in result.content if hasattr(item, 'text'))
        # Otherwise return string representation
        return str(result)

    async def get_effects(self) -> dict[str, str]:
        """Call the reserved geteffects tool to retrieve effects."""
        response = await self.call_tool("__reserved__geteffects")
        json_response = json.loads(response)
        return {self._name: json_response}


class MCPProxyClientFactory:
    def __init__(self):
        pass

    @contextlib.asynccontextmanager
    async def get(
        self,
        server_config: dict[str, dict],
        tools: list[str],
        endpoint: str = "http://127.0.0.1:7111",
    ) -> Generator[MCPProxyClient, Any, None]:
        """
        Create a fastmcp.Client for the specified server without requiring thinkingbox dependency.

        Args:
            server_config: Dict with server name as key and config as value
            tools: List of tool names (not used in this implementation)
            endpoint: Not used in direct client mode
        """
        # Extract server name from config (first key)
        if not server_config:
            raise ValueError("server_config must have at least one key")

        server_name = list(server_config.keys())[0]
        config = server_config[server_name]

        # Dynamically import the MCP server module
        try:
            module = importlib.import_module(f"thinkingbox_tools.mcp_{server_name}")
        except ImportError:
            raise ImportError(
                f"Could not import module 'thinkingbox_tools.mcp_{server_name}'. "
                f"Make sure the server exists."
            )

        # Get the mcp instance from the module
        if hasattr(module, 'mcp') and module.mcp is not None:
            mcp_instance = module.mcp
        elif hasattr(module, 'app') and module.app is not None:
            mcp_instance = module.app
        else:
            raise AttributeError(
                f"Module 'thinkingbox_tools.mcp_{server_name}' does not have an 'mcp' or 'app' attribute"
            )

        # TODO: We need to isolate the server state between tests. This is specific per server and cannot be resolved
        # through plain introspection.
        # See how this is handled in test_slack_server.py for reference
        # we could add some method to expose this to the tool tests so they can pass in the name of the DB parameter
        # and the correct initialization.

        # Create fastmcp client
        async with Client(mcp_instance) as client:
            # Initialize the server with config
            await client.call_tool("__reserved__init", {"config": config})

            # Yield wrapped client
            yield MCPProxyClient(server_name, client)


@pytest_asyncio.fixture(scope="function")
async def session_proxy():
    yield MCPProxyClientFactory()
