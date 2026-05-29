# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Shared fixtures for all sandbox_neobank_support tests."""

from pathlib import Path

import pytest
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db():
    """
    Create a shared database with data from the main SOR source.
    This fixture loads data from the initial_data directory.
    """
    # Path from tests/sandbox_neobank_support/main/ to mcp-tools-library/src/
    base_path = (
        Path(__file__).parent.parent.parent.parent
        / "tb_business_ops_servers_202606"
        / "toolslib"
        / "sandbox_neobank_support"
    )

    # Create database with main data source
    db = InMemoryDatabase(
        domain=STUB_DOMAIN,
        data_dir=None,
        additional_sources={
            "main": (
                str(base_path / "main" / "initial_data"),
                "tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models",
            ),
        },
    )

    return db
