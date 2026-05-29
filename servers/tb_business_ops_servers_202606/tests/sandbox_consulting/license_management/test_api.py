# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for license_management_api master tool."""

from datetime import datetime

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.license_management.models import (
    LicenseAllocation,
    LicensePool,
    LicensePoolRecord,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.license_management.tools.api import (
    LicenseManagementApiTool,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.software_catalog.models import (
    PoolType,
    SoftwareCatalog,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestLicenseManagementApi:
    @pytest.fixture
    def test_db(self):
        """Create a test database with license pools, allocations, and software catalog."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "license_pools": LicensePoolRecord,
            "license_allocations": LicenseAllocation,
            "software_catalog": SoftwareCatalog,
        }
        db._model_cls_to_stem = {
            LicensePoolRecord: "license_pools",
            LicenseAllocation: "license_allocations",
            SoftwareCatalog: "software_catalog",
        }

        # Create test license pools
        pool1 = LicensePoolRecord(
            catalog_id="CAT-1000001",
            pool_type=LicensePool.STANDARD,
            total_licenses=10,  # 10 total, 2 allocated = 8 available
        )

        pool2 = LicensePoolRecord(
            catalog_id="CAT-1000002",
            pool_type=LicensePool.ENTERPRISE,
            total_licenses=None,  # Unlimited
        )

        pool3 = LicensePoolRecord(
            catalog_id="CAT-1000003",
            pool_type=LicensePool.STANDARD,
            total_licenses=5,  # 5 total, 1 allocated = 4 available
        )

        # Create test license allocations
        allocation1 = LicenseAllocation(
            id="LIC-1000001",
            catalog_id="CAT-1000001",
            employee_email="john.smith@msg.com",
            engagement_code="ENG-0012345",
            pool_type=LicensePool.STANDARD,
            deallocated_at=None,
        )

        allocation2 = LicenseAllocation(
            id="LIC-1000002",
            catalog_id="CAT-1000001",
            employee_email="jane.doe@msg.com",
            engagement_code="ENG-0012345",
            pool_type=LicensePool.STANDARD,
            deallocated_at=None,
        )

        allocation3 = LicenseAllocation(
            id="LIC-1000003",
            catalog_id="CAT-1000002",
            employee_email="alice.wilson@msg.com",
            engagement_code="ENG-0023456",
            pool_type=LicensePool.ENTERPRISE,
            deallocated_at=None,
        )

        allocation4 = LicenseAllocation(
            id="LIC-1000004",
            catalog_id="CAT-1000003",
            employee_email="bob.taylor@msg.com",
            engagement_code=None,
            pool_type=LicensePool.STANDARD,
            deallocated_at=None,
        )

        # Deallocated allocation (should not be counted)
        allocation5 = LicenseAllocation(
            id="LIC-1000005",
            catalog_id="CAT-1000001",
            employee_email="old.user@msg.com",
            engagement_code="ENG-0034567",
            pool_type=LicensePool.STANDARD,
            deallocated_at=datetime(2024, 10, 15),
        )

        # Create test software catalog entries
        software1 = SoftwareCatalog(
            id="CAT-1000001",
            name="Tableau Desktop",
            annual_cost=840,
            pool_type=PoolType.STANDARD,
        )

        software2 = SoftwareCatalog(
            id="CAT-1000002",
            name="Microsoft Power BI Pro",
            annual_cost=120,
            pool_type=PoolType.ENTERPRISE,
        )

        software3 = SoftwareCatalog(
            id="CAT-1000003",
            name="Adobe Creative Cloud",
            annual_cost=600,
            pool_type=PoolType.STANDARD,
        )

        db._store = {
            LicensePoolRecord: [pool1, pool2, pool3],
            LicenseAllocation: [
                allocation1,
                allocation2,
                allocation3,
                allocation4,
                allocation5,
            ],
            SoftwareCatalog: [software1, software2, software3],
        }
        return db

    @pytest.fixture
    def license_tool(self):
        """Create an instance of the License Management API tool."""
        return LicenseManagementApiTool()

    # Tests for check_availability action
    @pytest.mark.anyio
    async def test_check_availability_standard_pool(self, license_tool, test_db):
        """Test checking availability for standard pool."""
        # Arrange - CAT-1000001: 10 total, 2 active allocations = 8 available
        request_data = {
            "action": "check_availability",
            "catalog_id": "CAT-1000001",
            "pool_type": "standard",
        }

        # Act
        result = await license_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("available_count") == 8

    @pytest.mark.anyio
    async def test_check_availability_enterprise_pool_unlimited(
        self, license_tool, test_db
    ):
        """Test checking availability for enterprise pool returns 99999 (unlimited)."""
        # Arrange - CAT-1000002 is enterprise (total_licenses=null)
        request_data = {
            "action": "check_availability",
            "catalog_id": "CAT-1000002",
            "pool_type": "enterprise",
        }

        # Act
        result = await license_tool.run_with_validation(test_db, request_data)

        # Assert - 99999 means unlimited
        assert result.get("available_count") == 99999

    @pytest.mark.anyio
    async def test_check_availability_excludes_deallocated(self, license_tool, test_db):
        """Test that deallocated licenses are not counted against availability."""
        # Arrange - CAT-1000003: 5 total, 1 active (1 deallocated should be ignored) = 4 available
        request_data = {
            "action": "check_availability",
            "catalog_id": "CAT-1000003",
            "pool_type": "standard",
        }

        # Act
        result = await license_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("available_count") == 4

    @pytest.mark.anyio
    async def test_check_availability_pool_not_found(self, license_tool, test_db):
        """Test error when license pool not found."""
        # Arrange
        request_data = {
            "action": "check_availability",
            "catalog_id": "CAT-9999999",
            "pool_type": "standard",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="License pool not found"):
            await license_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_check_availability_missing_catalog_id(self, license_tool, test_db):
        """Test error when catalog_id is missing."""
        # Arrange
        request_data = {"action": "check_availability", "pool_type": "standard"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: catalog_id"
        ):
            await license_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_check_availability_missing_pool_type(self, license_tool, test_db):
        """Test error when pool_type is missing."""
        # Arrange
        request_data = {"action": "check_availability", "catalog_id": "CAT-1000001"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: pool_type"
        ):
            await license_tool.run_with_validation(test_db, request_data)

    # Tests for allocate action
    @pytest.mark.anyio
    async def test_allocate_success_with_engagement(self, license_tool, test_db):
        """Test successful license allocation with engagement code."""
        # Arrange
        request_data = {
            "action": "allocate",
            "catalog_id": "CAT-1000003",
            "email": "newuser@msg.com",
            "pool_type": "standard",
            "engagement_code": "ENG-0045678",
        }

        # Act
        result = await license_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert result.get("success") is True

        # Verify allocation was created
        allocations = test_db.get_all(LicenseAllocation)
        new_allocation = [
            a for a in allocations if a.employee_email == "newuser@msg.com"
        ]
        assert len(new_allocation) == 1
        assert new_allocation[0].catalog_id == "CAT-1000003"
        assert new_allocation[0].engagement_code == "ENG-0045678"
        assert new_allocation[0].pool_type == LicensePool.STANDARD
        assert new_allocation[0].deallocated_at is None

    @pytest.mark.anyio
    async def test_allocate_success_without_engagement(self, license_tool, test_db):
        """Test successful license allocation without engagement code."""
        # Arrange
        request_data = {
            "action": "allocate",
            "catalog_id": "CAT-1000002",
            "email": "anotheruser@msg.com",
            "pool_type": "enterprise",
        }

        # Act
        result = await license_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert result.get("success") is True

        # Verify allocation was created
        allocations = test_db.get_all(LicenseAllocation)
        new_allocation = [
            a for a in allocations if a.employee_email == "anotheruser@msg.com"
        ]
        assert len(new_allocation) == 1
        assert new_allocation[0].engagement_code is None

    @pytest.mark.anyio
    async def test_allocate_missing_catalog_id(self, license_tool, test_db):
        """Test error when catalog_id is missing."""
        # Arrange
        request_data = {
            "action": "allocate",
            "email": "user@msg.com",
            "pool_type": "standard",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: catalog_id"
        ):
            await license_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_allocate_missing_email(self, license_tool, test_db):
        """Test error when email is missing."""
        # Arrange
        request_data = {
            "action": "allocate",
            "catalog_id": "CAT-1000001",
            "pool_type": "standard",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await license_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_allocate_missing_pool_type(self, license_tool, test_db):
        """Test error when pool_type is missing."""
        # Arrange
        request_data = {
            "action": "allocate",
            "catalog_id": "CAT-1000001",
            "email": "user@msg.com",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: pool_type"
        ):
            await license_tool.run_with_validation(test_db, request_data)

    # Tests for get_cost action
    @pytest.mark.anyio
    async def test_get_cost_success(self, license_tool, test_db):
        """Test successful cost retrieval."""
        # Arrange
        request_data = {"action": "get_cost", "catalog_id": "CAT-1000001"}

        # Act
        result = await license_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("annual_cost") == 840

    @pytest.mark.anyio
    async def test_get_cost_different_software(self, license_tool, test_db):
        """Test cost retrieval for different software."""
        # Arrange
        request_data = {"action": "get_cost", "catalog_id": "CAT-1000003"}

        # Act
        result = await license_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("annual_cost") == 600

    @pytest.mark.anyio
    async def test_get_cost_not_found(self, license_tool, test_db):
        """Test error when software catalog entry not found."""
        # Arrange
        request_data = {"action": "get_cost", "catalog_id": "CAT-9999999"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Software catalog entry not found"
        ):
            await license_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_cost_missing_catalog_id(self, license_tool, test_db):
        """Test error when catalog_id is missing."""
        # Arrange
        request_data = {"action": "get_cost"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: catalog_id"
        ):
            await license_tool.run_with_validation(test_db, request_data)

    # General tests
    @pytest.mark.anyio
    async def test_invalid_action(self, license_tool, test_db):
        """Test error with invalid action."""
        # Arrange
        request_data = {"action": "invalid_action"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await license_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_check_availability_empty_database(self, license_tool):
        """Test check_availability with empty database."""
        # Arrange
        empty_db = InMemoryDatabase.__new__(InMemoryDatabase)
        empty_db._stem_to_model_cls = {"license_pools": LicensePoolRecord}
        empty_db._model_cls_to_stem = {LicensePoolRecord: "license_pools"}
        empty_db._store = {LicensePoolRecord: []}

        request_data = {
            "action": "check_availability",
            "catalog_id": "CAT-1000001",
            "pool_type": "standard",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="License pool not found"):
            await license_tool.run_with_validation(empty_db, request_data)
