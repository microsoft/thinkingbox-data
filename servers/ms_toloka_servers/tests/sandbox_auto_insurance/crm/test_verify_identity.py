# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for the verify_identity tool."""

import pytest
from ms_toloka_servers.toolslib.sandbox_auto_insurance.crm.models import Customer
from ms_toloka_servers.toolslib.sandbox_auto_insurance.crm.tools.verify_identity import (
    VerifyIdentityTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestVerifyIdentity:
    @pytest.fixture
    def test_db(self):
        """Create a test database with sample data."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"customers": Customer}
        db._model_cls_to_stem = {Customer: "customers"}

        # Create sample customers
        customer1 = Customer(
            id="CUS-00012345",
            email="john.smith@email.com",
            first_name="John",
            last_name="Smith",
            date_of_birth="1985-03-15",
            tier="Standard",
            fraud_flag=False,
            ssn_last_4="1234",
            security_question="What is your pet's name?",
            security_answer="Fluffy",
        )
        customer2 = Customer(
            id="CUS-00023456",
            email="jane.doe@email.com",
            first_name="Jane",
            last_name="Doe",
            date_of_birth="1990-07-22",
            tier="Preferred",
            ssn_last_4=None,
            security_question=None,
            security_answer=None,
        )

        db._store = {Customer: [customer1, customer2]}
        return db

    @pytest.fixture
    def verify_identity_tool(self):
        """Create an instance of VerifyIdentityTool."""
        return VerifyIdentityTool()

    @pytest.mark.anyio
    async def test_verify_identity_with_ssn_success(
        self, verify_identity_tool, test_db
    ):
        """Test successful identity verification using SSN."""
        # Arrange
        request_data = {"customer_id": "CUS-00012345", "ssn_last_4": "1234"}

        # Act
        result = await verify_identity_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["verified"] is True
        assert result["verification_method"] == "ssn"

    @pytest.mark.anyio
    async def test_verify_identity_with_ssn_failure(
        self, verify_identity_tool, test_db
    ):
        """Test failed identity verification using wrong SSN."""
        # Arrange
        request_data = {"customer_id": "CUS-00012345", "ssn_last_4": "9999"}

        # Act
        result = await verify_identity_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["verified"] is False
        assert result["verification_method"] == "ssn"

    @pytest.mark.anyio
    async def test_verify_identity_with_security_question_success(
        self, verify_identity_tool, test_db
    ):
        """Test successful identity verification using security question."""
        # Arrange
        request_data = {"customer_id": "CUS-00012345", "security_answer": "Fluffy"}

        # Act
        result = await verify_identity_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["verified"] is True
        assert result["verification_method"] == "security_question"

    @pytest.mark.anyio
    async def test_verify_identity_with_security_question_case_insensitive(
        self, verify_identity_tool, test_db
    ):
        """Test that security question verification is case-insensitive."""
        # Arrange
        request_data = {"customer_id": "CUS-00012345", "security_answer": "fluffy"}

        # Act
        result = await verify_identity_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["verified"] is True
        assert result["verification_method"] == "security_question"

    @pytest.mark.anyio
    async def test_verify_identity_with_security_question_failure(
        self, verify_identity_tool, test_db
    ):
        """Test failed identity verification using wrong security answer."""
        # Arrange
        request_data = {"customer_id": "CUS-00012345", "security_answer": "WrongAnswer"}

        # Act
        result = await verify_identity_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["verified"] is False
        assert result["verification_method"] == "security_question"

    @pytest.mark.anyio
    async def test_verify_identity_no_credentials_provided(
        self, verify_identity_tool, test_db
    ):
        """Test error when no verification credentials are provided."""
        # Arrange
        request_data = {"customer_id": "CUS-00012345"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError,
            match="Must provide either ssn_last_4 or security_answer",
        ):
            await verify_identity_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_verify_identity_customer_not_found(
        self, verify_identity_tool, test_db
    ):
        """Test error when customer ID is not found."""
        # Arrange
        request_data = {"customer_id": "CUS-99999999", "ssn_last_4": "1234"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="not found"):
            await verify_identity_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_verify_identity_ssn_takes_precedence(
        self, verify_identity_tool, test_db
    ):
        """Test that SSN verification is used when both SSN and security answer are provided."""
        # Arrange
        request_data = {
            "customer_id": "CUS-00012345",
            "ssn_last_4": "1234",
            "security_answer": "WrongAnswer",
        }

        # Act
        result = await verify_identity_tool.run_with_validation(test_db, request_data)

        # Assert
        # Should use SSN verification (which is correct) and succeed
        assert result["verified"] is True
        assert result["verification_method"] == "ssn"

    @pytest.mark.anyio
    async def test_verify_identity_with_no_security_answer_on_file(
        self, verify_identity_tool, test_db
    ):
        """Test verification when customer has no security answer on file."""
        # Arrange
        request_data = {"customer_id": "CUS-00023456", "security_answer": "AnyAnswer"}

        # Act
        result = await verify_identity_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["verified"] is False
        assert result["verification_method"] == "security_question"
