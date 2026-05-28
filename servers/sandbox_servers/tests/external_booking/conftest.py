# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Shared fixtures for all external_booking tests."""

from pathlib import Path

import pytest
from sandbox_servers.toolslib.external_booking.booking_api.models import (
    Booking,
    GroupBooking,
    HotelInventory,
)
from sandbox_servers.toolslib.external_booking.corporate_api.models import (
    CorporateAccount,
)
from sandbox_servers.toolslib.external_booking.crm_api.models import CustomerProfile
from sandbox_servers.toolslib.external_booking.hotel_partner_api.models import Hotel
from sandbox_servers.toolslib.external_booking.payment_api.models import Transaction
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db():
    """
    Create a shared database with data from all SOR sources.
    This fixture loads data from the correct System of Record for each table.
    """
    base_path = (
        Path(__file__).parent.parent.parent
        / "sandbox_servers"
        / "toolslib"
        / "external_booking"
    )

    # Create database with additional_sources pointing to all SOR locations
    db = InMemoryDatabase(
        domain=STUB_DOMAIN,
        data_dir=None,
        additional_sources={
            "booking_api": (
                str(base_path / "booking_api" / "initial_data"),
                "sandbox_servers.toolslib.external_booking.booking_api.models",
            ),
            "hotel_partner_api": (
                str(base_path / "hotel_partner_api" / "initial_data"),
                "sandbox_servers.toolslib.external_booking.hotel_partner_api.models",
            ),
            "payment_api": (
                str(base_path / "payment_api" / "initial_data"),
                "sandbox_servers.toolslib.external_booking.payment_api.models",
            ),
            "corporate_api": (
                str(base_path / "corporate_api" / "initial_data"),
                "sandbox_servers.toolslib.external_booking.corporate_api.models",
            ),
            "crm_api": (
                str(base_path / "crm_api" / "initial_data"),
                "sandbox_servers.toolslib.external_booking.crm_api.models",
            ),
            "zendesk": (
                str(base_path / "zendesk" / "initial_data"),
                "sandbox_servers.toolslib.external_booking.zendesk.models",
            ),
        },
    )

    return db
