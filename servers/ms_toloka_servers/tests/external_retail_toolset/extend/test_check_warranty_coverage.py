# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for check_warranty_coverage tool."""

from datetime import datetime, timedelta

import pytest
from ms_toloka_servers.toolslib.external_retail_toolset.extend.models import (
    WarrantyContract,
    WarrantyType,
)
from ms_toloka_servers.toolslib.external_retail_toolset.extend.tools.check_warranty_coverage import (
    CheckWarrantyCoverageTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestCheckWarrantyCoverage:
    @pytest.fixture
    def test_db(self):
        """Create a test database with warranty contracts."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"warranty_contract": WarrantyContract}
        db._model_cls_to_stem = {WarrantyContract: "warranty_contract"}

        # Create test warranty contracts with dates relative to current time
        current_date = datetime.now()

        # Active manufacturer warranty
        contract1 = WarrantyContract(
            id="WCT-10000001",
            order_id="ORD-10000001",
            sku="SKU-10000001",
            customer_id="CUS-10000001",
            warranty_type=WarrantyType.manufacturer,
            start_date=current_date - timedelta(days=30),
            end_date=current_date + timedelta(days=335),
            coverage_details="Covers defects in materials and workmanship",
        )

        # Active extended warranty
        contract2 = WarrantyContract(
            id="WCT-10000002",
            order_id="ORD-10000002",
            sku="SKU-10000002",
            customer_id="CUS-10000002",
            warranty_type=WarrantyType.extended_warranty,
            start_date=current_date - timedelta(days=100),
            end_date=current_date + timedelta(days=800),
            coverage_details="Extended warranty covering defects in materials and workmanship for 5 years",
        )

        # Active protection plan
        contract3 = WarrantyContract(
            id="WCT-10000003",
            order_id="ORD-10000003",
            sku="SKU-10000003",
            customer_id="CUS-10000003",
            warranty_type=WarrantyType.protection_plan,
            start_date=current_date - timedelta(days=60),
            end_date=current_date + timedelta(days=1035),
            coverage_details="Comprehensive protection plan covering defects, drops, spills, and electrical surges",
        )

        # Expired warranty
        contract4 = WarrantyContract(
            id="WCT-10000004",
            order_id="ORD-10000004",
            sku="SKU-10000004",
            customer_id="CUS-10000001",
            warranty_type=WarrantyType.manufacturer,
            start_date=current_date - timedelta(days=400),
            end_date=current_date - timedelta(days=35),
            coverage_details="Covers defects in materials and workmanship",
        )

        # Future warranty (not yet active)
        contract5 = WarrantyContract(
            id="WCT-10000005",
            order_id="ORD-10000005",
            sku="SKU-10000005",
            customer_id="CUS-10000004",
            warranty_type=WarrantyType.extended_warranty,
            start_date=current_date + timedelta(days=10),
            end_date=current_date + timedelta(days=1105),
            coverage_details="Extended warranty covering defects in materials and workmanship for 3 years",
        )

        db._store = {
            WarrantyContract: [contract1, contract2, contract3, contract4, contract5]
        }
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"warranty_contract": WarrantyContract}
        db._model_cls_to_stem = {WarrantyContract: "warranty_contract"}
        db._store = {WarrantyContract: []}
        return db

    @pytest.fixture
    def check_warranty_coverage_tool(self):
        """Create an instance of CheckWarrantyCoverageTool."""
        return CheckWarrantyCoverageTool()

    @pytest.mark.anyio
    async def test_check_warranty_coverage_active_manufacturer(
        self, check_warranty_coverage_tool, test_db
    ):
        """Test checking active manufacturer warranty."""
        # Arrange
        request_data = {"order_id": "ORD-10000001", "sku": "SKU-10000001"}

        # Act
        result = await check_warranty_coverage_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["has_coverage"] is True
        assert result["contract_id"] == "WCT-10000001"
        assert result["warranty_type"] == "manufacturer"
        assert result["start_date"] is not None
        assert result["end_date"] is not None
        assert (
            result["coverage_details"] == "Covers defects in materials and workmanship"
        )

    @pytest.mark.anyio
    async def test_check_warranty_coverage_active_extended(
        self, check_warranty_coverage_tool, test_db
    ):
        """Test checking active extended warranty."""
        # Arrange
        request_data = {"order_id": "ORD-10000002", "sku": "SKU-10000002"}

        # Act
        result = await check_warranty_coverage_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["has_coverage"] is True
        assert result["contract_id"] == "WCT-10000002"
        assert result["warranty_type"] == "extended_warranty"
        assert "Extended warranty" in result["coverage_details"]

    @pytest.mark.anyio
    async def test_check_warranty_coverage_active_protection_plan(
        self, check_warranty_coverage_tool, test_db
    ):
        """Test checking active protection plan."""
        # Arrange
        request_data = {"order_id": "ORD-10000003", "sku": "SKU-10000003"}

        # Act
        result = await check_warranty_coverage_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["has_coverage"] is True
        assert result["contract_id"] == "WCT-10000003"
        assert result["warranty_type"] == "protection_plan"
        assert "drops, spills" in result["coverage_details"]

    @pytest.mark.anyio
    async def test_check_warranty_coverage_expired(
        self, check_warranty_coverage_tool, test_db
    ):
        """Test checking expired warranty."""
        # Arrange
        request_data = {"order_id": "ORD-10000004", "sku": "SKU-10000004"}

        # Act
        result = await check_warranty_coverage_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["has_coverage"] is False
        assert result.get("contract_id") is None
        assert result.get("warranty_type") is None

    @pytest.mark.anyio
    async def test_check_warranty_coverage_not_yet_active(
        self, check_warranty_coverage_tool, test_db
    ):
        """Test checking warranty that hasn't started yet."""
        # Arrange
        request_data = {"order_id": "ORD-10000005", "sku": "SKU-10000005"}

        # Act
        result = await check_warranty_coverage_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["has_coverage"] is False
        assert result.get("contract_id") is None

    @pytest.mark.anyio
    async def test_check_warranty_coverage_order_not_found(
        self, check_warranty_coverage_tool, test_db
    ):
        """Test checking warranty for non-existent order."""
        # Arrange
        request_data = {"order_id": "ORD-99999999", "sku": "SKU-10000001"}

        # Act
        result = await check_warranty_coverage_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["has_coverage"] is False
        assert result.get("contract_id") is None

    @pytest.mark.anyio
    async def test_check_warranty_coverage_sku_not_found(
        self, check_warranty_coverage_tool, test_db
    ):
        """Test checking warranty for non-existent SKU."""
        # Arrange
        request_data = {"order_id": "ORD-10000001", "sku": "SKU-99999999"}

        # Act
        result = await check_warranty_coverage_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["has_coverage"] is False
        assert result.get("contract_id") is None

    @pytest.mark.anyio
    async def test_check_warranty_coverage_wrong_sku_for_order(
        self, check_warranty_coverage_tool, test_db
    ):
        """Test checking warranty with mismatched order and SKU."""
        # Arrange
        request_data = {"order_id": "ORD-10000001", "sku": "SKU-10000002"}

        # Act
        result = await check_warranty_coverage_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["has_coverage"] is False
        assert result.get("contract_id") is None

    @pytest.mark.anyio
    async def test_check_warranty_coverage_empty_database(
        self, check_warranty_coverage_tool, empty_db
    ):
        """Test checking warranty from empty database."""
        # Arrange
        request_data = {"order_id": "ORD-10000001", "sku": "SKU-10000001"}

        # Act
        result = await check_warranty_coverage_tool.run_with_validation(
            empty_db, request_data
        )

        # Assert
        assert result["has_coverage"] is False
        assert result.get("contract_id") is None
