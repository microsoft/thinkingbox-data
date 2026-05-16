# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for okta_provision_access tool."""

import pytest
from ms_toloka_servers.toolslib.sandbox_consulting.okta.models import (
    AccessType,
    ApplicationAccessLog,
)
from ms_toloka_servers.toolslib.sandbox_consulting.okta.tools.provision_access import (
    OktaProvisionAccessTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestOktaProvisionAccess:
    @pytest.fixture
    def test_db(self):
        """Create a test database with application access logs."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "application_access_logs": ApplicationAccessLog,
        }
        db._model_cls_to_stem = {
            ApplicationAccessLog: "application_access_logs",
        }

        # Create test access log entries
        log1 = ApplicationAccessLog(
            id="AAL-1000001",
            employee_email="jane.doe@msg.com",
            app_name="Tableau Desktop",
            access_type=AccessType.FULL_ACCESS,
        )

        log2 = ApplicationAccessLog(
            id="AAL-1000002",
            employee_email="john.smith@msg.com",
            app_name="Microsoft Power BI Pro",
            access_type=AccessType.FULL_ACCESS,
        )

        log3 = ApplicationAccessLog(
            id="AAL-1000003",
            employee_email="sarah.johnson@msg.com",
            app_name="Adobe Creative Cloud",
            access_type=AccessType.CONTRIBUTOR,
        )

        db._store = {
            ApplicationAccessLog: [log1, log2, log3],
        }
        return db

    @pytest.fixture
    def provision_tool(self):
        """Create an instance of the provision access tool."""
        return OktaProvisionAccessTool()

    @pytest.mark.anyio
    async def test_provision_access_success_with_access_type(
        self, provision_tool, test_db
    ):
        """Test successful access provisioning with specified access type."""
        # Arrange
        request_data = {
            "email": "test.user@msg.com",
            "app_name": "Tableau",
            "access_type": "read_only",
        }

        # Act
        result = await provision_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert result["success"] is True

        # Assert database state
        all_logs = test_db.get_all(ApplicationAccessLog)
        assert len(all_logs) == 4
        new_log = all_logs[-1]
        assert new_log.id == "AAL-2-000000"
        assert new_log.employee_email == "test.user@msg.com"
        assert new_log.app_name == "Tableau"
        assert new_log.access_type == AccessType.READ_ONLY

    @pytest.mark.anyio
    async def test_provision_access_success_default_access_type(
        self, provision_tool, test_db
    ):
        """Test successful access provisioning with default access type."""
        # Arrange
        request_data = {
            "email": "another.user@msg.com",
            "app_name": "Salesforce",
        }

        # Act
        result = await provision_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert result["success"] is True

        # Assert database state
        all_logs = test_db.get_all(ApplicationAccessLog)
        assert len(all_logs) == 4
        new_log = all_logs[-1]
        assert new_log.id == "AAL-2-000000"
        assert new_log.employee_email == "another.user@msg.com"
        assert new_log.app_name == "Salesforce"
        assert new_log.access_type == AccessType.FULL_ACCESS  # Default

    @pytest.mark.anyio
    async def test_provision_access_multiple_sequential(self, provision_tool, test_db):
        """Test multiple sequential access provisioning operations."""
        # Arrange & Act - First provision
        request1 = {
            "email": "user1@msg.com",
            "app_name": "App1",
            "access_type": "admin",
        }
        result1 = await provision_tool.run_with_validation(test_db, request1)

        # Assert first provision
        assert result1["success"] is True
        all_logs = test_db.get_all(ApplicationAccessLog)
        assert len(all_logs) == 4
        assert all_logs[-1].id == "AAL-2-000000"

        # Arrange & Act - Second provision
        request2 = {
            "email": "user2@msg.com",
            "app_name": "App2",
            "access_type": "contributor",
        }
        result2 = await provision_tool.run_with_validation(test_db, request2)

        # Assert second provision
        assert result2["success"] is True
        all_logs = test_db.get_all(ApplicationAccessLog)
        assert len(all_logs) == 5
        assert all_logs[-1].id == "AAL-2-000001"

    @pytest.mark.anyio
    async def test_provision_access_all_access_types(self, provision_tool, test_db):
        """Test provisioning with all valid access types."""
        access_types = ["full_access", "read_only", "contributor", "admin"]

        for idx, access_type in enumerate(access_types):
            # Arrange
            request_data = {
                "email": f"user{idx}@msg.com",
                "app_name": f"App{idx}",
                "access_type": access_type,
            }

            # Act
            result = await provision_tool.run_with_validation(test_db, request_data)

            # Assert
            assert result["success"] is True

        # Assert database state
        all_logs = test_db.get_all(ApplicationAccessLog)
        assert len(all_logs) == 7  # 3 initial + 4 new

    @pytest.mark.anyio
    async def test_provision_access_empty_database(self, provision_tool):
        """Test provisioning with empty database."""
        # Arrange
        empty_db = InMemoryDatabase.__new__(InMemoryDatabase)
        empty_db._stem_to_model_cls = {"application_access_logs": ApplicationAccessLog}
        empty_db._model_cls_to_stem = {ApplicationAccessLog: "application_access_logs"}
        empty_db._store = {ApplicationAccessLog: []}

        request_data = {
            "email": "first.user@msg.com",
            "app_name": "FirstApp",
            "access_type": "full_access",
        }

        # Act
        result = await provision_tool.run_with_validation(empty_db, request_data)

        # Assert
        assert result["success"] is True
        all_logs = empty_db.get_all(ApplicationAccessLog)
        assert len(all_logs) == 1
        assert all_logs[0].id == "AAL-2-000000"

    @pytest.mark.anyio
    async def test_provision_access_same_user_multiple_apps(
        self, provision_tool, test_db
    ):
        """Test provisioning multiple apps for the same user."""
        # Arrange
        email = "multi.app.user@msg.com"
        apps = ["App1", "App2", "App3"]

        for app in apps:
            request_data = {
                "email": email,
                "app_name": app,
                "access_type": "full_access",
            }

            # Act
            result = await provision_tool.run_with_validation(test_db, request_data)

            # Assert
            assert result["success"] is True

        # Assert database state - same user can have multiple app access
        all_logs = test_db.get_all(ApplicationAccessLog)
        user_logs = [log for log in all_logs if log.employee_email == email]
        assert len(user_logs) == 3
