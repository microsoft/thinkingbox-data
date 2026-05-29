# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for client_access_api master tool."""

from datetime import datetime, timezone

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.client_access.models import (
    AccessType,
    ClearanceRecord,
    ClearanceStatus,
    ClientSystemAccess,
    NdaRecord,
    NdaStatus,
    VpnAccess,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.client_access.tools.api import (
    ClientAccessApiTool,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.degreed.models import (
    TrainingEnrollment,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.salesforce_crm.models import (
    ClearanceLevel,
    Client,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestClientAccessApi:
    @pytest.fixture
    def test_db(self):
        """Create a test database with client access data."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "vpn_access": VpnAccess,
            "client_system_access": ClientSystemAccess,
            "clearance_records": ClearanceRecord,
            "nda_records": NdaRecord,
            "training_enrollments": TrainingEnrollment,
            "clients": Client,
        }
        db._model_cls_to_stem = {
            VpnAccess: "vpn_access",
            ClientSystemAccess: "client_system_access",
            ClearanceRecord: "clearance_records",
            NdaRecord: "nda_records",
            TrainingEnrollment: "training_enrollments",
            Client: "clients",
        }

        # Create test VPN access records
        vpn1 = VpnAccess(
            id="VPN-1000001",
            employee_email="jane.doe@msg.com",
            client_id=None,
            revoked_at=None,
        )

        vpn2 = VpnAccess(
            id="VPN-1000002",
            employee_email="jane.doe@msg.com",
            client_id="CLT-0012345",
            revoked_at=None,
        )

        vpn3 = VpnAccess(
            id="VPN-1000003",
            employee_email="john.smith@msg.com",
            client_id=None,
            revoked_at=datetime(2024, 11, 1, tzinfo=timezone.utc),
        )

        # Create test client system access records
        csa1 = ClientSystemAccess(
            id="CSA-1000001",
            employee_email="jane.doe@msg.com",
            client_id="CLT-0012345",
            system_name="Client Salesforce",
            access_type=AccessType.FULL_ACCESS,
            revoked_at=None,
        )

        # Create test clearance records
        clearance1 = ClearanceRecord(
            employee_email="jane.doe@msg.com",
            clearance_level="standard",
            status=ClearanceStatus.CLEARED,
        )

        clearance2 = ClearanceRecord(
            employee_email="john.smith@msg.com",
            clearance_level="standard",
            status=ClearanceStatus.IN_PROGRESS,
        )

        # Create test NDA records
        nda1 = NdaRecord(
            employee_email="jane.doe@msg.com",
            client_id="CLT-0012345",
            status=NdaStatus.SIGNED,
        )

        nda2 = NdaRecord(
            employee_email="john.smith@msg.com",
            client_id="CLT-0012345",
            status=NdaStatus.SENT_FOR_SIGNATURE,
        )

        # Create test training enrollments
        enrollment1 = TrainingEnrollment(
            id="ENR-1000001",
            employee_email="jane.doe@msg.com",
            course_id="CRS-1000001",
            completion_date=datetime(2024, 11, 15),
        )

        enrollment2 = TrainingEnrollment(
            id="ENR-1000002",
            employee_email="jane.doe@msg.com",
            course_id="CRS-1000003",
            completion_date=datetime(2024, 10, 20),
        )

        enrollment3 = TrainingEnrollment(
            id="ENR-1000003",
            employee_email="john.smith@msg.com",
            course_id="CRS-1000001",
            completion_date=None,
        )

        # Create test client
        client1 = Client(
            id="CLT-0012345",
            name="Healthcare Corp",
            requires_nda=True,
            clearance_level=ClearanceLevel.STANDARD,
            required_training_courses=["CRS-1000001", "CRS-1000003"],
        )

        db._store = {
            VpnAccess: [vpn1, vpn2, vpn3],
            ClientSystemAccess: [csa1],
            ClearanceRecord: [clearance1, clearance2],
            NdaRecord: [nda1, nda2],
            TrainingEnrollment: [enrollment1, enrollment2, enrollment3],
            Client: [client1],
        }
        return db

    @pytest.fixture
    def client_access_tool(self):
        """Create an instance of the Client Access API tool."""
        return ClientAccessApiTool()

    # Tests for provision_vpn action
    @pytest.mark.anyio
    async def test_provision_vpn_success(self, client_access_tool, test_db):
        """Test successful VPN provisioning."""
        # Arrange
        request_data = {"action": "provision_vpn", "email": "new.user@msg.com"}

        # Act
        result = await client_access_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify VPN access was created
        vpn_records = test_db.get_all(VpnAccess)
        new_vpn = [v for v in vpn_records if v.employee_email == "new.user@msg.com"]
        assert len(new_vpn) == 1
        assert new_vpn[0].client_id is None
        assert new_vpn[0].revoked_at is None

    @pytest.mark.anyio
    async def test_provision_vpn_with_client_id(self, client_access_tool, test_db):
        """Test VPN provisioning with client-specific access."""
        # Arrange
        request_data = {
            "action": "provision_vpn",
            "email": "new.user@msg.com",
            "client_id": "CLT-0012345",
        }

        # Act
        result = await client_access_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify VPN access was created with client_id
        vpn_records = test_db.get_all(VpnAccess)
        new_vpn = [v for v in vpn_records if v.employee_email == "new.user@msg.com"]
        assert len(new_vpn) == 1
        assert new_vpn[0].client_id == "CLT-0012345"

    @pytest.mark.anyio
    async def test_provision_vpn_missing_email(self, client_access_tool, test_db):
        """Test VPN provisioning without email raises error."""
        # Arrange
        request_data = {"action": "provision_vpn"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await client_access_tool.run_with_validation(test_db, request_data)

    # Tests for check_vpn_access action
    @pytest.mark.anyio
    async def test_check_vpn_access_success(self, client_access_tool, test_db):
        """Test successful VPN access check."""
        # Arrange
        request_data = {"action": "check_vpn_access", "email": "jane.doe@msg.com"}

        # Act
        result = await client_access_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("vpn_access") is not None
        vpn_access = result["vpn_access"]
        assert len(vpn_access) == 2  # Two active VPN records for jane.doe
        assert all(v["employee_email"] == "jane.doe@msg.com" for v in vpn_access)
        assert all(v.get("revoked_at") is None for v in vpn_access)

    @pytest.mark.anyio
    async def test_check_vpn_access_excludes_revoked(self, client_access_tool, test_db):
        """Test that revoked VPN access is not included."""
        # Arrange
        request_data = {"action": "check_vpn_access", "email": "john.smith@msg.com"}

        # Act
        result = await client_access_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("vpn_access") is not None
        assert len(result["vpn_access"]) == 0  # Revoked VPN should not be included

    @pytest.mark.anyio
    async def test_check_vpn_access_empty_result(self, client_access_tool, test_db):
        """Test VPN access check for employee with no access."""
        # Arrange
        request_data = {"action": "check_vpn_access", "email": "nobody@msg.com"}

        # Act
        result = await client_access_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("vpn_access") is not None
        assert len(result["vpn_access"]) == 0

    @pytest.mark.anyio
    async def test_check_vpn_access_missing_email(self, client_access_tool, test_db):
        """Test VPN access check without email raises error."""
        # Arrange
        request_data = {"action": "check_vpn_access"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await client_access_tool.run_with_validation(test_db, request_data)

    # Tests for revoke_vpn action
    @pytest.mark.anyio
    async def test_revoke_vpn_all_access(self, client_access_tool, test_db):
        """Test revoking all VPN access for an employee."""
        # Arrange
        request_data = {"action": "revoke_vpn", "email": "jane.doe@msg.com"}

        # Act
        result = await client_access_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify all VPN access was revoked
        vpn_records = test_db.get_all(VpnAccess)
        jane_vpn = [v for v in vpn_records if v.employee_email == "jane.doe@msg.com"]
        assert all(v.revoked_at is not None for v in jane_vpn)

    @pytest.mark.anyio
    async def test_revoke_vpn_specific_client(self, client_access_tool, test_db):
        """Test revoking VPN access for specific client."""
        # Arrange
        request_data = {
            "action": "revoke_vpn",
            "email": "jane.doe@msg.com",
            "client_id": "CLT-0012345",
        }

        # Act
        result = await client_access_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify only client-specific VPN was revoked
        vpn_records = test_db.get_all(VpnAccess)
        jane_vpn = [v for v in vpn_records if v.employee_email == "jane.doe@msg.com"]

        # General VPN should still be active
        general_vpn = [v for v in jane_vpn if v.client_id is None]
        assert len(general_vpn) == 1
        assert general_vpn[0].revoked_at is None

        # Client-specific VPN should be revoked
        client_vpn = [v for v in jane_vpn if v.client_id == "CLT-0012345"]
        assert len(client_vpn) == 1
        assert client_vpn[0].revoked_at is not None

    @pytest.mark.anyio
    async def test_revoke_vpn_missing_email(self, client_access_tool, test_db):
        """Test VPN revocation without email raises error."""
        # Arrange
        request_data = {"action": "revoke_vpn"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await client_access_tool.run_with_validation(test_db, request_data)

    # Tests for provision_client_system action
    @pytest.mark.anyio
    async def test_provision_client_system_success(self, client_access_tool, test_db):
        """Test successful client system provisioning."""
        # Arrange
        request_data = {
            "action": "provision_client_system",
            "email": "new.user@msg.com",
            "client_id": "CLT-0012345",
            "system_name": "Client Portal",
            "access_type": "read_only",
        }

        # Act
        result = await client_access_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify access was created
        access_records = test_db.get_all(ClientSystemAccess)
        new_access = [
            a for a in access_records if a.employee_email == "new.user@msg.com"
        ]
        assert len(new_access) == 1
        assert new_access[0].client_id == "CLT-0012345"
        assert new_access[0].system_name == "Client Portal"
        assert new_access[0].access_type == AccessType.READ_ONLY

    @pytest.mark.anyio
    async def test_provision_client_system_all_access_types(
        self, client_access_tool, test_db
    ):
        """Test provisioning with all access types."""
        access_types = ["full_access", "read_only", "contributor", "admin"]

        for access_type in access_types:
            # Arrange
            request_data = {
                "action": "provision_client_system",
                "email": f"{access_type}@msg.com",
                "client_id": "CLT-0012345",
                "system_name": "Test System",
                "access_type": access_type,
            }

            # Act
            result = await client_access_tool.run_with_validation(test_db, request_data)

            # Assert
            assert result["success"] is True

    @pytest.mark.anyio
    async def test_provision_client_system_missing_email(
        self, client_access_tool, test_db
    ):
        """Test provisioning without email raises error."""
        # Arrange
        request_data = {
            "action": "provision_client_system",
            "client_id": "CLT-0012345",
            "system_name": "Test System",
            "access_type": "read_only",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await client_access_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_provision_client_system_missing_client_id(
        self, client_access_tool, test_db
    ):
        """Test provisioning without client_id raises error."""
        # Arrange
        request_data = {
            "action": "provision_client_system",
            "email": "user@msg.com",
            "system_name": "Test System",
            "access_type": "read_only",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: client_id"
        ):
            await client_access_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_provision_client_system_missing_system_name(
        self, client_access_tool, test_db
    ):
        """Test provisioning without system_name raises error."""
        # Arrange
        request_data = {
            "action": "provision_client_system",
            "email": "user@msg.com",
            "client_id": "CLT-0012345",
            "access_type": "read_only",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: system_name"
        ):
            await client_access_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_provision_client_system_missing_access_type(
        self, client_access_tool, test_db
    ):
        """Test provisioning without access_type raises error."""
        # Arrange
        request_data = {
            "action": "provision_client_system",
            "email": "user@msg.com",
            "client_id": "CLT-0012345",
            "system_name": "Test System",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: access_type"
        ):
            await client_access_tool.run_with_validation(test_db, request_data)

    # Tests for check_client_requirements action
    @pytest.mark.anyio
    async def test_check_client_requirements_success(self, client_access_tool, test_db):
        """Test successful client requirements check."""
        # Arrange
        request_data = {
            "action": "check_client_requirements",
            "client_id": "CLT-0012345",
        }

        # Act
        result = await client_access_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("requirements") is not None
        requirements = result["requirements"]
        assert requirements["clearance_level"] == "standard"
        assert requirements["requires_nda"] is True
        assert len(requirements["required_training_courses"]) == 2
        assert "CRS-1000001" in requirements["required_training_courses"]
        assert "CRS-1000003" in requirements["required_training_courses"]

    @pytest.mark.anyio
    async def test_check_client_requirements_not_found(
        self, client_access_tool, test_db
    ):
        """Test client requirements check for non-existent client."""
        # Arrange
        request_data = {
            "action": "check_client_requirements",
            "client_id": "CLT-9999999",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Client not found"):
            await client_access_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_check_client_requirements_missing_client_id(
        self, client_access_tool, test_db
    ):
        """Test client requirements check without client_id raises error."""
        # Arrange
        request_data = {"action": "check_client_requirements"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: client_id"
        ):
            await client_access_tool.run_with_validation(test_db, request_data)

    # Tests for get_employee_prerequisites action
    @pytest.mark.anyio
    async def test_get_employee_prerequisites_success(
        self, client_access_tool, test_db
    ):
        """Test successful employee prerequisites retrieval."""
        # Arrange
        request_data = {
            "action": "get_employee_prerequisites",
            "email": "jane.doe@msg.com",
            "client_id": "CLT-0012345",
        }

        # Act
        result = await client_access_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["clearance_status"] == "cleared"
        assert result["nda_status"] == "signed"
        assert result.get("completed_training_courses") is not None
        assert len(result["completed_training_courses"]) == 2
        assert "CRS-1000001" in result["completed_training_courses"]
        assert "CRS-1000003" in result["completed_training_courses"]

    @pytest.mark.anyio
    async def test_get_employee_prerequisites_no_clearance(
        self, client_access_tool, test_db
    ):
        """Test prerequisites when employee has no clearance record."""
        # Arrange
        request_data = {
            "action": "get_employee_prerequisites",
            "email": "nobody@msg.com",
            "client_id": "CLT-0012345",
        }

        # Act
        result = await client_access_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["clearance_status"] == "not_initiated"
        assert result["nda_status"] == "not_signed"
        assert len(result["completed_training_courses"]) == 0

    @pytest.mark.anyio
    async def test_get_employee_prerequisites_in_progress_clearance(
        self, client_access_tool, test_db
    ):
        """Test prerequisites with in-progress clearance."""
        # Arrange
        request_data = {
            "action": "get_employee_prerequisites",
            "email": "john.smith@msg.com",
            "client_id": "CLT-0012345",
        }

        # Act
        result = await client_access_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["clearance_status"] == "in_progress"
        assert result["nda_status"] == "sent_for_signature"
        assert len(result["completed_training_courses"]) == 0  # Incomplete enrollment

    @pytest.mark.anyio
    async def test_get_employee_prerequisites_missing_email(
        self, client_access_tool, test_db
    ):
        """Test prerequisites without email raises error."""
        # Arrange
        request_data = {
            "action": "get_employee_prerequisites",
            "client_id": "CLT-0012345",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await client_access_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_employee_prerequisites_missing_client_id(
        self, client_access_tool, test_db
    ):
        """Test prerequisites without client_id raises error."""
        # Arrange
        request_data = {
            "action": "get_employee_prerequisites",
            "email": "user@msg.com",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: client_id"
        ):
            await client_access_tool.run_with_validation(test_db, request_data)

    # Test for invalid action
    @pytest.mark.anyio
    async def test_invalid_action(self, client_access_tool, test_db):
        """Test that invalid action raises validation error."""
        # Arrange
        request_data = {"action": "invalid_action"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await client_access_tool.run_with_validation(test_db, request_data)
