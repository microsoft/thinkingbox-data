# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import copy
import datetime

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from thinkingbox_tools.mcp_online_banking import mcp

SERVER_CONFIG = {
    "accounts": [
        {
            "account_type": "checking",
            "account_number": "599521725",
            "balance": 1000.00,
        },
        {
            "account_type": "savings",
            "account_number": "843847393",
            "balance": 5000.00,
        },
        {
            "account_type": "investment",
            "account_number": "691240002",
            "balance": 15000.00,
        },
    ],
    "payees": [
        {"name": "Electric Company", "account_number": "PAY1001"},
        {"name": "Internet Provider", "account_number": "PAY1002"},
        {"name": "Water Company", "account_number": "PAY1003"},
        {"name": "Mortgage Lender", "account_number": "PAY1004"},
    ],
}


@pytest.mark.asyncio
async def test_initialize():
    async with Client(mcp) as client:
        response = await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})
        assert response.structured_content["status"] == "ok"


@pytest.mark.asyncio
async def test_get_accounts_with_balances():
    async with Client(mcp) as client:
        await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})
        response = await client.call_tool("get_accounts", {})
        assert response.structured_content["status"] == "ok"
        accounts = response.structured_content["accounts"]
        checking = next(a for a in accounts if a["account_number"] == "599521725")
        assert checking["balance"] == 1000.00


@pytest.mark.asyncio
async def test_get_balance():
    async with Client(mcp) as client:
        await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})
        response = await client.call_tool(
            "get_balance", {"account_number": "599521725"}
        )
        assert response.structured_content["status"] == "ok"
        assert response.structured_content["balance"] == 1000.00
        assert response.structured_content["account_number"] == "599521725"


@pytest.mark.asyncio
async def test_get_balance_invalid_account():
    async with Client(mcp) as client:
        await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})
        response = await client.call_tool(
            "get_balance", {"account_number": "999999999"}
        )
        assert "Error!" in response.content[0].text


@pytest.mark.asyncio
async def test_transfer():
    async with Client(mcp) as client:
        await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})
        response = await client.call_tool(
            "transfer",
            {"from_account": "599521725", "to_account": "843847393", "amount": 100.00},
        )
        assert response.structured_content["status"] == "ok"
        assert response.structured_content["amount"] == 100.00

        # Verify balances changed
        from_balance = await client.call_tool(
            "get_balance", {"account_number": "599521725"}
        )
        to_balance = await client.call_tool(
            "get_balance", {"account_number": "843847393"}
        )
        assert from_balance.structured_content["balance"] == 900.00
        assert to_balance.structured_content["balance"] == 5100.00


@pytest.mark.asyncio
async def test_transfer_insufficient_funds():
    async with Client(mcp) as client:
        await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})
        response = await client.call_tool(
            "transfer",
            {
                "from_account": "599521725",
                "to_account": "843847393",
                "amount": 10000.00,
            },
        )
        assert "Error!" in response.content[0].text


@pytest.mark.asyncio
async def test_deposit():
    async with Client(mcp) as client:
        await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})
        response = await client.call_tool(
            "deposit", {"account_number": "599521725", "amount": 500.00}
        )
        assert response.structured_content["status"] == "ok"
        assert response.structured_content["balance"] == 1500.00
        assert response.structured_content["account_number"] == "599521725"


@pytest.mark.asyncio
async def test_deposit_large_amount():
    async with Client(mcp) as client:
        await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})
        response = await client.call_tool(
            "deposit", {"account_number": "691240002", "amount": 50000.00}
        )
        assert response.structured_content["status"] == "ok"
        assert response.structured_content["balance"] == 65000.00


@pytest.mark.asyncio
async def test_get_payees():
    async with Client(mcp) as client:
        await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})
        response = await client.call_tool("get_payees", {})
        assert response.structured_content["status"] == "ok"
        assert "payees" in response.structured_content
        assert len(response.structured_content["payees"]) == 4


@pytest.mark.asyncio
async def test_get_payees_verify_data():
    async with Client(mcp) as client:
        await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})
        response = await client.call_tool("get_payees", {})
        assert response.structured_content["status"] == "ok"
        payees = response.structured_content["payees"]
        electric = next(p for p in payees if p["account_number"] == "PAY1001")
        assert electric["name"] == "Electric Company"


@pytest.mark.asyncio
async def test_pay_bill_with_date():
    async with Client(mcp) as client:
        await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})
        payment_date = datetime.datetime(
            2025, 11, 1, 12, 0, 0, tzinfo=datetime.timezone.utc
        )
        response = await client.call_tool(
            "pay_bill",
            {
                "user_account": "599521725",
                "payee_account": "PAY1001",
                "amount": 150.00,
                "date": payment_date.isoformat(),
            },
        )
        assert response.structured_content["status"] == "ok"
        assert "scheduled_bill" in response.structured_content
        bill = response.structured_content["scheduled_bill"]
        assert bill["amount"] == 150.00


@pytest.mark.asyncio
async def test_pay_bill_default_date():
    async with Client(mcp) as client:
        await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})
        response = await client.call_tool(
            "pay_bill",
            {
                "user_account": "599521725",
                "payee_account": "PAY1002",
                "amount": 75.50,
            },
        )
        assert response.structured_content["status"] == "ok"
        assert "scheduled_bill" in response.structured_content
        bill = response.structured_content["scheduled_bill"]
        assert bill["amount"] == 75.50
        assert bill["payee_account"] == "PAY1002"


@pytest.mark.asyncio
async def test_initialize_with_integer_account_numbers():
    """Test that account numbers provided as integers are handled correctly"""
    config = {
        "accounts": [
            {
                "account_type": "checking",
                "account_number": "599521725",
                "balance": 1000.00,
            },
        ],
        "payees": [
            {"name": "Electric Company", "account_number": "1001"},
        ],
    }
    config_int_account = copy.deepcopy(config)
    config_int_account["accounts"][0]["account_number"] = 599521725
    config_int_payee = copy.deepcopy(config)
    config_int_payee["payees"][0]["account_number"] = 1001

    # account's account_number must be a string
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            _ = await client.call_tool(
                "__reserved__init", {"config": config_int_account}
            )

    # payee's account_number must be a string
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            _ = await client.call_tool("__reserved__init", {"config": config_int_payee})


@pytest.mark.asyncio
async def test_geteffects():
    async with Client(mcp) as client:
        await client.call_tool("__reserved__init", {"config": SERVER_CONFIG})

        # Perform some operations
        await client.call_tool(
            "deposit", {"account_number": "599521725", "amount": 200.00}
        )
        await client.call_tool(
            "transfer",
            {"from_account": "599521725", "to_account": "843847393", "amount": 50.00},
        )
        await client.call_tool(
            "pay_bill",
            {
                "user_account": "599521725",
                "payee_account": "PAY1001",
                "amount": 100.00,
            },
        )

        # Get effects
        response = await client.call_tool("__reserved__geteffects", {})
        assert "transactions" in response.structured_content
        assert "scheduled_bills" in response.structured_content
        assert "accounts" in response.structured_content
        assert "payees" in response.structured_content

        # Verify we have transactions
        assert len(response.structured_content["transactions"]) > 0
        assert len(response.structured_content["scheduled_bills"]) > 0
