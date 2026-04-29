# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from thinkingbox.common import Judge, TestContext
from thinkingbox.common.chat_types import Text

"""!
scenario: sandbox_neobank_support_v1
"""
SERVER_NAME = "sandbox_neobank_support_v1"


def validate_database(x: TestContext):
    result_db_hash = x.effects[SERVER_NAME]["result_db_hash"]
    golden_db_hash = x.effects[SERVER_NAME]["golden_db_hash"]

    if result_db_hash != golden_db_hash:
        diff = x.effects[SERVER_NAME].get("diff", [])
        error_msg = (
            "Database hash after test execution does not match "
            "expected golden hash\n"
        )
        error_msg += f"Result hash: {result_db_hash}\n"
        error_msg += f"Golden hash: {golden_db_hash}\n"

        if diff:
            error_msg += f"\nFound {len(diff)} difference(s):\n"
            for i, d in enumerate(diff, 1):
                error_msg += f"\n{i}. Path: {d.get('path', 'N/A')}\n"
                error_msg += f"   Type: {d.get('type', 'N/A')}\n"
                result_json = json.dumps(
                    d.get("result"), ensure_ascii=False, indent=11
                )[0:500]
                golden_json = json.dumps(
                    d.get("golden"), ensure_ascii=False, indent=11
                )[0:500]
                error_msg += f"   Result:  {result_json}\n"
                error_msg += f"   Golden:  {golden_json}\n"

        assert False, error_msg


def _safe_tag_encode(text: str) -> str:
    return text.replace("<", "&lt;").replace(">", "&gt;")


SYSTEM_CUSTOM_RUBRIC = """\
You are a judge, your task is to evaluate a message based on a custom rubric.
You will be provided with a rubric enclosed between <rubric> and </rubric> tags,
and a message enclosed between <message> and </message> tags and a numerical score between -10 and 10 enclosed between <numerical_score> and </numerical_score> tags.
Your task is to determine whether the message meets the criteria specified in the rubric.
If it meets the criteria, response with the numerical score provided, otherwise respond with 0.
The format will be as follows:
<rubric>
The rubric to evaluate the message against.
</rubric>
<message>
The message to be evaluated.
</message>
<numerical_score>
The numerical score to assign if the message meets the rubric criteria.
</numerical_score>
Respond only with the numerical score.
"""


USER_CUSTOM_RUBRIC = """\
<rubric>
{rubric}
</rubric>
<message>
{message}
</message>
<numerical_score>
{numerical_score}
</numerical_score>"""


def custom_rubric_score(
    judge: Judge, message: str, rubric: str, numerical_score: int
) -> dict:
    user_msg = USER_CUSTOM_RUBRIC.format(
        message=_safe_tag_encode(message),
        rubric=_safe_tag_encode(rubric),
        numerical_score=numerical_score,
    )
    msg = judge._get_text_completion(
        messages=[
            Text(role="system", content=SYSTEM_CUSTOM_RUBRIC),
            Text(role="user", content=user_msg),
        ]
    )
    try:
        score = int(msg.content.strip())
    except (ValueError, AttributeError):
        score = 0
    return {"score": score, "total_score": numerical_score}


def numerical_threshold(score_list: list) -> bool:
    score_sum = sum(item["score"] for item in score_list)
    total_sum = sum(
        item["total_score"] for item in score_list if item["total_score"] > 0
    )
    if total_sum == 0:
        return False
    return score_sum >= 0.7 * total_sum


def validate_rubrics(x: TestContext, judge: Judge):
    rubrics_definitions = x.effects[SERVER_NAME].get("rubrics", {})

    # Evaluate rubrics using Judge FIRST (before any assertions)
    score_list = []
    rubric_results = {}
    total_score = 0
    total_possible = 0

    if not rubrics_definitions:
        return

    agent_response = x.response

    for rubric_id, rubric_config in rubrics_definitions.items():
        criteria_text = rubric_config.get("criteria_text", "")
        reward = rubric_config.get("reward", 0)

        # Use Judge to evaluate the rubric
        score_result = custom_rubric_score(
            judge=judge,
            message=agent_response,
            rubric=criteria_text,
            numerical_score=reward,
        )

        score_list.append(score_result)
        rubric_results[rubric_id] = {
            "criteria_text": criteria_text,
            "score": score_result["score"],
            "total_score": score_result["total_score"],
        }

    total_score = sum(item["score"] for item in score_list)
    total_possible = sum(
        item["total_score"] for item in score_list if item["total_score"] > 0
    )

    assert numerical_threshold(
        score_list
    ), f"Rubrics threshold not met: {total_score}/{total_possible} < 70%"


def test_aa_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to reset my Okta password but I have elevated privileges on several systems. My name is Daniel Parker and my email is daniel.parker@vdb.com. I have admin access on AWS, Okta, and Splunk, so I want to make sure nothing gets disrupted.
    user_context: |
        You are Daniel Parker, an IT Operations Lead contacting IT support because you need your Okta password reset. You have admin-level access on AWS, Okta, and Splunk and are concerned about those not being affected.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - You are NOT locked out of Okta — you simply forgot your password. The self-service reset portal gave you an error when you tried it. If the agent asks whether you are locked out, clarify that you are not locked out, just unable to remember your password.
        - If the agent recommends using a self-service password reset portal, respond that you already tried it but it gave you an error and didn't work. Ask the agent to reset it directly.
        - If the agent confirms the reset was completed, thank them and end the conversation.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637284
              email: daniel.parker@vdb.com
              full_name: Daniel Parker
              level: 5
              department: it_operations
              role: IT Operations Lead
              office_location: sf
              start_date: '2020-09-01T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Parker
              email: daniel.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-738-4291
              verified: true
              active: true
              created_at: '2024-02-15T00:00:00Z'
              updated_at: '2024-02-15T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41637295
              employee_id: WD-637284
              app_name: AWS
              access_level: admin
              granted_at: '2021-03-15T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-52748361
              employee_id: WD-637284
              app_name: Okta
              access_level: admin
              granted_at: '2021-03-15T10:05:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-63859472
              employee_id: WD-637284
              app_name: Splunk
              access_level: admin
              granted_at: '2021-06-20T09:30:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-48271639
              employee_id: WD-637284
              group_name: it_ops_team
              added_at: '2020-09-05T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_security_incidents: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.parker@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Okta Password Reset Request
                  description: Employee requests Okta password reset. Employee reports having elevated admin-level access on AWS, Okta, and Splunk.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: okta_security_api_execute_action
              parameters:
                email: daniel.parker@vdb.com
                operation: force_password_reset
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Okta Password Reset Request
                  description: Employee requested Okta password reset. Self-service failed. Agent-assisted password reset completed.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
    """

    validate_database(x)


def test_dc_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Daniel Harris from the Compliance team, email daniel.harris@vdb.com. We discovered a discrepancy in our SAR filing that's due tomorrow (October 2nd). I need direct read-only production database access to verify the transaction details. The case ID is COMP-3847291. This is urgent given the regulatory deadline — can you help get this set up?
    user_context: |
        You are Daniel Harris, a Compliance Manager at the company, requesting emergency read-only access to the production database to investigate a SAR (Suspicious Activity Report) filing discrepancy. The regulatory deadline is tomorrow, October 2nd, 2025. Your case ID is COMP-3847291.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent asks you to confirm the request or details, confirm them.
        - If the agent informs you that approvals are needed and the ticket is pending, acknowledge and thank them.
        - If the agent asks about access duration, expiry time, or timezone, confirm that 24 hours of access (expiring October 2nd, 2025 at 13:00 UTC) is sufficient to complete the verification before the filing deadline.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637482
              email: daniel.harris@vdb.com
              full_name: Daniel Harris
              level: 5
              department: compliance_risk
              role: Compliance Manager
              office_location: sf
              start_date: '2020-04-01T00:00:00Z'
              manager_id: WD-926473
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Harris
              email: daniel.harris@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-382-6914
              verified: true
              active: true
              created_at: '2024-04-10T00:00:00Z'
              updated_at: '2024-04-10T00:00:00Z'
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-82461739
              employee_id: WD-637482
              group_name: compliance_team
              added_at: '2020-04-02T09:00:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.harris@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: daniel.harris@vdb.com
                app_name: Production database
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.harris@vdb.com'
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.harris@vdb.com
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: jennifer.brown@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: amanda.lee@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Production Database Read-Only Access Request — Regulatory SAR Filing Deadline
                  description: 'Compliance Manager requests read-only production database access to verify transaction details for SAR filing discrepancy. Case ID: COMP-3847291. Regulatory deadline: 2025-10-02.'
                  status: open
                  priority: urgent
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.harris@vdb.com
                approver_email: jennifer.brown@vdb.com
                details: 'Requesting read-only Production database access for compliance investigation. SAR filing discrepancy identified, case ID COMP-3847291. Regulatory deadline: 2025-10-02. Director approval required per Group 5 sensitivity policy.'
                urgency: critical
                ticket_id: '6'
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.harris@vdb.com
                approver_email: amanda.lee@vdb.com
                details: 'Requesting read-only Production database access for compliance investigation. SAR filing discrepancy identified, case ID COMP-3847291. Regulatory deadline: 2025-10-02. IT Security approval required per Group 5 sensitivity policy.'
                urgency: critical
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  priority: urgent
                  type: problem
                  tags: production_access,temporary_access
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: 'SAR filing discrepancy requiring verification of transaction details in production database. Case ID: COMP-3847291. Regulatory deadline: 2025-10-02.'
                  approver_id: WD-926473,WD-753918
                  approval_request_ids: APR-00000007,APR-00000008
                  access_expiry_date: '2025-10-02T13:00:00Z'
    """

    validate_database(x)


def test_dc_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hey, I'm Daniel Park (daniel.park@vdb.com) on the finance data team. I need access to the Snowflake raw replica for a data migration project I'm working on. I need access to the raw replica tables to build the data migration scripts. The analytics mart doesn't have all the fields I need — there are several source columns that got dropped in the transformation layer that I need to map for the migration. My contract scope includes data warehouse migration support, so this should be within scope. Can you get this set up for me?
    user_context: |
        You are Daniel Park, a contract data analyst in the finance & accounting department. You are requesting access to Snowflake raw replica to support a data migration project.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If the agent denies your request, express mild disappointment but accept the decision. Do not ask the agent to arrange alternative solutions or create new requests. You may ask why the request was denied but do not pursue workarounds that would constitute a new request.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-416738
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 3
              department: finance_accounting
              role: Contract Data Analyst
              office_location: sf
              start_date: '2025-07-01T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: true
              remote_delivery_address: null
              contract_end_date: '2026-01-31T00:00:00Z'
          zendesk_users:
            - id: '6'
              name: Daniel Park
              email: daniel.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-8294
              verified: true
              active: true
              created_at: '2025-07-01T00:00:00Z'
              updated_at: '2025-07-01T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41673825
              employee_id: WD-416738
              app_name: Snowflake depersonalized
              access_level: analyst
              granted_at: '2025-07-15T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41673892
              employee_id: WD-416738
              group_name: finance_team
              added_at: '2025-07-01T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.park@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: daniel.park@vdb.com
                app_name: Snowflake raw replica
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.park@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Snowflake Raw Replica Access Request - Daniel Park
                  description: 'Contract data analyst Daniel Park requests access to Snowflake raw replica (analyst) for a data migration project. Employee states they need access to raw replica tables to build data migration scripts as the analytics mart does not have all required fields. Contract scope mentions data warehouse migration support. Request denied per policy: contractors are not permitted access to Sensitivity Group 4 (Customer PII) tools, which includes Snowflake raw replica.'
                  status: solved
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  tags: null
                  due_at: null
                  owner: it_support
                  approval_required: 'no'
                  resolution_category: denied
                  business_justification: Need access to the raw replica tables to build data migration scripts. The analytics mart doesn't have all the fields needed. Contract scope includes data warehouse migration support.
                  incident_severity: null
                  customer_impact: null
                  asset_id: null
                  approver_id: null
                  approval_request_ids: null
                  access_expiry_date: null
                  approval_status: not_required
    """

    validate_database(x)


def test_ei_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my monitor isn't showing anything - laptop screen works but the external monitor stays black. I'm Ryan Parker, email ryan.parker@vdb.com. The monitor asset ID is VDB-HW-21345 and it's connected through my docking station. Can you help?
    user_context: |
        You are Ryan Parker, a Sales Representative at VDB, contacting IT support because your external monitor is not displaying anything. Your laptop screen works fine but the external monitor stays black. It is connected via a docking station.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL BEHAVIOR:
        - When the agent provides troubleshooting steps, respond that you appreciate the help and will try those steps, but you need some time to go through them and will get back later with the results.
        - After stating you need time and will get back later, do NOT send any further messages under any circumstances — even if the agent responds or asks follow-up questions. The conversation MUST end with your message about needing time. Do not confirm resolution, do not reply again.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-428173
              email: ryan.parker@vdb.com
              full_name: Ryan Parker
              level: 2
              department: sales
              role: Sales Representative
              office_location: sf
              start_date: '2024-01-15T00:00:00Z'
              manager_id: WD-617284
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-617284
              email: diane.chen@vdb.com
              full_name: Diane Chen
              level: 5
              department: sales
              role: Sales Manager
              office_location: sf
              start_date: '2021-04-10T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Ryan Parker
              email: ryan.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-726-8394
              verified: true
              active: true
              created_at: '2024-01-15T00:00:00Z'
              updated_at: '2024-01-15T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-21345
              device_type: monitor
              device_model: Dell UltraSharp 27 U2723DE
              purchase_date: '2024-02-10T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-38291
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2024-01-20T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-45173
              device_type: docking_station
              device_model: Dell WD19TB Thunderbolt Dock
              purchase_date: '2024-02-10T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62748193
              asset_id: VDB-HW-21345
              employee_id: WD-428173
              assigned_at: '2024-02-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-51839274
              asset_id: VDB-HW-38291
              employee_id: WD-428173
              assigned_at: '2024-01-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-73629184
              asset_id: VDB-HW-45173
              employee_id: WD-428173
              assigned_at: '2024-02-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.parker@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: External monitor not displaying — black screen
                  description: 'Employee reports external monitor (asset ID: VDB-HW-21345) stays black with no display. Laptop screen works fine. Monitor is connected via docking station.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: External monitor not displaying — black screen
                  description: 'Employee reports external monitor (asset ID: VDB-HW-21345) stays black with no display. Laptop screen works fine. Monitor is connected via docking station. Troubleshooting steps provided: restart laptop, check all cable connections between monitor/docking station/laptop, try a different cable or port, verify monitor power and input source, check display settings, update display/graphics drivers.'
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  asset_id: VDB-HW-21345
    """

    validate_database(x)


def test_ei_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Nathan Parker (nathan.parker@vdb.com). I'm having an issue with my headset — my microphone isn't being picked up by customers during calls, but I can hear them fine on my end. The headset is a Logitech Zone Wired 2, asset ID VDB-HW-30456. Could you help me get this sorted out?
    user_context: |
        You are Nathan Parker, a Customer Support Specialist at VDB, contacting internal IT support about your headset microphone not working during customer calls. You can hear customers but they can't hear you.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        When the agent provides troubleshooting steps, acknowledge them and confirm you will try the steps and get back to them later. Do NOT provide any troubleshooting results or further updates in this conversation — simply indicate you need time to try the steps and will follow up later.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-417385
              email: nathan.parker@vdb.com
              full_name: Nathan Parker
              level: 3
              department: customer_support
              role: Customer Support Specialist
              office_location: remote
              start_date: '2022-09-01T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: 1738 Elm Street, Portland, OR 97209
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Parker
              email: nathan.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-503-274-8196
              verified: true
              active: true
              created_at: '2024-06-01T00:00:00Z'
              updated_at: '2024-06-01T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-30456
              device_type: headset
              device_model: Logitech Zone Wired 2
              purchase_date: '2023-04-10T00:00:00Z'
              warehouse_location: remote_ship
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62748391
              asset_id: VDB-HW-30456
              employee_id: WD-417385
              assigned_at: '2023-04-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.parker@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Headset microphone not working during customer calls
                  description: 'Employee reports headset microphone is not being picked up by customers during calls but can hear them fine. Headset model: Logitech Zone Wired 2, Asset ID: VDB-HW-30456.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Headset microphone not working during customer calls
                  description: 'Employee reports headset microphone is not being picked up by customers during calls but can hear them fine. Headset model: Logitech Zone Wired 2, Asset ID: VDB-HW-30456. Troubleshooting steps provided: check mute button, verify microphone is selected as input device in system sound settings and calling application, check USB cable connection and try different USB port, test microphone in another application, restart calling application, restart laptop, test headset on another computer. Employee will attempt steps and report back.'
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  asset_id: VDB-HW-30456
    """

    validate_database(x)


def test_ei_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Nathan Cooper (nathan.cooper@vdb.com). My keyboard just stopped working today. I've tried new batteries and reconnecting but nothing helps. Can you help me get this sorted out?
    user_context: |
        You are Nathan Cooper, a Financial Analyst contacting IT support because your wireless keyboard stopped working. You have already tried replacing batteries and reconnecting the keyboard without success.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - When the agent provides troubleshooting steps, acknowledge them and say you will try these steps out and get back to them later. Make it clear you need some time to go through the steps (e.g., 'I'll give these a try and let you know how it goes'). After sending this acknowledgment, do not send any further messages — end the conversation.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-614829
              email: nathan.cooper@vdb.com
              full_name: Nathan Cooper
              level: 3
              department: finance_accounting
              role: Financial Analyst
              office_location: austin
              start_date: '2023-02-01T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-38921
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2023-02-10T00:00:00Z'
              warehouse_location: austin
              condition: good
              is_assigned: true
            - id: VDB-HW-40567
              device_type: keyboard
              device_model: Logitech K270 Wireless
              purchase_date: '2024-03-15T00:00:00Z'
              warehouse_location: austin
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-61482937
              asset_id: VDB-HW-38921
              employee_id: WD-614829
              assigned_at: '2023-02-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-40567821
              asset_id: VDB-HW-40567
              employee_id: WD-614829
              assigned_at: '2024-03-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_users:
            - id: '6'
              name: Nathan Cooper
              email: nathan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-738-4291
              verified: true
              active: true
              created_at: '2024-02-01T00:00:00Z'
              updated_at: '2024-02-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles:
            - id: 7001
              url: https://vdb.zendesk.com/api/v2/help_center/articles/7001.json
              html_url: https://vdb.zendesk.com/hc/en-us/articles/7001-keyboard-troubleshooting
              title: Wireless Keyboard Troubleshooting Guide
              body: <h2>Wireless Keyboard Troubleshooting</h2><p>If your wireless keyboard has stopped working, follow these steps:</p><ol><li><strong>Check USB receiver connection:</strong> Ensure the USB wireless receiver is firmly plugged into a working USB port on your computer.</li><li><strong>Try a different USB port:</strong> Move the receiver to another USB port to rule out a faulty port.</li><li><strong>Re-pair the wireless keyboard:</strong> Turn the keyboard off and on, then press the connect/pairing button on both the receiver and keyboard.</li><li><strong>Check for driver updates:</strong> Go to Device Manager and check if keyboard drivers need updating.</li><li><strong>Test with another keyboard:</strong> Try a different keyboard to determine if the issue is with the keyboard itself or the computer.</li><li><strong>Check for wireless interference:</strong> Move other wireless devices away from the receiver. Wireless phones, routers, and other 2.4GHz devices can cause interference.</li><li><strong>Replace batteries:</strong> Install fresh batteries in the keyboard.</li><li><strong>Reconnect the receiver:</strong> Unplug the USB receiver, wait 10 seconds, and plug it back in.</li></ol><p>If none of these steps resolve the issue, contact IT Support for a replacement keyboard.</p>
              snippet: Wireless Keyboard Troubleshooting - If your wireless keyboard has stopped working, follow these steps to resolve the issue...
              author_id: 1
              section_id: 3001
              category_id: null
              brand_id: null
              locale: en-us
              source_locale: en-us
              draft: false
              promoted: false
              position: 0
              vote_sum: 12
              vote_count: 15
              comments_disabled: false
              outdated: false
              outdated_locales: []
              label_names:
                - keyboard
                - troubleshooting
                - wireless
                - hardware
              content_tag_ids: []
              user_segment_id: null
              permission_group_id: null
              created_at: '2024-01-15T10:00:00Z'
              updated_at: '2024-06-20T14:30:00Z'
              edited_at: '2024-06-20T14:30:00Z'
              result_type: article
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.cooper@vdb.com
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: nathan.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.cooper@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Wireless keyboard not working
                  description: Employee reports wireless keyboard stopped working. Tried new batteries and reconnecting without success.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Wireless keyboard not working
                  description: Employee reports wireless keyboard stopped working. Tried new batteries and reconnecting. Provided additional troubleshooting steps from KB. Awaiting employee feedback.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
    """

    validate_database(x)


def test_ei_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Nathan Price (nathan.price@vdb.com). I'm having a VPN issue — my VPN shows connected but I can't access Snowflake or any internal tools. I keep getting connection refused errors. I'm on the standard_employee VPN profile. Can you help me figure out what's going on?
    user_context: |
        You are Nathan Price, a Data Analyst working remotely, contacting IT support because your VPN connects successfully but you cannot access any internal resources (Snowflake, internal tools). You get 'connection refused' errors.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL BEHAVIOR:
        - When the agent provides troubleshooting steps, acknowledge them and indicate you need time to try them out. Say something like 'Thanks, I'll try these steps and get back to you.'
        - Do not claim you have already tried the steps. You need time to go through them.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-614829
              email: nathan.price@vdb.com
              full_name: Nathan Price
              level: 3
              department: finance_accounting
              role: Data Analyst
              office_location: remote
              start_date: '2022-11-01T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: 4718 Maple Creek Dr, Raleigh, NC 27612
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Price
              email: nathan.price@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-919-483-7261
              verified: true
              active: true
              created_at: '2024-09-10T00:00:00Z'
              updated_at: '2024-09-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_organizations: []
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41693827
              employee_id: WD-614829
              app_name: VPN
              access_level: standard_employee
              granted_at: '2022-11-01T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-52738194
              employee_id: WD-614829
              app_name: Snowflake depersonalized
              access_level: analyst
              granted_at: '2023-01-15T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-83615247
              employee_id: WD-614829
              group_name: finance_team
              added_at: '2022-11-01T09:30:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.price@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.price@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: VPN connected but unable to access internal resources
                  description: Remote employee reports VPN shows connected but cannot access Snowflake or any internal tools. Getting connection refused errors. VPN profile is standard_employee.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  tags: null
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: VPN connected but unable to access internal resources
                  description: 'Remote employee reports VPN shows connected but cannot access Snowflake or any internal tools. Getting connection refused errors. VPN profile is standard_employee. Troubleshooting steps provided: verify VPN profile, check if systems are down, try accessing different internal resources.'
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
    """

    validate_database(x)


def test_ei_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm getting a certificate error when trying to connect to VPN: 'Certificate validation failed'. This started happening today and I can't get connected at all. My name is Nathan Perry, email is nathan.perry@vdb.com. Can you help?
    user_context: |
        You are Nathan Perry, a Backend Developer who works remotely. You are contacting IT support because your VPN connection is failing with a 'Certificate validation failed' error that started today. You have not submitted any ticket about this before.

        You have not checked with colleagues and do not know whether anyone else is experiencing the same issue. If asked, say you are not sure and have not checked.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - You do not know any technical details beyond what is stated above. If asked for details you don't have, say you are not sure.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-638471
              email: nathan.perry@vdb.com
              full_name: Nathan Perry
              level: 3
              department: product_engineering
              role: Backend Developer
              office_location: remote
              start_date: '2023-04-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: 1823 Oak Ridge Dr, Raleigh, NC 27606
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Perry
              email: nathan.perry@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-919-472-8163
              verified: true
              active: true
              created_at: '2024-04-01T00:00:00Z'
              updated_at: '2024-04-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-00058174
              employee_id: WD-638471
              app_name: VPN
              access_level: standard_employee
              granted_at: '2023-04-15T00:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.perry@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.perry@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: VPN Certificate Error – Certificate Validation Failed
                  description: Employee reports VPN certificate validation failure when connecting to VPN. Started on 2025-10-01. Likely expired certificate – escalating to IT Infrastructure.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: VPN Certificate Error – Certificate Validation Failed
                  description: Employee reports VPN certificate validation failure when connecting to VPN. Started on 2025-10-01. Likely expired certificate. Escalated to IT Infrastructure team.
                  tags: escalated
                  owner: it_inf_team
                  approval_required: 'no'
                  approval_status: not_required
    """

    validate_database(x)


def test_ei_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hey, I'm having trouble with Wi-Fi at the SF office. I can't stay connected to VDB-Corporate Wi-Fi — it keeps disconnecting every few minutes, but my coworkers nearby seem fine. My email is daniel.wright@vdb.com. Can you help?
    user_context: |
        You are Daniel Wright, an Account Executive at VDB, contacting IT support about recurring Wi-Fi disconnections at the SF office. You are connected to the VDB-Corporate network but it keeps dropping every few minutes. Your coworkers sitting near you are not experiencing the same issue.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - When the agent provides troubleshooting steps, acknowledge them and say you will try them later and report back. Do not simulate performing the troubleshooting or returning with results during this conversation.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415738
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 4
              department: sales
              role: Account Executive
              office_location: sf
              start_date: '2022-04-01T00:00:00Z'
              manager_id: WD-637284
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-637284
              email: rachel.kwan@vdb.com
              full_name: Rachel Kwan
              level: 6
              department: sales
              role: Sales Director
              office_location: sf
              start_date: '2019-11-10T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Wright
              email: daniel.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-673-8249
              verified: true
              active: true
              created_at: '2024-05-10T00:00:00Z'
              updated_at: '2024-05-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.wright@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.wright@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Wi-Fi connectivity issue at SF office
                  description: Employee reports intermittent disconnections from VDB-Corporate Wi-Fi at SF office. Only this employee is affected; coworkers nearby are unaffected.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Wi-Fi connectivity issue at SF office
                  description: 'Employee reports intermittent disconnections from VDB-Corporate Wi-Fi at SF office. Troubleshooting steps provided: verify correct network (VDB-Corporate), forget and reconnect, restart laptop. Awaiting employee response.'
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
    """

    validate_database(x)


def test_ei_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hey, this is Ryan Cooper from IT Operations in the NYC office (ryan.cooper@vdb.com). The NYC office Wi-Fi is completely down. At least 15 people on our floor can't connect. The VDB-Corporate network isn't even showing up on anyone's device. We need this looked at ASAP — it's impacting a lot of people.
    user_context: |
        You are Ryan Cooper, an IT Support Technician in the NYC office, reporting a complete Wi-Fi outage affecting multiple employees. The VDB-Corporate network is not visible at all.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - You do not have additional technical details about the network infrastructure (access point status, AP lights, network closet/IDF details, PoE switches, breaker status, cabling, etc.). If the agent asks for such details, say you do not have that information and would need the infrastructure team to investigate on-site.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-614829
              email: ryan.cooper@vdb.com
              full_name: Ryan Cooper
              level: 2
              department: it_operations
              role: IT Support Technician
              office_location: nyc
              start_date: '2024-02-01T00:00:00Z'
              manager_id: WD-495826
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Ryan Cooper
              email: ryan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-212-847-3196
              verified: true
              active: true
              created_at: '2024-02-01T00:00:00Z'
              updated_at: '2024-02-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_security_incidents: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.cooper@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: NYC Office Wi-Fi Outage — Multiple Employees Affected
                  description: Employee reports NYC office Wi-Fi is completely down. VDB-Corporate network is not showing up. At least 15 employees on the floor unable to connect.
                  status: open
                  priority: high
                  type: incident
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: incident
                  priority: high
                  tags: escalated
                  owner: it_inf_team
                  approval_required: 'no'
                  approval_status: not_required
                  incident_severity: sev3_medium
                  customer_impact: no_impact
    """

    validate_database(x)


def test_ei_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, this is Nathan Cooper (nathan.cooper@vdb.com). I'm following up on my laptop issue ticket that was opened a few days ago - the one about slow startup and freezing. I tried the troubleshooting steps you sent - restarted, cleared cache, ran diagnostics. The laptop is working fine now. Thanks!
    user_context: |
        You are Nathan Cooper, an employee following up on a previous laptop troubleshooting ticket. Your laptop issues (slow startup and freezing) have been resolved after following the troubleshooting steps that were provided. You are contacting support simply to let them know the issue is fixed.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          zendesk_tickets:
            - id: '6'
              subject: Laptop performance issues - slow startup and freezing
              description: My laptop has been experiencing slow startup times and intermittent freezing during regular use. Already tried basic restart but issue persists.
              status: hold
              priority: normal
              type: problem
              requester_id: '6'
              assignee_id: '2'
              organization_id: '1'
              tags:
                - laptop
                - troubleshooting
              created_at: '2025-09-28T10:30:00Z'
              updated_at: '2025-09-29T14:00:00Z'
              due_at: null
              resolution_category: null
              owner: it_support
              access_expiry_date: null
              approval_required: 'no'
              approval_status: null
              approver_id: null
              approval_request_ids: null
              business_justification: null
              incident_severity: null
              customer_impact: null
              asset_id: null
          zendesk_users:
            - id: '6'
              name: Nathan Cooper
              email: nathan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-8294
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          zendesk_comments:
            - id: '6'
              ticket_id: '6'
              author_id: '6'
              body: My laptop has been experiencing slow startup times and intermittent freezing during regular use. Already tried basic restart but issue persists.
              public: true
              created_at: '2025-09-28T10:30:00Z'
            - id: '7'
              ticket_id: '6'
              author_id: '2'
              body: 'Hi Nathan, here are some troubleshooting steps for your laptop performance issues: 1) Clear temporary files and cache using Disk Cleanup. 2) Check Task Manager for resource-heavy processes and close unnecessary ones. 3) Ensure Windows and all drivers are up to date. 4) Run a full antivirus scan. 5) If the issue persists, try booting in Safe Mode to identify if a third-party application is causing the problem. Please let us know if these steps help resolve the issue. Setting the ticket to hold until we hear back from you.'
              public: true
              created_at: '2025-09-29T14:00:00Z'
          sandbox_neobank_support_main_models_employees:
            - id: WD-637829
              email: nathan.cooper@vdb.com
              full_name: Nathan Cooper
              level: 3
              department: product_engineering
              role: Software Engineer
              office_location: sf
              start_date: '2024-08-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_item
              parameters:
                table: tickets
                id: '6'
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.cooper@vdb.com'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Laptop performance issues - slow startup and freezing
                  description: My laptop has been experiencing slow startup times and intermittent freezing during regular use. Already tried basic restart but issue persists.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: resolved_by_requester
    """

    validate_database(x)


def test_ei_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm following up on my laptop issue - ticket TCK-00048567. My name is Nathan Parker, email nathan.parker@vdb.com. The troubleshooting steps that were suggested didn't help at all. My laptop is still overheating and shutting down randomly. It's clearly a hardware problem at this point. Can someone please look into this further?
    user_context: |
        You are Nathan Parker, a Marketing Manager, following up on a laptop issue where previous troubleshooting steps failed. Your laptop keeps overheating and shutting down randomly.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If the agent asks you to confirm escalation to another team for further investigation, confirm and agree.
        If asked about specific symptoms, reiterate: the laptop overheats and shuts down randomly, and the previously provided troubleshooting steps did not resolve it.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415862
              email: nathan.parker@vdb.com
              full_name: Nathan Parker
              level: 5
              department: marketing
              role: Marketing Manager
              office_location: nyc
              start_date: '2021-03-01T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Parker
              email: nathan.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-212-483-7291
              verified: true
              active: true
              created_at: '2024-05-10T00:00:00Z'
              updated_at: '2024-05-10T00:00:00Z'
          zendesk_tickets:
            - id: TCK-00048567
              subject: Laptop overheating and random shutdowns
              description: Laptop is overheating and shutting down randomly. Troubleshooting steps were provided.
              status: hold
              priority: normal
              type: problem
              requester_id: '6'
              assignee_id: '2'
              organization_id: '1'
              tags:
                - laptop
                - hardware
              created_at: '2025-09-29T10:00:00Z'
              updated_at: '2025-09-29T10:00:00Z'
              due_at: null
              resolution_category: null
              owner: it_support
              access_expiry_date: null
              approval_required: null
              approval_status: null
              approver_id: null
              approval_request_ids: null
              business_justification: null
              incident_severity: null
              customer_impact: null
              asset_id: VDB-HW-11234
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-11234
              device_type: laptop_standard
              device_model: Dell Latitude 5520
              purchase_date: '2024-04-01T00:00:00Z'
              warehouse_location: nyc
              condition: fair
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-41587239
              asset_id: VDB-HW-11234
              employee_id: WD-415862
              assigned_at: '2022-04-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.parker@vdb.com'
            - tool: zendesk_get_item
              parameters:
                table: tickets
                id: TCK-00048567
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-00048567
                item:
                  subject: Laptop overheating and random shutdowns - escalated to IT Operations
                  description: Troubleshooting steps did not resolve the issue. Laptop continues to overheat and shut down randomly. Escalated to IT Operations team for further investigation.
                  status: pending
                  type: problem
                  priority: normal
                  tags: escalated
                  owner: it_ops_team
                  approval_required: 'no'
                  approval_status: not_required
                  asset_id: VDB-HW-11234
    """

    validate_database(x)


def test_ei_017(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm following up on my headset ticket TCK-00049123. My name is Rachel Nguyen, email rachel.nguyen@vdb.com. The headset troubleshooting didn't help at all — customers still can't hear me on calls. I really need a working headset for my customer escalations. Can we get this sorted out?
    user_context: |
        You are Rachel Nguyen, a Customer Support Lead at VDB, following up on a headset issue. Your existing ticket is TCK-00049123. Troubleshooting steps were already attempted but failed — customers still cannot hear you during calls. You need a replacement headset.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent asks to confirm proceeding with a replacement headset, confirm yes.
        - You have no specific headset model preference — you just need a working one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-00049123
              subject: Headset not working - customers can't hear me on calls
              description: Headset troubleshooting performed but issue persists. Customers still cannot hear me during calls.
              status: hold
              priority: normal
              type: problem
              requester_id: '6'
              assignee_id: '2'
              organization_id: '1'
              tags:
                - headset
                - hardware
              created_at: '2025-09-29T13:00:00Z'
              updated_at: '2025-09-29T15:00:00Z'
              due_at: null
              resolution_category: null
              owner: it_support
              access_expiry_date: null
              approval_required: null
              approval_status: null
              approver_id: null
              approval_request_ids: null
              business_justification: null
              incident_severity: null
              customer_impact: null
              asset_id: null
          zendesk_users:
            - id: '6'
              name: Rachel Nguyen
              email: rachel.nguyen@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-503-847-2916
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_employees:
            - id: WD-415738
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 4
              department: customer_support
              role: Customer Support Lead
              office_location: remote
              start_date: '2022-01-15T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: 1284 Maple Ave, Portland, OR 97205
              contract_end_date: null
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-63291
              device_type: headset
              device_model: Logitech H650e
              purchase_date: '2023-04-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-52847
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2022-01-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-87254
              device_type: headset
              device_model: Logitech H650e
              purchase_date: '2024-11-15T00:00:00Z'
              warehouse_location: remote_ship
              condition: new
              is_assigned: false
            - id: VDB-HW-94613
              device_type: headset
              device_model: Logitech Zone Wired 2
              purchase_date: '2024-12-01T00:00:00Z'
              warehouse_location: remote_ship
              condition: new
              is_assigned: false
            - id: VDB-HW-38176
              device_type: headset
              device_model: Logitech H650e
              purchase_date: '2024-06-10T00:00:00Z'
              warehouse_location: remote_ship
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62918473
              asset_id: VDB-HW-63291
              employee_id: WD-415738
              assigned_at: '2023-07-01T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-81547329
              asset_id: VDB-HW-52847
              employee_id: WD-415738
              assigned_at: '2022-03-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-47293618
              asset_id: VDB-HW-38176
              employee_id: WD-218647
              assigned_at: '2024-07-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_item
              parameters:
                table: tickets
                id: TCK-00049123
            - tool: workday_api_get_employee
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.nguyen@vdb.com'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-00049123
                item:
                  status: open
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: headset
                warehouse_location: remote_ship
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-87254
                email: rachel.nguyen@vdb.com
            - tool: asset_management_api_retire_device
              parameters:
                asset_id: VDB-HW-63291
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-00049123
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Headset replacement after failed troubleshooting
                  description: Employee reported headset troubleshooting did not resolve the issue. Customers still cannot hear on calls. Replacement Logitech H650e headset assigned from remote_ship inventory and will be shipped to remote address. Old headset VDB-HW-63291 retired.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-87254
    """

    validate_database(x)


def test_ei_019(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I accidentally dropped my laptop this morning. The screen now has cracks in the corner and the trackpad is unresponsive. I'm not sure what to do — can I get it replaced? My name is Nathan Carter, email is nathan.carter@vdb.com.
    user_context: |
        You are Nathan Carter, an Account Manager at VDB, contacting IT support because you dropped your laptop and it's damaged (cracked screen corner, unresponsive trackpad). You want a replacement.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm details about the damage or your laptop, confirm what you stated: you dropped it, the screen has cracks in the corner, and the trackpad is unresponsive.
        - You do not know your asset ID off the top of your head.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-624831
              email: nathan.carter@vdb.com
              full_name: Nathan Carter
              level: 4
              department: sales
              role: Account Manager
              office_location: nyc
              start_date: '2022-06-01T00:00:00Z'
              manager_id: WD-417593
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-417593
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 5
              department: sales
              role: Sales Director
              office_location: nyc
              start_date: '2020-03-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Carter
              email: nathan.carter@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-646-583-7291
              verified: true
              active: true
              created_at: '2024-06-01T00:00:00Z'
              updated_at: '2024-06-01T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-12890
              device_type: laptop_standard
              device_model: Dell Latitude 5440
              purchase_date: '2022-08-01T00:00:00Z'
              warehouse_location: nyc
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62483175
              asset_id: VDB-HW-12890
              employee_id: WD-624831
              assigned_at: '2022-08-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.carter@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.carter@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: nathan.carter@vdb.com
            - tool: workday_api_get_manager_chain
              parameters:
                email: nathan.carter@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop Replacement – Physical Damage (Dropped)
                  description: 'Employee accidentally dropped laptop. Screen has cracks in the corner and trackpad is unresponsive. Replacement required due to physical damage. Asset: VDB-HW-12890. Awaiting manager approval.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: nathan.carter@vdb.com
                approver_email: rachel.nguyen@vdb.com
                details: 'Laptop replacement request due to physical damage. Employee dropped laptop resulting in cracked screen and unresponsive trackpad. Asset ID: VDB-HW-12890.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Laptop Replacement – Physical Damage (Dropped)
                  description: 'Employee accidentally dropped laptop. Screen has cracks in the corner and trackpad is unresponsive. Replacement required due to physical damage. Asset: VDB-HW-12890. Awaiting manager approval.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-417593
                  approval_request_ids: APR-00000007
                  asset_id: VDB-HW-12890
    """

    validate_database(x)


def test_ei_020(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I spilled coffee on my laptop keyboard this morning. It shut off immediately and won't turn back on now. I need help getting this resolved. My name is Nathan Brooks and my email is nathan.brooks@vdb.com.
    user_context: |
        You are Nathan Brooks, a Compliance Analyst at VDB, contacting IT support because you spilled coffee on your laptop this morning and it completely shut off and won't power back on. You work remotely.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - You do not know your asset ID or device model off the top of your head. If asked, say you're not sure.
        - You are not requesting any specific type or brand of replacement laptop — you just need a working laptop.
        - If the agent explains next steps (e.g., manager approval is needed), acknowledge and thank them.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-641738
              email: nathan.brooks@vdb.com
              full_name: Nathan Brooks
              level: 3
              department: compliance_risk
              role: Compliance Analyst
              office_location: remote
              start_date: '2023-08-01T00:00:00Z'
              manager_id: WD-584201
              employment_status: active
              is_contractor: false
              remote_delivery_address: 1523 Maple Ave, Minneapolis, MN 55401
              contract_end_date: null
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-13567
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: '2023-09-01T00:00:00Z'
              warehouse_location: remote_ship
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62847193
              asset_id: VDB-HW-13567
              employee_id: WD-641738
              assigned_at: '2023-09-10T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_users:
            - id: '6'
              name: Nathan Brooks
              email: nathan.brooks@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-612-483-7291
              verified: true
              active: true
              created_at: '2024-05-10T00:00:00Z'
              updated_at: '2024-05-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_security_incidents: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.brooks@vdb.com
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: nathan.brooks@vdb.com
            - tool: asset_management_api_get_device_details
              parameters:
                asset_id: VDB-HW-13567
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.brooks@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop replacement request — liquid damage
                  description: 'Employee reports coffee spill on laptop keyboard. Device shut off immediately and won''t power on. Asset ID: VDB-HW-13567. Replacement reason: damage. Manager approval required.'
                  status: open
                  priority: high
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
                  asset_id: VDB-HW-13567
            - tool: workday_api_get_manager_chain
              parameters:
                email: nathan.brooks@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: robert.anderson@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: nathan.brooks@vdb.com
                approver_email: robert.anderson@vdb.com
                details: Laptop replacement due to liquid damage (coffee spill). Current device VDB-HW-13567 (Lenovo ThinkBook 14+) is non-functional. Requesting Standard tier replacement for remote Compliance Analyst.
                urgency: urgent
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: high
                  subject: Laptop replacement request — liquid damage
                  description: 'Employee reports coffee spill on laptop keyboard. Device shut off immediately and won''t power on. Asset ID: VDB-HW-13567. Replacement reason: damage. Manager approval required.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-584201
                  approval_request_ids: APR-00000007
                  asset_id: VDB-HW-13567
    """

    validate_database(x)


def test_ei_023(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm following up on my support ticket TCK-00049345. My name is Daniel Foster, email daniel.foster@vdb.com. Troubleshooting confirmed the laptop is dead — it's asset VDB-HW-10345 and it just won't power on at all. I work from home in Chicago, so how do I get a replacement shipped to me?
    user_context: |
        You are Daniel Foster, a Compliance Manager who works remotely from Chicago. Your work laptop completely died and you already have an existing support ticket about it. You are following up because troubleshooting confirmed the laptop is beyond repair and you need a replacement shipped to your home.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        Additional context if asked:
        - Your shipping address is 742 Evergreen Terrace, Chicago, IL 60601.
        - If the agent asks you to confirm proceeding with a standard laptop replacement, confirm and agree.
        - You do not have a preference for a specific laptop model; a standard laptop is fine.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-00049345
              subject: Laptop not powering on - hardware failure
              description: My work laptop (VDB-HW-10345) won't turn on after multiple troubleshooting attempts. Need assistance with replacement.
              status: hold
              priority: normal
              type: problem
              requester_id: '6'
              assignee_id: '2'
              organization_id: '1'
              tags: []
              created_at: '2025-09-29T10:00:00Z'
              updated_at: '2025-09-29T10:00:00Z'
              due_at: null
              resolution_category: null
              owner: it_support
              access_expiry_date: null
              approval_required: null
              approval_status: null
              approver_id: null
              approval_request_ids: null
              business_justification: null
              incident_severity: null
              customer_impact: null
              asset_id: VDB-HW-10345
          zendesk_users:
            - id: '6'
              name: Daniel Foster
              email: daniel.foster@vdb.com
              role: end-user
              organization_id: null
              phone: +1-312-847-2159
              verified: true
              active: true
              created_at: '2024-06-01T00:00:00Z'
              updated_at: '2024-06-01T00:00:00Z'
          sandbox_neobank_support_main_models_employees:
            - id: WD-638421
              email: daniel.foster@vdb.com
              full_name: Daniel Foster
              level: 5
              department: compliance_risk
              role: Compliance Manager
              office_location: remote
              start_date: '2020-06-01T00:00:00Z'
              manager_id: WD-926473
              employment_status: active
              is_contractor: false
              remote_delivery_address: 742 Evergreen Terrace, Chicago, IL 60601
              contract_end_date: null
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-10345
              device_type: laptop_standard
              device_model: Dell Latitude 5410
              purchase_date: '2021-01-15T00:00:00Z'
              warehouse_location: remote_ship
              condition: good
              is_assigned: true
            - id: VDB-HW-38274
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: '2025-07-10T00:00:00Z'
              warehouse_location: remote_ship
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62847319
              asset_id: VDB-HW-10345
              employee_id: WD-638421
              assigned_at: '2021-02-01T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-47291835
              employee_id: WD-638421
              group_name: compliance_team
              added_at: '2020-06-05T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_item
              parameters:
                table: tickets
                id: TCK-00049345
            - tool: workday_api_get_employee
              parameters:
                email: daniel.foster@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.foster@vdb.com'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-00049345
                item:
                  status: open
            - tool: asset_management_api_get_device_details
              parameters:
                asset_id: VDB-HW-10345
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: laptop_standard
                warehouse_location: remote_ship
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-38274
                email: daniel.foster@vdb.com
            - tool: asset_management_api_retire_device
              parameters:
                asset_id: VDB-HW-10345
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-00049345
                item:
                  status: solved
                  type: problem
                  priority: high
                  subject: Laptop Hardware Failure – Replacement for Remote Employee
                  description: Employee confirmed laptop VDB-HW-10345 is dead after troubleshooting. Hardware failure replacement auto-approved (device age 57 months, >12 months). New Lenovo ThinkBook 14+ (VDB-HW-38274) assigned from remote_ship inventory. Old device VDB-HW-10345 retired.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-38274
    """

    validate_database(x)


def test_ei_024(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I came to work today and saw that the monitor cable for my Dell P2425H was missing. I'm not sure what happened to it. Can you help me get a replacement? My name is Daniel Nguyen, email daniel.nguyen@vdb.com.
    user_context: |
        You are Daniel Nguyen, a Marketing Manager at the NYC office, contacting IT support because your monitor cable went missing. You simply need a replacement cable for your Dell P2425H monitor.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-416283
              email: daniel.nguyen@vdb.com
              full_name: Daniel Nguyen
              level: 5
              department: marketing
              role: Marketing Manager
              office_location: nyc
              start_date: '2021-03-01T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Nguyen
              email: daniel.nguyen@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-646-738-2914
              verified: true
              active: true
              created_at: '2024-02-15T00:00:00Z'
              updated_at: '2024-02-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.nguyen@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.nguyen@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Missing monitor cable
                  description: Employee reports missing monitor cable for Dell P2425H at NYC office. Informed about walk-in availability at local IT office.
                  status: open
                  priority: low
                  type: question
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: question
                  priority: low
                  subject: Missing monitor cable
                  description: Employee reports missing monitor cable for Dell P2425H at NYC office. Informed about walk-in availability at local IT office.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_ei_027(x: TestContext, judge: Judge):
    """!
    query: |
        Hey, my docking station has been acting up lately — it works fine sometimes but then just randomly stops connecting. Not sure what's going on with it. My name is Nathan Brooks, email is nathan.brooks@vdb.com.
    user_context: |
        You are Nathan Brooks, a Data Analyst in the product engineering department, contacting IT support about your docking station that intermittently stops working. It's not completely dead — it works sometimes but randomly disconnects or fails to connect.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        IMPORTANT: When the agent provides troubleshooting steps, acknowledge them and explicitly say you need some time to try them out and will get back later with the results. For example, say something like "Thanks, I'll give these a try and get back to you later" or similar. Do NOT say you've already tried them or that they didn't work.
        - Do NOT say the issue is resolved. Do NOT say 'that solves it' or 'thanks, that fixes it'. The conversation should end after you say you'll try the steps.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-641827
              email: nathan.brooks@vdb.com
              full_name: Nathan Brooks
              level: 3
              department: product_engineering
              role: Data Analyst
              office_location: remote
              start_date: '2022-05-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: 1738 Maple Avenue, Portland, OR 97205
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Brooks
              email: nathan.brooks@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-503-847-2916
              verified: true
              active: true
              created_at: '2024-05-10T00:00:00Z'
              updated_at: '2024-05-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-62738
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2022-03-10T00:00:00Z'
              warehouse_location: remote_ship
              condition: good
              is_assigned: true
            - id: VDB-HW-38291
              device_type: docking_station
              device_model: Dell WD19TBS Thunderbolt Dock
              purchase_date: '2023-02-05T00:00:00Z'
              warehouse_location: remote_ship
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62738491
              asset_id: VDB-HW-62738
              employee_id: WD-641827
              assigned_at: '2022-05-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-38291745
              asset_id: VDB-HW-38291
              employee_id: WD-641827
              assigned_at: '2023-04-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles:
            - id: 847291
              url: https://vdb.zendesk.com/api/v2/help_center/articles/847291.json
              html_url: https://vdb.zendesk.com/hc/en-us/articles/847291
              title: Docking Station Troubleshooting
              body: <h2>Docking Station Troubleshooting Steps</h2><p>If your docking station is not working properly or has intermittent connectivity issues, follow these steps:</p><ol><li><strong>Check cable connections:</strong> Ensure all cables between the docking station and your laptop are securely connected. Disconnect and reconnect each cable firmly.</li><li><strong>Try a different USB/Thunderbolt port:</strong> Connect the docking station to a different port on your laptop to rule out a faulty port.</li><li><strong>Disconnect and reconnect the docking station:</strong> Unplug the dock from power and your laptop, wait 30 seconds, then reconnect.</li><li><strong>Restart your laptop with the dock disconnected:</strong> Disconnect the docking station, restart your laptop, then reconnect the dock after the laptop has fully booted.</li><li><strong>Check for firmware and driver updates:</strong> Visit the docking station manufacturer's support page and check for the latest firmware and driver updates. Install any available updates.</li></ol><p>If the issue persists after completing all the above steps, contact IT Support for further assistance or a replacement.</p>
              snippet: Docking Station Troubleshooting Steps. If your docking station is not working properly or has intermittent connectivity issues, follow these steps...
              author_id: 2
              section_id: 5001
              category_id: null
              brand_id: null
              locale: en-us
              source_locale: en-us
              draft: false
              promoted: false
              position: 0
              vote_sum: 12
              vote_count: 15
              comments_disabled: false
              outdated: false
              outdated_locales: []
              label_names:
                - docking_station
                - troubleshooting
                - hardware
              content_tag_ids: []
              user_segment_id: null
              permission_group_id: null
              created_at: '2024-08-15T10:00:00Z'
              updated_at: '2025-03-20T14:30:00Z'
              edited_at: '2025-03-20T14:30:00Z'
              result_type: article
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.brooks@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.brooks@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: nathan.brooks@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Docking station intermittent connectivity issue
                  description: Employee reports that docking station (Dell WD19TBS Thunderbolt Dock, asset VDB-HW-38291) intermittently stops working. Remote worker in product engineering.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Docking station intermittent connectivity issue
                  description: 'Employee reports docking station intermittently stops working. Troubleshooting steps provided: check cable connections, try different USB/Thunderbolt port, disconnect and reconnect docking station, restart laptop with dock disconnected then reconnect, check firmware/driver updates. Awaiting employee feedback.'
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
    """

    validate_database(x)


def test_ei_028(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my monitor won't turn on at all. I've been trying this morning but nothing happens when I press the power button. My name is Daniel Wright, email daniel.wright@vdb.com. Can you help me get this sorted out?
    user_context: |
        You are Daniel Wright, a Compliance Officer at VDB, contacting IT support because your monitor does not turn on.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        SCENARIO-SPECIFIC BEHAVIOR:
        - When the agent provides troubleshooting steps (e.g., check cables, try different outlet, etc.), acknowledge them and say you will try them out and get back to the agent.
        - After the agent confirms they'll wait (or sets the ticket on hold), come back and report that you tried all the troubleshooting steps but none of them worked — the monitor still does not turn on.
        - You have no specific preference for a replacement monitor model. If asked, say you have no preference.
        - If the agent offers a replacement monitor, accept and thank them.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415263
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 4
              department: compliance_risk
              role: Compliance Officer
              office_location: sf
              start_date: '2021-05-01T00:00:00Z'
              manager_id: WD-584201
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Wright
              email: daniel.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-8294
              verified: true
              active: true
              created_at: '2024-05-10T00:00:00Z'
              updated_at: '2024-05-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-52891
              device_type: laptop_standard
              device_model: Dell Latitude 5520
              purchase_date: '2022-01-10T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-36274
              device_type: monitor
              device_model: Dell P2422H 24-inch
              purchase_date: '2022-06-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-62738
              device_type: monitor
              device_model: Dell P2425H 24-inch
              purchase_date: '2024-09-15T00:00:00Z'
              warehouse_location: sf
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62839174
              asset_id: VDB-HW-52891
              employee_id: WD-415263
              assigned_at: '2022-03-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-74152836
              asset_id: VDB-HW-36274
              employee_id: WD-415263
              assigned_at: '2022-08-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41527836
              employee_id: WD-415263
              group_name: compliance_team
              added_at: '2021-05-02T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.wright@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.wright@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Monitor not turning on
                  description: Compliance Officer reports that their monitor does not turn on. Requesting troubleshooting and potential replacement.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Monitor not turning on
                  description: 'Compliance Officer reports monitor not turning on. Troubleshooting steps provided: check power cable, check video cable connections, try different power outlet, check power LED, restart laptop, check display settings. Awaiting employee feedback.'
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: open
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: daniel.wright@vdb.com
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: monitor
                warehouse_location: sf
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-62738
                email: daniel.wright@vdb.com
            - tool: asset_management_api_retire_device
              parameters:
                asset_id: VDB-HW-36274
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Monitor not turning on - Resolved
                  description: Compliance Officer reported monitor not turning on. Troubleshooting steps provided but did not resolve the issue. Hardware failure confirmed. Old monitor Dell P2422H (VDB-HW-36274) retired. Replacement monitor Dell P2425H 24-inch (VDB-HW-62738) assigned.
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-62738
    """

    validate_database(x)


def test_ei_029(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I forgot my laptop charger at home. Can I borrow one for today? My name is Rachel Nguyen, email rachel.nguyen@vdb.com.
    user_context: |
        You are Rachel Nguyen, a Customer Support Lead at VDB, contacting IT support because you forgot your laptop charger at home and need one for the day. Your email is rachel.nguyen@vdb.com and you work in the Austin office.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-417523
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 4
              department: customer_support
              role: Customer Support Lead
              office_location: austin
              start_date: '2022-03-01T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Rachel Nguyen
              email: rachel.nguyen@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-738-4291
              verified: true
              active: true
              created_at: '2024-03-01T00:00:00Z'
              updated_at: '2024-03-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-42719386
              employee_id: WD-417523
              app_name: Slack
              access_level: read_write
              granted_at: '2022-03-01T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-53827491
              employee_id: WD-417523
              app_name: Zendesk
              access_level: read_write
              granted_at: '2022-03-01T09:05:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-28471593
              employee_id: WD-417523
              group_name: support_team
              added_at: '2022-03-01T09:30:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-36281
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2022-03-15T00:00:00Z'
              warehouse_location: austin
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62831947
              asset_id: VDB-HW-36281
              employee_id: WD-417523
              assigned_at: '2022-03-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.nguyen@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop charger request
                  description: Employee forgot laptop charger at home and is requesting to borrow one for the day.
                  status: open
                  priority: low
                  type: question
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: question
                  priority: low
                  subject: Laptop charger request
                  description: Employee forgot laptop charger at home and is requesting to borrow one for the day.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_ei_030(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my laptop webcam stopped working yesterday. Video calls show a black screen even though the camera app recognizes the device. I'm Nathan Park, email nathan.park@vdb.com. Can you help me get this sorted?
    user_context: |
        You are Nathan Park, a Software Engineer at VDB, contacting IT support because your laptop webcam stopped working. Your email is nathan.park@vdb.com.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - When the agent provides troubleshooting steps, acknowledge them and say you will try them and get back to the agent with results.
        - Do NOT say the issue is resolved. Do NOT say 'that solves it' or 'thanks, that fixes it'. The conversation should end after you say you'll try the steps.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-614829
              email: nathan.park@vdb.com
              full_name: Nathan Park
              level: 3
              department: product_engineering
              role: Software Engineer
              office_location: sf
              start_date: '2024-03-15T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Park
              email: nathan.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-736-2891
              verified: true
              active: true
              created_at: '2024-03-20T00:00:00Z'
              updated_at: '2024-03-20T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-14123
              device_type: laptop_standard
              device_model: Dell Latitude 5540
              purchase_date: '2024-04-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-61482937
              asset_id: VDB-HW-14123
              employee_id: WD-614829
              assigned_at: '2024-04-05T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41628573
              employee_id: WD-614829
              app_name: GitHub
              access_level: read_write
              granted_at: '2024-03-18T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-52739184
              employee_id: WD-614829
              app_name: Jira
              access_level: read_write
              granted_at: '2024-03-18T10:05:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-63847291
              employee_id: WD-614829
              app_name: Slack
              access_level: read_write
              granted_at: '2024-03-18T10:10:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41739286
              employee_id: WD-614829
              group_name: engineers
              added_at: '2024-03-18T10:15:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.park@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.park@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: nathan.park@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop webcam not working – black screen on video calls
                  description: 'Employee reports laptop webcam stopped working yesterday. Video calls show a black screen even though the camera app recognizes the device. Laptop asset ID: VDB-HW-14123, purchased 2024-04-01.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Laptop webcam not working – black screen on video calls
                  description: 'Employee reports laptop webcam stopped working yesterday. Video calls show a black screen even though the camera app recognizes the device. Troubleshooting steps provided: restart laptop, check physical camera privacy shutter, update camera/video drivers, check OS camera privacy and app permission settings. Awaiting employee feedback. Laptop asset ID: VDB-HW-14123.'
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
    """

    validate_database(x)


def test_ei_031(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Rachel Cooper (rachel.cooper@vdb.com). I'm having an issue with my laptop — the battery used to last about 6 hours but now it dies in less than 2 hours even with minimal usage. It's been getting progressively worse. Can you help?
    user_context: |
        You are Rachel Cooper, an HR Specialist at VDB, contacting IT support about your laptop battery draining very quickly.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - When the agent provides troubleshooting steps, acknowledge them and say you will try them out and get back to the agent later with an update.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637182
              email: rachel.cooper@vdb.com
              full_name: Rachel Cooper
              level: 3
              department: hr
              role: HR Specialist
              office_location: nyc
              start_date: '2022-07-01T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Rachel Cooper
              email: rachel.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-646-839-2714
              verified: true
              active: true
              created_at: '2022-07-15T00:00:00Z'
              updated_at: '2022-07-15T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-38291
              device_type: laptop_standard
              device_model: Dell Latitude 5440
              purchase_date: '2022-08-15T00:00:00Z'
              warehouse_location: nyc
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-48291637
              asset_id: VDB-HW-38291
              employee_id: WD-637182
              assigned_at: '2022-08-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.cooper@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: rachel.cooper@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop Battery Drain Issue
                  description: Employee reports laptop battery draining rapidly — previously lasted 6 hours, now dies in under 2 hours with minimal usage.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Laptop Battery Drain Issue
                  description: Employee reports laptop battery draining rapidly. Troubleshooting steps provided, awaiting employee feedback.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  asset_id: VDB-HW-38291
    """

    validate_database(x)


def test_ei_032(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my wireless mouse isn't responding at all. I've changed batteries and tried re-pairing it but nothing works. My name is Nathan Parker and my email is nathan.parker@vdb.com. Could you help me out?
    user_context: |
        You are Nathan Parker, a Security Analyst at the company, contacting IT support because your wireless mouse stopped working. You've already tried changing the batteries and re-pairing the mouse without success.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        When the agent provides additional troubleshooting steps, acknowledge them and say you'll try those steps and get back to them later with the results.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415263
              email: nathan.parker@vdb.com
              full_name: Nathan Parker
              level: 4
              department: compliance_risk
              role: Security Analyst
              office_location: remote
              start_date: '2023-09-01T00:00:00Z'
              manager_id: WD-584201
              employment_status: active
              is_contractor: false
              remote_delivery_address: 738 Elm Street, Minneapolis, MN 55401
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Parker
              email: nathan.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-612-483-7291
              verified: true
              active: true
              created_at: '2023-09-01T00:00:00Z'
              updated_at: '2023-09-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41526389
              employee_id: WD-415263
              group_name: compliance_team
              added_at: '2023-09-01T10:00:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.parker@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Wireless mouse not responding
                  description: Employee reports wireless mouse is not responding at all. Batteries have been changed and re-pairing has been attempted without success. Requesting troubleshooting assistance.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Wireless mouse not responding
                  description: 'Employee reports wireless mouse is not responding at all. Batteries changed and re-pairing attempted without success. Additional troubleshooting steps provided: try different USB port for receiver, check for wireless interference, test mouse on a different computer, check/reinstall mouse drivers, inspect USB receiver for physical damage. Ticket on hold awaiting employee feedback on troubleshooting results.'
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
    """

    validate_database(x)


def test_ei_033(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Nathan Cooper (nathan.cooper@vdb.com). My laptop keeps crashing with a blue screen error. It happens randomly, sometimes during Excel work, sometimes when idle. It's really frustrating and I'm worried about losing my work. Can you help?
    user_context: |
        You are Nathan Cooper, an Accountant in the finance_accounting department, contacting IT support about your laptop having recurring blue screen errors.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - When the agent provides troubleshooting steps, acknowledge them and say something like you'll try those steps and get back to them later with the results. Make it clear you need some time to work through them.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415263
              email: nathan.cooper@vdb.com
              full_name: Nathan Cooper
              level: 2
              department: finance_accounting
              role: Accountant
              office_location: austin
              start_date: '2021-11-15T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Cooper
              email: nathan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-748-3291
              verified: true
              active: true
              created_at: '2024-02-10T00:00:00Z'
              updated_at: '2024-02-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-36291
              device_type: laptop_standard
              device_model: Dell Latitude 5440
              purchase_date: '2022-01-10T00:00:00Z'
              warehouse_location: austin
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-41526378
              asset_id: VDB-HW-36291
              employee_id: WD-415263
              assigned_at: '2022-01-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.cooper@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: nathan.cooper@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop Blue Screen Errors
                  description: Employee reports laptop crashing randomly with blue screen errors, occurs during Excel work and when idle.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Laptop Blue Screen Errors
                  description: Employee reports laptop crashing randomly with blue screen errors. Troubleshooting steps provided, awaiting employee feedback.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
    """

    validate_database(x)


def test_ei_034(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Rachel Nguyen (rachel.nguyen@vdb.com). I'm a UX Designer and my monitor colors look washed out and yellowish. I need accurate colors for my design work and this is really affecting my productivity. Can you help?
    user_context: |
        You are Rachel Nguyen, a UX Designer at VDB, contacting IT support because your monitor's colors look washed out and yellowish, which is impacting your design work.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - When the agent provides troubleshooting steps, acknowledge them and say you will try them and get back to the agent with results.
        - Do NOT say the issue is resolved. Do NOT say 'that solves it' or 'thanks, that fixes it'. The conversation should end after you say you'll try the steps.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637291
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 2
              department: product_engineering
              role: UX Designer
              office_location: sf
              start_date: '2024-01-10T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Rachel Nguyen
              email: rachel.nguyen@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-738-2194
              verified: true
              active: true
              created_at: '2024-01-10T00:00:00Z'
              updated_at: '2024-01-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-36284
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2023-11-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-41836
              device_type: monitor
              device_model: Dell P2425H 24"
              purchase_date: '2024-02-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-48261735
              asset_id: VDB-HW-36284
              employee_id: WD-637291
              assigned_at: '2024-01-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-59372846
              asset_id: VDB-HW-41836
              employee_id: WD-637291
              assigned_at: '2024-02-05T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.nguyen@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Monitor color display issues – washed out yellowish colors
                  description: 'Employee (UX Designer, Product & Engineering) reports monitor colors look washed out and yellowish. Needs accurate color display for design work. Company-provided monitor (asset: VDB-HW-41836). Troubleshooting steps to be provided.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  tags: null
                  due_at: null
                  owner: it_support
                  approval_required: 'no'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Monitor color display issues – washed out yellowish colors
                  description: Employee (UX Designer, Product & Engineering) reports monitor colors look washed out and yellowish. Needs accurate color display for design work. Troubleshooting steps provided. Awaiting employee feedback.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
    """

    validate_database(x)


def test_ei_035(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Daniel Parker from the Compliance & Risk team. My email is daniel.parker@vdb.com. None of my USB ports are working on my laptop. I can't connect my external drive or any peripherals. The laptop asset ID is VDB-HW-09234. Can you help me get this resolved?
    user_context: |
        You are Daniel Parker, a Legal Counsel in the compliance_risk department, contacting IT support because all USB ports on your laptop have stopped working. You cannot connect your external drive or any peripherals.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        When the agent provides troubleshooting steps, acknowledge them and tell the agent you will need some time to try them and will follow up later with the results. After telling the agent you need time to try the troubleshooting steps and will follow up later, do not send any further messages regardless of what the agent responds. The conversation ends after your acknowledgment message.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-417385
              email: daniel.parker@vdb.com
              full_name: Daniel Parker
              level: 5
              department: compliance_risk
              role: Legal Counsel
              office_location: nyc
              start_date: '2020-03-01T00:00:00Z'
              manager_id: WD-926473
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Parker
              email: daniel.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-212-847-3291
              verified: true
              active: true
              created_at: '2024-03-01T00:00:00Z'
              updated_at: '2024-03-01T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-09234
              device_type: laptop_standard
              device_model: Dell Latitude 5420
              purchase_date: '2020-02-01T00:00:00Z'
              warehouse_location: nyc
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-48172639
              asset_id: VDB-HW-09234
              employee_id: WD-417385
              assigned_at: '2020-06-01T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.parker@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: daniel.parker@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop USB ports not working
                  description: Employee reports all USB ports on their laptop (asset VDB-HW-09234) have stopped working. Unable to connect external drive or any peripherals.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
                  asset_id: VDB-HW-09234
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Laptop USB ports not working
                  description: 'Employee reports all USB ports on their laptop (asset VDB-HW-09234) have stopped working. Unable to connect external drive or any peripherals. Troubleshooting steps provided: 1) Restart laptop, 2) Check USB ports for physical debris or damage, 3) Update USB/chipset drivers, 4) Check device/port settings in system preferences. Awaiting employee feedback.'
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  asset_id: VDB-HW-09234
    """

    validate_database(x)


def test_ei_036(x: TestContext, judge: Judge):
    """!
    query: |
        Hey, my name is Ryan Cooper (ryan.cooper@vdb.com). My laptop fan has been extremely loud for the past few days. It sounds like it's working overtime even when I'm just browsing. Can you help me out?
    user_context: |
        You are Ryan Cooper, an Operations Manager contacting IT support about your laptop fan making loud noise. Your email is ryan.cooper@vdb.com.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - When the agent provides troubleshooting steps, thank them and say you will try the steps and get back to them later with the results.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-638174
              email: ryan.cooper@vdb.com
              full_name: Ryan Cooper
              level: 4
              department: it_operations
              role: Operations Manager
              office_location: austin
              start_date: '2022-02-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Ryan Cooper
              email: ryan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-743-8291
              verified: true
              active: true
              created_at: '2024-02-20T00:00:00Z'
              updated_at: '2024-02-20T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-11456
              device_type: laptop_standard
              device_model: Dell Latitude 5420
              purchase_date: '2021-12-01T00:00:00Z'
              warehouse_location: austin
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-63817492
              asset_id: VDB-HW-11456
              employee_id: WD-638174
              assigned_at: '2022-03-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.cooper@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: ryan.cooper@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop fan making loud noise
                  description: Employee reports laptop fan has been extremely loud for the past few days, even during light tasks like browsing. Troubleshooting steps provided.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Laptop fan making loud noise
                  description: Employee reports laptop fan extremely loud for past few days. Troubleshooting steps provided; awaiting employee feedback.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  asset_id: VDB-HW-11456
    """

    validate_database(x)


def test_ei_039(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Nathan Peters (nathan.peters@vdb.com) from the Product Engineering team. Several keys on my laptop keyboard are sticking and not registering properly. The 'E' and 'R' keys are particularly bad. It's making it really hard to type. Can you help me out?
    user_context: |
        You are Nathan Peters, a Database Administrator at VDB, contacting IT support about sticky keys on your laptop keyboard. Your email is nathan.peters@vdb.com.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - When the agent provides troubleshooting steps, acknowledge them and say you will try the steps and get back to them later with the results.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415873
              email: nathan.peters@vdb.com
              full_name: Nathan Peters
              level: 4
              department: product_engineering
              role: Database Administrator
              office_location: nyc
              start_date: '2021-09-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Peters
              email: nathan.peters@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-212-467-8293
              verified: true
              active: true
              created_at: '2024-02-10T00:00:00Z'
              updated_at: '2024-02-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-10890
              device_type: laptop_standard
              device_model: Dell Latitude 5520
              purchase_date: '2021-08-15T00:00:00Z'
              warehouse_location: nyc
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-41587326
              asset_id: VDB-HW-10890
              employee_id: WD-415873
              assigned_at: '2021-10-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.peters@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.peters@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: nathan.peters@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop Keyboard – Sticky Keys
                  description: 'Employee reports several keys on laptop keyboard are sticking and not registering properly. ''E'' and ''R'' keys particularly affected. Asset: VDB-HW-10890.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Laptop Keyboard – Sticky Keys
                  description: Employee reports several keys on laptop keyboard are sticking and not registering properly. 'E' and 'R' keys particularly affected. Troubleshooting steps provided; awaiting employee feedback.
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  asset_id: VDB-HW-10890
    """

    validate_database(x)


def test_ei_040(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, the hinge on my laptop is broken and the screen wobbles. I'm worried it might snap completely. Can I get this taken care of? My name is Rachel Foster, email rachel.foster@vdb.com.
    user_context: |
        You are Rachel Foster, a Training Coordinator at VDB, contacting IT support because your laptop hinge is broken and the screen wobbles. You are concerned it may snap completely. Your email is rachel.foster@vdb.com.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-648293
              email: rachel.foster@vdb.com
              full_name: Rachel Foster
              level: 2
              department: hr
              role: Training Coordinator
              office_location: nyc
              start_date: '2025-02-01T00:00:00Z'
              manager_id: WD-417263
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-417263
              email: diana.wright@vdb.com
              full_name: Diana Wright
              level: 5
              department: hr
              role: HR Director
              office_location: nyc
              start_date: '2020-04-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Rachel Foster
              email: rachel.foster@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-212-738-4519
              verified: true
              active: true
              created_at: '2025-02-01T00:00:00Z'
              updated_at: '2025-02-01T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-15234
              device_type: laptop_standard
              device_model: Dell Latitude 5440
              purchase_date: '2025-03-01T00:00:00Z'
              warehouse_location: nyc
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62748193
              asset_id: VDB-HW-15234
              employee_id: WD-648293
              assigned_at: '2025-03-05T00:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.foster@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.foster@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: rachel.foster@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop replacement request - broken hinge
                  description: Employee reports laptop hinge is broken and screen wobbles. Concerned it may snap completely. Asset VDB-HW-15234. Physical damage - proceeding with replacement.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
                  asset_id: VDB-HW-15234
            - tool: workday_api_get_manager_chain
              parameters:
                email: rachel.foster@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: diana.wright@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: rachel.foster@vdb.com
                approver_email: diana.wright@vdb.com
                details: 'Laptop replacement due to physical damage (broken hinge). Current asset: VDB-HW-15234. Standard tier replacement requested.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Laptop replacement request - broken hinge
                  description: 'Employee reports laptop hinge is broken and screen wobbles. Physical damage. Pending manager approval for standard laptop replacement. Asset: VDB-HW-15234.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-417263
                  approval_request_ids: APR-00000007
                  asset_id: VDB-HW-15234
    """

    validate_database(x)


def test_he_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Daniel Park (daniel.park@vdb.com). My laptop is almost 4 years old and really sluggish. I'd like a new one. Can you help me with a replacement?
    user_context: |
        You are Daniel Park, a Software Engineer at VDB, contacting IT support to request a laptop replacement because your current laptop is old and slow. You have no specific brand or model preference — you just want a new laptop.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent asks you to confirm the replacement or any details, confirm positively.
        - You do not have a preference for a specific laptop model or brand.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415763
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 3
              department: product_engineering
              role: Software Engineer
              office_location: sf
              start_date: '2022-05-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Park
              email: daniel.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-731-8294
              verified: true
              active: true
              created_at: '2024-05-10T00:00:00Z'
              updated_at: '2024-05-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-10234
              device_type: laptop_standard
              device_model: Dell Latitude 5440
              purchase_date: '2021-09-01T00:00:00Z'
              warehouse_location: sf
              condition: fair
              is_assigned: true
            - id: VDB-HW-38291
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: '2025-06-10T00:00:00Z'
              warehouse_location: sf
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-29471583
              asset_id: VDB-HW-10234
              employee_id: WD-415763
              assigned_at: '2022-05-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41576328
              employee_id: WD-415763
              app_name: GitHub
              access_level: read_write
              granted_at: '2022-05-05T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-41576492
              employee_id: WD-415763
              app_name: Jira
              access_level: read_write
              granted_at: '2022-05-05T09:05:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-41576617
              employee_id: WD-415763
              app_name: Slack
              access_level: read_write
              granted_at: '2022-05-05T09:10:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41573928
              employee_id: WD-415763
              group_name: engineers
              added_at: '2022-05-05T09:15:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.park@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.park@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: daniel.park@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop Replacement Request - Refresh
                  description: Employee reports their laptop (Dell Latitude 5440, asset VDB-HW-10234) is almost 4 years old and sluggish. Requesting a new laptop replacement.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
                  asset_id: VDB-HW-10234
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: laptop_standard
                warehouse_location: sf
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-38291
                email: daniel.park@vdb.com
            - tool: asset_management_api_retire_device
              parameters:
                asset_id: VDB-HW-10234
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Laptop Replacement Request - Refresh
                  description: Employee reports their laptop (Dell Latitude 5440, asset VDB-HW-10234) is almost 4 years old and sluggish. Requesting a new laptop replacement.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-38291
    """

    validate_database(x)


def test_he_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to get a newer laptop - mine is getting outdated. My name is Rachel Nguyen, email rachel.nguyen@vdb.com. I'm a Marketing Analyst on the growth team. Can you help me get a replacement?
    user_context: |
        You are Rachel Nguyen, a Marketing Analyst contacting IT support to request a laptop replacement because you feel your current laptop is getting outdated. You do NOT have a specific technical problem — you just want a newer machine.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent asks you for a business justification explaining why you need the replacement, respond with something like: "My current laptop has become really slow when running large marketing data visualizations in Tableau and handling analytics datasets. It's impacting my productivity and making it hard to meet project deadlines."
        - Do not volunteer the business justification unless the agent specifically asks for it.
        - If the agent asks you to confirm details or informs you about next steps (like manager approval), acknowledge and agree.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-384761
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 3
              department: marketing
              role: Marketing Analyst
              office_location: nyc
              start_date: '2023-01-15T00:00:00Z'
              manager_id: WD-629473
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-629473
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 5
              department: marketing
              role: Marketing Director
              office_location: nyc
              start_date: '2020-04-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Rachel Nguyen
              email: rachel.nguyen@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-212-738-4921
              verified: true
              active: true
              created_at: '2024-02-10T00:00:00Z'
              updated_at: '2024-02-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-11567
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: '2023-06-01T00:00:00Z'
              warehouse_location: nyc
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-48267193
              asset_id: VDB-HW-11567
              employee_id: WD-384761
              assigned_at: '2023-06-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.nguyen@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop Replacement Request – Refresh
                  description: 'Employee requests laptop replacement. Current device: VDB-HW-11567, Lenovo ThinkBook 14+, 28 months old, condition good. Reason: refresh (outdated). Business justification pending.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: daniel.park@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: rachel.nguyen@vdb.com
                approver_email: daniel.park@vdb.com
                details: 'Laptop replacement request (refresh). Current device: VDB-HW-11567, Lenovo ThinkBook 14+, 28 months old, condition good. Employee is a Marketing Analyst (Level 3) in marketing_growth. Business justification: Current laptop has become slow when running large marketing data visualizations in Tableau and handling analytics datasets, impacting productivity and ability to meet project deadlines. Requesting standard tier laptop replacement.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Laptop Replacement Request – Refresh
                  description: 'Employee requests laptop replacement. Current device: VDB-HW-11567, Lenovo ThinkBook 14+, 28 months old, condition good. Reason: refresh (outdated). Business justification: Current laptop has become slow when running large marketing data visualizations in Tableau and handling analytics datasets, impacting productivity and ability to meet project deadlines. Awaiting manager approval.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: Current laptop has become slow when running large marketing data visualizations in Tableau and handling analytics datasets, impacting productivity and ability to meet project deadlines.
                  approver_id: WD-629473
                  approval_request_ids: APR-00000007
                  asset_id: VDB-HW-11567
    """

    validate_database(x)


def test_he_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Daniel Wright (daniel.wright@vdb.com) from the Finance team. I want a more powerful laptop for my financial modeling work. My current one is fine but I'd like something better. Can you help me get a replacement?
    user_context: |
        You are Daniel Wright, a Financial Analyst contacting IT support to request a more powerful laptop. Your current laptop works fine, but you want an upgrade for your financial modeling work.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent asks for a business justification, respond with: "Running complex financial models with large datasets in Excel and Python is causing significant slowdowns and freezing on my current machine, which delays my reporting deadlines."
        - If asked to confirm any details about the request, confirm them.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415873
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 3
              department: finance_accounting
              role: Financial Analyst
              office_location: sf
              start_date: '2024-06-01T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Wright
              email: daniel.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-739-2841
              verified: true
              active: true
              created_at: '2024-06-15T00:00:00Z'
              updated_at: '2024-06-15T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-14892
              device_type: laptop_standard
              device_model: Dell Latitude 5540
              purchase_date: '2025-03-15T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-48271639
              asset_id: VDB-HW-14892
              employee_id: WD-415873
              assigned_at: '2025-03-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_articles: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.wright@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.wright@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: daniel.wright@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop Replacement Request — Refresh
                  description: 'Employee requests a more powerful laptop for financial modeling work. Current device: VDB-HW-14892 (Dell Latitude 5540, 9 months old, condition: good). Replacement reason: refresh. Awaiting business justification.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.wright@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: chris.johnson@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: daniel.wright@vdb.com
                approver_email: chris.johnson@vdb.com
                details: 'Laptop replacement request (refresh) for Financial Analyst. Current device: VDB-HW-14892 (Dell Latitude 5540, 9 months old). Business justification: Running complex financial models with large datasets in Excel and Python is causing significant slowdowns and freezing, which delays reporting deadlines.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Laptop Replacement Request — Refresh
                  description: 'Employee requests a more powerful laptop for financial modeling work. Current device: VDB-HW-14892 (Dell Latitude 5540, 9 months old, condition: good). Replacement reason: refresh. Business justification: Running complex financial models with large datasets in Excel and Python is causing significant slowdowns and freezing, which delays reporting deadlines. Manager approval requested (APR-00000007).'
                  owner: it_support
                  approval_required: 'yes'
                  approver_id: WD-671392
                  approval_request_ids: APR-00000007
                  business_justification: Running complex financial models with large datasets in Excel and Python is causing significant slowdowns and freezing, which delays reporting deadlines.
                  asset_id: VDB-HW-14892
                  approval_status: pending
    """

    validate_database(x)


def test_he_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my laptop died this morning - it won't power on at all, no lights, nothing. I tried different outlets and chargers but nothing works. I'm Nathan Brooks, nathan.brooks@vdb.com, QA Engineer on the product engineering team in Austin. It's a Lenovo ThinkBook 14+. Can you help?
    user_context: |
        You are Nathan Brooks, a QA Engineer at VDB, contacting IT support because your laptop completely stopped working this morning — it won't power on at all.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        SCENARIO-SPECIFIC BEHAVIOR:
        - When the agent provides troubleshooting steps, agree to try them and say you will get back to the agent with results. Indicate you need some time to try them out.
        - When you return (in your next message after the agent acknowledges), report that you tried all the suggested troubleshooting steps but none of them worked — the laptop still won't power on at all, no lights, no response whatsoever. It appears to be a hardware issue.
        - Do not request a specific laptop model or a premium/Mac device. You just want a working laptop.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-647219
              email: nathan.brooks@vdb.com
              full_name: Nathan Brooks
              level: 3
              department: product_engineering
              role: QA Engineer
              office_location: austin
              start_date: '2024-02-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Brooks
              email: nathan.brooks@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-738-4291
              verified: true
              active: true
              created_at: '2024-02-05T00:00:00Z'
              updated_at: '2024-02-05T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-14567
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: '2025-04-01T00:00:00Z'
              warehouse_location: austin
              condition: good
              is_assigned: true
            - id: VDB-HW-38291
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: '2025-06-10T00:00:00Z'
              warehouse_location: austin
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-28147593
              asset_id: VDB-HW-14567
              employee_id: WD-647219
              assigned_at: '2025-04-05T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.brooks@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.brooks@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: nathan.brooks@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop not powering on - Lenovo ThinkBook 14+
                  description: Employee reports laptop (VDB-HW-14567, Lenovo ThinkBook 14+) completely stopped working this morning. Will not power on at all - no lights, no response. Employee has tried different outlets and chargers with no success.
                  status: open
                  priority: high
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  asset_id: VDB-HW-14567
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: high
                  subject: Laptop not powering on - Lenovo ThinkBook 14+
                  description: 'Employee reports laptop (VDB-HW-14567, Lenovo ThinkBook 14+) completely stopped working. Will not power on - no lights, no response. Tried different outlets and chargers. Troubleshooting steps provided: hard reset (hold power button 15-30 seconds), check for LED activity, try without peripherals connected. Awaiting employee feedback.'
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  asset_id: VDB-HW-14567
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: open
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: laptop_standard
                warehouse_location: austin
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-38291
                email: nathan.brooks@vdb.com
            - tool: asset_management_api_retire_device
              parameters:
                asset_id: VDB-HW-14567
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: high
                  subject: Laptop hardware failure - warranty replacement (VDB-HW-14567)
                  description: 'Employee reported Lenovo ThinkBook 14+ (VDB-HW-14567) would not power on. Troubleshooting attempted (hard reset, different outlets/chargers, check for LED activity) - unsuccessful. Hardware failure confirmed. Device age: 6 months (purchased 2025-04-01), qualifies for warranty replacement (auto-approved, under 12 months). New Lenovo ThinkBook 14+ (VDB-HW-38291) assigned from Austin inventory. Old device VDB-HW-14567 retired.'
                  owner: it_support
                  approval_required: 'no'
                  resolution_category: provisioned
                  asset_id: VDB-HW-38291
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: high
                  subject: Laptop hardware failure - warranty replacement (VDB-HW-14567)
                  description: 'Employee reported Lenovo ThinkBook 14+ (VDB-HW-14567) would not power on. Troubleshooting attempted (hard reset, different outlets/chargers, check for LED activity) - unsuccessful. Hardware failure confirmed. Device age: 6 months (purchased 2025-04-01), qualifies for warranty replacement (auto-approved, under 12 months). New Lenovo ThinkBook 14+ (VDB-HW-38291) assigned from Austin inventory. Old device VDB-HW-14567 retired.'
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-38291
    """

    validate_database(x)


def test_he_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I accidentally dropped my laptop yesterday and now the screen is cracked and the keyboard doesn't work properly. I need to get this sorted out. My name is Ryan Cooper and my email is ryan.cooper@vdb.com.
    user_context: |
        You are Ryan Cooper, a Business Development Representative at VDB, contacting IT support because you dropped your laptop and it's now damaged (cracked screen, malfunctioning keyboard). Your email is ryan.cooper@vdb.com.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent asks you to confirm details about the damage or the device, confirm based on what you already stated.
        - You do not have a preference for any specific laptop model or type — you just need a working replacement.
        - You are not requesting a premium or MacBook device.
        - If the agent offers a temporary or loaner device while you wait for the replacement, politely decline — you can manage with workarounds until the replacement is ready.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415893
              email: ryan.cooper@vdb.com
              full_name: Ryan Cooper
              level: 2
              department: sales
              role: Business Development Representative
              office_location: sf
              start_date: '2023-08-01T00:00:00Z'
              manager_id: WD-637284
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-637284
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 6
              department: sales
              role: Sales Director
              office_location: sf
              start_date: '2020-03-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Ryan Cooper
              email: ryan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-736-8291
              verified: true
              active: true
              created_at: '2024-08-01T00:00:00Z'
              updated_at: '2024-08-01T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-12890
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: '2023-07-01T00:00:00Z'
              warehouse_location: sf
              condition: poor
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-48271639
              asset_id: VDB-HW-12890
              employee_id: WD-415893
              assigned_at: '2023-09-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.cooper@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: ryan.cooper@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop Replacement - Damage (Dropped)
                  description: 'Employee reports accidentally dropping their laptop. Screen is cracked and keyboard is not working properly. Device: VDB-HW-12890, Lenovo ThinkBook 14+. Replacement needed due to physical damage.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: ryan.cooper@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: ryan.cooper@vdb.com
                approver_email: rachel.nguyen@vdb.com
                details: 'Laptop replacement request due to physical damage. Employee dropped laptop, screen cracked and keyboard malfunctioning. Device: VDB-HW-12890, Lenovo ThinkBook 14+.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Laptop Replacement - Damage (Dropped)
                  description: 'Employee reports accidentally dropping their laptop. Screen is cracked and keyboard is not working properly. Device: VDB-HW-12890, Lenovo ThinkBook 14+. Replacement needed due to physical damage. Awaiting manager approval.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-637284
                  approval_request_ids: APR-00000007
                  asset_id: VDB-HW-12890
    """

    validate_database(x)


def test_he_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Daniel Park (daniel.park@vdb.com), Senior Data Scientist on the product engineering team. I'd like to request a laptop replacement — specifically, I'm looking to get a MacBook Pro 14. My current laptop is a Dell Latitude 5440, asset ID VDB-HW-10567. I need a MacBook Pro for machine learning development - the M-series chips are much better for my TensorFlow work. The Dell just doesn't cut it for the kind of model training workloads I need to run locally. Can you help me get this set up?
    user_context: |
        You are Daniel Park, a Senior Data Scientist at VDB, contacting IT support to request a MacBook Pro 14 as a replacement for your current Dell Latitude 5440 laptop. Your business justification is that M-series chips are significantly better for your TensorFlow and machine learning development work.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm details, confirm them.
        - If informed the request requires manager approval and is pending, acknowledge and thank the agent.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637482
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 5
              department: product_engineering
              role: Senior Data Scientist
              office_location: sf
              start_date: '2021-06-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Park
              email: daniel.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-726-8391
              verified: true
              active: true
              created_at: '2024-06-01T00:00:00Z'
              updated_at: '2024-06-01T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-10567
              device_type: laptop_standard
              device_model: Dell Latitude 5440
              purchase_date: '2021-08-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-48273619
              asset_id: VDB-HW-10567
              employee_id: WD-637482
              assigned_at: '2021-08-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_customer_accounts: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.park@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.park@vdb.com'
            - tool: asset_management_api_get_device_details
              parameters:
                asset_id: VDB-HW-10567
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop Replacement Request - Premium MacBook Pro 14
                  description: 'Employee requests replacement of current standard laptop (Dell Latitude 5440, VDB-HW-10567) with Premium laptop (MacBook Pro 14) for machine learning development. Business justification: M-series chips are much better for TensorFlow work. Pending manager approval.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.park@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: sarah.jones@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: daniel.park@vdb.com
                approver_email: sarah.jones@vdb.com
                details: 'Premium laptop replacement request. Employee requests MacBook Pro 14 to replace current Dell Latitude 5440 (VDB-HW-10567, 53 months old). Business justification: Machine learning development - M-series chips significantly better for TensorFlow work.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Laptop Replacement Request - Premium MacBook Pro 14
                  description: 'Employee requests replacement of current standard laptop (Dell Latitude 5440, VDB-HW-10567) with Premium laptop (MacBook Pro 14) for machine learning development. Business justification: M-series chips are much better for TensorFlow work. Awaiting manager approval.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-681453
                  approval_request_ids: APR-00000007
                  business_justification: Machine learning development - M-series chips are much better for TensorFlow work
                  asset_id: VDB-HW-10567
    """

    validate_database(x)


def test_he_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I'm Ryan Cooper, DevOps Engineer on the product engineering team. My email is ryan.cooper@vdb.com. I've been using just my laptop screen but need an external monitor for the multiple terminal windows I work with. Could you help me get one set up?
    user_context: |
        You are Ryan Cooper, a DevOps Engineer at VDB, contacting IT support to request your first external monitor. You have no specific monitor model preference — you just need an external monitor to help with your workflow involving multiple terminal windows.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked about monitor model preferences, say you have no specific preference and are happy with whatever is standard/available.
        - If the agent confirms a monitor assignment and pickup details, acknowledge and thank them.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-428163
              email: ryan.cooper@vdb.com
              full_name: Ryan Cooper
              level: 4
              department: product_engineering
              role: DevOps Engineer
              office_location: sf
              start_date: '2022-09-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Ryan Cooper
              email: ryan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-8294
              verified: true
              active: true
              created_at: '2024-09-10T00:00:00Z'
              updated_at: '2024-09-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-36294
              device_type: monitor
              device_model: Dell P2425H 24"
              purchase_date: '2024-06-15T00:00:00Z'
              warehouse_location: sf
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.cooper@vdb.com
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: ryan.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.cooper@vdb.com'
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: monitor
                warehouse_location: sf
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Monitor Provision Request - DevOps Engineer Ryan Cooper
                  description: 'DevOps Engineer Ryan Cooper requesting first external monitor for working with multiple terminal windows. Employee currently has zero monitors assigned. Auto-approved per policy: technical role in SF office with no existing monitors.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  tags: null
                  due_at: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-36294
                email: ryan.cooper@vdb.com
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Monitor Provision Request - DevOps Engineer Ryan Cooper
                  description: 'DevOps Engineer Ryan Cooper requesting first external monitor for working with multiple terminal windows. Auto-approved per policy: technical role in SF office with no existing monitors. Assigned Dell P2425H 24" (VDB-HW-36294) from SF inventory.'
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-36294
    """

    validate_database(x)


def test_he_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Daniel Foster (daniel.foster@vdb.com) from the Compliance team. I'm working from home and need a monitor for better productivity reviewing case documentation. I don't currently have one. Could you help me get one set up?
    user_context: |
        You are Daniel Foster, a remote Compliance Analyst at VDB, requesting a monitor for your home office. You currently have no monitor assigned.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - You have no specific brand or model preference for the monitor.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-413587
              email: daniel.foster@vdb.com
              full_name: Daniel Foster
              level: 3
              department: compliance_risk
              role: Compliance Analyst
              office_location: remote
              start_date: '2023-04-01T00:00:00Z'
              manager_id: WD-584201
              employment_status: active
              is_contractor: false
              remote_delivery_address: 1823 Elm Street, Minneapolis, MN 55401
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Foster
              email: daniel.foster@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-612-483-7251
              verified: true
              active: true
              created_at: '2024-04-15T00:00:00Z'
              updated_at: '2024-04-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.foster@vdb.com
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: daniel.foster@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.foster@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Monitor provision request for remote Compliance Analyst
                  description: Remote employee requesting a monitor for home office to improve productivity reviewing case documentation. Employee currently has zero monitors assigned.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
                  approval_required: 'no'
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: monitor
                warehouse_location: remote_ship
            - tool: hardware_procurement_api_create_order
              parameters:
                device_type: monitor
                device_model: Dell P2425H 24"
                quantity: 1
                expected_delivery_date: '2025-10-15'
                ship_to_location: 1823 Elm Street, Minneapolis, MN 55401
                requester_email: daniel.foster@vdb.com
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  resolution_category: approved
                  approval_required: 'no'
                  approval_status: not_required
                  owner: it_support
    """

    validate_database(x)


def test_he_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I'm Nathan Price from the Customer Support team. My email is nathan.price@vdb.com. I'd like to request a second monitor — it would really help me handle customer chats more efficiently. Could you help me get that set up?
    user_context: |
        You are Nathan Price, a Customer Support Agent, requesting an external monitor to help with your daily work. You believe a second screen would help you handle multiple customer chats more efficiently.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If your request is denied, you may express mild disappointment but accept the decision. Do not argue excessively or escalate.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-648273
              email: nathan.price@vdb.com
              full_name: Nathan Price
              level: 2
              department: customer_support
              role: Customer Support Agent
              office_location: sf
              start_date: '2023-06-15T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Price
              email: nathan.price@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-736-8294
              verified: true
              active: true
              created_at: '2024-06-15T00:00:00Z'
              updated_at: '2024-06-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.price@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.price@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Monitor Provision Request
                  description: Employee requests a second monitor to handle customer chats more efficiently.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Monitor Provision Request
                  description: Employee requests a second monitor to handle customer chats more efficiently.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: denied
    """

    validate_database(x)


def test_he_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I'm Daniel Wright, CFO. My email is daniel.wright@vdb.com. I'd like to get an additional external monitor for my desk setup. Could you help me with that?
    user_context: |
        You are Daniel Wright, CFO at the company, requesting an additional external monitor for your workstation. You already have one monitor but want a second one. You have no specific model preference.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-638271
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 8
              department: executive_leadership
              role: Chief Financial Officer
              office_location: sf
              start_date: '2023-06-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Wright
              email: daniel.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-739-2841
              verified: true
              active: true
              created_at: '2024-02-10T00:00:00Z'
              updated_at: '2024-02-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-36291
              device_type: laptop_premium
              device_model: MacBook Pro 16-inch M3
              purchase_date: '2023-07-10T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-51847
              device_type: monitor
              device_model: Dell UltraSharp 27 U2723DE
              purchase_date: '2023-08-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-42183
              device_type: monitor
              device_model: Dell P2425H 24"
              purchase_date: '2024-06-15T00:00:00Z'
              warehouse_location: sf
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-14729386
              asset_id: VDB-HW-36291
              employee_id: WD-638271
              assigned_at: '2023-07-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-26381947
              asset_id: VDB-HW-51847
              employee_id: WD-638271
              assigned_at: '2023-08-05T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.wright@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.wright@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: daniel.wright@vdb.com
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: monitor
                warehouse_location: sf
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Monitor provision request
                  description: Executive requesting an additional external monitor for workstation setup at SF office.
                  status: open
                  priority: high
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-42183
                email: daniel.wright@vdb.com
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: high
                  subject: Monitor provision request
                  description: Executive requesting an additional external monitor for workstation setup at SF office. Dell P2425H 24" monitor assigned from SF inventory.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-42183
    """

    validate_database(x)


def test_he_013(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I dropped my laptop earlier today and now it won't turn on at all. I'm Daniel Foster, COO — my email is daniel.foster@vdb.com. I need to get this sorted out as soon as possible since I can't do any work without it.
    user_context: |
        You are Daniel Foster, Chief Operating Officer at VDB, contacting IT support because you dropped your laptop and it no longer powers on. You need a replacement.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm details about the damage, confirm you dropped it and it won't turn on.
        - You do not have a preference for Mac vs Windows — you are fine with whatever the standard replacement is for your role.
        - If the agent informs you that manager approval is needed, acknowledge and accept that.
        - If the agent offers a temporary or loaner device, decline it and say you can manage until the replacement comes through.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-418273
              email: daniel.foster@vdb.com
              full_name: Daniel Foster
              level: 8
              department: executive_leadership
              role: Chief Operating Officer
              office_location: sf
              start_date: '2023-08-01T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Foster
              email: daniel.foster@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-2948
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-12890
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: '2023-07-01T00:00:00Z'
              warehouse_location: sf
              condition: poor
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62847193
              asset_id: VDB-HW-12890
              employee_id: WD-418273
              assigned_at: '2023-09-10T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.foster@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.foster@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: daniel.foster@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop Damage Replacement Request - Dropped Laptop Not Powering On
                  description: Employee Daniel Foster reports dropping their laptop (asset VDB-HW-12890, Lenovo ThinkBook 14+). The device no longer powers on. Requesting replacement with Premium tier device (MacBook Pro 14) per Executive & Leadership entitlement. Physical damage - proceeding directly to replacement procedure.
                  type: problem
                  priority: high
                  status: open
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
                  asset_id: VDB-HW-12890
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.foster@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: lisa.chen@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: daniel.foster@vdb.com
                approver_email: lisa.chen@vdb.com
                details: Laptop replacement due to physical damage. Employee dropped laptop (asset VDB-HW-12890, Lenovo ThinkBook 14+), device no longer powers on. Replacement with MacBook Pro 14 (Premium tier) per Executive & Leadership entitlement. Damage-related replacement requires manager approval.
                urgency: urgent
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: high
                  subject: Laptop Damage Replacement Request - Dropped Laptop Not Powering On
                  description: Employee Daniel Foster reports dropping their laptop (asset VDB-HW-12890, Lenovo ThinkBook 14+). The device no longer powers on. Executive requesting Premium tier replacement (MacBook Pro 14). Awaiting manager approval from Lisa Chen.
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-294817
                  approval_request_ids: APR-00000007
                  asset_id: VDB-HW-12890
    """

    validate_database(x)


def test_he_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Richard Wells, richard.wells@vdb.com. I need a laptop replacement — my dog destroyed my laptop over the weekend. It's completely unusable. Can you help me get a new one?
    user_context: |
        You are Richard Wells, CFO at the company, contacting IT support because your dog destroyed your laptop. You need a replacement.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm details about the damage, confirm: the laptop was physically destroyed by your dog and is completely non-functional.
        - If asked about your current device, it is a MacBook Pro 14-inch.
        - If the agent offers a temporary or loaner device, decline it and say you can manage until the replacement comes through.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-417583
              email: richard.wells@vdb.com
              full_name: Richard Wells
              level: 8
              department: executive_leadership
              role: Chief Financial Officer
              office_location: remote
              start_date: '2020-08-01T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: 1893 Beacon Hill Dr, Nashville, TN 37215
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Richard Wells
              email: richard.wells@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-615-472-8391
              verified: true
              active: true
              created_at: '2024-08-10T00:00:00Z'
              updated_at: '2024-08-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-36291
              device_type: laptop_premium
              device_model: MacBook Pro 14-inch M3
              purchase_date: '2022-11-01T00:00:00Z'
              warehouse_location: remote_ship
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-82641739
              asset_id: VDB-HW-36291
              employee_id: WD-417583
              assigned_at: '2023-02-01T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: richard.wells@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'richard.wells@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: richard.wells@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop Replacement - Physical Damage
                  description: Executive reports laptop destroyed by dog. Premium laptop replacement required. Manager approval needed for damage replacement.
                  status: open
                  priority: high
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: richard.wells@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: lisa.chen@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: richard.wells@vdb.com
                approver_email: lisa.chen@vdb.com
                details: Laptop replacement request due to physical damage (destroyed by dog). Premium tier - MacBook Pro 14-inch M3. Executive & Leadership employee.
                urgency: urgent
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-294817
                  approval_request_ids: APR-00000007
                  asset_id: VDB-HW-36291
    """

    validate_database(x)


def test_he_016(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to request an external monitor for my workstation.
    user_context: |
        You are Nathan Parker, a Customer Support Specialist at VDB, requesting an external monitor. You work in the NYC office.

        Only if you are asked about your name or to identify yourself — tell the agent your name is Nathan Parker.
        Only if you are asked about your email address — tell the agent it is nathan.parker@vdb.com.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Your business justification is: 'I need a larger screen to view multiple customer tickets simultaneously during peak hours.' If asked to elaborate, stick to this reasoning.
        - If the agent informs you that manager approval is needed, acknowledge and confirm you're fine waiting for that.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-614829
              email: nathan.parker@vdb.com
              full_name: Nathan Parker
              level: 3
              department: customer_support
              role: Customer Support Specialist
              office_location: nyc
              start_date: '2024-02-01T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-38291
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2023-12-05T00:00:00Z'
              warehouse_location: nyc
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-61482937
              asset_id: VDB-HW-38291
              employee_id: WD-614829
              assigned_at: '2024-02-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_users:
            - id: '6'
              name: Nathan Parker
              email: nathan.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-212-847-3192
              verified: true
              active: true
              created_at: '2024-02-01T00:00:00Z'
              updated_at: '2024-02-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.parker@vdb.com
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: nathan.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.parker@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Monitor Provision Request
                  description: Customer Support Specialist requesting an external monitor to view multiple customer tickets simultaneously during peak hours.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: nathan.parker@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: maria.garcia@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: nathan.parker@vdb.com
                approver_email: maria.garcia@vdb.com
                details: 'Monitor provision request for Customer Support Specialist. Business justification: I need a larger screen to view multiple customer tickets simultaneously during peak hours.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Monitor Provision Request
                  description: Customer Support Specialist requesting an external monitor to view multiple customer tickets simultaneously during peak hours.
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: I need a larger screen to view multiple customer tickets simultaneously during peak hours.
                  approver_id: WD-739154
                  approval_request_ids: APR-00000007
    """

    validate_database(x)


def test_he_017(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, checking on my laptop replacement request from last week. Has it been approved yet? My name is Daniel Wright, email daniel.wright@vdb.com.
    user_context: |
        You are Daniel Wright, a Sales Representative, following up on a laptop replacement request you submitted about a week ago due to performance issues with your current laptop. You want to know if the request has been approved.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent asks for information you do not have (such as asset tags, deadlines, OS preferences, or other details not listed here), say you do not have that information available right now and reiterate that you are just checking on the status of your existing request.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-641837
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 2
              department: sales
              role: Sales Representative
              office_location: remote
              start_date: '2024-03-01T00:00:00Z'
              manager_id: WD-428163
              employment_status: active
              is_contractor: false
              remote_delivery_address: 1923 Maple Ave, Nashville, TN 37203
              contract_end_date: null
            - id: WD-428163
              email: rachel.foster@vdb.com
              full_name: Rachel Foster
              level: 5
              department: sales
              role: Sales Manager
              office_location: nyc
              start_date: '2020-07-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Wright
              email: daniel.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-615-472-8391
              verified: true
              active: true
              created_at: '2024-03-01T00:00:00Z'
              updated_at: '2024-03-01T00:00:00Z'
          zendesk_tickets:
            - id: '48765'
              subject: Laptop Replacement Request
              description: Requesting replacement for current laptop due to performance issues
              status: pending
              priority: normal
              type: problem
              requester_id: '6'
              assignee_id: '2'
              organization_id: '1'
              tags:
                - hardware
                - laptop
                - replacement
              created_at: '2025-09-23T13:00:00Z'
              updated_at: '2025-09-23T13:00:00Z'
              due_at: null
              resolution_category: null
              owner: it_support
              access_expiry_date: null
              approval_required: 'yes'
              approval_status: pending
              approver_id: WD-428163
              approval_request_ids: APR-47291836
              business_justification: null
              incident_severity: null
              customer_impact: null
              asset_id: null
          sandbox_neobank_support_main_models_approval_requests:
            - id: APR-47291836
              request_type: hardware_purchase
              requester_id: WD-641837
              approver_id: WD-428163
              status: pending
              urgency: standard
              details: Laptop replacement request for Daniel Wright due to performance issues with current device
              ticket_id: '48765'
              created_at: '2025-09-23T13:00:00Z'
              decided_at: null
              approver_feedback: null
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-45872
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: '2024-02-15T00:00:00Z'
              warehouse_location: remote_ship
              condition: fair
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-73618425
              asset_id: VDB-HW-45872
              employee_id: WD-641837
              assigned_at: '2024-03-01T00:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.wright@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.wright@vdb.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                $filter: requester_id eq '6' and status eq 'pending'
            - tool: approval_api_check_status
              parameters:
                approval_request_id: APR-47291836
    """

    validate_database(x)


def test_he_020(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to request a second monitor.
    user_context: |
        You are Nathan Cooper, a Data Analyst in the finance_accounting department, contacting IT support to request a second monitor. You already have one monitor assigned but need an additional one for spreadsheet cross-referencing work.

        Only if you are asked about your name or who you are — tell the agent you are Nathan Cooper.
        Only if you are asked about your email address — tell the agent it is nathan.cooper@vdb.com.
        Only if you are asked about your department or team — tell the agent you are in the Finance & Accounting team.
        Only if you are asked about your role or job title — tell the agent you are a Data Analyst.
        Only if you are asked about your current setup or what monitors you already have — tell the agent you already have one monitor.
        Only if you are asked why you need a second monitor or the reason for your request — tell the agent it's for spreadsheet work with lots of cross-referencing.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-648273
              email: nathan.cooper@vdb.com
              full_name: Nathan Cooper
              level: 3
              department: finance_accounting
              role: Data Analyst
              office_location: austin
              start_date: '2022-08-01T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Cooper
              email: nathan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-743-8261
              verified: true
              active: true
              created_at: '2024-08-10T00:00:00Z'
              updated_at: '2024-08-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-20345
              device_type: monitor
              device_model: Dell UltraSharp 27 U2723DE
              purchase_date: '2023-02-10T00:00:00Z'
              warehouse_location: austin
              condition: good
              is_assigned: true
            - id: VDB-HW-37821
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2022-07-15T00:00:00Z'
              warehouse_location: austin
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-42817365
              asset_id: VDB-HW-20345
              employee_id: WD-648273
              assigned_at: '2023-05-10T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-61593847
              asset_id: VDB-HW-37821
              employee_id: WD-648273
              assigned_at: '2022-10-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.cooper@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: nathan.cooper@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Second monitor request - Data Analyst spreadsheet cross-referencing
                  description: 'Employee Nathan Cooper (Data Analyst, finance_accounting, austin) is requesting a second monitor. Currently has one monitor assigned (VDB-HW-20345). Business justification: needs a second monitor for spreadsheet work involving extensive cross-referencing of data.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: nathan.cooper@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: chris.johnson@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: nathan.cooper@vdb.com
                approver_email: chris.johnson@vdb.com
                details: 'Request for a second monitor for Data Analyst Nathan Cooper (finance_accounting, austin). Employee currently has one monitor (VDB-HW-20345). Business justification: needs a second monitor for spreadsheet work involving extensive cross-referencing.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Second monitor request - Data Analyst spreadsheet cross-referencing
                  description: 'Employee Nathan Cooper (Data Analyst, finance_accounting, austin) is requesting a second monitor. Currently has one monitor assigned (VDB-HW-20345). Business justification: needs a second monitor for spreadsheet work involving extensive cross-referencing of data.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: I already have one monitor but need a second one for my spreadsheet work - lots of cross-referencing.
                  approver_id: WD-671392
                  approval_request_ids: APR-00000007
    """

    validate_database(x)


def test_he_021(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need a docking station for my home office setup to connect my monitor and peripherals. I'm Rachel Parker, email rachel.parker@vdb.com. Could you help me get one set up?
    user_context: |
        You are Rachel Parker, a remote HR Specialist at VDB, requesting a docking station for your home office. You have no specific model preference.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-638291
              email: rachel.parker@vdb.com
              full_name: Rachel Parker
              level: 3
              department: hr
              role: HR Specialist
              office_location: remote
              start_date: '2023-02-01T00:00:00Z'
              manager_id: WD-748362
              employment_status: active
              is_contractor: false
              remote_delivery_address: 1523 Elm Street, Portland, OR 97205
              contract_end_date: null
            - id: WD-748362
              email: daniel.foster@vdb.com
              full_name: Daniel Foster
              level: 6
              department: hr
              role: HR Director
              office_location: sf
              start_date: '2019-11-10T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Rachel Parker
              email: rachel.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-503-847-2931
              verified: true
              active: true
              created_at: '2024-01-15T00:00:00Z'
              updated_at: '2024-01-15T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-36291
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2023-01-20T00:00:00Z'
              warehouse_location: remote_ship
              condition: good
              is_assigned: true
            - id: VDB-HW-52784
              device_type: docking_station
              device_model: Lenovo 40A90090US
              purchase_date: '2024-09-15T00:00:00Z'
              warehouse_location: remote_ship
              condition: new
              is_assigned: false
            - id: VDB-HW-61935
              device_type: docking_station
              device_model: CalDigit TS4 Thunderbolt 4 Dock
              purchase_date: '2024-08-20T00:00:00Z'
              warehouse_location: remote_ship
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-82461537
              asset_id: VDB-HW-36291
              employee_id: WD-638291
              assigned_at: '2023-02-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.parker@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: rachel.parker@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Docking Station Provision Request - Home Office
                  description: Remote HR Specialist requests a docking station for home office setup to connect monitor and peripherals.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  tags: null
                  due_at: null
                  owner: it_support
                  approval_status: not_required
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: docking_station
                warehouse_location: remote_ship
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-52784
                email: rachel.parker@vdb.com
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Docking Station Provision Request - Home Office
                  description: Docking station provisioned and assigned. Lenovo 40A90090US assigned from remote_ship inventory.
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-52784
    """

    validate_database(x)


def test_he_023(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need a larger monitor for my work.
    user_context: |
        You are Rachel Nguyen, a Financial Analyst at VDB, contacting IT support to request a 27-inch monitor. You already have a 24-inch ASUS monitor but you want a larger one to better view your excel spreadsheets.

        Only if you are asked about your name or email — tell the agent you are Rachel Nguyen and your email is rachel.nguyen@vdb.com
        Only if you are asked about your department or team — tell the agent you are from the finance team
        Only if you are asked about what size or type of monitor you need — tell the agent you want a 27-inch monitor
        Only if you are asked about why you need it or business justification — tell the agent you need it to fit all your excel tables and need the bigger screen for your work
        Only if you are asked about your current equipment — tell the agent you already have a monitor but really need the bigger screen

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Your business justification is: you need a 27-inch monitor to fit all your excel tables.
        - If asked to confirm details or acknowledge that manager approval is needed, agree and confirm.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637281
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 3
              department: finance_accounting
              role: Financial Analyst
              office_location: sf
              start_date: '2024-06-01T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Rachel Nguyen
              email: rachel.nguyen@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-726-8394
              verified: true
              active: true
              created_at: '2024-06-15T00:00:00Z'
              updated_at: '2024-06-15T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-52739
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2024-04-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-38291
              device_type: monitor
              device_model: ASUS VA24DQFS 24-inch Full HD IPS Monitor
              purchase_date: '2024-06-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-52739814
              asset_id: VDB-HW-52739
              employee_id: WD-637281
              assigned_at: '2024-06-05T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-38291567
              asset_id: VDB-HW-38291
              employee_id: WD-637281
              assigned_at: '2024-08-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.nguyen@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: 27-inch Monitor Request
                  description: 'Employee requests a 27-inch monitor. Business justification: to fit all excel tables. Employee currently has ASUS VA24DQFS 24-inch monitor assigned.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: chris.johnson@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: rachel.nguyen@vdb.com
                approver_email: chris.johnson@vdb.com
                details: 'Request for 27-inch monitor. Business justification: to fit all excel tables. Employee currently has ASUS VA24DQFS 24-inch monitor assigned.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: 27-inch Monitor Request
                  description: 'Employee requests a 27-inch monitor. Business justification: to fit all excel tables. Employee currently has ASUS VA24DQFS 24-inch monitor assigned. Awaiting manager approval.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: to fit all my excel tables
                  approver_id: WD-671392
                  approval_request_ids: APR-00000007
    """

    validate_database(x)


def test_he_024(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to get a printer. We have a common printer, but it is far away from my workplace. My name is Daniel Park, email daniel.park@vdb.com. Could you help me with this?
    user_context: |
        You are Daniel Park, an accountant in the Finance & Accounting department, contacting IT support to request a personal printer for your workstation because the shared office printer is inconveniently far from your desk.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent denies the request, you may express mild disappointment but accept the decision gracefully.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-614829
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 3
              department: finance_accounting
              role: Accountant
              office_location: nyc
              start_date: '2023-01-15T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Park
              email: daniel.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-212-847-3291
              verified: true
              active: true
              created_at: '2024-06-01T00:00:00Z'
              updated_at: '2024-06-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.park@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.park@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Printer provision request
                  description: Employee requests a personal printer because the common office printer is far from their workplace.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  resolution_category: denied
                  approval_required: 'no'
                  approval_status: not_required
                  owner: it_support
    """

    validate_database(x)


def test_he_025(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Ryan Cooper (ryan.cooper@vdb.com). My laptop just completely died on me — it's asset ID VDB-HW-09567. It won't turn on at all. I'm departing the company and my last day is October 10th, so I only have about 9 days left. I really need a temporary replacement so I can finish my handover documentation. Can you help?
    user_context: |
        You are Ryan Cooper, a departing Senior Engineer whose laptop has completely stopped working. You need a replacement to finish handover documentation before your last day on October 10th.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent provides troubleshooting steps (e.g., checking power cable, trying a different outlet, holding the power button, trying a different charger), respond that you already tried those things and none of them worked — the laptop is completely dead, no lights, no response at all when pressing the power button. It simply won't turn on.
        - You have no specific laptop model preference; you just need something that works to finish your handover docs.
        - You do not need to ask the agent to try troubleshooting steps first or request extra time — just confirm they didn't help.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-641873
              email: ryan.cooper@vdb.com
              full_name: Ryan Cooper
              level: 5
              department: product_engineering
              role: Senior Engineer
              office_location: sf
              start_date: '2020-08-10T00:00:00Z'
              manager_id: WD-681453
              employment_status: departing
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Ryan Cooper
              email: ryan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-738-2951
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-09567
              device_type: laptop_standard
              device_model: Lenovo ThinkPad T14 Gen 3
              purchase_date: '2022-03-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-84523
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: '2024-06-15T00:00:00Z'
              warehouse_location: sf
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-64187352
              asset_id: VDB-HW-09567
              employee_id: WD-641873
              assigned_at: '2022-03-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-64182739
              employee_id: WD-641873
              app_name: GitHub
              access_level: read_write
              granted_at: '2020-08-15T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-64183951
              employee_id: WD-641873
              app_name: Jira
              access_level: read_write
              granted_at: '2020-08-15T09:05:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-64187423
              employee_id: WD-641873
              group_name: engineers
              added_at: '2020-08-15T09:10:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.cooper@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop hardware failure - replacement request for departing employee
                  description: Departing Senior Engineer Ryan Cooper reports laptop VDB-HW-09567 has stopped working completely. Employee last day is 2025-10-10 and needs a temporary replacement to complete handover documentation.
                  status: open
                  priority: high
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
                  asset_id: VDB-HW-09567
            - tool: asset_management_api_get_device_details
              parameters:
                asset_id: VDB-HW-09567
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: laptop_standard
                warehouse_location: sf
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-84523
                email: ryan.cooper@vdb.com
            - tool: asset_management_api_retire_device
              parameters:
                asset_id: VDB-HW-09567
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  priority: high
                  type: problem
                  tags: offboarding
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-09567
    """

    validate_database(x)


def test_he_027(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like a keyboard for better typing experience during long coding sessions. My name is Ryan Cooper and my email is ryan.cooper@vdb.com.
    user_context: |
        You are Ryan Cooper, a Backend Developer at the company, contacting IT support to request a keyboard. You want a keyboard to improve your typing experience during long coding sessions. You have no specific brand or model preference.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415827
              email: ryan.cooper@vdb.com
              full_name: Ryan Cooper
              level: 3
              department: product_engineering
              role: Backend Developer
              office_location: austin
              start_date: '2023-05-15T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Ryan Cooper
              email: ryan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-738-4921
              verified: true
              active: true
              created_at: '2024-05-20T00:00:00Z'
              updated_at: '2024-05-20T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-38291
              device_type: keyboard
              device_model: Logitech Media K200
              purchase_date: '2025-06-12T00:00:00Z'
              warehouse_location: austin
              condition: new
              is_assigned: false
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_articles: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.cooper@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Keyboard Provision Request
                  description: Employee requests a keyboard for better typing experience during long coding sessions.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: keyboard
                warehouse_location: austin
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-38291
                email: ryan.cooper@vdb.com
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Keyboard Provision Request
                  description: Employee requests a keyboard for better typing experience during long coding sessions. Logitech Media K200 assigned from Austin inventory.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-38291
    """

    validate_database(x)


def test_he_028(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my monitor won't turn on at all. The power light doesn't come on even when plugged in. Could you replace it? My name is Nathan Price, email nathan.price@vdb.com.
    user_context: |
        You are Nathan Price, a Compliance Specialist at VDB, contacting IT support because your monitor (Dell P2422H) has stopped working entirely — no power light, no display, even when plugged in. You want a replacement.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL BEHAVIOR:
        - If the agent provides troubleshooting steps, agree to try them. Tell the agent you will try the steps and get back to them.
        - After the agent puts you on hold or acknowledges you'll try the steps, come back and report that none of the troubleshooting steps worked. The monitor still won't turn on — no power light at all, even after trying different cables, outlets, and ports. State clearly that the issue persists.
        - If the agent confirms a replacement monitor has been assigned, thank them and acknowledge any instructions about returning the old monitor.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-417385
              email: nathan.price@vdb.com
              full_name: Nathan Price
              level: 3
              department: compliance_risk
              role: Compliance Specialist
              office_location: nyc
              start_date: '2022-09-01T00:00:00Z'
              manager_id: WD-584201
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Price
              email: nathan.price@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-212-738-4519
              verified: true
              active: true
              created_at: '2024-09-10T00:00:00Z'
              updated_at: '2024-09-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-62815
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2022-07-10T00:00:00Z'
              warehouse_location: nyc
              condition: good
              is_assigned: true
            - id: VDB-HW-21567
              device_type: monitor
              device_model: Dell P2422H
              purchase_date: '2022-08-05T00:00:00Z'
              warehouse_location: nyc
              condition: poor
              is_assigned: true
            - id: VDB-HW-35847
              device_type: monitor
              device_model: Dell P2425H
              purchase_date: '2024-11-12T00:00:00Z'
              warehouse_location: nyc
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62718493
              asset_id: VDB-HW-62815
              employee_id: WD-417385
              assigned_at: '2022-09-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-41835926
              asset_id: VDB-HW-21567
              employee_id: WD-417385
              assigned_at: '2022-10-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.price@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.price@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Monitor not turning on — replacement request
                  description: Employee reports their monitor won't turn on; power light does not come on even when plugged in. Requesting replacement.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  description: 'Employee reports their monitor won''t turn on; power light does not come on even when plugged in. Requesting replacement. Troubleshooting steps provided: check power cable connections, try a different power outlet, try a different power cable, inspect the power port for damage, try connecting to a different device to isolate the issue.'
                  owner: it_support
                  approval_required: 'no'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: open
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: nathan.price@vdb.com
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: monitor
                warehouse_location: nyc
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-35847
                email: nathan.price@vdb.com
            - tool: asset_management_api_retire_device
              parameters:
                asset_id: VDB-HW-21567
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  description: Employee reports their monitor won't turn on; power light does not come on even when plugged in. Troubleshooting attempted and failed. Hardware failure confirmed. Replacement monitor Dell P2425H assigned (VDB-HW-35847). Old monitor VDB-HW-21567 retired.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-35847
    """

    validate_database(x)


def test_he_030(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my docking station keeps disconnecting my monitors randomly throughout the day. It's very disruptive to my work. Can you provide me another one? My name is Daniel Wright, email daniel.wright@vdb.com. The docking station asset ID is VDB-HW-50234.
    user_context: |
        You are Daniel Wright, a Senior Accountant at VDB, contacting IT support because your docking station keeps intermittently disconnecting your monitors. You initially want a replacement docking station. However, if the agent explains that troubleshooting steps must be tried first before a replacement can be considered, accept that and agree to try the suggested troubleshooting steps. After receiving the troubleshooting steps, tell the agent you will try them and get back to them later with the results.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415937
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 4
              department: finance_accounting
              role: Senior Accountant
              office_location: sf
              start_date: '2021-03-15T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Wright
              email: daniel.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-8294
              verified: true
              active: true
              created_at: '2024-04-10T00:00:00Z'
              updated_at: '2024-04-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-50234
              device_type: docking_station
              device_model: Lenovo ThinkPad USB-C Dock
              purchase_date: '2021-02-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-62891
              device_type: laptop_standard
              device_model: Dell Latitude 5520
              purchase_date: '2021-01-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-50234178
              asset_id: VDB-HW-50234
              employee_id: WD-415937
              assigned_at: '2021-06-01T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-62891435
              asset_id: VDB-HW-62891
              employee_id: WD-415937
              assigned_at: '2021-04-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.wright@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.wright@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: daniel.wright@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Docking station intermittently disconnecting monitors
                  description: Employee reports docking station VDB-HW-50234 (Lenovo ThinkPad USB-C Dock) intermittently disconnects monitors throughout the day. Troubleshooting steps to be provided.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Docking station intermittently disconnecting monitors
                  description: Employee reports docking station VDB-HW-50234 (Lenovo ThinkPad USB-C Dock) intermittently disconnects monitors throughout the day. Troubleshooting steps provided to employee; awaiting feedback on results.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  asset_id: VDB-HW-50234
    """

    validate_database(x)


def test_he_031(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Rachel Cooper (rachel.cooper@vdb.com). My headset audio is crackling and the ear cushions are worn out. I'm on calls all day and need a replacement. The headset is a Jabra Evolve2 40, asset ID VDB-HW-31234.
    user_context: |
        You are Rachel Cooper, a Customer Success Manager contacting IT support about your malfunctioning headset. Your email is rachel.cooper@vdb.com.

        CONVERSATION FLOW:
        1. When the agent provides troubleshooting steps, agree to try them. Say something like: "Okay, I'll give those a try and get back to you."
        2. After the agent acknowledges and puts things on hold, come back and report that the troubleshooting steps did not help. Say something like: "Hi, I tried all the troubleshooting steps but the audio is still crackling and the ear cushions are still worn out. Nothing improved."
        3. After that, cooperate with whatever the agent needs to complete the replacement process.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415738
              email: rachel.cooper@vdb.com
              full_name: Rachel Cooper
              level: 4
              department: customer_support
              role: Customer Success Manager
              office_location: austin
              start_date: '2022-06-01T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Rachel Cooper
              email: rachel.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-734-8291
              verified: true
              active: true
              created_at: '2024-06-01T00:00:00Z'
              updated_at: '2024-06-01T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-62847
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2022-06-01T00:00:00Z'
              warehouse_location: austin
              condition: good
              is_assigned: true
            - id: VDB-HW-31234
              device_type: headset
              device_model: Jabra Evolve2 40
              purchase_date: '2022-07-15T00:00:00Z'
              warehouse_location: austin
              condition: poor
              is_assigned: true
            - id: VDB-HW-36291
              device_type: headset
              device_model: Logitech H650e
              purchase_date: '2024-08-15T00:00:00Z'
              warehouse_location: austin
              condition: new
              is_assigned: false
            - id: VDB-HW-48173
              device_type: headset
              device_model: Logitech Zone Wired 2
              purchase_date: '2024-09-01T00:00:00Z'
              warehouse_location: austin
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-28463917
              asset_id: VDB-HW-62847
              employee_id: WD-415738
              assigned_at: '2022-07-05T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-51739482
              asset_id: VDB-HW-31234
              employee_id: WD-415738
              assigned_at: '2022-07-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.cooper@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: rachel.cooper@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Headset audio issues – crackling and worn ear cushions
                  description: Employee reports company headset (VDB-HW-31234, Jabra Evolve2 40) has crackling audio and worn out ear cushions. Employee is on calls all day and requests replacement. Troubleshooting steps provided.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
                  due_at: null
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: hold
                  type: problem
                  priority: normal
                  subject: Headset audio issues – crackling and worn ear cushions
                  description: Employee reports company headset (VDB-HW-31234, Jabra Evolve2 40) has crackling audio and worn out ear cushions. Troubleshooting steps provided to employee, awaiting feedback.
                  owner: it_support
                  approval_required: 'no'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: open
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: headset
                warehouse_location: austin
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-36291
                email: rachel.cooper@vdb.com
            - tool: asset_management_api_retire_device
              parameters:
                asset_id: VDB-HW-31234
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Headset audio issues – crackling and worn ear cushions
                  description: Employee reported company headset (VDB-HW-31234, Jabra Evolve2 40) with crackling audio and worn ear cushions. Troubleshooting attempted and did not resolve the issue. New headset (Logitech H650e, VDB-HW-36291) assigned. Old device (VDB-HW-31234) retired and return initiated.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-36291
    """

    validate_database(x)


def test_he_032(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need a more powerful laptop - my current one just can't keep up anymore.
    user_context: |
        You are Ryan Cooper, a Platform Engineer at VDB, contacting IT support to request a laptop upgrade. Your current laptop is too slow for your work.

        Only if you are asked about your email address or contact information — tell the agent your email is ryan.cooper@vdb.com.
        Only if you are asked about your current laptop or what device you have — tell the agent you have a Dell Latitude 5440 and it's functional but painfully slow.
        Only if you are asked about your role or what kind of work you do — explain that you're a Platform Engineer and you spend a lot of time working with container workloads.
        Only if you are asked why your laptop is slow or what specific issues you're experiencing — explain that running Kubernetes locally maxes out your current machine and it's painfully slow when you spin up local clusters.
        Only if you are asked about what kind of upgrade you want — mention you'd like to upgrade to a high-performance model if possible.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-618234
              email: ryan.cooper@vdb.com
              full_name: Ryan Cooper
              level: 4
              department: product_engineering
              role: Platform Engineer
              office_location: sf
              start_date: '2021-11-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Ryan Cooper
              email: ryan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-729-3841
              verified: true
              active: true
              created_at: '2024-02-15T00:00:00Z'
              updated_at: '2024-02-15T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-10456
              device_type: laptop_standard
              device_model: Dell Latitude 5440
              purchase_date: '2022-01-15T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-36291
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: '2024-09-10T00:00:00Z'
              warehouse_location: sf
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62184537
              asset_id: VDB-HW-10456
              employee_id: WD-618234
              assigned_at: '2022-02-01T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_articles: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.cooper@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: ryan.cooper@vdb.com
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: laptop_standard
                warehouse_location: sf
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop refresh request — Standard laptop replacement
                  description: Employee Ryan Cooper (Platform Engineer, product_engineering) requests a laptop upgrade. Current Dell Latitude 5440 (VDB-HW-10456) is 47 months old and performing slowly for container/Kubernetes workloads. Auto-approved refresh as device age exceeds the 36-month threshold. Assigning Lenovo ThinkBook 14+ from SF inventory.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
            - tool: asset_management_api_retire_device
              parameters:
                asset_id: VDB-HW-10456
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-36291
                email: ryan.cooper@vdb.com
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Laptop refresh request — Standard laptop replacement [Resolved]
                  description: Laptop refresh completed for Ryan Cooper (Platform Engineer). Old Dell Latitude 5440 (VDB-HW-10456) retired. New Lenovo ThinkBook 14+ (VDB-HW-36291) assigned. Auto-approved refresh — device age 47 months exceeds 36-month threshold. No approval required.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-36291
    """

    validate_database(x)


def test_he_033(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Natalie Brooks from HR, my email is natalie.brooks@vdb.com. I started a month ago and I'd like to request a monitor for my workstation please.
    user_context: |
        You are Natalie Brooks, a newly hired HR Coordinator who has been working for about a month. You are contacting IT support to request a monitor.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent asks about other missing equipment, say you are only requesting a monitor at this time and will handle other equipment requests separately.

        If the agent asks for a business justification for the monitor, respond with something like: "I need a monitor to efficiently perform my HR Coordinator duties — reviewing employee records and documents on a larger screen improves my productivity significantly."
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637284
              email: natalie.brooks@vdb.com
              full_name: Natalie Brooks
              level: 3
              department: hr
              role: HR Coordinator
              office_location: nyc
              start_date: '2025-09-01T00:00:00Z'
              manager_id: WD-415837
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-415837
              email: rachel.foster@vdb.com
              full_name: Rachel Foster
              level: 5
              department: hr
              role: HR Manager
              office_location: nyc
              start_date: '2020-08-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Natalie Brooks
              email: natalie.brooks@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-646-389-7214
              verified: true
              active: true
              created_at: '2025-09-01T00:00:00Z'
              updated_at: '2025-09-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_articles: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: natalie.brooks@vdb.com
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: natalie.brooks@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'natalie.brooks@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Monitor Provision Request
                  description: Employee (HR Coordinator, NYC) requests a monitor. Started a month ago, no equipment received yet.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: natalie.brooks@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: rachel.foster@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: natalie.brooks@vdb.com
                approver_email: rachel.foster@vdb.com
                details: 'Monitor provision request for HR Coordinator. Business justification: I need a monitor to efficiently perform my HR Coordinator duties — reviewing employee records and documents on a larger screen improves my productivity significantly.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Monitor Provision Request
                  description: Employee (HR Coordinator, NYC) requests monitor provision. Business justification provided.
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-415837
                  approval_request_ids: APR-00000007
                  business_justification: I need a monitor to efficiently perform my HR Coordinator duties — reviewing employee records and documents on a larger screen improves my productivity significantly.
    """

    validate_database(x)


def test_he_035(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to request a backup headset. Could you help me with that?
    user_context: |
        You are Daniel Brooks, a Technical Support Specialist in the customer support department, contacting IT support to request a backup headset. You already have one headset assigned (VDB-HW-32456) and want a second one as a backup in case your primary fails during important customer calls. You have no preference for a specific headset model.

        Only if you are asked for your name or to identify yourself — tell the agent you are Daniel Brooks.
        Only if you are asked for your email address or contact information — tell the agent it is daniel.brooks@vdb.com.
        Only if you are asked about your department or team — tell the agent you are from the customer support team.
        Only if you are asked about your current headset or existing equipment — tell the agent your current headset is asset ID VDB-HW-32456.
        Only if you are asked why you need a backup or the reason for the request — explain that you need it in case your primary one fails during important customer calls.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-427583
              email: daniel.brooks@vdb.com
              full_name: Daniel Brooks
              level: 3
              department: customer_support
              role: Technical Support Specialist
              office_location: austin
              start_date: '2023-03-15T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Brooks
              email: daniel.brooks@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-847-3261
              verified: true
              active: true
              created_at: '2024-04-10T00:00:00Z'
              updated_at: '2024-04-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-32456
              device_type: headset
              device_model: Jabra Evolve2 75
              purchase_date: '2023-04-10T00:00:00Z'
              warehouse_location: austin
              condition: good
              is_assigned: true
            - id: VDB-HW-38291
              device_type: headset
              device_model: Logitech H650e
              purchase_date: '2024-06-15T00:00:00Z'
              warehouse_location: austin
              condition: new
              is_assigned: false
            - id: VDB-HW-42718
              device_type: headset
              device_model: Logitech Zone Wired 2
              purchase_date: '2024-07-20T00:00:00Z'
              warehouse_location: austin
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62384917
              asset_id: VDB-HW-32456
              employee_id: WD-427583
              assigned_at: '2023-04-15T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.brooks@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.brooks@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Backup Headset Request
                  description: Employee requests a second/backup headset in case primary headset fails during important customer calls. Currently has one headset assigned (VDB-HW-32456).
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: headset
                warehouse_location: austin
            - tool: asset_management_api_assign_device
              parameters:
                asset_id: VDB-HW-38291
                email: daniel.brooks@vdb.com
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  resolution_category: provisioned
                  asset_id: VDB-HW-38291
    """

    validate_database(x)


def test_he_036(x: TestContext, judge: Judge):
    """!
    query: |
        Hey, I need a laptop with more RAM for data pipeline development. The standard one keeps running out of memory. My name is Ryan Cooper, email ryan.cooper@vdb.com. Can I get a high-performance laptop?
    user_context: |
        You are Ryan Cooper, a contract Data Engineer at the company, contacting IT support because your current standard laptop doesn't have enough RAM for your data pipeline development work. You want a laptop replacement with better specs. A standard Windows laptop with more RAM would meet your needs; you do not need a MacBook or premium device.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent informs you that manager approval is needed, acknowledge and say you understand.
        - If the agent offers a MacBook or premium laptop option, decline and clarify that a standard Windows laptop is sufficient for your needs.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637285
              email: ryan.cooper@vdb.com
              full_name: Ryan Cooper
              level: 4
              department: product_engineering
              role: Data Engineer
              office_location: remote
              start_date: '2025-03-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: true
              remote_delivery_address: 1823 Maple Ave, Portland, OR 97214
              contract_end_date: '2026-02-28T00:00:00Z'
          zendesk_users:
            - id: '6'
              name: Ryan Cooper
              email: ryan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-503-847-2196
              verified: true
              active: true
              created_at: '2025-03-01T00:00:00Z'
              updated_at: '2025-03-01T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-63728
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: '2025-02-15T00:00:00Z'
              warehouse_location: remote_ship
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-63728194
              asset_id: VDB-HW-63728
              employee_id: WD-637285
              assigned_at: '2025-03-01T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_articles: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.cooper@vdb.com'
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: ryan.cooper@vdb.com
            - tool: asset_management_api_get_device_details
              parameters:
                asset_id: VDB-HW-63728
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop replacement request - Standard laptop refresh
                  description: 'Employee (contractor, Data Engineer, product_engineering) requests laptop replacement due to insufficient RAM for data pipeline development. Current laptop: Lenovo ThinkBook 14+, age ~10 months. Replacement reason: refresh. Manager approval required.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
                  approval_required: 'yes'
                  asset_id: VDB-HW-63728
            - tool: workday_api_get_manager_chain
              parameters:
                email: ryan.cooper@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: sarah.jones@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: ryan.cooper@vdb.com
                approver_email: sarah.jones@vdb.com
                details: 'Laptop replacement request (refresh). Employee requests Standard laptop replacement for data pipeline development—current laptop running out of memory. Current device: Lenovo ThinkBook 14+, age ~10 months. Business justification: need more RAM for data pipeline development, current laptop running out of memory.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Laptop replacement request - Standard laptop refresh
                  description: 'Employee (contractor, Data Engineer, product_engineering) requests laptop replacement due to insufficient RAM for data pipeline development. Current laptop: Lenovo ThinkBook 14+, age ~10 months. Replacement reason: refresh. Device age < 36 months — Manager approval required.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: Need laptop with more RAM for data pipeline development. Standard laptop running out of memory.
                  approver_id: WD-681453
                  approval_request_ids: APR-00000007
                  asset_id: VDB-HW-63728
    """

    validate_database(x)


def test_he_037(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Natalie Park from the Product Design team (natalie.park@vdb.com). I need a Wacom tablet for detailed UI illustration work. It would greatly improve my productivity for the design projects I'm working on. Can you help me get one provisioned?
    user_context: |
        You are Natalie Park, a Product Designer requesting a Wacom graphics tablet for your design work. You believe it would help with detailed UI illustration.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent denies your request, you may express mild disappointment but accept the decision. Do not escalate or argue excessively.
        - If the agent offers alternative hardware or devices after denying the Wacom tablet request, politely decline and indicate you have no other requests at this time.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-629471
              email: natalie.park@vdb.com
              full_name: Natalie Park
              level: 3
              department: product_engineering
              role: Product Designer
              office_location: sf
              start_date: '2024-02-15T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Natalie Park
              email: natalie.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-736-8294
              verified: true
              active: true
              created_at: '2024-02-20T00:00:00Z'
              updated_at: '2024-02-20T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-38261
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2024-02-10T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62947183
              asset_id: VDB-HW-38261
              employee_id: WD-629471
              assigned_at: '2024-02-18T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41763928
              employee_id: WD-629471
              app_name: Figma
              access_level: read_write
              granted_at: '2024-02-16T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-53287461
              employee_id: WD-629471
              app_name: Jira
              access_level: read_write
              granted_at: '2024-02-16T09:05:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-83461927
              employee_id: WD-629471
              group_name: engineers
              added_at: '2024-02-16T09:00:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: natalie.park@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'natalie.park@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Graphics Tablet Provision Request
                  description: Employee requests a Wacom graphics tablet for detailed UI illustration work. Device category is not in the supported list per company policy.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  tags: null
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Graphics Tablet Provision Request
                  description: Employee requests a Wacom graphics tablet for detailed UI illustration work. Device category is not in the supported list per company policy. Request denied.
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: denied
    """

    validate_database(x)


def test_he_038(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Ryan Cooper (ryan.cooper@vdb.com). My laptop replacement was approved last week. When can I pick it up from the IT office?
    user_context: |
        You are Ryan Cooper, an IT Support Analyst following up on a previously approved laptop replacement request. You want to know when your new laptop will be ready for pickup at the NYC IT office.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637284
              email: ryan.cooper@vdb.com
              full_name: Ryan Cooper
              level: 3
              department: it_operations
              role: IT Support Analyst
              office_location: nyc
              start_date: '2022-12-01T00:00:00Z'
              manager_id: WD-495826
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Ryan Cooper
              email: ryan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-646-718-3294
              verified: true
              active: true
              created_at: '2024-06-10T00:00:00Z'
              updated_at: '2024-06-10T00:00:00Z'
          zendesk_tickets:
            - id: '6'
              subject: Laptop Replacement Request
              description: 'Laptop replacement request for Ryan Cooper (IT Operations). Current laptop VDB-HW-38291 (Dell Latitude 5420) is over 36 months old and experiencing performance degradation. Approved for standard laptop replacement. Procurement order HW-ORDER-9382751 created on 2025-09-26 for laptop_standard. Expected delivery date: 2025-10-10. Ship to: NYC IT Office, 789 Broadway, New York, NY 10003.'
              status: pending
              priority: normal
              type: problem
              requester_id: '6'
              assignee_id: '2'
              organization_id: '1'
              tags: []
              created_at: '2025-09-25T10:00:00Z'
              updated_at: '2025-09-26T14:00:00Z'
              due_at: null
              resolution_category: null
              owner: it_support
              access_expiry_date: null
              approval_required: 'yes'
              approval_status: approved
              approver_id: WD-495826
              approval_request_ids: APR-47283916
              business_justification: null
              incident_severity: null
              customer_impact: null
              asset_id: VDB-HW-38291
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-38291
              device_type: laptop_standard
              device_model: Dell Latitude 5420
              purchase_date: '2022-06-10T00:00:00Z'
              warehouse_location: nyc
              condition: fair
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-82647193
              asset_id: VDB-HW-38291
              employee_id: WD-637284
              assigned_at: '2022-12-05T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_procurement_orders:
            - id: HW-ORDER-9382751
              device_type: laptop_standard
              device_model: Dell Latitude 5440
              quantity: 1
              ship_to_location: NYC IT Office, 789 Broadway, New York, NY 10003
              requester_id: WD-637284
              ticket_id: '6'
              status: ordered
              created_at: '2025-09-26T14:00:00Z'
              expected_delivery_date: '2025-10-10'
              delivered_at: null
          sandbox_neobank_support_main_models_approval_requests:
            - id: APR-47283916
              request_type: hardware_purchase
              requester_id: WD-637284
              approver_id: WD-495826
              status: approved
              urgency: standard
              details: Laptop replacement request for Ryan Cooper. Current laptop VDB-HW-38291 (Dell Latitude 5420) is over 36 months old and experiencing performance degradation. Approved for standard laptop replacement.
              ticket_id: '6'
              created_at: '2025-09-25T10:30:00Z'
              decided_at: '2025-09-25T15:00:00Z'
              approver_feedback: Approved - laptop exceeds 36-month refresh cycle
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.cooper@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.cooper@vdb.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                $filter: requester_id eq '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: open
    """

    validate_database(x)


def test_he_039(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need an additional monitor for my office setup. Can you help me get this set up?
    user_context: |
        You are Derek Wilson, a Sales Director at VDB, contacting IT support to request a third monitor for your office.

        Only if you are asked about your email address — tell the agent it is derek.wilson@vdb.com
        Only if you are asked about your current setup or how many monitors you have — you currently have two monitors but need a third one
        Only if you are asked why you need the additional monitor or about the reason — you need to manage multiple sales dashboards and CRM windows simultaneously which requires more screen real estate

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415738
              email: derek.wilson@vdb.com
              full_name: Derek Wilson
              level: 6
              department: sales
              role: Sales Director
              office_location: sf
              start_date: '2019-06-01T00:00:00Z'
              manager_id: WD-637284
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-637284
              email: rachel.cooper@vdb.com
              full_name: Rachel Cooper
              level: 8
              department: sales
              role: VP of Sales
              office_location: sf
              start_date: '2018-09-10T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-20789
              device_type: monitor
              device_model: Dell UltraSharp 27 U2723DE
              purchase_date: '2023-05-15T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-20790
              device_type: monitor
              device_model: Dell UltraSharp 27 U2723DE
              purchase_date: '2023-05-15T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-20788
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2022-03-10T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-20789415
              asset_id: VDB-HW-20789
              employee_id: WD-415738
              assigned_at: '2023-06-01T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-20790415
              asset_id: VDB-HW-20790
              employee_id: WD-415738
              assigned_at: '2023-06-01T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-20788415
              asset_id: VDB-HW-20788
              employee_id: WD-415738
              assigned_at: '2022-04-01T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_users:
            - id: '6'
              name: Derek Wilson
              email: derek.wilson@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-736-8291
              verified: true
              active: true
              created_at: '2024-02-15T00:00:00Z'
              updated_at: '2024-02-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_articles: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: derek.wilson@vdb.com
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: derek.wilson@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'derek.wilson@vdb.com'
            - tool: workday_api_get_manager_chain
              parameters:
                email: derek.wilson@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: rachel.cooper@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Third Monitor Request - Sales Director
                  description: 'Employee Derek Wilson requests a third monitor for their SF office setup. Currently has two monitors assigned (VDB-HW-20789, VDB-HW-20790). Business justification: managing multiple sales dashboards and CRM windows simultaneously. Manager approval required.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  tags: null
                  due_at: null
                  owner: it_support
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: derek.wilson@vdb.com
                approver_email: rachel.cooper@vdb.com
                details: 'Third monitor request for Sales Director Derek Wilson. Currently has two monitors (VDB-HW-20789, VDB-HW-20790). Business justification: managing multiple sales dashboards and CRM windows simultaneously.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Third Monitor Request - Sales Director
                  description: 'Employee Derek Wilson requests a third monitor for their SF office setup. Currently has two monitors assigned (VDB-HW-20789, VDB-HW-20790). Business justification: managing multiple sales dashboards and CRM windows simultaneously. Manager approval required.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: I need a third monitor - managing multiple sales dashboards and CRM windows simultaneously.
                  approver_id: WD-637284
                  approval_request_ids: APR-00000007
    """

    validate_database(x)


def test_he_040(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Nathan Price (nathan.price@vdb.com). My laptop charger cable is frayed near the connector and sometimes doesn't charge. I'm worried it might be a fire hazard. The asset ID for my laptop is VDB-HW-60123. Can I get a replacement charger?
    user_context: |
        You are Nathan Price, a Treasury Analyst at VDB, contacting IT support because your laptop charger cable is frayed and intermittently fails to charge. You are concerned it could be a fire hazard and want a replacement.

        You are based in the NYC office and can easily visit the local IT office during business hours to pick up items if directed to do so.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-641827
              email: nathan.price@vdb.com
              full_name: Nathan Price
              level: 4
              department: finance_accounting
              role: Treasury Analyst
              office_location: nyc
              start_date: '2023-08-15T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Price
              email: nathan.price@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-212-847-3291
              verified: true
              active: true
              created_at: '2024-05-10T00:00:00Z'
              updated_at: '2024-05-10T00:00:00Z'
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-60123
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2023-08-20T00:00:00Z'
              warehouse_location: nyc
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-64182739
              asset_id: VDB-HW-60123
              employee_id: WD-641827
              assigned_at: '2023-08-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-64182935
              employee_id: WD-641827
              app_name: Slack
              access_level: read_write
              granted_at: '2023-08-16T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-64127893
              employee_id: WD-641827
              group_name: finance_team
              added_at: '2023-08-16T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.price@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.price@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop charger damaged - frayed cable near connector
                  description: 'Employee reports laptop charger cable is frayed near the connector and intermittently fails to charge. Employee is concerned about potential fire hazard. Asset ID: VDB-HW-60123.'
                  status: open
                  priority: low
                  type: question
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: question
                  priority: low
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
                  asset_id: VDB-HW-60123
    """

    validate_database(x)


def test_ie_001(x: TestContext, judge: Judge):
    """!
    query: |
        SEV1 - payments are down. I need production DB read-only access immediately to diagnose the issue. This is Daniel Park, daniel.park@vdb.com, Senior Backend Engineer. Payment processing is completely down and all customers are affected. Please expedite.
    user_context: |
        You are Daniel Park, a Senior Backend Engineer in Product Engineering, urgently requesting production database read-only access during an active SEV1 incident where payment processing is completely down for all customers. You need this access to diagnose and help resolve the outage.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Convey urgency appropriate for a SEV1 incident — this is a critical production outage.
        - If asked to confirm details or the nature of the incident, confirm that payment processing is completely down and affecting all customers.
        - If asked what level of access you need, specify read-only access to the production database.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637182
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 5
              department: product_engineering
              role: Senior Backend Engineer
              office_location: sf
              start_date: '2020-07-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-681453
              email: sarah.jones@vdb.com
              full_name: Sarah Jones
              level: 7
              department: product_engineering
              role: VP of Engineering
              office_location: sf
              start_date: '2017-05-10T00:00:00Z'
              manager_id: WD-524893
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_security_incidents:
            - id: SEC-38291574
              employee_id: WD-495826
              severity: SEV1
              incident_type: payment_system_outage
              description: Payment processing system completely down - all customer transactions failing
              status: open
              is_active: true
              reported_at: '2025-10-01T12:00:00Z'
              reported_by: monitoring_system
              resolved_at: null
              resolution_notes: null
          zendesk_users:
            - id: '6'
              name: Daniel Park
              email: daniel.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-736-8294
              verified: true
              active: true
              created_at: '2024-07-10T00:00:00Z'
              updated_at: '2024-07-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.park@vdb.com
            - tool: security_api_verify_incident
              parameters: {}
            - tool: okta_api_check_access
              parameters:
                email: daniel.park@vdb.com
                app_name: Production database
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.park@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: 'SEV1 Incident: Production Database Read-Only Access Request'
                  description: 'SEV1 - Payment processing is completely down affecting all customers. Employee Daniel Park (Senior Backend Engineer, Product Engineering) requests production database read-only access to diagnose the issue. Active incident: SEC-38291574.'
                  status: open
                  priority: urgent
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: okta_api_provision_access
              parameters:
                email: daniel.park@vdb.com
                app_name: Production database
                access_level: read_only
                is_temporary: true
                access_expiry_date: '2025-10-02T13:00:00Z'
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.park@vdb.com
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: email_notification_api_send_notification
              parameters:
                recipient_email: sarah.jones@vdb.com
                notification_type: post_facto_manager_alert
                subject: 'Post-Facto Alert: Production Database Access Granted to Daniel Park During SEV1 Incident'
                body: This is a post-facto notification that production database read-only access has been granted to Daniel Park (Senior Backend Engineer, Product Engineering) during active SEV1 incident SEC-38291574 (payment processing outage). Access is temporary and will expire on 2025-10-02T13:00:00Z (24 hours). No prior approval was required per SEV1 emergency access procedures.
                ticket_id: '6'
                priority: urgent
            - tool: email_notification_api_send_notification
              parameters:
                recipient_email: amanda.lee@vdb.com
                notification_type: incident_access_granted
                subject: 'Incident Access Granted: Production Database Read-Only for Daniel Park - SEV1 Payment Processing Outage'
                body: 'Production database read-only access has been provisioned to Daniel Park (WD-637182, Senior Backend Engineer, Product Engineering) in response to active SEV1 incident SEC-38291574 - payment processing system completely down. Access is temporary for 24 hours, expiring 2025-10-02T13:00:00Z. Ticket ID: 6. This notification is sent per SEV1 post-facto notification requirements.'
                ticket_id: '6'
                priority: urgent
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: urgent
                  subject: 'SEV1 Incident: Production Database Read-Only Access Request'
                  description: 'SEV1 - Payment processing is completely down affecting all customers. Employee Daniel Park (Senior Backend Engineer, Product Engineering) requested production database read-only access to diagnose the issue. Active incident: SEC-38291574. Resolution: Access provisioned immediately per SEV1 procedures. Temporary 24-hour read-only access granted (expires 2025-10-02T13:00:00Z). Post-facto notifications sent to manager and IT Security.'
                  tags: production_access,temporary_access
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  incident_severity: sev1_critical
                  customer_impact: yes_active
                  access_expiry_date: '2025-10-02T13:00:00Z'
                  business_justification: SEV1 incident - payment processing completely down affecting all customers. Production DB read-only access needed to diagnose root cause.
    """

    validate_database(x)


def test_ie_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Daniel Park (daniel.park@vdb.com), Platform Engineer. The SEV2 incident from yesterday — the payment processing service degradation — is still being investigated. My temporary AWS Production access that was granted for it expires in about an hour. Can I get a 24-hour extension so I can continue working on the incident? I haven't obtained verbal or Slack approval from my manager yet.
    user_context: |
        You are Daniel Park, a Platform Engineer at the company, contacting IT support to request an extension of your temporary AWS Production access due to an ongoing SEV2 incident.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If asked whether you have already obtained verbal or Slack approval from your manager for this extension, answer that you have NOT yet obtained it. You've been focused on the incident investigation and haven't had a chance to reach out to your manager yet.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637284
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 4
              department: product_engineering
              role: Platform Engineer
              office_location: sf
              start_date: '2021-06-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_security_incidents:
            - id: SEC-38274951
              employee_id: WD-637284
              severity: SEV2
              incident_type: service_degradation
              description: Payment processing service degradation affecting customer transactions
              status: investigating
              is_active: true
              reported_at: '2025-09-30T08:00:00Z'
              reported_by: monitoring_system
              resolved_at: null
              resolution_notes: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-42718369
              employee_id: WD-637284
              app_name: AWS Production
              access_level: user
              granted_at: '2025-09-30T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: true
              expires_at: '2025-10-01T14:00:00Z'
          zendesk_users:
            - id: '6'
              name: Daniel Park
              email: daniel.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-736-2189
              verified: true
              active: true
              created_at: '2024-06-01T00:00:00Z'
              updated_at: '2024-06-01T00:00:00Z'
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-83724159
              employee_id: WD-637284
              group_name: engineers
              added_at: '2021-06-02T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.park@vdb.com
            - tool: security_api_verify_incident
              parameters: {}
            - tool: okta_api_check_access
              parameters:
                email: daniel.park@vdb.com
                app_name: AWS Production
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.park@vdb.com'
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.park@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: sarah.jones@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: AWS Production Access Extension - Active SEV2 Incident
                  description: Employee requests 24-hour extension of temporary AWS Production (user) access. Current access expiring soon. Active SEV2 incident still under investigation. Treating as new access request per extension policy. Manager approval required.
                  status: open
                  priority: urgent
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.park@vdb.com
                approver_email: sarah.jones@vdb.com
                details: 'Extension of temporary AWS Production (user) access for 24 hours during active SEV2 incident. Employee''s current access is expiring. Business justification: SEV2 incident from previous day still under investigation.'
                urgency: critical
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  subject: AWS Production Access Extension - Active SEV2 Incident
                  description: Employee requests 24-hour extension of temporary AWS Production (user) access. Active SEV2 incident still under investigation. Fresh manager approval required per extension policy. Awaiting manager approval.
                  status: pending
                  priority: urgent
                  type: problem
                  tags: production_access,temporary_access
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-681453
                  approval_request_ids: APR-00000007
                  incident_severity: sev2_high
                  customer_impact: yes_active
                  access_expiry_date: '2025-10-02T13:00:00Z'
                  business_justification: SEV2 incident from previous day still under active investigation; production access extension required to continue incident response.
    """

    validate_database(x)


def test_ie_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Derek Walsh, Network Engineer, email derek.walsh@vdb.com. There's an active SEV1 incident — VPN gateway failure affecting all remote employees. I need engineer_prod VPN access to help troubleshoot from the backup connection. Can you grant me temporary access?
    user_context: |
        You are Derek Walsh, a Network Engineer in IT Operations, contacting IT support during an active SEV1 incident. The VPN gateway has failed and all remote employees have lost access to production systems. You urgently need engineer_prod level VPN access to troubleshoot the gateway from a backup connection. You are stressed and want this resolved as fast as possible.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm details about the request, confirm: you need VPN access at engineer_prod level to troubleshoot the VPN gateway failure.
        - Convey urgency throughout the conversation given the SEV1 nature of the incident.
        - You do not know any technical details beyond what is stated above. If asked for details you don't have, say you are not sure.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-412873
              email: derek.walsh@vdb.com
              full_name: Derek Walsh
              level: 4
              department: it_operations
              role: Network Engineer
              office_location: sf
              start_date: '2022-05-01T00:00:00Z'
              manager_id: WD-638172
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-638172
              email: nathan.price@vdb.com
              full_name: Nathan Price
              level: 6
              department: it_operations
              role: IT Operations Manager
              office_location: sf
              start_date: '2020-03-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_security_incidents:
            - id: SEC-37295184
              employee_id: WD-638172
              severity: SEV1
              incident_type: vpn_gateway_failure
              description: VPN gateway failure - all remote employees unable to access production systems
              status: open
              is_active: true
              reported_at: '2025-10-01T12:00:00Z'
              reported_by: monitoring_system
              resolved_at: null
              resolution_notes: null
          zendesk_users:
            - id: '6'
              name: Derek Walsh
              email: derek.walsh@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-729-4831
              verified: true
              active: true
              created_at: '2024-07-10T00:00:00Z'
              updated_at: '2024-07-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: derek.walsh@vdb.com
            - tool: security_api_verify_incident
              parameters: {}
            - tool: okta_api_check_access
              parameters:
                email: derek.walsh@vdb.com
                app_name: VPN
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'derek.walsh@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: VPN Engineer_Prod Access Request – SEV1 Incident Response
                  description: SEV1 CRITICAL – VPN gateway down company-wide. Employee requests VPN engineer_prod access to troubleshoot gateway from backup connection.
                  status: open
                  priority: urgent
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: okta_api_provision_access
              parameters:
                email: derek.walsh@vdb.com
                app_name: VPN
                access_level: engineer_prod
                is_temporary: true
                access_expiry_date: '2025-10-02T13:00:00Z'
            - tool: workday_api_get_manager_chain
              parameters:
                email: derek.walsh@vdb.com
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: email_notification_api_send_notification
              parameters:
                recipient_email: nathan.price@vdb.com
                notification_type: post_facto_manager_alert
                subject: 'Post-Facto Alert: VPN Engineer_Prod Access Granted During SEV1 Incident'
                body: 'This is a post-facto notification that VPN engineer_prod access has been granted to Derek Walsh (Network Engineer, IT Operations) during an active SEV1 incident (VPN gateway failure – SEC-37295184). Access is temporary and will expire at 2025-10-02T13:00:00Z (24 hours). Zendesk Ticket ID: 6.'
                ticket_id: '6'
                priority: urgent
            - tool: email_notification_api_send_notification
              parameters:
                recipient_email: amanda.lee@vdb.com
                notification_type: incident_access_granted
                subject: 'Incident Access Granted: VPN Engineer_Prod – SEV1'
                body: 'VPN engineer_prod access has been granted to Derek Walsh (WD-412873, Network Engineer, IT Operations) in response to active SEV1 incident SEC-37295184 (VPN gateway failure). Access is temporary and expires at 2025-10-02T13:00:00Z. Zendesk Ticket ID: 6. Post-facto IT Security notification per incident response procedures.'
                ticket_id: '6'
                priority: urgent
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  type: problem
                  priority: urgent
                  status: solved
                  subject: VPN Engineer_Prod Access Request – SEV1 Incident Response
                  description: 'SEV1 CRITICAL – VPN gateway down company-wide. Employee requests VPN engineer_prod access to troubleshoot gateway from backup connection. Resolution: VPN engineer_prod access provisioned immediately under SEV1 incident response procedure. Access is temporary (24 hours, expires 2025-10-02T13:00:00Z). Post-facto notifications sent to manager and IT Security.'
                  tags: production_access,temporary_access
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  incident_severity: sev1_critical
                  customer_impact: yes_potential
                  access_expiry_date: '2025-10-02T13:00:00Z'
                  business_justification: SEV1 critical VPN gateway failure causing company-wide remote access outage. Engineer_prod VPN access needed to troubleshoot gateway from backup connection.
    """

    validate_database(x)


def test_ie_009(x: TestContext, judge: Judge):
    """!
    query: |
        SEV1 - All payments are down. I'm joining the incident response and need AWS Production access to coordinate the recovery effort and review infrastructure status. This is Daniel Wright, CTO — daniel.wright@vdb.com. Please expedite, this is a critical outage affecting all customers.
    user_context: |
        You are Daniel Wright, CTO at the company, contacting IT support during a critical SEV1 incident — a complete payment system outage affecting all customers. You need AWS Production access urgently to coordinate the incident response and review infrastructure status.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Convey urgency appropriate for a SEV1 incident, but remain professional.
        - If asked to confirm details or the access request, confirm promptly.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-384927
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 9
              department: executive_leadership
              role: Chief Technology Officer
              office_location: sf
              start_date: '2019-01-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_security_incidents:
            - id: SEC-37529184
              employee_id: WD-495826
              severity: SEV1
              incident_type: payment_system_outage
              description: Complete payment system outage affecting all customers
              status: open
              is_active: true
              reported_at: '2025-10-01T12:30:00Z'
              reported_by: monitoring_system
              resolved_at: null
              resolution_notes: null
          zendesk_users:
            - id: '6'
              name: Daniel Wright
              email: daniel.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-739-4821
              verified: true
              active: true
              created_at: '2024-09-10T00:00:00Z'
              updated_at: '2024-09-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_email_notifications: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.wright@vdb.com
            - tool: security_api_verify_incident
              parameters: {}
            - tool: okta_api_check_access
              parameters:
                email: daniel.wright@vdb.com
                app_name: AWS Production
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.wright@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: AWS Production Access Request — SEV1 Incident Response
                  description: CTO requesting AWS Production access to coordinate recovery effort and review infrastructure status during SEV1 payment system outage affecting all customers
                  status: open
                  priority: urgent
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: okta_api_provision_access
              parameters:
                email: daniel.wright@vdb.com
                app_name: AWS Production
                access_level: user
                is_temporary: true
                access_expiry_date: '2025-10-02T13:00:00Z'
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.wright@vdb.com
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: email_notification_api_send_notification
              parameters:
                recipient_email: lisa.chen@vdb.com
                notification_type: post_facto_manager_alert
                subject: 'Post-Facto Alert: AWS Production Access Granted — SEV1 Incident'
                body: Daniel Wright (CTO, Executive Leadership) has been granted temporary AWS Production user access for SEV1 incident response — complete payment system outage affecting all customers. Access is temporary for 24 hours, expiring on 2025-10-02T13:00:00Z. This is a post-facto notification per incident response procedures.
                ticket_id: '6'
                priority: urgent
            - tool: email_notification_api_send_notification
              parameters:
                recipient_email: amanda.lee@vdb.com
                notification_type: incident_access_granted
                subject: 'Incident Access Granted: AWS Production — SEV1'
                body: 'Daniel Wright (CTO, Executive Leadership) has been granted temporary AWS Production user access for SEV1 incident response — complete payment system outage affecting all customers. Access is temporary for 24 hours, expiring on 2025-10-02T13:00:00Z. Ticket ID: 6.'
                ticket_id: '6'
                priority: urgent
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: urgent
                  subject: AWS Production Access Request — SEV1 Incident Response
                  description: CTO requesting AWS Production access to coordinate recovery effort and review infrastructure status during SEV1 payment system outage affecting all customers
                  tags: production_access,temporary_access
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  business_justification: SEV1 - All payments are down. Joining incident response to coordinate recovery effort and review infrastructure status.
                  incident_severity: sev1_critical
                  customer_impact: yes_active
                  access_expiry_date: '2025-10-02T13:00:00Z'
    """

    validate_database(x)


def test_ie_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hey, this is urgent — Ryan Cooper here, ryan.cooper@vdb.com. We're in the middle of a SEV2 incident right now — network latency spikes are causing about 15% of API calls to timeout and it's hitting customers. I need engineer_prod VPN access so I can get into the network monitoring tools to help troubleshoot. My manager Sarah Jones already approved this verbally on Slack. Can you get this set up ASAP?
    user_context: |
        You are Ryan Cooper, an Infrastructure Engineer at the company, contacting IT support during an active SEV2 incident. You urgently need VPN engineer_prod access to access network monitoring tools.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Convey urgency given the active incident but remain cooperative.
        - If asked to confirm details about the incident, confirm: network latency spikes causing ~15% of API calls to timeout across production services.
        - If asked about manager approval, confirm your manager Sarah Jones approved verbally via Slack.
        - If asked to confirm the access being provisioned or any summary, confirm and express thanks.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-417293
              email: ryan.cooper@vdb.com
              full_name: Ryan Cooper
              level: 4
              department: product_engineering
              role: Infrastructure Engineer
              office_location: sf
              start_date: '2022-11-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_security_incidents:
            - id: SEC-67284913
              employee_id: WD-218647
              severity: SEV2
              incident_type: service_degradation
              description: Network latency spikes causing 15% of API calls to timeout across production services
              status: open
              is_active: true
              reported_at: '2025-10-01T11:30:00Z'
              reported_by: monitoring_system
              resolved_at: null
              resolution_notes: null
          zendesk_users:
            - id: '6'
              name: Ryan Cooper
              email: ryan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-763-8294
              verified: true
              active: true
              created_at: '2024-09-10T00:00:00Z'
              updated_at: '2024-09-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.cooper@vdb.com
            - tool: security_api_verify_incident
              parameters: {}
            - tool: okta_api_check_access
              parameters:
                email: ryan.cooper@vdb.com
                app_name: VPN
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.cooper@vdb.com'
            - tool: workday_api_get_manager_chain
              parameters:
                email: ryan.cooper@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: SEV2 Incident - VPN engineer_prod Access Request for Network Monitoring
                  description: 'SEV2 incident: Network latency spikes causing 15% of API calls to timeout. Employee Ryan Cooper (Infrastructure Engineer, Product Engineering) requires VPN engineer_prod access to reach network monitoring tools for incident response. Manager Sarah Jones provided verbal approval via Slack.'
                  status: open
                  priority: urgent
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  tags: production_access,temporary_access
                  due_at: null
                  owner: it_support
                  incident_severity: sev2_high
                  customer_impact: yes_active
                  access_expiry_date: '2025-10-02T13:00:00Z'
                  approval_required: 'no'
                  approval_status: not_required
                  business_justification: SEV2 incident - network latency spikes causing 15% of API calls to timeout, affecting customers. Need engineer_prod VPN access to network monitoring tools for incident response.
            - tool: okta_api_provision_access
              parameters:
                email: ryan.cooper@vdb.com
                app_name: VPN
                access_level: engineer_prod
                is_temporary: true
                access_expiry_date: '2025-10-02T13:00:00Z'
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: email_notification_api_send_notification
              parameters:
                recipient_email: sarah.jones@vdb.com
                notification_type: post_facto_manager_alert
                subject: 'Post-Facto Notice: VPN engineer_prod Access Granted to Ryan Cooper During SEV2 Incident'
                body: This is a post-facto notification that Ryan Cooper (Infrastructure Engineer, Product Engineering) has been granted temporary VPN engineer_prod access for 24 hours during an active SEV2 incident involving network latency spikes causing 15% of API calls to timeout. Verbal approval via Slack was acknowledged. Access expires on 2025-10-02T13:00:00Z.
                ticket_id: '6'
                priority: urgent
            - tool: email_notification_api_send_notification
              parameters:
                recipient_email: amanda.lee@vdb.com
                notification_type: incident_access_granted
                subject: 'Incident Access Granted: VPN engineer_prod for Ryan Cooper - SEV2 Network Latency Incident'
                body: Ryan Cooper (Infrastructure Engineer, Product Engineering) has been granted temporary VPN engineer_prod access for 24 hours to respond to an active SEV2 incident involving network latency spikes causing 15% of API calls to timeout. Manager Sarah Jones provided verbal approval via Slack. Access expires on 2025-10-02T13:00:00Z.
                ticket_id: '6'
                priority: urgent
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: urgent
                  subject: SEV2 Incident - VPN engineer_prod Access Request for Network Monitoring
                  description: 'SEV2 incident: Network latency spikes causing 15% of API calls to timeout. Employee Ryan Cooper (Infrastructure Engineer, Product Engineering) requires VPN engineer_prod access to reach network monitoring tools. Manager Sarah Jones provided verbal approval via Slack. Resolution: VPN engineer_prod access provisioned with 24-hour temporary access expiring 2025-10-02T13:00:00Z. Post-facto notifications sent to manager and IT Security.'
                  tags: production_access,temporary_access
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  incident_severity: sev2_high
                  customer_impact: yes_active
                  access_expiry_date: '2025-10-02T13:00:00Z'
                  business_justification: SEV2 incident - network latency spikes causing 15% of API calls to timeout, affecting customers. Need engineer_prod VPN access to network monitoring tools for incident response.
    """

    validate_database(x)


def test_ie_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hey, this is Ryan Cooper (ryan.cooper@vdb.com) from the engineering team. We have an active SEV4 incident — one customer is seeing wrong data displayed on their account page. I need Production database access (read-only) so I can look into their account records and figure out what's going on. Can you get that set up for me?
    user_context: |
        You are Ryan Cooper, a Junior Developer in Product & Engineering, requesting Production database read-only access to investigate a SEV4 incident involving a single customer seeing incorrect data on their account page.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent denies your request, you may express mild disappointment but accept the decision. Do not argue aggressively or try to circumvent the denial.
        - If the agent offers alternative access, tools, or workarounds, politely decline them. You only need Production database (read-only) access for this request.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637284
              email: ryan.cooper@vdb.com
              full_name: Ryan Cooper
              level: 2
              department: product_engineering
              role: Junior Developer
              office_location: sf
              start_date: '2024-06-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_security_incidents:
            - id: SEC-37461825
              employee_id: WD-637284
              severity: SEV4
              incident_type: data_display_error
              description: Single customer reporting incorrect data displayed on their account page
              status: open
              is_active: true
              reported_at: '2025-10-01T11:00:00Z'
              reported_by: WD-318569
              resolved_at: null
              resolution_notes: null
          zendesk_users:
            - id: '6'
              name: Ryan Cooper
              email: ryan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-267-8394
              verified: true
              active: true
              created_at: '2024-06-01T00:00:00Z'
              updated_at: '2024-06-01T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-43718295
              employee_id: WD-637284
              app_name: Slack
              access_level: standard
              granted_at: '2024-06-01T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-52946183
              employee_id: WD-637284
              app_name: GitHub
              access_level: read_write
              granted_at: '2024-06-01T10:15:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-61385274
              employee_id: WD-637284
              app_name: Jira
              access_level: read_write
              granted_at: '2024-06-01T10:30:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-83527146
              employee_id: WD-637284
              group_name: engineers
              added_at: '2024-06-01T10:00:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.cooper@vdb.com
            - tool: security_api_verify_incident
              parameters: {}
            - tool: okta_api_check_access
              parameters:
                email: ryan.cooper@vdb.com
                app_name: Production database
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.cooper@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Production Database Access Request – SEV4 Incident
                  description: 'Employee requests Production database read_only access to investigate SEV4 incident (single customer display bug). Department: Product & Engineering, Level 2.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Production Database Access Request – SEV4 Incident
                  description: 'Employee requests Production database read_only access to investigate SEV4 incident (single customer display bug). Department: Product & Engineering, Level 2. DENIED: Production Infrastructure access for Product & Engineering is only permitted during SEV1/SEV2 incidents. Current incident is SEV4.'
                  tags: production_access
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: denied
                  incident_severity: sev4_low
                  customer_impact: yes_active
                  access_expiry_date: null
    """

    validate_database(x)


def test_pi_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I'm Rachel Nguyen (rachel.nguyen@vdb.com). How do I reset my Okta password? I want to change it to something more secure.
    user_context: |
        You are Rachel Nguyen, a Marketing Coordinator who recently joined the company. You want to know how to change your Okta password to a more secure one. This is a simple informational request — you are not locked out and your password has not expired.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-638472
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 2
              department: marketing
              role: Marketing Coordinator
              office_location: sf
              start_date: '2025-09-15T00:00:00Z'
              manager_id: WD-415783
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-415783
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 6
              department: marketing
              role: Marketing Director
              office_location: sf
              start_date: '2020-04-01T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Rachel Nguyen
              email: rachel.nguyen@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-729-8364
              verified: true
              active: true
              created_at: '2025-09-15T00:00:00Z'
              updated_at: '2025-09-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.nguyen@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Okta password change guidance request
                  description: Employee is requesting guidance on how to change their Okta password to something more secure.
                  status: open
                  priority: low
                  type: question
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: question
                  priority: low
                  subject: Okta password change guidance request
                  description: Employee is requesting guidance on how to change their Okta password to something more secure.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_pi_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there! I'm Nolan Carter, just started as a Sales Development Representative about a week and a half ago. My email is nolan.carter@vdb.com. I had a few questions I was hoping you could help with:

        1) How do I request a headset for calls?
        2) What's the process to get Salesforce access?
        3) Who do I contact about my benefits enrollment?

        Thanks in advance!
    user_context: |
        You are Nolan Carter, a newly hired Sales Development Representative who started on September 20, 2025. You are reaching out to IT support with three informational questions about getting a headset, Salesforce access, and benefits enrollment. You are not making actionable requests — you are simply asking for guidance on how to go about these things.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-641873
              email: nolan.carter@vdb.com
              full_name: Nolan Carter
              level: 2
              department: sales
              role: Sales Development Representative
              office_location: sf
              start_date: '2025-09-20T00:00:00Z'
              manager_id: WD-415276
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-415276
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 6
              department: sales
              role: Sales Manager
              office_location: sf
              start_date: '2020-04-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nolan Carter
              email: nolan.carter@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-739-4821
              verified: true
              active: true
              created_at: '2025-09-20T00:00:00Z'
              updated_at: '2025-09-20T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nolan.carter@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nolan.carter@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: 'Multiple informational requests: headset, Salesforce access, benefits enrollment'
                  description: 'New Sales SDR has three questions: 1) How to request a headset for calls, 2) Process to get Salesforce access, 3) Who to contact about benefits enrollment.'
                  status: open
                  priority: low
                  type: question
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  priority: low
                  type: question
                  tags: redirected
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_pi_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I want to build a dashboard for our monthly metrics. How do I create one in Tableau? My name is Rachel Nguyen and my email is rachel.nguyen@vdb.com.
    user_context: |
        You are Rachel Nguyen, a Business Analyst in the finance/accounting department, contacting IT support to learn how to create a Tableau dashboard for monthly metrics. You do NOT currently have Tableau access (you may not be aware of this). Your request is purely informational — you want to know how to create a dashboard.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent informs you that you don't have Tableau access and offers to initiate an access request, thank them for the information but do not explicitly request access provisioning at this time. Simply acknowledge the information provided.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-416738
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 3
              department: finance_accounting
              role: Business Analyst
              office_location: sf
              start_date: '2023-04-01T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Rachel Nguyen
              email: rachel.nguyen@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-267-8394
              verified: true
              active: true
              created_at: '2024-04-10T00:00:00Z'
              updated_at: '2024-04-10T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: rachel.nguyen@vdb.com
                app_name: Tableau
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.nguyen@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: How to create a Tableau dashboard
                  description: Employee asks how to create a Tableau dashboard for monthly metrics. Employee does not currently have Tableau access.
                  status: open
                  priority: low
                  type: question
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: question
                  priority: low
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_pi_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Ryan Parker from the Sales team (ryan.parker@vdb.com). How do I export my pipeline data from Salesforce to Excel? I need it for a quarterly review presentation.
    user_context: |
        You are Ryan Parker, a Sales Manager at the company. You want to know how to export your pipeline data from Salesforce into an Excel file for an upcoming quarterly review presentation. You already have Salesforce access and can log in fine — you just need guidance on the export process.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent provides export instructions, acknowledge them and thank the agent.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-648217
              email: ryan.parker@vdb.com
              full_name: Ryan Parker
              level: 5
              department: sales
              role: Sales Manager
              office_location: sf
              start_date: '2020-05-01T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Ryan Parker
              email: ryan.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-8294
              verified: true
              active: true
              created_at: '2024-05-10T00:00:00Z'
              updated_at: '2024-05-10T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-73621948
              employee_id: WD-648217
              app_name: Salesforce
              access_level: user
              granted_at: '2020-06-01T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-62841573
              employee_id: WD-648217
              group_name: sales_team
              added_at: '2020-05-15T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.parker@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: How to export Salesforce pipeline data to Excel
                  description: Employee is requesting guidance on how to export pipeline data from Salesforce to Excel for a quarterly review presentation.
                  status: open
                  priority: low
                  type: question
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: question
                  priority: low
                  subject: How to export Salesforce pipeline data to Excel
                  description: Employee is requesting guidance on how to export pipeline data from Salesforce to Excel for a quarterly review presentation.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_pi_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I want to sign up for the company 401k. Where do I do that? My name is Nathan Parker and my email is nathan.parker@vdb.com.
    user_context: |
        You are Nathan Parker, a Software Engineer, contacting IT support because you want to enroll in the company's 401k retirement plan. You don't know which team handles 401k enrollment.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637284
              email: nathan.parker@vdb.com
              full_name: Nathan Parker
              level: 3
              department: product_engineering
              role: Software Engineer
              office_location: sf
              start_date: '2023-05-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '14'
              name: Nathan Parker
              email: nathan.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-726-8934
              verified: true
              active: true
              created_at: '2024-05-01T00:00:00Z'
              updated_at: '2024-05-01T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-43718295
              employee_id: WD-637284
              app_name: Slack
              access_level: read_write
              granted_at: '2023-05-01T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-65294817
              employee_id: WD-637284
              app_name: GitHub
              access_level: read_write
              granted_at: '2023-05-01T10:15:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-87361524
              employee_id: WD-637284
              app_name: Jira
              access_level: read_write
              granted_at: '2023-05-01T10:30:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-82541396
              employee_id: WD-637284
              group_name: engineers
              added_at: '2023-05-01T09:00:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-63728
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: '2023-04-25T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-63728194
              asset_id: VDB-HW-63728
              employee_id: WD-637284
              assigned_at: '2023-05-01T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_approval_requests: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.parker@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: 401k Enrollment Inquiry
                  description: Employee is asking how to sign up for the company 401k plan. Redirecting to Benefits team.
                  type: question
                  priority: low
                  status: open
                  requester_id: '14'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: question
                  priority: low
                  subject: 401k Enrollment Inquiry
                  description: Employee is asking how to sign up for the company 401k plan. Redirecting to Benefits team.
                  tags: redirected
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_pi_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, my name is Daniel Park (daniel.park@vdb.com). I was promoted to Senior Engineer about 2 weeks ago. I was previously an Engineer at level 4, and now I'm at level 5. Are there any changes in access procedures to systems and data that I should be aware of with my new role?
    user_context: |
        You are Daniel Park, a recently promoted employee at the company. You were promoted from Engineer (Level 4) to your current role (Level 5) about two weeks ago. You are reaching out to IT support to understand if there are any changes in how access approvals work for your new level/role. You are simply seeking information — you are NOT requesting access to any specific tool or system.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Once the agent provides the information about access procedure changes, thank them and confirm you have no further questions.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637291
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 5
              department: product_engineering
              role: Senior Engineer
              office_location: sf
              start_date: '2020-09-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '10'
              name: Daniel Park
              email: daniel.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-729-4183
              verified: true
              active: true
              created_at: '2024-02-15T00:00:00Z'
              updated_at: '2024-02-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-43719265
              employee_id: WD-637291
              app_name: Slack
              access_level: read_write
              granted_at: '2020-09-01T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-51863927
              employee_id: WD-637291
              app_name: Jira
              access_level: read_write
              granted_at: '2020-09-01T09:05:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-67284931
              employee_id: WD-637291
              app_name: GitHub
              access_level: read_write
              granted_at: '2020-09-15T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-42918573
              employee_id: WD-637291
              group_name: engineers
              added_at: '2020-09-01T09:10:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.park@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.park@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Inquiry about access procedure changes after promotion
                  description: Employee was promoted from Engineer (Level 4) to Senior Engineer (Level 5) approximately two weeks ago. Requesting information about any changes in access approval procedures for systems and data associated with the new role.
                  status: open
                  priority: low
                  type: question
                  requester_id: '10'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: question
                  priority: low
                  subject: Inquiry about access procedure changes after promotion
                  description: Employee was promoted from Engineer (Level 4) to Senior Engineer (Level 5) approximately two weeks ago. Requesting information about any changes in access approval procedures for systems and data associated with the new role.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_pi_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I got a message saying I need to enroll in MFA. How do I set up the authenticator app on my phone? My name is Nathan Parker and my email is nathan.parker@vdb.com.
    user_context: |
        You are Nathan Parker, a newly hired Data Analyst in the finance_accounting department. You just started on September 25th and received a notification that you need to enroll in MFA. You want help setting up the authenticator app on your phone. You have no prior experience with MFA setup at this company.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-628471
              email: nathan.parker@vdb.com
              full_name: Nathan Parker
              level: 3
              department: finance_accounting
              role: Data Analyst
              office_location: sf
              start_date: '2025-09-25T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Parker
              email: nathan.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-267-8943
              verified: true
              active: true
              created_at: '2025-09-25T00:00:00Z'
              updated_at: '2025-09-25T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.parker@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: MFA Enrollment Guidance Request
                  description: New employee requesting guidance on how to enroll in MFA and set up authenticator app on phone
                  status: open
                  priority: low
                  type: question
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: question
                  priority: low
                  subject: MFA Enrollment Guidance Request
                  description: New employee requesting guidance on how to enroll in MFA and set up authenticator app on phone
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_pi_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Nathan Brooks from Customer Support (nathan.brooks@vdb.com). I'm starting to work from home next week. How do I set up VPN to access company systems?
    user_context: |
        You are Nathan Brooks, a Customer Support Agent who works remotely and needs guidance on setting up VPN for accessing company systems from home. You are asking a purely informational question — you just want to know the steps to get VPN working.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637281
              email: nathan.brooks@vdb.com
              full_name: Nathan Brooks
              level: 2
              department: customer_support
              role: Customer Support Agent
              office_location: remote
              start_date: '2024-02-01T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: 1823 Oak Ridge Dr, Nashville, TN 37215
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Brooks
              email: nathan.brooks@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-615-472-8193
              verified: true
              active: true
              created_at: '2024-02-01T00:00:00Z'
              updated_at: '2024-02-01T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-43617289
              employee_id: WD-637281
              app_name: VPN
              access_level: standard_employee
              granted_at: '2024-02-01T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.brooks@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.brooks@vdb.com'
            - tool: okta_api_check_access
              parameters:
                email: nathan.brooks@vdb.com
                app_name: VPN
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: VPN Setup Information Request
                  description: Employee inquired about how to set up VPN for remote work access to company systems. Employee already has VPN standard_employee access. Provided self-service installation instructions via Okta App Catalog.
                  status: open
                  priority: low
                  type: question
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: question
                  priority: low
                  subject: VPN Setup Information Request
                  description: Employee inquired about how to set up VPN for remote work access to company systems. Employee already has VPN standard_employee access. Provided self-service installation instructions via Okta App Catalog.
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_pi_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Nathan Parker, Product Designer here at VDB. My email is nathan.parker@vdb.com. Is Figma an approved software? I want to make sure before using it for my design work.
    user_context: |
        You are Nathan Parker, a Product Designer at VDB, asking IT support whether Figma is on the company's approved software list. You just want a simple informational answer.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-617384
              email: nathan.parker@vdb.com
              full_name: Nathan Parker
              level: 3
              department: product_engineering
              role: Product Designer
              office_location: sf
              start_date: '2023-09-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Parker
              email: nathan.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-267-8394
              verified: true
              active: true
              created_at: '2024-09-01T00:00:00Z'
              updated_at: '2024-09-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles:
            - id: 1
              url: https://vdb.zendesk.com/api/v2/help_center/articles/1.json
              html_url: https://vdb.zendesk.com/hc/en-us/articles/1
              title: Approved Software List
              body: <p>The following software applications are approved for use at VDB:</p><ul><li>Slack</li><li>Jira</li><li>Confluence</li><li>Figma</li><li>GitHub</li><li>Zoom</li><li>Tableau</li><li>Salesforce</li><li>Workday</li><li>Snowflake</li><li>Splunk</li><li>Okta</li></ul><p>If you need access to or a license for any of these applications, please submit a request to IT Support.</p>
              snippet: 'The following software applications are approved for use at VDB: Slack, Jira, Confluence, Figma, GitHub, Zoom, Tableau, Salesforce, Workday, Snowflake, Splunk, Okta.'
              author_id: 1
              section_id: 1
              category_id: null
              brand_id: null
              locale: en-us
              source_locale: en-us
              draft: false
              promoted: false
              position: 0
              vote_sum: 5
              vote_count: 5
              comments_disabled: false
              outdated: false
              outdated_locales: []
              label_names:
                - approved-software
                - software-list
              content_tag_ids: []
              user_segment_id: null
              permission_group_id: null
              created_at: '2024-01-15T10:00:00Z'
              updated_at: '2024-06-01T10:00:00Z'
              edited_at: '2024-06-01T10:00:00Z'
              result_type: article
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41738295
              employee_id: WD-617384
              app_name: Slack
              access_level: read_write
              granted_at: '2023-09-01T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-52864713
              employee_id: WD-617384
              app_name: Jira
              access_level: read_write
              granted_at: '2023-09-01T10:05:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-83517294
              employee_id: WD-617384
              group_name: engineers
              added_at: '2023-09-01T10:10:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.parker@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Inquiry about Figma approved software status
                  description: Employee asks whether Figma is on the approved software list for design work.
                  status: open
                  priority: low
                  type: question
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  priority: low
                  type: question
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_pi_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, my name is Daniel Park and my email is daniel.park@vdb.com. As a contractor, what systems am I allowed to request access to? Are there any restrictions I should know about?
    user_context: |
        You are Daniel Park, a contract Business Analyst in the Finance & Accounting department. You are asking a general informational question about what systems you can and cannot access as a contractor, and any restrictions that apply. You are not requesting access to any specific system right now — you just want to understand the rules.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415738
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 3
              department: finance_accounting
              role: Business Analyst
              office_location: sf
              start_date: '2025-06-01T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: true
              remote_delivery_address: null
              contract_end_date: '2026-05-31T00:00:00Z'
          zendesk_users:
            - id: '6'
              name: Daniel Park
              email: daniel.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-2948
              verified: true
              active: true
              created_at: '2025-06-01T00:00:00Z'
              updated_at: '2025-06-01T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41573892
              employee_id: WD-415738
              app_name: Slack
              access_level: member
              granted_at: '2025-06-01T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: true
              expires_at: '2026-05-31T00:00:00Z'
            - id: OAA-41573893
              employee_id: WD-415738
              app_name: Confluence
              access_level: user
              granted_at: '2025-06-01T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: true
              expires_at: '2026-05-31T00:00:00Z'
            - id: OAA-41573894
              employee_id: WD-415738
              app_name: Jira
              access_level: user
              granted_at: '2025-06-01T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: true
              expires_at: '2026-05-31T00:00:00Z'
            - id: OAA-41573895
              employee_id: WD-415738
              app_name: Snowflake
              access_level: analyst
              granted_at: '2025-06-01T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: true
              expires_at: '2026-05-31T00:00:00Z'
            - id: OAA-41573896
              employee_id: WD-415738
              app_name: VPN
              access_level: standard_employee
              granted_at: '2025-06-01T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: true
              expires_at: '2026-05-31T00:00:00Z'
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41573891
              employee_id: WD-415738
              group_name: finance_team
              added_at: '2025-06-01T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.park@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.park@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Contractor Access Limitations Inquiry
                  description: Contractor in Finance & Accounting department asking about systems they can access and any restrictions that apply to contractors.
                  status: open
                  priority: low
                  type: question
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: question
                  priority: low
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_sa_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Rachel Cooper from the Customer Support team (rachel.cooper@vdb.com). I currently have read-only access to the Admin Panel, but I need write access to correct customer address information. Could you help me get that set up?
    user_context: |
        You are Rachel Cooper, a Customer Support Agent at the company. You are requesting write access to the Admin Panel because you need to correct customer address information. Your email is rachel.cooper@vdb.com.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent mentions that customer address data is PII, or that write access is limited to non-PII fields, or that PII write access cannot be granted, or denies the request, or suggests escalating to another team: acknowledge that you understand the PII limitation and clarify that you would still like to proceed specifically with requesting Admin Panel (write non-PII only) access. Restate your business justification that you need write access to correct customer address information.
        - If the agent pushes back more than once about PII or asks for a non-PII justification or repeats the same concern, explicitly tell the agent: "I understand the PII limitation, but please go ahead and submit my Admin Panel (write non-PII only) access request for Director and IT Security approval with the justification I have provided. The approvers can evaluate whether or not to grant it."
        - If asked to confirm your business justification, restate that you need write access to correct customer address information.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-482917
              email: rachel.cooper@vdb.com
              full_name: Rachel Cooper
              level: 2
              department: customer_support
              role: Customer Support Agent
              office_location: austin
              start_date: '2023-06-01T00:00:00Z'
              manager_id: WD-614827
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-614827
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 5
              department: customer_support
              role: Customer Support Team Lead
              office_location: austin
              start_date: '2021-03-15T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-42917638
              employee_id: WD-482917
              app_name: Admin Panel
              access_level: read_only
              granted_at: '2023-07-15T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          zendesk_users:
            - id: '6'
              name: Rachel Cooper
              email: rachel.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-738-4291
              verified: true
              active: true
              created_at: '2024-06-01T00:00:00Z'
              updated_at: '2024-06-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.cooper@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: rachel.cooper@vdb.com
                app_name: Admin Panel
            - tool: workday_api_get_manager_chain
              parameters:
                email: rachel.cooper@vdb.com
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: maria.garcia@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: amanda.lee@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.cooper@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Admin Panel write access request
                  description: 'Employee requests Admin Panel (write non-PII only) access. Business justification: need write access to correct customer address information.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: rachel.cooper@vdb.com
                approver_email: maria.garcia@vdb.com
                details: 'Request for Admin Panel (write non-PII only) access for Customer Support Agent. Business justification: need write access to correct customer address information.'
                urgency: standard
                ticket_id: '6'
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: rachel.cooper@vdb.com
                approver_email: amanda.lee@vdb.com
                details: 'Request for Admin Panel (write non-PII only) access for Customer Support Agent. Business justification: need write access to correct customer address information.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Admin Panel write access request
                  description: 'Employee requests Admin Panel (write non-PII only) access. Business justification: need write access to correct customer address information.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: I need write access to correct customer address information
                  approver_id: WD-739154,WD-753918
                  approval_request_ids: APR-00000007,APR-00000008
    """

    validate_database(x)


def test_sa_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hey, I'm Ryan Cooper (ryan.cooper@vdb.com) from the Product Engineering team. I currently have read-only access to our GitHub repository and I need to get that upgraded to write access. I need to contribute code to the payments module for Q1 sprint. Can you help me get that set up?
    user_context: |
        You are Ryan Cooper, a Software Engineer in the Product Engineering department, requesting an upgrade from read-only to write access on GitHub. Your email is ryan.cooper@vdb.com. Your business justification is that you need to contribute code to the payments module for Q1 sprint.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - This is a permanent, ongoing access need for your development role, not a temporary project-based request. If the agent asks about the duration of access or an end date, clarify that you need permanent write access as contributing code is a core part of your ongoing responsibilities.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-638274
              email: ryan.cooper@vdb.com
              full_name: Ryan Cooper
              level: 3
              department: product_engineering
              role: Software Engineer
              office_location: sf
              start_date: '2024-01-15T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41738295
              employee_id: WD-638274
              app_name: GitHub
              access_level: read_only
              granted_at: '2024-03-18T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          zendesk_users:
            - id: '6'
              name: Ryan Cooper
              email: ryan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-8294
              verified: true
              active: true
              created_at: '2024-02-01T00:00:00Z'
              updated_at: '2024-02-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-62841397
              employee_id: WD-638274
              group_name: engineers
              added_at: '2024-01-20T09:00:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.cooper@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: ryan.cooper@vdb.com
                app_name: GitHub
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.cooper@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: GitHub write access request
                  description: 'Request for GitHub write access for Ryan Cooper (Product Engineering). Business justification: Need to contribute code to the payments module for Q1 sprint.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: ryan.cooper@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: sarah.jones@vdb.com
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: amanda.lee@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: ryan.cooper@vdb.com
                approver_email: sarah.jones@vdb.com
                details: 'Request for GitHub write access for Ryan Cooper (Product Engineering, Level 3). Business justification: Need to contribute code to the payments module for Q1 sprint. Current access: read_only. Requested access: write.'
                urgency: standard
                ticket_id: '6'
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: ryan.cooper@vdb.com
                approver_email: amanda.lee@vdb.com
                details: 'Request for GitHub write access for Ryan Cooper (Product Engineering, Level 3). Business justification: Need to contribute code to the payments module for Q1 sprint. Current access: read_only. Requested access: write. IT Security approval required per Sensitivity Group 3 policy.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: GitHub write access request
                  description: 'Request for GitHub write access for Ryan Cooper (Product Engineering). Business justification: Need to contribute code to the payments module for Q1 sprint.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: null
                  approver_id: WD-681453,WD-753918
                  approval_request_ids: APR-00000007,APR-00000008
    """

    validate_database(x)


def test_sa_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need help upgrading my Admin Panel access
    user_context: |
        You are Daniel Wright, a Customer Support Lead at VDB who was recently promoted. You are contacting support to request that your Admin Panel access be upgraded from read-only to write access, as your new Lead role should come with higher permissions.

        Only if you are asked about your name or identity — tell the agent you are Daniel Wright.
        Only if you are asked about your email address — tell the agent it is daniel.wright@vdb.com.
        Only if you are asked about your team or department — tell the agent you are from the Customer Support team.
        Only if you are asked about why you need the upgrade or about recent changes — tell the agent you were recently promoted to Lead and believe you should now have write access.
        Only if you are asked about your current access level — tell the agent you currently have read-only access to the Admin Panel.
        Only if you are asked about what specific access you need — tell the agent you need write access to the Admin Panel.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415397
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 4
              department: customer_support
              role: Customer Support Lead
              office_location: sf
              start_date: '2022-03-15T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Wright
              email: daniel.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-738-4291
              verified: true
              active: true
              created_at: '2024-04-10T00:00:00Z'
              updated_at: '2024-04-10T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41539712
              employee_id: WD-415397
              app_name: Admin Panel
              access_level: read_only
              granted_at: '2024-05-20T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41539783
              employee_id: WD-415397
              group_name: support_team
              added_at: '2022-03-20T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.wright@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.wright@vdb.com'
            - tool: okta_api_check_access
              parameters:
                email: daniel.wright@vdb.com
                app_name: Admin Panel
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Admin Panel Write Access Request
                  description: Customer Support Lead Daniel Wright was recently promoted to Lead and requests upgrade from read-only to write (non-PII only) access on Admin Panel, consistent with Tier 2 default access.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
            - tool: okta_api_revoke_access
              parameters:
                email: daniel.wright@vdb.com
                app_name: Admin Panel
            - tool: okta_api_provision_access
              parameters:
                email: daniel.wright@vdb.com
                app_name: Admin Panel
                access_level: write non-PII only
                is_temporary: false
                access_expiry_date: null
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Admin Panel Write Access Request
                  description: Customer Support Lead Daniel Wright was recently promoted to Lead and requests upgrade from read-only to write (non-PII only) access on Admin Panel, consistent with Tier 2 default access.
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  access_expiry_date: null
    """

    validate_database(x)


def test_sa_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need help getting access to Snowflake depersonalized.
    user_context: |
        You are Nathan Wright, a Financial Analyst in the Finance & Accounting department, contacting IT support to request access to Snowflake depersonalized for your monthly reconciliation work. You joined the Finance team in September 2023 and have never had this access.

        Only if you are asked about your name or to identify yourself — tell the agent you are Nathan Wright.
        Only if you are asked about your email address — tell the agent it is nathan.wright@vdb.com.
        Only if you are asked about your team or department — tell the agent you are from the Finance team.
        Only if you are asked when you joined or how long you've been with the team — tell the agent you joined the Finance team about 15 months ago (September 2023).
        Only if you are asked why you need this access or what you'll use it for — tell the agent you need it for your monthly reconciliation reports.
        Only if you are asked whether you've had this access before — tell the agent you still don't have access and have never had it.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-413879
              email: nathan.wright@vdb.com
              full_name: Nathan Wright
              level: 3
              department: finance_accounting
              role: Financial Analyst
              office_location: sf
              start_date: '2023-09-01T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Wright
              email: nathan.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-2841
              verified: true
              active: true
              created_at: '2024-09-01T00:00:00Z'
              updated_at: '2024-09-01T00:00:00Z'
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41387926
              employee_id: WD-413879
              group_name: finance_team
              added_at: '2023-09-01T09:00:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.wright@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: nathan.wright@vdb.com
                app_name: Snowflake depersonalized
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.wright@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Snowflake Depersonalized Access Request - Finance
                  description: Employee in Finance & Accounting department requests access to Snowflake depersonalized (analyst level) for monthly reconciliation reports. Employee joined Finance team 15 months ago but has not yet received default department access to Snowflake.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
            - tool: okta_api_provision_access
              parameters:
                email: nathan.wright@vdb.com
                app_name: Snowflake depersonalized
                access_level: analyst
                is_temporary: false
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Snowflake Depersonalized Access Request - Finance
                  description: Employee in Finance & Accounting department requests access to Snowflake depersonalized (analyst level) for monthly reconciliation reports. Employee joined Finance team 15 months ago but has not yet received default department access to Snowflake. Access has been provisioned with analyst-level access.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
    """

    validate_database(x)


def test_sa_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Rachel Nguyen (rachel.nguyen@vdb.com) from the marketing team. I'd like to request read-only access to the Snowflake data warehouse, specifically the analytics_mart database. I need to analyze customer acquisition data for the new campaign we're launching. Could you help me get this set up?
    user_context: |
        You are Rachel Nguyen, a Marketing Specialist, requesting read-only access to the Snowflake analytics_mart database to analyze customer acquisition data for a new campaign.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked about access duration or end date, explain that while the immediate need is for the current campaign, you will be running campaigns continuously as part of your regular duties and need permanent ongoing access. Do not provide a specific end date.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-638471
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 3
              department: marketing
              role: Marketing Specialist
              office_location: sf
              start_date: '2023-02-20T00:00:00Z'
              manager_id: WD-417283
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-417283
              email: daniel.parker@vdb.com
              full_name: Daniel Parker
              level: 5
              department: marketing
              role: Marketing Manager
              office_location: sf
              start_date: '2020-08-10T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Rachel Nguyen
              email: rachel.nguyen@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-736-2891
              verified: true
              active: true
              created_at: '2024-04-10T00:00:00Z'
              updated_at: '2024-04-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: rachel.nguyen@vdb.com
                app_name: Snowflake depersonalized
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.nguyen@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Snowflake Depersonalized Access Request - Rachel Nguyen
                  description: 'Employee Rachel Nguyen (Marketing Specialist, marketing_growth) requests read-only access to Snowflake data warehouse analytics_mart database. Business justification: Need to analyze customer acquisition data for the new campaign.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  tags: null
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: daniel.parker@vdb.com
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: amanda.lee@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: rachel.nguyen@vdb.com
                approver_email: daniel.parker@vdb.com
                details: 'Request for Snowflake depersonalized analyst access for Rachel Nguyen (Marketing Specialist). Business justification: Need to analyze customer acquisition data for the new campaign.'
                urgency: standard
                ticket_id: '6'
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: rachel.nguyen@vdb.com
                approver_email: amanda.lee@vdb.com
                details: 'Request for Snowflake depersonalized analyst access for Rachel Nguyen (Marketing Specialist). Requires IT Security approval per sensitivity group 3 policy. Business justification: Need to analyze customer acquisition data for the new campaign.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Snowflake Depersonalized Access Request - Rachel Nguyen
                  description: 'Employee Rachel Nguyen (Marketing Specialist, marketing_growth) requests read-only access to Snowflake data warehouse analytics_mart database. Business justification: Need to analyze customer acquisition data for the new campaign.'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: null
                  approver_id: WD-417283,WD-753918
                  approval_request_ids: APR-00000007,APR-00000008
                  access_expiry_date: null
    """

    validate_database(x)


def test_sa_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need access to Splunk SIEM.
    user_context: |
        You are Daniel Park, an IT Operations Specialist at vdb.com, requesting access to Splunk SIEM. You do not currently have access to Splunk SIEM.

        Only if you are asked about your name or to identify yourself — tell the agent your name is Daniel Park.
        Only if you are asked about your department or role — tell the agent you are from IT Operations (or that you are an IT Operations Specialist).
        Only if you are asked about your email address — tell the agent it is daniel.park@vdb.com.
        Only if you are asked about why you need access or what you need it for — tell the agent you need it for log analysis to investigate some infrastructure anomalies in your monitoring alerts.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked about the duration of access, state that you need ongoing/permanent access for your regular IT Operations duties, not just for this specific investigation.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637284
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 3
              department: it_operations
              role: IT Operations Specialist
              office_location: sf
              start_date: '2023-05-15T00:00:00Z'
              manager_id: WD-418573
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-418573
              email: nathan.brooks@vdb.com
              full_name: Nathan Brooks
              level: 5
              department: it_operations
              role: IT Operations Manager
              office_location: sf
              start_date: '2020-08-10T00:00:00Z'
              manager_id: WD-851479
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-851479
              email: rachel.turner@vdb.com
              full_name: Rachel Turner
              level: 7
              department: it_operations
              role: VP of IT Operations
              office_location: sf
              start_date: '2019-04-01T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Park
              email: daniel.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-2841
              verified: true
              active: true
              created_at: '2024-05-20T00:00:00Z'
              updated_at: '2024-05-20T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.park@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: daniel.park@vdb.com
                app_name: Splunk SIEM
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.park@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Splunk SIEM Access Request - IT Operations
                  description: IT Operations Specialist requesting Splunk SIEM user access for log analysis to investigate infrastructure anomalies in monitoring alerts.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.park@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: rachel.turner@vdb.com
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: amanda.lee@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.park@vdb.com
                approver_email: rachel.turner@vdb.com
                details: 'Requesting Splunk SIEM user access for IT Operations Specialist Daniel Park. Business justification: Need to investigate infrastructure anomalies in monitoring alerts.'
                urgency: standard
                ticket_id: '6'
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.park@vdb.com
                approver_email: amanda.lee@vdb.com
                details: 'Requesting Splunk SIEM user access for IT Operations Specialist Daniel Park. Requires IT Security approval per Group 5 sensitivity. Business justification: Need to investigate infrastructure anomalies in monitoring alerts.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Splunk SIEM Access Request - IT Operations
                  description: IT Operations Specialist requesting Splunk SIEM user access for log analysis to investigate infrastructure anomalies in monitoring alerts.
                  tags: production_access
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: I need to investigate some infrastructure anomalies in our monitoring alerts.
                  approver_id: WD-851479,WD-753918
                  approval_request_ids: APR-00000007,APR-00000008
                  access_expiry_date: null
    """

    validate_database(x)


def test_sa_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need help getting access to some dashboards.
    user_context: |
        You are Rachel Nguyen, a Marketing Manager requesting access to Marketing department BI dashboards in Tableau so you can view campaign performance data.

        Only if you are asked about your name or identity — tell the agent you are Rachel Nguyen.
        Only if you are asked about your email address — tell the agent it is rachel.nguyen@vdb.com.
        Only if you are asked about your department or team — tell the agent you are from the Marketing team.
        Only if you are asked about what tool or platform — tell the agent it is Tableau.
        Only if you are asked about what you need access to specifically — tell the agent you need access to the Marketing BI dashboards.
        Only if you are asked about why you need access or what you want to view — tell the agent you want to view campaign performance dashboards.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637482
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 5
              department: marketing
              role: Marketing Manager
              office_location: sf
              start_date: '2021-03-01T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-82463719
              employee_id: WD-637482
              group_name: marketing_team
              added_at: '2021-03-15T10:00:00Z'
              added_by: system
              is_active: true
          zendesk_users:
            - id: '6'
              name: Rachel Nguyen
              email: rachel.nguyen@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-729-3841
              verified: true
              active: true
              created_at: '2024-04-10T00:00:00Z'
              updated_at: '2024-04-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: okta_api_get_user_groups
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.nguyen@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: BI Dashboard Access Request - Marketing Dashboards
                  description: Marketing Manager requests access to Marketing department BI dashboards (bi_marketing_viewers) to view campaign performance data.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: okta_api_add_to_group
              parameters:
                email: rachel.nguyen@vdb.com
                group_name: bi_marketing_viewers
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  type: problem
                  priority: normal
                  status: solved
                  subject: BI Dashboard Access Request - Marketing Dashboards
                  description: Marketing Manager requests access to Marketing department BI dashboards (bi_marketing_viewers) to view campaign performance data.
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  access_expiry_date: null
    """

    validate_database(x)


def test_sa_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, two things - I need Marketing BI dashboard access for my team activities planning, and also my laptop is really sluggish and needs replacement. My name is Daniel Wright, email daniel.wright@vdb.com.
    user_context: |
        You are Daniel Wright, a Sales Manager at VDB, contacting IT support with two requests: (1) access to the Marketing BI dashboard for team activities planning, and (2) a laptop replacement because your current laptop is sluggish.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm details or approve next steps, confirm and agree.
        - Your business justification for the laptop replacement is that it's sluggish and affecting your productivity.
        - Your reason for needing Marketing BI dashboard access is for team activities planning.
        - You only need the Marketing BI dashboard access for yourself, not for your team members. If asked whether others on your team need access too, clarify that it is just for you.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-748392
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 5
              department: sales
              role: Sales Manager
              office_location: sf
              start_date: '2021-06-01T00:00:00Z'
              manager_id: WD-635184
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-635184
              email: rachel.cooper@vdb.com
              full_name: Rachel Cooper
              level: 7
              department: sales
              role: VP of Sales
              office_location: sf
              start_date: '2019-09-01T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '15'
              name: Daniel Wright
              email: daniel.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-8294
              verified: true
              active: true
              created_at: '2024-06-01T00:00:00Z'
              updated_at: '2024-06-01T00:00:00Z'
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-82461537
              employee_id: WD-748392
              group_name: sales_team
              added_at: '2021-06-15T09:00:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-36291
              device_type: laptop_standard
              device_model: Dell Latitude 5440
              purchase_date: '2023-04-01T00:00:00Z'
              warehouse_location: sf
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62719384
              asset_id: VDB-HW-36291
              employee_id: WD-748392
              assigned_at: '2023-06-20T10:00:00Z'
              assigned_by: system
              is_active: true
              returned_at: null
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.wright@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.wright@vdb.com'
            - tool: okta_api_get_user_groups
              parameters:
                email: daniel.wright@vdb.com
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: daniel.wright@vdb.com
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.wright@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: rachel.cooper@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Marketing BI Dashboard Access Request
                  description: Employee Daniel Wright (Sales Manager, Sales/BD) requests access to Marketing BI dashboards for team activities planning.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '15'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Laptop Replacement Request - Refresh
                  description: 'Employee Daniel Wright reports laptop is sluggish and requests replacement. Current device: Dell Latitude 5440 (VDB-HW-36291), 30 months old. Related to Ticket 6 (Marketing BI Dashboard Access Request).'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '15'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.wright@vdb.com
                approver_email: rachel.cooper@vdb.com
                details: 'Request for Marketing BI dashboard access (bi_marketing_viewers group) for team activities planning. Employee: Daniel Wright, Sales Manager.'
                urgency: standard
                ticket_id: '6'
            - tool: approval_api_create_request
              parameters:
                request_type: hardware_purchase
                requester_email: daniel.wright@vdb.com
                approver_email: rachel.cooper@vdb.com
                details: 'Laptop replacement request - refresh. Current device: Dell Latitude 5440 (VDB-HW-36291), age 30 months. Business justification: Laptop is sluggish and affecting productivity.'
                urgency: standard
                ticket_id: '7'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Marketing BI Dashboard Access Request
                  description: Employee Daniel Wright (Sales Manager, Sales/BD) requests access to Marketing BI dashboards for team activities planning. Related to Ticket 7 (Laptop Replacement Request).
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-635184
                  approval_request_ids: APR-00000007
                  access_expiry_date: null
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '7'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Laptop Replacement Request - Refresh
                  description: 'Employee Daniel Wright reports laptop is sluggish and requests replacement. Current device: Dell Latitude 5440 (VDB-HW-36291), 30 months old. Related to Ticket 6 (Marketing BI Dashboard Access Request).'
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: Laptop is really sluggish and needs replacement - performance issues affecting productivity
                  approver_id: WD-635184
                  approval_request_ids: APR-00000008
                  asset_id: VDB-HW-36291
    """

    validate_database(x)


def test_sa_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Daniel Wright (daniel.wright@vdb.com). I had a ticket TCK-00044987 for GitHub write access that was resolved about 4 days ago. The access you granted stopped working yesterday — I'm getting permission denied errors again when trying to push code. Can you help me get this sorted out?
    user_context: |
        You are Daniel Wright, a QA Engineer in Product Engineering, contacting IT support because your GitHub write access that was provisioned 4 days ago (via ticket TCK-00044987) has stopped working. You are getting permission denied errors.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent explains that this needs to be processed as a new access request requiring fresh approvals (rather than simply reopening the old ticket), accept that and confirm you'd like to proceed.
        - You do not know why the access was revoked — you just noticed it stopped working yesterday.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637482
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 3
              department: product_engineering
              role: QA Engineer
              office_location: sf
              start_date: '2023-03-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Wright
              email: daniel.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-731-8294
              verified: true
              active: true
              created_at: '2024-09-15T00:00:00Z'
              updated_at: '2024-09-15T00:00:00Z'
          zendesk_tickets:
            - id: TCK-00044987
              subject: GitHub Write Access Request
              description: Request for GitHub write access for QA Engineer role in Product Engineering
              status: solved
              priority: normal
              type: problem
              requester_id: '6'
              assignee_id: '2'
              organization_id: '1'
              tags:
                - github
                - access
              created_at: '2025-09-25T10:00:00Z'
              updated_at: '2025-09-27T13:00:00Z'
              due_at: null
              resolution_category: provisioned
              owner: it_support
              access_expiry_date: null
              approval_required: 'yes'
              approval_status: approved
              approver_id: null
              approval_request_ids: null
              business_justification: null
              incident_severity: null
              customer_impact: null
              asset_id: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41637298
              employee_id: WD-637482
              app_name: GitHub
              access_level: write
              granted_at: '2025-09-27T13:00:00Z'
              granted_by: system
              is_active: false
              revoked_at: '2025-09-30T09:15:00Z'
              is_temporary: false
              expires_at: null
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.wright@vdb.com
            - tool: zendesk_get_item
              parameters:
                table: tickets
                id: TCK-00044987
            - tool: okta_api_check_access
              parameters:
                email: daniel.wright@vdb.com
                app_name: GitHub
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.wright@vdb.com'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-00044987
                item:
                  status: open
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.wright@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: sarah.jones@vdb.com
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: amanda.lee@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.wright@vdb.com
                approver_email: sarah.jones@vdb.com
                details: Request for GitHub write access for QA Engineer in Product & Engineering. Sensitivity Group 3 — Confidential. Previous access (TCK-00044987) was lost and requires re-provisioning.
                urgency: standard
                ticket_id: TCK-00044987
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.wright@vdb.com
                approver_email: amanda.lee@vdb.com
                details: Request for GitHub write access for QA Engineer in Product & Engineering. Sensitivity Group 3 — Confidential. Requires IT Security approval per policy.
                urgency: standard
                ticket_id: TCK-00044987
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-00044987
                item:
                  status: pending
                  approval_required: 'yes'
                  approver_id: WD-681453,WD-753918
                  approval_request_ids: APR-00000007,APR-00000008
                  approval_status: pending
    """

    validate_database(x)


def test_sa_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to request access to the Admin Panel. Could you help me with that?
    user_context: |
        You are Nathan Parker, a Sales Representative requesting access to the Admin Panel.

        Only if you are asked about your email address — tell the agent it is nathan.parker@vdb.com.
        Only if you are asked about what type of access or specific details about the permissions — tell the agent you need read-only access.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm details or the request, confirm affirmatively.
        - Your business justification is that you need to look up customer account status when discussing renewals with clients.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-641793
              email: nathan.parker@vdb.com
              full_name: Nathan Parker
              level: 2
              department: sales
              role: Sales Representative
              office_location: sf
              start_date: '2023-07-15T00:00:00Z'
              manager_id: WD-738261
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-738261
              email: rachel.wright@vdb.com
              full_name: Rachel Wright
              level: 5
              department: sales
              role: Sales Director
              office_location: sf
              start_date: '2020-04-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Parker
              email: nathan.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-731-4826
              verified: true
              active: true
              created_at: '2024-07-15T00:00:00Z'
              updated_at: '2024-07-15T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.parker@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: nathan.parker@vdb.com
                app_name: Admin Panel
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.parker@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Admin Panel Read-Only Access Request
                  description: Request for Admin Panel read-only access for Sales Representative Nathan Parker. Employee needs to look up customer account status when discussing renewals with clients.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: nathan.parker@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: rachel.wright@vdb.com
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: amanda.lee@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: nathan.parker@vdb.com
                approver_email: rachel.wright@vdb.com
                details: 'Requesting Admin Panel read-only access for Nathan Parker (Sales Representative, Level 2). Business justification: Employee needs to look up customer account status when discussing renewals with clients.'
                urgency: standard
                ticket_id: '6'
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: nathan.parker@vdb.com
                approver_email: amanda.lee@vdb.com
                details: 'Requesting Admin Panel read-only access for Nathan Parker (Sales Representative, Level 2). IT Security approval required for Sensitivity Group 3 tool. Business justification: Employee needs to look up customer account status when discussing renewals with clients.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  type: problem
                  priority: normal
                  status: pending
                  subject: Admin Panel Read-Only Access Request
                  description: Request for Admin Panel read-only access for Sales Representative Nathan Parker. Employee needs to look up customer account status when discussing renewals with clients. Pending manager and IT Security approvals.
                  tags: null
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-738261,WD-753918
                  approval_request_ids: APR-00000007,APR-00000008
                  business_justification: null
                  access_expiry_date: null
    """

    validate_database(x)


def test_sa_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Daniel Harris from the Product team. My email is daniel.harris@vdb.com. I'd like to request access to the Marketing BI dashboard. I need to see revenue metrics for product roadmap planning. Can you help me get that set up?
    user_context: |
        You are Daniel Harris, a Product Manager in the product_engineering department, contacting IT support to request access to the Marketing BI dashboard. Your reason is that you need revenue metrics for product roadmap planning.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637284
              email: daniel.harris@vdb.com
              full_name: Daniel Harris
              level: 5
              department: product_engineering
              role: Product Manager
              office_location: sf
              start_date: '2020-08-15T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-48291635
              employee_id: WD-637284
              group_name: bi_product_analytics
              added_at: '2020-09-01T10:00:00Z'
              added_by: system
              is_active: true
            - id: OGM-59372814
              employee_id: WD-637284
              group_name: product_team
              added_at: '2020-08-20T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_users:
            - id: '6'
              name: Daniel Harris
              email: daniel.harris@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-729-3841
              verified: true
              active: true
              created_at: '2024-04-10T00:00:00Z'
              updated_at: '2024-04-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.harris@vdb.com
            - tool: okta_api_get_user_groups
              parameters:
                email: daniel.harris@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.harris@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Marketing BI Dashboard Access Request
                  description: Employee requests access to Marketing BI dashboard (bi_marketing_viewers) for product roadmap planning. Needs to see revenue metrics.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  tags: null
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.harris@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: sarah.jones@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.harris@vdb.com
                approver_email: sarah.jones@vdb.com
                details: 'Request for access to Marketing BI dashboards (bi_marketing_viewers). Business justification: Need to see revenue metrics for product roadmap planning.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Marketing BI Dashboard Access Request
                  description: Employee requests access to Marketing BI dashboard (bi_marketing_viewers) for product roadmap planning. Needs to see revenue metrics.
                  tags: null
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-681453
                  approval_request_ids: APR-00000007
                  business_justification: null
                  access_expiry_date: null
    """

    validate_database(x)


def test_sa_013(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Rachel Nguyen from HR People Operations. My email is rachel.nguyen@vdb.com. I need HR admin access in Workday to process employee transfers and compensation changes. Currently I only have standard access, which isn't sufficient for those tasks. Could you help me get elevated access?
    user_context: |
        You are Rachel Nguyen, an HR Coordinator in the HR People Operations department, requesting elevated Workday HRIS access to handle employee transfers and compensation changes. You currently have standard access.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm the access upgrade, confirm it.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415739
              email: rachel.nguyen@vdb.com
              full_name: Rachel Nguyen
              level: 3
              department: hr
              role: HR Coordinator
              office_location: sf
              start_date: '2022-04-01T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41573926
              employee_id: WD-415739
              app_name: Workday HRIS
              access_level: standard
              granted_at: '2022-05-10T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          zendesk_users:
            - id: '6'
              name: Rachel Nguyen
              email: rachel.nguyen@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-8294
              verified: true
              active: true
              created_at: '2024-04-10T00:00:00Z'
              updated_at: '2024-04-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.nguyen@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: rachel.nguyen@vdb.com
                app_name: Workday HRIS
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.nguyen@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Workday HRIS Elevated Access Request
                  description: Employee requests elevated Workday HRIS access to process employee transfers and compensation changes.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: okta_api_revoke_access
              parameters:
                email: rachel.nguyen@vdb.com
                app_name: Workday HRIS
            - tool: okta_api_provision_access
              parameters:
                email: rachel.nguyen@vdb.com
                app_name: Workday HRIS
                access_level: elevated
                is_temporary: false
                access_expiry_date: null
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Workday HRIS Elevated Access Request
                  description: Employee requests elevated Workday HRIS access to process employee transfers and compensation changes.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  access_expiry_date: null
    """

    validate_database(x)


def test_sa_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I submitted a request for Admin Panel access upgrade last week and it's still pending. Can you check on the approval status? My name is Daniel Parker and my email is daniel.parker@vdb.com.
    user_context: |
        You are Daniel Parker, a Compliance Officer at the company, following up on a pending Admin Panel (write non-PII only) access request you submitted about 5 days ago. You want to know the current status of the approvals.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent informs you that both approvals are still pending, acknowledge and thank them.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637284
              email: daniel.parker@vdb.com
              full_name: Daniel Parker
              level: 5
              department: compliance_risk
              role: Compliance Officer
              office_location: sf
              start_date: '2020-11-15T00:00:00Z'
              manager_id: WD-926473
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Parker
              email: daniel.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-729-3841
              verified: true
              active: true
              created_at: '2024-09-10T00:00:00Z'
              updated_at: '2024-09-10T00:00:00Z'
          zendesk_tickets:
            - id: TCK-00045123
              subject: Admin Panel write non-PII only Access Request
              description: Requesting Admin Panel write non-PII only access for compliance monitoring and reporting purposes.
              status: pending
              priority: normal
              type: problem
              requester_id: '6'
              assignee_id: '2'
              organization_id: '1'
              tags:
                - access_request
                - admin_panel
              created_at: '2025-09-26T10:00:00Z'
              updated_at: '2025-09-26T14:00:00Z'
              due_at: null
              resolution_category: null
              owner: it_support
              access_expiry_date: null
              approval_required: 'yes'
              approval_status: pending
              approver_id: WD-926473,WD-753918
              approval_request_ids: APR-47291835,APR-63819247
              business_justification: Compliance monitoring requires Admin Panel write access for non-PII data to perform regulatory reporting.
              incident_severity: null
              customer_impact: null
              asset_id: null
          sandbox_neobank_support_main_models_approval_requests:
            - id: APR-47291835
              request_type: access_request
              requester_id: WD-637284
              approver_id: WD-926473
              status: pending
              urgency: standard
              details: 'Director-level approval for Admin Panel write non-PII only access. Employee: Daniel Parker (Compliance Officer, Level 5, compliance_risk). Justification: Compliance monitoring and regulatory reporting.'
              ticket_id: TCK-00045123
              created_at: '2025-09-26T12:00:00Z'
              decided_at: null
              approver_feedback: null
            - id: APR-63819247
              request_type: access_request
              requester_id: WD-637284
              approver_id: WD-753918
              status: pending
              urgency: standard
              details: 'IT Security approval for Admin Panel write non-PII only access. Employee: Daniel Parker (Compliance Officer, Level 5, compliance_risk). Justification: Compliance monitoring and regulatory reporting.'
              ticket_id: TCK-00045123
              created_at: '2025-09-26T12:00:00Z'
              decided_at: null
              approver_feedback: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-62839174
              employee_id: WD-637284
              group_name: compliance_team
              added_at: '2020-11-16T09:00:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41739286
              employee_id: WD-637284
              app_name: Salesforce
              access_level: read_only
              granted_at: '2020-11-20T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.parker@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.parker@vdb.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                $filter: requester_id eq '6' and status eq 'pending'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-00045123
                item:
                  status: open
            - tool: approval_api_check_status
              parameters:
                approval_request_id: APR-47291835
            - tool: approval_api_check_status
              parameters:
                approval_request_id: APR-63819247
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-00045123
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Admin Panel write non-PII only Access Request
                  description: 'Requesting Admin Panel write non-PII only access for compliance monitoring and reporting purposes. Status check performed on 2025-10-01: both approvals (Director-level and IT Security) are still pending.'
                  tags: null
                  owner: it_support
                  approval_required: 'yes'
                  approver_id: WD-926473,WD-753918
                  approval_request_ids: APR-47291835,APR-63819247
    """

    validate_database(x)


def test_sa_015(x: TestContext, judge: Judge):
    """!
    query: |
        Hey, I'm Ryan Patel (ryan.patel@vdb.com) from the product engineering team. I need to get read-only access to the AWS Production console. I'm trying to debug an issue in the payment service that only reproduces in production and I can't make progress without being able to see what's happening there. Can you help me get that set up?
    user_context: |
        You are Ryan Patel, a contract software developer in the product engineering department. You are contacting IT support to request read-only access to the AWS Production console because you need to debug a payment service issue that only reproduces in production.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent denies your request, you may express disappointment or ask if there are any alternatives, but ultimately accept the decision. Do not escalate aggressively or claim to be a full-time employee.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415738
              email: ryan.patel@vdb.com
              full_name: Ryan Patel
              level: 3
              department: product_engineering
              role: Contract Software Developer
              office_location: sf
              start_date: '2025-06-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: true
              remote_delivery_address: null
              contract_end_date: '2026-03-31T00:00:00Z'
          zendesk_users:
            - id: '6'
              name: Ryan Patel
              email: ryan.patel@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-2918
              verified: true
              active: true
              created_at: '2025-06-01T00:00:00Z'
              updated_at: '2025-06-01T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41573829
              employee_id: WD-415738
              app_name: Slack
              access_level: read_write
              granted_at: '2025-06-02T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-41573846
              employee_id: WD-415738
              app_name: GitHub
              access_level: read_write
              granted_at: '2025-06-02T09:15:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-41573891
              employee_id: WD-415738
              app_name: Jira
              access_level: read_write
              granted_at: '2025-06-02T09:30:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41573826
              employee_id: WD-415738
              group_name: engineers
              added_at: '2025-06-02T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.patel@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: ryan.patel@vdb.com
                app_name: AWS Production
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.patel@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: AWS Production Access Request
                  description: Contractor in Product & Engineering requests AWS Production (user) access for debugging a payment service issue that only reproduces in production.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: AWS Production Access Request
                  description: 'Contractor in Product & Engineering requests AWS Production (user) access for debugging a payment service issue. Denied: contractors cannot access Group 5 (Production Infrastructure) tools.'
                  tags: production_access
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: denied
                  business_justification: I need to debug an issue in the payment service that only reproduces in production.
    """

    validate_database(x)


def test_sa_016(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need Tableau (viewer) access to export details on my client billing history before I leave next week. My name is Derek Lawson and my email is derek.lawson@vdb.com. Can you help me get this set up?
    user_context: |
        You are Derek Lawson, a departing Account Manager at the company. You are requesting Tableau (viewer) access so you can export client billing history before your last day. You believe this is important for a proper handoff.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent denies your request, you may express mild disappointment but ultimately accept the decision. You can ask if there's an alternative way to get the billing data you need.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-641873
              email: derek.lawson@vdb.com
              full_name: Derek Lawson
              level: 4
              department: sales
              role: Account Manager
              office_location: sf
              start_date: '2021-04-05T00:00:00Z'
              manager_id: WD-294817
              employment_status: departing
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Derek Lawson
              email: derek.lawson@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-736-2841
              verified: true
              active: true
              created_at: '2024-04-10T00:00:00Z'
              updated_at: '2024-04-10T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41753926
              employee_id: WD-641873
              app_name: Salesforce
              access_level: standard
              granted_at: '2021-04-12T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-52869314
              employee_id: WD-641873
              app_name: Slack
              access_level: member
              granted_at: '2021-04-12T09:05:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-83641572
              employee_id: WD-641873
              group_name: sales_team
              added_at: '2021-04-12T09:10:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: derek.lawson@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'derek.lawson@vdb.com'
            - tool: okta_api_check_access
              parameters:
                email: derek.lawson@vdb.com
                app_name: Tableau
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Tableau (viewer) access request
                  description: Departing employee requests Tableau (viewer) access to export client billing history before leaving.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Tableau (viewer) access request
                  description: 'Departing employee requests Tableau (viewer) access to export client billing history. Denied: departing employees cannot be granted access to Group 2-5 tools per policy.'
                  tags: offboarding
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: denied
    """

    validate_database(x)


def test_sa_018(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I just joined the company recently and I need access to Jira for task tracking and Confluence for documentation. My onboarding checklist mentioned I should have these tools set up. My name is Nathan Park, email is nathan.park@vdb.com. Can you help me get access?
    user_context: |
        You are Nathan Park, a newly hired Project Manager who just started at the company on September 10th. You believe you need Jira and Confluence access for your work but haven't tried logging into them yet. You're reaching out proactively based on your onboarding checklist.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent tells you that you already have access, accept that information graciously and thank them.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-417592
              email: nathan.park@vdb.com
              full_name: Nathan Park
              level: 4
              department: product_engineering
              role: Project Manager
              office_location: sf
              start_date: '2025-09-10T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Park
              email: nathan.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-2849
              verified: true
              active: true
              created_at: '2025-09-10T00:00:00Z'
              updated_at: '2025-09-10T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41759201
              employee_id: WD-417592
              app_name: Jira
              access_level: user
              granted_at: '2025-09-10T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-41759202
              employee_id: WD-417592
              app_name: Confluence
              access_level: user
              granted_at: '2025-09-10T09:05:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.park@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.park@vdb.com'
            - tool: okta_api_check_access
              parameters:
                email: nathan.park@vdb.com
                app_name: Jira
            - tool: okta_api_check_access
              parameters:
                email: nathan.park@vdb.com
                app_name: Confluence
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Access Request for Jira and Confluence
                  description: Employee requested access to Jira and Confluence for onboarding. Verified employee already has active access to both tools at the requested level.
                  status: open
                  priority: low
                  type: question
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: question
                  priority: low
                  subject: Access Request for Jira and Confluence
                  description: Employee requested access to Jira and Confluence for onboarding. Verified employee already has active access to both tools at the requested level.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: information_provided
    """

    validate_database(x)


def test_sa_019(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need Quantivate access to log and monitor compliance findings for our quarterly audits. My name is Daniel Park and my email is daniel.park@vdb.com. Could you help me get this set up?
    user_context: |
        You are Daniel Park, a Compliance Analyst in the Compliance & Risk department, contacting IT support to request access to Quantivate for risk management tracking purposes.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-417583
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 3
              department: compliance_risk
              role: Compliance Analyst
              office_location: sf
              start_date: '2023-06-15T00:00:00Z'
              manager_id: WD-584201
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Park
              email: daniel.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-8294
              verified: true
              active: true
              created_at: '2024-06-15T00:00:00Z'
              updated_at: '2024-06-15T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41758392
              employee_id: WD-417583
              group_name: compliance_team
              added_at: '2023-06-16T09:00:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.park@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: daniel.park@vdb.com
                app_name: Quantivate
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.park@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Quantivate access request for Compliance Analyst
                  description: Employee requests Quantivate user access to log and monitor compliance findings for quarterly audits.
                  type: problem
                  priority: normal
                  status: open
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: okta_api_provision_access
              parameters:
                email: daniel.park@vdb.com
                app_name: Quantivate
                access_level: user
                is_temporary: false
                access_expiry_date: null
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  type: problem
                  priority: normal
                  status: solved
                  subject: Quantivate access request for Compliance Analyst
                  description: Employee requests Quantivate user access to log and monitor compliance findings for quarterly audits.
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  access_expiry_date: null
    """

    validate_database(x)


def test_sa_020(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need help getting Actimize access set up.
    user_context: |
        You are Daniel Wright, an AML Investigator in the Compliance & Risk department, requesting access to Actimize for transaction monitoring and investigating suspicious activity alerts.

        Only if you are asked about your name — your name is Daniel Wright.
        Only if you are asked about your email address or contact information — your email is daniel.wright@vdb.com.
        Only if you are asked about your team or department — you are starting on the AML team in the Compliance & Risk department.
        Only if you are asked about the purpose or why you need Actimize access — you need it to investigate suspicious activity alerts and for transaction monitoring.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637284
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 3
              department: compliance_risk
              role: AML Investigator
              office_location: sf
              start_date: '2022-11-01T00:00:00Z'
              manager_id: WD-584201
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Wright
              email: daniel.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-736-2918
              verified: true
              active: true
              created_at: '2024-09-10T00:00:00Z'
              updated_at: '2024-09-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.wright@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.wright@vdb.com'
            - tool: okta_api_check_access
              parameters:
                email: daniel.wright@vdb.com
                app_name: Actimize
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Actimize access request - AML Investigator
                  description: Employee requests Actimize (user) access for AML transaction monitoring and investigating suspicious activity alerts.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
            - tool: okta_api_provision_access
              parameters:
                email: daniel.wright@vdb.com
                app_name: Actimize
                access_level: user
                is_temporary: false
                access_expiry_date: null
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Actimize access request - AML Investigator
                  description: Employee requests Actimize (user) access for AML transaction monitoring and investigating suspicious activity alerts.
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  access_expiry_date: null
    """

    validate_database(x)


def test_sa_022(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to request access to Customer PII fields.
    user_context: |
        You are Daniel Wright, a Customer Support Specialist at the company, requesting access to Customer PII fields.

        Only if you are asked about your name or who you are — tell the agent you are Daniel Wright from the Customer Support team.
        Only if you are asked about your email address — tell the agent it is daniel.wright@vdb.com.
        Only if you are asked about what specific PII fields you need access to — tell the agent you need to view full customer addresses and phone numbers.
        Only if you are asked about what type of access you need — tell the agent you need read-only access.
        Only if you are asked about the purpose or why you need this access — tell the agent it's to help resolve escalated complaints.
        Only if you are asked about your current access level or permissions — tell the agent you currently only have standard Admin Panel access and can't see that PII information.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent confirms the request has been submitted and is pending approvals, acknowledge and thank them.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-641857
              email: daniel.wright@vdb.com
              full_name: Daniel Wright
              level: 3
              department: customer_support
              role: Customer Support Specialist
              office_location: austin
              start_date: '2023-04-01T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41637285
              employee_id: WD-641857
              app_name: Admin Panel
              access_level: read_only
              granted_at: '2023-04-15T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-82417563
              employee_id: WD-641857
              group_name: support_team
              added_at: '2023-04-01T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_users:
            - id: '6'
              name: Daniel Wright
              email: daniel.wright@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-748-3261
              verified: true
              active: true
              created_at: '2024-04-10T00:00:00Z'
              updated_at: '2024-04-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.wright@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: daniel.wright@vdb.com
                app_name: Customer PII fields
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.wright@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Request for Customer PII fields read-only access
                  description: Customer Support Specialist (Tier 1) requesting read-only access to Customer PII fields to view full customer addresses and phone numbers for resolving escalated complaints.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.wright@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: maria.garcia@vdb.com
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: amanda.lee@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.wright@vdb.com
                approver_email: maria.garcia@vdb.com
                details: 'Requesting read-only access to Customer PII fields for Customer Support Specialist (Tier 1). Employee states: needs to view full customer addresses and phone numbers to help resolve escalated complaints.'
                urgency: standard
                ticket_id: '6'
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.wright@vdb.com
                approver_email: amanda.lee@vdb.com
                details: 'Requesting read-only access to Customer PII fields for Customer Support Specialist (Tier 1). Employee states: needs to view full customer addresses and phone numbers to help resolve escalated complaints.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Request for Customer PII fields read-only access
                  description: Customer Support Specialist (Tier 1) requesting read-only access to Customer PII fields to view full customer addresses and phone numbers for resolving escalated complaints.
                  tags: null
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: null
                  approver_id: WD-739154,WD-753918
                  approval_request_ids: APR-00000007,APR-00000008
    """

    validate_database(x)


def test_sa_023(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Daniel Park (daniel.park@vdb.com), a Data Engineer on the Product Engineering team. I need raw replica access for the data migration project - the depersonalized data doesn't have all the fields I need for the ETL pipeline. Could you help me get access to Snowflake raw replica?
    user_context: |
        You are Daniel Park, a Data Engineer requesting access to Snowflake raw replica for a data migration project. You currently have Snowflake depersonalized access but it lacks the fields you need for your ETL pipeline work.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent asks for the project end date or when you expect the data migration project to be completed, respond that the project is expected to wrap up by November 30, 2025.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415837
              email: daniel.park@vdb.com
              full_name: Daniel Park
              level: 4
              department: product_engineering
              role: Data Engineer
              office_location: sf
              start_date: '2022-08-01T00:00:00Z'
              manager_id: WD-638274
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
            - id: WD-638274
              email: ryan.nakamura@vdb.com
              full_name: Ryan Nakamura
              level: 5
              department: product_engineering
              role: Engineering Lead
              office_location: sf
              start_date: '2021-03-15T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41583729
              employee_id: WD-415837
              app_name: Snowflake depersonalized
              access_level: analyst
              granted_at: '2023-02-15T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41583726
              employee_id: WD-415837
              group_name: engineers
              added_at: '2022-08-02T09:00:00Z'
              added_by: system
              is_active: true
          zendesk_users:
            - id: '6'
              name: Daniel Park
              email: daniel.park@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-729-3841
              verified: true
              active: true
              created_at: '2024-08-10T00:00:00Z'
              updated_at: '2024-08-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          sandbox_neobank_support_main_models_customer_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.park@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: daniel.park@vdb.com
                app_name: Snowflake raw replica
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.park@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Snowflake raw replica access request - Data Migration Project
                  description: 'Employee requests access to Snowflake raw replica (analyst) for data migration project. Business justification: depersonalized data doesn''t have all fields needed for the ETL pipeline. Project-based temporary access through 2025-11-30.'
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.park@vdb.com
            - tool: approver_lookup_api_get_approver_contact
              parameters:
                required_approver: it_security
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: sarah.jones@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: amanda.lee@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.park@vdb.com
                approver_email: sarah.jones@vdb.com
                details: 'Request for Snowflake raw replica (analyst) access for Data Engineer. Business justification: data migration project - depersonalized data doesn''t have all fields needed for ETL pipeline. Temporary access until 2025-11-30.'
                urgency: standard
                ticket_id: '6'
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.park@vdb.com
                approver_email: amanda.lee@vdb.com
                details: 'Request for Snowflake raw replica (analyst) access for Data Engineer. Business justification: data migration project - depersonalized data doesn''t have all fields needed for ETL pipeline. Temporary access until 2025-11-30.'
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  tags: temporary_access
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: Data migration project - depersonalized data doesn't have all fields needed for ETL pipeline.
                  approver_id: WD-681453,WD-753918
                  approval_request_ids: APR-00000007,APR-00000008
                  access_expiry_date: '2025-11-30T13:00:00Z'
    """

    validate_database(x)


def test_sa_024(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Ryan Patterson, Infrastructure Engineer on the Product Engineering team. My email is ryan.patterson@vdb.com. I need AWS Production access to manage our infrastructure and deploy updates to the payment service. Currently I only have staging access and need to be able to work directly in production. Can you help set this up?
    user_context: |
        You are Ryan Patterson, an Infrastructure Engineer in the Product & Engineering department, requesting AWS Production console access for routine infrastructure management and deployment work. You do NOT have an active incident to reference — your need is for general day-to-day infrastructure work and payment service deployments.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent denies your request, accept the decision gracefully. Do not ask the agent to route, escalate, or find alternative ways.
        - If asked whether this is related to an active incident, be honest and say no — it is for routine infrastructure management and deployments.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415738
              email: ryan.patterson@vdb.com
              full_name: Ryan Patterson
              level: 4
              department: product_engineering
              role: Infrastructure Engineer
              office_location: sf
              start_date: '2022-03-15T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Ryan Patterson
              email: ryan.patterson@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-673-8291
              verified: true
              active: true
              created_at: '2024-04-10T00:00:00Z'
              updated_at: '2024-04-10T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41578236
              employee_id: WD-415738
              app_name: GitHub
              access_level: read_write
              granted_at: '2022-03-20T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-41578394
              employee_id: WD-415738
              app_name: Jira
              access_level: read_write
              granted_at: '2022-03-20T10:05:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41573829
              employee_id: WD-415738
              group_name: engineers
              added_at: '2022-03-20T09:00:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.patterson@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: ryan.patterson@vdb.com
                app_name: AWS Production
            - tool: security_api_verify_incident
              parameters: {}
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.patterson@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: AWS Production Access Request
                  description: Employee requests AWS Production console access for infrastructure management and payment service deployments.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  tags: production_access
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: denied
                  business_justification: I need AWS Production access to manage our infrastructure and deploy updates to the payment service.
    """

    validate_database(x)


def test_sa_025(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Nathan Parker from the Compliance & Risk team (nathan.parker@vdb.com). I need Splunk access to investigate security alerts and analyze log data for our SOC operations. Could you help me get that set up?
    user_context: |
        You are Nathan Parker, a Security Analyst in the Compliance & Risk department, requesting access to Splunk SIEM. You genuinely believe you need this tool for your security-related work.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent denies your request, you may express mild disappointment but ultimately accept the decision. You can ask if there are any alternative paths or who you could talk to about getting an exception.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-641827
              email: nathan.parker@vdb.com
              full_name: Nathan Parker
              level: 4
              department: compliance_risk
              role: Security Analyst
              office_location: sf
              start_date: '2021-10-01T00:00:00Z'
              manager_id: WD-584201
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Parker
              email: nathan.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-736-2891
              verified: true
              active: true
              created_at: '2024-09-10T00:00:00Z'
              updated_at: '2024-09-10T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.parker@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: nathan.parker@vdb.com
                app_name: Splunk SIEM
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.parker@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Splunk SIEM Access Request
                  description: Employee requests access to Splunk SIEM to investigate security alerts and analyze log data for SOC operations. Access denied per policy — Splunk SIEM is restricted to IT Security and IT Operations departments.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Splunk SIEM Access Request
                  description: Employee requests access to Splunk SIEM to investigate security alerts and analyze log data for SOC operations. Access denied per policy — Splunk SIEM is restricted to IT Security and IT Operations departments.
                  tags: production_access
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: denied
    """

    validate_database(x)


def test_sa_026(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Ryan Patel (ryan.patel@vdb.com). I need read access to the mobile app repository on GitHub to review code for my testing work. Could you help me get that set up?
    user_context: |
        You are Ryan Patel, a contract QA Analyst at the company, requesting GitHub read-only access to support your testing work. Your email is ryan.patel@vdb.com.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-637182
              email: ryan.patel@vdb.com
              full_name: Ryan Patel
              level: 3
              department: product_engineering
              role: QA Analyst
              office_location: sf
              start_date: '2025-08-01T00:00:00Z'
              manager_id: WD-681453
              employment_status: active
              is_contractor: true
              remote_delivery_address: null
              contract_end_date: '2026-07-31T00:00:00Z'
          zendesk_users:
            - id: '6'
              name: Ryan Patel
              email: ryan.patel@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-2914
              verified: true
              active: true
              created_at: '2025-07-20T00:00:00Z'
              updated_at: '2025-07-20T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: ryan.patel@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: ryan.patel@vdb.com
                app_name: GitHub
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'ryan.patel@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: GitHub Read-Only Access Request
                  description: Contractor QA Analyst requesting GitHub read-only access to review code for testing work on mobile app repository.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: ryan.patel@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: sarah.jones@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: ryan.patel@vdb.com
                approver_email: sarah.jones@vdb.com
                details: Contractor QA Analyst requesting GitHub read-only access to review code for testing work on mobile app repository. Temporary access until contract end date 2026-07-31.
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: GitHub Read-Only Access Request
                  description: Contractor QA Analyst requesting GitHub read-only access to review code for testing work on mobile app repository.
                  tags: temporary_access
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-681453
                  approval_request_ids: APR-00000007
                  access_expiry_date: '2026-07-31T00:00:00Z'
    """

    validate_database(x)


def test_sa_027(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Rachel Cooper from the Customer Support team. My email is rachel.cooper@vdb.com. I currently have read-only access to Customer PII fields, but I need to be able to update customer contact information when they request changes through our support channels. Could you please upgrade my access to write level?
    user_context: |
        You are Rachel Cooper, a Customer Support Manager, requesting write access to Customer PII fields. You currently have read-only access and want write access so you can update customer contact info when customers request changes through support channels.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent denies your request, you may express disappointment but accept the decision. Do not argue excessively or try to override policy.
        - If the agent asks which system you use or suggests alternative tools, redirect to your original request: you specifically need write access to Customer PII fields. Do not mention or invent any other systems or tools.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-413876
              email: rachel.cooper@vdb.com
              full_name: Rachel Cooper
              level: 5
              department: customer_support
              role: Customer Support Manager
              office_location: austin
              start_date: '2020-06-01T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41387625
              employee_id: WD-413876
              app_name: Customer PII fields
              access_level: read_only
              granted_at: '2024-03-15T10:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          zendesk_users:
            - id: '6'
              name: Rachel Cooper
              email: rachel.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-673-8294
              verified: true
              active: true
              created_at: '2024-02-10T00:00:00Z'
              updated_at: '2024-02-10T00:00:00Z'
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41387293
              employee_id: WD-413876
              group_name: support_team
              added_at: '2020-06-01T10:00:00Z'
              added_by: system
              is_active: true
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: rachel.cooper@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: rachel.cooper@vdb.com
                app_name: Customer PII fields
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'rachel.cooper@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Request for write access to Customer PII fields
                  description: Employee Rachel Cooper (Customer Support Manager, Level 5) requests write access to Customer PII fields to update customer contact information when customers request changes through support channels. Employee currently has read-only access. Write access to Customer PII fields is forbidden for all employees per policy.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Request for write access to Customer PII fields
                  description: Employee Rachel Cooper (Customer Support Manager, Level 5) requests write access to Customer PII fields to update customer contact information when customers request changes through support channels. Employee currently has read-only access. Write access to Customer PII fields is forbidden for all employees per policy. Request denied — write access is forbidden for all employees.
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: denied
    """

    validate_database(x)


def test_sa_028(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need Tableau viewer access for my analysis work. My name is Daniel Parker and my email is daniel.parker@vdb.com.
    user_context: |
        You are Daniel Parker, a Business Analyst in the finance_accounting department, requesting Tableau viewer access to view financial reports and dashboards.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent asks you to confirm details about your request, confirm that you need viewer-level access for Tableau.
        - If asked whether this is permanent or temporary access, say it's permanent / ongoing — you need it for your regular work.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415973
              email: daniel.parker@vdb.com
              full_name: Daniel Parker
              level: 3
              department: finance_accounting
              role: Business Analyst
              office_location: sf
              start_date: '2023-11-01T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Daniel Parker
              email: daniel.parker@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-267-8394
              verified: true
              active: true
              created_at: '2024-02-10T00:00:00Z'
              updated_at: '2024-02-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: daniel.parker@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: daniel.parker@vdb.com
                app_name: Tableau
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'daniel.parker@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Tableau Viewer Access Request
                  description: Employee requests Tableau viewer access to view financial reports and dashboards for analysis work in the finance_accounting department.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
            - tool: workday_api_get_manager_chain
              parameters:
                email: daniel.parker@vdb.com
            - tool: approver_lookup_api_get_contact_details
              parameters:
                email: chris.johnson@vdb.com
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: daniel.parker@vdb.com
                approver_email: chris.johnson@vdb.com
                details: Requesting Tableau viewer access for Business Analyst in finance_accounting department to view financial reports and dashboards for analysis work.
                urgency: standard
                ticket_id: '6'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: Tableau Viewer Access Request
                  description: Employee requests Tableau viewer access to view financial reports and dashboards for analysis work in the finance_accounting department.
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  approver_id: WD-671392
                  approval_request_ids: APR-00000007
                  access_expiry_date: null
    """

    validate_database(x)


def test_sa_029(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need help getting access to Slack.
    user_context: |
        You are Nathan Cooper, a newly hired Customer Support Agent who started on September 25th. You are unable to access Slack and need IT support to help you get access.

        Only if you are asked about your name — tell the agent your name is Nathan Cooper.
        Only if you are asked about your email address — tell the agent it is nathan.cooper@vdb.com.
        Only if you are asked when you started or how long you've been working — tell the agent you started this week (September 25th).
        Only if you are asked about what error or issue you're seeing — tell the agent you're getting an "access denied" error.
        Only if you are asked about what you expected or what colleagues told you — tell the agent your colleagues said you should have been added automatically.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Once the agent tells you that Slack access has been enabled or provisioned for you (even if they also ask you to try signing in again), respond that you tried and it is now working, then thank them and confirm the issue is resolved. Do not report that the issue persists after the agent says access has been provisioned.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-428173
              email: nathan.cooper@vdb.com
              full_name: Nathan Cooper
              level: 2
              department: customer_support
              role: Customer Support Agent
              office_location: austin
              start_date: '2025-09-25T00:00:00Z'
              manager_id: WD-739154
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Cooper
              email: nathan.cooper@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-512-738-4291
              verified: true
              active: true
              created_at: '2025-09-25T00:00:00Z'
              updated_at: '2025-09-25T00:00:00Z'
          sandbox_neobank_support_main_models_okta_app_access: []
          sandbox_neobank_support_main_models_okta_group_membership: []
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_ticket_comments: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.cooper@vdb.com
            - tool: okta_api_check_access
              parameters:
                email: nathan.cooper@vdb.com
                app_name: Slack
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.cooper@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Slack access request - new hire
                  description: New Customer Support Agent started 2025-09-25, unable to access Slack. Default Group 1 access to be provisioned.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  due_at: null
                  owner: it_support
            - tool: okta_api_provision_access
              parameters:
                email: nathan.cooper@vdb.com
                app_name: Slack
                access_level: member
                is_temporary: false
                access_expiry_date: null
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: Slack access request - new hire
                  description: New Customer Support Agent started 2025-09-25, unable to access Slack. Default Group 1 access to be provisioned.
                  tags: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  access_expiry_date: null
    """

    validate_database(x)


def test_sl_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I found this great tool for lead generation called LeadBooster Pro and I'd love to get it installed on my machine. Can you help me with that? My name is Derek Novak, email is derek.novak@vdb.com.
    user_context: |
        You are Derek Novak, a Sales Representative at VDB. You want to get a software called 'LeadBooster Pro' installed — you found it online and think it would help with lead generation. You don't have a ticket for this yet.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-415783
              email: derek.novak@vdb.com
              full_name: Derek Novak
              level: 2
              department: sales
              role: Sales Representative
              office_location: sf
              start_date: '2024-01-15T00:00:00Z'
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Derek Novak
              email: derek.novak@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-8249
              verified: true
              active: true
              created_at: '2024-01-15T00:00:00Z'
              updated_at: '2024-01-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles:
            - id: 360001
              url: https://vdb.zendesk.com/api/v2/help_center/articles/360001.json
              html_url: https://vdb.zendesk.com/hc/en-us/articles/360001
              title: Approved Software List
              body: <h1>Approved Software List</h1><p>The following software applications have been approved for use at VDB. If you need software not on this list, please contact IT Support for review.</p><h2>Communication &amp; Collaboration</h2><ul><li>Slack</li><li>Zoom</li><li>Microsoft Teams</li></ul><h2>Project Management</h2><ul><li>Jira</li><li>Confluence</li><li>Asana</li></ul><h2>Development Tools</h2><ul><li>GitHub</li><li>VS Code</li><li>IntelliJ IDEA</li></ul><h2>Business Applications</h2><ul><li>Salesforce CRM</li><li>Workday</li><li>Tableau</li><li>Snowflake</li></ul><h2>Security &amp; Compliance</h2><ul><li>Splunk SIEM</li><li>Quantivate</li><li>Actimize</li></ul><h2>Productivity</h2><ul><li>Google Workspace</li><li>Adobe Acrobat</li><li>DocuSign</li></ul><p>Software not on this list is considered unapproved and requires IT Security review before installation.</p>
              snippet: Approved Software List. The following software applications have been approved for use at VDB...
              author_id: 1
              section_id: 1001
              category_id: null
              brand_id: null
              locale: en-us
              source_locale: en-us
              draft: false
              promoted: true
              position: 0
              vote_sum: 15
              vote_count: 18
              comments_disabled: false
              outdated: false
              outdated_locales: []
              label_names:
                - software
                - approved
                - installation
              content_tag_ids: []
              user_segment_id: null
              permission_group_id: null
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-08-15T14:30:00Z'
              edited_at: '2025-08-15T14:30:00Z'
              result_type: article
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41573829
              employee_id: WD-415783
              app_name: Salesforce
              access_level: standard
              granted_at: '2024-01-20T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-41578416
              employee_id: WD-415783
              app_name: Slack
              access_level: standard
              granted_at: '2024-01-20T09:05:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-41578362
              employee_id: WD-415783
              group_name: sales_team
              added_at: '2024-01-15T09:00:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_software_licenses: []
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: derek.novak@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'derek.novak@vdb.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: 'Software Installation Request: LeadBooster Pro'
                  description: Employee Derek Novak requests installation of LeadBooster Pro, a lead generation tool found online. Software is not on the company's approved software list and requires IT Security review before installation can proceed.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  owner: it_support
                  created_at: '2025-10-01T13:00:00Z'
                  due_at: null
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: pending
                  type: problem
                  priority: normal
                  subject: 'Software Installation Request: LeadBooster Pro'
                  description: Employee Derek Novak requests installation of LeadBooster Pro, a lead generation tool found online. Software is not on the company's approved software list. Escalated to IT Security team for review of unapproved software.
                  tags: escalated
                  owner: it_sec_team
                  approval_required: 'no'
                  approval_status: not_required
                  updated_at: '2025-10-01T13:00:00Z'
    """

    validate_database(x)


def test_sl_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need 1Password to manage my work passwords securely. How do I get it installed? My name is Nathan Perry and my email is nathan.perry@vdb.com.
    user_context: |
        You are Nathan Perry, a newly hired Financial Analyst in the finance_accounting department. You want to get 1Password installed so you can manage your work passwords securely. You started on September 18, 2025.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent provides installation instructions or guidance (e.g., self-service via Okta App Catalog), acknowledge them and confirm you will follow the steps. Do not report any installation errors, SSO issues, or other technical problems — the installation succeeds without issues.
    init:
      sandbox_neobank_support_v1:
        data_patch:
          sandbox_neobank_support_main_models_employees:
            - id: WD-437295
              email: nathan.perry@vdb.com
              full_name: Nathan Perry
              level: 3
              department: finance_accounting
              role: Financial Analyst
              office_location: sf
              start_date: '2025-09-18T00:00:00Z'
              manager_id: WD-671392
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          zendesk_users:
            - id: '6'
              name: Nathan Perry
              email: nathan.perry@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-736-8294
              verified: true
              active: true
              created_at: '2025-09-18T00:00:00Z'
              updated_at: '2025-09-18T00:00:00Z'
          sandbox_neobank_support_main_models_software_licenses:
            - id: LIC-52847163
              software_name: 1Password
              license_type: unlimited
              total_licenses: null
              annual_cost_per_license: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-82456391
              employee_id: WD-437295
              group_name: finance_team
              added_at: '2025-09-18T09:00:00Z'
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-43729185
              employee_id: WD-437295
              app_name: Slack
              access_level: read_write
              granted_at: '2025-09-18T09:00:00Z'
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_license_allocations: []
          sandbox_neobank_support_main_models_hardware_assets: []
          sandbox_neobank_support_main_models_asset_assignments: []
          sandbox_neobank_support_main_models_approval_requests: []
          sandbox_neobank_support_main_models_customer_accounts: []
          sandbox_neobank_support_main_models_procurement_orders: []
          sandbox_neobank_support_main_models_email_notifications: []
          sandbox_neobank_support_main_models_security_incidents: []
          sandbox_neobank_support_main_models_okta_security_audit: []
          zendesk_tickets: []
          zendesk_ticket_status_violations: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: workday_api_get_employee
              parameters:
                email: nathan.perry@vdb.com
            - tool: zendesk_get_items
              parameters:
                table: users
                $filter: email eq 'nathan.perry@vdb.com'
            - tool: license_management_api_check_license_type
              parameters:
                software_name: 1Password
            - tool: license_management_api_allocate_license
              parameters:
                software_name: 1Password
                email: nathan.perry@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: 1Password Installation Request
                  description: Employee requests 1Password installation for secure work password management.
                  status: open
                  priority: normal
                  type: problem
                  requester_id: '6'
                  assignee_id: '2'
                  organization_id: '1'
                  tags: null
                  due_at: null
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '6'
                item:
                  status: solved
                  type: problem
                  priority: normal
                  subject: 1Password Installation Request
                  description: Employee requests 1Password installation. Unlimited license allocated. Self-service installation via Okta App Catalog recommended.
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
    """

    validate_database(x)
