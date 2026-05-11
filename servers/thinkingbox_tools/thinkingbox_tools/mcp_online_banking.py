# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import datetime
import traceback
from typing import Annotated, Literal, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from thinkingbox_tools.toolslib.online_banking import (
    Account,
    BankingSystem,
    BankingSystemError,
    Payee,
)

mcp = FastMCP("online_banking")
db = BankingSystem()


class SuccessResponse(BaseModel):
    status: Literal["ok"] = "ok"
    model_config = ConfigDict(extra="allow")


# Response helpers
def error_response(exc) -> str:
    if isinstance(exc, BankingSystemError):
        return "Error!\n" + str(exc)
    traceback.print_exc()
    return "Error!"


@mcp.tool(name="__reserved__init")
async def initialize(config: dict):
    db.accounts = {
        item["account_number"]: Account(**item) for item in config["accounts"]
    }
    db.payees = {item["account_number"]: Payee(**item) for item in config["payees"]}

    return SuccessResponse()


@mcp.tool(name="__reserved__geteffects")
async def geteffects() -> dict:
    obj = {
        "transactions": db.transactions,
        "scheduled_bills": db.scheduled_bills,
        "accounts": db.accounts,
        "payees": db.payees,
    }
    return obj


@mcp.tool(name="get_accounts", description="Retrieve all accounts with balances")
async def get_accounts():
    try:
        accts = db.get_accounts()
        return SuccessResponse(accounts=accts)
    except Exception as e:
        return error_response(e)


@mcp.tool(name="get_balance", description="Retrieve the balance of a specific account")
async def get_balance(
    account_number: Annotated[str, Field(description="The account number to query")],
):
    try:
        bal = db.get_balance(account_number)
        return SuccessResponse(account_number=account_number, balance=bal)
    except Exception as e:
        return error_response(e)


@mcp.tool(name="transfer", description="Transfer funds from one account to another")
async def transfer(
    from_account: Annotated[str, Field(description="Sender account number")],
    to_account: Annotated[str, Field(description="Recipient account number")],
    amount: Annotated[float, Field(description="Amount to transfer")],
):
    try:
        db.transfer(from_account, to_account, amount)
        return SuccessResponse(
            from_account=from_account, to_account=to_account, amount=amount
        )
    except Exception as e:
        return error_response(e)


# Tool: deposit to account
@mcp.tool(
    name="deposit", description="deposit amount to account and return the balance"
)
async def deposit(
    account_number: Annotated[str, Field(description="Deposit account number")],
    amount: Annotated[float, Field(description="Amount to Deposit")],
):
    try:
        bal = db.deposit(account_number, amount)
        return SuccessResponse(account_number=account_number, balance=bal)
    except Exception as e:
        return error_response(e)


# Tool: list all payees
@mcp.tool(name="get_payees", description="List all configured payees")
async def get_payees():
    try:
        payees = db.get_payees()
        return SuccessResponse(payees=payees)
    except Exception as e:
        return error_response(e)


# Tool: schedule a bill payment, defaulting date to now if not provided
@mcp.tool(
    name="pay_bill",
    description="Schedule a bill payment on a specific date (defaults to now)",
)
async def pay_bill(
    user_account: Annotated[str, Field(description="User's account number")],
    payee_account: Annotated[str, Field(description="Payee account number")],
    amount: Annotated[float, Field(description="Amount to pay")],
    date: Annotated[
        Optional[datetime.datetime],
        Field(description="Payment date (ISO 8601), defaults to now"),
    ] = None,
):
    try:
        # Default date to now UTC
        if date is None:
            date = datetime.datetime.now(datetime.timezone.utc)
        sb = db.schedule_bill(user_account, payee_account, amount, date)
        return SuccessResponse(scheduled_bill=sb)
    except Exception as e:
        return error_response(e)


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
