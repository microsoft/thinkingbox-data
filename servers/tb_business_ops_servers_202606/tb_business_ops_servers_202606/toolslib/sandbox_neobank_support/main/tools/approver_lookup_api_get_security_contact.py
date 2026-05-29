# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for getting approver contact."""

from typing import Any, Dict, Type

from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
    Department,
    Employee,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class GetApproverContactInput(BaseModel):
    """Input for get_approver_contact tool."""

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, validate_assignment=True
    )

    required_approver: str = Field(
        ...,
        description="Department enum value for the required approver's team",
        examples=["it_security", "finance_accounting"],
    )


class GetApproverContactOutput(BaseModel):
    """Output for get_approver_contact tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    employee_id: str = Field(
        ..., description="Approver's employee ID", examples=["WD-100042"]
    )
    contact_email: str = Field(
        ..., description="Approver's email", examples=["amanda.lee@vdb.com"]
    )
    contact_name: str = Field(
        ..., description="Approver's full name", examples=["Amanda Lee"]
    )


class GetApproverContactTool(Tool):
    """Tool implementation for getting approver contact."""

    @property
    def name(self) -> str:
        return "approver_lookup_api_get_approver_contact"

    @property
    def description(self) -> str:
        return (
            "Retrieves contact details (employee_id, email, name) for a required approver by department. "
            "Supports: 'it_security', 'finance_accounting', 'compliance_risk'. "
            "Returns the highest-level employee from the specified department. "
            "Use this to dynamically lookup who to route approval requests to based on the request type "
            "and approval workflow requirements."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetApproverContactInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetApproverContactOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetApproverContactInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetApproverContactOutput

    async def run(
        self, db: InMemoryDatabase, request: GetApproverContactInput
    ) -> GetApproverContactOutput:
        """Get approver contact based on required_approver type."""
        try:
            # Get all employees
            all_employees = db.get_all(Employee)

            # Map required_approver string to Department enum
            # Accepted values: it_security, finance_accounting, compliance_risk
            # (Legal removed as not used in Policy)
            approver_to_dept = {
                "it_security": Department.IT_SECURITY,
                "finance_accounting": Department.FINANCE_ACCOUNTING,
                "compliance_risk": Department.COMPLIANCE_RISK,
            }

            approver_type = request.required_approver.lower()

            if approver_type not in approver_to_dept:
                raise Tool.ExecutionError(
                    f"Invalid required_approver: {request.required_approver}. "
                    "Must be one of: it_security, finance_accounting, compliance_risk"
                )

            target_dept = approver_to_dept[approver_type]

            # Query: employees WHERE department = {required_approver input} AND level = (SELECT MAX(level) FROM employees WHERE department = {required_approver input})
            # Find the maximum level in the department
            dept_employees = [
                emp for emp in all_employees if emp.department == target_dept
            ]

            if not dept_employees:
                raise Tool.ExecutionError(f"No {target_dept.value} team members found")

            max_level = max(emp.level for emp in dept_employees)

            # Get the highest-level employee(s) and return the first one
            approver = next(emp for emp in dept_employees if emp.level == max_level)

            # Return approver contact information
            return GetApproverContactOutput(
                employee_id=approver.id,
                contact_email=approver.email,
                contact_name=approver.full_name,
            )

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to get approver contact: {str(e)}"
            raise Tool.ExecutionError(error_message)
