# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from thinkingbox.common import Judge, TestContext

"""!
scenario: sandbox_consulting
"""
SERVER_NAME = "sandbox_consulting"


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
        score_result = judge.custom_rubric_score(
            message=agent_response, rubric=criteria_text, numerical_score=reward
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

    assert judge.numerical_threshold(
        score_list
    ), f"Rubrics threshold not met: {total_score}/{total_possible} < 70%"


def test_csa_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com), I need VPN access to Meridian Consulting client systems for my current engagement (ENG-1234567). My background check is complete, NDA is signed, and I've finished the required training courses (Ethics & Code of Conduct and Security Awareness). Can you open a ticket for this request, and let me know if it will be pending the manager's approval?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record:
            - clearance_level: standard
              employee_email: sarah.martinez@msg.com
              status: cleared
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-2847391
              employee_email: sarah.martinez@msg.com
              status: signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: '2025-08-04T20:00:00'
              id: CRS-1001234
              max_seats: 5
              prerequisites: []
              start_date: '2025-08-01T00:00:00'
              title: Ethics & Code of Conduct
              training_category: must_have
            - cost: 0
              end_date: '2025-08-14T20:00:00'
              id: CRS-1001235
              max_seats: 7
              prerequisites: []
              start_date: '2025-08-11T00:00:00'
              title: Security Awareness
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2025-08-04T20:00:00'
              course_id: CRS-1001234
              employee_email: sarah.martinez@msg.com
              id: ENR-5003011
            - completion_date: '2025-08-14T20:00:00'
              course_id: CRS-1001235
              employee_email: sarah.martinez@msg.com
              id: ENR-5003056
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2026-01-31T00:00:00'
              engagement_code: ENG-1234567
              id: ASG-2847391
              senior_manager_email: david.thompson@msg.com
              start_date: '2024-09-01T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2026-01-31T00:00:00'
              engagement_code: ENG-1234567
              senior_manager_email: david.thompson@msg.com
              start_date: '2024-09-01T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-2847391
              name: Meridian Consulting
              required_training_courses:
                - CRS-1001234
                - CRS-1001235
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-2847391
              end_date: '2026-01-31T00:00:00'
              engagement_code: ENG-1234567
              engagement_manager_email: david.thompson@msg.com
              start_date: '2024-09-01T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2024-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: david.thompson@msg.com
              level: Senior Manager
              manager_email: richard.williams@msg.com
              name: David Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2020-05-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-03-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  approval_required: 'yes'
                  approver_id: david.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: CLT-2847391
                  course_id: null
                  description: Meridian Consulting VPN access for Sarah Martinez
                  device_type: null
                  due_at: null
                  engagement_code: ENG-1234567
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: Meridian Consulting VPN access for Sarah Martinez
                  tags:
                    - client_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: null
                approver_email: david.thompson@msg.com
                engagement_code: ENG-1234567
                request_type: client_access
                requester_email: sarah.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Approval request to provision Meridian Consulting VPN access for Sarah Martinez is created. Pending engagement manager decision.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_csa_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi Support Team,

        I’m writing you about my **existing access request from last week** for **RetailMax**—it’s still **Pending**. Engagement has started and I cannot access the client system which is blocking my work. I need full access to RetailMax client systems to work for my current engagement: **ENG-3456789**. I’ve already **signed the RetailMax NDA** and **completed the required RetailMax security training**. I don’t believe my **clearance/background check has been initiated yet**—please let me know what you need from me to get that started so the request can move forward.

        Thanks,

        Sarah Martinez
    user_context: |


        1. **If asked for the engagement manager / approver**“The engagement manager is **Richard Williams (richard.williams@msg.com)**.”
        2. **If asked to confirm whether there’s an existing ticket ID**“Yes—my prior request is **Ticket TCK-584739**, created about a week ago. It’s pending for clearance.”
        3. **If asked what exactly I need access to**“Access to RetailMax client systems needed for inventory optimization work. I’m fine with **standard contributor access**—I do **not** need admin privileges.”
        4. **If asked whether NDA and training are complete**“Yes. NDA is signed and I completed the RetailMax security training.”
        5. **If asked about clearance/background check status**“I haven’t started it yet. I’m available to provide whatever information is required to initiate it.”
        6. **If asked when access is needed / urgency**“I’m scheduled to begin active work on this next week, so I’d like to initiate any prerequisites as soon as possible.”
        7. **If asked for personal details that would normally be in Workday (office, manager)**“I’m based in **Chicago**. My manager is **Michael Chen (michael.chen@msg.com)**.”
        8. **If the agent suggests creating a new ticket**“Please keep everything on the existing ticket **TCK-584739** so we avoid duplicates.”
        9. **If the agent asks for screenshots, attachments, or external documents**“I don’t have additional documents to attach right now—please proceed using internal records for NDA/training, and let me know if you need anything specific from me.”
        10. **If the agent asks for approval routing before clearance**“I’m happy to provide the engagement manager’s details, but I understand clearance needs to be initiated first—please start that step.



        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-2847391
              employee_email: sarah.martinez@msg.com
              status: signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: '2025-09-20T00:00:00'
              id: CRS-8472639
              max_seats: 50
              prerequisites: []
              start_date: '2025-09-10T00:00:00'
              title: RetailMax Security Training
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2025-09-15T00:00:00'
              course_id: CRS-8472639
              employee_email: sarah.martinez@msg.com
              id: ENR-9384751
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-3456789
              id: ASG-8472951
              senior_manager_email: richard.williams@msg.com
              start_date: '2025-09-05T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-3456789
              senior_manager_email: richard.williams@msg.com
              start_date: '2025-09-05T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-2847391
              name: RetailMax
              required_training_courses:
                - CRS-8472639
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-2847391
              end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-3456789
              engagement_manager_email: richard.williams@msg.com
              start_date: '2025-09-05T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Senior Consultant
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2023-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: full_access
              approval_required: 'no'
              assignee_id: '157'
              client_id: CLT-2847391
              created_at: '2025-09-25T13:00:00Z'
              description: 'Requester: Sarah Martinez (Senior Consultant)

                Client: RetailMax (CLT-2847391)

                Engagement: ENG-3456789 (active; requester assigned)

                Request: Access to RetailMax client systems for inventory optimization work.

                Prereqs: NDA signed; client training completed. Clearance/background check has NOT been started.

                Status reason: Pending - waiting for clearance/background check before approvals and provisioning.'
              due_at: null
              engagement_code: ENG-3456789
              id: '6'
              organization_id: '1'
              priority: normal
              requester_id: '28473910'
              status: pending
              subject: RetailMax client system access - Inventory optimization (ENG-3456789)
              tags:
                - client_access
              type: task
              updated_at: '2025-09-25T13:00:00Z'
          zendesk_users:
            - active: true
              created_at: '2025-09-24T13:00:00Z'
              email: sarah.martinez@msg.com
              id: '28473910'
              name: Sarah Martinez
              organization_id: '1'
              phone: +1 (347) 482-7319
              role: end-user
              updated_at: '2025-09-24T13:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: initiate
                clearance_level: standard
                email: sarah.martinez@msg.com
              tool: background_check_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  status: pending
                  subject: null
                  tags: null
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_csa_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is David Martinez, [david.martinez@msg.com](mailto:david.martinez@msg.com). I need full access to MedHealth Systems client systems. My valid engagement code is ENG-4567890. I am still waiting on my clearance to complete. Can you grant me full access to the client system today? I can understand if I have to wait for my clearance to complete.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record:
            - clearance_level: high_security
              employee_email: david.martinez@msg.com
              status: in_progress
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-9384751
              employee_email: david.martinez@msg.com
              status: not_signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: '2025-10-04T17:00:00Z'
              id: CRS-7841236
              max_seats: 15
              prerequisites: []
              start_date: '2025-10-04T09:00:00Z'
              title: HIPAA Compliance Training
              training_category: must_have
            - cost: 0
              end_date: '2025-10-03T17:00:00Z'
              id: CRS-7841237
              max_seats: 20
              prerequisites: []
              start_date: '2025-10-03T09:00:00Z'
              title: Advanced Data Analytics with Python
              training_category: must_have
            - cost: 0
              end_date: '2025-10-02T17:00:00Z'
              id: CRS-7841238
              max_seats: 15
              prerequisites: []
              start_date: '2025-10-02T09:00:00Z'
              title: Cloud Architecture Certification Prep
              training_category: must_have
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-4567890
              id: ASN-7294851
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-4567890
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: high_security
              id: CLT-9384751
              name: MedHealth Systems
              required_training_courses:
                - CRS-7841236
                - CRS-7841237
                - CRS-7841238
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-9384751
              end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-4567890
              engagement_manager_email: jennifer.wilson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: completed
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: CLT-9384751
                  course_id: null
                  description: David Martinez (Manager) requests access to MedHealth Systems (high-security client, engagement code ENG-4567890). High-security background check in progress, NDA not signed, HIPAA training not completed.
                  device_type: null
                  due_at: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: Request for MedHealth Systems client system access
                  tags:
                    - client_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: full_access
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-4567890
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_csa_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need access to the TechCorp client development environment. I am David Martinez and my email is [david.martinez@msg.com](mailto:david.martinez@msg.com). My engagement code is ENG-5678901. I completed my background check and I have finished all required training. Please let me know what else is needed.
    user_context: |
        Data available to you:

        "level": "Senior Manager",

        "office_location": "Chicago",

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record:
            - clearance_level: standard
              employee_email: david.martinez@msg.com
              status: cleared
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-4829573
              employee_email: david.martinez@msg.com
              status: not_signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: null
              id: CRS-8472951
              max_seats: null
              prerequisites: []
              start_date: null
              title: TechCorp Security Fundamentals
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2025-09-15T17:00:00Z'
              course_id: CRS-8472951
              employee_email: david.martinez@msg.com
              id: ENR-5678901
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-5678901
              id: ASN-7394821
              senior_manager_email: sarah.johnson@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-5678901
              senior_manager_email: sarah.johnson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829573
              name: TechCorp
              required_training_courses:
                - CRS-8472951
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829573
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-5678901
              engagement_manager_email: sarah.johnson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Manager
              manager_email: jennifer.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: robert.chen@msg.com
              start_date: '2022-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                engagement_code: ENG-5678901
              tool: salesforce_crm_get_engagement
            - parameters:
                action: validate_engagement_code
                email: david.martinez@msg.com
                engagement_code: ENG-5678901
              tool: mavenlink_api
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.johnson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: CLT-4829573
                  course_id: null
                  description: David Martinez requests access to TechCorp client development environment. Engagement code ENG-5678901. Background check and training complete. NDA not signed; NDA sent for signature.
                  device_type: null
                  due_at: null
                  engagement_code: ENG-5678901
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: Request for TechCorp client development environment access
                  tags:
                    - client_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: send_for_signature
                client_id: CLT-4829573
                email: david.martinez@msg.com
              tool: nda_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_csa_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is David Martinez I am a partner, [david.martinez@msg.com](mailto:david.martinez@msg.com). I urgently need full access to the high-security GlobalBank's client trading systems ( GlobalBank Trading Systems) for my strategic advisory engagement (ENG-6789012). All my required training, NDA, and background checks are complete, and both my engagement manager and the Security Director with the following emails have already approved: [sarah.thompson@msg.com](mailto:sarah.thompson@msg.com),[security.director@msg.com](mailto:security.director@msg.com). Can you complete this request today? It is urgent.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: null
              approver_email: sarah.thompson@msg.com
              engagement_code: ENG-6789012
              id: APR-1060203
              request_type: client_access
              requester_email: david.martinez@msg.com
              status: approved
            - amount: null
              approver_email: security.director@msg.com
              engagement_code: ENG-6789012
              id: APR-1100703
              request_type: client_access
              requester_email: david.martinez@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record:
            - clearance_level: high_security
              employee_email: david.martinez@msg.com
              status: cleared
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-2847391
              employee_email: david.martinez@msg.com
              status: signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 500
              end_date: '2025-08-17T17:00:00Z'
              id: CRS-1020202
              max_seats: 5
              prerequisites: []
              start_date: '2025-08-17T09:00:00Z'
              title: SOC 2
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2025-08-17T18:00:00Z'
              course_id: CRS-1020202
              employee_email: david.martinez@msg.com
              id: ENR-1205001
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-6789012
              id: ASN-4729183
              senior_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-6789012
              senior_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: high_security
              id: CLT-2847391
              name: GlobalBank Trading Systems
              required_training_courses:
                - CRS-1020202
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-2847391
              end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-6789012
              engagement_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Partner
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: New York
              onboarding_phase: null
              partner_email: david.martinez@msg.com
              start_date: '2019-08-12T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Partner
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: New York
              onboarding_phase: null
              partner_email: sarah.thompson@msg.com
              start_date: '2017-03-20T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-03-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: full_access
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: CLT-2847391
                  course_id: null
                  description: Partner David Martinez requests access to GlobalBank Trading Systems for strategic advisory engagement ENG-6789012. All required SOC 2 training, NDA, and high-security background check are complete. Engagement manager and Security Director have approved.
                  device_type: null
                  due_at: null
                  engagement_code: ENG-6789012
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: urgent
                  requester_id: '8'
                  status: open
                  subject: 'Client system access request: GlobalBank Trading Systems (ENG-6789012)'
                  tags:
                    - client_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                access_type: full_access
                action: provision_client_system
                client_id: CLT-2847391
                email: david.martinez@msg.com
                system_name: GlobalBank Trading Systems
              tool: client_access_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com,security.director@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_csa_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com), I need access to the InsureCo client claims system for my active engagement (ENG-7890123). My background check and NDA are complete, and I have finished the Ethics & Code of Conduct course. Can you grant me full access?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record:
            - clearance_level: standard
              employee_email: sarah.martinez@msg.com
              status: cleared
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-4829573
              employee_email: sarah.martinez@msg.com
              status: signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: null
              id: CRS-1001234
              max_seats: null
              prerequisites: []
              start_date: null
              title: Ethics & Code of Conduct
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001235
              max_seats: null
              prerequisites: []
              start_date: null
              title: Security Awareness
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001236
              max_seats: null
              prerequisites: []
              start_date: null
              title: Data Handling
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2023-03-22T16:30:00Z'
              course_id: CRS-1001234
              employee_email: sarah.martinez@msg.com
              id: ENR-5003001
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-7890123
              id: ASG-2847391
              senior_manager_email: jennifer.adams@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-7890123
              senior_manager_email: jennifer.adams@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829573
              name: InsureCo
              required_training_courses:
                - CRS-1001234
                - CRS-1001235
                - CRS-1001236
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829573
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-7890123
              engagement_manager_email: jennifer.adams@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.wilson@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: jennifer.adams@msg.com
              level: Senior Manager
              manager_email: david.wilson@msg.com
              name: Jennifer Adams
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.wilson@msg.com
              start_date: '2020-05-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: full_access
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: CLT-4829573
                  course_id: null
                  description: Requesting access for engagement ENG-7890123. Background check and NDA complete. Ethics & Code of Conduct course completed. Missing Security Awareness and Data Handling trainings.
                  device_type: null
                  due_at: null
                  engagement_code: ENG-7890123
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: 'Access request: InsureCo client claims system'
                  tags:
                    - client_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: enroll_employee
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-1001235
                email: sarah.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                action: enroll_employee
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-1001236
                email: sarah.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: CLT-4829573
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-7890123
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_csa_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am David Martinez, my email address is [david.martinez@msg.com](mailto:david.martinez@msg.com), my engagement code is ENG-8901234. Please I want you to help me get access to EnergyPlus Solutions client (CLT-4829571) systems for sustainability reporting.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements:
            - end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-8901234
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-09-01T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829571
              name: EnergyPlus Solutions
              required_training_courses:
                - CRS-0078901
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829571
              end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-8901234
              engagement_manager_email: jennifer.wilson@msg.com
              start_date: '2025-09-01T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Consultant
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2021-08-10T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: jennifer.wilson@msg.com
              level: Manager
              manager_email: robert.davis@msg.com
              name: Jennifer Wilson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2020-05-18T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: robert.davis@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Robert Davis
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-02-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: (813) 492-7584
              role: end-user
              updated_at: '2023-03-15T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: CLT-4829571
                  course_id: null
                  description: 'David Martinez requests access to EnergyPlus Solutions client systems for sustainability reporting. Engagement code provided: ENG-8901234.'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Request for EnergyPlus Solutions client system access (ENG-8901234)
                  tags:
                    - client_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Request denied: You are not assigned to the active engagement (ENG-8901234) for EnergyPlus Solutions. Access cannot be granted unless you are assigned to the engagement. Please contact your engagement manager if you believe this is an error.'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_csa_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi Internal Support Team,

        I’m **David Martinez**, a **Senior Consultant** at Meridian Strategy Group. I need access to **DefenseContractor’s secure client systems** for my current engagement.

        My engagement code is **ENG-9012345**, and I’m actively assigned to this engagement. I’ve already **signed the required NDA** and **completed the mandatory client security training**. I understand this is a **high-security government client** and that a **high-security background clearance** is required before access can be granted.

        Please let me know the next steps and initiate whatever is needed to move this request forward.

        Thank you.
    user_context: |
        - Rules:
        - - Do not change your goal or switch topics.
        - - Do not invent or provide information that is not present in the user’s messages.
        - - If the user asks for the same information again, provide it consistently.
        - - Remain focused, clear, and patient throughout the conversation.
        -
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record:
            - clearance_level: high_security
              employee_email: david.martinez@msg.com
              status: not_initiated
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-4829371
              employee_email: david.martinez@msg.com
              status: signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: null
              id: CRS-8472951
              max_seats: null
              prerequisites: []
              start_date: null
              title: DefenseContractor Security Awareness
              training_category: must_have
          degreed_training_enrollments:
            - course_id: CRS-8472951
              employee_email: david.martinez@msg.com
              id: ENR-63918427
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-9012345
              id: ASN-7394852
              senior_manager_email: robert.wilson@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-9012345
              senior_manager_email: robert.wilson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: high_security
              id: CLT-4829371
              name: DefenseContractor
              required_training_courses:
                - CRS-8472951
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829371
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-9012345
              engagement_manager_email: jennifer.adams@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: robert.wilson@msg.com
              email: david.martinez@msg.com
              level: Senior Consultant
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: New York
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '847295'
              name: David Martinez
              organization_id: null
              phone: +1-212-438-9076
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                engagement_code: ENG-9012345
              tool: salesforce_crm_get_engagement
            - parameters:
                email: david.martinez@msg.com
                engagement_code: ENG-9012345
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                access_type: null
                action: check_client_requirements
                client_id: CLT-4829371
                email: david.martinez@msg.com
                system_name: null
              tool: client_access_api
            - parameters:
                access_type: null
                action: get_employee_prerequisites
                client_id: CLT-4829371
                email: david.martinez@msg.com
                system_name: null
              tool: client_access_api
            - parameters:
                action: check_certification_status
                category: null
                certification_name: DefenseContractor Security Awareness
                client_id: null
                course_id: null
                email: david.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                action: initiate
                clearance_level: high_security
                email: david.martinez@msg.com
              tool: background_check_api
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Senior Consultant requesting access to DefenseContractor high-security client systems for active engagement ENG-9012345.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '847295'
                  status: open
                  subject: Request for DefenseContractor client system access (ENG-9012345)
                  tags:
                    - client_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: jennifer.adams@msg.com,security.director@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: CLT-4829371
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-9012345
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_csa_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I’m requesting access to the LogiTrans client logistics platform. I’m a Manager assigned to the active engagement ENG-0123456. I’ve completed the background check, signed the NDA, and finished all required client trainings.

        My engagement manager is currently on leave, but the designated backup approver has already approved this access. Could you please help provision my access?
    user_context: |
        Data available to you:

        "email": "david.martinez@msg.com",

        "name": "David Martinez",

        "level": "Manager",

        "office_location": "Chicago",

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: null
              approver_email: robert.davis@msg.com
              engagement_code: ENG-0123456
              id: APR-1000517
              request_type: client_access
              requester_email: david.martinez@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record:
            - clearance_level: standard
              employee_email: david.martinez@msg.com
              status: cleared
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-0847293
              employee_email: david.martinez@msg.com
              status: signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments:
            - completion_date: '2025-09-15T00:00:00Z'
              course_id: CRS-0847291
              employee_email: david.martinez@msg.com
              id: ENR-1041352
            - completion_date: '2025-09-20T00:00:00Z'
              course_id: CRS-0847292
              employee_email: david.martinez@msg.com
              id: ENR-1052431
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-0123456
              id: ASG-0847291
              senior_manager_email: jennifer.wilson@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-0123456
              senior_manager_email: jennifer.wilson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-0847293
              name: LogiTrans Solutions
              required_training_courses:
                - CRS-0847291
                - CRS-0847292
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-0847293
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-0123456
              engagement_manager_email: jennifer.wilson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: on_leave
              backup_approver_email: robert.davis@msg.com
              email: jennifer.wilson@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Jennifer Wilson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2021-08-10T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: robert.davis@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Robert Davis
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2020-11-05T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: '1'
              phone: +1-510-2921090
              role: end-user
              updated_at: '2025-09-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                engagement_code: ENG-0123456
              tool: salesforce_crm_get_engagement
            - parameters:
                email: david.martinez@msg.com
                engagement_code: ENG-0123456
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                access_type: null
                action: check_client_requirements
                client_id: CLT-0847293
                email: null
                system_name: null
              tool: client_access_api
            - parameters:
                access_type: null
                action: get_employee_prerequisites
                client_id: CLT-0847293
                email: david.martinez@msg.com
                system_name: null
              tool: client_access_api
            - parameters:
                item:
                  access_type: full_access
                  approval_required: 'yes'
                  approver_id: robert.davis@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: CLT-0847293
                  course_id: null
                  description: System access for LogiTrans Solutions (ENG-0123456). All prerequisites and approvals complete.
                  device_type: null
                  due_at: null
                  engagement_code: ENG-0123456
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: Access to LogiTrans client logistics platform
                  tags:
                    - client_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                access_type: full_access
                action: provision_client_system
                client_id: CLT-0847293
                email: david.martinez@msg.com
                system_name: LogiTrans
              tool: client_access_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)




def test_csa_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi my name is Sarah Martinez, [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). I need access to PharmaCorp's research systems for my current engagement (ENG-2233445). My NDA is signed and I've completed all required training, but I think my background check is not final yet. Can you let me know when my access will be granted?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record:
            - clearance_level: high_security
              employee_email: sarah.martinez@msg.com
              status: in_progress
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-8472951
              employee_email: sarah.martinez@msg.com
              status: signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: '2025-08-18T08:00:00Z'
              id: CRS-1100501
              max_seats: 10
              prerequisites: []
              start_date: '2025-08-17T08:00:00Z'
              title: Pharma Training
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2025-08-17T10:00:00Z'
              course_id: CRS-1100501
              employee_email: sarah.martinez@msg.com
              id: ENR-1006001
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-2233445
              id: ASN-4729183
              senior_manager_email: john.smith@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-2233445
              senior_manager_email: john.smith@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: high_security
              id: CLT-8472951
              name: PharmaCorp
              required_training_courses:
                - CRS-1100501
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-8472951
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-2233445
              engagement_manager_email: emily.rodriguez@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2024-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: john.smith@msg.com
              level: Senior Manager
              manager_email: richard.williams@msg.com
              name: John Smith
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2021-03-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: full_access
              approval_required: 'no'
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: CLT-8472951
              course_id: null
              created_at: '2025-09-10T14:30:00Z'
              description: Request for access to PharmaCorp research system for engagement ENG-2233445. Employee is assigned to active engagement and requires high-security clearance. Setting ticket to pending while user obtains background check
              device_type: null
              due_at: null
              engagement_code: ENG-2233445
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '2847'
              license_pool: null
              organization_id: null
              priority: high
              requester_id: '8'
              status: pending
              subject: Client System Access Request - PharmaCorp Research System
              tags:
                - client_access
              type: task
              updated_at: '2025-09-10T14:30:00Z'
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-03-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                $filter: email eq 'sarah.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8'
                $orderby: created_at desc
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: get_status
                clearance_level: null
                email: sarah.martinez@msg.com
              tool: background_check_api
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Background check for high-security client access is still in progress (expected completion in 1 week). NDA is signed and training is complete. Access will be granted once background check is complete. Please follow up in 1 week.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_csa_013(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I’m Alyssa Grant, a Consultant at Meridian Strategy Group.

        My corporate email is [alyssa.grant@msg.com](mailto:alyssa.grant@msg.com).

        I need access to the WealthManage client portfolio systems for my current engagement (ENG-3344556); if anything is missing, please let me know and proceed with whatever step I qualify for.


    user_context: |
        User Information:

        Name: Alyssa Grant

        Corporate Email: [alyssa.grant@msg.com]()

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record:
            - clearance_level: high_security
              employee_email: alyssa.grant@msg.com
              status: cleared
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-8472951
              employee_email: alyssa.grant@msg.com
              status: not_signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: '2025-02-03T00:00:00'
              id: CRS-7841952
              max_seats: null
              prerequisites: []
              start_date: '2025-02-03T00:00:00'
              title: SOC 2 Basics
              training_category: nice_to_have
            - cost: 0
              end_date: '2025-02-10T00:00:00'
              id: CRS-6397284
              max_seats: null
              prerequisites: []
              start_date: '2025-02-10T00:00:00'
              title: WealthManage High-Security Access Training
              training_category: nice_to_have
          degreed_training_enrollments:
            - completion_date: '2025-02-04T00:00:00'
              course_id: CRS-7841952
              employee_email: alyssa.grant@msg.com
              id: ENR-6029471
            - completion_date: '2025-02-12T00:00:00'
              course_id: CRS-6397284
              employee_email: alyssa.grant@msg.com
              id: ENR-7714385
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: alyssa.grant@msg.com
              end_date: '2025-12-31T00:00:00'
              engagement_code: ENG-3344556
              id: ASN-7394821
              senior_manager_email: david.thompson@msg.com
              start_date: '2024-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-31T00:00:00'
              engagement_code: ENG-3344556
              senior_manager_email: david.thompson@msg.com
              start_date: '2024-08-01T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: high_security
              id: CLT-8472951
              name: WealthManage
              required_training_courses:
                - CRS-7841952
                - CRS-6397284
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-8472951
              end_date: '2025-12-31T00:00:00'
              engagement_code: ENG-3344556
              engagement_manager_email: brian.holloway@msg.com
              start_date: '2024-08-01T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: alyssa.grant@msg.com
              level: Consultant
              manager_email: brian.holloway@msg.com
              name: Alyssa Grant
              office_location: Chicago
              onboarding_phase: null
              partner_email: patricia.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: brian.holloway@msg.com
              level: Manager
              manager_email: patricia.chen@msg.com
              name: Brian Holloway
              office_location: Chicago
              onboarding_phase: null
              partner_email: patricia.chen@msg.com
              start_date: '2021-08-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T10:00:00Z'
              email: alyssa.grant@msg.com
              id: '847293'
              name: Alyssa Grant
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
            - active: true
              created_at: '2021-08-10T09:00:00Z'
              email: brian.holloway@msg.com
              id: '592847'
              name: Brian Holloway
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-25T11:15:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                $filter: email eq 'alyssa.grant@msg.com'
                $orderby: null
                $select: null
                $skip: 0
                $top: 1
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester.email eq 'alyssa.grant@msg.com' and (status eq 'open' or status eq 'pending' or status eq 'hold')
                $orderby: null
                $select: null
                $skip: 0
                $top: 5
                table: tickets
              tool: zendesk_get_items
            - parameters:
                engagement_code: ENG-3344556
              tool: salesforce_crm_get_engagement
            - parameters:
                email: alyssa.grant@msg.com
                engagement_code: ENG-3344556
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                action: get_status
                clearance_level: high_security
                email: alyssa.grant@msg.com
              tool: background_check_api
            - parameters:
                action: get_training_history
                category: null
                certification_name: null
                client_id: null
                course_id: null
                email: alyssa.grant@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                action: check_status
                client_id: CLT-8472951
                email: alyssa.grant@msg.com
              tool: nda_api
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Consultant requests access to WealthManage client portfolio systems for active engagement ENG-3344556.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '847293'
                  status: open
                  subject: WealthManage client system access request
                  tags:
                    - client_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: send_for_signature
                client_id: CLT-8472951
                email: alyssa.grant@msg.com
              tool: nda_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'no'
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: CLT-8472951
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-3344556
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_csa_016(x: TestContext, judge: Judge):
    """!
    query: |
        I need access to the DataServices client analytics platform. My engagement code is ENG-6677889.
    user_context: |
        Your goal to request the access to the DataServices platform by mentioning your engagement code. If asked for your email, provide [michael.rodriguez@msg.com](mailto:michael.rodriguez@msg.com). Your engagement code is ENG-6677889. You do not have other engagement codes. If any issues arise with the engagement code, clearly communicate that you do not have any other ones, accept the result and ask agent to close your case.

        Rules:

        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829573
              name: DataServices Corporation
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: michael.rodriguez@msg.com
              level: Senior Manager
              manager_email: sarah.chen@msg.com
              name: Michael Rodriguez
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.thompson@msg.com
              start_date: '2019-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.chen@msg.com
              level: Partner
              manager_email: david.thompson@msg.com
              name: Sarah Chen
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.thompson@msg.com
              start_date: '2015-08-20T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: david.thompson@msg.com
              level: Partner
              manager_email: null
              name: David Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.thompson@msg.com
              start_date: '2014-01-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2019-03-15T09:00:00Z'
              email: michael.rodriguez@msg.com
              id: '8'
              name: Michael Rodriguez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: validate_engagement_code
                email: michael.rodriguez@msg.com
                engagement_code: ENG-6677889
              tool: mavenlink_api
            - parameters:
                $filter: email eq 'michael.rodriguez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8' and (status eq 'open' or status eq 'pending' or status eq 'hold')
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: get_employee
                email: michael.rodriguez@msg.com
              tool: workday_api
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  course_id: null
                  description: Employee requests access to DataServices client analytics platform. Provided engagement code ENG-6677889 is invalid.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Access request to DataServices client analytics platform
                  tags:
                    - client_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_csa_018(x: TestContext, judge: Judge):
    """!
    query: |
        Hi support, this is Alex Rivera ([alex.rivera@msg.com](mailto:alex.rivera@msg.com)). So I reached out 5 days ago about getting access to the SecureGov federal systems and the ticket got closed, but I'm still having the same issue - can't connect to their VPN at all. The engagement is ENG-8899001. Could you take another look at this? I really need to get this sorted out.
    user_context: |
        **General rules**

        - Do not invent or provide any data that is not present in the provided context.
        - Do not change your goal or switch topics.
        - If the agent asks again for the same information, provide it again.
        - Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record:
            - clearance_level: high_security
              employee_email: alex.rivera@msg.com
              status: cleared
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-8847291
              employee_email: alex.rivera@msg.com
              status: signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: null
              id: CRS-9847201
              max_seats: null
              prerequisites: []
              start_date: null
              title: Federal Government Security Standards
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-9847202
              max_seats: null
              prerequisites: []
              start_date: null
              title: FISMA Compliance Training
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-9847203
              max_seats: null
              prerequisites: []
              start_date: null
              title: Government Data Handling Procedures
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-9847204
              max_seats: null
              prerequisites: []
              start_date: null
              title: Secure Communication Protocols
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2025-08-20T00:00:00Z'
              course_id: CRS-9847201
              employee_email: alex.rivera@msg.com
              id: ENR-9847201
            - completion_date: '2025-08-22T00:00:00Z'
              course_id: CRS-9847202
              employee_email: alex.rivera@msg.com
              id: ENR-9847202
            - completion_date: '2025-08-25T00:00:00Z'
              course_id: CRS-9847203
              employee_email: alex.rivera@msg.com
              id: ENR-9847203
            - completion_date: '2025-08-27T00:00:00Z'
              course_id: CRS-9847204
              employee_email: alex.rivera@msg.com
              id: ENR-9847204
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: alex.rivera@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-8899001
              id: ASN-5591203
              senior_manager_email: michael.chen@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-8899001
              senior_manager_email: michael.chen@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: high_security
              id: CLT-8847291
              name: SecureGov Federal Agency
              required_training_courses:
                - CRS-9847201
                - CRS-9847202
                - CRS-9847203
                - CRS-9847204
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-8847291
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-8899001
              engagement_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: alex.rivera@msg.com
              level: Analyst
              manager_email: sarah.thompson@msg.com
              name: Alex Rivera
              office_location: Chicago
              onboarding_phase: completed
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: completed
              partner_email: michael.chen@msg.com
              start_date: '2020-01-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: full_access
              approval_required: 'yes'
              approver_id: sarah.thompson@msg.com,security.director@msg.com
              assignee_id: '157'
              client_id: CLT-8847291
              created_at: '2025-09-26T09:00:00Z'
              description: Need VPN and system access to SecureGov federal systems for engagement ENG-8899001
              engagement_code: ENG-8899001
              id: '1001'
              priority: high
              requester_id: ZD-7623849
              status: solved
              subject: SecureGov Federal Systems Access
              tags:
                - client_access
              type: task
              updated_at: '2025-09-26T14:30:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T00:00:00Z'
              email: alex.rivera@msg.com
              id: ZD-7623849
              name: Alex Rivera
              organization_id: '1'
              phone: +1-312-415-2961
              role: end-user
              updated_at: '2025-09-26T10:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '1001'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                amount: null
                approver_email: sarah.thompson@msg.com
                engagement_code: ENG-8899001
                request_type: client_access
                requester_email: alex.rivera@msg.com
              tool: approval_create_request
            - parameters:
                amount: null
                approver_email: security.director@msg.com
                engagement_code: ENG-8899001
                request_type: client_access
                requester_email: alex.rivera@msg.com
              tool: approval_create_request
            - parameters:
                id: '1001'
                item:
                  access_type: full_access
                  active: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com,security.director@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: CLT-8847291
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: ENG-8899001
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: high
                  requester_id: null
                  role: null
                  status: pending
                  subject: null
                  tags:
                    - client_access
                  type: null
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am Sarah Martinez, my email address is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). I'd like viewer access to the 'MSG Templates Library' Box folder (FLD-2847391) so I can download templates for my client presentations.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders:
            - client_id: null
              confidentiality_level: public
              engagement_code: null
              folder_name: MSG Templates Library
              id: FLD-2847391
              owner_email: admin.templates@msg.com
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Consultant
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2023-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: (813) 492-7584
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_folder_details
                email: null
                folder_id: FLD-2847391
                permission_level: null
              tool: box_api
            - parameters:
                item:
                  access_type: read_only
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Sarah Martinez requests viewer access to the 'MSG Templates Library' Box folder (FLD-2847391) to download templates for client presentations.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: FLD-2847391
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Request for viewer access to MSG Templates Library (FLD-2847391)
                  tags:
                    - document_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: grant_folder_access
                email: sarah.martinez@msg.com
                folder_id: FLD-2847391
                permission_level: viewer
              tool: box_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi — I’m trying to get access to a Box folder for my work.

        My name is Avery Patel, I’m an Analyst at MSG.

        The folder is called **“Healthcare Practice Resources”** and I only need **viewer access** so I can reference the methodology documents for an upcoming project.

        Can you help me get access?
    user_context: |
        **Rules:**



        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same information, provide it again consistently.
        - Remain focused, clear, and patient.
        - Respond as the employee requesting support.
        - Only provide information that is explicitly requested by the agent.
        - Do not volunteer additional details unless asked.





        **Identity Confirmation (only if asked):**



        - Confirm your corporate email address as provided in the scenario data.
        - Confirm your employee level as listed in the scenario data.





        **Request Details (only if asked):**



        - State that the request is for document / folder access.
        - Confirm the folder name is _Healthcare Practice Resources_.
        - Confirm the folder ID is _FLD-0002001_.
        - Explain the purpose is to reference internal methodology documents.
        - Confirm the requested access level is viewer (read-only).





        **Approval & Policy Questions (only if asked):**



        - State that you have not requested manager approval.
        - Indicate that you believe approval is not required for this request.





        **Confidentiality Clarification (only if asked):**



        - Confirm the folder contains internal practice materials.
        - State that it is not client-confidential content.





        **Ticket History (only if asked):**



        - Confirm that you do not have any existing open, pending, or on-hold tickets for this request.





        **Urgency (only if asked):**



        - State that the request is not urgent.





        **Engagement Code (only if asked):**



        - State that no engagement code applies to this request.





        **Conversation Closure (only if asked):**



        - Acknowledge completion and thank the agent.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders:
            - client_id: null
              confidentiality_level: internal
              engagement_code: null
              folder_name: Healthcare Practice Resources
              id: FLD-0002001
              owner_email: owner.healthcare.practice@msg.com
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: avery.patel@msg.com
              level: Analyst
              manager_email: rachel.johns@msg.com
              name: Avery Patel
              office_location: Chicago
              onboarding_phase: null
              partner_email: abigail.cameron@msg.com
              start_date: '2024-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2024-09-15T14:30:00Z'
              description: Request for Adobe Creative Suite access has been processed and completed.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '12001'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '91002'
              status: solved
              subject: Software access request completed
              tags:
                - software_access
              type: task
              updated_at: '2024-09-16T16:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: avery.patel@msg.com
              id: '91001'
              name: Avery Patel
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-03-15T09:00:00Z'
              verified: true
            - active: true
              created_at: '2024-02-10T10:00:00Z'
              email: sarah.martinez@gmail.com
              id: '91002'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-02-10T10:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_folder_details
                email: null
                folder_id: FLD-0002001
                permission_level: null
              tool: box_api
            - parameters:
                $filter: requester_id eq '91001' and (status eq 'open' or status eq 'pending' or status eq 'hold')
                $select: id,subject,status
                $skip: 3
                $top: 10
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee requesting viewer access to internal Box folder for reference purposes
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '91001'
                  status: open
                  subject: Document access request – Healthcare Practice Resources
                  tags:
                    - document_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: grant_folder_access
                email: avery.patel@msg.com
                folder_id: FLD-0002001
                permission_level: viewer
              tool: box_api
            - parameters:
                id: '7'
                item:
                  access_type: read_only
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: FLD-0002001
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez, I requested viewer access to the 'Financial Modeling Toolkit - Restricted' Box folder (ID: FLD-8472951) for my internal project a few days ago, but haven't received access yet. Can you please update me on the status or help expedite the approval?
    user_context: |
        - Do not invent or provide any data that is not present in the provided context.
        - Do not change your goal or switch topics.
        - If the agent asks again for the same information, provide it again.
        - Remain focused, clear, and patient.
        Your email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com)
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: null
              approver_email: david.thompson@msg.com
              engagement_code: null
              id: APR-5847291
              request_type: document_access
              requester_email: sarah.martinez@msg.com
              status: pending
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders:
            - client_id: null
              confidentiality_level: confidential
              engagement_code: null
              folder_name: Financial Modeling Toolkit - Restricted
              id: FLD-8472951
              owner_email: finance.team@msg.com
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Senior Consultant
              manager_email: david.thompson@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: david.thompson@msg.com
              level: Manager
              manager_email: jennifer.chen@msg.com
              name: David Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.chen@msg.com
              start_date: '2021-08-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-28T10:15:00Z'
              description: Request for viewer access to Financial Modeling Toolkit - Restricted folder for internal project analysis work.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '47291'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: pending
              subject: Box Folder Access Request - Financial Modeling Toolkit
              tags:
                - document_access
              type: task
              updated_at: '2025-09-28T11:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '47291'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: david.thompson@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: FLD-8472951
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: null
                  status: open
                  subject: null
                  tags:
                    - document_access
                  type: task
                table: tickets
              tool: zendesk_update_item
            - parameters:
                approver_email: david.thompson@msg.com
                engagement_code: null
                request_type: document_access
                requester_email: sarah.martinez@msg.com
              tool: approval_get_status
            - parameters:
                email: david.thompson@msg.com
              tool: approver_lookup_get_contact
            - parameters:
                id: '47291'
                item:
                  access_type: read_only
                  active: null
                  approval_required: 'yes'
                  approver_id: david.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Request for viewer access to Financial Modeling Toolkit - Restricted folder for internal project analysis work.
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: FLD-8472951
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: pending
                  subject: Box Folder Access Request - Financial Modeling Toolkit
                  tags:
                    - document_access
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi my name is Alex Martinez, [alex.martinez@msg.com](mailto:alex.martinez@msg.com). I need viewer access to the 'Executive Compensation Analysis' Box folder (ID: FLD-3847291) for leadership planning work. My manager is on holiday but I talked with his replacement (jimmy.chen@msg.com) and I think he gave me the approval.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: null
              approver_email: jimmy.chen@msg.com
              engagement_code: null
              id: APR-2847391
              request_type: document_access
              requester_email: alex.martinez@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders:
            - client_id: null
              confidentiality_level: confidential
              engagement_code: null
              folder_name: Executive Compensation Analysis
              id: FLD-3847291
              owner_email: sarah.williams@msg.com
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: jimmy.chen@msg.com
              email: alex.martinez@msg.com
              level: Manager
              manager_email: john.thompson@msg.com
              name: Alex Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: sarah.williams@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: on_leave
              backup_approver_email: jimmy.chen@msg.com
              email: john.thompson@msg.com
              level: Senior Manager
              manager_email: sarah.williams@msg.com
              name: John Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: sarah.williams@msg.com
              start_date: '2019-08-12T00:00:00'
            - availability_status: available
              backup_approver_email: michael.rodriguez@msg.com
              email: jimmy.chen@msg.com
              level: Senior Manager
              manager_email: sarah.williams@msg.com
              name: Jimmy Chen
              office_location: Chicago
              onboarding_phase: null
              partner_email: sarah.williams@msg.com
              start_date: '2020-01-20T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: alex.martinez@msg.com
              id: '8'
              name: Alex Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
            - active: true
              created_at: '2019-08-12T09:00:00Z'
              email: john.thompson@msg.com
              id: '13'
              name: John Thompson
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-25T11:15:00Z'
              verified: true
            - active: true
              created_at: '2020-01-20T09:00:00Z'
              email: jimmy.chen@msg.com
              id: '27'
              name: Jimmy Chen
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-30T16:45:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: alex.martinez@msg.com
              tool: workday_api
            - parameters:
                email: john.thompson@msg.com
              tool: approver_lookup_get_contact
            - parameters:
                action: get_folder_details
                email: null
                folder_id: FLD-3847291
                permission_level: null
              tool: box_api
            - parameters:
                approver_email: null
                engagement_code: null
                request_type: document_access
                requester_email: alex.martinez@msg.com
              tool: approval_get_status
            - parameters:
                $filter: email eq 'alex.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq  '8'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  access_type: read_only
                  approval_required: 'yes'
                  approver_id: jimmy.chen@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee requested access to folder, approval granted already
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: FLD-3847291
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Document Access request
                  tags:
                    - document_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: grant_folder_access
                email: alex.martinez@msg.com
                folder_id: FLD-3847291
                permission_level: viewer
              tool: box_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I submitted a request a couple of days ago (ticket #12847) for viewer access to the 'TechCorp - Project Documents' Box folder **(ID: FLD-2847391)** for my engagement ENG-1357924. I have already signed the NDA and completed the security clearance, but I still don't have access. Can you please check on this and finalize the access?
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.

        Rules: Do not invent or provide any data that is not present in the provided context. Do not change your goal or switch topics. If the agent asks again for the same information, provide it again. Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders:
            - client_id: CLT-2847391
              confidentiality_level: client_confidential
              engagement_code: null
              folder_name: TechCorp - Project Documents
              id: FLD-2847391
              owner_email: michael.chen@msg.com
          client_access_clearance_record:
            - clearance_level: standard
              employee_email: sarah.martinez@msg.com
              status: cleared
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-2847391
              employee_email: sarah.martinez@msg.com
              status: signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-12-31T00:00:00'
              engagement_code: ENG-1357924
              id: ASG-2847391
              senior_manager_email: jennifer.williams@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-31T00:00:00'
              engagement_code: ENG-1357924
              senior_manager_email: jennifer.williams@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-2847391
              name: TechCorp
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-2847391
              end_date: '2025-12-31T00:00:00'
              engagement_code: ENG-1357924
              engagement_manager_email: michael.chen@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Consultant
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2023-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-29T13:00:00Z'
              description: 'Requesting viewer access to TechCorp - Project Documents folder for client engagement work. Engagement code: ENG-1357924'
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '12847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: open
              subject: Box folder access request - TechCorp Project Documents
              tags:
                - document_access
              type: task
              updated_at: '2025-09-29T13:00:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: grant_folder_access
                email: sarah.martinez@msg.com
                folder_id: FLD-2847391
                permission_level: viewer
              tool: box_api
            - parameters:
                id: '12847'
                item:
                  access_type: read_only
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: CLT-2847391
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-1357924
                  expense_report_id: null
                  folder_id: FLD-2847391
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need viewer access to the 'MedHealth - Strategy Documents' Box folder with id FLD-8472639. I am assigned to this active engagement ENG-3579146 and have completed my security clearance. I have requested it already one week ago. Can you please check the status of the existing ticket on this request and help me grant access?
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.

        Your corporate email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). Provide it to the agent if asked.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders:
            - client_id: CLT-4829573
              confidentiality_level: client_confidential
              engagement_code: null
              folder_name: MedHealth - Strategy Documents
              id: FLD-8472639
              owner_email: david.thompson@msg.com
          client_access_clearance_record:
            - clearance_level: standard
              employee_email: sarah.martinez@msg.com
              status: cleared
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-4829573
              employee_email: sarah.martinez@msg.com
              status: not_signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-3579146
              id: ASG-7294851
              senior_manager_email: rachel.johnson@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-3579146
              senior_manager_email: rachel.johnson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829573
              name: MedHealth Corporation
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829573
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-3579146
              engagement_manager_email: david.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2023-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: 'no'
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: CLT-4829573
              course_id: null
              created_at: '2025-09-24T10:30:00Z'
              description: Request for viewer access to Box folder 'MedHealth - Strategy Documents' (FLD-8472639) for MedHealth engagement ENG-3579146. Employee has completed security clearance but NDA signature is pending. NDA has been sent for electronic signature. Request will proceed once NDA is signed and processed in the system.
              device_type: null
              due_at: null
              engagement_code: ENG-3579146
              expense_report_id: null
              folder_id: FLD-8472639
              hardware_order_id: null
              id: '12847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8389469'
              status: pending
              subject: Box folder access request - MedHealth Strategy Documents
              tags:
                - document_access
              type: task
              updated_at: '2025-09-24T11:15:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8389469'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-20T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '12847'
                item:
                  access_type: read_only
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: CLT-4829573
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-3579146
                  expense_report_id: null
                  folder_id: FLD-8472639
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: send_for_signature
                client_id: CLT-4829573
                email: sarah.martinez@msg.com
              tool: nda_api
            - parameters:
                id: '12847'
                item:
                  access_type: read_only
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)




def test_doc_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need viewer access to the Box folder 'GlobalBank - Operations Manual' (FLD-4829571) for my active engagement (ENG-5791368). My NDA is signed, and my high-security clearance is still in progress (should complete in about a week). Can you confirm when I will get access? My email address is [david.martinez@msg.com](mailto:david.martinez@msg.com).
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders:
            - client_id: CLT-4829571
              confidentiality_level: client_confidential
              engagement_code: null
              folder_name: GlobalBank - Operations Manual
              id: FLD-4829571
              owner_email: jennifer.wilson@msg.com
          client_access_clearance_record:
            - clearance_level: high_security
              employee_email: david.martinez@msg.com
              status: in_progress
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-4829571
              employee_email: david.martinez@msg.com
              status: signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-5791368
              id: ASG-2847391
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-5791368
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: high_security
              id: CLT-4829571
              name: GlobalBank
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829571
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-5791368
              engagement_manager_email: jennifer.wilson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-10T10:15:00Z'
              description: Request for viewer access to GlobalBank - Operations Manual folder (FLD-4829571) for engagement ENG-5791368. Waiting for high-security clearance completion.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '2847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: pending
              subject: Box folder access request - GlobalBank Operations Manual
              tags:
                - document_access
              type: task
              updated_at: '2025-09-10T10:15:00Z'
          zendesk_users:
            - active: true
              created_at: '2019-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                $filter: requester_id eq '8' and status in ('open','pending','hold')
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: validate_engagement_code
                email: null
                engagement_code: ENG-5791368
              tool: mavenlink_api
            - parameters:
                action: get_status
                clearance_level: null
                email: david.martinez@msg.com
              tool: background_check_api
            - parameters:
                action: get_employee_assignments
                email: david.martinez@msg.com
                engagement_code: null
              tool: mavenlink_api
            - parameters:
                action: get_folder_details
                email: null
                folder_id: FLD-4829571
                permission_level: null
              tool: box_api
            - parameters:
                action: check_status
                client_id: CLT-4829571
                email: david.martinez@msg.com
              tool: nda_api
            - parameters:
                action: get_status
                clearance_level: high_security
                email: david.martinez@msg.com
              tool: background_check_api
            - parameters:
                action: get_timeline
                clearance_level: high_security
                email: null
              tool: background_check_api
            - parameters:
                id: '2847'
                item:
                  access_type: read_only
                  active: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: CLT-4829571
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: ENG-5791368
                  expense_report_id: null
                  folder_id: FLD-4829571
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: null
                  requester_id: '8'
                  role: null
                  status: open
                  subject: null
                  tags:
                    - document_access
                  type: null
                  verified: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need viewer access to the Box folder 'EnergyPlus - Contract Files' folder id FLD-8472951 for my current engagement (ENG-6802479). I'm assigned to the EnergyPlus project and my NDA isn't signed yet. I haven't started the security clearance process. Can you help me get access? [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com)
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders:
            - client_id: CLT-8472951
              confidentiality_level: client_confidential
              engagement_code: null
              folder_name: EnergyPlus - Contract Files
              id: FLD-8472951
              owner_email: richard.williams@msg.com
          client_access_clearance_record:
            - clearance_level: standard
              employee_email: sarah.martinez@msg.com
              status: not_initiated
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-8472951
              employee_email: sarah.martinez@msg.com
              status: not_signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-6802479
              id: ASG-4729183
              senior_manager_email: richard.williams@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-6802479
              senior_manager_email: richard.williams@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-8472951
              name: EnergyPlus Corporation
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-8472951
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-6802479
              engagement_manager_email: richard.williams@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Consultant
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2023-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2023-03-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: User requesting viewer access to Box folder 'EnergyPlus - Contract Files' (FLD-8472951)
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Access request
                  tags:
                    - document_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                action: get_folder_details
                email: null
                folder_id: FLD-8472951
                permission_level: null
              tool: box_api
            - parameters:
                action: validate_engagement_code
                email: sarah.martinez@msg.com
                engagement_code: ENG-6802479
              tool: mavenlink_api
            - parameters:
                engagement_code: ENG-6802479
              tool: salesforce_crm_get_engagement
            - parameters:
                email: sarah.martinez@msg.com
                engagement_code: ENG-6802479
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                access_type: null
                action: get_employee_prerequisites
                client_id: CLT-8472951
                email: sarah.martinez@msg.com
                system_name: null
              tool: client_access_api
            - parameters:
                action: initiate
                clearance_level: standard
                email: sarah.martinez@msg.com
              tool: background_check_api
            - parameters:
                id: '6'
                item:
                  access_type: read_only
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: CLT-8472951
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-6802479
                  expense_report_id: null
                  folder_id: FLD-8472951
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)




def test_doc_013(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need admin access to the Box folder 'RetailMax - Final Deliverables' (folder ID FLD-3847291) for my team. My engagement code is ENG-7913580 and my NDA and security clearance are complete. Can you please grant me admin permissions? email is [david.martinez@msg.com](mailto:david.martinez@msg.com)
    user_context: |
        Do not change your goal or switch topics.

        Do not give wrong email. Correct email is [david.martinez@msg.com](mailto:david.martinez@msg.com)

        If asked for the same info, provide it again’ and ‘Remain focused, clear, and patient

        You are David Martinez, a Manager at Meridian Strategy Group.

        Your goal is to gain admin access to the Box folder 'RetailMax - Final Deliverables' (ID: FLD-3847291) to manage permissions for your team.

        You have an active engagement (ENG-7913580) and have already signed the NDA and completed security clearance.

        You have a pending ticket for this request.

        Speak naturally and professionally.

        Do not invent data not provided in the context.

        If the agent denies admin access, accept 'viewer' access if that is the only option allowed by policy.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders:
            - client_id: CLT-8472951
              confidentiality_level: client_confidential
              engagement_code: null
              folder_name: RetailMax - Final Deliverables
              id: FLD-3847291
              owner_email: sarah.johnson@msg.com
          client_access_clearance_record:
            - clearance_level: standard
              employee_email: david.martinez@msg.com
              status: cleared
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-8472951
              employee_email: david.martinez@msg.com
              status: signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-7913580
              id: ASN-4729183
              senior_manager_email: sarah.johnson@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-7913580
              senior_manager_email: sarah.johnson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-8472951
              name: RetailMax Corporation
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-8472951
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-7913580
              engagement_manager_email: sarah.johnson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.johnson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: read_only
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: CLT-8472951
              course_id: null
              created_at: '2025-09-27T10:30:00Z'
              description: I need access to the RetailMax deliverables folder.
              device_type: null
              due_at: null
              engagement_code: ENG-7913580
              expense_report_id: null
              folder_id: FLD-3847291
              hardware_order_id: null
              id: '12847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: pending
              subject: Access to RetailMax folder
              tags:
                - document_access
              type: task
              updated_at: '2025-09-27T10:30:00Z'
          zendesk_users:
            - active: true
              created_at: '2025-08-10T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-08-10T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                $filter: email eq 'david.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8'
                $orderby: created_at desc
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                id: '12847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: task
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: get_folder_details
                email: null
                folder_id: FLD-3847291
                permission_level: null
              tool: box_api
            - parameters:
                email: david.martinez@msg.com
                engagement_code: ENG-7913580
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                access_type: null
                action: get_employee_prerequisites
                client_id: CLT-8472951
                email: david.martinez@msg.com
                system_name: null
              tool: client_access_api
            - parameters:
                action: grant_folder_access
                email: david.martinez@msg.com
                folder_id: FLD-3847291
                permission_level: viewer
              tool: box_api
            - parameters:
                id: '12847'
                item:
                  access_type: read_only
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: CLT-8472951
                  course_id: null
                  description: Access granted as 'viewer' (read-only) per policy for client_confidential folders. Admin access is not supported by Support; please contact the folder owner (Sarah Johnson) for permission upgrades.
                  device_type: null
                  due_at: null
                  engagement_code: ENG-7913580
                  expense_report_id: null
                  folder_id: FLD-3847291
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am David Martinez and my Email is [david.martinez@msg.com](mailto:david.martinez@msg.com). I need access to the 'HR Policy Documents' Box folder (ID: FLD-3847291) so I can update some outdated policies. Please grant me full access (read/write/delete) permissions.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders:
            - client_id: null
              confidentiality_level: internal
              engagement_code: null
              folder_name: HR Policy Documents
              id: FLD-3847291
              owner_email: hr.director@msg.com
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2019-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                $filter: email eq 'david.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: 'requester_id eq ''8'' and tags/any(t: t eq ''document_access'') and (status eq ''open'' or status eq ''pending'' or status eq ''hold'')'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: David Martinez (david.martinez@msg.com) requests full access to Box folder ID FLD-3847291 to update outdated policies.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: FLD-3847291
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Access to 'HR Policy Documents' Box folder
                  tags:
                    - document_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: get_folder_details
                email: null
                folder_id: FLD-3847291
                permission_level: null
              tool: box_api
            - parameters:
                action: grant_folder_access
                email: david.martinez@msg.com
                folder_id: FLD-3847291
                permission_level: viewer
              tool: box_api
            - parameters:
                id: '6'
                item:
                  access_type: read_only
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_015(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez, [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). I need viewer access to the Box folder 'ConsumerGoods - Project Docs' (Folder ID: FLD-8024691) for my work on the ConsumerGoods engagement. My engagement code is ENG-8024691, and my NDA is already signed. Client does not require me to get any security clearance. Can you please grant me access?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders:
            - client_id: CLT-8024691
              confidentiality_level: client_confidential
              engagement_code: null
              folder_name: ConsumerGoods - Project Docs
              id: FLD-8024691
              owner_email: michael.chen@msg.com
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-8024691
              employee_email: sarah.martinez@msg.com
              status: signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-12-28T00:00:00'
              engagement_code: ENG-8024691
              id: ASG-2847391
              senior_manager_email: richard.williams@msg.com
              start_date: '2024-08-15T00:00:00'
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients:
            - id: CLT-8024691
              name: ConsumerGoods Corp
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-8024691
              end_date: '2025-12-28T00:00:00'
              engagement_code: ENG-8024691
              engagement_manager_email: michael.chen@msg.com
              start_date: '2024-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Consultant
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2024-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: read_only
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: CLT-8024691
              course_id: null
              created_at: '2025-09-28T10:30:00Z'
              description: 'Requesting viewer access to Box folder ''ConsumerGoods - Project Docs'' for client project work. Folder ID: FLD-8024691. Engagement code: ENG-8024691.'
              device_type: null
              due_at: null
              engagement_code: ENG-8024691
              expense_report_id: null
              folder_id: FLD-8024691
              hardware_order_id: null
              id: '47'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: open
              subject: Box folder access request - ConsumerGoods Project Docs
              tags:
                - document_access
              type: task
              updated_at: '2025-09-28T10:30:00Z'
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-03-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: grant_folder_access
                email: sarah.martinez@msg.com
                folder_id: FLD-8024691
                permission_level: viewer
              tool: box_api
            - parameters:
                id: '47'
                item:
                  access_type: read_only
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: CLT-8024691
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-8024691
                  expense_report_id: null
                  folder_id: FLD-8024691
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_016(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need viewer access to the Box folder 'SecureGov - Audit Files' (FLD-8472951) for my current SecureGov engagement (ENG-9135702). My high-security clearance is complete, but I haven't signed the NDA yet. Can you help me get access? My work email is [david.martinez@msg.com](mailto:david.martinez@msg.com).
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders:
            - client_id: CLT-8472951
              confidentiality_level: client_confidential
              engagement_code: null
              folder_name: SecureGov - Audit Files
              id: FLD-8472951
              owner_email: sarah.thompson@msg.com
          client_access_clearance_record:
            - clearance_level: high_security
              employee_email: david.martinez@msg.com
              status: cleared
          client_access_client_system_access: []
          client_access_nda_record:
            - client_id: CLT-8472951
              employee_email: david.martinez@msg.com
              status: not_signed
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: null
              engagement_code: ENG-9135702
              id: ASN-4729183
              senior_manager_email: michael.chen@msg.com
              start_date: '2025-10-01T00:00:00'
          mavenlink_mv_engagements:
            - end_date: null
              engagement_code: ENG-9135702
              senior_manager_email: michael.chen@msg.com
              start_date: '2025-10-01T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: high_security
              id: CLT-8472951
              name: SecureGov Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-8472951
              end_date: null
              engagement_code: ENG-9135702
              engagement_manager_email: sarah.thompson@msg.com
              start_date: '2025-10-01T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Analyst
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2024-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: (312) 515-1173
              role: end-user
              updated_at: '2024-03-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: read_only
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: CLT-8472951
                  course_id: null
                  description: David Martinez (ENG-9135702) requests viewer access to Box folder 'SecureGov - Audit Files' for SecureGov engagement. High-security clearance complete, NDA not signed. Initiated NDA process.
                  device_type: null
                  due_at: null
                  engagement_code: ENG-9135702
                  expense_report_id: null
                  folder_id: FLD-8472951
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Request for viewer access to SecureGov - Audit Files (client_confidential)
                  tags:
                    - document_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: send_for_signature
                client_id: CLT-8472951
                email: david.martinez@msg.com
              tool: nda_api
            - parameters:
                id: '6'
                item:
                  access_type: read_only
                  active: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: CLT-8472951
                  course_id: null
                  description: David Martinez (ENG-9135702) requests viewer access to Box folder 'SecureGov - Audit Files' for SecureGov engagement. High-security clearance complete, NDA not signed. Pending NDA signature.
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: ENG-9135702
                  expense_report_id: null
                  folder_id: FLD-8472951
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: pending
                  subject: Request for viewer access to SecureGov - Audit Files (client_confidential)
                  tags:
                    - document_access
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my expense report EXP-2847293 was rejected because it says I exceeded the daily per diem limit. The expense was $120 for a client dinner in San Francisco, and I attached an itemized receipt. Can you help me get this approved? My email address is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com).
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 120
              category: meals
              employee_email: sarah.martinez@msg.com
              expense_date: '2025-09-16T00:00:00'
              id: EXP-2847293
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: itemized
              rejection_reason: Exceeds daily per diem limit
              trip_location_city: null
              trip_location_state: null
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Consultant
              manager_email: michael.thompson@msg.com
              name: Sarah Martinez
              office_location: San Francisco
              onboarding_phase: null
              partner_email: david.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: michael.thompson@msg.com
              level: Manager
              manager_email: david.chen@msg.com
              name: Michael Thompson
              office_location: San Francisco
              onboarding_phase: null
              partner_email: david.chen@msg.com
              start_date: '2021-08-10T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: david.chen@msg.com
              level: Partner
              manager_email: david.chen@msg.com
              name: David Chen
              office_location: San Francisco
              onboarding_phase: null
              partner_email: david.chen@msg.com
              start_date: '2018-01-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: +1-312-928-0417
              role: end-user
              updated_at: '2023-03-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                email: michael.thompson@msg.com
              tool: approver_lookup_get_contact
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Expense report EXP-2847293 for $120 client dinner in San Francisco rejected for exceeding $100/day per diem. Itemized receipt attached. Manager approval requested.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: EXP-2847293
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: 'Expense report EXP-2847293 rejected: per diem exception request'
                  tags:
                    - expense_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: 120
                approver_email: michael.thompson@msg.com
                engagement_code: null
                request_type: expense_override
                requester_email: sarah.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: michael.thompson@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: EXP-2847293
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez and my email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). My expense report EXP-4829573 for $60 meals in Chicago was rejected because the receipt is missing. I do have the receipt and can send it to my manager. Can you help get this approved?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 60
              category: meals
              employee_email: sarah.martinez@msg.com
              expense_date: '2025-09-06T00:00:00'
              id: EXP-4829573
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: missing
              rejection_reason: Receipt required for expenses $25 and above
              trip_location_city: Chicago
              trip_location_state: IL
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.thompson@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: completed
              partner_email: jennifer.chen@msg.com
              start_date: '2023-03-15T00:00:00Z'
            - availability_status: available
              backup_approver_email: emily.davis@msg.com
              email: michael.thompson@msg.com
              level: Manager
              manager_email: jennifer.chen@msg.com
              name: Michael Thompson
              office_location: Chicago
              onboarding_phase: completed
              partner_email: jennifer.chen@msg.com
              start_date: '2020-05-10T00:00:00Z'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-29T10:15:00Z'
              description: My expense report EXP-4829573 for $60 meals in Chicago was rejected by Concur. The system says receipt is required for expenses $25 and above. I need help getting this approved.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: EXP-4829573
              folder_id: null
              hardware_order_id: null
              id: '2848'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: open
              subject: Expense Report Flagged - Receipt Required
              tags:
                - expense_support
              type: task
              updated_at: '2025-09-29T10:15:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                amount: 60
                approver_email: michael.thompson@msg.com
                engagement_code: null
                request_type: expense_override
                requester_email: sarah.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '2848'
                item:
                  access_type: null
                  active: null
                  approval_required: 'yes'
                  approver_id: michael.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee confirmed they have the required receipt for expense report EXP-4829573 and will email it directly to their manager (michael.thompson@msg.com) for review. Awaiting manager confirmation of receipt before proceeding with approval.
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: EXP-4829573
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: high
                  requester_id: '8'
                  role: null
                  status: pending
                  subject: Expense Report Flagged - Receipt Required
                  tags:
                    - expense_support
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_003(x: TestContext, judge: Judge):
    """!
    query: |
        My expense report for a team lunch in Houston, TX, totaling $85 on 2025-09-01 (EXP-4829573), was rejected with the reason 'Exceeds daily per diem limit.' Can you help me get this approved? My email address is [david.martinez@msg.com](mailto:david.martinez@msg.com).
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 85
              category: meals
              employee_email: david.martinez@msg.com
              expense_date: '2025-09-01T00:00:00'
              id: EXP-4829573
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: itemized
              rejection_reason: Exceeds daily per diem limit
              trip_location_city: null
              trip_location_state: null
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Consultant
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2021-08-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Expense report for team lunch in Houston, TX, $85 on 2025-09-01, rejected for ''Exceeds daily per diem limit''. Fully itemized receipt attached. Employee: david.martinez@msg.com.'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: EXP-4829573
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: 'Expense report override request: Team lunch in Houston, TX ($85, 2025-09-01)'
                  tags:
                    - expense_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: 85
                approver_email: sarah.thompson@msg.com
                engagement_code: null
                request_type: expense_override
                requester_email: david.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: EXP-4829573
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi! My name is Michael Rodriguez, [michael.rodriguez@msg.com](mailto:michael.rodriguez@msg.com). My expense report EXP-4829573 was rejected because I don't have the itemized receipt for a $90 dinner in New York City. I lost the receipt and can't get another one. I believe my manager is available. Can you help me get this approved today?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 90
              category: meals
              employee_email: michael.rodriguez@msg.com
              expense_date: '2025-08-17T00:00:00'
              id: EXP-4829573
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: missing
              rejection_reason: Itemized receipt required for expenses above $75
              trip_location_city: null
              trip_location_state: null
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: michael.rodriguez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: Michael Rodriguez
              office_location: New York
              onboarding_phase: completed
              partner_email: david.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Senior Manager
              manager_email: david.chen@msg.com
              name: Sarah Thompson
              office_location: New York
              onboarding_phase: completed
              partner_email: david.chen@msg.com
              start_date: '2019-08-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: michael.rodriguez@msg.com
              id: '8'
              name: Michael Rodriguez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee requests override for $90 meal expense in New York City (high-cost region) on 2025-08-17. Receipt is lost and cannot be obtained.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: EXP-4829573
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: Expense report EXP-4829573 rejected due to missing receipt
                  tags:
                    - expense_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: 90
                approver_email: sarah.thompson@msg.com
                request_type: expense_override
                requester_email: michael.rodriguez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi! My name is David Martinez [david.martinez@msg.com](mailto:david.martinez@msg.com). My expense report EXP-3847291 is rejected but I made a request for approval with my manager. I only have a receipt showing the total amount, and I can't get an itemized version. Can you help override this so I can get reimbursed?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: 95
              approver_email: patricia.wong@msg.com
              engagement_code: null
              id: APR-2847391
              request_type: expense_override
              requester_email: david.martinez@msg.com
              status: pending
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 95
              category: client_entertainment
              employee_email: david.martinez@msg.com
              expense_date: '2025-09-11T00:00:00'
              id: EXP-3847291
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: attached
              rejection_reason: Exceeds daily per diem limit; Itemized receipt required
              trip_location_city: Denver
              trip_location_state: CO
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Manager
              manager_email: patricia.wong@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.thompson@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: patricia.wong@msg.com
              level: Partner
              manager_email: richard.thompson@msg.com
              name: Patricia Wong
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.thompson@msg.com
              start_date: '2018-07-22T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: 'yes'
              approver_id: patricia.wong@msg.com
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-26T10:30:00Z'
              description: Requesting approval override for expense report EXP-3847291. Denver client entertainment expense of $95 was rejected for exceeding per diem limit and requiring itemized receipt. I have the receipt but it only shows total amount, not itemized breakdown. Cannot obtain itemized version.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: EXP-3847291
              folder_id: null
              hardware_order_id: null
              id: '2847'
              license_pool: null
              organization_id: null
              priority: high
              requester_id: '8'
              status: pending
              subject: Expense Override Request - EXP-3847291
              tags:
                - expense_support
              type: task
              updated_at: '2025-09-26T15:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T14:30:00Z'
              verified: true
            - active: true
              created_at: '2018-07-22T09:00:00Z'
              email: patricia.wong@msg.com
              id: '13'
              name: Patricia Wong
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-20T11:15:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_expense_report
                approver_email: null
                booking_id: null
                expense_report_id: EXP-3847291
                override_reason: null
              tool: concur_api
            - parameters:
                $filter: email eq 'david.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                approver_email: null
                engagement_code: null
                request_type: expense_override
                requester_email: david.martinez@msg.com
              tool: approval_get_status
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is David Martinez, e-mail [david.martinez@msg.com](mailto:david.martinez@msg.com). My expense report EXP-2847293 was rejected because it was submitted late. I was traveling a lot and forgot to submit it within the 90-day window, but I have attached the receipt. Can you help me get this approved?
    user_context: |
        Your phone number is +1-512-847-3928
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 45
              category: meals
              employee_email: david.martinez@msg.com
              expense_date: '2025-06-03T11:00:00Z'
              id: EXP-2847293
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: attached
              rejection_reason: Late submission - exceeds 90-day policy
              trip_location_city: Phoenix
              trip_location_state: AZ
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements:
            - end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-4829573
              senior_manager_email: michael.chen@msg.com
              start_date: '2025-09-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829573
              name: TechFlow Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829573
              end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-4829573
              engagement_manager_email: sarah.thompson@msg.com
              start_date: '2025-09-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Consultant
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Austin
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Austin
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2021-05-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-08-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: 512-847-3928
              role: end-user
              updated_at: '2024-08-15T09:00:00Z'
              verified: true
            - active: true
              created_at: '2024-07-20T10:00:00Z'
              email: sarah.thompson@msg.com
              id: '9'
              name: Sarah Thompson
              organization_id: null
              phone: 415-892-3847
              role: end-user
              updated_at: '2024-07-20T10:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                $filter: email eq 'david.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8'
                $orderby: '''created_at_desc'''
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Employee has a rejected ticket and would like to have it approved '
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: 'Creating expense ticket '
                  tags:
                    - expense_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: get_employee
                email: sarah.thompson@msg.com
              tool: workday_api
            - parameters:
                action: get_expense_report
                approver_email: null
                booking_id: null
                expense_report_id: EXP-2847293
                override_reason: null
              tool: concur_api
            - parameters:
                amount: 45
                approver_email: sarah.thompson@msg.com
                engagement_code: null
                request_type: expense_override
                requester_email: david.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  active: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Customer reached out for rejected expense, overriding expense report, sent for manager approval
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: EXP-2847293
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: high
                  requester_id: '8'
                  role: null
                  status: pending
                  subject: Override expense report
                  tags:
                    - expense_support
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my expense report EXP-7394821 for a client dinner in Boston was rejected because it exceeded the $100/day per diem and was submitted 95 days after the expense date. The amount was $150 and I attached an itemized receipt. My engagement code is ENG-1357924. My manager Sarah Thompson(sarah.thompson@msg.com) has already approved the override. Can you help process this?
    user_context: |
        You are David Martinez and your email is  [david.martinez@msg.com](mailto:david.martinez@msg.com)

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: 150
              approver_email: sarah.thompson@msg.com
              engagement_code: ENG-1357924
              id: APR-8472951
              request_type: expense_override
              requester_email: david.martinez@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 150
              category: meals
              employee_email: david.martinez@msg.com
              expense_date: '2025-06-28T00:00:00'
              id: EXP-7394821
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: itemized
              rejection_reason: Exceeds daily per diem limit; Late submission
              trip_location_city: Boston
              trip_location_state: MA
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-1357924
              id: ASN-2847391
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-01T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-1357924
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-01T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829573
              name: Boston Financial Group
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829573
              end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-1357924
              engagement_manager_email: jennifer.wilson@msg.com
              start_date: '2025-08-01T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Analyst
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: New York
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: New York
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2020-01-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-30T14:30:00Z'
              description: Need approval override for rejected expense report EXP-7394821. Client dinner in Boston exceeded per diem limit and was submitted late.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '12847'
              license_pool: null
              organization_id: null
              priority: high
              requester_id: '8'
              status: open
              subject: Expense Report Override Request - EXP-7394821
              tags:
                - expense_support
              type: task
              updated_at: '2025-09-30T14:30:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T10:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                approver_email: sarah.thompson@msg.com
                engagement_code: ENG-1357924
                request_type: expense_override
                requester_email: david.martinez@msg.com
              tool: approval_get_status
            - parameters:
                action: override_expense_rejection
                approver_email: sarah.thompson@msg.com
                booking_id: null
                expense_report_id: EXP-7394821
                override_reason: justified_exception
              tool: concur_api
            - parameters:
                id: '12847'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-1357924
                  expense_report_id: EXP-7394821
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi,

        My expense report for meals in Atlanta, GA from 40 days ago (amount: $70, receipt missing) was flagged and rejected because a receipt is required for expenses over $25. I lost the receipt during travel and can't recover it, but my manager has already approved an exception. Can you help get this expense reimbursed?
    user_context: |
        You are Sarah Martinez and your email address is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). Your expense report ID is EXP-2847593

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: 70
              approver_email: david.thompson@msg.com
              engagement_code: null
              id: APR-4829573
              request_type: expense_override
              requester_email: sarah.martinez@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 70
              category: meals
              employee_email: sarah.martinez@msg.com
              expense_date: '2025-08-22T00:00:00'
              id: EXP-2847593
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: missing
              rejection_reason: Receipt required for expenses $25 and above
              trip_location_city: null
              trip_location_state: null
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Senior Consultant
              manager_email: david.thompson@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: david.thompson@msg.com
              level: Manager
              manager_email: jennifer.chen@msg.com
              name: David Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.chen@msg.com
              start_date: '2021-08-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: +1-312-847-3921
              role: end-user
              updated_at: '2025-09-28T10:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: david.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Manager-approved exception for Sarah Martinez, Senior Consultant''s, expense report (ID: EXP-2847593, $70 for meals, Atlanta, GA, 40 days ago).'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: EXP-2847593
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: Expense Report Override - EXP-2847593
                  tags:
                    - expense_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                action: get_expense_report
                approver_email: null
                booking_id: null
                expense_report_id: EXP-2847593
                override_reason: null
              tool: concur_api
            - parameters:
                approver_email: null
                engagement_code: null
                request_type: expense_override
                requester_email: sarah.martinez@msg.com
              tool: approval_get_status
            - parameters:
                action: override_expense_rejection
                approver_email: david.thompson@msg.com
                booking_id: null
                expense_report_id: EXP-2847593
                override_reason: receipt_exception
              tool: concur_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_009(x: TestContext, judge: Judge):
    """!
    query: |
        My expense report EXP-2847392 for a $22 lunch in Dallas, TX was flagged as a policy violation, but it's under $25 and within the per diem limit. I didn't attach a receipt since it's not required for expenses under $25, so there seems to be a system error. Can you help resolve this?
    user_context: |
        Your email address is [david.martinez@msg.com](mailto:david.martinez@msg.com).

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 22
              category: meals
              employee_email: david.martinez@msg.com
              expense_date: '2025-08-27T00:00:00'
              id: EXP-2847392
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: missing
              rejection_reason: Policy violation detected
              trip_location_city: Dallas
              trip_location_state: TX
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Austin
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Austin
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2019-08-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                action: get_expense_report
                approver_email: null
                booking_id: null
                expense_report_id: EXP-2847392
                override_reason: null
              tool: concur_api
            - parameters:
                $filter: email eq 'david.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee reports expense report EXP-2847392 for $22 lunch in Dallas, TX was flagged for policy violation. Expense is under $25, within per diem, and no receipt required.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: EXP-2847392
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: Expense report EXP-2847392 flagged for $22 lunch in Dallas, TX (no receipt required)
                  tags:
                    - expense_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: override_expense_rejection
                approver_email: sarah.thompson@msg.com
                booking_id: null
                expense_report_id: EXP-2847392
                override_reason: system_error
              tool: concur_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_010(x: TestContext, judge: Judge):
    """!
    query: |
        My expense report EXP-5847291 for a client dinner in Seattle, WA was rejected because it exceeded the daily per diem limit. I actually have an existing ticket from 3 days ago for this request that is currently pending manager approval. I have attached an itemized receipt and provided the engagement code ENG-2468035 to assist with the process. Can you please check its status? My email address is [david.martinez@msg.com](mailto:david.martinez@msg.com).
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: 110
              approver_email: sarah.thompson@msg.com
              engagement_code: ENG-2468035
              id: APR-8472951
              request_type: expense_override
              requester_email: david.martinez@msg.com
              status: pending
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 110
              category: meals
              employee_email: david.martinez@msg.com
              expense_date: '2025-09-03T00:00:00'
              id: EXP-5847291
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: itemized
              rejection_reason: Exceeds daily per diem limit
              trip_location_city: null
              trip_location_state: null
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-2468035
              id: ASN-7294851
              senior_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-8472951
              name: Pacific Northwest Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-8472951
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-2468035
              engagement_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: San Francisco
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Partner
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: San Francisco
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-08-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-28T10:15:00Z'
              description: 'Request for manager approval to override expense report EXP-5847291. Client working dinner in Seattle, WA exceeded per diem limit ($110 vs $100 limit). Receipt attached with itemization. Engagement code: ENG-2468035'
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '47291'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: pending
              subject: Expense Report Override Request - EXP-5847291
              tags:
                - expense_support
              type: task
              updated_at: '2025-09-28T10:15:00Z'
          zendesk_users:
            - active: true
              created_at: '2025-09-28T10:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T10:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                $filter: subject eq 'Expense Report Override Request - EXP-5847291'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                approver_email: null
                engagement_code: ENG-2468035
                request_type: expense_override
                requester_email: david.martinez@msg.com
              tool: approval_get_status
            - parameters:
                action: validate_engagement_code
                email: null
                engagement_code: ENG-2468035
              tool: mavenlink_api
            - parameters:
                engagement_code: ENG-2468035
              tool: salesforce_crm_get_engagement
            - parameters:
                email: david.martinez@msg.com
                engagement_code: ENG-2468035
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                approver_email: sarah.thompson@msg.com
                engagement_code: ENG-2468035
                request_type: expense_override
                requester_email: david.martinez@msg.com
              tool: approval_get_status
            - parameters:
                id: '47291'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-2468035
                  expense_report_id: EXP-5847291
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                id: '47291'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Ethan Carter, e-mail [ethan.carter@msg.com](mailto:ethan.carter@msg.com). I was informed that my expense report EXP-9755108 for a team dinner in Philadelphia was rejected because it exceeded the $75 per diem, the receipt is missing, and it was submitted late (100 days after the expense date). I have lost the receipt and it can't be recovered. My manager Alex Diets has already approved the override for all violations. The engagement code for this expense is ENG-9753108.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: 80
              approver_email: alex.diets@msg.com
              engagement_code: ENG-9753108
              id: APR-1100205
              request_type: expense_override
              requester_email: ethan.carter@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 80
              category: meals
              employee_email: ethan.carter@msg.com
              expense_date: '2025-06-23T13:00:00Z'
              id: EXP-9755108
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: missing
              rejection_reason: Exceeds daily per diem limit; Receipt required; Late submission
              trip_location_city: Philadelphia
              trip_location_state: PA
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: ethan.carter@msg.com
              end_date: '2025-08-31T00:00:00'
              engagement_code: ENG-9753108
              id: ASN-0016145
              senior_manager_email: alex.diets@msg.com
              start_date: '2025-03-16T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-08-31T00:00:00'
              engagement_code: ENG-9753108
              senior_manager_email: alex.diets@msg.com
              start_date: '2025-03-15T00:00:00'
              status: completed
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-9113108
              name: Liberty East Healthcare
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-9113108
              end_date: '2025-08-31T00:00:00'
              engagement_code: ENG-9753108
              engagement_manager_email: alex.diets@msg.com
              start_date: '2025-03-15T00:00:00'
              status: completed
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: ethan.carter@msg.com
              level: Consultant
              manager_email: alex.diets@msg.com
              name: Ethan Carter
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2023-04-10T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: alex.diets@msg.com
              level: Manager
              manager_email: richard.williams@msg.com
              name: Alex Diets
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2020-02-03T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-04-10T09:00:00Z'
              email: ethan.carter@msg.com
              id: '8'
              name: Ethan Carter
              organization_id: null
              phone: +1 (215) 555-0148
              role: end-user
              updated_at: '2025-09-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                $filter: requester_id eq '8'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: alex.diets@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Employee (Ethan Carter, Consultant) requests override for rejected Concur expense report EXP-9755108. Details: Philadelphia, PA; $80 meals/team dinner; expense date 2025-06-23; receipt missing and unrecoverable. Concur rejection: per diem exceeded, receipt required, late submission (>90 days). Manager Alex Diets already approved override. Engagement code provided ENG-9753108 is completed/inactive and will not be recorded on the ticket.'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: EXP-9755108
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: Expense report EXP-9755108 rejected — override request (per diem, receipt, late submission)
                  tags:
                    - expense_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: get_employee
                email: ethan.carter@msg.com
              tool: workday_api
            - parameters:
                action: get_expense_report
                approver_email: null
                booking_id: null
                expense_report_id: EXP-9755108
                override_reason: null
              tool: concur_api
            - parameters:
                action: get_engagement
                email: null
                engagement_code: ENG-9753108
              tool: mavenlink_api
            - parameters:
                action: override_expense_rejection
                approver_email: alex.diets@msg.com
                booking_id: null
                expense_report_id: EXP-9755108
                override_reason: justified_exception
              tool: concur_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  active: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: null
                  requester_id: null
                  role: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi! My name is Sarah Martinez, [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). My expense report EXP-4829573 for $65 in meals during a workshop in Austin, TX was rejected for exceeding the per diem limit. I have attached an itemized receipt. Can you help me get this approved? I have contacted support on this matter before.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 65
              category: meals
              employee_email: sarah.martinez@msg.com
              expense_date: '2025-08-12T00:00:00'
              id: EXP-4829573
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: itemized
              rejection_reason: Exceeds daily per diem limit
              trip_location_city: Austin
              trip_location_state: TX
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.thompson@msg.com
              name: Sarah Martinez
              office_location: Austin
              onboarding_phase: completed
              partner_email: jennifer.davis@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: michael.thompson@msg.com
              level: Manager
              manager_email: jennifer.davis@msg.com
              name: Michael Thompson
              office_location: Austin
              onboarding_phase: null
              partner_email: jennifer.davis@msg.com
              start_date: '2021-08-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-27T10:15:00Z'
              description: My expense report EXP-4829573 was rejected for exceeding per diem limit. The expense was $65 for meals during a workshop in Austin, TX. I have itemized receipts attached. Can you help me get this approved?
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '12847'
              license_pool: null
              organization_id: null
              priority: high
              requester_id: '8'
              status: open
              subject: Expense Report Rejection - Austin Workshop Meals
              tags:
                - expense_support
              type: task
              updated_at: '2025-09-27T10:15:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-20T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                amount: 65
                approver_email: michael.thompson@msg.com
                request_type: expense_override
                requester_email: sarah.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '12847'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: michael.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: My expense report EXP-4829573 was rejected for exceeding per diem limit. The expense was $65 for meals during a workshop in Austin, TX. I have itemized receipts attached. Can you help me get this approved?
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: EXP-4829573
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: pending
                  subject: Expense Report Rejection - Austin Workshop Meals
                  tags:
                    - expense_support
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_013(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I’m a Partner and I need help resolving an expense report issue. My expense report EXP-2847294 for a $ 95 executive dinner in Washington, DC was flagged for review in Concur. An itemized receipt is attached, and I’m aware the per-day limit is 100, so this appears to be a mistake. It shouldn't be rejected and should not require any approvals. Could you please review it and approve the report?
    user_context: |
        Data available to you:

        "email": "david.harrison@msg.com",

        "name": "David Harrison",

        "level": "Partner",

        "office_location": "New York",

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 95
              category: meals
              employee_email: david.harrison@msg.com
              expense_date: '2025-09-13T00:00:00'
              id: EXP-2847294
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: itemized
              rejection_reason: Flagged for review
              trip_location_city: Washington
              trip_location_state: DC
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: michael.torres@msg.com
              email: david.harrison@msg.com
              level: Partner
              manager_email: sarah.mitchell@msg.com
              name: David Harrison
              office_location: New York
              onboarding_phase: null
              partner_email: david.harrison@msg.com
              start_date: '2019-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.mitchell@msg.com
              level: Partner
              manager_email: robert.chen@msg.com
              name: Sarah Mitchell
              office_location: New York
              onboarding_phase: null
              partner_email: david.harrison@msg.com
              start_date: '2017-08-22T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2019-03-15T09:00:00Z'
              email: david.harrison@msg.com
              id: '8'
              name: David Harrison
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_expense_report
                approver_email: null
                booking_id: null
                expense_report_id: EXP-2847294
                override_reason: null
              tool: concur_api
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Expense report EXP-2847294 for $95 executive dinner in Washington, DC flagged for review. Itemized receipt attached. Amount under $100 per diem limit.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: EXP-2847294
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: urgent
                  requester_id: '8'
                  status: open
                  subject: Expense report EXP-2847294 flagged for review - under per diem limit
                  tags:
                    - expense_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: override_expense_rejection
                approver_email: sarah.mitchell@msg.com
                booking_id: null
                expense_report_id: EXP-2847294
                override_reason: system_error
              tool: concur_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Michael Rodriguez (michael.rodriguez@msg.com). My expense report EXP-2847391 was rejected by Concur for "Receipt documentation issue". It's a $55 meal expense from my Portland trip, and I attached the receipt showing the total. I thought itemized receipts were only required for expenses over $7. It looks like an error, can you help me resolve this?
    user_context: |
        You are Michael Rodriguez. Your email is [michael.rodriguez@msg.com](mailto:michael.rodriguez@msg.com) and you work in the Chicago office. Today is October 1, 2025. You submitted an expense report (EXP-2847391) for a $55 meal expense from your Portland trip on September 9, 2025. You attached a receipt showing the total amount. Concur rejected it with the message "Receipt documentation issue." You're familiar with the company's expense policy and believe itemized receipts are only required for expenses over $75, so you don't understand why your $55 expense was rejected when you provided a regular receipt.



        **Rules**:

        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 55
              category: meals
              employee_email: michael.rodriguez@msg.com
              expense_date: '2025-09-09T00:00:00'
              id: EXP-2847391
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: attached
              rejection_reason: Receipt documentation issue
              trip_location_city: Portland
              trip_location_state: OR
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: michael.rodriguez@msg.com
              level: Senior Consultant
              manager_email: sarah.thompson@msg.com
              name: Michael Rodriguez
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Manager
              manager_email: david.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.chen@msg.com
              start_date: '2021-08-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: michael.rodriguez@msg.com
              id: '8'
              name: Michael Rodriguez
              organization_id: null
              phone: +1-321-2847-391
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: michael.rodriguez@msg.com
              tool: workday_api
            - parameters:
                action: get_expense_report
                approver_email: null
                booking_id: null
                expense_report_id: EXP-2847391
                override_reason: null
              tool: concur_api
            - parameters:
                brand_id: null
                category: null
                label_names: null
                locale: null
                multibrand: null
                query: expense per diem rates
                section: null
              tool: zendesk_search_articles
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: $55 meal expense in Portland, OR rejected for 'Receipt documentation issue'. Receipt attached shows total. Employee requests override.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: EXP-2847391
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: Expense report EXP-2847391 rejected for receipt issue
                  tags:
                    - expense_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: override_expense_rejection
                approver_email: sarah.thompson@msg.com
                booking_id: null
                expense_report_id: EXP-2847391
                override_reason: system_error
              tool: concur_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_015(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need assistance with my expense report EXP-2847392 for the $30 lunch meeting in Tucson, AZ. The report was rejected because the receipt is missing, and I already confirmed I can't recover it. My manager has approved the receipt exception. Can you help finalize the override so I can get reimbursed? My email is [david.martinez@msg.com](mailto:david.martinez@msg.com).
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: 30
              approver_email: sarah.thompson@msg.com
              engagement_code: null
              id: APR-8472951
              request_type: expense_override
              requester_email: david.martinez@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 30
              category: meals
              employee_email: david.martinez@msg.com
              expense_date: '2025-08-02T00:00:00'
              id: EXP-2847392
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: missing
              rejection_reason: Receipt required for expenses $25 and above
              trip_location_city: null
              trip_location_state: null
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Austin
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Austin
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-06-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: 'yes'
              approver_id: sarah.thompson@msg.com
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-24T14:30:00Z'
              description: Request for receipt exception approval for expense report EXP-2847392. Lunch meeting expense of $30 in Tucson, AZ. Receipt was accidentally discarded and cannot be recovered.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '47291'
              license_pool: null
              organization_id: null
              priority: high
              requester_id: '8'
              status: pending
              subject: Expense Report Receipt Exception Request - EXP-2847392
              tags:
                - expense_support
              type: task
              updated_at: '2025-09-24T15:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_expense_report
                approver_email: null
                booking_id: null
                expense_report_id: EXP-2847392
                override_reason: null
              tool: concur_api
            - parameters:
                approver_email: null
                engagement_code: null
                request_type: expense_override
                requester_email: david.martinez@msg.com
              tool: approval_get_status
            - parameters:
                id: '47291'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: override_expense_rejection
                approver_email: sarah.thompson@msg.com
                booking_id: null
                expense_report_id: EXP-2847392
                override_reason: receipt_exception
              tool: concur_api
            - parameters:
                id: '47291'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: EXP-2847392
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_exp_018(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need help with a rejected expense report. The report ID is EXP-1000011. It was for a client meeting lunch in Houston that cost $55, but it got rejected for exceeding the daily limit and missing receipt. I actually found the receipt - it was in my email. The expense was from 70 days ago. Also, this is for engagement ENG-4826159. I already had a ticket about this that was marked solved 2 days ago, but the expense is still showing as rejected in Concur.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports:
            - amount: 55
              category: meals
              employee_email: jennifer.patel@msg.com
              expense_date: '2025-07-23T00:00:00'
              id: EXP-1000011
              override_approved: false
              override_approved_by: null
              override_reason: null
              receipt_status: missing
              rejection_reason: Exceeds daily per diem limit; Receipt required
              trip_location_city: Houston
              trip_location_state: TX
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: jennifer.patel@msg.com
              end_date: '2025-12-31T00:00:00'
              engagement_code: ENG-4826159
              id: ASG-0000001
              senior_manager_email: sarah.johnson@msg.com
              start_date: '2025-06-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-31T00:00:00'
              engagement_code: ENG-4826159
              senior_manager_email: sarah.johnson@msg.com
              start_date: '2025-06-01T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements:
            - client_id: CLT-0012345
              end_date: '2025-12-31T00:00:00'
              engagement_code: ENG-4826159
              engagement_manager_email: sarah.johnson@msg.com
              start_date: '2025-06-01T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees: []
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-29T10:30:00Z'
              description: Expense report EXP-1000011 was rejected by Concur system for policy violations
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: EXP-1000011
              folder_id: null
              hardware_order_id: null
              id: '1001'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: solved
              subject: Expense report rejection
              tags:
                - expense_support
              type: task
              updated_at: '2025-09-29T15:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2025-09-15T09:00:00Z'
              email: jennifer.patel@msg.com
              id: '8'
              name: Jennifer Patel
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: jennifer.patel@msg.com
              tool: workday_api
            - parameters:
                $filter: '''email eq "jennifer.patel@msg.com"'''
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: '''requester_id eq "8"'''
                $orderby: created_at desc
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                id: '1001'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: get_expense_report
                approver_email: null
                booking_id: null
                expense_report_id: EXP-1000011
                override_reason: null
              tool: concur_api
            - parameters:
                brand_id: null
                category: null
                label_names: null
                locale: null
                multibrand: null
                query: expense per diem rates travel region
                section: null
              tool: zendesk_search_articles
            - parameters:
                action: validate_engagement_code
                email: null
                engagement_code: ENG-4826159
              tool: mavenlink_api
            - parameters:
                engagement_code: ENG-4826159
              tool: salesforce_crm_get_engagement
            - parameters:
                email: jennifer.patel@msg.com
                engagement_code: ENG-4826159
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                email: michael.chen@msg.com
              tool: approver_lookup_get_contact
            - parameters:
                amount: 55
                approver_email: michael.chen@msg.com
                engagement_code: ENG-4826159
                request_type: expense_override
                requester_email: jennifer.patel@msg.com
              tool: approval_create_request
            - parameters:
                id: '1001'
                item:
                  access_type: null
                  active: null
                  approval_required: 'yes'
                  approver_id: michael.chen@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: ENG-4826159
                  expense_report_id: EXP-1000011
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: high
                  requester_id: null
                  role: null
                  status: pending
                  subject: null
                  tags:
                    - expense_support
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to request a replacement for my company phone. My current device is an iPhone 14, it's 30 months old and the battery health is at 78%. There's no physical damage. I'm based in Chicago, my email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com).
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG84729163
              employee_email: sarah.martinez@msg.com
              id: ASN-4729183
              returned_at: null
          asset_management_devices:
            - age_months: 30
              device_type: phone
              id: MSG84729163
              inventory_status: assigned
              location: Chicago
              model: iPhone 14
            - age_months: 0
              device_type: phone
              id: MSG95847261
              inventory_status: available
              location: Chicago
              model: iPhone 15
            - age_months: 0
              device_type: phone
              id: MSG95847262
              inventory_status: available
              location: Chicago
              model: iPhone 15
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Consultant
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2022-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                $filter: email eq 'sarah.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                action: get_employee_devices
                asset_id: null
                device_type: null
                email: sarah.martinez@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                action: check_inventory
                asset_id: null
                device_type: phone
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: reserve_device
                asset_id: null
                device_type: phone
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: assign_device
                asset_id: MSG95847261
                device_type: null
                email: sarah.martinez@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                action: retire_device
                asset_id: MSG84729163
                device_type: null
                email: null
                location: null
              tool: asset_management_api
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: MSG95847261
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee requests replacement for iPhone 14 (30 months old, battery health 78%, no damage). Chicago office. New device to be assigned.
                  device_type: phone
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Phone replacement request - battery health 78%
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_003(x: TestContext, judge: Judge):
    """!
    query: |
        My phone battery drains really fast. Can I get a replacement? My phone is an iPhone 14, 14 months old, battery health is 92%.
    user_context: |
        - If the agent asks for your email, it's [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com)

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG47382951
              employee_email: sarah.martinez@msg.com
              id: ASSGN-8472951
              returned_at: null
          asset_management_devices:
            - age_months: 14
              device_type: phone
              id: MSG47382951
              inventory_status: assigned
              location: Chicago
              model: iPhone 14
            - age_months: 14
              device_type: phone
              id: MSG47383541
              inventory_status: available
              location: Chicago
              model: iPhone 14
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Senior Consultant
              manager_email: michael.thompson@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.chen@msg.com
              start_date: '2023-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee requests replacement for iPhone 14 (14 months old, battery health 92%, no damage).
                  device_type: phone
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: Phone battery drains fast - replacement request
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: phone
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi! My name is Alex Diets, e-mail [alex.diets@msg.com](mailto:alex.diets@msg.com). My phone screen is cracked and partially unresponsive. I need a replacement for it. My current phone is an iPhone 14, about 20 months old, and the battery health is 88%. I work out of the Chicago office. Can you help me get a new phone? I think my manager is available so you can send him the approval request
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG47382951
              employee_email: alex.diets@msg.com
              id: ASMT-8472951
              returned_at: null
          asset_management_devices:
            - age_months: 20
              device_type: phone
              id: MSG47382951
              inventory_status: assigned
              location: Chicago
              model: iPhone 14
            - age_months: 0
              device_type: phone
              id: MSG59284736
              inventory_status: available
              location: Chicago
              model: iPhone 15
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: alex.diets@msg.com
              level: Manager
              manager_email: sarah.martinez@msg.com
              name: Alex Diets
              office_location: Chicago
              onboarding_phase: completed
              partner_email: david.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Senior Manager
              manager_email: david.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: completed
              partner_email: david.chen@msg.com
              start_date: '2019-08-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: alex.diets@msg.com
              id: '7'
              name: Alex Dieths
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: alex.diets@msg.com
              tool: workday_api
            - parameters:
                $filter: email eq 'alex.diets@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '7'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: check_inventory
                asset_id: null
                device_type: phone
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                email: sarah.martinez@msg.com
              tool: approver_lookup_get_contact
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.martinez@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Alex Diets requests urgent replacement for iPhone 14 (20 months old, battery health 88%) due to cracked and partially unresponsive screen. Chicago office has phones in stock. Approval required from direct manager.
                  device_type: phone
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '7'
                  status: open
                  subject: Urgent phone replacement request - cracked screen (iPhone 14, 20 months old)
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: null
                approver_email: sarah.martinez@msg.com
                engagement_code: null
                request_type: hardware_replacement
                requester_email: alex.diets@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  active: null
                  asset_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  role: null
                  status: pending
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is David Martinez, my email address is [david.martinez@msg.com](mailto:david.martinez@msg.com). My iPhone 14 (28 months old) was dropped in water and now won't charge. Can you help me get a replacement? I need it urgently for work. I already reported this yesterday. You may also need to retire the device as it no longer charges and won't come on, I suspect the battery is damaged.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG84729163
              employee_email: david.martinez@msg.com
              id: DA-8472916
              returned_at: null
          asset_management_devices:
            - age_months: 28
              device_type: phone
              id: MSG84729163
              inventory_status: assigned
              location: Chicago
              model: iPhone 14
            - age_months: 0
              device_type: phone
              id: MSG84729164
              inventory_status: available
              location: Chicago
              model: iPhone 15
            - age_months: 0
              device_type: phone
              id: MSG84729165
              inventory_status: available
              location: Chicago
              model: iPhone 15
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Partner
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2018-01-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-30T14:30:00Z'
              description: My iPhone 14 was dropped in water yesterday and no longer charges properly. The device is 28 months old. I need a replacement phone as soon as possible as I cannot receive calls or access work applications.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '12847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: open
              subject: Phone replacement needed - water damage
              tags:
                - hardware_request
              type: task
              updated_at: '2025-09-30T14:30:00Z'
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-30T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                id: '12847'
                table: tickets
              tool: zendesk_get_item
            - parameters:
                action: get_employee_devices
                device_type: phone
                email: david.martinez@msg.com
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: get_device_details
                asset_id: MSG84729163
                device_type: phone
                email: david.martinez@msg.com
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: check_inventory
                device_type: phone
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: reserve_device
                asset_id: MSG84729164
                device_type: phone
                email: david.martinez@msg.com
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: assign_device
                asset_id: MSG84729164
                device_type: phone
                email: david.martinez@msg.com
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: retire_device
                asset_id: MSG84729163
                device_type: phone
                email: david.martinez@msg.com
                location: Chicago
              tool: asset_management_api
            - parameters:
                id: '12847'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: MSG84729164
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Phone replacement request due to water damage
                  device_type: phone
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: urgent
                  requester_id: '8'
                  status: solved
                  subject: 'New phone was assigned ID: MSG84729164'
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi! My work phone was stolen during a business trip. I’ve already filed a police report, and the phone is about 15 months old. Please help me get a replacement as soon as possible. By the way, I haven't requested an approval from my boss yet.
    user_context: |
        You are Simon (MSG employee - senior consultant), your email is [simon.johnson@msg.com](mailto:simon.johnson@msg.com). Keep your replies polite, professional, and concise. Use a formal tone, and answer only what the agent asks (do not introduce new topics or extra requests). When the agent asks follow-up questions, you should: confirm that a police report has been filed, confirm the phone was stolen during a business trip, state that battery health / damage details are not applicable because the phone is missing, and confirm you can pick up the replacement at your office and want the fastest option. You must not claim that approval is already granted. Do not invent or provide any data not present in the provided context. If the agent indicates that an approval request has been created, do not make repeated status checks .
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG84729163
              employee_email: simon.johnson@msg.com
              id: DA-8472916
              returned_at: null
          asset_management_devices:
            - age_months: 15
              device_type: phone
              id: MSG84729163
              inventory_status: assigned
              location: Chicago
              model: iPhone 14
            - age_months: 0
              device_type: phone
              id: MSG94738251
              inventory_status: available
              location: Chicago
              model: iPhone 15
            - age_months: 0
              device_type: phone
              id: MSG94738252
              inventory_status: available
              location: Chicago
              model: iPhone 15
            - age_months: 0
              device_type: phone
              id: MSG94738253
              inventory_status: available
              location: Chicago
              model: iPhone 15
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: simon.johnson@msg.com
              level: Senior Consultant
              manager_email: rachel.martinez@msg.com
              name: Simon Johnson
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: rachel.martinez@msg.com
              level: Manager
              manager_email: david.chen@msg.com
              name: Rachel Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.chen@msg.com
              start_date: '2020-01-20T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-15T10:30:00Z'
              description: Need access to Adobe Creative Suite for client presentation materials
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '1247'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: solved
              subject: Software access request - Adobe Creative Suite
              tags:
                - software_access
              type: task
              updated_at: '2025-09-18T16:45:00Z'
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-08-22T14:15:00Z'
              description: Need access to marketing template folder for upcoming client proposal
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '1389'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: solved
              subject: Box folder access - Marketing templates
              tags:
                - document_access
              type: task
              updated_at: '2025-08-23T11:20:00Z'
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: simon.johnson@msg.com
              id: '8'
              name: Simon Johnson
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: simon.johnson@msg.com
              tool: workday_api
            - parameters:
                $filter: requester_id eq '8' and status in ('open','pending','hold')
                $orderby: null
                $select: null
                $skip: null
                $top: 5
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee reports work phone (15 months old) was stolen during business trip. Police report filed.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: urgent
                  requester_id: '8'
                  status: open
                  subject: Stolen phone replacement request
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: get_employee_devices
                asset_id: null
                device_type: null
                email: simon.johnson@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                action: get_device_details
                asset_id: MSG84729163
                device_type: null
                email: null
                location: null
              tool: asset_management_api
            - parameters:
                action: check_inventory
                asset_id: null
                device_type: phone
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                email: rachel.martinez@msg.com
              tool: approver_lookup_get_contact
            - parameters:
                amount: null
                approver_email: rachel.martinez@msg.com
                engagement_code: null
                request_type: hardware_replacement
                requester_email: simon.johnson@msg.com
              tool: approval_create_request
            - parameters:
                id: '8'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: rachel.martinez@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: phone
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am Sarah Martinez, my email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). I made a phone replacement request two weeks ago, my current iPhone 13 is 26 months old, battery health is 75%, and there's no physical damage. I know there are no phones in stock at the Chicago office, can you provide an update on when I might receive my phone replacement?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG84729163
              employee_email: sarah.martinez@msg.com
              id: DA-8472916
              returned_at: null
          asset_management_devices:
            - age_months: 26
              device_type: phone
              id: MSG84729163
              inventory_status: assigned
              location: Chicago
              model: iPhone 13
            - age_months: 0
              device_type: phone
              id: MSG94738251
              inventory_status: available
              location: New York
              model: iPhone 14
            - age_months: 0
              device_type: phone
              id: MSG85729463
              inventory_status: available
              location: San Francisco
              model: iPhone 14
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: jennifer.williams@msg.com
              level: Partner
              manager_email: jennifer.williams@msg.com
              name: Jennifer Williams
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2019-01-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: 'no'
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-17T09:30:00Z'
              description: Requesting phone replacement due to poor battery health. Current device is 26 months old with battery health at 75%. No physical damage reported.
              device_type: phone
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '2847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: pending
              subject: Phone Replacement Request - Battery Health 75%
              tags:
                - hardware_request
              type: task
              updated_at: '2025-09-17T11:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T10:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: (813) 492-7584
              role: end-user
              updated_at: '2025-09-15T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                deliver_to: Chicago
                device_model: iPhone 13
                quantity: 1
              tool: hardware_procurement_create_order
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: No phones are currently in stock at the Chicago office. A procurement order has been placed for a replacement device. The expected delivery timeline is 14 days. Once inventory is replenished, your replacement phone will ship within 1-2 business days. Your request remains pending until inventory is available.
                  device_type: phone
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: HWO-0056435
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to request a replacement for my company phone. My current device is an iPhone 14, it's 22 months old and the battery health is at 83%. There is no physical damage. My direct manager is currently on leave, but the request has already been approved by the designated backup approver. Can I get a new phone from our Chicago office inventory? My work email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com).
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: null
              approver_email: jennifer.davis@msg.com
              engagement_code: null
              id: APR-9384751
              request_type: hardware_replacement
              requester_email: sarah.martinez@msg.com
              status: approved
          asset_management_device_assignments:
            - asset_id: MSG47382951
              employee_email: sarah.martinez@msg.com
              id: ASSGN-8472951
              returned_at: null
          asset_management_devices:
            - age_months: 22
              device_type: phone
              id: MSG47382951
              inventory_status: assigned
              location: Chicago
              model: iPhone 14
            - age_months: 0
              device_type: phone
              id: MSG58394726
              inventory_status: available
              location: Chicago
              model: iPhone 15
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: jennifer.davis@msg.com
              email: sarah.martinez@msg.com
              level: Senior Consultant
              manager_email: michael.thompson@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: robert.chen@msg.com
              start_date: '2022-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: jennifer.davis@msg.com
                  asset_id: MSG58394726
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee requests replacement for iPhone 14 (22 months old, 83% battery, no damage). New iPhone 15 assigned. Old device MSG47382951 marked for return.
                  device_type: phone
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Phone replacement request - iPhone 14 (83% battery)
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: check_inventory
                asset_id: null
                device_type: phone
                email: sarah.martinez@msg.com
                location: Chicago
              tool: asset_management_api
            - parameters:
                approver_email: jennifer.davis@msg.com
                engagement_code: null
                request_type: hardware_replacement
                requester_email: sarah.martinez@msg.com
              tool: approval_get_status
            - parameters:
                action: reserve_device
                asset_id: null
                device_type: phone
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: assign_device
                asset_id: MSG58394726
                device_type: phone
                email: sarah.martinez@msg.com
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: retire_device
                asset_id: MSG47382951
                device_type: phone
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  active: null
                  approval_required: 'yes'
                  approver_id: jennifer.davis@msg.com
                  asset_id: MSG58394726
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee requests replacement for iPhone 14 (22 months old, 83% battery, no damage). New iPhone 15 assigned. Old device MSG47382951 marked for return.
                  device_type: phone
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: solved
                  subject: Phone replacement request - iPhone 14 (83% battery)
                  tags:
                    - hardware_request
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, My name is David Martinez,email : [david.martinez@msg.com](mailto:david.martinez@msg.com) and I'd like to request a replacement for my current Dell Latitude laptop. It's about 40 months old and still works, but I'd like to refresh to a newer Windows laptop. Can you help me get a new laptop?
    user_context: |
        Office Location is Chicago

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG84729163
              employee_email: david.martinez@msg.com
              id: DA-8472916
          asset_management_devices:
            - age_months: 40
              device_type: laptop
              id: MSG84729163
              inventory_status: assigned
              location: Chicago
              model: Dell Latitude 5520
            - age_months: 0
              device_type: laptop
              id: MSG95847261
              inventory_status: available
              location: Chicago
              model: Dell Latitude 7420
            - age_months: 0
              device_type: laptop
              id: MSG95847262
              inventory_status: available
              location: Chicago
              model: Dell Latitude 7420
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2020-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2018-08-20T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2020-03-15T10:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              phone: null
              role: end-user
              updated_at: '2025-09-15T14:30:00Z'
              verified: false
            - active: true
              created_at: '2018-08-20T10:00:00Z'
              email: sarah.thompson@msg.com
              id: '13'
              name: Sarah Thompson
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-20T16:45:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                $filter: email eq 'david.martinez@msg.com'
                $orderby: null
                $select: id, email
                $skip: null
                $top: 1
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8' and (status eq 'open' or status eq 'hold' or status eq 'pending')
                $orderby: null
                $select: id,subject,status
                $skip: null
                $top: 10
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Manager requested a standard Windows laptop refresh. Current Dell Latitude 5520 is 40 months old. IT will validate eligibility, reserve Chicago inventory, assign replacement, and retire old device.
                  device_type: laptop
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Laptop replacement request - Dell Latitude replacement
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                action: get_employee_devices
                asset_id: null
                device_type: laptop
                email: david.martinez@msg.com
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: get_device_details
                asset_id: MSG84729163
                device_type: null
                email: david.martinez@msg.com
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: check_inventory
                asset_id: null
                device_type: laptop
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: reserve_device
                asset_id: null
                device_type: laptop
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: assign_device
                asset_id: MSG00005002
                device_type: laptop
                email: david.martinez@msg.com
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: retire_device
                asset_id: MSG84729163
                device_type: laptop
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: MSG00005002
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Manager laptop refresh request completed. Old laptop wil be retired and the new one will be available for pick up at IT. Manager to return old laptop at IT. '
                  device_type: laptop
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: null
                  status: solved
                  subject: Laptop replacement request - Dell Latitude replacement-completed
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez, [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). My laptop was damaged when my bag fell—the screen is cracked and the hinges are broken, however it is partially working. Can I get a replacement standard Windows laptop? I spoke to my manager and he is available, can you resolve this issue today?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG84729163
              employee_email: sarah.martinez@msg.com
              id: ASGN-8472916
              returned_at: null
          asset_management_devices:
            - age_months: 30
              device_type: laptop
              id: MSG84729163
              inventory_status: assigned
              location: Austin
              model: Dell Latitude 5520
            - age_months: 0
              device_type: laptop
              id: MSG95738241
              inventory_status: available
              location: Austin
              model: Dell Latitude 5530
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: alex.williams@msg.com
              name: Sarah Martinez
              office_location: Austin
              onboarding_phase: completed
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: alex.williams@msg.com
              level: Manager
              manager_email: michael.chen@msg.com
              name: Alex Williams
              office_location: Austin
              onboarding_phase: completed
              partner_email: michael.chen@msg.com
              start_date: '2023-01-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Sarah Martinez reports her Dell Latitude 5520 (asset_id: MSG84729163, 30 months old, Austin) was damaged: screen cracked, hinges broken. Requesting standard Windows laptop replacement.'
                  device_type: laptop
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: Laptop replacement request due to physical damage
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                approver_email: alex.williams@msg.com
                request_type: hardware_replacement
                requester_email: sarah.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: alex.williams@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I lost my ThinkPad laptop in a taxi over a week ago and still haven't received a replacement. My previous ticket was marked as solved and my manager has already approved the request, but I never got a new laptop.  My old device was 24 months old, and I need a standard Windows laptop for work. Can you help me get a replacement from the Chicago office inventory? For your reference, my name is David Martinez and my email is [david.martinez@msg.com](mailto:david.martinez@msg.com)
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: null
              approver_email: sarah.thompson@msg.com
              engagement_code: null
              id: APR-4837291
              request_type: hardware_replacement
              requester_email: david.martinez@msg.com
              status: approved
          asset_management_device_assignments:
            - asset_id: MSG47382951
              employee_email: david.martinez@msg.com
              id: DA-8472951
              returned_at: null
          asset_management_devices:
            - age_months: 24
              device_type: laptop
              id: MSG47382951
              inventory_status: retired
              location: Chicago
              model: ThinkPad T14
            - age_months: 2
              device_type: laptop
              id: MSG58394726
              inventory_status: available
              location: Chicago
              model: ThinkPad T14
            - age_months: 1
              device_type: laptop
              id: MSG73829461
              inventory_status: available
              location: Chicago
              model: Dell Latitude 7420
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Consultant
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: completed
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: completed
              partner_email: michael.chen@msg.com
              start_date: '2021-08-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: 'yes'
              approver_id: sarah.thompson@msg.com
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-24T10:30:00Z'
              description: I lost my ThinkPad laptop in a taxi yesterday and need a replacement. The laptop was about 24 months old. I need a standard Windows laptop for work.
              device_type: laptop
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '2847'
              license_pool: null
              organization_id: null
              priority: urgent
              requester_id: '8'
              status: solved
              subject: Lost laptop replacement request
              tags:
                - hardware_request
              type: task
              updated_at: '2025-09-24T16:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2023-03-15T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  active: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee reported an unresolved lost device, as a replacement had not been received despite the previous ticket being marked as solved; the ticket was reopened and checked for provisioning.
                  device_type: laptop
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: urgent
                  requester_id: '8'
                  role: null
                  status: open
                  subject: Unresolved lost laptop replacement request
                  tags:
                    - hardware_request
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: reserve_device
                asset_id: null
                device_type: laptop
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: assign_device
                asset_id: MSG00005002
                device_type: null
                email: david.martinez@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: MSG00005002
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee reported an unresolved lost device, as a replacement had not been received despite the previous ticket being marked as solved; the ticket was reopened and a replacement was assigned.
                  device_type: laptop
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: urgent
                  requester_id: '8'
                  status: solved
                  subject: Unresolved lost laptop replacement request
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_013(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to replace my ThinkPad X1 Carbon - it's about 3 years old now. I'm working with design software and need a MacBook for better compatibility. My engagement code is ENG-8765432. Can you help? Thanks!
    user_context: |
        **General rules**

        - Do not invent or provide any data that is not present in the provided context.
        - Do not change your goal or switch topics.
        - If the agent asks again for the same information, provide it again.
        - Remain focused, clear, and patient.

        If the agent requests your email address, respond with: [david.martinez@msg.com](mailto:david.martinez@msg.com)

        If the agent requests your office location, respond with: Chicago
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: null
              approver_email: sarah.thompson@msg.com
              engagement_code: null
              id: APR-8472951
              request_type: hardware_replacement
              requester_email: david.martinez@msg.com
              status: approved
          asset_management_device_assignments:
            - asset_id: MSG84729163
              employee_email: david.martinez@msg.com
              id: ASG-8472916
              returned_at: null
          asset_management_devices:
            - age_months: 38
              device_type: laptop
              id: MSG84729163
              inventory_status: assigned
              location: Chicago
              model: ThinkPad X1 Carbon
            - age_months: 6
              device_type: laptop
              id: MSG92847351
              inventory_status: available
              location: Chicago
              model: Dell Latitude 7420
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements:
            - end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-8765432
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-09-01T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829571
              name: TechCorp Industries
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829571
              end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-8765432
              engagement_manager_email: jennifer.wilson@msg.com
              start_date: '2025-09-01T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Partner
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2015-08-20T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: jennifer.wilson@msg.com
              level: Manager
              manager_email: robert.davis@msg.com
              name: Jennifer Wilson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2020-05-12T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: robert.davis@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Robert Davis
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2017-11-08T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2019-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Employee requests laptop replacement. Current device: ThinkPad X1 Carbon (38 months old). Non-standard device request denied due to invalid engagement assignment. Standard laptop approved based on device age eligibility.'
                  device_type: laptop
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Laptop Replacement Request
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: reserve_device
                asset_id: null
                device_type: laptop
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: assign_device
                asset_id: MSG00005002
                device_type: null
                email: david.martinez@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                action: retire_device
                asset_id: MSG84729163
                device_type: null
                email: null
                location: null
              tool: asset_management_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: MSG00005002
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am David Martinez, my email address is [david.martinez@msg.com](mailto:david.martinez@msg.com). My Dell Latitude laptop is only 32 months old, but it's having critical performance issues—it freezes often, takes over 10 minutes to boot, and applications crash regularly. Can I get a replacement standard Windows laptop from the Chicago office inventory? My manager Sarah Thompson (sarah.thompson@msg.com) is available.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG84729163
              employee_email: david.martinez@msg.com
              id: ASSGN-8472916
              returned_at: null
          asset_management_devices:
            - age_months: 32
              device_type: laptop
              id: MSG84729163
              inventory_status: assigned
              location: Chicago
              model: Dell Latitude 5520
            - age_months: 0
              device_type: laptop
              id: MSG95847261
              inventory_status: available
              location: Chicago
              model: Dell Latitude 5530
            - age_months: 0
              device_type: laptop
              id: MSG73829164
              inventory_status: available
              location: Chicago
              model: ThinkPad T14
            - age_months: 0
              device_type: laptop
              id: MSG46182739
              inventory_status: available
              location: Chicago
              model: Dell Latitude 5540
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-08-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: (813) 492-7583
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Employee requests replacement of Dell Latitude (asset ID MSG84729163, 32 months old) due to critical performance issues: frequent freezes, 10+ min boot, app crashes. Standard Windows laptop requested from Chicago inventory.'
                  device_type: laptop
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: high
                  requester_id: '8'
                  status: open
                  subject: Laptop replacement request - critical performance issues (Dell Latitude, 32 months)
                  tags:
                    - hardware_request
                  type: problem
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: null
                approver_email: sarah.thompson@msg.com
                engagement_code: null
                request_type: hardware_replacement
                requester_email: david.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: laptop
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags:
                    - hardware_request
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_015(x: TestContext, judge: Judge):
    """!
    query: |
        Hi! My name is Sarah Martinez, [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). I would like to replace my current ThinkPad X1 Carbon laptop, with a MacBook for video editing. Can I get a MacBook instead of a standard Windows laptop? I cannot provide you with an engagement code. I opened a request about this a few days ago.
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: null
              approver_email: michael.chen@msg.com
              engagement_code: null
              id: APR-5829473
              request_type: hardware_replacement
              requester_email: sarah.martinez@msg.com
              status: approved
          asset_management_device_assignments:
            - asset_id: MSG47382951
              employee_email: sarah.martinez@msg.com
              id: ASN-2847391
              returned_at: null
          asset_management_devices:
            - age_months: 44
              device_type: laptop
              id: MSG47382951
              inventory_status: assigned
              location: Austin
              model: ThinkPad X1 Carbon
            - age_months: 2
              device_type: laptop
              id: MSG07501071
              inventory_status: available
              location: Austin
              model: Dell Latitude 7430
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Senior Consultant
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Austin
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2022-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: 'no'
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-29T10:30:00Z'
              description: My current ThinkPad X1 Carbon is experiencing significant performance issues and is 44 months old. I would like to request a laptop replacement as it qualifies for the refresh cycle.
              device_type: laptop
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '2847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: pending
              subject: Laptop replacement request - ThinkPad performance issues
              tags:
                - hardware_request
              type: task
              updated_at: '2025-09-29T10:30:00Z'
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
            - active: true
              created_at: '2019-08-12T09:00:00Z'
              email: michael.chen@msg.com
              id: '13'
              name: Michael Chen
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-25T16:45:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                $filter: email eq 'sarah.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: get_employee_devices
                asset_id: null
                device_type: null
                email: sarah.martinez@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                action: check_inventory
                asset_id: null
                device_type: laptop
                email: null
                location: Austin
              tool: asset_management_api
            - parameters:
                action: reserve_device
                asset_id: null
                device_type: laptop
                email: null
                location: Austin
              tool: asset_management_api
            - parameters:
                action: assign_device
                asset_id: MSG07501071
                device_type: null
                email: sarah.martinez@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                action: retire_device
                asset_id: MSG47382951
                device_type: null
                email: null
                location: null
              tool: asset_management_api
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: MSG07501071
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_016(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my Dell Latitude laptop is now 36 months old and it's starting to slow down. Can I get a replacement standard Windows laptop? I'm based in Chicago and my email is [Sarah.martinez@msg.com](mailto:Sarah.martinez@msg.com).
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG84729163
              employee_email: sarah.martinez@msg.com
              id: ASSGN-8472916
              returned_at: null
          asset_management_devices:
            - age_months: 36
              device_type: laptop
              id: MSG84729163
              inventory_status: assigned
              location: Chicago
              model: Dell Latitude 7420
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2021-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2021-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                $filter: user_email
                $orderby: null
                $select: Sarah.martinez@msg.com
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: get_employee_devices
                asset_id: null
                device_type: null
                email: sarah.martinez@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                action: get_device_details
                asset_id: MSG84729163
                device_type: null
                email: null
                location: null
              tool: asset_management_api
            - parameters:
                brand_id: null
                category: null
                label_names: null
                locale: null
                multibrand: null
                query: Laptop Replacement Eligibility
                section: null
              tool: zendesk_search_articles
            - parameters:
                action: check_inventory
                asset_id: null
                device_type: laptop
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                brand_id: null
                category: null
                label_names: null
                locale: null
                multibrand: null
                query: Laptop Procurement Lead times
                section: null
              tool: zendesk_search_articles
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                deliver_to: Chicago
                device_model: Dell Latitude 7420
                quantity: 1
              tool: hardware_procurement_create_order
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee requests standard Windows laptop replacement (Dell Latitude) at 36 months. No standard laptops in Chicago inventory. Procurement order placed; lead time 18 days. Employee advised to return after inventory replenishment.
                  device_type: laptop
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Laptop replacement request - no standard inventory available in Chicago
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  active: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee requests standard Windows laptop replacement (Dell Latitude) at 36 months. No standard laptops in Chicago inventory. Procurement order placed; lead time 18 days. Employee advised to return after inventory replenishment.
                  device_type: laptop
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: HWO-0056435
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: pending
                  subject: Laptop replacement request - no standard inventory available in Chicago
                  tags:
                    - hardware_request
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_019(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Michael Rodriguez, a Senior Manager in the Chicago office. I'd like to request a monitor for my home office setup. Can you help me with this?
    user_context: |
        Your email is [michael.rodriguez@msg.com](mailto:michael.rodriguez@msg.com)


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices:
            - age_months: 13
              device_type: monitor
              id: MSG84729163
              inventory_status: available
              location: Chicago
              model: Dell UltraSharp U2723QE
            - age_months: 11
              device_type: monitor
              id: MSG84729164
              inventory_status: available
              location: Chicago
              model: Dell UltraSharp U2723QE
            - age_months: 9
              device_type: monitor
              id: MSG84729165
              inventory_status: available
              location: Chicago
              model: LG 27UP850-W
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: michael.rodriguez@msg.com
              level: Senior Manager
              manager_email: sarah.chen@msg.com
              name: Michael Rodriguez
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.thompson@msg.com
              start_date: '2019-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2019-03-15T09:00:00Z'
              email: michael.rodriguez@msg.com
              id: '8'
              name: Michael Rodriguez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Senior Manager Michael Rodriguez requests a monitor for his home office setup. Chicago office inventory available.
                  device_type: monitor
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Monitor request for home office setup
                  tags:
                    - hardware_request
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: reserve_device
                asset_id: null
                device_type: monitor
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: assign_device
                asset_id: MSG84729163
                device_type: null
                email: michael.rodriguez@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: MSG84729163
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Monitor assigned to Michael Rodriguez. Asset ID: MSG84729163. Request fulfilled.'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_hwa_020(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I requested a docking station for my desk a while ago. Any update on when it will arrive?
    user_context: |
        Rules:

        - Do not invent or provide any data that is not present in the provided context.

        - Do not change your goal or switch topics.

        - If the agent asks again for the same information, provide it again.

        - Remain focused, clear, and patient.



        You are Elena Torres. You work at the New York office as an Analyst. About 10 days ago, you requested a docking station for your desk, but you never received it. You are now following up to ask when it will arrive. Your email is [elena.torres@msg.com](mailto:elena.torres@msg.com). If the agent asks for any ID or details, provide your email. If the agent confirms the order is still in progress, acknowledge and ask for the expected delivery date.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: elena.torres@msg.com
              level: Analyst
              manager_email: sarah.johnson@msg.com
              name: Elena Torres
              office_location: New York
              onboarding_phase: completed
              partner_email: richard.williams@msg.com
              start_date: '2024-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-21T10:00:00Z'
              description: I need a docking station for my desk setup.
              device_type: docking_station
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: HWO-1000001
              id: '50'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '20'
              status: pending
              subject: Docking station request
              tags:
                - hardware_request
              type: task
              updated_at: '2025-09-21T10:00:00Z'
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: elena.torres@msg.com
              id: '20'
              name: Elena Torres
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-03-15T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: elena.torres@msg.com
              tool: workday_api
            - parameters:
                $filter: email eq 'elena.torres@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '20'
                $orderby: created_at desc
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                id: '50'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: check_inventory
                asset_id: null
                device_type: docking_station
                email: null
                location: New York
              tool: asset_management_api
            - parameters:
                id: '50'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_onb_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez, e-mail [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). I'm a new hire, just started in the Chicago office. I haven't received my laptop or access to company systems yet (Workday, Slack, Microsoft Office, Zoom). Can you help me with getting these?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices:
            - age_months: 13
              device_type: laptop
              id: MSG00005003
              inventory_status: available
              location: Chicago
              model: Dell Latitude 7440
            - age_months: 11
              device_type: laptop
              id: MSG00005004
              inventory_status: available
              location: Chicago
              model: Dell Latitude 7440
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: day_1_3_initial
              partner_email: richard.williams@msg.com
              start_date: '2025-09-30T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2025-09-30T08:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: +1-312-674-0198
              role: end-user
              updated_at: '2025-09-30T08:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                $filter: email eq 'sarah.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: New hire Sarah Martinez (Analyst, Chicago) requests Phase 1 onboarding setup. No laptop assigned.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: 'Onboarding Phase 1: Core systems setup for new hire Sarah Martinez'
                  tags:
                    - onboarding
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: check_inventory
                asset_id: null
                device_type: laptop
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: get_employee_devices
                asset_id: null
                device_type: null
                email: sarah.martinez@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                action: reserve_device
                asset_id: null
                device_type: laptop
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: assign_device
                asset_id: MSG00005002
                device_type: null
                email: sarah.martinez@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                access_type: full_access
                app_name: Workday
                email: sarah.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                access_type: full_access
                app_name: Slack
                email: sarah.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                access_type: full_access
                app_name: Microsoft Office
                email: sarah.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                access_type: full_access
                app_name: Zoom
                email: sarah.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                id: '6'
                item:
                  access_type: full_access
                  approval_required: null
                  approver_id: null
                  asset_id: MSG00005002
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Completed software onboarding for new hire Sarah Martinez. Laptop has been assigned
                  device_type: laptop
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: Completed core systems setup for new hire Sarah Martinez
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_onb_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I’m Sarah Martinez [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). I’m a new hire Consultant and I started on 9/29. I contacted IT yesterday because I still don’t have a company laptop or my onboarding access set up. Can you tell me what’s happening with my laptop request and help me get access to Office 365, Slack, Zoom, and Workday?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices:
            - age_months: 14
              device_type: laptop
              id: MSG84729301
              inventory_status: available
              location: New York
              model: Dell Latitude 5530
            - age_months: 18
              device_type: laptop
              id: MSG84729302
              inventory_status: available
              location: San Francisco
              model: ThinkPad T14
            - age_months: 12
              device_type: laptop
              id: MSG84729303
              inventory_status: available
              location: Austin
              model: Dell Latitude 5530
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Consultant
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: day_1_3_initial
              partner_email: richard.williams@msg.com
              start_date: '2025-09-29T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-30T14:30:00Z'
              description: 'New hire (Consultant, start date 2025-09-29, Day 1) requesting Phase 1 onboarding setup including laptop assignment and core system access. Workday shows no application access provisioned and no laptop assigned. Office location: Chicago. Ticket is pending while laptop assignment/shipment is arranged.'
              device_type: laptop
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '2847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: pending
              subject: Phase 1 Onboarding Setup - Laptop and System Access
              tags:
                - onboarding
              type: task
              updated_at: '2025-09-30T16:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2025-09-29T08:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-29T08:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  active: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: laptop
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: null
                  role: null
                  status: open
                  subject: null
                  tags:
                    - onboarding
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: reserve_device
                asset_id: null
                device_type: laptop
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: assign_device
                asset_id: MSG00005002
                device_type: null
                email: sarah.martinez@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                access_type: full_access
                app_name: Office 365
                email: sarah.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                access_type: full_access
                app_name: Slack
                email: sarah.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                access_type: full_access
                app_name: Zoom
                email: sarah.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                access_type: full_access
                app_name: Workday
                email: sarah.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                id: '2847'
                item:
                  access_type: full_access
                  active: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: MSG00005002
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Phase 1 onboarding completed. Laptop assigned from Chicago inventory (asset MSG00005002). Access provisioned: Office 365, Slack, Zoom, Workday. If the user experiences login issues, reopen ticket and troubleshoot.'
                  device_type: laptop
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: null
                  role: null
                  status: solved
                  subject: null
                  tags:
                    - onboarding
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_onb_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm a new hire and some of my apps aren't working yet. I started on September 28 and I'm in the New York office. I have access to Workday and email, but I can't use Slack, Microsoft Office, or Zoom. Can you help complete my onboarding setup?
    user_context: |
        You are Analyst, your name is Tomas Mets, email [tomas.mets@msg.com](mailto:tomas.mets@msg.com)

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG84729183
              employee_email: tomas.mets@msg.com
              id: DA-8472918
              returned_at: null
          asset_management_devices:
            - age_months: 6
              device_type: laptop
              id: MSG84729183
              inventory_status: assigned
              location: New York
              model: Dell Latitude 5530
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs:
            - access_type: null
              app_name: Workday
              employee_email: tomas.mets@msg.com
              id: OAL-8472918
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: tomas.mets@msg.com
              level: Analyst
              manager_email: sarah.johnson@msg.com
              name: Tomas Mets
              office_location: New York
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2025-09-28T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2025-09-28T09:00:00Z'
              email: tomas.mets@msg.com
              id: '8'
              name: Tomas Mets
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: New hire Tomas Mets (Analyst, Day 3, New York office) reports only Workday and email are enabled. Slack, Microsoft Office, and Zoom are missing. Laptop is assigned. Requesting completion of Phase 1 onboarding setup.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Onboarding Phase 1 - Core systems access incomplete (Slack, Office, Zoom)
                  tags:
                    - onboarding
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                access_type: null
                app_name: Slack
                email: tomas.mets@msg.com
              tool: okta_provision_access
            - parameters:
                access_type: null
                app_name: Microsoft Office
                email: tomas.mets@msg.com
              tool: okta_provision_access
            - parameters:
                access_type: null
                app_name: Zoom
                email: tomas.mets@msg.com
              tool: okta_provision_access
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_onb_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I have an open ticket to complete Phase 2 of my onboarding. You enrolled me in the first two courses, but I had to leave before we could do the other two. Could you help me enroll in Data Privacy and Anti-harassment? Also: I haven't finished any of them yet, but do I need to contact you again when I'm done so you can close the ticket?
    user_context: |
        You are Billy Bishop. Your email is [billy.bishop@msg.com](mailto:billy.bishop@msg.com).



        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices:
            - age_months: 6
              device_type: laptop
              id: MSG35679516
              inventory_status: assigned
              location: San Francisco
              model: Dell Latitude 7420
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: null
              id: CRS-1001001
              max_seats: null
              prerequisites: []
              start_date: null
              title: Ethics & Code of Conduct
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001002
              max_seats: null
              prerequisites: []
              start_date: null
              title: Security Awareness
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001003
              max_seats: null
              prerequisites: []
              start_date: null
              title: Data Privacy
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001004
              max_seats: null
              prerequisites: []
              start_date: null
              title: Anti-harassment
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: null
              course_id: CRS-1001001
              employee_email: billy.bishop@msg.com
              id: ENR-2556391
            - completion_date: null
              course_id: CRS-1001002
              employee_email: billy.bishop@msg.com
              id: ENR-2556392
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs:
            - access_type: null
              app_name: Workday
              employee_email: billy.bishop@msg.com
              id: LOG-8472951
            - access_type: null
              app_name: Slack
              employee_email: billy.bishop@msg.com
              id: LOG-8472952
            - access_type: null
              app_name: Microsoft Office
              employee_email: billy.bishop@msg.com
              id: LOG-8472953
            - access_type: null
              app_name: Zoom
              employee_email: billy.bishop@msg.com
              id: LOG-8472954
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: billy.bishop@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Billy Bishop
              office_location: San Francisco
              onboarding_phase: day_3_7_provisioning
              partner_email: jennifer.williams@msg.com
              start_date: '2025-09-25T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: 'no'
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: CRS-1001001,CRS-1001002
              created_at: '2025-09-29T14:30:00Z'
              description: 'Enrolled: Ethics & Code of Conduct, Security Awareness. Not yet enrolled: Data Privacy, Anti-harassment. Completed: None.'
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '1847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: open
              subject: Mandatory Phase 2 onboarding training
              tags:
                - onboarding
              type: task
              updated_at: '2025-09-29T14:30:00Z'
          zendesk_users:
            - active: true
              created_at: '2025-09-25T09:00:00Z'
              email: billy.bishop@msg.com
              id: '8'
              name: Billy Bishop
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-25T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                $filter: email eq 'billy.bishop@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                action: get_employee
                email: billy.bishop@msg.com
              tool: workday_api
            - parameters:
                $filter: requester_id eq '8'
                $orderby: id desc
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: enroll_employee
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-1001003
                email: billy.bishop@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                action: enroll_employee
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-1001004
                email: billy.bishop@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                id: '1847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: CRS-1001001,CRS-1001002,CRS-1001003,CRS-1001004
                  description: 'Enrolling Billy Bishop in mandatory Phase 2 onboarding training. Enrollment is complete for all 4 courses. Now waiting on Billy Bishop to finish his training. '
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_onb_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi! this is David Martinez (david.martinez@msg.com). I'm following up on my existing pending ticket #2847 regarding Phase 3 access to Concur and Salesforce. I have completed all 4 mandatory onboarding courses. I've confirmed with HR that for Phase 3 standard provisioning, NO engagement code is required. Please allocate licenses and activate my full access immediately.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: null
              id: CRS-1001234
              max_seats: null
              prerequisites: []
              start_date: null
              title: Ethics & Code of Conduct
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001235
              max_seats: null
              prerequisites: []
              start_date: null
              title: Security Awareness
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001236
              max_seats: null
              prerequisites: []
              start_date: null
              title: Data Privacy
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001237
              max_seats: null
              prerequisites: []
              start_date: null
              title: Anti-harassment
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2025-09-27T00:00:00'
              course_id: CRS-1001234
              employee_email: david.martinez@msg.com
              id: ENR-2847001
            - completion_date: '2025-09-27T00:00:00'
              course_id: CRS-1001235
              employee_email: david.martinez@msg.com
              id: ENR-2847002
            - completion_date: '2025-09-27T00:00:00'
              course_id: CRS-1001236
              employee_email: david.martinez@msg.com
              id: ENR-2847003
            - completion_date: '2025-09-27T00:00:00'
              course_id: CRS-1001237
              employee_email: david.martinez@msg.com
              id: ENR-2847004
          license_management_license_allocation: []
          license_management_license_pool_record:
            - catalog_id: CAT-1847293
              pool_type: enterprise
              total_licenses: 500
            - catalog_id: CAT-2948571
              pool_type: enterprise
              total_licenses: 400
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog:
            - annual_cost: 180
              id: CAT-1847293
              name: Concur
              pool_type: enterprise
            - annual_cost: 240
              id: CAT-2948571
              name: Salesforce
              pool_type: enterprise
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: San Francisco
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2025-09-23T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-28T14:30:00Z'
              description: Requesting access to expense and CRM systems as part of Phase 3 onboarding provisioning. Phase 1 and Phase 2 are complete, all mandatory training courses have been completed.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '2847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: pending
              subject: Phase 3 Onboarding - Role-Based Software Access
              tags:
                - onboarding
              type: task
              updated_at: '2025-09-28T14:30:00Z'
          zendesk_users:
            - active: true
              created_at: '2025-09-23T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-23T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '2847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: allocate
                catalog_id: CAT-1847293
                email: david.martinez@msg.com
                engagement_code: null
                pool_type: enterprise
              tool: license_management_api
            - parameters:
                action: allocate
                catalog_id: CAT-2948571
                email: david.martinez@msg.com
                engagement_code: null
                pool_type: enterprise
              tool: license_management_api
            - parameters:
                access_type: full_access
                app_name: Concur
                email: david.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                access_type: full_access
                app_name: Salesforce
                email: david.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                id: '2847'
                item:
                  access_type: full_access
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: CAT-1847293,CAT-2948571
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: enterprise
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)




def test_onb_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez. My email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com)
        I started on September 24 and I'm on Day 7 of onboarding. I completed Ethics & Code of Conduct and Data Privacy trainings, but Security Awareness and Anti-harassment are still in progress. I was enrolled for all 4 trainings. When can I get access to Concur for expense reporting?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: null
              id: CRS-1001001
              max_seats: null
              prerequisites: []
              start_date: null
              title: Ethics & Code of Conduct
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001002
              max_seats: null
              prerequisites: []
              start_date: null
              title: Security Awareness
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001003
              max_seats: null
              prerequisites: []
              start_date: null
              title: Data Privacy
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001004
              max_seats: null
              prerequisites: []
              start_date: null
              title: Anti-harassment
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2025-09-28T15:30:00Z'
              course_id: CRS-1001001
              employee_email: sarah.martinez@msg.com
              id: ENR-2847391-001
            - completion_date: null
              course_id: CRS-1001002
              employee_email: sarah.martinez@msg.com
              id: ENR-2847391-002
            - completion_date: '2025-09-29T11:45:00Z'
              course_id: CRS-1001003
              employee_email: sarah.martinez@msg.com
              id: ENR-2847391-003
            - completion_date: null
              course_id: CRS-1001004
              employee_email: sarah.martinez@msg.com
              id: ENR-2847391-004
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog:
            - annual_cost: 0
              id: CAT-1001001
              name: Concur
              pool_type: enterprise
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2025-09-24T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-27T14:30:00Z'
              description: New hire requesting Concur access for expense reporting as part of Phase 3 onboarding provisioning.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '1247'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: pending
              subject: Phase 3 Onboarding - Concur Access Request
              tags:
                - onboarding
              type: task
              updated_at: '2025-09-27T14:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2025-09-24T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-24T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                action: get_training_history
                category: must_have
                certification_name: null
                client_id: null
                course_id: CRS-1001001
                email: sarah.martinez@msg.com
                keyword: Ethics & Code of Conduct
              tool: degreed_api
            - parameters:
                action: get_training_history
                category: must_have
                certification_name: null
                client_id: null
                course_id: CRS-1001002
                email: sarah.martinez@msg.com
                keyword: Security Awareness
              tool: degreed_api
            - parameters:
                action: get_training_history
                category: must_have
                certification_name: null
                client_id: null
                course_id: CRS-1001003
                email: sarah.martinez@msg.com
                keyword: Data Privacy
              tool: degreed_api
            - parameters:
                action: get_training_history
                category: must_have
                certification_name: null
                client_id: null
                course_id: CRS-1001004
                email: sarah.martinez@msg.com
                keyword: Anti-harassment
              tool: degreed_api
            - parameters:
                id: '1247'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Concur access (Phase 3 onboarding) cannot be provisioned until all four mandatory trainings are completed. Ethics & Code of Conduct and Data Privacy are complete; Security Awareness and Anti-harassment are still in progress. Request remains pending until all trainings are finished.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Phase 3 Onboarding - Concur Access Request
                  tags:
                    - onboarding
                  type: task
                table: tickets
              tool: zendesk_update_item
            - parameters:
                id: '1247'
                item:
                  access_type: null
                  active: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Concur access (Phase 3 onboarding) cannot be provisioned until all four mandatory trainings are completed. Ethics & Code of Conduct and Data Privacy are complete; Security Awareness and Anti-harassment are still in progress. Request remains pending until all trainings are finished.
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: pending
                  subject: Phase 3 Onboarding - Concur Access Request
                  tags:
                    - onboarding
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_onb_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm David Martinez, email is [david.martinez@msg.com](mailto:david.martinez@msg.com) I started on September 22 and I'm on Day 9 of onboarding. I've completed Phase 1 and received my laptop. Can you please provision Phase 3 software access for me now? have not completed Phase 2 trainings yet. I have not been enrolled to Phase 2 trainings yet.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG84729163
              employee_email: david.martinez@msg.com
              id: DA-8472916
              returned_at: null
          asset_management_devices:
            - age_months: 0
              device_type: laptop
              id: MSG84729163
              inventory_status: assigned
              location: New York
              model: Dell Latitude 7420
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: null
              id: CRS-1001001
              max_seats: null
              prerequisites: []
              start_date: null
              title: Ethics & Code of Conduct
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001002
              max_seats: null
              prerequisites: []
              start_date: null
              title: Security Awareness
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001003
              max_seats: null
              prerequisites: []
              start_date: null
              title: Data Privacy
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001004
              max_seats: null
              prerequisites: []
              start_date: null
              title: Anti-harassment
              training_category: must_have
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs:
            - access_type: null
              app_name: Workday
              employee_email: david.martinez@msg.com
              id: OAL-8472916
            - access_type: null
              app_name: Slack
              employee_email: david.martinez@msg.com
              id: OAL-8472917
            - access_type: null
              app_name: Microsoft Office
              employee_email: david.martinez@msg.com
              id: OAL-8472918
            - access_type: null
              app_name: Zoom
              employee_email: david.martinez@msg.com
              id: OAL-8472919
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog:
            - annual_cost: 0
              id: CAT-2001001
              name: Concur
              pool_type: enterprise
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Consultant
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: New York
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2025-09-22T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2025-09-22T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-22T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: New hire requesting Phase 3 access. Phase 2 mandatory trainings are not yet enrolled or completed.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Onboarding Phase 3 Access
                  tags:
                    - onboarding
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: enroll_employee
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-1001001
                email: david.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                action: enroll_employee
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-1001002
                email: david.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                action: enroll_employee
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-1001003
                email: david.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                action: enroll_employee
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-1001004
                email: david.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_onb_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am Sarah Martinez and my email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). I'm a new hire in the Chicago office and started on September 29, 2025. I don't know how to get started. Can you help me begin Phase 1 onboarding? I heard from a friend that I should get a laptop, and access to Workday, Slack, Microsoft Office, Zoom. Because I asked a similar question yesterday and the request was not resolved.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices:
            - age_months: 2
              device_type: laptop
              id: MSG00847291
              inventory_status: available
              location: Chicago
              model: Dell Latitude 5530
            - age_months: 1
              device_type: laptop
              id: MSG00847292
              inventory_status: available
              location: Chicago
              model: ThinkPad T14
            - age_months: 3
              device_type: laptop
              id: MSG00847293
              inventory_status: available
              location: Chicago
              model: Dell Latitude 5540
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: day_1_3_initial
              partner_email: jennifer.williams@msg.com
              start_date: '2025-09-29T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: jennifer.williams@msg.com
              level: Partner
              manager_email: jennifer.williams@msg.com
              name: Jennifer Williams
              office_location: Chicago
              onboarding_phase: completed
              partner_email: jennifer.williams@msg.com
              start_date: '2020-01-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-30T14:30:00Z'
              description: Hi, I'm a new hire and started yesterday. I'm not sure what I need to do to get set up with systems and access. Can someone help me understand the onboarding process?
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '1847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: open
              subject: New hire onboarding help - getting started
              tags:
                - onboarding
              type: question
              updated_at: '2025-09-30T15:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2025-09-29T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-29T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '1847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: reserve_device
                asset_id: null
                device_type: laptop
                email: null
                location: Chicago
              tool: asset_management_api
            - parameters:
                action: assign_device
                asset_id: MSG00005002
                device_type: null
                email: sarah.martinez@msg.com
                location: null
              tool: asset_management_api
            - parameters:
                access_type: full_access
                app_name: Workday
                email: sarah.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                access_type: full_access
                app_name: Slack
                email: sarah.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                access_type: full_access
                app_name: Microsoft Office
                email: sarah.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                access_type: full_access
                app_name: Zoom
                email: sarah.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                id: '1847'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: MSG00005002
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Onboarding Phase 1 completed: Laptop assigned and Okta access provisioned. Next steps: mandatory training enrollment.'
                  device_type: laptop
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: solved
                  subject: New hire onboarding help - getting started
                  tags:
                    - onboarding
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)




def test_onb_013(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am David Martinez, I am a manager, e-mail: [david.martinez@msg.com](mailto:david.martinez@msg.com) . I started at Meridian Strategy Group on September 19, 2025 (about 12 days ago) and I’m based in the Chicago office. I am in Phase 3 of my onboarding, and I have Concur working, but I still don’t have Salesforce CRM access. Can you please help me complete my phase 3 onboarding and get Salesforce set up with full access? I heard from colleagues that there might not be licenses available.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG00101803
              employee_email: david.martinez@msg.com
              id: ASMT-1040201
              returned_at: null
          asset_management_devices:
            - age_months: 2
              device_type: laptop
              id: MSG00101803
              inventory_status: assigned
              location: Chicago
              model: Dell Latitude 7430
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: null
              id: CRS-1110009
              max_seats: null
              prerequisites: []
              start_date: null
              title: Ethics & Code of Conduct
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1029019
              max_seats: null
              prerequisites: []
              start_date: null
              title: Security Awareness
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1502609
              max_seats: null
              prerequisites: []
              start_date: null
              title: Data Privacy
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1102009
              max_seats: null
              prerequisites: []
              start_date: null
              title: Anti-harassment
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2025-09-20T08:00:00Z'
              course_id: CRS-1110009
              employee_email: david.martinez@msg.com
              id: ENR-1006001
            - completion_date: '2025-09-20T09:00:00Z'
              course_id: CRS-1029019
              employee_email: david.martinez@msg.com
              id: ENR-1005002
            - completion_date: '2025-09-20T10:00:00Z'
              course_id: CRS-1502609
              employee_email: david.martinez@msg.com
              id: ENR-1200003
            - completion_date: '2025-09-20T11:00:00Z'
              course_id: CRS-1102009
              employee_email: david.martinez@msg.com
              id: ENR-1220103
          license_management_license_allocation:
            - catalog_id: CAT-1847392
              deallocated_at: null
              employee_email: david.martinez@msg.com
              engagement_code: null
              id: LIC-2847391
              pool_type: enterprise
          license_management_license_pool_record:
            - catalog_id: CAT-2847391
              pool_type: standard
              total_licenses: 0
            - catalog_id: CAT-1847392
              pool_type: enterprise
              total_licenses: 50
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs:
            - access_type: read_only
              app_name: Workday
              employee_email: david.martinez@msg.com
              id: OKTA-001
            - access_type: read_only
              app_name: Slack
              employee_email: david.martinez@msg.com
              id: OKTA-002
            - access_type: read_only
              app_name: Microsoft Office
              employee_email: david.martinez@msg.com
              id: OKTA-003
            - access_type: read_only
              app_name: Zoom
              employee_email: david.martinez@msg.com
              id: OKTA-004
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog:
            - annual_cost: 300
              id: CAT-2847391
              name: Salesforce CRM
              pool_type: standard
            - annual_cost: 480
              id: CAT-1847392
              name: Concur Expense
              pool_type: enterprise
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: day_7_30_engagement_ramp
              partner_email: michael.chen@msg.com
              start_date: '2025-09-19T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2025-09-19T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-19T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                $filter: email eq 'david.martinez@msg.com'
                $orderby: null
                $select: id,name,email
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8' and (status eq 'open' or status eq 'pending' or status eq 'hold')
                $orderby: null
                $select: id,subject,status,priority
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: get_training_history
                category: null
                certification_name: null
                client_id: null
                course_id: null
                email: david.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                item:
                  access_type: full_access
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: CAT-2847391
                  client_id: null
                  course_id: null
                  description: Employee requests Salesforce access. Trainings completed, moving forward to phase 3, if licenses are available
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: standard
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: 'Onboarding Phase 3: Salesforce access request'
                  tags:
                    - onboarding
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Onboarding Phase 3 is blocked because no licenses are available for salesforce. '
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_onb_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez. I am a new hire, I started on the 25th of September. I queried about my onboarding a few days ago. I have already completed 1 training module Ethics and Code of Conduct in the onboarding phase 2. Can you check if there's any training left in phase 2 and let me know what I need to do next? My email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com).


    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again. Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments:
            - asset_id: MSG84729301
              employee_email: sarah.martinez@msg.com
              id: ASG-2847001
              returned_at: null
          asset_management_devices:
            - age_months: 6
              device_type: laptop
              id: MSG84729301
              inventory_status: assigned
              location: Chicago
              model: Dell Latitude 7420
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: null
              id: CRS-1001001
              max_seats: null
              prerequisites: []
              start_date: null
              title: Ethics & Code of Conduct
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001002
              max_seats: null
              prerequisites: []
              start_date: null
              title: Security Awareness
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001003
              max_seats: null
              prerequisites: []
              start_date: null
              title: Data Privacy
              training_category: must_have
            - cost: 0
              end_date: null
              id: CRS-1001004
              max_seats: null
              prerequisites: []
              start_date: null
              title: Anti-harassment
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2025-09-29T14:30:00Z'
              course_id: CRS-1001001
              employee_email: sarah.martinez@msg.com
              id: ENR-2847001
            - completion_date: null
              course_id: CRS-1001002
              employee_email: sarah.martinez@msg.com
              id: ENR-2847002
            - completion_date: null
              course_id: CRS-1001003
              employee_email: sarah.martinez@msg.com
              id: ENR-2847003
            - completion_date: null
              course_id: CRS-1001004
              employee_email: sarah.martinez@msg.com
              id: ENR-2847004
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs:
            - access_type: read_only
              app_name: Slack
              employee_email: sarah.martinez@msg.com
              id: OKTA-002
            - access_type: read_only
              app_name: Microsoft Office
              employee_email: sarah.martinez@msg.com
              id: OKTA-003
            - access_type: read_only
              app_name: Zoom
              employee_email: sarah.martinez@msg.com
              id: OKTA-004
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: day_3_7_provisioning
              partner_email: jennifer.williams@msg.com
              start_date: '2025-09-25T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-28T10:30:00Z'
              description: New hire requesting enrollment in mandatory compliance training courses for Phase 2 onboarding.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '12847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: open
              subject: Onboarding Phase 2 - Mandatory Training Enrollment
              tags:
                - onboarding
              type: task
              updated_at: '2025-09-28T14:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2025-09-25T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-25T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '12847'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: All four mandatory compliance trainings (Ethics & Code of Conduct, Security Awareness, Data Privacy, Anti-harassment) are already enrolled. Please complete the remaining courses before proceeding to the next onboarding phase.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: pending
                  subject: Onboarding Phase 2 - Mandatory Training Enrollment
                  tags:
                    - onboarding
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I’m requesting access to Tableau for my data visualization work. I’m currently working on engagement ENG-2847561. Please complete any required validations or approvals and proceed with granting access. Thank you.
    user_context: |
        Data available to you:

        "name": "Sarah Martinez",

        "email": "sarah.martinez@msg.com",

        "phone": "+1-510-292-1090",

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record:
            - catalog_id: CAT-1847293
              pool_type: standard
              total_licenses: 50
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-2847561
              id: ASG-2847561
              senior_manager_email: richard.williams@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00Z'
              engagement_code: ENG-2847561
              senior_manager_email: richard.williams@msg.com
              start_date: '2025-08-15T00:00:00Z'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829374
              name: Tableau
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829374
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-2847561
              engagement_manager_email: david.martinez@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 420
              id: CAT-1847293
              name: Tableau
              pool_type: standard
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: david.martinez@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2024-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: david.martinez@msg.com
              email: micheal.chen@msg.com
              level: Manager
              manager_email: david.martinez@msg.com
              name: Michael Chen
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2023-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: '1'
              phone: +1-510-292-1090
              role: end-user
              updated_at: '2025-09-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                action: validate_engagement_code
                email: null
                engagement_code: ENG-2847561
              tool: mavenlink_api
            - parameters:
                email: sarah.martinez@msg.com
                engagement_code: ENG-2847561
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                $filter: requester_id eq '8' and catalog_id eq 'CAT-1847293' and (status eq 'open' or status eq 'hold' or status eq 'pending')
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                software_name: Tableau
              tool: software_catalog_search
            - parameters:
                catalog_id: CAT-1847293
              tool: software_catalog_get_details
            - parameters:
                action: check_availability
                catalog_id: CAT-1847293
                email: null
                engagement_code: null
                pool_type: standard
              tool: license_management_api
            - parameters:
                email: david.martinez@msg.com
              tool: approver_lookup_get_contact
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: david.martinez@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: CAT-1847293
                  client_id: null
                  course_id: null
                  description: 'Sarah Martinez requests Tableau access for data visualization. Engagement code: ENG-2847561.'
                  device_type: null
                  due_at: null
                  engagement_code: ENG-2847561
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: standard
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Tableau access request for data visualization work
                  tags:
                    - software_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: 420
                approver_email: david.martinez@msg.com
                engagement_code: ENG-2847561
                request_type: software_access
                requester_email: sarah.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need access to Adobe Creative Cloud for client presentation design. My engagement code is ENG-3918472. I'm a Consultant. My name is Sarah Martinez and my email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com)
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-3918472
              id: ASN-2847391
              senior_manager_email: jennifer.williams@msg.com
              start_date: '2025-09-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-3918472
              senior_manager_email: jennifer.williams@msg.com
              start_date: '2025-09-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-2847391
              name: TechCorp Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-2847391
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-3918472
              engagement_manager_email: david.chen@msg.com
              start_date: '2025-09-15T00:00:00'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 720
              id: CAT-1847293
              name: Adobe Creative Cloud
              pool_type: enterprise
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Consultant
              manager_email: david.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: completed
              partner_email: jennifer.williams@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: david.chen@msg.com
              level: Manager
              manager_email: jennifer.williams@msg.com
              name: David Chen
              office_location: Chicago
              onboarding_phase: completed
              partner_email: jennifer.williams@msg.com
              start_date: '2021-08-10T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: jennifer.williams@msg.com
              level: Partner
              manager_email: null
              name: Jennifer Williams
              office_location: Chicago
              onboarding_phase: completed
              partner_email: null
              start_date: '2018-01-22T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  approval_required: 'yes'
                  approver_id: david.chen@msg.com,jennifer.williams@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: CAT-1847293
                  client_id: null
                  course_id: null
                  description: 'Request for Adobe Creative Cloud for client presentation design. Engagement code: ENG-3918472.'
                  device_type: null
                  due_at: null
                  engagement_code: ENG-3918472
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: enterprise
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Adobe Creative Cloud access request
                  tags:
                    - software_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: 720
                approver_email: david.chen@msg.com
                engagement_code: ENG-3918472
                request_type: software_access
                requester_email: sarah.martinez@msg.com
              tool: approval_create_request
            - parameters:
                amount: 720
                approver_email: jennifer.williams@msg.com
                engagement_code: ENG-3918472
                request_type: software_access
                requester_email: sarah.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  active: null
                  approval_required: 'yes'
                  approver_id: david.chen@msg.com,jennifer.williams@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: CAT-1847293
                  client_id: null
                  course_id: null
                  description: 'Request for Adobe Creative Cloud for client presentation design. Engagement code: ENG-3918472. Approval requests sent. Ticket is set to ''pending'' (waiting for approval).'
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: ENG-3918472
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: enterprise
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: pending
                  subject: Adobe Creative Cloud access request
                  tags:
                    - software_access
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my email id is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com)  and I'm currently working as a Senior Consultant and based out of Chicago office. I need access to Alteryx for advanced analytics. Can you please help me with the request?
    user_context: |
        Rules:

        Provide engagement code ENG-4027183 when the agent requests for it.

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation:
            - catalog_id: CAT-4829571
              deallocated_at: null
              employee_email: john.smith@msg.com
              engagement_code: ENG-4027183
              id: LIC-2847391
              pool_type: standard
            - catalog_id: CAT-4829571
              deallocated_at: null
              employee_email: emily.rodriguez@msg.com
              engagement_code: ENG-4027183
              id: LIC-3948572
              pool_type: standard
            - catalog_id: CAT-4829571
              deallocated_at: null
              employee_email: marcus.thompson@msg.com
              engagement_code: ENG-4027183
              id: LIC-5729384
              pool_type: standard
            - catalog_id: CAT-4829571
              deallocated_at: null
              employee_email: priya.patel@msg.com
              engagement_code: ENG-4027183
              id: LIC-6847291
              pool_type: standard
            - catalog_id: CAT-4829571
              deallocated_at: null
              employee_email: ahmed.hassan@msg.com
              engagement_code: ENG-4027183
              id: LIC-7293847
              pool_type: standard
            - catalog_id: CAT-4829571
              deallocated_at: null
              employee_email: isabella.rossi@msg.com
              engagement_code: ENG-4027183
              id: LIC-8394756
              pool_type: standard
          license_management_license_pool_record:
            - catalog_id: CAT-4829571
              pool_type: standard
              total_licenses: 6
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2026-12-31T00:00:00Z'
              engagement_code: ENG-4027183
              id: ASN-0012344
              senior_manager_email: sarah.johnson@msg.com
              start_date: '2024-01-15T00:00:00Z'
          mavenlink_mv_engagements:
            - end_date: '2026-12-31T00:00:00Z'
              engagement_code: ENG-4027183
              senior_manager_email: sarah.johnson@msg.com
              start_date: '2024-01-15T00:00:00Z'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-0045677
              name: Retail Dynamics LLC
              required_training_courses: []
              requires_nda: false
          salesforce_crm_sf_engagements:
            - client_id: CLT-0045677
              end_date: '2026-12-31T00:00:00Z'
              engagement_code: ENG-4027183
              engagement_manager_email: sarah.johnson@msg.com
              start_date: '2024-01-15T00:00:00Z'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 5200
              id: CAT-4829571
              name: Alteryx
              pool_type: standard
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Senior Consultant
              manager_email: mini.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: completed
              partner_email: david.wilson@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: sarah.johnson@msg.com
              email: mini.chen@msg.com
              level: Manager
              manager_email: david.wilson@msg.com
              name: Mini Chen
              office_location: Chicago
              onboarding_phase: completed
              partner_email: david.wilson@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: david.wilson@msg.com
              level: Partner
              manager_email: david.wilson@msg.com
              name: David Wilson
              office_location: Chicago
              onboarding_phase: completed
              partner_email: david.wilson@msg.com
              start_date: '2019-01-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: '1'
              phone: 312-345-4376
              role: end-user
              updated_at: '2023-03-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                action: validate_engagement_code
                email: null
                engagement_code: ENG-4027183
              tool: mavenlink_api
            - parameters:
                email: sarah.martinez@msg.com
                engagement_code: ENG-4027183
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                software_name: Alteryx
              tool: software_catalog_search
            - parameters:
                catalog_id: CAT-4829571
              tool: software_catalog_get_details
            - parameters:
                action: check_availability
                catalog_id: CAT-4829571
                email: null
                engagement_code: null
                pool_type: standard
              tool: license_management_api
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee requested access to Alteryx (annual cost $5,200, standard pool) but license pool is at capacity. Request cannot be fulfilled.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Request for Alteryx access - license pool full
                  tags:
                    - software_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: CAT-4829571
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: standard
                  organization_id: null
                  priority: normal
                  requester_id: null
                  status: solved
                  subject: null
                  tags:
                    - software_access
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is David Martinez, and my email is [david.martinez@msg.com](). I’m a Manager at Meridian Strategy Group. I’d like to request full access to Miro for workshop facilitation purposes. My engagement code is ENG-5182934.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record:
            - catalog_id: CAT-2847391
              pool_type: enterprise
              total_licenses: 500
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-20T00:00:00Z'
              engagement_code: ENG-5182934
              id: ASN-8472951
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-15T00:00:00Z'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00Z'
              engagement_code: ENG-5182934
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-15T00:00:00Z'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-3947281
              name: TechCorp Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-3947281
              end_date: '2025-12-20T00:00:00Z'
              engagement_code: ENG-5182934
              engagement_manager_email: jennifer.wilson@msg.com
              start_date: '2025-08-15T00:00:00Z'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 350
              id: CAT-2847391
              name: Miro
              pool_type: enterprise
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: completed
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00Z'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: full_access
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: CAT-2847391
                  client_id: null
                  course_id: null
                  description: Manager requests access to Miro for workshop facilitation. Engagement code ENG-5182934 has been provided and validated.
                  device_type: null
                  due_at: null
                  engagement_code: ENG-5182934
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: enterprise
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Miro access request for workshop facilitation
                  tags:
                    - software_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: allocate
                catalog_id: CAT-2847391
                email: david.martinez@msg.com
                engagement_code: ENG-5182934
                pool_type: enterprise
              tool: license_management_api
            - parameters:
                access_type: full_access
                app_name: Miro
                email: david.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I requested access to Power BI Premium for my client engagement ENG-6293045 three days ago, but I haven't received an update yet. Can you let me know the status or help move this forward?
    user_context: |
        Your email address is [david.martinez@msg.com](mailto:david.martinez@msg.com).

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: 600
              approver_email: sarah.thompson@msg.com
              engagement_code: ENG-6293045
              id: APR-5829471
              request_type: software_access
              requester_email: david.martinez@msg.com
              status: pending
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record:
            - catalog_id: CAT-2847391
              pool_type: standard
              total_licenses: 50
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-6293045
              id: ASG-4829371
              senior_manager_email: jennifer.adams@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-6293045
              senior_manager_email: jennifer.adams@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements:
            - client_id: CLT-8472951
              end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-6293045
              engagement_manager_email: jennifer.adams@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 600
              id: CAT-2847391
              name: Power BI Premium
              pool_type: standard
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: michael.chen@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: sarah.thompson@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Partner
              manager_email: robert.wilson@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: sarah.thompson@msg.com
              start_date: '2019-01-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: full_access
              approval_required: 'yes'
              approver_id: sarah.thompson@msg.com
              asset_id: null
              assignee_id: '157'
              catalog_id: CAT-2847391
              client_id: null
              course_id: null
              created_at: '2025-09-28T14:30:00Z'
              description: Request for access to Power BI Premium for data analytics work on client engagement ENG-6293045. Annual cost is $600, requires partner approval per policy.
              device_type: null
              due_at: null
              engagement_code: ENG-6293045
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '12847'
              license_pool: standard
              organization_id: null
              priority: normal
              requester_id: '8'
              status: pending
              subject: Software Access Request - Power BI Premium
              tags:
                - software_access
              type: task
              updated_at: '2025-09-28T15:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T10:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                $filter: email eq 'david.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: '8'
                $orderby: created_at desc
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                id: '12847'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                approver_email: null
                engagement_code: null
                request_type: software_access
                requester_email: david.martinez@msg.com
              tool: approval_get_status
            - parameters:
                email: sarah.thompson@msg.com
              tool: approver_lookup_get_contact
            - parameters:
                action: validate_engagement_code
                email: null
                engagement_code: ENG-6293045
              tool: mavenlink_api
            - parameters:
                engagement_code: ENG-6293045
              tool: salesforce_crm_get_engagement
            - parameters:
                email: david.martinez@msg.com
                engagement_code: ENG-6293045
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                software_name: Power BI Premium
              tool: software_catalog_search
            - parameters:
                catalog_id: CAT-2847391
              tool: software_catalog_get_details
            - parameters:
                action: check_availability
                catalog_id: CAT-2847391
                email: null
                engagement_code: ENG-6293045
                pool_type: standard
              tool: license_management_api
            - parameters:
                id: '12847'
                item:
                  access_type: full_access
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: CAT-2847391
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-6293045
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: standard
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am David Martinez, Senior Manager. I need access to Jira for project management under engagement code ENG-7304156. I submitted a request yesterday but haven't received access yet. Can you please check the status or help expedite this?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record:
            - catalog_id: CAT-3847291
              pool_type: enterprise
              total_licenses: 500
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-7304156
              id: ASSIGN-8472951
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-7304156
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829573
              name: TechFlow Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829573
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-7304156
              engagement_manager_email: jennifer.wilson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 180
              id: CAT-3847291
              name: Jira
              pool_type: enterprise
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-30T14:30:00Z'
              description: I need access to Jira software for managing our client project tasks and tracking development progress. My engagement code is ENG-7304156.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '12847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: open
              subject: Request access to Jira for project management
              tags:
                - software_access
              type: task
              updated_at: '2025-09-30T14:30:00Z'
          zendesk_users:
            - active: true
              created_at: '2019-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '12847'
                table: tickets
              tool: zendesk_get_item
            - parameters:
                action: allocate
                catalog_id: CAT-3847291
                email: david.martinez@msg.com
                engagement_code: ENG-7304156
                pool_type: enterprise
              tool: license_management_api
            - parameters:
                access_type: full_access
                app_name: Jira
                email: david.martinez@msg.com
              tool: okta_provision_access
            - parameters:
                id: '12847'
                item:
                  access_type: full_access
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: CAT-3847291
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-7304156
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: enterprise
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to request access to Confluence for my current engagement. My engagement code is ENG-8415267. I'm A Senior Manager. My name is David Martinez and my email is [david.martinez@msg.com](mailto:david.martinez@msg.com). The practice area partner is currently on leave, but someone else should be available to see this request through. Could you complete this request today?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record:
            - catalog_id: CAT-3847291
              pool_type: standard
              total_licenses: 50
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-8415267
              id: ASN-8472951
              senior_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-8415267
              senior_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-2847391
              name: TechCorp Industries
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-2847391
              end_date: '2026-02-28T00:00:00'
              engagement_code: ENG-8415267
              engagement_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 540
              id: CAT-3847291
              name: Confluence
              pool_type: standard
          workday_employees:
            - availability_status: available
              backup_approver_email: richard.smith@msg.com
              email: david.martinez@msg.com
              level: Senior Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: completed
              partner_email: jennifer.davis@msg.com
              start_date: '2019-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Partner
              manager_email: robert.wilson@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: completed
              partner_email: sarah.thompson@msg.com
              start_date: '2015-08-20T00:00:00'
            - availability_status: on_leave
              backup_approver_email: null
              email: jennifer.davis@msg.com
              level: Partner
              manager_email: robert.wilson@msg.com
              name: Jennifer Davis
              office_location: Chicago
              onboarding_phase: completed
              partner_email: jennifer.davis@msg.com
              start_date: '2014-06-12T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: richard.smith@msg.com
              level: Partner
              manager_email: null
              name: Richard Smith
              office_location: Chicago
              onboarding_phase: completed
              partner_email: null
              start_date: '2010-05-01T00:00:00Z'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2019-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: full_access
                  approval_required: 'yes'
                  approver_id: richard.smith@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: CAT-3847291
                  client_id: null
                  course_id: null
                  description: Employee requests access to Confluence for current engagement ENG-8415267.
                  device_type: null
                  due_at: null
                  engagement_code: ENG-8415267
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: standard
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Request access to Confluence
                  tags:
                    - software_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: 540
                approver_email: richard.smith@msg.com
                engagement_code: ENG-8415267
                request_type: software_access
                requester_email: david.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: full_access
                  active: null
                  approval_required: 'yes'
                  approver_id: richard.smith@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: CAT-3847291
                  client_id: null
                  course_id: null
                  description: Employee requested access to Confluence for current engagement ENG-8415267. Approval request sent to backup approver (richard.smith@msg.com ); pending approval.
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: ENG-8415267
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: standard
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: pending
                  subject: Request access to Confluence
                  tags:
                    - software_access
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my email id is [sarah.martin@msg.com](mailto:sarah.martin@msg.com). I need access to Figma for wireframing. Can you help me get set up?
    user_context: |
        Rules:

        If the agent asks for the engagement code, mention that you don't know the engagement code and will get back after checking with your manager.

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record:
            - catalog_id: CAT-1847293
              pool_type: standard
              total_licenses: 3
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martin@msg.com
              end_date: '2026-12-31T00:00:00Z'
              engagement_code: ENG-0012344
              id: ASN-0012344
              senior_manager_email: sarah.johnson@msg.com
              start_date: '2025-06-15T00:00:00Z'
          mavenlink_mv_engagements:
            - end_date: '2026-12-31T00:00:00Z'
              engagement_code: ENG-0012344
              senior_manager_email: sarah.johnson@msg.com
              start_date: '2024-01-15T00:00:00Z'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-0045677
              name: Retail Dynamics LLC
              required_training_courses: []
              requires_nda: false
          salesforce_crm_sf_engagements:
            - client_id: CLT-0045677
              end_date: '2026-12-31T00:00:00Z'
              engagement_code: ENG-0012344
              engagement_manager_email: sarah.johnson@msg.com
              start_date: '2024-01-15T00:00:00Z'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 180
              id: CAT-1847293
              name: Figma
              pool_type: standard
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martin@msg.com
              level: Analyst
              manager_email: rob.chen@msg.com
              name: Sarah Martin
              office_location: Chicago
              onboarding_phase: completed
              partner_email: rick.williams@msg.com
              start_date: '2024-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: sarah.johnson@msg.com
              email: rob.chen@msg.com
              level: Manager
              manager_email: rick.williams@msg.com
              name: Rob Chen
              office_location: Chicago
              onboarding_phase: completed
              partner_email: rick.williams@msg.com
              start_date: '2020-02-10T00:00:00Z'
            - availability_status: available
              backup_approver_email: null
              email: rick.williams@msg.com
              level: Partner
              manager_email: null
              name: Rick Williams
              office_location: Chicago
              onboarding_phase: completed
              partner_email: null
              start_date: '2010-05-01T00:00:00Z'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: sarah.martin@msg.com
              id: '8'
              name: Sarah Martin
              organization_id: '1'
              phone: 312-345-4376
              role: end-user
              updated_at: '2024-03-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: sarah.martin@msg.com
              tool: workday_api
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Sarah Martin (Analyst) requests access to Figma for wireframing. Employee did not provide engagement code. Per policy, engagement code is required for all specialized software access. Agent requests engagement code from employee and explains why it is needed.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Request for Figma access (engagement code needed)
                  tags:
                    - software_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  asset_id: null
                  assignee_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: hold
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)




def test_swa_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am David Martinez (Manager), [david.martinez@msg.com](mailto:david.martinez@msg.com). I need full access to the Airtable software. My engagement code is ENG-2748590. I am on this engagement but it has completed a while back, can I still access the software?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record:
            - catalog_id: CAT-1847293
              pool_type: standard
              total_licenses: 50
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2024-08-30T00:00:00'
              engagement_code: ENG-2748590
              id: ASN-0022355
              senior_manager_email: michael.chen@msg.com
              start_date: '2024-02-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2024-08-30T00:00:00'
              engagement_code: ENG-2748590
              senior_manager_email: michael.chen@msg.com
              start_date: '2024-02-15T00:00:00'
              status: completed
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-8472951
              name: TechCorp Industries
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-8472951
              end_date: '2024-08-30T00:00:00'
              engagement_code: ENG-2748590
              engagement_manager_email: sarah.thompson@msg.com
              start_date: '2024-02-15T00:00:00'
              status: completed
          software_catalog_software_catalog:
            - annual_cost: 240
              id: CAT-1847293
              name: Airtable
              pool_type: standard
          workday_employees:
            - availability_status: available
              backup_approver_email: jennifer.davis@msg.com
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: jennifer.davis@msg.com
              email: sarah.thompson@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-08-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: User requests access to Airtable for project tracking. Engagement code ENG-2748590 is completed. Access cannot be granted for completed engagements. Request solved as denied
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Airtable access request - engagement completed
                  tags:
                    - software_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: full_access
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: CAT-1847293
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: standard
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_013(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need access to DataRobotX Pro for my machine learning work. My engagement code is ENG-3859601. My email address is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). Can you provision this for me?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-3859601
              id: ASN-2847391
              senior_manager_email: michael.thompson@msg.com
              start_date: '2025-09-01T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-3859601
              senior_manager_email: michael.thompson@msg.com
              start_date: '2025-09-01T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829573
              name: TechCorp Industries
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829573
              end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-3859601
              engagement_manager_email: michael.thompson@msg.com
              start_date: '2025-09-01T00:00:00'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 840
              id: CAT-1847293
              name: Tableau Desktop
              pool_type: standard
            - annual_cost: 1200
              id: CAT-2948571
              name: Python Analytics Suite
              pool_type: standard
            - annual_cost: 995
              id: CAT-3847291
              name: R Studio Professional
              pool_type: enterprise
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.thompson@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: completed
              partner_email: jennifer.chen@msg.com
              start_date: '2024-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: michael.thompson@msg.com
              level: Manager
              manager_email: jennifer.chen@msg.com
              name: Michael Thompson
              office_location: Chicago
              onboarding_phase: completed
              partner_email: jennifer.chen@msg.com
              start_date: '2022-01-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: +1-312-928-0417
              role: end-user
              updated_at: '2024-03-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                email: sarah.martinez@msg.com
                engagement_code: ENG-3859601
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                engagement_code: ENG-3859601
              tool: salesforce_crm_get_engagement
            - parameters:
                action: validate_engagement_code
                email: null
                engagement_code: ENG-3859601
              tool: mavenlink_api
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Analyst Sarah Martinez requests DataRobotX Pro using engagement ENG-3859601.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: 'Software Access Request: DataRobotX Pro'
                  tags:
                    - software_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_016(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I requested access to Notion (enterprise license pool) for documentation last week using engagement code ENG-6182934, but my ticket was marked as solved and I still can't access the software. Can you help me get access?
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.



        If asked, provide following information:

        Full name: David Martinez

        Corporate Email: [david.martinez@msg.com](mailto:david.martinez@msg.com)
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record:
            - catalog_id: CAT-3847291
              pool_type: enterprise
              total_licenses: 500
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-6182934
              id: ASG-7394821
              senior_manager_email: michael.chen@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-6182934
              senior_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829371
              name: TechCorp Industries
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829371
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-6182934
              engagement_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 96
              id: CAT-3847291
              name: Notion
              pool_type: enterprise
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Analyst
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2024-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-01-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: CAT-3847291
              client_id: null
              course_id: null
              created_at: '2025-09-23T10:30:00Z'
              description: 'Request for access to Notion software for documentation purposes. Engagement code: ENG-6182934'
              device_type: null
              due_at: null
              engagement_code: ENG-6182934
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '12847'
              license_pool: enterprise
              organization_id: null
              priority: normal
              requester_id: '8'
              status: solved
              subject: Software Access Request - Notion
              tags:
                - software_access
              type: task
              updated_at: '2025-09-24T16:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-03-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                $filter: requester_id eq '8' and subject eq 'Software Access Request - Notion'
                $orderby: null
                $select: null
                $skip: null
                $top: 5
                table: tickets
              tool: zendesk_get_items
            - parameters:
                email: david.martinez@msg.com
                engagement_code: ENG-6182934
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                action: get_employee_assignments
                email: david.martinez@msg.com
                engagement_code: ENG-6182934
              tool: mavenlink_api
            - parameters:
                engagement_code: ENG-6182934
              tool: salesforce_crm_get_engagement
            - parameters:
                software_name: Notion
              tool: software_catalog_search
            - parameters:
                action: check_availability
                catalog_id: CAT-3847291
                email: david.martinez@msg.com
                engagement_code: ENG-6182934
                pool_type: enterprise
              tool: license_management_api
            - parameters:
                id: '12847'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-6182934
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: enterprise
                  organization_id: null
                  priority: null
                  requester_id: '8'
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                action: get_employee
                email: sarah.thompson@msg.com
              tool: workday_api
            - parameters:
                amount: 96
                approver_email: sarah.thompson@msg.com
                engagement_code: ENG-6182934
                request_type: software_access
                requester_email: david.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '12847'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: CAT-3847291
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: ENG-6182934
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: enterprise
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: pending
                  subject: null
                  tags:
                    - software_access
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_017(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am David Martinez, my email address is [david.martinez@msg.com](mailto:david.martinez@msg.com), I need access to Looker for business intelligence work. My engagement code is ENG-7293045.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record:
            - catalog_id: CAT-5847291
              pool_type: standard
              total_licenses: 0
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-7293045
              id: ASN-7293045-001
              senior_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-7293045
              senior_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829573
              name: TechFlow Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829573
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-7293045
              engagement_manager_email: sarah.thompson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 2400
              id: CAT-5847291
              name: Looker
              pool_type: standard
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-08-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: CAT-5847291
                  client_id: null
                  course_id: null
                  description: 'David Martinez requests access to Looker for business intelligence. Engagement code: ENG-7293045.'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: standard
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Request for Looker access (ENG-7293045)
                  tags:
                    - software_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: CAT-5847291
                  client_id: null
                  course_id: null
                  description: 'Request denied: Looker access cannot be provisioned at this time because all standard pool licenses are currently allocated. There is no waitlist. Please check back later.'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: standard
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags:
                    - software_access
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_019(x: TestContext, judge: Judge):
    """!
    query: |
        I need full access to Asana (Standard License) for my team coordination work.  My engagement code is ENG-9415267 but I am not yet assigned to the engagement. I understand that as a Senior Manager I don't need approval for this software. Please provision access for me.
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.



        If asked provide following information:

        Full Name: David Martinez

        Email: [david.martinez@msg.com](mailto:david.martinez@msg.com)

        Engagement Code: ENG-9415267
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record:
            - catalog_id: CAT-3847291
              pool_type: standard
              total_licenses: 50
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: jennifer.wilson@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-9415267
              id: ASSIGN-8472951
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-15T00:00:00'
            - assignment_status: active
              employee_email: robert.davis@msg.com
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-9415267
              id: ASSIGN-8472952
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-9415267
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-8472951
              name: TechCorp Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-8472951
              end_date: '2025-12-20T00:00:00'
              engagement_code: ENG-9415267
              engagement_manager_email: jennifer.wilson@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 150
              id: CAT-3847291
              name: Asana
              pool_type: standard
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                action: validate_engagement_code
                email: david.martinez@msg.com
                engagement_code: ENG-9415267
              tool: mavenlink_api
            - parameters:
                email: david.martinez@msg.com
                engagement_code: ENG-9415267
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                software_name: Asana
              tool: software_catalog_search
            - parameters:
                item:
                  access_type: full_access
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: CAT-3847291
                  client_id: null
                  course_id: null
                  description: Software access required for engagement ENG-9415267
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: standard
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Asana access request - engagement ENG-9415267
                  tags:
                    - software_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: full_access
                  active: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: CAT-3847291
                  client_id: null
                  course_id: null
                  description: Request denied. Software access requires you to be assigned to an active engagement. No provisioning will occur.
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: standard
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: solved
                  subject: 'Denied: Asana access request - not assigned to engagement ENG-9415267'
                  tags:
                    - software_access
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_swa_020(x: TestContext, judge: Judge):
    """!
    query: |
        Hi! My name is David Martinez, e-mail [david.martinez@msg.com](mailto:david.martinez@msg.com). I am a partner at the firm and I would like to request urgent access to Palantir Foundry. I am on an active engagement with engagement code: ENG-00526378. Could you complete my request today?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation:
            - catalog_id: CAT-4829571
              deallocated_at: null
              employee_email: michael.chen@msg.com
              engagement_code: null
              id: LIC-2847391
              pool_type: standard
          license_management_license_pool_record:
            - catalog_id: CAT-4829571
              pool_type: standard
              total_licenses: 25
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              engagement_code: ENG-0526378
              id: ASSIGN-900001
              senior_manager_email: alex.jordan@msg.com
              start_date: '2025-08-01'
          mavenlink_mv_engagements:
            - engagement_code: ENG-0526378
              senior_manager_email: alex.jordan@msg.com
              start_date: '2025-08-01'
              status: active
          okta_application_access_logs: []
          salesforce_crm_sf_engagements:
            - client_id: CLT-7654321
              end_date: '2026-01-31'
              engagement_code: ENG-0526378
              engagement_manager_email: alex.jordan@msg.com
              start_date: '2025-08-01'
              status: active
          software_catalog_software_catalog:
            - annual_cost: 50000
              id: CAT-4829571
              name: Palantir Foundry
              pool_type: standard
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Partner
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.martinez@msg.com
              start_date: '2019-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2019-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: CAT-4829571
                  client_id: null
                  course_id: null
                  description: Partner requested urgent access to Palantir Foundry. A valid engagement code is required to proceed.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: urgent
                  requester_id: '8'
                  status: open
                  subject: 'Urgent: Palantir Foundry access request'
                  tags:
                    - software_access
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: standard
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trn_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to enroll in the 'Advanced Excel for Consultants' training scheduled for October 15-16, 2025. I don't have any active or booked engagements during those dates, and I believe there are seats available. Can you help me with the enrollment?
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.

        If asked info for verification, provide this info, name is Sarah Martinez, email id is [sarah.martinez@gmail.com](mailto:sarah.martinez@gmail.com).
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: '2025-10-16T00:00:00'
              id: CRS-0847291
              max_seats: 8
              prerequisites: []
              start_date: '2025-10-15T00:00:00'
              title: Advanced Excel for Consultants
              training_category: nice_to_have
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@gmail.com
              level: Analyst
              manager_email: michael.chen@gmail.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@gmail.com
              start_date: '2024-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2025-09-15T10:00:00Z'
              email: sarah.martinez@gmail.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T10:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: enroll_employee
                course_id: CRS-0847291
                email: sarah.martinez@gmail.com
              tool: degreed_api
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: CRS-0847291
                  description: Employee requests enrollment in 'Advanced Excel for Consultants' (internal, $0, Oct 15-16, 2025). No prerequisites required. No active/booked engagements during training dates. 8 seats available. Enrolled.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: 'Training enrollment: Advanced Excel for Consultants (Oct 15-16, 2025)'
                  tags:
                    - training_enrollment
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  active: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: CRS-0847291
                  description: null
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: solved
                  subject: null
                  tags:
                    - training_enrollment
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trn_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is **Sarah Martinez**, and I’m a **Consultant** at Meridian Strategy Group.
        My corporate email is **[sarah.martinez@msg.com]()**.

        I’d like to enroll in the **Project Management Professional (PMP) Prep** training scheduled for **October 20–24, 2025**. From what I can see, it’s an external certification prep course with a total cost of **$3,500**.

        I’ve already completed all the prerequisite courses, and I don’t have any active or upcoming client engagements during those dates.

        Could you please let me know if you can help me proceed with the enrollment, or if you need anything further from me?
    user_context: |
        Rules:

        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same information, provide it again exactly as previously stated.
        - Do not reference internal policies, tools, approvals, or backend systems.
        - Do not guide, coach, or hint the agent toward any action.
        - Respond only to questions asked by the agent.
        - Remain focused, clear, patient, and realistic in tone.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 3500
              end_date: '2025-10-24T00:00:00'
              id: CRS-2847391
              max_seats: 10
              prerequisites: []
              start_date: '2025-10-20T00:00:00'
              title: Project Management Professional (PMP) Prep
              training_category: nice_to_have
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements:
            - end_date: '2025-09-15T00:00:00'
              engagement_code: ENG-2847391
              senior_manager_email: jennifer.chen@msg.com
              start_date: '2025-06-01T00:00:00'
              status: completed
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829371
              name: TechCorp Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829371
              end_date: '2025-09-15T00:00:00'
              engagement_code: ENG-2847391
              engagement_manager_email: michael.thompson@msg.com
              start_date: '2025-06-01T00:00:00'
              status: completed
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Consultant
              manager_email: michael.thompson@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.chen@msg.com
              start_date: '2024-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: michael.thompson@msg.com
              level: Manager
              manager_email: jennifer.chen@msg.com
              name: Michael Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.chen@msg.com
              start_date: '2022-08-10T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: jennifer.chen@msg.com
              level: Partner
              manager_email: null
              name: Jennifer Chen
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.chen@msg.com
              start_date: '2019-01-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-03-15T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_course_details
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-2847391
                email: null
                keyword: null
              tool: degreed_api
            - parameters:
                action: check_enrollment
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-2847391
                email: null
                keyword: null
              tool: degreed_api
            - parameters:
                action: get_training_history
                category: null
                certification_name: null
                client_id: null
                course_id: null
                email: sarah.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                action: get_employee_assignments
                email: sarah.martinez@msg.com
                engagement_code: null
              tool: mavenlink_api
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                email: michael.thompson@msg.com
              tool: approver_lookup_get_contact
            - parameters:
                amount: 3500
                approver_email: michael.thompson@msg.com
                engagement_code: null
                request_type: training_cost
                requester_email: sarah.martinez@msg.com
              tool: approval_create_request
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: michael.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: CRS-2847391
                  description: Request to enroll in external PMP Prep training (Oct 20-24, 2025, $3,500). Prerequisites complete. No active/booked engagements.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: 'Training enrollment: Project Management Professional (PMP) Prep (Oct 20-24, 2025)'
                  tags:
                    - training_enrollment
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trn_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez and my email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). I'd like to enroll in the 'AWS Solutions Architect Professional' training (course ID: CRS-3847291) scheduled for November 3-7, 2025. I've already completed the AWS Associate certification. Please let me know what the next steps are.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 7200
              end_date: '2025-11-07T00:00:00'
              id: CRS-3847291
              max_seats: null
              prerequisites:
                - CRS-2847193
              start_date: '2025-11-03T00:00:00'
              title: AWS Solutions Architect Professional
              training_category: nice_to_have
            - cost: 3500
              end_date: '2025-06-19T00:00:00'
              id: CRS-2847193
              max_seats: null
              prerequisites: []
              start_date: '2025-06-15T00:00:00'
              title: AWS Solutions Architect Associate
              training_category: nice_to_have
          degreed_training_enrollments:
            - completion_date: '2025-06-19T00:00:00'
              course_id: CRS-2847193
              employee_email: sarah.martinez@msg.com
              id: ENR-4829371
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements:
            - end_date: '2025-10-25T00:00:00'
              engagement_code: ENG-2847391
              senior_manager_email: jennifer.williams@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-2847391
              name: TechCorp Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-2847391
              end_date: '2025-10-25T00:00:00'
              engagement_code: ENG-2847391
              engagement_manager_email: michael.rodriguez@msg.com
              start_date: '2025-08-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Senior Consultant
              manager_email: david.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: david.chen@msg.com
              level: Manager
              manager_email: jennifer.williams@msg.com
              name: David Chen
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2021-08-10T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: jennifer.williams@msg.com
              level: Partner
              manager_email: jennifer.williams@msg.com
              name: Jennifer Williams
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2018-01-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: CRS-3847291
                  description: Request to enroll in AWS Solutions Architect Professional (CRS-3847291), external training, $7,200, Nov 3-7, 2025. Prerequisites completed. No engagement overlap. Approvals required.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: 'Training enrollment: AWS Solutions Architect Professional (Nov 3-7, 2025)'
                  tags:
                    - training_enrollment
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: 7200
                approver_email: david.chen@msg.com
                engagement_code: null
                request_type: training_cost
                requester_email: sarah.martinez@msg.com
              tool: approval_create_request
            - parameters:
                amount: 7200
                approver_email: jennifer.williams@msg.com
                engagement_code: null
                request_type: training_cost
                requester_email: sarah.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  active: null
                  approval_required: 'yes'
                  approver_id: david.chen@msg.com,jennifer.williams@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: CRS-3847291
                  description: Request to enroll in AWS Solutions Architect Professional (CRS-3847291), external training, $7,200, Nov 3-7, 2025. Prerequisites completed. No engagement overlap. Approvals required.
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: pending
                  subject: 'Training enrollment: AWS Solutions Architect Professional (Nov 3-7, 2025)'
                  tags:
                    - training_enrollment
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trn_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez, e-mail [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). I'd like to enroll in the 'Leadership Excellence' training scheduled for October 8-9, 2025. I made a request with you earlier and I've already completed the prerequisite 'Empathy' course. I am currently also on an engagement (ENG-1472583). The senior manager for my engagement, Michael Thompson, has already approved. Can you confirm my enrollment?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: null
              approver_email: michael.thompson@msg.com
              engagement_code: ENG-1472583
              id: APR-1002001
              request_type: training_engagement_coordination
              requester_email: sarah.martinez@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: '2025-09-16T00:00:00'
              id: CRS-2847391
              max_seats: '12'
              prerequisites: []
              start_date: '2025-09-15T00:00:00'
              title: Empathy
              training_category: nice_to_have
            - cost: 0
              end_date: '2025-10-09T00:00:00'
              id: CRS-3847291
              max_seats: 12
              prerequisites:
                - CRS-2847391
              start_date: '2025-10-08T00:00:00'
              title: Leadership Excellence
              training_category: nice_to_have
          degreed_training_enrollments:
            - completion_date: '2025-09-16T00:00:00'
              course_id: CRS-2847391
              employee_email: sarah.martinez@msg.com
              id: ENR-2847391
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-11-30T00:00:00'
              engagement_code: ENG-1472583
              id: ASG-2847391
              senior_manager_email: michael.thompson@msg.com
              start_date: '2025-10-01T00:00:00'
            - assignment_status: active
              employee_email: michael.thompson@msg.com
              end_date: '2025-11-30T00:00:00'
              engagement_code: ENG-1472583
              id: ASG-2847392
              senior_manager_email: michael.thompson@msg.com
              start_date: '2025-10-01T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-11-30T00:00:00'
              engagement_code: ENG-1472583
              senior_manager_email: michael.thompson@msg.com
              start_date: '2025-10-01T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements:
            - client_id: CLT-8394751
              end_date: '2025-11-30T00:00:00'
              engagement_code: ENG-1472583
              engagement_manager_email: david.chen@msg.com
              start_date: '2025-10-01T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Manager
              manager_email: david.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.thompson@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: michael.thompson@msg.com
              level: Senior Manager
              manager_email: david.chen@msg.com
              name: Michael Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.thompson@msg.com
              start_date: '2019-06-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '157'
              created_at: '2025-09-29T08:00:00Z'
              description: Employee requests enrollment to the leadership excellence training. Waiting for senior manager approval to be complete
              due_at: null
              id: '7'
              organization_id: null
              priority: normal
              requester_id: '8'
              status: hold
              subject: Training enrollment request
              tags:
                - training_enrollment
              type: task
              updated_at: '2025-09-29T12:00:00Z'
          zendesk_users:
            - active: true
              created_at: '2024-08-15T09:30:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-08-15T09:30:00Z'
              verified: false
            - active: true
              created_at: '2024-07-20T14:15:00Z'
              email: michael.thompson@msg.com
              id: '13'
              name: Michael Thompson
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-07-20T14:15:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                action: search_courses
                category: null
                certification_name: null
                client_id: null
                course_id: null
                email: null
                keyword: Excellence
              tool: degreed_api
            - parameters:
                action: get_course_details
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-3847291
                email: null
              tool: degreed_api
            - parameters:
                action: get_training_history
                category: null
                certification_name: null
                client_id: null
                course_id: null
                email: sarah.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                approver_email: null
                engagement_code: null
                request_type: training_engagement_coordination
                requester_email: sarah.martinez@msg.com
              tool: approval_get_status
            - parameters:
                $filter: requester_id eq '8' and status in ('open','pending','hold') and subject eq 'Training enrollment request'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: get_engagement
                email: null
                engagement_code: ENG-1472583
              tool: mavenlink_api
            - parameters:
                id: '7'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: open
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                approver_email: null
                engagement_code: null
                request_type: training_engagement_coordination
                requester_email: sarah.martinez@msg.com
              tool: approval_get_status
            - parameters:
                action: enroll_employee
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-3847291
                email: sarah.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                id: '7'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: michael.thompson@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: CRS-3847291
                  description: Completed enrollment for employee
                  device_type: null
                  due_at: null
                  engagement_code: ENG-1472583
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  requester_id: null
                  status: solved
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trn_005(x: TestContext, judge: Judge):
    """!
    query: |
        I'd like to enroll in the 'Strategic Client Management' external training (October 14-16, 2025, $4,500). Please sign me up.
    user_context: |
        Your email is [david.martinez@msg.com](mailto:david.martinez@msg.com)

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 4500
              end_date: '2025-10-16T00:00:00'
              id: CRS-2847391
              max_seats: null
              prerequisites: []
              start_date: '2025-10-14T00:00:00'
              title: Strategic Client Management
              training_category: nice_to_have
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-10-31T00:00:00'
              engagement_code: ENG-2583694
              id: ASN-4729583
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-09-15T00:00:00'
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-3694705
              id: ASN-5847293
              senior_manager_email: lisa.chen@msg.com
              start_date: '2025-10-01T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-10-31T00:00:00'
              engagement_code: ENG-2583694
              senior_manager_email: robert.davis@msg.com
              start_date: '2025-09-15T00:00:00'
              status: active
            - end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-3694705
              senior_manager_email: lisa.chen@msg.com
              start_date: '2025-10-01T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements:
            - client_id: CLT-4729583
              end_date: '2025-10-31T00:00:00'
              engagement_code: ENG-2583694
              engagement_manager_email: jennifer.wilson@msg.com
              start_date: '2025-09-15T00:00:00'
              status: active
            - client_id: CLT-5847293
              end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-3694705
              engagement_manager_email: amanda.rodriguez@msg.com
              start_date: '2025-10-01T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Partner
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2018-07-20T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: robert.davis@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Robert Davis
              office_location: New York
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-04-12T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: lisa.chen@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Lisa Chen
              office_location: San Francisco
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2020-01-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: jennifer.wilson@msg.com
              level: Manager
              manager_email: robert.davis@msg.com
              name: Jennifer Wilson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2021-06-08T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: lisa.chen@msg.com,robert.davis@msg.com,sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: CRS-2847391
                  description: David Martinez requests enrollment in external training Strategic Client Management (CRS-2847391), scheduled 2025-10-14 to 2025-10-16, $4,500. Overlaps with active engagements ENG-2583694 and ENG-3694705.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: 'Training Enrollment: Strategic Client Management (CRS-2847391)'
                  tags:
                    - training_enrollment
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: null
                approver_email: robert.davis@msg.com
                engagement_code: ENG-2583694
                request_type: training_engagement_coordination
                requester_email: david.martinez@msg.com
              tool: approval_create_request
            - parameters:
                amount: null
                approver_email: lisa.chen@msg.com
                engagement_code: ENG-3694705
                request_type: training_engagement_coordination
                requester_email: david.martinez@msg.com
              tool: approval_create_request
            - parameters:
                amount: 4500
                approver_email: sarah.thompson@msg.com
                request_type: training_cost
                requester_email: david.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trn_006(x: TestContext, judge: Judge):
    """!
    query: |
        I'd like to enroll in the 'Board Governance & Fiduciary Duties' training scheduled for November 10-12, 2025. Please confirm my registration.
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.



        Your corporate email address is [thomas.anderson@msg.com](mailto:thomas.anderson@msg.com).

        Your direct manager is Elizabeth Chen ([elizabeth.chen@msg.com](mailto:elizabeth.chen@msg.com)).

        Your practice area partner is Robert Martinez ([robert.martinez@msg.com](mailto:robert.martinez@msg.com)).
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 8500
              end_date: '2025-11-12T17:00:00Z'
              id: CRS-1000013
              max_seats: 4
              prerequisites: []
              start_date: '2025-11-10T09:00:00Z'
              title: Board Governance & Fiduciary Duties
              training_category: nice_to_have
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: thomas.anderson@msg.com
              level: Partner
              manager_email: elizabeth.chen@msg.com
              name: Thomas Anderson
              office_location: Chicago
              onboarding_phase: completed
              partner_email: robert.martinez@msg.com
              start_date: '2015-03-01T00:00:00Z'
            - availability_status: available
              backup_approver_email: null
              email: elizabeth.chen@msg.com
              level: Partner
              manager_email: null
              name: Elizabeth Chen
              office_location: New York
              onboarding_phase: completed
              partner_email: null
              start_date: '2005-03-01T00:00:00Z'
            - availability_status: available
              backup_approver_email: null
              email: robert.martinez@msg.com
              level: Partner
              manager_email: null
              name: Robert Martinez
              office_location: Chicago
              onboarding_phase: completed
              partner_email: null
              start_date: '2008-06-15T00:00:00Z'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2015-03-01T00:00:00Z'
              email: thomas.anderson@msg.com
              id: '8'
              name: Thomas Anderson
              organization_id: null
              phone: +1-312-784-2156
              role: end-user
              updated_at: '2015-03-01T00:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: CRS-1000013
                  description: 'Partner requests enrollment in external training Board Governance & Fiduciary Duties (CRS-1000013) scheduled for November 10-12, 2025. Cost: $8,500. Awaiting manager approval.'
                  device_type: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  priority: urgent
                  requester_id: '8'
                  status: open
                  subject: 'Training enrollment: Board Governance & Fiduciary Duties'
                  tags:
                    - training_enrollment
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: 8500
                approver_email: elizabeth.chen@msg.com
                engagement_code: null
                request_type: training_cost
                requester_email: thomas.anderson@msg.com
              tool: approval_create_request
            - parameters:
                amount: 8500
                approver_email: robert.martinez@msg.com
                engagement_code: null
                request_type: training_cost
                requester_email: thomas.anderson@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: elizabeth.chen@msg.com,robert.martinez@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trn_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi Support Team — I’m Sarah Martinez ([sarah.martinez@msg.com]()), Consultant in the Chicago office. My identity details (including DOB) are already on file in Workday. I want to attend the National Data Science Conference 2025 (Oct 22–24, 2025). It’s an external conference and the registration fee is $1,800. Please create the training enrollment request for me and let me know if it’s approved or denied.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 1800
              end_date: '2025-10-24T00:00:00Z'
              id: CRS-4829571
              max_seats: null
              prerequisites: []
              start_date: '2025-10-22T00:00:00Z'
              title: National Data Science Conference 2025
              training_category: conference
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-11-15T00:00:00Z'
              engagement_code: ENG-6927038
              id: ASN-4829571
              senior_manager_email: david.wilson@msg.com
              start_date: '2025-10-01T00:00:00Z'
          mavenlink_mv_engagements:
            - end_date: '2025-11-15T00:00:00Z'
              engagement_code: ENG-6927038
              senior_manager_email: david.wilson@msg.com
              start_date: '2025-10-01T00:00:00Z'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-8472951
              name: TechCorp Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-8472951
              end_date: '2025-11-15T00:00:00Z'
              engagement_code: ENG-6927038
              engagement_manager_email: michael.chen@msg.com
              start_date: '2025-10-01T00:00:00Z'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Consultant
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.wilson@msg.com
              start_date: '2023-03-15T00:00:00Z'
            - availability_status: available
              backup_approver_email: null
              email: david.wilson@msg.com
              level: Partner
              manager_email: david.wilson@msg.com
              name: David Wilson
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.wilson@msg.com
              start_date: '2018-01-15T00:00:00Z'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Request to attend external conference National Data Science Conference 2025, Oct 22–24, 2025, $1,800 registration fee.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: 'Training Enrollment: National Data Science Conference 2025 (Oct 22–24, 2025)'
                  tags:
                    - training_enrollment
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: CRS-4829571
                  description: 'Request denied: Conferences can only be attended after completion of any active engagement. The requested conference dates (Oct 22–24, 2025) overlap your current active engagement (ENG-6927038, Oct 1–Nov 15, 2025).'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trn_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am Michael Rodriguez and my email is [michael.rodriguez@msg.com](mailto:michael.rodriguez@msg.com). I'd like to enroll in the 'Executive Presence & Communication' training (CRS-4829571) scheduled for October 20-22, 2025. FYI, I don't have any conflicts for the given dates. Can you sign me up?
    user_context: |
        Data available to you:

        "level": "Senior Manager",

        "office_location": "Chicago",

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 5200
              end_date: '2025-10-22T17:00:00Z'
              id: CRS-4829571
              max_seats: 0
              prerequisites: []
              start_date: '2025-10-20T09:00:00Z'
              title: Executive Presence & Communication
              training_category: nice_to_have
            - cost: 800
              end_date: '2025-08-16T17:00:00Z'
              id: CRS-1251789
              max_seats: null
              prerequisites: []
              start_date: '2025-08-15T09:00:00Z'
              title: Fundamentals of Leadership
              training_category: nice_to_have
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: michael.rodriguez@msg.com
              end_date: '2025-10-15T00:00:00Z'
              engagement_code: ENG-2847391
              id: ASN-8472951
              senior_manager_email: david.thompson@msg.com
              start_date: '2025-09-01T00:00:00Z'
          mavenlink_mv_engagements:
            - end_date: '2025-10-15T00:00:00Z'
              engagement_code: ENG-2847391
              senior_manager_email: david.thompson@msg.com
              start_date: '2025-09-01T00:00:00Z'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-3847291
              name: TechCorp Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-3847291
              end_date: '2025-10-15T00:00:00Z'
              engagement_code: ENG-2847391
              engagement_manager_email: sarah.chen@msg.com
              start_date: '2025-09-01T00:00:00Z'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: michael.rodriguez@msg.com
              level: Senior Manager
              manager_email: sarah.chen@msg.com
              name: Michael Rodriguez
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.thompson@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.chen@msg.com
              level: Partner
              manager_email: david.thompson@msg.com
              name: Sarah Chen
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.thompson@msg.com
              start_date: '2018-01-10T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: david.thompson@msg.com
              level: Partner
              manager_email: david.thompson@msg.com
              name: David Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: david.thompson@msg.com
              start_date: '2015-06-01T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: michael.rodriguez@msg.com
              id: '8'
              name: Michael Rodriguez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: CRS-4829571
                  description: Employee requested enrollment in 'Executive Presence & Communication' (CRS-4829571) for Oct 20-22, 2025.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: 'Enrollment request: Executive Presence & Communication (CRS-4829571) Oct 20-22, 2025'
                  tags:
                    - training_enrollment
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: check_enrollment
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-4829571
                email: null
                keyword: null
              tool: degreed_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trn_018(x: TestContext, judge: Judge):
    """!
    query: |
        I would like to enroll in the 'Client Presentation Skills' external training scheduled for October 29-30, 2025. I have completed all prerequisites and am currently not assigned to any engagements. Can you help me with the enrollment process?
    user_context: |
        You are Sarah Martinez and your email is [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com)

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 1500
              end_date: '2025-10-30T00:00:00'
              id: CRS-2847391
              max_seats: null
              prerequisites:
                - CRS-1002134
                - CRS-1002135
              start_date: '2025-10-29T00:00:00'
              title: Client Presentation Skills
              training_category: nice_to_have
            - cost: 0
              end_date: '2025-09-20T00:00:00'
              id: CRS-1002134
              max_seats: null
              prerequisites: []
              start_date: '2025-09-20T00:00:00'
              title: Basic Communication Skills
              training_category: must_have
            - cost: 0
              end_date: '2025-09-22T00:00:00'
              id: CRS-1002135
              max_seats: null
              prerequisites: []
              start_date: '2025-09-22T00:00:00'
              title: Professional Presentation Fundamentals
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2025-09-20T00:00:00'
              course_id: CRS-1002134
              employee_email: sarah.martinez@msg.com
              id: ENR-2847391
            - completion_date: '2025-09-22T00:00:00'
              course_id: CRS-1002135
              employee_email: sarah.martinez@msg.com
              id: ENR-2847392
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.thompson@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.chen@msg.com
              start_date: '2025-09-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: michael.thompson@msg.com
              level: Manager
              manager_email: jennifer.chen@msg.com
              name: Michael Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: jennifer.chen@msg.com
              level: Partner
              manager_email: jennifer.chen@msg.com
              name: Jennifer Chen
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.chen@msg.com
              start_date: '2018-01-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2025-09-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: sarah.martinez@msg.com
              tool: workday_api
            - parameters:
                action: get_course_details
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-2847391
                email: null
                keyword: null
              tool: degreed_api
            - parameters:
                action: check_enrollment
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-2847391
                email: null
                keyword: null
              tool: degreed_api
            - parameters:
                action: get_training_history
                category: null
                certification_name: null
                client_id: null
                course_id: null
                email: sarah.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                action: get_employee_assignments
                email: sarah.martinez@msg.com
                engagement_code: null
              tool: mavenlink_api
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Request to enroll in 'Client Presentation Skills' external training scheduled for October 29-30, 2025. Employee has completed all prerequisites and is not assigned to any engagements.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: 'Training Enrollment Request: Client Presentation Skills'
                  tags:
                    - training_enrollment
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                amount: 1500
                approver_email: michael.thompson@msg.com
                engagement_code: null
                request_type: training_cost
                requester_email: sarah.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: michael.thompson@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: CRS-2847391
                  description: Approval requested from manager, updating status to pending while awaiting approval
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trn_021(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is David Martinez and my email is [david.martinez@msg.com](mailto:david.martinez@msg.com). I previously requested enrollment in the Global Consulting Leadership Conference 2025 (November 18-20, external, $4,200) and my ticket was marked as solved three days ago, but I never received any confirmation or enrollment details. I have no active or booked engagements. Can you complete the enrollment today since my approval request was approved?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: 4200
              approver_email: sarah.thompson@msg.com
              engagement_code: null
              id: APR-2847391
              request_type: training_cost
              requester_email: david.martinez@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 4200
              end_date: '2025-11-20T00:00:00'
              id: CRS-2847391
              max_seats: 50
              prerequisites: []
              start_date: '2025-11-18T00:00:00'
              title: Global Consulting Leadership Conference 2025
              training_category: conference
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-3847291
              name: TechCorp Industries
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-3847291
              end_date: '2025-09-30T00:00:00'
              engagement_code: ENG-1847293
              engagement_manager_email: sarah.thompson@msg.com
              start_date: '2025-06-15T00:00:00'
              status: completed
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-08-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments:
            - ItemInternalId: null
              author_id: 157
              body: Training enrollment request approved and processed. You should receive enrollment confirmation within 24-48 hours.
              created_at: '2025-09-28T16:45:00Z'
              html_body: null
              id: 28471
              key: null
              public: true
              ticket_id: 12847
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: 'no'
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: CRS-2847391
              created_at: '2025-09-28T10:15:00Z'
              description: I would like to enroll in the Global Consulting Leadership Conference 2025 scheduled for November 18-20. This is an external conference with a cost of $4,200. I have no active engagements currently.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '12847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: solved
              subject: Training Enrollment - Global Consulting Leadership Conference 2025
              tags:
                - training_enrollment
              type: task
              updated_at: '2025-09-28T16:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '12847'
                item:
                  access_type: null
                  active: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: CRS-2847391
                  description: I would like to enroll in the Global Consulting Leadership Conference 2025 scheduled for November 18-20. This is an external conference with a cost of $4,200. I have no active engagements currently.
                  device_type: null
                  due_at: null
                  email: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: open
                  subject: Training Enrollment - Global Consulting Leadership Conference 2025
                  tags:
                    - training_enrollment
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
            - parameters:
                action: enroll_employee
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-2847391
                email: david.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                id: '12847'
                item:
                  access_type: null
                  active: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: CRS-2847391
                  description: I would like to enroll in the Global Consulting Leadership Conference 2025 scheduled for November 18-20. This is an external conference with a cost of $4,200. I have no active engagements currently.
                  device_type: null
                  due_at: null
                  email: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: solved
                  subject: Training Enrollment - Global Consulting Leadership Conference 2025
                  tags:
                    - training_enrollment
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trn_022(x: TestContext, judge: Judge):
    """!
    query: |
        Hi IT Support,

        **Name:** Sarah Martinez
        **Email:** [sarah.martinez@msg.com]()
        **Level:** Analyst
        **Office:** Chicago

        I’m trying to enroll in the **HIPAA Compliance Certification** training scheduled for **Oct 14–18, 2025**. I’ve completed the prerequisites.

        The dates overlap with my current/upcoming engagements (**ENG-4705816**, **ENG-5816927**, **ENG-6927038**). I’ve already discussed this with my engagement leadership and my management chain and understand that approvals have been provided.

        I submitted this request about **two days ago** and was told a ticket may have been raised for it. Could you please check the status and help finalize my enrollment, and confirm once it’s done?

        Thanks.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: null
              approver_email: lisa.thompson@msg.com
              engagement_code: ENG-4705816
              id: APR-TRN-022-001
              request_type: training_engagement_coordination
              requester_email: sarah.martinez@msg.com
              status: approved
            - amount: null
              approver_email: mark.rodriguez@msg.com
              engagement_code: ENG-5816927
              id: APR-TRN-022-002
              request_type: training_engagement_coordination
              requester_email: sarah.martinez@msg.com
              status: approved
            - amount: null
              approver_email: patricia.lee@msg.com
              engagement_code: ENG-6927038
              id: APR-TRN-022-003
              request_type: training_engagement_coordination
              requester_email: sarah.martinez@msg.com
              status: approved
            - amount: 8500
              approver_email: michael.chen@msg.com
              engagement_code: null
              id: APR-TRN-022-004
              request_type: training_cost
              requester_email: sarah.martinez@msg.com
              status: approved
            - amount: 8500
              approver_email: jennifer.williams@msg.com
              engagement_code: null
              id: APR-TRN-022-005
              request_type: training_cost
              requester_email: sarah.martinez@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests: []
          degreed_certifications: []
          degreed_training_courses:
            - cost: 0
              end_date: null
              id: CRS-9001200
              max_seats: null
              prerequisites: []
              start_date: null
              title: Healthcare Data Privacy Basics (Prerequisite)
              training_category: must_have
            - cost: 8500
              end_date: '2025-10-18T17:00:00Z'
              id: CRS-9001203
              max_seats: 10
              prerequisites:
                - CRS-9001200
              start_date: '2025-10-14T09:00:00Z'
              title: HIPAA Compliance Certification
              training_category: must_have
          degreed_training_enrollments:
            - completion_date: '2025-08-12T16:00:00Z'
              course_id: CRS-9001200
              employee_email: sarah.martinez@msg.com
              id: ENR-9001200-SARAH
            - completion_date: null
              course_id: CRS-9001203
              employee_email: alex.chen@msg.com
              id: ENR-9001203-0001
            - completion_date: null
              course_id: CRS-9001203
              employee_email: maria.gomez@msg.com
              id: ENR-9001203-0002
            - completion_date: null
              course_id: CRS-9001203
              employee_email: jordan.kim@msg.com
              id: ENR-9001203-0003
            - completion_date: null
              course_id: CRS-9001203
              employee_email: priya.shah@msg.com
              id: ENR-9001203-0004
            - completion_date: null
              course_id: CRS-9001203
              employee_email: noah.brown@msg.com
              id: ENR-9001203-0005
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-10-31T00:00:00Z'
              engagement_code: ENG-4705816
              id: ASN-4705816-SM
              senior_manager_email: lisa.thompson@msg.com
              start_date: '2025-09-20T00:00:00Z'
            - assignment_status: active
              employee_email: sarah.martinez@msg.com
              end_date: '2025-11-15T00:00:00Z'
              engagement_code: ENG-5816927
              id: ASN-5816927-SM
              senior_manager_email: mark.rodriguez@msg.com
              start_date: '2025-10-01T00:00:00Z'
            - assignment_status: booked
              employee_email: sarah.martinez@msg.com
              end_date: '2025-12-20T00:00:00Z'
              engagement_code: ENG-6927038
              id: ASN-6927038-SM
              senior_manager_email: patricia.lee@msg.com
              start_date: '2025-10-12T00:00:00Z'
          mavenlink_mv_engagements:
            - end_date: '2025-10-31T00:00:00Z'
              engagement_code: ENG-4705816
              senior_manager_email: lisa.thompson@msg.com
              start_date: '2025-09-20T00:00:00Z'
              status: active
            - end_date: '2025-11-15T00:00:00Z'
              engagement_code: ENG-5816927
              senior_manager_email: mark.rodriguez@msg.com
              start_date: '2025-10-01T00:00:00Z'
              status: active
            - end_date: '2025-12-20T00:00:00Z'
              engagement_code: ENG-6927038
              senior_manager_email: patricia.lee@msg.com
              start_date: '2025-10-12T00:00:00Z'
              status: pipeline
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4705816
              name: MedTech Solutions
              required_training_courses:
                - CRS-9001203
              requires_nda: true
            - clearance_level: standard
              id: CLT-5816927
              name: HealthCare Partners
              required_training_courses:
                - CRS-9001203
              requires_nda: true
            - clearance_level: standard
              id: CLT-6927038
              name: Regional Medical Center
              required_training_courses:
                - CRS-9001203
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4705816
              end_date: '2025-10-31T00:00:00Z'
              engagement_code: ENG-4705816
              engagement_manager_email: david.johnson@msg.com
              start_date: '2025-09-20T00:00:00Z'
              status: active
            - client_id: CLT-5816927
              end_date: '2025-11-15T00:00:00Z'
              engagement_code: ENG-5816927
              engagement_manager_email: robert.davis@msg.com
              start_date: '2025-10-01T00:00:00Z'
              status: active
            - client_id: CLT-6927038
              end_date: '2025-12-20T00:00:00Z'
              engagement_code: ENG-6927038
              engagement_manager_email: amanda.wilson@msg.com
              start_date: '2025-10-12T00:00:00Z'
              status: pipeline
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2023-03-15T00:00:00Z'
            - availability_status: available
              backup_approver_email: null
              email: jennifer.williams@msg.com
              level: Partner
              manager_email: jennifer.williams@msg.com
              name: Jennifer Williams
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2015-06-01T00:00:00Z'
            - availability_status: available
              backup_approver_email: null
              email: lisa.thompson@msg.com
              level: Senior Manager
              manager_email: jennifer.williams@msg.com
              name: Lisa Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2017-04-10T00:00:00Z'
            - availability_status: available
              backup_approver_email: null
              email: mark.rodriguez@msg.com
              level: Senior Manager
              manager_email: jennifer.williams@msg.com
              name: Mark Rodriguez
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2016-09-12T00:00:00Z'
            - availability_status: available
              backup_approver_email: null
              email: patricia.lee@msg.com
              level: Senior Manager
              manager_email: jennifer.williams@msg.com
              name: Patricia Lee
              office_location: Chicago
              onboarding_phase: null
              partner_email: jennifer.williams@msg.com
              start_date: '2018-01-08T00:00:00Z'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - approval_required: 'yes'
              approver_id: lisa.thompson@msg.com,mark.rodriguez@msg.com,patricia.lee@msg.com,michael.chen@msg.com,jennifer.williams@msg.com
              assignee_id: '157'
              course_id: CRS-9001203
              created_at: '2025-09-29T10:15:00Z'
              description: Request to enroll in HIPAA Compliance Certification (mandatory for healthcare client work). Course dates Oct 14–18, 2025 overlap with engagements ENG-4705816, ENG-5816927, and booked ENG-6927038. All prerequisites completed. Approvals already obtained from all engagement senior managers, direct manager, and practice partner.
              engagement_code: null
              id: '2201'
              priority: normal
              requester_id: '8'
              status: open
              subject: 'Training enrollment: HIPAA Compliance Certification (Oct 14–18, 2025)'
              tags:
                - training_enrollment
              type: task
              updated_at: '2025-09-29T10:15:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-29T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                $filter: email eq 'sarah.martinez@msg.com'
                $orderby: null
                $select: id,email,name
                $skip: 0
                $top: 1
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: 'requester_id eq ''8'' and (status eq ''open'' or status eq ''pending'' or status eq ''hold'') and tags/any(t: t eq ''training_enrollment'')'
                $orderby: created_at desc
                $select: id,subject,status,priority,type,tags,custom_fields
                $skip: 0
                $top: 10
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: get_course_details
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-9001203
                email: null
                keyword: null
              tool: degreed_api
            - parameters:
                action: get_training_history
                category: null
                certification_name: null
                client_id: null
                course_id: null
                email: sarah.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                action: check_enrollment
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-9001203
                email: null
                keyword: null
              tool: degreed_api
            - parameters:
                approver_email: null
                engagement_code: null
                request_type: training_engagement_coordination
                requester_email: sarah.martinez@msg.com
              tool: approval_get_status
            - parameters:
                approver_email: null
                engagement_code: null
                request_type: training_cost
                requester_email: sarah.martinez@msg.com
              tool: approval_get_status
            - parameters:
                action: enroll_employee
                category: null
                certification_name: null
                client_id: null
                course_id: CRS-9001203
                email: sarah.martinez@msg.com
                keyword: null
              tool: degreed_api
            - parameters:
                id: '2201'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: jennifer.williams@msg.com,lisa.thompson@msg.com,mark.rodriguez@msg.com,michael.chen@msg.com,patricia.lee@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: CRS-9001203
                  description: Course prerequisites retrieved from catalog and verified via training history. Seat availability confirmed. Approvals verified as approved. Enrollment completed in Degreed for HIPAA Compliance Certification (Oct 14–18, 2025)
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: null
                  status: solved
                  subject: null
                  tags:
                    - training_enrollment
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trv_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Sarah Martinez, e-mail [sarah.martinez@msg.com](mailto:sarah.martinez@msg.com). My travel booking TRV-1234567 to San Francisco was flagged in Concur. The trip departs on October 21, 2025, is for 5 days, flight is economy class for 4 hours, and hotel rate is $180/night. Can you help me understand why it was flagged and what I need to do to proceed?
    user_context: |
        You do not have an engagement code.
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests:
            - departure_date: '2025-10-21T00:00:00'
              destination: San Francisco, CA
              employee_email: sarah.martinez@msg.com
              flight_class: economy
              hotel_rate_per_night: 180
              id: TRV-1234567
              return_date: '2025-10-25T00:00:00'
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: sarah.martinez@msg.com
              level: Analyst
              manager_email: michael.chen@msg.com
              name: Sarah Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: richard.williams@msg.com
              start_date: '2024-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-03-15T09:00:00Z'
              email: sarah.martinez@msg.com
              id: '8'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_travel_booking
                approver_email: null
                booking_id: TRV-1234567
                expense_report_id: null
                override_reason: null
              tool: concur_api
            - parameters:
                brand_id: null
                category: null
                label_names: null
                locale: null
                multibrand: null
                query: Travel Policy
                section: null
              tool: zendesk_search_articles
            - parameters:
                $filter: email eq 'sarah.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Employee Sarah Martinez (Analyst) requests review of travel booking TRV-1234567 to San Francisco (departure 2025-10-21, 5 days, economy class, hotel $180/night). Agent confirms all booking details comply with MSG travel policy. Employee can proceed with booking in Concur.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Travel booking TRV-1234567 flagged in Concur - policy compliance review
                  tags:
                    - travel_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trv_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my travel booking TRV-2345678 is still blocked in Concur. The departure date is October 11, 2025, which is 10 days from now. I'm a Consultant, and I understand this violates the 14-day advance booking policy. The flight is economy class for 3 hours, hotel rate is $185/night, and the trip is 4 days. Can you help me check the status and let me know if I can proceed with the trip. Here's my email [david.martinez@msg.com](mailto:david.martinez@msg.com).
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: 1240
              approver_email: sarah.thompson@msg.com
              engagement_code: null
              id: APR-8472951
              request_type: travel
              requester_email: david.martinez@msg.com
              status: pending
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests:
            - departure_date: '2025-10-11T00:00:00'
              destination: Denver, CO
              employee_email: david.martinez@msg.com
              flight_class: economy
              hotel_rate_per_night: 185
              id: TRV-2345678
              return_date: '2025-10-14T00:00:00'
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Consultant
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2020-08-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: 'yes'
              approver_id: sarah.thompson@msg.com
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-29T14:45:00Z'
              description: 'Request for travel policy exception for booking TRV-2345678. Departure date October 11, 2025 violates 14-day advance booking requirement for Consultant level. Flight: economy class for 3-hour flight. Hotel: $185/night (within policy). Trip duration: 4 days.'
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '12848'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: pending
              subject: Travel Policy Exception Request - TRV-2345678
              tags:
                - travel_support
              type: task
              updated_at: '2025-09-29T15:30:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: +1-312-847-3921
              role: end-user
              updated_at: '2023-03-15T09:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                $filter: email eq 'david.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8' and (status eq 'open' or status eq 'pending' or status eq 'hold')
                $orderby: created_at desc
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: get_travel_booking
                approver_email: null
                booking_id: TRV-2345678
                expense_report_id: null
                override_reason: null
              tool: concur_api
            - parameters:
                id: '12848'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Request for travel policy exception for booking TRV-2345678. Departure date October 11, 2025 violates 14-day advance booking requirement for Consultant level. Flight: economy class for 3-hour flight. Hotel: $185/night (within policy). Trip duration: 4 days.'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Travel Policy Exception Request - TRV-2345678
                  tags:
                    - travel_support
                  type: task
                table: tickets
              tool: zendesk_update_item
            - parameters:
                approver_email: sarah.thompson@msg.com
                engagement_code: null
                request_type: travel
                requester_email: david.martinez@msg.com
              tool: approval_get_status
            - parameters:
                id: '12848'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: pending
                  subject: null
                  tags:
                    - travel_support
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trv_004(x: TestContext, judge: Judge):
    """!
    query: |
        My travel booking (TRV-4567890) to Denver is blocked in Concur. I need you to check the approval status and let me know if I can proceed with the trip. The trip departs in 5 days, I'm flying economy for a 5-hour flight, and my hotel rate is $280/night for 4 days. Here is my email [david.martinez@msg.com](mailto:david.martinez@msg.com).
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: 1850
              approver_email: sarah.thompson@msg.com
              engagement_code: null
              id: APR-8472951
              request_type: travel
              requester_email: david.martinez@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests:
            - departure_date: '2025-10-06T00:00:00'
              destination: Denver, CO
              employee_email: david.martinez@msg.com
              flight_class: economy
              hotel_rate_per_night: 280
              id: TRV-4567890
              return_date: '2025-10-09T00:00:00'
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-08-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                $filter: '''email eq david.martinez@msg.com'''
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: '''requester_id eq 8'''
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: get_travel_booking
                approver_email: null
                booking_id: TRV-4567890
                expense_report_id: null
                override_reason: null
              tool: concur_api
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Manager requests approval for travel booking TRV-4567890 to Denver, departing in 5 days. Flight class: economy, hotel rate: $280/night for 4 days. Blocked in Concur due to 7-day advance booking policy.'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Travel booking exception for TRV-4567890 (Denver, 5 days)
                  tags:
                    - travel_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                approver_email: sarah.thompson@msg.com
                engagement_code: null
                request_type: travel
                requester_email: david.martinez@msg.com
              tool: approval_get_status
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: solved
                  subject: null
                  tags:
                    - travel_support
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trv_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need help with my travel booking TRV-6789012 for my trip to London. It is showing as flagged for review. I am leaving on October 4th, so I need this cleared up immediately. Can you please check why it is held up?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests:
            - departure_date: '2025-10-04T09:00:00Z'
              destination: London
              employee_email: morgan.pierce@msg.com
              flight_class: business
              hotel_rate_per_night: 500
              id: TRV-6789012
              return_date: '2025-10-08T18:00:00Z'
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: morgan.pierce@msg.com
              level: Partner
              manager_email: david.chen@msg.com
              name: Morgan Pierce
              office_location: New York
              onboarding_phase: null
              partner_email: morgan.pierce@msg.com
              start_date: '2018-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2018-03-15T10:00:00Z'
              email: morgan.pierce@msg.com
              id: '8'
              name: Morgan Pierce
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Hi, I need help with my travel booking TRV-6789012 for my trip to London. It is showing as flagged for review. I am leaving on October 4th, so I need this cleared up immediately. Can you please check why it is held up?
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: urgent
                  requester_id: '8'
                  status: open
                  subject: Travel booking TRV-6789012 flagged for review
                  tags:
                    - travel_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: get_employee
                email: morgan.pierce@msg.com
              tool: workday_api
            - parameters:
                action: get_travel_booking
                approver_email: null
                booking_id: TRV-6789012
                expense_report_id: null
                override_reason: null
              tool: concur_api
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trv_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my travel booking (TRV-9012345) to San Francisco was flagged in Concur. The trip is from October 26 to November 2, 2025. It's an 8-day trip, economy flight, and hotel rate is $195/night. Can you help me get this approved? Here is my email [david.martinez@msg.com](mailto:david.martinez@msg.com).
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests:
            - departure_date: '2025-10-26T00:00:00'
              destination: San Francisco, CA
              employee_email: david.martinez@msg.com
              flight_class: economy
              hotel_rate_per_night: 195
              id: TRV-9012345
              return_date: '2025-11-02T00:00:00'
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Senior Consultant
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2021-08-10T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: +1-312-847-3921
              role: end-user
              updated_at: '2025-09-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                $filter: email eq 'david.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8' and (status eq 'open' or status eq 'pending' or status eq 'hold')
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: get_travel_booking
                approver_email: sarah.thompson@msg.com
                booking_id: TRV-9012345
                expense_report_id: null
                override_reason: null
              tool: concur_api
            - parameters:
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Travel booking TRV-9012345 for David Martinez (Senior Consultant) flagged in Concur. Trip: Oct 26 - Nov 2, 2025, 8 days, economy flight, hotel $195/night. Requires manager approval due to trip duration.'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Travel booking TRV-9012345 flagged for approval (8-day trip)
                  tags:
                    - travel_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                email: sarah.thompson@msg.com
              tool: approver_lookup_get_contact
            - parameters:
                amount: 1365
                approver_email: sarah.thompson@msg.com
                engagement_code: null
                request_type: travel
                requester_email: david.martinez@msg.com
              tool: approval_create_request
            - parameters:
                id: '6'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: pending
                  subject: null
                  tags:
                    - travel_support
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trv_010(x: TestContext, judge: Judge):
    """!
    query: |
        My travel booking TRV-2748391 to San Francisco is blocked. The trip is for 3 days, departing October 13, 2025, with a hotel rate of $290/night and business class flight. My manager Sarah Thompson has already approved it. Can you help me resolve this?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: 2848
              approver_email: sarah.thompson@msg.com
              engagement_code: null
              id: APR-2847391
              request_type: travel
              requester_email: david.martinez@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests:
            - departure_date: '2025-10-13T00:00:00'
              destination: San Francisco, CA
              employee_email: david.martinez@msg.com
              flight_class: business
              hotel_rate_per_night: 290
              id: TRV-2748391
              return_date: '2025-10-15T00:00:00'
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Manager
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2022-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Senior Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-08-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                action: get_travel_booking
                approver_email: sarah.thompson@msg.com
                booking_id: TRV-2748391
                expense_report_id: null
              tool: concur_api
            - parameters:
                approver_email: sarah.thompson@msg.com
                engagement_code: null
                request_type: travel
                requester_email: david.martinez@msg.com
              tool: approval_get_status
            - parameters:
                item:
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Employee requests assistance with blocked travel booking TRV-2748391. Booking details: 3-day trip to San Francisco, departure 2025-10-13, hotel rate $290/night, business class for 5-hour flight. Manager approval already in place. Hotel rate and advance booking requirements are met.'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Travel booking TRV-2748391 blocked due to flight class policy violation
                  tags:
                    - travel_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  access_type: null
                  active: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Employee requests assistance with blocked travel booking TRV-2748391. Booking details: 3-day trip to San Francisco, departure 2025-10-13, hotel rate $290/night, business class for 5-hour flight. Manager approval already in place. '
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: '8'
                  role: null
                  status: solved
                  subject: Travel booking TRV-2748391 blocked due to flight class policy violation
                  tags:
                    - travel_support
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trv_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need help with a blocked travel booking. My Concur booking ID is TRV-1122334 and it's being flagged for policy violations. I'm a Senior Manager and I have an engagement code ENG-1122334 for this client travel. My direct manager Sarah Johnson has already approved this exception. Can you help me get this approved so I can proceed with my booking?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: null
              approver_email: sarah.johnson@msg.com
              engagement_code: ENG-1122334
              id: APR-2847391
              request_type: travel
              requester_email: jennifer.patel@msg.com
              status: approved
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests:
            - departure_date: '2025-10-05T08:00:00Z'
              destination: New York, NY
              employee_email: jennifer.patel@msg.com
              flight_class: economy
              hotel_rate_per_night: 310
              id: TRV-1122334
              return_date: '2025-10-11T18:00:00Z'
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: jennifer.patel@msg.com
              end_date: '2025-12-31T00:00:00Z'
              engagement_code: ENG-1122334
              id: ASG-4729183
              senior_manager_email: sarah.johnson@msg.com
              start_date: '2024-09-01T00:00:00Z'
          mavenlink_mv_engagements:
            - end_date: '2025-12-31T00:00:00Z'
              engagement_code: ENG-1122334
              senior_manager_email: sarah.johnson@msg.com
              start_date: '2024-09-01T00:00:00Z'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements:
            - client_id: CLT-0012345
              end_date: '2025-12-31T00:00:00Z'
              engagement_code: ENG-1122334
              engagement_manager_email: sarah.johnson@msg.com
              start_date: '2024-09-01T00:00:00Z'
              status: active
          software_catalog_software_catalog: []
          workday_employees: []
          zendesk_articles:
            - author_id: 157
              body: 'ADVANCE BOOKING REQUIREMENTS:

                - Analyst/Consultant: 14+ days advance booking required

                - Manager/Senior Manager: 7+ days advance booking required

                - Partner: No advance booking requirement

                - Exception: Travel within 48 hours is considered urgent


                FLIGHT CLASS ELIGIBILITY:

                - Analyst/Consultant: Economy class only

                - Manager/Senior Manager: Economy standard; Business class allowed for flights over 6 hours

                - Partner: Any class allowed


                HOTEL RATE CAPS:

                - Analyst/Consultant: $200/night maximum

                - Manager/Senior Manager: $300/night maximum

                - Partner: No limit


                TRIP DURATION:

                - Trips under 7 days: Standard approval

                - Trips 7 days and longer: Manager approval required


                All exceptions to these policies require manager approval.'
              brand_id: null
              category_id: null
              comments_disabled: false
              content_tag_ids: []
              created_at: '2024-01-15T10:00:00Z'
              draft: false
              edited_at: null
              html_url: https://msg.zendesk.com/hc/en-us/articles/KB-0000002
              id: 2
              label_names: []
              locale: en-us
              outdated: false
              outdated_locales: []
              permission_group_id: null
              position: 0
              promoted: false
              result_type: article
              section_id: 1001
              snippet: null
              source_locale: en-us
              title: Travel Policy Compliance Reference
              updated_at: '2024-01-15T10:00:00Z'
              url: https://msg.zendesk.com/hc/en-us/articles/KB-0000002
              user_segment_id: null
              vote_count: 0
              vote_sum: 0
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-29T10:30:00Z'
              description: Need assistance with travel booking TRV-1122334 for upcoming trip to New York
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '12'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: open
              subject: Travel booking assistance for TRV-1122334
              tags:
                - travel_support
              type: task
              updated_at: '2025-09-29T10:30:00Z'
          zendesk_users:
            - active: true
              created_at: '2025-09-15T09:00:00Z'
              email: jennifer.patel@msg.com
              id: '8'
              name: Jennifer Patel
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T09:00:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: jennifer.patel@msg.com
              tool: workday_api
            - parameters:
                $filter: email eq 'jennifer.patel@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8'
                $orderby: created_at desc
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: get_travel_booking
                approver_email: null
                booking_id: TRV-1122334
                expense_report_id: null
                override_reason: null
              tool: concur_api
            - parameters:
                action: validate_engagement_code
                email: null
                engagement_code: ENG-1122334
              tool: mavenlink_api
            - parameters:
                engagement_code: ENG-1122334
              tool: salesforce_crm_get_engagement
            - parameters:
                email: jennifer.patel@msg.com
                engagement_code: ENG-1122334
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                brand_id: null
                category: null
                label_names: null
                locale: null
                multibrand: null
                query: Travel Policy Compliance Reference
                section: null
              tool: zendesk_search_articles
            - parameters:
                approver_email: sarah.johnson@msg.com
                engagement_code: ENG-1122334
                request_type: travel
                requester_email: jennifer.patel@msg.com
              tool: approval_get_status
            - parameters:
                id: '12'
                item:
                  access_type: null
                  active: null
                  approval_required: 'yes'
                  approver_id: sarah.johnson@msg.com
                  asset_id: null
                  assignee_id: null
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: ENG-1122334
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: null
                  role: null
                  status: solved
                  subject: null
                  tags:
                    - travel_support
                  type: task
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trv_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm following up on my travel booking TRV-2233445. It's still blocked in Concur due to the hotel rate and trip duration, and I haven't heard back about the manager approval yet. Can you provide an update or help move this forward? Here is my email [david.martinez@msg.com](mailto:david.martinez@msg.com).
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests:
            - amount: 2100
              approver_email: sarah.thompson@msg.com
              engagement_code: null
              id: APR-8472951
              request_type: travel
              requester_email: david.martinez@msg.com
              status: pending
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests:
            - departure_date: '2025-10-16T00:00:00'
              destination: San Francisco, CA
              employee_email: david.martinez@msg.com
              flight_class: economy
              hotel_rate_per_night: 210
              id: TRV-2233445
              return_date: '2025-10-26T00:00:00'
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments: []
          mavenlink_mv_engagements: []
          okta_application_access_logs: []
          salesforce_crm_clients: []
          salesforce_crm_sf_engagements: []
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Analyst
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
            - availability_status: available
              backup_approver_email: null
              email: sarah.thompson@msg.com
              level: Manager
              manager_email: michael.chen@msg.com
              name: Sarah Thompson
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2019-08-12T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - access_type: null
              approval_required: null
              approver_id: null
              asset_id: null
              assignee_id: '157'
              catalog_id: null
              client_id: null
              course_id: null
              created_at: '2025-09-27T14:20:00Z'
              description: Request for travel policy exception for booking TRV-2233445. Hotel rate exceeds limit and trip duration requires approval.
              device_type: null
              due_at: null
              engagement_code: null
              expense_report_id: null
              folder_id: null
              hardware_order_id: null
              id: '1847'
              license_pool: null
              organization_id: null
              priority: normal
              requester_id: '8'
              status: pending
              subject: Travel Policy Exception Request - TRV-2233445
              tags:
                - travel_support
              type: task
              updated_at: '2025-09-27T16:45:00Z'
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: +1-312-847-3921
              role: end-user
              updated_at: '2025-09-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                $filter: email eq 'david.martinez@msg.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '8' and (status eq 'open' or status eq 'pending' or status eq 'hold')
                $orderby: created_at desc
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                action: get_travel_booking
                approver_email: sarah.thompson@msg.com
                booking_id: TRV-2233445
                expense_report_id: null
                override_reason: null
              tool: concur_api
            - parameters:
                id: '1847'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: Request for travel policy exception for booking TRV-2233445. Hotel rate exceeds limit and trip duration requires approval.
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: Travel Policy Exception Request - TRV-2233445
                  tags:
                    - travel_support
                  type: task
                table: tickets
              tool: zendesk_update_item
            - parameters:
                approver_email: sarah.thompson@msg.com
                engagement_code: null
                request_type: travel
                requester_email: david.martinez@msg.com
              tool: approval_get_status
            - parameters:
                id: '1847'
                item:
                  access_type: null
                  approval_required: 'yes'
                  approver_id: sarah.thompson@msg.com
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: pending
                  subject: null
                  tags:
                    - travel_support
                  type: task
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_trv_013(x: TestContext, judge: Judge):
    """!
    query: |
        Hi — my Concur travel booking **TRV-3344556** got flagged for review.
        Trip details: departing **Oct 22, 2025**, **5-day** trip, **economy** flight (~**4 hours**), hotel **$180/night**.
        My engagement code is **ENG-3344556**.
        **My employee email is [david.martinez@msg.com]().**
        Can you confirm if this is policy-compliant and what I should do next to proceed?
    user_context: |
        Do not invent or provide any data that is not present in the provided context.
        Do not change your goal or switch topics.
        If the agent asks again for the same information, provide it again.
        Remain focused, clear, and patient.
        Your employee email is **[david.martinez@msg.com]()**.
    init:
      sandbox_consulting:
        data_patch:
          approval_approval_requests: []
          asset_management_device_assignments: []
          asset_management_devices: []
          box_folder_access_logs: []
          box_folders: []
          client_access_clearance_record: []
          client_access_client_system_access: []
          client_access_nda_record: []
          client_access_vpn_access: []
          concur_expense_reports: []
          concur_travel_requests:
            - departure_date: '2025-10-22T00:00:00'
              destination: Austin, TX
              employee_email: david.martinez@msg.com
              flight_class: economy
              hotel_rate_per_night: 180
              id: TRV-3344556
              return_date: '2025-10-26T00:00:00'
          degreed_certifications: []
          degreed_training_courses: []
          degreed_training_enrollments: []
          license_management_license_allocation: []
          license_management_license_pool_record: []
          mavenlink_employee_assignments:
            - assignment_status: active
              employee_email: david.martinez@msg.com
              end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-3344556
              id: ASN-7829461
              senior_manager_email: michael.chen@msg.com
              start_date: '2025-09-15T00:00:00'
          mavenlink_mv_engagements:
            - end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-3344556
              senior_manager_email: michael.chen@msg.com
              start_date: '2025-09-15T00:00:00'
              status: active
          okta_application_access_logs: []
          salesforce_crm_clients:
            - clearance_level: standard
              id: CLT-4829573
              name: TechFlow Solutions
              required_training_courses: []
              requires_nda: true
          salesforce_crm_sf_engagements:
            - client_id: CLT-4829573
              end_date: '2025-12-15T00:00:00'
              engagement_code: ENG-3344556
              engagement_manager_email: sarah.thompson@msg.com
              start_date: '2025-09-15T00:00:00'
              status: active
          software_catalog_software_catalog: []
          workday_employees:
            - availability_status: available
              backup_approver_email: null
              email: david.martinez@msg.com
              level: Consultant
              manager_email: sarah.thompson@msg.com
              name: David Martinez
              office_location: Chicago
              onboarding_phase: null
              partner_email: michael.chen@msg.com
              start_date: '2023-03-15T00:00:00'
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-03-15T09:00:00Z'
              email: david.martinez@msg.com
              id: '8'
              name: David Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                $filter: requester_id eq '8'
                $orderby: null
                $select: null
                $skip: null
                $top: 10
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  access_type: null
                  approval_required: null
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: 'Concur travel booking TRV-3344556 flagged for review. Depart 2025-10-22, return 2025-10-26, economy flight (~4 hours), hotel $180/night, duration 5 days. Engagement code provided: ENG-3344556. Request: confirm policy compliance and next steps.'
                  device_type: null
                  due_at: null
                  engagement_code: null
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  organization_id: null
                  priority: normal
                  requester_id: '8'
                  status: open
                  subject: 'Travel booking flagged for review: TRV-3344556'
                  tags:
                    - travel_support
                  type: task
                table: tickets
              tool: zendesk_create_item
            - parameters:
                action: get_employee
                email: david.martinez@msg.com
              tool: workday_api
            - parameters:
                action: get_travel_booking
                approver_email: null
                booking_id: TRV-3344556
                expense_report_id: null
                override_reason: null
              tool: concur_api
            - parameters:
                brand_id: null
                category: null
                label_names: null
                locale: null
                multibrand: null
                query: travel policy 14-day advance booking economy flight hotel cap 200 trip duration 7 days
                section: null
              tool: zendesk_search_articles
            - parameters:
                engagement_code: ENG-3344556
              tool: salesforce_crm_get_engagement
            - parameters:
                email: david.martinez@msg.com
                engagement_code: ENG-3344556
              tool: salesforce_crm_check_employee_assignment
            - parameters:
                id: '6'
                item:
                  access_type: null
                  active: null
                  approval_required: 'no'
                  approver_id: null
                  asset_id: null
                  assignee_id: '157'
                  catalog_id: null
                  client_id: null
                  course_id: null
                  description: null
                  device_type: null
                  due_at: null
                  email: null
                  engagement_code: ENG-3344556
                  expense_report_id: null
                  folder_id: null
                  hardware_order_id: null
                  license_pool: null
                  name: null
                  organization_id: null
                  phone: null
                  priority: normal
                  requester_id: null
                  role: null
                  status: solved
                  subject: null
                  tags:
                    - travel_support
                  type: null
                  verified: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)
