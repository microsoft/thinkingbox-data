import json

import pytest



TOOLS = [
    "list_emails",
    "send_email",
    "delete_email",
    "add_contact",
    "list_contacts",
    "get_contact",
]
SERVER_CONFIG = {
    "email_system": {
        "users": {
            "alice@example.com": {
                "messages": [
                    {
                        "id": "11111111-aaaa-bbbb-cccc-000000000001",
                        "sender": "bob@example.com",
                        "to": ["alice@example.com"],
                        "cc": [],
                        "subject": "Welcome!",
                        "body": "Hi Alice—just checking your mailbox works",
                        "sent_at": "2025-05-21T12:00:00Z",
                        "folder": "Inbox",
                        "read": False,
                        "attachments": {},
                    }
                ],
                "folders": [
                    {"id": "inbox", "name": "Inbox"},
                    {"id": "sent", "name": "Sent"},
                ],
                "events": [],
                "contacts": [
                    {
                        "id": "manager-1",
                        "name": "Jane Smith",
                        "email": "jane@example.com",
                        "phone": "555-0001",
                        "manager": None,
                        "position": "Engineering Manager",
                    },
                    {
                        "id": "contact-1",
                        "name": "John Doe",
                        "email": "john@example.com",
                        "phone": "555-1234",
                        "manager": "manager-1",
                        "position": "Software Engineer",
                    },
                ],
            }
        }
    }
}


@pytest.mark.asyncio
async def test_list_emails(session_proxy):
    async with session_proxy.get(SERVER_CONFIG, TOOLS) as session:
        session: MCPProxyClient
        response = await session.call_tool("list_emails", folder="Inbox")
        result = json.loads(response)
        assert result["status"] == "ok"
        assert len(result["emails"]) == 1
        assert result["emails"][0]["subject"] == "Welcome!"


@pytest.mark.asyncio
async def test_send_email(session_proxy):
    async with session_proxy.get(SERVER_CONFIG, TOOLS) as session:
        session: MCPProxyClient
        response = await session.call_tool(
            "send_email",
            to="test@example.com",
            cc="",
            subject="Test Subject",
            body="Test Body",
            attachments={},
        )
        result = json.loads(response)
        assert result["status"] == "ok"
        assert result["email"]["subject"] == "Test Subject"


@pytest.mark.asyncio
async def test_add_contact(session_proxy):
    async with session_proxy.get(SERVER_CONFIG, TOOLS) as session:
        session: MCPProxyClient
        response = await session.call_tool(
            "add_contact",
            name="New Contact",
            email="new@example.com",
            phone="555-9999",
            manager="manager-1",  # Reference to existing manager contact
            position="Manager",
        )
        result = json.loads(response)
        assert result["status"] == "ok"
        assert "contact_id" in result


@pytest.mark.asyncio
async def test_list_contacts(session_proxy):
    async with session_proxy.get(SERVER_CONFIG, TOOLS) as session:
        session: MCPProxyClient
        response = await session.call_tool("list_contacts")
        result = json.loads(response)
        assert result["status"] == "ok"
        assert len(result["contacts"]) == 2  # manager + employee

        # Find the employee contact
        employee_contact = None
        for contact in result["contacts"]:
            if contact["id"] == "contact-1":
                employee_contact = contact
                break

        assert employee_contact is not None
        assert employee_contact["name"] == "John Doe"
        assert employee_contact["email"] == "john@example.com"
        assert employee_contact["phone"] == "555-1234"
        assert employee_contact["manager"] == "manager-1"
        assert employee_contact["position"] == "Software Engineer"


@pytest.mark.asyncio
async def test_get_contact(session_proxy):
    async with session_proxy.get(SERVER_CONFIG, TOOLS) as session:
        session: MCPProxyClient
        response = await session.call_tool("get_contact", contact_id="contact-1")
        result = json.loads(response)
        assert result["status"] == "ok"
        contact = result["contact"]
        assert contact["name"] == "John Doe"
        assert contact["email"] == "john@example.com"
        assert contact["phone"] == "555-1234"
        assert contact["manager"] == "manager-1"
        assert contact["position"] == "Software Engineer"


@pytest.mark.asyncio
async def test_get_contact_not_found(session_proxy):
    async with session_proxy.get(SERVER_CONFIG, TOOLS) as session:
        session: MCPProxyClient
        response = await session.call_tool("get_contact", contact_id="nonexistent")
        # Should return an error response
        assert "Error!" in response


@pytest.mark.asyncio
async def test_delete_email(session_proxy):
    async with session_proxy.get(SERVER_CONFIG, TOOLS) as session:
        session: MCPProxyClient
        response = await session.call_tool(
            "delete_email",
            email_id="11111111-aaaa-bbbb-cccc-000000000001",
            folder="Inbox",
        )
        result = json.loads(response)
        assert result["status"] == "ok"
        assert result["email_id"] == "11111111-aaaa-bbbb-cccc-000000000001"
