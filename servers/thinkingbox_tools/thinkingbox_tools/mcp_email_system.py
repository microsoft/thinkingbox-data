# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import traceback
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from pydantic_core import to_jsonable_python

from thinkingbox_tools.toolslib.email_system import (
    EmailSystem,
    EmailSystemError,
    MessageCreate,
)

mcp = FastMCP("email_system")
db = EmailSystem()


class SuccessResponse(BaseModel):
    status: Literal["ok"]


def success_response(**kwargs) -> str:
    obj = {
        "status": "ok",
        **to_jsonable_python(kwargs),
    }
    return json.dumps(obj)


# Response helpers
def error_response(exc) -> str:
    if isinstance(exc, EmailSystemError):
        return "Error!\n" + str(exc)
    traceback.print_exc()
    return "Error!"


@mcp.tool(name="__reserved__init")
async def initialize(config: dict):
    db.initialize(config)
    result = list(db._state.keys())
    return json.dumps({"status": "ok", "result": result})


@mcp.tool(name="__reserved__geteffects")
async def geteffects():
    obj = {"effects": db.effects}
    return json.dumps(to_jsonable_python(obj))


@mcp.tool(
    name="list_emails",
    description="View the content of emails present in a folder (defaults to Inbox).",
)
async def list_messages(
    folder: Annotated[
        str, Field(description="Folder name to list emails from")
    ] = "Inbox",
) -> str:
    try:
        emails = db.list_messages(folder)
        return success_response(emails=emails)
    except Exception as e:
        return error_response(e)


@mcp.tool(name="send_email", description="Send an email to a recipient.")
async def send_email(
    to: Annotated[str, Field(description="Recipient email address")],
    cc: Annotated[str, Field(description="CC email address")],
    subject: Annotated[str, Field(description="Subject of the email")],
    body: Annotated[str, Field(description="Body of the email")],
    attachments: Annotated[dict, Field(description="Attachments")] = {},
) -> str:
    try:
        payload = MessageCreate(
            to=to,
            cc=cc,
            subject=subject,
            body=body,
            attachments=attachments,
        )
        db.send_message(payload)

        return success_response(
            email=payload.model_dump(exclude_none=True, by_alias=True)
        )
    except Exception as e:
        return error_response(e)


@mcp.tool(name="delete_email", description="Delete an email from a folder.")
async def delete_email(
    email_id: Annotated[str, Field(description="Email ID to delete")],
    folder: Annotated[
        str, Field(description="Folder name to delete the email from")
    ] = "Inbox",
) -> str:
    try:
        db.delete_message(email_id, folder)
        return success_response(email_id=email_id, folder=folder)
    except Exception as e:
        return error_response(e)


@mcp.tool(name="add_contact", description="Add a new contact to the address book")
async def add_contact(
    name: Annotated[str, Field(description="Name of the contact")],
    email: Annotated[str, Field(description="Email address of the contact")],
    phone: Annotated[str, Field(description="Phone number of the contact")] = None,
    manager: Annotated[str, Field(description="Contact ID of the manager")] = None,
    position: Annotated[str, Field(description="Job position of the contact")] = None,
) -> str:
    try:
        contact_id = db.add_contact(
            name=name, email=email, phone=phone, manager=manager, position=position
        )
        return success_response(contact_id=contact_id)
    except Exception as e:
        return error_response(e)


@mcp.tool(name="list_contacts", description="List all contacts in the address book")
async def list_contacts() -> str:
    try:
        contacts = db.list_contacts()
        return success_response(contacts=contacts)
    except Exception as e:
        return error_response(e)


@mcp.tool(name="get_contact", description="Get details of a specific contact by ID")
async def get_contact(
    contact_id: Annotated[str, Field(description="ID of the contact to retrieve")],
) -> str:
    try:
        contact = db.get_contact(contact_id)
        return success_response(contact=contact)
    except Exception as e:
        return error_response(e)


@mcp.tool(
    name="get_user_profile", description="Get the current user's profile information"
)
async def get_user_profile() -> str:
    try:
        profile = db.get_user_profile()
        return success_response(profile=profile)
    except Exception as e:
        return error_response(e)


@mcp.tool(name="get_user_manager", description="Get the current user's manager contact")
async def get_user_manager() -> str:
    try:
        manager = db.get_user_manager()
        return success_response(manager=manager)
    except Exception as e:
        return error_response(e)


@mcp.tool(
    name="get_manager_of_manager",
    description="Get the manager of the current user's manager",
)
async def get_manager_of_manager() -> str:
    try:
        manager_of_manager = db.get_manager_of_manager()
        return success_response(manager_of_manager=manager_of_manager)
    except Exception as e:
        return error_response(e)


if __name__ == "__main__":
    mcp.run(transport="stdio")
