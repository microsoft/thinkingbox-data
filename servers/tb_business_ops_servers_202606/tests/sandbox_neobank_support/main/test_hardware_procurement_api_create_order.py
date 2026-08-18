# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for Hardware Procurement - Create Order Tool."""

from datetime import timedelta

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import DeviceType
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.hardware_procurement_api_create_order import (
    FIXED_CURRENT_TIME,
    HardwareProcurementCreateOrderInput,
    HardwareProcurementCreateOrderTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
)


@pytest.mark.anyio
async def test_create_order_laptop_premium(db: InMemoryDatabase):
    """Test creating hardware order for premium laptop (example from spec)."""
    tool = HardwareProcurementCreateOrderTool()
    expected_date = (FIXED_CURRENT_TIME + timedelta(days=10)).isoformat()
    request = HardwareProcurementCreateOrderInput(
        device_type=DeviceType.LAPTOP_PREMIUM,
        device_model="MacBook Pro 14",
        quantity=1,
        expected_delivery_date=expected_date,
        ship_to_location="123 Main St, San Francisco, CA 94102",
        requester_email="marcus.thompson@vdb.com",
        ticket_id="TCK-00012345",
    )

    result = await tool.run(db, request)

    assert result.order_id.startswith("HW-ORDER-")
    assert result.status == "pending"


@pytest.mark.anyio
async def test_create_order_monitor(db: InMemoryDatabase):
    """Test creating hardware order for monitor."""
    tool = HardwareProcurementCreateOrderTool()
    expected_date = (FIXED_CURRENT_TIME + timedelta(days=10)).isoformat()
    request = HardwareProcurementCreateOrderInput(
        device_type=DeviceType.MONITOR,
        device_model="Dell UltraSharp 27",
        quantity=2,
        expected_delivery_date=expected_date,
        ship_to_location="456 Market St, San Francisco, CA 94102",
        requester_email="maria.garcia@vdb.com",
        ticket_id="TCK-00012346",
    )

    result = await tool.run(db, request)

    assert result.order_id.startswith("HW-ORDER-")
    assert result.status == "pending"


@pytest.mark.anyio
async def test_create_order_headset_accessory(db: InMemoryDatabase):
    """Test creating hardware order for headset (accessory with shorter lead time)."""
    tool = HardwareProcurementCreateOrderTool()
    expected_date = (FIXED_CURRENT_TIME + timedelta(days=5)).isoformat()
    request = HardwareProcurementCreateOrderInput(
        device_type=DeviceType.HEADSET,
        device_model="Sony WH-1000XM5",
        quantity=1,
        expected_delivery_date=expected_date,
        ship_to_location="789 Broadway, New York, NY 10003",
        requester_email="chris.johnson@vdb.com",
    )

    result = await tool.run(db, request)

    assert result.order_id.startswith("HW-ORDER-")
    assert result.status == "pending"


@pytest.mark.anyio
async def test_create_order_without_ticket_id(db: InMemoryDatabase):
    """Test creating hardware order without ticket ID."""
    tool = HardwareProcurementCreateOrderTool()
    expected_date = (FIXED_CURRENT_TIME + timedelta(days=5)).isoformat()
    request = HardwareProcurementCreateOrderInput(
        device_type=DeviceType.KEYBOARD,
        device_model="Logitech MX Keys",
        quantity=1,
        expected_delivery_date=expected_date,
        ship_to_location="100 Pine St, Seattle, WA 98101",
        requester_email="emma.wilson@vdb.com",
    )

    result = await tool.run(db, request)

    assert result.order_id.startswith("HW-ORDER-")
    assert result.status == "pending"


@pytest.mark.anyio
async def test_create_order_laptop_standard(db: InMemoryDatabase):
    """Test creating hardware order for standard laptop."""
    tool = HardwareProcurementCreateOrderTool()
    expected_date = (FIXED_CURRENT_TIME + timedelta(days=10)).isoformat()
    request = HardwareProcurementCreateOrderInput(
        device_type=DeviceType.LAPTOP_STANDARD,
        device_model="Dell Latitude 5430",
        quantity=3,
        expected_delivery_date=expected_date,
        ship_to_location="200 Congress Ave, Austin, TX 78701",
        requester_email="sophia.davis@vdb.com",
        ticket_id="TCK-00012347",
    )

    result = await tool.run(db, request)

    assert result.order_id.startswith("HW-ORDER-")
    assert result.status == "pending"


@pytest.mark.anyio
async def test_create_order_docking_station(db: InMemoryDatabase):
    """Test creating hardware order for docking station."""
    tool = HardwareProcurementCreateOrderTool()
    expected_date = (FIXED_CURRENT_TIME + timedelta(days=10)).isoformat()
    request = HardwareProcurementCreateOrderInput(
        device_type=DeviceType.DOCKING_STATION,
        device_model="CalDigit TS4",
        quantity=5,
        expected_delivery_date=expected_date,
        ship_to_location="300 Boylston St, Boston, MA 02116",
        requester_email="robert.anderson@vdb.com",
        ticket_id="TCK-00012348",
    )

    result = await tool.run(db, request)

    assert result.order_id.startswith("HW-ORDER-")
    assert result.status == "pending"


@pytest.mark.anyio
async def test_create_order_mouse_accessory(db: InMemoryDatabase):
    """Test creating hardware order for mouse (accessory)."""
    tool = HardwareProcurementCreateOrderTool()
    expected_date = (FIXED_CURRENT_TIME + timedelta(days=5)).isoformat()
    request = HardwareProcurementCreateOrderInput(
        device_type=DeviceType.MOUSE,
        device_model="Logitech MX Master 3S",
        quantity=2,
        expected_delivery_date=expected_date,
        ship_to_location="400 Park Ave, New York, NY 10022",
        requester_email="alex.taylor@vdb.com",
    )

    result = await tool.run(db, request)

    assert result.order_id.startswith("HW-ORDER-")
    assert result.status == "pending"


@pytest.mark.anyio
async def test_create_order_requester_not_found(db: InMemoryDatabase):
    """Test creating hardware order for non-existent employee."""
    tool = HardwareProcurementCreateOrderTool()
    expected_date = (FIXED_CURRENT_TIME + timedelta(days=10)).isoformat()
    request = HardwareProcurementCreateOrderInput(
        device_type=DeviceType.LAPTOP_PREMIUM,
        device_model="MacBook Pro 14",
        quantity=1,
        expected_delivery_date=expected_date,
        ship_to_location="123 Main St, San Francisco, CA 94102",
        requester_email="nonexistent@vdb.com",
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "Requester not found" in str(exc_info.value)


@pytest.mark.anyio
async def test_create_order_incremental_ids(db: InMemoryDatabase):
    """Test that order IDs increment correctly."""
    tool = HardwareProcurementCreateOrderTool()
    expected_date = (FIXED_CURRENT_TIME + timedelta(days=5)).isoformat()

    # Create first order
    request1 = HardwareProcurementCreateOrderInput(
        device_type=DeviceType.HEADSET,
        device_model="Sony WH-1000XM5",
        quantity=1,
        expected_delivery_date=expected_date,
        ship_to_location="123 Main St, San Francisco, CA 94102",
        requester_email="marcus.thompson@vdb.com",
    )
    result1 = await tool.run(db, request1)

    # Create second order
    request2 = HardwareProcurementCreateOrderInput(
        device_type=DeviceType.MOUSE,
        device_model="Logitech MX Master 3S",
        quantity=1,
        expected_delivery_date=expected_date,
        ship_to_location="456 Market St, San Francisco, CA 94102",
        requester_email="maria.garcia@vdb.com",
    )
    result2 = await tool.run(db, request2)

    # Extract numeric parts and verify increment
    id1_num = int(result1.order_id.split("-")[-1])
    id2_num = int(result2.order_id.split("-")[-1])
    assert id2_num == id1_num + 1


@pytest.mark.anyio
async def test_create_order_validates_device_type(db: InMemoryDatabase):
    """Test that invalid device type is rejected by Pydantic."""
    from pydantic import ValidationError

    expected_date = (FIXED_CURRENT_TIME + timedelta(days=10)).isoformat()

    with pytest.raises(ValidationError):
        HardwareProcurementCreateOrderInput(
            device_type="invalid_device",  # type: ignore
            device_model="Some Model",
            quantity=1,
            expected_delivery_date=expected_date,
            ship_to_location="123 Main St, San Francisco, CA 94102",
            requester_email="marcus.thompson@vdb.com",
        )


@pytest.mark.anyio
async def test_create_order_stores_expected_delivery_date(db: InMemoryDatabase):
    """Test that expected_delivery_date from input is stored as date-only in the database."""
    from datetime import date

    from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
        ProcurementOrder,
    )

    tool = HardwareProcurementCreateOrderTool()
    expected_date_str = "2025-12-28"
    request = HardwareProcurementCreateOrderInput(
        device_type=DeviceType.LAPTOP_PREMIUM,
        device_model="MacBook Pro 14",
        quantity=1,
        expected_delivery_date=expected_date_str,
        ship_to_location="123 Main St, San Francisco, CA 94102",
        requester_email="marcus.thompson@vdb.com",
        ticket_id="TCK-00012345",
    )

    result = await tool.run(db, request)

    # Verify the order was created
    assert result.order_id.startswith("HW-ORDER-")

    # Retrieve the order from database and verify expected_delivery_date was stored
    order = db.get_by_id(ProcurementOrder, result.order_id)
    assert order is not None
    assert order.expected_delivery_date is not None

    # Verify the date matches what was provided (date-only, no time component)
    assert order.expected_delivery_date == date.fromisoformat(expected_date_str)
