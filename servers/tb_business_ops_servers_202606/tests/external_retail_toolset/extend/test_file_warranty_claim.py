# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for file_warranty_claim tool."""

from datetime import datetime, timedelta

import pytest
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.extend.models import (
    WarrantyClaim,
    WarrantyClaimStatus,
    WarrantyContract,
    WarrantyType,
)
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.extend.tools.file_warranty_claim import (
    FileWarrantyClaimTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestFileWarrantyClaim:
    @pytest.fixture
    def test_db(self):
        """Create a test database with warranty contracts and claims."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "warranty_contract": WarrantyContract,
            "warranty_claim": WarrantyClaim,
        }
        db._model_cls_to_stem = {
            WarrantyContract: "warranty_contract",
            WarrantyClaim: "warranty_claim",
        }

        # Create test warranty contracts
        current_date = datetime.now()

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

        # Create existing warranty claim
        claim1 = WarrantyClaim(
            id="WCL-10000001",
            contract_id="WCT-10000002",
            customer_id="CUS-10000002",
            claim_date=current_date - timedelta(days=10),
            issue_description="Product not functioning properly",
            status=WarrantyClaimStatus.approved,
            resolution="Replacement unit approved and shipped",
        )

        db._store = {
            WarrantyContract: [contract1, contract2, contract3],
            WarrantyClaim: [claim1],
        }
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "warranty_contract": WarrantyContract,
            "warranty_claim": WarrantyClaim,
        }
        db._model_cls_to_stem = {
            WarrantyContract: "warranty_contract",
            WarrantyClaim: "warranty_claim",
        }
        db._store = {WarrantyContract: [], WarrantyClaim: []}
        return db

    @pytest.fixture
    def file_warranty_claim_tool(self):
        """Create an instance of FileWarrantyClaimTool."""
        return FileWarrantyClaimTool()

    @pytest.mark.anyio
    async def test_file_warranty_claim_product_not_functioning(
        self, file_warranty_claim_tool, test_db
    ):
        """Test filing warranty claim for product not functioning."""
        # Arrange
        request_data = {
            "contract_id": "WCT-10000001",
            "customer_id": "CUS-10000001",
            "warranty_issue_type": "product_not_functioning",
        }

        # Act
        result = await file_warranty_claim_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["claim_id"].startswith("WCL-2")
        assert result["status"] == "pending"
        assert result["claim_date"] is not None

        # Verify claim was created in database
        all_claims = test_db.get_all(WarrantyClaim)
        new_claim = None
        for claim in all_claims:
            if claim.id == result["claim_id"]:
                new_claim = claim
                break

        assert new_claim is not None
        assert new_claim.contract_id == "WCT-10000001"
        assert new_claim.customer_id == "CUS-10000001"
        assert new_claim.issue_description == "Product not functioning properly"
        assert new_claim.status == WarrantyClaimStatus.pending
        assert new_claim.resolution is None

    @pytest.mark.anyio
    async def test_file_warranty_claim_component_failed(
        self, file_warranty_claim_tool, test_db
    ):
        """Test filing warranty claim for component failure."""
        # Arrange
        request_data = {
            "contract_id": "WCT-10000002",
            "customer_id": "CUS-10000002",
            "warranty_issue_type": "component_failed",
        }

        # Act
        result = await file_warranty_claim_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["claim_id"].startswith("WCL-2")
        assert result["status"] == "pending"

        # Verify claim was created in database
        all_claims = test_db.get_all(WarrantyClaim)
        new_claim = None
        for claim in all_claims:
            if claim.id == result["claim_id"]:
                new_claim = claim
                break

        assert new_claim is not None
        assert new_claim.issue_description == "Component failed"

    @pytest.mark.anyio
    async def test_file_warranty_claim_performance_degradation(
        self, file_warranty_claim_tool, test_db
    ):
        """Test filing warranty claim for performance degradation."""
        # Arrange
        request_data = {
            "contract_id": "WCT-10000001",
            "customer_id": "CUS-10000001",
            "warranty_issue_type": "performance_degradation",
        }

        # Act
        result = await file_warranty_claim_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["claim_id"].startswith("WCL-2")
        assert result["status"] == "pending"

        # Verify claim was created in database
        all_claims = test_db.get_all(WarrantyClaim)
        new_claim = None
        for claim in all_claims:
            if claim.id == result["claim_id"]:
                new_claim = claim
                break

        assert new_claim is not None
        assert new_claim.issue_description == "Performance degradation"

    @pytest.mark.anyio
    async def test_file_warranty_claim_accidental_damage(
        self, file_warranty_claim_tool, test_db
    ):
        """Test filing warranty claim for accidental damage (protection plan)."""
        # Arrange
        request_data = {
            "contract_id": "WCT-10000003",
            "customer_id": "CUS-10000003",
            "warranty_issue_type": "accidental_damage",
        }

        # Act
        result = await file_warranty_claim_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["claim_id"].startswith("WCL-2")
        assert result["status"] == "pending"

        # Verify claim was created in database
        all_claims = test_db.get_all(WarrantyClaim)
        new_claim = None
        for claim in all_claims:
            if claim.id == result["claim_id"]:
                new_claim = claim
                break

        assert new_claim is not None
        assert new_claim.issue_description == "Accidental damage"

    @pytest.mark.anyio
    async def test_file_warranty_claim_multiple_claims(
        self, file_warranty_claim_tool, test_db
    ):
        """Test filing multiple warranty claims generates unique IDs."""
        # Arrange
        request_data1 = {
            "contract_id": "WCT-10000001",
            "customer_id": "CUS-10000001",
            "warranty_issue_type": "product_not_functioning",
        }

        request_data2 = {
            "contract_id": "WCT-10000002",
            "customer_id": "CUS-10000002",
            "warranty_issue_type": "component_failed",
        }

        # Act
        result1 = await file_warranty_claim_tool.run_with_validation(
            test_db, request_data1
        )
        result2 = await file_warranty_claim_tool.run_with_validation(
            test_db, request_data2
        )

        # Assert
        assert result1["claim_id"] != result2["claim_id"]
        assert result1["status"] == "pending"
        assert result2["status"] == "pending"

        # Verify both claims exist in database
        all_claims = test_db.get_all(WarrantyClaim)
        claim_ids = [claim.id for claim in all_claims]
        assert result1["claim_id"] in claim_ids
        assert result2["claim_id"] in claim_ids

    @pytest.mark.anyio
    async def test_file_warranty_claim_contract_not_found(
        self, file_warranty_claim_tool, test_db
    ):
        """Test error when warranty contract is not found."""
        # Arrange
        request_data = {
            "contract_id": "WCT-99999999",
            "customer_id": "CUS-10000001",
            "warranty_issue_type": "product_not_functioning",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await file_warranty_claim_tool.run_with_validation(test_db, request_data)

        assert "Warranty contract not found" in str(error.value)

    @pytest.mark.anyio
    async def test_file_warranty_claim_empty_database(
        self, file_warranty_claim_tool, empty_db
    ):
        """Test error when filing claim in empty database."""
        # Arrange
        request_data = {
            "contract_id": "WCT-10000001",
            "customer_id": "CUS-10000001",
            "warranty_issue_type": "product_not_functioning",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await file_warranty_claim_tool.run_with_validation(empty_db, request_data)

        assert "Warranty contract not found" in str(error.value)

    @pytest.mark.anyio
    async def test_file_warranty_claim_first_claim_in_db(
        self, file_warranty_claim_tool, test_db
    ):
        """Test that first new claim gets correct ID."""
        # Arrange - test_db already has WCL-10000001
        request_data = {
            "contract_id": "WCT-10000001",
            "customer_id": "CUS-10000001",
            "warranty_issue_type": "product_not_functioning",
        }

        # Act
        result = await file_warranty_claim_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        # Should create WCL-20000001 (prefix WCL-2 for new claims)
        assert result["claim_id"] == "WCL-20000001"
        assert result["status"] == "pending"
