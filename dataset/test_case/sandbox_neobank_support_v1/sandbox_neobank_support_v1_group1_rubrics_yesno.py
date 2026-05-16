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


def validate_rubrics_yesno(x: TestContext, judge: Judge):
    rubrics = x.effects[SERVER_NAME].get("rubrics_yesno", [])
    for rubric in rubrics:
        assert judge.text_yesno(x.response, rubric), f"Rubric yesno failed: {rubric}"


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
              start_date: "2020-09-01T00:00:00Z"
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
              created_at: "2024-02-15T00:00:00Z"
              updated_at: "2024-02-15T00:00:00Z"
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41637295
              employee_id: WD-637284
              app_name: AWS
              access_level: admin
              granted_at: "2021-03-15T10:00:00Z"
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-52748361
              employee_id: WD-637284
              app_name: Okta
              access_level: admin
              granted_at: "2021-03-15T10:05:00Z"
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-63859472
              employee_id: WD-637284
              app_name: Splunk
              access_level: admin
              granted_at: "2021-06-20T09:30:00Z"
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-48271639
              employee_id: WD-637284
              group_name: it_ops_team
              added_at: "2020-09-05T09:00:00Z"
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
                $filter: "email eq 'daniel.parker@vdb.com'"
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
        rubrics_yesno:
          - "Does the agent's final message avoid claiming that the user's access to systems such as AWS, Okta, or Splunk was verified as undisrupted? No such verification was performed — only a password reset was executed. (Yes = no such claim is made or topic not mentioned, No = the agent claims access to other systems was verified as undisrupted)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2022-09-01T00:00:00Z"
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
              created_at: "2024-09-10T00:00:00Z"
              updated_at: "2024-09-10T00:00:00Z"
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-36294
              device_type: monitor
              device_model: "Dell P2425H 24\\""
              purchase_date: "2024-06-15T00:00:00Z"
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
                $filter: "email eq 'ryan.cooper@vdb.com'"
            - tool: asset_management_api_check_inventory
              parameters:
                device_type: monitor
                warehouse_location: sf
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Monitor Provision Request - DevOps Engineer Ryan Cooper
                  description: "DevOps Engineer Ryan Cooper requesting first external monitor for working with multiple terminal windows. Employee currently has zero monitors assigned. Auto-approved per policy: technical role in SF office with no existing monitors."
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
                  description: "DevOps Engineer Ryan Cooper requesting first external monitor for working with multiple terminal windows. Auto-approved per policy: technical role in SF office with no existing monitors. Assigned Dell P2425H 24\\" (VDB-HW-36294) from SF inventory."
                  owner: it_support
                  approval_required: 'no'
                  approval_status: not_required
                  resolution_category: provisioned
                  asset_id: VDB-HW-36294
        rubrics_yesno:
          - "The agent's system prompt states: 'There is no need in referencing Zendesk tickets, internal tools, URLs to articles, etc.' Does the agent's final message avoid referencing a Zendesk ticket ID (e.g., 'Ticket ID: 6')? (Yes = no ticket ID referenced or topic not mentioned, No = a Zendesk ticket ID is explicitly referenced)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2023-04-01T00:00:00Z"
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
              created_at: "2024-04-15T00:00:00Z"
              updated_at: "2024-04-15T00:00:00Z"
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
                $filter: "email eq 'daniel.foster@vdb.com'"
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
                device_model: "Dell P2425H 24\\""
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
        rubrics_yesno:
          - "Policy states: 'In case a procurement order for a laptop was created due to Hardware failure or Damage, agent should notify employee that they may ask for a temporary device.' This rule applies only to laptop orders. IF the agent's final message concerns a monitor procurement order, does it avoid offering or suggesting a temporary or loaner device? (Yes = no temporary device offer is made, or no monitor procurement discussed, No = agent offers a temporary device for a monitor order)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2022-08-01T00:00:00Z"
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
              created_at: "2024-08-10T00:00:00Z"
              updated_at: "2024-08-10T00:00:00Z"
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-20345
              device_type: monitor
              device_model: Dell UltraSharp 27 U2723DE
              purchase_date: "2023-02-10T00:00:00Z"
              warehouse_location: austin
              condition: good
              is_assigned: true
            - id: VDB-HW-37821
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: "2022-07-15T00:00:00Z"
              warehouse_location: austin
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-42817365
              asset_id: VDB-HW-20345
              employee_id: WD-648273
              assigned_at: "2023-05-10T10:00:00Z"
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-61593847
              asset_id: VDB-HW-37821
              employee_id: WD-648273
              assigned_at: "2022-10-15T10:00:00Z"
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
                $filter: "email eq 'nathan.cooper@vdb.com'"
            - tool: asset_management_api_get_employee_devices
              parameters:
                email: nathan.cooper@vdb.com
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Second monitor request - Data Analyst spreadsheet cross-referencing
                  description: "Employee Nathan Cooper (Data Analyst, finance_accounting, austin) is requesting a second monitor. Currently has one monitor assigned (VDB-HW-20345). Business justification: needs a second monitor for spreadsheet work involving extensive cross-referencing of data."
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
                details: "Request for a second monitor for Data Analyst Nathan Cooper (finance_accounting, austin). Employee currently has one monitor (VDB-HW-20345). Business justification: needs a second monitor for spreadsheet work involving extensive cross-referencing."
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
                  description: "Employee Nathan Cooper (Data Analyst, finance_accounting, austin) is requesting a second monitor. Currently has one monitor assigned (VDB-HW-20345). Business justification: needs a second monitor for spreadsheet work involving extensive cross-referencing of data."
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: I already have one monitor but need a second one for my spreadsheet work - lots of cross-referencing.
                  approver_id: WD-671392
                  approval_request_ids: APR-00000007
        rubrics_yesno:
          - "Policy states: 'There is no need in referencing Zendesk tickets, internal tools, URLs to articles, etc.' Does the agent's final message avoid referencing Zendesk ticket IDs or internal system request IDs (e.g., approval request IDs)? (Yes = no such IDs mentioned, No = mentions a Zendesk ticket ID or internal system request ID)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2022-06-01T00:00:00Z"
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
              created_at: "2024-06-01T00:00:00Z"
              updated_at: "2024-06-01T00:00:00Z"
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-62847
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: "2022-06-01T00:00:00Z"
              warehouse_location: austin
              condition: good
              is_assigned: true
            - id: VDB-HW-31234
              device_type: headset
              device_model: Jabra Evolve2 40
              purchase_date: "2022-07-15T00:00:00Z"
              warehouse_location: austin
              condition: poor
              is_assigned: true
            - id: VDB-HW-36291
              device_type: headset
              device_model: Logitech H650e
              purchase_date: "2024-08-15T00:00:00Z"
              warehouse_location: austin
              condition: new
              is_assigned: false
            - id: VDB-HW-48173
              device_type: headset
              device_model: Logitech Zone Wired 2
              purchase_date: "2024-09-01T00:00:00Z"
              warehouse_location: austin
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-28463917
              asset_id: VDB-HW-62847
              employee_id: WD-415738
              assigned_at: "2022-07-05T10:00:00Z"
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-51739482
              asset_id: VDB-HW-31234
              employee_id: WD-415738
              assigned_at: "2022-07-20T10:00:00Z"
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
                $filter: "email eq 'rachel.cooper@vdb.com'"
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
        rubrics_yesno:
          - "The replacement headset (Logitech H650e, VDB-HW-36291) was assigned from existing inventory stock at the Austin office — no procurement order was created. IF the agent describes how the replacement headset was sourced in the final message, does it correctly indicate it was assigned from existing stock rather than ordered through procurement? (Yes = correctly indicates stock assignment or does not describe sourcing method, No = states the headset was 'ordered' implying a procurement order was placed)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2021-11-01T00:00:00Z"
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
              created_at: "2024-02-15T00:00:00Z"
              updated_at: "2024-02-15T00:00:00Z"
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-10456
              device_type: laptop_standard
              device_model: Dell Latitude 5440
              purchase_date: "2022-01-15T00:00:00Z"
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-36291
              device_type: laptop_standard
              device_model: Lenovo ThinkBook 14+
              purchase_date: "2024-09-10T00:00:00Z"
              warehouse_location: sf
              condition: new
              is_assigned: false
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-62184537
              asset_id: VDB-HW-10456
              employee_id: WD-618234
              assigned_at: "2022-02-01T10:00:00Z"
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
                $filter: "email eq 'ryan.cooper@vdb.com'"
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
        rubrics_yesno:
          - "The agent's policy states: 'There is no need in referencing Zendesk tickets, internal tools, URLs to articles, etc.' Does the agent's final message avoid referencing Zendesk ticket IDs or numbers? (Yes = no ticket ID/number referenced or topic not mentioned, No = a Zendesk ticket ID or number is referenced)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2025-09-01T00:00:00Z"
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
              start_date: "2020-08-15T00:00:00Z"
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
              created_at: "2025-09-01T00:00:00Z"
              updated_at: "2025-09-01T00:00:00Z"
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
                $filter: "email eq 'natalie.brooks@vdb.com'"
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
                details: "Monitor provision request for HR Coordinator. Business justification: I need a monitor to efficiently perform my HR Coordinator duties — reviewing employee records and documents on a larger screen improves my productivity significantly."
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
        rubrics_yesno:
          - "Policy states: 'There is no need in referencing Zendesk tickets, internal tools, URLs to articles, etc.' Does the agent's final message avoid mentioning a Zendesk ticket ID (a numeric ticket identifier such as 'ID 6' or 'ticket 6')? (Yes = no ticket ID mentioned or topic not discussed, No = a specific ticket ID number is mentioned)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2019-06-01T00:00:00Z"
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
              start_date: "2018-09-10T00:00:00Z"
              manager_id: WD-294817
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_hardware_assets:
            - id: VDB-HW-20789
              device_type: monitor
              device_model: Dell UltraSharp 27 U2723DE
              purchase_date: "2023-05-15T00:00:00Z"
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-20790
              device_type: monitor
              device_model: Dell UltraSharp 27 U2723DE
              purchase_date: "2023-05-15T00:00:00Z"
              warehouse_location: sf
              condition: good
              is_assigned: true
            - id: VDB-HW-20788
              device_type: laptop_standard
              device_model: Dell Latitude 5530
              purchase_date: "2022-03-10T00:00:00Z"
              warehouse_location: sf
              condition: good
              is_assigned: true
          sandbox_neobank_support_main_models_asset_assignments:
            - id: ASN-20789415
              asset_id: VDB-HW-20789
              employee_id: WD-415738
              assigned_at: "2023-06-01T10:00:00Z"
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-20790415
              asset_id: VDB-HW-20790
              employee_id: WD-415738
              assigned_at: "2023-06-01T10:00:00Z"
              assigned_by: system
              is_active: true
              returned_at: null
            - id: ASN-20788415
              asset_id: VDB-HW-20788
              employee_id: WD-415738
              assigned_at: "2022-04-01T10:00:00Z"
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
              created_at: "2024-02-15T00:00:00Z"
              updated_at: "2024-02-15T00:00:00Z"
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
                $filter: "email eq 'derek.wilson@vdb.com'"
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
                  description: "Employee Derek Wilson requests a third monitor for their SF office setup. Currently has two monitors assigned (VDB-HW-20789, VDB-HW-20790). Business justification: managing multiple sales dashboards and CRM windows simultaneously. Manager approval required."
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
                details: "Third monitor request for Sales Director Derek Wilson. Currently has two monitors (VDB-HW-20789, VDB-HW-20790). Business justification: managing multiple sales dashboards and CRM windows simultaneously."
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
                  description: "Employee Derek Wilson requests a third monitor for their SF office setup. Currently has two monitors assigned (VDB-HW-20789, VDB-HW-20790). Business justification: managing multiple sales dashboards and CRM windows simultaneously. Manager approval required."
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: I need a third monitor - managing multiple sales dashboards and CRM windows simultaneously.
                  approver_id: WD-637284
                  approval_request_ids: APR-00000007
        rubrics_yesno:
          - "Policy states: 'There is no need in referencing Zendesk tickets, internal tools, URLs to articles, etc.' Does the agent's final message avoid referencing internal system identifiers such as approval request IDs (e.g., 'APR-00000007'), Zendesk ticket IDs, or similar internal references? (Yes = no internal system identifiers mentioned, No = one or more internal system identifiers are referenced)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2020-09-01T00:00:00Z"
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
              created_at: "2024-02-15T00:00:00Z"
              updated_at: "2024-02-15T00:00:00Z"
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
              granted_at: "2020-09-01T09:00:00Z"
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-51863927
              employee_id: WD-637291
              app_name: Jira
              access_level: read_write
              granted_at: "2020-09-01T09:05:00Z"
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-67284931
              employee_id: WD-637291
              app_name: GitHub
              access_level: read_write
              granted_at: "2020-09-15T10:00:00Z"
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-42918573
              employee_id: WD-637291
              group_name: engineers
              added_at: "2020-09-01T09:10:00Z"
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
                $filter: "email eq 'daniel.park@vdb.com'"
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
        rubrics_yesno:
          - IF the agent provides specific tool examples for Sensitivity Group 2 (Internal Tools) in the final message, does it correctly identify them from among the actual Group 2 tools — Salesforce CRM (user), Tableau (viewer), GitHub (read_only), and Quantivate (user) — rather than listing Sensitivity Group 1 (Public) tools such as Slack, Confluence, Zoom, Jira, Workday HRIS (standard), or VPN (standard_employee)? (Yes = correct Group 2 examples listed or no specific tool examples given for Group 2, No = lists Group 1/Public tools as Group 2 examples)
          - "Policy states that BI dashboards have their own distinct approval structure: 'confidential' dashboards require Manager approval, 'financial_data' dashboards require Head of Finance & Accounting approval, and 'compliance_restricted' dashboards require Head of Compliance approval — these rules are separate from the Sensitivity Group 1–5 tool access matrix. Does the agent's final message avoid claiming that BI dashboards follow the same approval rules as the Sensitivity Group 1–5 tool access matrix? (Yes = does not make such a claim or does not mention BI dashboards, No = incorrectly claims BI dashboards follow the same group-based approval rules as tools)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2023-09-01T00:00:00Z"
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
              created_at: "2024-09-01T00:00:00Z"
              updated_at: "2024-09-01T00:00:00Z"
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles:
            - id: 1
              url: "https://vdb.zendesk.com/api/v2/help_center/articles/1.json"
              html_url: "https://vdb.zendesk.com/hc/en-us/articles/1"
              title: Approved Software List
              body: "<p>The following software applications are approved for use at VDB:</p><ul><li>Slack</li><li>Jira</li><li>Confluence</li><li>Figma</li><li>GitHub</li><li>Zoom</li><li>Tableau</li><li>Salesforce</li><li>Workday</li><li>Snowflake</li><li>Splunk</li><li>Okta</li></ul><p>If you need access to or a license for any of these applications, please submit a request to IT Support.</p>"
              snippet: "The following software applications are approved for use at VDB: Slack, Jira, Confluence, Figma, GitHub, Zoom, Tableau, Salesforce, Workday, Snowflake, Splunk, Okta."
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
              created_at: "2024-01-15T10:00:00Z"
              updated_at: "2024-06-01T10:00:00Z"
              edited_at: "2024-06-01T10:00:00Z"
              result_type: article
          zendesk_ticket_status_violations: []
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-41738295
              employee_id: WD-617384
              app_name: Slack
              access_level: read_write
              granted_at: "2023-09-01T10:00:00Z"
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
            - id: OAA-52864713
              employee_id: WD-617384
              app_name: Jira
              access_level: read_write
              granted_at: "2023-09-01T10:05:00Z"
              granted_by: system
              is_active: true
              revoked_at: null
              is_temporary: false
              expires_at: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-83517294
              employee_id: WD-617384
              group_name: engineers
              added_at: "2023-09-01T10:10:00Z"
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
                $filter: "email eq 'nathan.parker@vdb.com'"
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
        rubrics_yesno:
          - "Policy states: 'For software requiring licenses (Tableau Creator, Figma, specialized tools named by requester).' Figma is explicitly listed as software requiring a license. Does the agent's final message avoid claiming that Figma requires no special approval or license? (Yes = does not make such a claim, or correctly notes the license requirement, No = claims Figma needs no special approval or license)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2023-02-20T00:00:00Z"
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
              start_date: "2020-08-10T00:00:00Z"
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
              created_at: "2024-04-10T00:00:00Z"
              updated_at: "2024-04-10T00:00:00Z"
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
                $filter: "email eq 'rachel.nguyen@vdb.com'"
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Snowflake Depersonalized Access Request - Rachel Nguyen
                  description: "Employee Rachel Nguyen (Marketing Specialist, marketing_growth) requests read-only access to Snowflake data warehouse analytics_mart database. Business justification: Need to analyze customer acquisition data for the new campaign."
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
                details: "Request for Snowflake depersonalized analyst access for Rachel Nguyen (Marketing Specialist). Business justification: Need to analyze customer acquisition data for the new campaign."
                urgency: standard
                ticket_id: '6'
            - tool: approval_api_create_request
              parameters:
                request_type: access_request
                requester_email: rachel.nguyen@vdb.com
                approver_email: amanda.lee@vdb.com
                details: "Request for Snowflake depersonalized analyst access for Rachel Nguyen (Marketing Specialist). Requires IT Security approval per sensitivity group 3 policy. Business justification: Need to analyze customer acquisition data for the new campaign."
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
                  description: "Employee Rachel Nguyen (Marketing Specialist, marketing_growth) requests read-only access to Snowflake data warehouse analytics_mart database. Business justification: Need to analyze customer acquisition data for the new campaign."
                  owner: it_support
                  approval_required: 'yes'
                  approval_status: pending
                  business_justification: null
                  approver_id: WD-417283,WD-753918
                  approval_request_ids: APR-00000007,APR-00000008
                  access_expiry_date: null
        rubrics_yesno:
          - "Policy states: 'There is no need in referencing Zendesk tickets, internal tools, URLs to articles, etc.' Does the agent's final message avoid referencing a Zendesk ticket ID (e.g., 'ticket #6', 'Ticket ID 6')? (Yes = no ticket ID referenced, No = a ticket ID is referenced)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2020-08-15T00:00:00Z"
              manager_id: WD-681453
              employment_status: active
              is_contractor: false
              remote_delivery_address: null
              contract_end_date: null
          sandbox_neobank_support_main_models_okta_group_membership:
            - id: OGM-48291635
              employee_id: WD-637284
              group_name: bi_product_analytics
              added_at: "2020-09-01T10:00:00Z"
              added_by: system
              is_active: true
            - id: OGM-59372814
              employee_id: WD-637284
              group_name: product_team
              added_at: "2020-08-20T09:00:00Z"
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
              created_at: "2024-04-10T00:00:00Z"
              updated_at: "2024-04-10T00:00:00Z"
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
                $filter: "email eq 'daniel.harris@vdb.com'"
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
                details: "Request for access to Marketing BI dashboards (bi_marketing_viewers). Business justification: Need to see revenue metrics for product roadmap planning."
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
        rubrics_yesno:
          - "IF the agent's final message states the role or title of the approver (Sarah Jones), does it correctly identify her as 'Engineering Manager' rather than an incorrect title such as 'Director'? (Yes = correctly states 'Engineering Manager', or her role/title is not mentioned, No = states an incorrect role/title)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2025-08-01T00:00:00Z"
              manager_id: WD-681453
              employment_status: active
              is_contractor: true
              remote_delivery_address: null
              contract_end_date: "2026-07-31T00:00:00Z"
          zendesk_users:
            - id: '6'
              name: Ryan Patel
              email: ryan.patel@vdb.com
              role: end-user
              organization_id: '1'
              phone: +1-415-637-2914
              verified: true
              active: true
              created_at: "2025-07-20T00:00:00Z"
              updated_at: "2025-07-20T00:00:00Z"
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
                $filter: "email eq 'ryan.patel@vdb.com'"
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
                  access_expiry_date: "2026-07-31T00:00:00Z"
        rubrics_yesno:
          - "Policy states: 'There is no need in referencing Zendesk tickets, internal tools, URLs to articles, etc.' Does the agent's final message avoid mentioning Zendesk ticket numbers (e.g., 'Ticket #6')? (Yes = no ticket numbers mentioned, No = ticket number referenced)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2023-11-01T00:00:00Z"
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
              created_at: "2024-02-10T00:00:00Z"
              updated_at: "2024-02-10T00:00:00Z"
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
                $filter: "email eq 'daniel.parker@vdb.com'"
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
        rubrics_yesno:
          - "Policy states: 'There is no need in referencing Zendesk tickets, internal tools, URLs to articles, etc.' Does the agent's final message avoid referencing a Zendesk ticket ID? (Yes = no ticket ID referenced, No = a ticket ID is referenced)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


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
              start_date: "2025-09-18T00:00:00Z"
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
              created_at: "2025-09-18T00:00:00Z"
              updated_at: "2025-09-18T00:00:00Z"
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
              added_at: "2025-09-18T09:00:00Z"
              added_by: system
              is_active: true
          sandbox_neobank_support_main_models_okta_app_access:
            - id: OAA-43729185
              employee_id: WD-437295
              app_name: Slack
              access_level: read_write
              granted_at: "2025-09-18T09:00:00Z"
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
                $filter: "email eq 'nathan.perry@vdb.com'"
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
        rubrics_yesno:
          - "IF the agent's final message describes what was done for the 1Password request, does it avoid claiming that the software was already installed on the user's machine? The actual action performed was only a license allocation (allocation ID: LAL-00000009), not a software installation. (Yes = does not claim installation was completed on the machine, or not mentioned; No = incorrectly claims the software has been installed on the machine)"
          - "The agent's policy states: 'There is no need in referencing Zendesk tickets, internal tools, URLs to articles, etc.' Does the agent's final message avoid sharing internal system identifiers such as license allocation IDs (e.g., 'LAL-00000009')? (Yes = does not share internal system identifiers; No = shares internal system identifiers)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)
