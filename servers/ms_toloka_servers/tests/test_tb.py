# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import contextlib
import json

import pytest

TOOLS = ["create_rma", "search_policy"]

SERVER_CONFIG = {
    "sandbox_external_retail": {
        "sources": [
            {
                "name": "Source.md",
                "snippets": ["Content"],
            }
        ]
    }
}


@contextlib.asynccontextmanager
async def get_mcp_proxy_client(
    server_config: dict[str, dict],
    tools: list[str],
    endpoint: str = "http://127.0.0.1:7111",
):
    from thinkingbox.common.mcp_proxy_client import MCPProxyClient

    async with MCPProxyClient.session_context(
        endpoint=endpoint,
        server_config=server_config,
        available_tools=tools,
    ) as mcp:
        yield mcp


@pytest.mark.tb_mcp_start
@pytest.mark.asyncio
async def test_create_rma_enum_field():
    async with get_mcp_proxy_client(SERVER_CONFIG, TOOLS) as session:
        tools = await session.list_tools()
        create_rma_tool = [tool for tool in tools if tool.name == "create_rma"][0]
        rma_prop_return_reason = create_rma_tool.input_schema["properties"][
            "return_reason"
        ]
        assert (
            "enum" in rma_prop_return_reason
        ), "create_rma.properties.return_reason: not an enum"
        assert isinstance(
            rma_prop_return_reason["enum"], list
        ), "create_rma.properties.return_reason: invalid enum"
        assert all(
            isinstance(value, str) for value in rma_prop_return_reason["enum"]
        ), "create_rma.properties.return_reason: not a string enum"


@pytest.mark.tb_mcp_start
@pytest.mark.asyncio
async def test_search_policy():
    async with get_mcp_proxy_client(SERVER_CONFIG, TOOLS) as session:
        response = await session.call_tool("search_policy", query="some query")
        result = json.loads(response)
        assert len(result["snippets"]) == 1
        assert result["snippets"][0]["text"] == "Content"
