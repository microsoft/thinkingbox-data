# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.crm_api.models import CustomerProfile
from tb_business_ops_servers_202606.toolslib.external_booking.crm_api.tools.update_customer_info import (
    CrmApiUpdateCustomerInfoTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def tool():
    return CrmApiUpdateCustomerInfoTool()


@pytest.fixture
def db():
    """Load CRM initial data correctly from the external_booking path."""
    base_dir = pathlib.Path(__file__).parents[3]
    data_dir = (
        base_dir
        / "tb_business_ops_servers_202606"
        / "toolslib"
        / "external_booking"
        / "crm_api"
        / "initial_data"
    )

    return InMemoryDatabase(
        domain=STUB_DOMAIN,
        additional_sources={
            "crm_api": (
                str(data_dir),
                "tb_business_ops_servers_202606.toolslib.external_booking.crm_api.models",
            )
        },
    )


def _get_customer(db, customer_id: str) -> CustomerProfile:
    profiles = db.get_all(CustomerProfile)
    return next(p for p in profiles if p.customer_id == customer_id)


@pytest.mark.anyio
async def test_update_customer_info_success(tool, db):
    request = {
        "customer_id": "CUS-00000001",
        "preferences": ["quiet room", "high floor"],
        "complaint_count": 4,
    }

    result = await tool.run_with_validation(db, request)

    assert result["success"] is True
    assert set(result["updated_fields"]) == {"preferences", "complaint_count"}

    customer = _get_customer(db, "CUS-00000001")
    assert customer.preferences == ["quiet room", "high floor"]
    assert customer.complaint_count == 4


@pytest.mark.anyio
async def test_update_customer_info_append_notes(tool, db):
    request = {
        "customer_id": "CUS-00000002",
        "special_notes": ["call before check-in"],
    }

    result = await tool.run_with_validation(db, request)

    assert result["success"] is True
    assert result["updated_fields"] == ["special_notes"]

    customer = _get_customer(db, "CUS-00000002")
    assert customer.special_notes == ["call before check-in"]


@pytest.mark.anyio
async def test_update_customer_info_not_found(tool, db):
    with pytest.raises(tool.ExecutionError, match="Customer not found"):
        await tool.run_with_validation(
            db,
            {
                "customer_id": "CUS-NOPE",
                "preferences": ["test"],
            },
        )


@pytest.mark.anyio
async def test_update_customer_info_invalid_param(tool, db):
    with pytest.raises(tool.ExecutionError, match="Invalid parameters|Invalid.*update"):
        await tool.run_with_validation(
            db,
            {
                "customer_id": "CUS-00000001",
            },
        )


@pytest.mark.anyio
async def test_update_customer_info_disallowed_field(tool, db):
    # Now Pydantic validates and rejects disallowed fields before reaching business logic
    with pytest.raises(tool.ExecutionError, match=r"Extra inputs are not permitted"):
        await tool.run_with_validation(
            db,
            {
                "customer_id": "CUS-00000001",
                "vip_tier": "platinum",
            },
        )
