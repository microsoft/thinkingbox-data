# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from thinkingbox.common import Judge, TestContext

"""!
scenario: sandbox_auto_insurance
"""
SERVER_NAME = "sandbox_auto_insurance"


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


def test_bil_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Maria Rodriguez. My payment is past due and I need a few more days to pay. Can you give me an extension on my policy POL-3847291856?
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.



        If asked provide these details:

        Full Name: Maria Rodriguez

        email: [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com)

        phone: (415) 892-3847

        date of birth: 1987-03-15

        policy number: POL-3847291856

        SSN last 4 digits: 5478
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-19'
              customer_id: CUST-847291
              id: BILL-847291856
              installment_amount: null
              installment_count: null
              monthly_payment: 150
              new_due_date: null
              past_due_amount: 150
              payment_received: false
              policy_id: POL-3847291856
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: null
              security_question: null
              ssn_last_4: '5478'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-10-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: F5129876
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-10-01'
              expiration_date: '2025-10-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-10-01'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-10-01'
              effective_date: '2024-10-01'
              id: VEH-847291001
              make: Honda
              model: Civic
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGBH41JXMN109186
              year: 2021
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-15T14:22:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                policy_id: POL-3847291856
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-3847291856
              tool: billing_get_account_details
            - parameters:
                customer_id: CUST-847291
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUST-847291
                security_answer: null
                ssn_last_4: '5478'
              tool: crm_verify_identity
            - parameters:
                id: '847291'
                table: users
              tool: zendesk_get_item
            - parameters:
                months_back: null
                policy_id: POL-3847291856
              tool: claims_get_policy_claims
            - parameters:
                policy_id: POL-3847291856
              tool: billing_get_arrangement_history
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Maria Rodriguez (Named Insured, Standard tier, CA) requested a payment extension. Account was 12 days past due, monthly payment $150, past-due amount $150, 0 prior arrangements in past 12 months. Extension granted, new due date is 2025-10-11.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Payment extension granted for policy POL-3847291856
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                new_due_date: '2025-10-11'
                policy_id: POL-3847291856
              tool: billing_grant_extension
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Maria Rodriguez (Named Insured, Standard tier, CA) requested a payment extension. Account was 12 days past due, monthly payment $150, past-due amount $150, 0 prior arrangements in past 12 months. Extension granted, new due date is 2025-10-11.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: solved
                  subject: Payment extension granted for policy POL-3847291856
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez and my customer id is CUST-789536. I need more time to make my payment for policy POL-4577892231. Can you help me with an extension and also confirm the new due date? There is an open ticket related to the same issue.
    user_context: |
        Rules:

        Provide the below information if the agent asks for verification purposes -

        1) your email id - [maria.rodriguez@outlook.com](mailto:maria.rodriguez@outlook.com)

        2) last 4 digits of your SSN - 8392

        3) your date of birth - 1985-03-22

        4) answer to security question - Buddy

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-09-23'
              customer_id: CUST-789536
              id: BILL-783478
              installment_amount: null
              installment_count: null
              monthly_payment: 20000
              new_due_date: null
              past_due_amount: 20000
              payment_received: false
              policy_id: POL-4577892231
              status: In Grace Period
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Comprehensive – Glass Only
              created_date: '2025-09-15'
              date_of_loss: '2025-09-15'
              driver_id: DRV-789455
              has_bodily_injury: false
              id: CLM-789456
              loss_location: Austin, TX
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: null
              police_report_required: false
              policy_id: POL-4577892231
              severity: Minor
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-785989
              vehicle_vin: 1HGCV1F30JA123579
          crm_customers:
            - date_of_birth: '1985-03-22'
              email: maria.rodriguez@outlook.com
              first_name: Maria
              fraud_flag: false
              id: CUST-789536
              last_name: Rodriguez
              phone: 512-387-0147
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '8392'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-789536
              date_of_birth: '1985-03-22'
              effective_date: '2024-10-01'
              exclusion_form_required: false
              id: DRV-789455
              is_co_insured: false
              is_named_insured: true
              license_number: TX12345578
              license_state: TX
              name: Maria Rodriguez
              policy_id: POL-4577892231
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-789536
              effective_date: '2024-10-01'
              expiration_date: '2026-10-01'
              id: POL-4577892231
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-789536
              renewal_date: '2025-10-01'
              state: TX
              status: In Grace Period
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-10-01'
              effective_date: '2024-10-01'
              id: VEH-785989
              make: Honda
              model: Accord
              policy_id: POL-4577892231
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA123579
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-30T09:00:00Z'
              description: Customer received payment reminder for overdue account. Account is 8 days past due with $200 balance.
              due_at: null
              effective_date_of_change: null
              escalation_level: null
              id: '54322'
              internal_review_type: null
              organization_id: null
              outcome_summary: null
              priority: normal
              request_category: null
              requester_id: '12599'
              status: open
              subject: Payment Reminder - Account Past Due
              tags: []
              type: incident
              updated_at: '2025-09-30T09:00:00Z'
              user_type: null
          zendesk_users:
            - active: true
              created_at: '2024-10-01T13:00:00Z'
              email: maria.rodriguez@outlook.com
              id: '12599'
              name: Maria Rodriguez
              organization_id: '1'
              phone: 512-387-0147
              role: end-user
              updated_at: '2025-10-01T13:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-789536
                security_answer: Buddy
                ssn_last_4: '8392'
              tool: crm_verify_identity
            - parameters:
                customer_id: CUST-789536
              tool: crm_get_customer_profile
            - parameters:
                policy_id: POL-4577892231
              tool: billing_get_account_details
            - parameters:
                policy_id: POL-4577892231
              tool: billing_get_arrangement_history
            - parameters:
                policy_id: POL-4577892231
              tool: claims_check_open_major_claims
            - parameters:
                new_due_date: '2025-10-11'
                policy_id: POL-4577892231
              tool: billing_grant_extension
            - parameters:
                id: '54322'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Billing Extension Request Granted
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '12599'
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Maria Rodriguez and my customer id is CUST-FL-847291. My policy number is POL-3847291058. I'm really worried about my policy being cancelled—I just saw it's scheduled to cancel in 3 days. I need more time to make my payment. Can you please push back my payment due date? My monthly payment is $180 and I owe $360. I had extensions before but I really want to avoid cancellation.
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 7429

        2) Answer to the security question - Buddy

        3) your email id - [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com)

        4) your date of birth - 1987-03-15

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 2
              current_due_date: '2025-09-25'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 180
              new_due_date: null
              past_due_amount: 360
              payment_received: false
              policy_id: POL-3847291058
              status: Pending Cancellation
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Premium
          policy_drivers:
            - customer_id: CUST-FL-847291
              date_of_birth: '1987-03-15'
              effective_date: '2023-02-01'
              exclusion_form_required: false
              id: DRV-FL-847291
              is_co_insured: false
              is_named_insured: true
              license_number: R847291583
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2023-02-01'
              expiration_date: '2026-02-01'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2026-02-01'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2023-02-01'
              effective_date: '2023-02-01'
              id: VEH-FL-847291
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A847291
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-06-01T10:15:00Z'
              description: Customer requested extension on payment due date to avoid cancellation
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '384729'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: solved
              subject: Payment Extension Request
              tags: []
              type: task
              updated_at: '2025-06-01T15:30:00Z'
              user_type: Named Insured
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-03-15T14:20:00Z'
              description: Customer granted 10-day payment extension due to temporary financial hardship
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '291847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: solved
              subject: Billing Extension Approved
              tags: []
              type: task
              updated_at: '2025-03-15T16:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2022-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: '1'
              phone: (305) 847-2931
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-FL-847291
                security_answer: Buddy
                ssn_last_4: '7429'
              tool: crm_verify_identity
            - parameters:
                customer_id: CUST-FL-847291
              tool: crm_get_customer_profile
            - parameters:
                policy_id: POL-3847291058
              tool: billing_get_account_details
            - parameters:
                policy_id: POL-3847291058
              tool: billing_get_arrangement_history
            - parameters:
                policy_id: POL-3847291058
              tool: claims_check_open_major_claims
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Granted 10-day payment extension for Maria Rodriguez (Premium, FL) to avoid cancellation. New due date: 2025-10-11.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: high
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Payment Extension Granted
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                new_due_date: '2025-10-11'
                policy_id: POL-3847291058
              tool: billing_grant_extension
            - parameters:
                id: '8'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: high
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez and my customer id is CUST-847291. I'd like to split my past due payment of $350 into installments on my policy POL-3847291856. Can you please help me with the same? How will the payments be scheduled?
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 8394

        2) Answer to the security question - Buddy

        3) your email id - [sarah.martinez@outlook.com](mailto:sarah.martinez@outlook.com)

        4) your date of birth - 1987-03-22

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-16'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 175
              new_due_date: null
              past_due_amount: 350
              payment_received: false
              policy_id: POL-3847291856
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-22'
              email: sarah.martinez@outlook.com
              first_name: Sarah
              fraud_flag: false
              id: CUST-847291
              last_name: Martinez
              phone: 518-524-0147
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '8394'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1987-03-22'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: M123456789
              license_state: NY
              name: Sarah Martinez
              policy_id: POL-3847291856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-04-15'
              expiration_date: '2026-04-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-04-15'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA123456
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-04-15T10:00:00Z'
              email: sarah.martinez@outlook.com
              id: '847291'
              name: Sarah Martinez
              organization_id: '1'
              phone: 518-524-0147
              role: end-user
              updated_at: '2024-04-15T10:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-847291
                security_answer: Buddy
                ssn_last_4: '8394'
              tool: crm_verify_identity
            - parameters:
                customer_id: CUST-847291
              tool: crm_get_customer_profile
            - parameters:
                policy_id: POL-3847291856
              tool: billing_get_account_details
            - parameters:
                policy_id: POL-3847291856
              tool: billing_get_arrangement_history
            - parameters:
                policy_id: POL-3847291856
              tool: claims_check_open_major_claims
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests to split $350 past due payment into installments. Monthly payment is $175. No prior arrangements in last 12 months. No open claims.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Request to split past due payment into installments
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                installment_amount: 17500
                installment_count: 2
                policy_id: POL-3847291856
              tool: billing_create_installment_plan
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Installment plan created: $175 due immediately (2025-10-01), $175 due in 30 days (2025-10-31). If a payment is missed, policy may be subject to cancellation.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I’m Maria Rodriguez. My payment is 20 days overdue and I owe $660. Can I set up a payment plan to catch up? I’ve had some unexpected expenses and would like to split the amount into installments if possible.
    user_context: |
        Data available to you:

        "email": "maria.rodriguez@gmail.com",

        "first_name": "Maria",

        "last_name": "Rodriguez",

        "date_of_birth": "1985-03-15",

        "phone": "(415) 892-3847",

        "ssn_last_4": "4797",

        "security_question": "Your first animal's name",

        "security_answer": "Buddy"

        "policy id": "POL-3847291856",

        "customer_id": "CUST-847291",

        "state": "CA",

        "status": "Active",

        "effective_date": "2025-01-15",

        "expiration_date": "2026-01-15",

        "renewal_date": "2026-01-15"

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-09-11'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 220
              new_due_date: null
              past_due_amount: 660
              payment_received: false
              policy_id: POL-3847291856
              status: Past Due
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Collision – Multi-Vehicle
              created_date: '2025-09-16T10:30:00Z'
              date_of_loss: '2025-09-15'
              driver_id: null
              has_bodily_injury: false
              id: CLM-847291001
              loss_location: Los Angeles, CA
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: null
              police_report_required: false
              policy_id: POL-3847291856
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291001
              vehicle_vin: null
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: Your first animal's name
              ssn_last_4: '4797'
              tier: Premium
          policy_drivers:
            - customer_id: null
              date_of_birth: '1985-03-15'
              effective_date: '2025-01-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2025-01-15'
              expiration_date: '2026-01-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-01-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-01-15'
              effective_date: '2024-01-15'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263JA123456
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: FNOL – Collision
              created_at: '2025-09-25T09:15:00Z'
              description: Customer needs to provide additional documentation for claim CLM-847291001
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Pending – User Action
              priority: normal
              request_category: Claims
              requester_id: '847291'
              status: pending
              subject: Claim documentation needed
              tags: []
              type: task
              updated_at: '2025-09-25T14:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-02-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: '1'
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-15T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                email: maria.rodriguez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-847291
              tool: crm_get_customer_profile
            - parameters:
                $filter: '''email eq "maria.rodriguez@gmail.com"'''
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Premium tier customer Maria Rodriguez requested a payment plan for $660 past due. 3-installment plan of $220 each granted due to qualifying status and arrangement history. Customer explained unexpected expenses. Arrangement details confirmed in writing.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Payment plan arrangement granted
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                installment_amount: 22000
                installment_count: 3
                policy_id: POL-3847291856
              tool: billing_create_installment_plan
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to set up a payment plan to split my past-due amount for policy POL-2847391652. My payment is 5 days late and I owe $140. Can you help me with an installment plan? My name is Marcus Rodriguez and my email is [marcus.rodriguez@gmail.com](mailto:marcus.rodriguez@gmail.com)
    user_context: |
        Your date of birth is 15 March 1987 and your SSN last 4 digits are 5911

        If asked by the agent whether you want to proceed with payment extension, accept it.



        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-26'
              customer_id: CUS-84729163
              id: BILL-84729163
              installment_amount: null
              installment_count: null
              monthly_payment: 140
              new_due_date: null
              past_due_amount: 140
              payment_received: false
              policy_id: POL-2847391652
              status: In Grace Period
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: marcus.rodriguez@gmail.com
              first_name: Marcus
              fraud_flag: false
              id: CUS-84729163
              last_name: Rodriguez
              phone: (512) 847-2951
              security_answer: Buddy
              security_question: What is your pet's name?
              ssn_last_4: '5911'
              tier: Standard
          policy_drivers:
            - customer_id: CUS-84729163
              date_of_birth: '1987-03-15'
              effective_date: '2024-02-15'
              exclusion_form_required: false
              id: DRV-84729163
              is_co_insured: false
              is_named_insured: true
              license_number: '47291638'
              license_state: TX
              name: Marcus Rodriguez
              policy_id: POL-2847391652
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-84729163
              effective_date: '2024-02-15'
              expiration_date: '2026-02-15'
              id: POL-2847391652
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-84729163
              renewal_date: '2026-02-15'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-02-15'
              effective_date: '2024-02-15'
              id: VEH-84729163
              make: Honda
              model: Accord
              policy_id: POL-2847391652
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A125688
              year: 2003
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-02-01T14:30:00Z'
              description: Customer inquired about when their next payment was due and payment methods available.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '29847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: solved
              subject: Billing Question - Payment Due Date
              tags: []
              type: question
              updated_at: '2025-02-01T15:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-12T10:30:00Z'
              email: marcus.rodriguez@gmail.com
              id: '847291'
              name: Marcus Rodriguez
              organization_id: null
              phone: (512) 847-2951
              role: end-user
              updated_at: '2025-09-26T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested an installment plan for past-due amount. Explained that installment plan requires past-due > 1.5x monthly payment ($140). Offered 10-day extension instead.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Payment Extension Request - Installment Plan Not Eligible
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                new_due_date: '2025-10-11'
                policy_id: POL-2847391652
              tool: billing_grant_extension
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested an installment plan for past-due amount. Explained that installment plan requires past-due > 1.5x monthly payment ($140). Offered 10-day extension instead.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: solved
                  subject: Payment Extension Request - Installment Plan Not Eligible
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, My name is  Maria Rodriguez. My policy ID is POL-3847291058.  I need to split my past due bill. My monthly payment is $190 and I'm behind by 10 days. Can you check my eligibility for having an installment plan and set it up for me if possible? I would not be interested in extension
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.

        When the agent informs about installment ineligibility, make it clear that you are not interested in any other arrangement

        If asked provide following details about yourself:

        Full Name: Maria Rodriguez

        Email: [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com)

        Phone Number: (305) 847-2931

        Date of Birth: 1987-03-15

        Last 4 digits of SSN: 7429

        Answer to security Question: Buddy

        Policy Number: POL-3847291058
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-21'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 190
              new_due_date: null
              past_due_amount: 285
              payment_received: false
              policy_id: POL-3847291058
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-FL-847291
              date_of_birth: '1987-03-15'
              effective_date: '2025-06-15'
              exclusion_form_required: false
              id: DRV-FL-847291
              is_co_insured: false
              is_named_insured: true
              license_number: R847291537
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2025-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2026-06-15'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-06-15'
              effective_date: '2025-06-15'
              id: VEH-FL-847291
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA000001
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2025-06-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (305) 847-2931
              role: end-user
              updated_at: '2025-06-15T10:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                email: maria.rodriguez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-FL-847291
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUST-FL-847291
                security_answer: null
                ssn_last_4: '7429'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-3847291058
              tool: policy_get_policy_details
            - parameters:
                id: '847291'
                table: users
              tool: zendesk_get_item
            - parameters:
                policy_id: POL-3847291058
              tool: billing_get_account_details
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer request installment plan set up to split her past due bill of $285 into multiple payments.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: null
                  requester_id: '847291'
                  status: open
                  subject: Installment plan set up request
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                policy_id: POL-3847291058
              tool: billing_get_arrangement_history
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Maria Rodriguez, customer ID CUS-84729186 e-mail [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com) with policy ID POL-3847291582. My payment is 14 days overdue and I already had a successful extension earlier this year. Can I get more time to pay my $160 past due balance?
    user_context: |
        Your name is Maria Rodriguez. You have the following email: [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). You are born on 1987-03-15. Your  phone number is 415-892-3847. Your last 4 SSN digits are 7429, and your first pets name was Buddy
        If the agent offers to help you with the payment, do not accept it and say that you will complete it later.

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-09-17'
              customer_id: CUS-84729186
              id: BILL-842291
              installment_amount: null
              installment_count: null
              monthly_payment: 160
              new_due_date: null
              past_due_amount: 160
              payment_received: false
              policy_id: POL-3847291582
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUS-84729186
              last_name: Rodriguez
              phone: 415-892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Standard
          policy_drivers:
            - customer_id: CUS-84729186
              date_of_birth: '1987-03-15'
              effective_date: '2025-01-15'
              exclusion_form_required: false
              id: DRV-84729114
              is_co_insured: false
              is_named_insured: true
              license_number: D1254597
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291582
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-84729186
              effective_date: '2025-01-15'
              expiration_date: '2026-01-15'
              id: POL-3847291582
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-84729186
              renewal_date: '2026-01-15'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-01-16'
              effective_date: '2025-01-16'
              id: VEH-84729114
              make: Honda
              model: Accord
              policy_id: POL-3847291582
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263NA122486
              year: 2022
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-05-01T14:20:00Z'
              description: Customer requesting more time to pay their past due balance.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: null
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: open
              subject: Payment extension request
              tags: []
              type: task
              updated_at: '2025-05-01T14:35:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: 415-892-3847
              role: end-user
              updated_at: '2024-08-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUS-84729186
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUS-84729186
                security_answer: Buddy
                ssn_last_4: '7429'
              tool: crm_verify_identity
            - parameters:
                $filter: email eq 'maria.rodriguez@gmail.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '847291'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                policy_id: POL-3847291582
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-3847291582
              tool: billing_get_account_details
            - parameters:
                policy_id: POL-3847291582
              tool: billing_get_arrangement_history
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Ticket for the billing extension request of client with customer ID CUS-84729186
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: 'Arrangement request for user CUS-84729186 '
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: User has reached her limit of arrangements therefore no billing extension can be reached
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Declined
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: Arrangement request declined for user CUS-84729186 due to arrangement limit reached
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my email id is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). I've been a customer for years. My payment is 7 days overdue on my policy POL-3847291582. Can I get an extension on my $210 payment?
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 7429

        2) Answer to the security question - Buddy

        3) your date of birth - 1985-03-15

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: '2'
              current_due_date: '2025-09-24'
              customer_id: CUST-847291
              id: BILL-847291582
              installment_amount: null
              installment_count: null
              monthly_payment: 21000
              new_due_date: null
              past_due_amount: 21000
              payment_received: false
              policy_id: POL-3847291582
              status: In Grace Period
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1985-03-15'
              effective_date: '2019-05-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291582
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2019-05-01'
              expiration_date: '2026-05-01'
              id: POL-3847291582
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-05-01'
              state: CA
              status: In Grace Period
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2019-05-01'
              effective_date: '2019-05-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291582
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA123456
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-01-01T14:30:00Z'
              description: Customer requested payment extension due to temporary financial hardship. Extension granted for 10 days.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847291'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: solved
              subject: Payment Extension Request
              tags: []
              type: task
              updated_at: '2025-01-01T15:45:00Z'
              user_type: Named Insured
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-06-30T11:20:00Z'
              description: Customer requested installment plan to split past due balance. Two-payment installment plan approved.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '15847291'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: solved
              subject: Second Payment Arrangement Request
              tags: []
              type: task
              updated_at: '2025-06-30T12:10:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2019-04-12T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: '1'
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-15T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                email: maria.rodriguez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-847291
                security_answer: Buddy
                ssn_last_4: '7429'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-3847291582
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-3847291582
              tool: billing_get_account_details
            - parameters:
                policy_id: POL-3847291582
              tool: billing_get_arrangement_history
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested payment extension for $210 past-due amount. Request declined as Preferred tier arrangement limit (2 per 12 months) reached. Account is in grace period. Advised customer to make payment as soon as possible to avoid cancellation. Expressed appreciation for loyalty.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Payment Extension Request Declined
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '8'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_010(x: TestContext, judge: Judge):
    """!
    query: |
        I'd like to set up another installment plan for my past due amount of $500. My latest overdue payment was 18 days ago. Previously within this year, my requests for payment arrangement have been granted 3 times. My name is Marcus Rodriguez and my email is [marcus.rodriguez@techcorp.io](mailto:marcus.rodriguez@techcorp.io)
    user_context: |
        Your policy ID is POL-7855783847

        Your date of birth is 15 March 1985 and your SSN last 4 digits is 1194

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics (do not accept any other offer by the agent).

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 3
              current_due_date: '2025-09-13'
              customer_id: CUS-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 250
              new_due_date: null
              past_due_amount: 500
              payment_received: false
              policy_id: POL-7855783847
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: marcus.rodriguez@techcorp.io
              first_name: Marcus
              fraud_flag: false
              id: CUS-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '1194'
              tier: Premium
          policy_drivers:
            - customer_id: CUS-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291
              is_co_insured: false
              is_named_insured: true
              license_number: '12847392'
              license_state: TX
              name: Marcus Rodriguez
              policy_id: POL-7855783847
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-847291
              effective_date: '2025-06-15'
              expiration_date: '2026-06-15'
              id: POL-7855783847
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-847291
              renewal_date: '2026-06-15'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-847291
              make: Honda
              model: Accord
              policy_id: POL-7855783847
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A896854
              year: 2003
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-08-01T09:15:00Z'
              description: Customer requested payment extension due to temporary financial hardship. Granted 10-day extension as third arrangement for the year.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '29847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: solved
              subject: Payment Arrangement Request - Third Extension
              tags: []
              type: task
              updated_at: '2025-08-01T09:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-06-15T10:30:00Z'
              email: marcus.rodriguez@techcorp.io
              id: '847291'
              name: Marcus Rodriguez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-08-01T14:20:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested a new installment plan for $500 past due amount. Premium tier, Texas, 18 days overdue. Already used 3 arrangements in past 12 months (limit reached).
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Installment Plan Request - Arrangement Limit Reached
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Request for additional installment plan declined due to Premium tier arrangement limit (3 per 12 months). Customer informed of policy, rationale, Customer requested a new installment plan for $500 past due amount. Premium tier, Texas, 18 days overdue. Already used 3 arrangements in past 12 months (limit reached).
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: solved
                  subject: Installment Plan Request - Arrangement Limit Reached
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my next payment is due on October 6th with a monthly of $154, but I have a big expense coming up and want to plan ahead. Can I get an extension now, before the payment is due? My name is Maria Rodriguez, my email is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com), and my policy ID is POL-3847291658.
    user_context: |
        Your date of birth is 15 March 1987 and your SSN last 4 digits is 6574

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-06'
              customer_id: CUS-84729163
              id: BILL-84729163
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291658
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUS-84729163
              last_name: Rodriguez
              phone: (305) 847-2951
              security_answer: Luffy
              security_question: What is your pet's name?
              ssn_last_4: '6574'
              tier: Standard
          policy_drivers:
            - customer_id: CUS-84729163
              date_of_birth: '1987-03-15'
              effective_date: '2024-10-01'
              exclusion_form_required: false
              id: DRV-84729163
              is_co_insured: false
              is_named_insured: true
              license_number: R847291635
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291658
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 15
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-84729163
              effective_date: '2024-10-01'
              expiration_date: '2026-10-01'
              id: POL-3847291658
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-84729163
              renewal_date: '2026-10-01'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-10-01'
              effective_date: '2024-10-01'
              id: VEH-84729163
              make: Honda
              model: Accord
              policy_id: POL-3847291658
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A847291
              year: 2003
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-12T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '2847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (305) 847-2951
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Maria Rodriguez (Standard tier, FL, policy POL-3847291658) requests a payment extension before her payment is due. Account status is Current, payment due in 5 days, no past-due amount.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '2847291'
                  status: open
                  subject: Customer requests payment extension before due date
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Maria Rodriguez (Standard tier, FL, policy POL-3847291658) requests a payment extension before her payment is due. Account status is Current, payment due in 5 days, no past-due amount.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '2847291'
                  status: solved
                  subject: Customer requests payment extension before due date
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_013(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Maria Rodriguez. My policy ID is POL-3847291856 and customer ID is CUST-847291. I just realized my policy lapsed 10 days ago. I thought I was just behind on my payment. Can I have more time to pay the $660 I owe?
    user_context: |
        Your name is Maria Rodriguez. You have the following email: [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). You are born on 1985-03-15. Your  phone number is (415) 892-3847. Your last 4 SSN digits are 9012, and your Mother's maiden name was Williams
        Do not ask for creation of payment links. If the agent mentions anything about helping you to create the payment request or transfer, mention that you will do it at a later date.

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-09-11'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 220
              new_due_date: null
              past_due_amount: 660
              payment_received: false
              policy_id: POL-3847291856
              status: Lapsed
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: 415-892-3847
              security_answer: Williams
              security_question: What is your mother's maiden name?
              ssn_last_4: '9012'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1985-03-15'
              effective_date: '2025-04-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 14
              cancellation_date: '2025-09-21'
              cancellation_reason: Non-Payment
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2025-04-01'
              expiration_date: '2026-04-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: true
              lapse_start: '2025-09-21'
              named_insured_id: CUST-847291
              renewal_date: '2026-04-01'
              state: CA
              status: Lapsed
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-04-01'
              effective_date: '2025-04-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F3XJA122446
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: 415-892-3847
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-847291
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUST-847291
                security_answer: Williams
                ssn_last_4: '9012'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-3847291856
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-3847291856
              tool: billing_get_account_details
            - parameters:
                policy_id: POL-3847291856
              tool: billing_get_arrangement_history
            - parameters:
                $filter: email eq 'maria.rodriguez@gmail.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '847291'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Client requested billing payment extension. opening ticket to analysis, but client has a lapsed account in California which means she cannot make any more arrangements until she pays the past due amount in full
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Client requesting extension on billing payment
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: User requested extension however it does not qualify for any arrangement because status of billing account is lapsed. User has time left to complete payment in full. User payment is awaited and ticket set to pending
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Pending – User Action
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: pending
                  subject: 'Pending - waiting for customer payment in full of due amount '
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Gonzalez, date of birth is 1987-03-15. I know my account is about to be cancelled in 2 days, my policy number is POL-4729183847 but I just had a major accident and was hospitalized. I have an open claim (CLM-847291-001) and I really need to keep my coverage. Can you please give me an extension on my $155 past-due payment?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-03'
              customer_id: CUS-84729101
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 155
              new_due_date: null
              past_due_amount: 155
              payment_received: false
              policy_id: POL-4729183847
              status: Pending Cancellation
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Collision – Single Vehicle
              created_date: '2025-09-17'
              date_of_loss: '2025-09-17'
              driver_id: DRV-84729101
              has_bodily_injury: true
              id: CLM-847291-001
              loss_location: Austin, TX
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: APD-2025-847291
              police_report_required: true
              policy_id: POL-4729183847
              severity: Major
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-84729101
              vehicle_vin: 1HGCM82633A847291
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.gonzalez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUS-84729101
              last_name: Gonzalez
              phone: (512) 847-2931
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: null
              tier: Standard
          policy_drivers:
            - customer_id: CUS-84729101
              date_of_birth: '1987-03-15'
              effective_date: '2024-10-03'
              exclusion_form_required: false
              id: DRV-84729101
              is_co_insured: false
              is_named_insured: true
              license_number: TX12847291
              license_state: TX
              name: Maria Gonzalez
              policy_id: POL-4729183847
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-84729101
              effective_date: '2024-10-03'
              expiration_date: '2025-10-03'
              id: POL-4729183847
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-84729101
              renewal_date: '2025-10-03'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-10-03'
              effective_date: '2024-10-03'
              id: VEH-84729101
              make: Honda
              model: Accord
              policy_id: POL-4729183847
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A847291
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: FNOL – Collision
              created_at: '2025-09-17T14:30:00Z'
              description: 'Customer Maria Gonzalez reported being involved in an accident in Austin. Customer experienced neck pain and was transported to hospital by ambulance. Police report filed. Claim created: CLM-847291-001'
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: high
              request_category: Claims
              requester_id: '847291'
              status: solved
              subject: FNOL - Single vehicle accident with injuries
              tags: []
              type: incident
              updated_at: '2025-09-17T16:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-10-03T10:00:00Z'
              email: maria.gonzalez@gmail.com
              id: '847291'
              name: Maria Gonzalez
              organization_id: null
              phone: (512) 847-2931
              role: end-user
              updated_at: '2025-09-17T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer Maria Gonzalez (CLM-847291-001) requested an extension on her $155 past-due payment. She has an open major claim and was hospitalized. Per policy, Standard tier customers with a Major severity open claim are not eligible for extensions or payment arrangements.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: high
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Request for payment extension due to major accident claim
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: null
                  request_category: Billing & Payments
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_015(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez and my email id is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). I need to set up a payment plan for my past-due balance. My payment is 11 days late and I owe $400. Can I split this into installments? My policy number is POL-3847291058.
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 4178

        2) Answer to the security question - Buddy

        3) your date of birth - 1987-03-15

        If the agent offers 10-days extension, accept it.

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-20'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 200
              new_due_date: null
              past_due_amount: 400
              payment_received: false
              policy_id: POL-3847291058
              status: Past Due
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Collision – Multi-Vehicle
              created_date: '2025-09-15'
              date_of_loss: '2025-09-15'
              driver_id: DRV-FL-847291
              has_bodily_injury: false
              id: CLM-FL-847291-001
              loss_location: Miami, FL
              other_party_insurance: State Farm
              other_party_name: James Thompson
              other_party_phone: (305) 294-8371
              police_report_number: MPD-2025-847291
              police_report_required: true
              policy_id: POL-3847291058
              severity: Major
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-FL-847291
              vehicle_vin: 1HGCV1F30JA847291
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '4178'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-FL-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-FL-847291
              is_co_insured: false
              is_named_insured: true
              license_number: R847291583
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2024-04-15'
              expiration_date: '2026-04-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2025-04-15'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-FL-847291
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA847291
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: FNOL – Collision
              created_at: '2025-09-15T16:45:00Z'
              description: Customer reported rear-end collision on 9/15/25. Vehicle is total loss. Claim created for review.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Claims Adjuster
              organization_id: null
              outcome_summary: Pending – Internal Review
              priority: high
              request_category: Claims
              requester_id: '847291'
              status: hold
              subject: Vehicle Total Loss Claim - Rear-End Collision
              tags: []
              type: incident
              updated_at: '2025-09-15T16:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-04-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: '1'
              phone: (305) 847-2931
              role: end-user
              updated_at: '2025-09-15T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requested installment plan for $400 past-due balance. Installment not allowed due to open major claim. 10-day extension granted, new due date: 2025-10-11. Customer informed of policy limitation.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Payment Extension Granted - Past Due Balance
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                new_due_date: '2025-10-11'
                policy_id: POL-3847291058
              tool: billing_grant_extension
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Billing & Payments
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_016(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Maria Rodriguez, customer ID CUS-84721091 and policy ID POL-3847291856. I know my payment is late because of the accident, but can I get just a few more days to pay? An extension of maximum time possible would help me a lot.
    user_context: |
        Your phone number is 415-892-3847. Your date of birth is 1985-03-15 and last 4 SSN are 9012. Your mother's maiden name is Williams. Your e-mail is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com)
        If the agent grants you the extension send a message being surprised it is possible and thank him.
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-09-25'
              customer_id: CUS-84721091
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 170
              new_due_date: null
              past_due_amount: 170
              payment_received: false
              policy_id: POL-3847291856
              status: In Grace Period
          claims_claims:
            - claim_stage: Open – Investigation
              claim_type: Collision – Hit and Run
              created_date: '2025-08-16'
              date_of_loss: '2025-08-15'
              driver_id: DRV-847291001
              has_bodily_injury: true
              id: CLM-1400500003
              loss_location: New York, NY
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: NY-2022-33221
              police_report_required: true
              policy_id: POL-3847291856
              severity: Major
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291001
              vehicle_vin: 1HGCV1F3XJA122446
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUS-84721091
              last_name: Rodriguez
              phone: 415-892-3847
              security_answer: Williams
              security_question: What is your mother's maiden name?
              ssn_last_4: '9012'
              tier: Preferred
          policy_drivers:
            - customer_id: CUS-84721091
              date_of_birth: '1985-03-15'
              effective_date: '2025-04-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 14
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-84721091
              effective_date: '2025-04-01'
              expiration_date: '2026-04-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-84721091
              renewal_date: '2026-04-01'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-04-01'
              effective_date: '2025-04-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F3XJA122446
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: 415-892-3847
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUS-84721091
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUS-84721091
                security_answer: Williams
                ssn_last_4: '9012'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-3847291856
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-3847291856
              tool: billing_get_account_details
            - parameters:
                policy_id: POL-3847291856
              tool: billing_get_arrangement_history
            - parameters:
                policy_id: POL-3847291856
              tool: claims_check_open_major_claims
            - parameters:
                new_due_date: '2025-10-11'
                policy_id: POL-3847291856
              tool: billing_grant_extension
            - parameters:
                $filter: email eq 'maria.rodriguez@gmail.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '847291'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Granting billing extension of 10 days to customer with ID CUS-84721091 and billing account in grace period
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: high
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Granting billing extension
                  tags: null
                  type: task
                  user_type: null
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Successfully granted billing extension of 10 days to customer with ID CUS-84721091 and billing account in grace period
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: high
                  requester_id: '847291'
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_017(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez, date of birth is 1985-03-22, and my email address is [sarah.martinez@gmail.com](mailto:sarah.martinez@gmail.com). My payment is 16 days overdue, my policy number is POL-3847291856 but I have a major claim (CLM-84729102) open for my Honda Accord. Can I split the $460 I owe into payments?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-15'
              customer_id: CUS-84729102
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 230
              new_due_date: null
              past_due_amount: 460
              payment_received: false
              policy_id: POL-3847291856
              status: Past Due
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Collision – Single Vehicle
              created_date: '2025-09-20T16:30:00Z'
              date_of_loss: '2025-09-20'
              driver_id: DRV-84729102
              has_bodily_injury: true
              id: CLM-84729102
              loss_location: San Francisco, CA
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: SFPD-2025-092001
              police_report_required: true
              policy_id: POL-3847291856
              severity: Major
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-84729102
              vehicle_vin: 1HGCV1F53KA149587
          crm_customers:
            - date_of_birth: '1985-03-22'
              email: sarah.martinez@gmail.com
              first_name: Sarah
              fraud_flag: false
              id: CUS-84729102
              last_name: Martinez
              phone: (415) 892-3847
              security_answer: California
              security_question: What city were you born in?
              ssn_last_4: null
              tier: Premium
          policy_drivers:
            - customer_id: CUS-84729102
              date_of_birth: '1985-03-22'
              effective_date: '2024-02-01'
              exclusion_form_required: false
              id: DRV-84729102
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Sarah Martinez
              policy_id: POL-3847291856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-84729102
              effective_date: '2024-02-01'
              expiration_date: '2025-10-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-84729102
              renewal_date: '2025-10-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-02-01'
              effective_date: '2024-02-01'
              id: VEH-84729102
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F53KA149587
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: FNOL – Collision
              created_at: '2025-09-20T16:45:00Z'
              description: Customer reported single vehicle accident with injuries on 9/20/25. Claim CLM-84729102 created. Investigation in progress.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: high
              request_category: Claims
              requester_id: '847291'
              status: solved
              subject: Major collision claim - injuries reported
              tags: []
              type: incident
              updated_at: '2025-09-25T11:00:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: sarah.martinez@gmail.com
              id: '847291'
              name: Sarah Martinez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Premium customer Sarah Martinez (POL-3847291856) requested installment plans for $460 past-due. '
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Installment plan requested for past-due payment
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                installment_amount: 23000
                installment_count: 2
                policy_id: POL-3847291856
              tool: billing_create_installment_plan
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Billing & Payments
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_018(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez and my email id is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com) . My policy (POL-8472916583) is about to be cancelled tomorrow because I owe $840. Can you set up a 3-payment plan for me to stop the cancellation? I need to split the amount into three payments. I'm a Premium customer in Texas and I really need to keep my coverage active.
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 4264

        2) Answer to the security question - Buddy

        3) your date of birth - 1985-03-15

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: '2'
              current_due_date: '2025-09-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 280
              new_due_date: null
              past_due_amount: 840
              payment_received: false
              policy_id: POL-8472916583
              status: Pending Cancellation
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Collision – Multi-Vehicle
              created_date: '2025-09-21T10:15:00Z'
              date_of_loss: '2025-09-20'
              driver_id: DRV-847291
              has_bodily_injury: false
              id: CLM-847291
              loss_location: Austin, TX
              other_party_insurance: State Farm
              other_party_name: James Wilson
              other_party_phone: (512) 394-8271
              police_report_number: APD-2025-092047
              police_report_required: true
              policy_id: POL-8472916583
              severity: Major
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291
              vehicle_vin: 1HGCV1F30JA847291
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '4264'
              tier: Premium
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-847291
              is_co_insured: false
              is_named_insured: true
              license_number: TX12847392
              license_state: TX
              name: Maria Rodriguez
              policy_id: POL-8472916583
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: '2025-10-02'
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-04-15'
              expiration_date: '2026-04-15'
              id: POL-8472916583
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-04-15'
              state: TX
              status: Pending Cancellation
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-847291
              make: Honda
              model: Accord
              policy_id: POL-8472916583
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA847291
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-28T14:20:00Z'
              description: 'Customer policy POL-8472916583 is scheduled for cancellation on 2025-10-02 due to non-payment. Past due amount: $840.00. Customer has been notified via automated system.'
              due_at: null
              effective_date_of_change: null
              escalation_level: null
              id: '12847'
              internal_review_type: null
              organization_id: null
              outcome_summary: null
              priority: high
              request_category: null
              requester_id: '847291'
              status: open
              subject: Policy Cancellation Notice - POL-8472916583
              tags: []
              type: incident
              updated_at: '2025-09-28T14:20:00Z'
              user_type: null
          zendesk_users:
            - active: true
              created_at: '2024-04-10T09:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: '1'
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                installment_amount: 28000
                installment_count: 3
                policy_id: POL-8472916583
              tool: billing_create_installment_plan
            - parameters:
                id: '12847'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: high
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_019(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my email id is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). I need help with my bill. My payment is late and I'm not sure what options I have. My policy number is POL-3847291058.
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 7429

        2) Answer to the security question - Buddy

        3) your date of birth - 1987-03-15

        When the agent asks to choose between installment and extension, choose installment.

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-22'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 145
              new_due_date: null
              past_due_amount: 290
              payment_received: false
              policy_id: POL-3847291058
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-FL-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-03-01'
              exclusion_form_required: false
              id: DRV-FL-847291
              is_co_insured: false
              is_named_insured: true
              license_number: R847291583
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2024-03-01'
              expiration_date: '2026-03-01'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2025-03-01'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-03-01'
              effective_date: '2024-03-01'
              id: VEH-FL-847291
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA847291
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-01-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '2847'
              name: Maria Rodriguez
              organization_id: '1'
              phone: (305) 847-2931
              role: end-user
              updated_at: '2024-01-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                email: maria.rodriguez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-FL-847291
              tool: crm_get_customer_profile
            - parameters:
                policy_id: POL-3847291058
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-3847291058
              tool: billing_get_account_details
            - parameters:
                policy_id: POL-3847291058
              tool: billing_get_arrangement_history
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer Maria Rodriguez requests help with past-due bill. Needs options explained (extension or installment plan).
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '2847'
                  status: open
                  subject: Billing assistance request - Past Due
                  tags: null
                  type: question
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                installment_amount: 14500
                installment_count: 2
                policy_id: POL-3847291058
              tool: billing_create_installment_plan
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_020(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez, customer ID CUS-84729186, e-mail [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com) and policy POL-3847291582. I need help with my payment situation. My payment is 13 days overdue and I’m not sure what options I have. I have to pay 195 dollars. Can you tell me what I can do?
    user_context: |
        Your name is Maria Rodriguez. You have the following email: [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). You are born on 1987-03-15. Your  phone number is 415-892-3847. Your last 4 SSN digits are 7429, and your first pets name was Buddy

        If the agent offers you a billing extension, you must accept it.
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-18'
              customer_id: CUS-84729186
              id: BILL-842291
              installment_amount: null
              installment_count: null
              monthly_payment: 195
              new_due_date: null
              past_due_amount: 195
              payment_received: false
              policy_id: POL-3847291582
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUS-84729186
              last_name: Rodriguez
              phone: 415-892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Preferred
          policy_drivers:
            - customer_id: CUS-84729186
              date_of_birth: '1987-03-15'
              effective_date: '2025-01-15'
              exclusion_form_required: false
              id: DRV-84729114
              is_co_insured: false
              is_named_insured: true
              license_number: D1254597
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291582
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-84729186
              effective_date: '2025-01-15'
              expiration_date: '2026-01-15'
              id: POL-3847291582
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-84729186
              renewal_date: '2026-01-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-01-16'
              effective_date: '2025-01-16'
              id: VEH-84729114
              make: Honda
              model: Accord
              policy_id: POL-3847291582
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263NA122486
              year: 2022
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-04-01T14:20:00Z'
              description: Customer requested proof of insurance and ID card for vehicle registration
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Documents
              requester_id: '847291'
              status: solved
              subject: Request for Policy Documents
              tags: []
              type: task
              updated_at: '2025-04-01T14:35:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: 415-892-3847
              role: end-user
              updated_at: '2024-08-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUS-84729186
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUS-84729186
                security_answer: Buddy
                ssn_last_4: '7429'
              tool: crm_verify_identity
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer asked about options for payment, opening ticket to check possibilities, will suggest billing extension if customer situation allows
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Overdue payment arrangement inquiry
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                policy_id: POL-3847291582
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-3847291582
              tool: billing_get_account_details
            - parameters:
                policy_id: POL-3847291582
              tool: billing_get_arrangement_history
            - parameters:
                $filter: email eq 'maria.rodriguez@gmail.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '847291'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                new_due_date: '2025-10-11'
                policy_id: POL-3847291582
              tool: billing_grant_extension
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Granted 10 day billing extension to customer Maria Rodriguez '
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: solved
                  subject: Granted 10 day billing extension to customer Maria Rodriguez
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_021(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need more time to pay my bill. My payment of $165 is 4 days overdue and I have an open claim for a fender bender in Brooklyn last week. Will my claim affect my ability to get a payment extension?
    user_context: |
        You are Maria Rodriguez and your email is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com)

        date_of_birth: 1987-03-15,

        Name of your first pet is Whiskers

        Policy id: POL-3847291856

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-27'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 165
              new_due_date: null
              past_due_amount: 165
              payment_received: false
              policy_id: POL-3847291856
              status: In Grace Period
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Collision – Multi-Vehicle
              created_date: '2025-09-24T16:30:00Z'
              date_of_loss: '2025-09-24'
              driver_id: null
              has_bodily_injury: false
              id: CLM-847291001
              loss_location: Brooklyn, NY
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: NYC2025092401
              police_report_required: false
              policy_id: POL-3847291856
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291001
              vehicle_vin: null
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (212) 847-5692
              security_answer: Whiskers
              security_question: What was the name of your first pet?
              ssn_last_4: null
              tier: Standard
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-10-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: R493164378
              license_state: NY
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-10-01'
              expiration_date: '2025-10-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-10-01'
              state: NY
              status: In Grace Period
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-10-01'
              effective_date: '2024-10-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263JA213658
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: FNOL – Collision
              created_at: '2025-09-24T16:45:00Z'
              description: Customer reported being rear-ended at traffic light in Brooklyn. Minor damage to bumper, no injuries. Police report filed.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Claims
              requester_id: '847291'
              status: open
              subject: FNOL - Rear-end collision on 9/24
              tags: []
              type: incident
              updated_at: '2025-09-24T16:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (212) 847-5692
              role: end-user
              updated_at: '2025-09-27T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests more time to pay $165 bill, 4 days overdue. Open moderate claim for fender bender in Brooklyn last week. Asks if claim affects extension eligibility.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Request for payment extension - 4 days overdue, open claim
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                new_due_date: '2025-10-11'
                policy_id: POL-3847291856
              tool: billing_grant_extension
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: Extension of 10 days granted for $165 past-due payment. Claim does not affect extension eligibility for Standard tier. Customer reassured.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Billing & Payments
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_022(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Maria Rodriguez and my customer id is CUST-FL-847291. My payment is 22 days overdue and I'm between jobs right now. Can I set up an installment plan for my past-due amount of $520 on policy POL-3847291058. My monthly payment is $260. I had a payment arrangement a few months ago, but I need to split this balance into payments if possible.
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 7429

        2) Answer to the security question - Buddy

        3) your email id - [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com)

        4) your date of birth - 1987-03-15

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: '1'
              current_due_date: '2025-09-09'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 260
              new_due_date: null
              past_due_amount: 520
              payment_received: false
              policy_id: POL-3847291058
              status: Past Due
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Comprehensive – Glass Only
              created_date: '2025-09-15'
              date_of_loss: '2025-09-15'
              driver_id: DRV-FL-847291
              has_bodily_injury: false
              id: CLM-FL-847291-001
              loss_location: Miami, FL
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: null
              police_report_required: false
              policy_id: POL-3847291058
              severity: Minor
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-FL-847291
              vehicle_vin: 1HGCV1F30KA847291
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Premium
          policy_drivers:
            - customer_id: CUST-FL-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-FL-847291
              is_co_insured: false
              is_named_insured: true
              license_number: R847291583
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2024-04-15'
              expiration_date: '2026-04-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2025-04-15'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-FL-847291
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30KA847291
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-05-01T09:15:00Z'
              description: Customer requested payment extension due to temporary financial hardship
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847291'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: solved
              subject: Payment Extension Request
              tags: []
              type: task
              updated_at: '2025-05-01T11:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-04-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: '1'
              phone: (305) 847-2931
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-FL-847291
                security_answer: Buddy
                ssn_last_4: '7429'
              tool: crm_verify_identity
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requested a 2-installment plan for $520 past-due balance. Arrangement granted: 2 payments of $260 each. Customer is Premium tier, Florida, Past Due status, 1 prior arrangement in 12 months, open claim is Minor severity.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Installment Plan Arrangement
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                installment_amount: 26000
                installment_count: 2
                policy_id: POL-3847291058
              tool: billing_create_installment_plan
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_023(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez and my policy is about to be cancelled in a few days; I owe $360 and would like to split it into three payments.

        If three payments aren’t allowed, please explain why and proceed with the maximum option I qualify for.


    user_context: |
        User Information:

        Your name is Maria Rodriguez.

        Your email is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com).

        Your date of birth is 1987-03-15.

        Your policy number is POL-4729183650.



        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-01'
              customer_id: CUST-TX-847291
              id: BILL-TX-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 180
              new_due_date: null
              past_due_amount: 360
              payment_received: false
              policy_id: POL-4729183650
              status: Pending Cancellation
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-TX-847291
              date_of_birth: '1987-03-15'
              effective_date: '2025-04-15'
              exclusion_form_required: false
              id: DRV-TX-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: TX47291837
              license_state: TX
              name: Maria Rodriguez
              policy_id: POL-4729183650
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: '2025-10-05'
              cancellation_reason: Non-Payment
              co_insured_id: null
              customer_id: CUST-TX-847291
              effective_date: '2025-04-15'
              expiration_date: '2026-04-15'
              id: POL-4729183650
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2026-04-15'
              state: TX
              status: Pending Cancellation
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-04-15'
              effective_date: '2025-04-15'
              id: VEH-TX-847291-01
              make: Honda
              model: Accord
              policy_id: POL-4729183650
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F14JA045872
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-04-10T09:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '6'
              name: Maria Rodriguez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-11T09:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                email: maria.rodriguez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-TX-847291
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUST-TX-847291
                security_answer: Buddy
                ssn_last_4: '7394'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-4729183650
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-4729183650
              tool: billing_get_account_details
            - parameters:
                policy_id: POL-4729183650
              tool: billing_get_arrangement_history
            - parameters:
                $filter: requester_id eq '6' and (status eq 'open' or status eq 'pending' or status eq 'hold') and request_category eq 'Billing & Payments'
                $orderby: created_at desc
                $select: id,subject,status
                $skip: 0
                $top: 10
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested to split $360 past-due balance. Per policy, only 2 installments allowed. Customer agreed to proceed.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: high
                  request_category: Billing & Payments
                  requester_id: '6'
                  status: open
                  subject: Billing & Payments – Installment Plan Request
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                installment_amount: 18000
                installment_count: 2
                policy_id: POL-4729183650
              tool: billing_create_installment_plan
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_024(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I know my account is past due by $260 and my monthly payment is $130. I had a payment extension about a year ago, but I really need a few extra days to pay this time. Am I still eligible for an extension, or have I reached my limit? My policy number is POL-3847291856. I was given 10 days extension last time, would it be possible to get the same time now?
    user_context: |
        You are Maria Rodriguez, your date of birth is 1987-03-15, last 4 digits of SSN: 7429.

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-14'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 130
              new_due_date: null
              past_due_amount: 260
              payment_received: false
              policy_id: POL-3847291856
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: null
              security_question: null
              ssn_last_4: '7429'
              tier: Standard
          policy_drivers:
            - customer_id: null
              date_of_birth: '1987-03-15'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-04-15'
              expiration_date: '2026-04-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-04-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263JA159826
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2024-08-20T14:30:00Z'
              description: Customer requested payment extension due to temporary financial hardship
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: solved
              subject: Payment Extension Request
              tags: []
              type: task
              updated_at: '2024-08-21T09:15:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-04-15T10:00:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2024-04-15T10:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests a payment extension for $260 past-due amount. Monthly payment is $130. Customer had a previous extension 13 months ago (outside 12-month window). Confirmed eligible for extension.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Payment Extension Request
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                new_due_date: '2025-10-11'
                policy_id: POL-3847291856
              tool: billing_grant_extension
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Billing & Payments
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_025(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Maria Rodriguez. I need to discuss payment options for my auto policy (POL-3847291856). My payment is 3 days overdue and I’m really stressed—this is urgent, I could lose my job if my license gets suspended. My past-due amount is $480. Can you help me figure out what I can do? My email is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com).
    user_context: |
        Rules:

        Your Date of Birth is 1987-03-15.

        Your ssn last four is 2426.

        Your security answer is "Peter".

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-28'
              customer_id: CUS-1847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 24000
              new_due_date: null
              past_due_amount: 48000
              payment_received: false
              policy_id: POL-3847291856
              status: In Grace Period
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUS-1847291
              last_name: Rodriguez
              phone: (718) 394-8271
              security_answer: Peter
              security_question: What is your father's middle name?
              ssn_last_4: '2426'
              tier: Premium
          policy_drivers:
            - customer_id: CUS-1847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-02-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: R133756889
              license_state: NY
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-1847291
              effective_date: '2024-02-01'
              expiration_date: '2026-02-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-1847291
              renewal_date: '2026-02-01'
              state: NY
              status: In Grace Period
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-02-01'
              effective_date: '2024-02-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A127486
              year: 2003
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-03-01T14:30:00Z'
              description: Customer called to ask about coverage details for a potential claim scenario. Provided information about comprehensive coverage for weather-related damage. No actual claim filed.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: TKT-847291-001
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Claims
              requester_id: '847291'
              status: solved
              subject: Claim inquiry - coverage question
              tags: []
              type: question
              updated_at: '2025-03-01T15:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (718) 394-8271
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Maria Rodriguez, Premium tier NY customer, requests urgent help with payment options. Account in grace period, $480 past due, no prior arrangements. Stressed about license suspension risk.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: high
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: payment options request - grace period
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                installment_amount: 24000
                installment_count: 2
                policy_id: POL-3847291856
              tool: billing_create_installment_plan
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Maria Rodriguez, Premium tier NY customer, requests urgent help with payment options. Account in grace period, $480 past due, no prior arrangements. Stressed about license suspension risk.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: high
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: solved
                  subject: payment options request - grace period
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_101(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Maria Rodriguez, e-mail email: [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com) phone: (415) 892-3847,  date of birth: 1987-03-15, SSN last 4 digits: 5478. I am the co-insured on policy POL-3847291856. My payment is past due and I need a few more days to pay. Can you give me an extension on the policy?
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-21'
              customer_id: CUST-847291
              id: BILL-847291856
              installment_amount: null
              installment_count: null
              monthly_payment: 165
              new_due_date: null
              past_due_amount: 165
              payment_received: false
              policy_id: POL-3847291856
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: null
              security_question: null
              ssn_last_4: '5478'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-10-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: true
              is_named_insured: false
              license_number: TX5129876
              license_state: TX
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-10-01'
              expiration_date: '2025-12-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-811201
              renewal_date: '2025-10-01'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-10-01'
              effective_date: '2024-10-01'
              id: VEH-847291001
              make: Honda
              model: Civic
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGFC41JXMN109186
              year: 2021
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: '1'
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-15T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Maria Rodriguez (Co-insured, Standard tier, TX) requested a payment extension. Account was 10 days past due, monthly payment $165, past-due amount $165, 0 prior arrangements in past 12 months. Extension granted, new due date is 2025-10-11.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Payment extension granted for policy POL-3847291856
                  tags: null
                  type: task
                  user_type: Co-Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                new_due_date: '2025-10-11'
                policy_id: POL-3847291856
              tool: billing_grant_extension
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_bil_119(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my email id is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). I need help with my bill. My payment is late, and I'm not sure what options I have. My policy number is POL-3847291856, and I am coinsured on it.
    user_context: |
        If the agent requests for the below details for verification purposes, please provide the same.

        Name: Maria Rodriguez

        1) last 4 digits of your SSN - 4264

        2) Answer to the security question - Buddy

        3) your date of birth - 1987-03-15

        When the agent asks to choose between installment and extension, choose installment.

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-23'
              customer_id: CUST-847291
              id: BILL-847291856
              installment_amount: null
              installment_count: null
              monthly_payment: 155
              new_due_date: null
              past_due_amount: 310
              payment_received: false
              policy_id: POL-3847291856
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '4264'
              tier: Standard
            - date_of_birth: '1985-07-22'
              email: carlos.rodriguez@gmail.com
              first_name: Carlos
              fraud_flag: false
              id: CUST-847292
              last_name: Rodriguez
              phone: (415) 892-3848
              security_answer: null
              security_question: null
              ssn_last_4: null
              tier: Standard
          policy_drivers:
            - customer_id: CUST-847292
              date_of_birth: '1985-07-22'
              effective_date: '2024-02-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D1834867
              license_state: CA
              name: Carlos Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: CUST-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-02-01'
              exclusion_form_required: false
              id: DRV-847291002
              is_co_insured: true
              is_named_insured: false
              license_number: D7674371
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Co-Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 14
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-02-01'
              expiration_date: '2026-02-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847292
              renewal_date: '2026-02-01'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-02-01'
              effective_date: '2024-02-01'
              id: VEH-847291001
              make: Honda
              model: Civic
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGBH41JXMN109186
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '2847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-23T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                email: maria.rodriguez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-847291
              tool: crm_get_customer_profile
            - parameters:
                policy_id: POL-3847291856
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-3847291856
              tool: billing_get_account_details
            - parameters:
                policy_id: POL-3847291856
              tool: billing_get_arrangement_history
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Maria Rodriguez (Co-Insured) requests help with late payment. Account is Past Due (8 days), monthly $155, past-due $310, no prior arrangements. Agent to clarify if extension or installment plan is preferred.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '2847291'
                  status: open
                  subject: Customer inquires about payment options for past-due bill
                  tags: null
                  type: task
                  user_type: Co-Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                installment_amount: 15500
                installment_count: 2
                policy_id: POL-3847291856
              tool: billing_create_installment_plan
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Billing & Payments
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Co-Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Marcus Rodriguez, date of birth is 1985-03-15, and my email is [marcus.rodriguez@gmail.com](mailto:marcus.rodriguez@gmail.com). I need proof of insurance for my Honda Accord (VIN: 1HGCV1F30JA122795) on policy POL-4729183856. I just got pulled over and the officer is waiting, help me with a link to access the document immediately since I know it expires in 24 hours from now.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-25'
              customer_id: CUST-TX-847291
              id: BILL-TX-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 375
              payment_received: false
              policy_id: POL-4729183856
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: marcus.rodriguez@gmail.com
              first_name: Marcus
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-TX-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-08-15'
              exclusion_form_required: false
              id: DRV-TX-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: AB1 C345
              license_state: TX
              name: Marcus Rodriguez
              policy_id: POL-4729183856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 14
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-TX-847291
              effective_date: '2024-08-15'
              expiration_date: '2025-10-10'
              id: POL-4729183856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2025-10-10'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-15'
              effective_date: '2024-08-15'
              id: VEH-TX-847291-01
              make: Honda
              model: Accord
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA122795
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-28T14:20:00Z'
              description: Customer requesting extension on past due payment
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '8472'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Pending – User Action
              priority: normal
              request_category: Billing & Payments
              requester_id: '2847'
              status: pending
              subject: Payment Extension Request
              tags: []
              type: task
              updated_at: '2025-09-28T14:20:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: marcus.rodriguez@gmail.com
              id: '2847'
              name: Marcus Rodriguez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2024-08-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer urgently needs proof of insurance for Honda Accord (VIN: 1HGCV1F30JA122795) on policy POL-4729183856 due to being pulled over. Officer is waiting.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: urgent
                  request_category: Documents
                  requester_id: '2847'
                  status: open
                  subject: Urgent Proof of Insurance Request
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                document_type: proof_of_insurance
                expiration_date: '2025-10-02T13:00:05Z'
                policy_id: POL-4729183856
                ticket_id: '7'
              tool: policy_generate_document_link
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Documents
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Michael Rodriguez, date of birth is 1985-03-15, and my email address is [michael.rodriguez@gmail.com](mailto:michael.rodriguez@gmail.com). I need proof of insurance for my policy POL-3847291856. I have to renew my registration at the DMV tomorrow morning and need to make sure I have the document ready. Help me with a link to access the document since I know it expires in 24 hours from now.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (212) 847-3928
              security_answer: Fluffy
              security_question: What is your pet's name?
              ssn_last_4: null
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: KFG-5678
              license_state: NY
              name: Michael Rodriguez
              policy_id: POL-3847291856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 7
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-06-15'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30KA030216
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-02-14T10:30:00Z'
              email: michael.rodriguez@gmail.com
              id: '847291'
              name: Michael Rodriguez
              organization_id: null
              phone: (212) 847-3928
              role: end-user
              updated_at: '2025-09-15T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests proof of insurance for DMV registration renewal tomorrow morning. Needs document link to be available through the morning.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Documents
                  requester_id: '847291'
                  status: open
                  subject: Proof of Insurance for DMV Registration Renewal
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                document_type: proof_of_insurance
                expiration_date: '2025-10-02T13:00:05Z'
                policy_id: POL-3847291856
                ticket_id: '6'
              tool: policy_generate_document_link
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Documents
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Maria Rodriguez, my date of birth is 1987-03-15, and my email is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). I need a copy of my insurance ID card, but I can't remember my policy number or security answer right now—sorry! Can you help me get my ID card?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2026-03-01'
              customer_id: CUS-84729103
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUS-84729103
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: null
              tier: Standard
          policy_drivers:
            - customer_id: CUS-84729103
              date_of_birth: '1987-03-15'
              effective_date: '2024-03-01'
              exclusion_form_required: false
              id: DRV-84729103
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-84729103
              effective_date: '2024-03-01'
              expiration_date: '2026-03-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-84729103
              renewal_date: '2026-03-01'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-03-01'
              effective_date: '2024-03-01'
              id: VEH-84729103
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A123456
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '2847'
              name: Maria Rodriguez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2024-08-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Maria Rodriguez (DOB 1987-03-15, Standard tier, CA, partially verified) requests a copy of her insurance ID card for policy POL-3847291856. No fraud flag. No prior ticket.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: low
                  request_category: Documents
                  requester_id: '2847'
                  status: open
                  subject: Request for insurance ID card
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Pending – User Action
                  priority: null
                  request_category: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am Marcus Rodriguez, my date of birth is 1985-03-15, my email address is [marcus.rodriguez@gmail.com](mailto:marcus.rodriguez@gmail.com), and my policy number is POL-4729183856. Can you tell me what coverages I have on my vehicles? I want to understand my coverages before my claim for the 2019 Honda Accord proceeds.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-TX-847291
              id: BILL-TX-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183856
              status: Current
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Collision – Multi-Vehicle
              created_date: '2025-09-26'
              date_of_loss: '2025-09-25'
              driver_id: DRV-TX-847291
              has_bodily_injury: false
              id: CLM-TX-394827
              loss_location: Austin, TX
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: APD-2025-092501
              police_report_required: true
              policy_id: POL-4729183856
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-TX-294857
              vehicle_vin: 1HGCV1F48KA003922
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: marcus.rodriguez@gmail.com
              first_name: Marcus
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Premium
          policy_drivers:
            - customer_id: CUST-TX-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-TX-847291
              is_co_insured: false
              is_named_insured: true
              license_number: TX12847395
              license_state: TX
              name: Marcus Rodriguez
              policy_id: POL-4729183856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-TX-847291
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-4729183856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2026-06-15'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-TX-294857
              make: Honda
              model: Accord
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: true
              status: Active
              uw_pending: false
              vin: 1HGCV1F48KA003922
              year: 2019
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-TX-294858
              make: Toyota
              model: Corolla
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: true
              status: Active
              uw_pending: false
              vin: 2T1BURHE7JC050127
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: FNOL – Collision
              created_at: '2025-09-26T14:20:00Z'
              description: Customer reported being rear-ended at traffic light on 2025-09-25. Claim CLM-TX-394827 created for 2019 Honda Accord. No injuries reported. Police report APD-2025-092501 obtained.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '6'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Claims
              requester_id: '847291'
              status: open
              subject: Claim filed for rear-end collision
              tags: []
              type: incident
              updated_at: '2025-09-26T14:20:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-06-15T10:30:00Z'
              email: marcus.rodriguez@gmail.com
              id: '847291'
              name: Marcus Rodriguez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-26T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer Marcus Rodriguez requests a summary of coverages for all vehicles on policy POL-4729183856 prior to claim processing.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: low
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Coverage inquiry for active vehicles
                  tags: null
                  type: question
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am Maria Rodriguez, my date of birth is 1978-03-15, my email address is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com), and my policy number is POL-3847291058. I'm considering adding my teenage daughter to my HorizonShield auto policy (POL-3847291058) here in Florida. Can you explain if adding her will increase my premium or not and what information I'd need to provide if I decide to move forward? I am not adding her yet, this is an information-only request.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291058
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: Bella
              security_question: What was the name of your first pet?
              ssn_last_4: null
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-FL-847291
              date_of_birth: '1978-03-15'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-FL-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: R847291583
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2024-04-15'
              expiration_date: '2026-04-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2026-04-15'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-FL-847291-01
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F53KA149587
              year: 2019
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-04-01'
              effective_date: '2025-04-01'
              id: VEH-FL-847291-02
              make: Toyota
              model: Camry
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 4T1C11AK7MU512333
              year: 2021
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-04-01T09:15:00Z'
              description: Customer requested to add a 2021 Toyota Camry to policy POL-3847291058. Vehicle successfully added with effective date 2025-04-01.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '6'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Policy Servicing
              requester_id: '847291'
              status: solved
              subject: Add Vehicle - 2021 Toyota Camry
              tags: []
              type: task
              updated_at: '2025-04-01T11:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-04-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (305) 847-2931
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer Maria Rodriguez (Preferred, FL, Named Insured, policy POL-3847291058) requests information about how adding her teenage daughter as a driver would affect her premium and what information is required.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: low
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: 'Inquiry: Adding Teenage Daughter as Driver'
                  tags: null
                  type: question
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_doc_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez. I have an active auto policy, policy number POL-3847291856. I need a copy of my declarations page and new ID cards. My email is [sarah.martinez@gmail.com](mailto:sarah.martinez@gmail.com), my date of birth is March 15, 1987, and the last four digits of my SSN are 7821. Please send me both documents.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: sarah.martinez@gmail.com
              first_name: Sarah
              fraud_flag: false
              id: CUST-847291
              last_name: Martinez
              phone: (518) 394-7821
              security_answer: null
              security_question: null
              ssn_last_4: '7821'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-02-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: M7429A6813
              license_state: NY
              name: Sarah Martinez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 7
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-02-01'
              expiration_date: '2026-02-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-02-01'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-02-01'
              effective_date: '2024-02-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F3XKA092847
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-12T10:30:00Z'
              email: sarah.martinez@gmail.com
              id: '847291'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests declarations page and ID cards.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: low
                  request_category: Documents
                  requester_id: '847291'
                  status: open
                  subject: Document Request - Declarations Page and ID Cards
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                document_type: declarations_page
                expiration_date: '2025-10-02T13:00:05Z'
                policy_id: POL-3847291856
                ticket_id: '6'
              tool: policy_generate_document_link
            - parameters:
                document_type: id_card
                expiration_date: '2025-10-02T13:00:05Z'
                policy_id: POL-3847291856
                ticket_id: '6'
              tool: policy_generate_document_link
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Documents
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_001(x: TestContext, judge: Judge):
    """!
    query: |
        > Hi — I need to add my son as a driver on my auto policy. My name is Jordan Ramirez, DOB 04/18/1982, policy POL-1000000001.

        > My email is [jordan.ramirez@gmail.com](mailto:jordan.ramirez@gmail.com).

        > My son is Ethan Ramirez, DOB 03/11/2006. He just got his California license (E9182746). Relationship: child.

        > He has a clean record (no accidents or violations in the past 5 years) and no DUI history. Can you add him effective today?
    user_context: |
        **User Agent Instructions**



        - You are the customer **Jordan Ramirez**.
        - Follow these rules:
            - Do not invent any information not provided below.
            - Only answer what the agent asks.
            - If asked again for the same info, repeat it.
            - Stay focused on the request to add a driver.
        - If asked to verify identity, provide:
            - Full name: **Jordan Ramirez**
            - Date of birth: **1982-04-18**
            - Policy number: **POL-1000000001**
            - Email: **[jordan.ramirez@gmail.com](mailto:jordan.ramirez@gmail.com)**
            - SSN last 4: **4567**
            - Security answer: **Civic**
        - If asked about the driver to add, provide:
            - Name: **Ethan Ramirez**
            - Date of birth: **2006-03-11**
            - Relationship: **child** (customer phrasing)
            - License state: **CA**
            - License number: **E9182746**
            - Accidents/violations past 5 years: **none / clean record**
            - DUI/DWI history: **none**
        - If asked about effective date, respond:
            - **Effective today (2025-10-01)**


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-1000001
              id: BILL-1000001
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-1000000001
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1982-04-18'
              email: jordan.ramirez@gmail.com
              first_name: Jordan
              fraud_flag: false
              id: CUST-1000001
              last_name: Ramirez
              phone: +1-415-438-2719
              security_answer: Civic
              security_question: What was your first car?
              ssn_last_4: '4567'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-1000001
              date_of_birth: '1982-04-18'
              effective_date: '2025-01-01'
              exclusion_form_required: false
              id: DRV-2001
              is_co_insured: false
              is_named_insured: true
              license_number: K8041936
              license_state: CA
              name: Jordan Ramirez
              policy_id: POL-1000000001
              relationship: self
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1984-09-02'
              effective_date: '2025-01-01'
              exclusion_form_required: false
              id: DRV-2002
              is_co_insured: false
              is_named_insured: false
              license_number: R5172964
              license_state: CA
              name: Maria Ramirez
              policy_id: POL-1000000001
              relationship: spouse
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 10
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-1000001
              effective_date: '2025-01-01'
              expiration_date: '2026-01-01'
              id: POL-1000000001
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-1000001
              renewal_date: '2026-01-01'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-01-01'
              effective_date: '2025-01-01'
              id: VEH-1001
              make: Toyota
              model: Camry
              policy_id: POL-1000000001
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 4T1G11AK1MU6R3K91
              year: 2021
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-01-01'
              effective_date: '2025-01-01'
              id: VEH-1002
              make: Honda
              model: CR-V
              policy_id: POL-1000000001
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2HKRW2H84KH5M7D28
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2025-01-01T10:00:00Z'
              email: jordan.ramirez@gmail.com
              id: ZD-USER-90001
              name: Jordan Ramirez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-01-01T10:00:00Z'
              verified: true
            - active: true
              created_at: '2025-09-15T14:30:00Z'
              email: sarah.chen@outlook.com
              id: ZD-USER-90002
              name: Sarah Chen
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-15T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                policy_id: POL-1000000001
              tool: policy_get_policy_details
            - parameters:
                $filter: email eq 'jordan.ramirez@gmail.com'
                $orderby: null
                $select: id,email,name,role,active,verified
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq 'ZD-USER-90001' and (status eq 'open' or status eq 'pending' or status eq 'hold')
                $orderby: null
                $select: id,status,subject
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer (Named Insured) requested to add licensed child driver Ethan Ramirez (DOB 2006-03-11), CA license E9182746, effective today (2025-10-01). Customer states clean record and no DUI history.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: null
                  requester_id: ZD-USER-90001
                  status: open
                  subject: 'Policy servicing: add driver (Ethan Ramirez) to POL-1000000001'
                  tags: null
                  type: task
                  user_type: null
                table: tickets
              tool: zendesk_create_item
            - parameters:
                date_of_birth: '2006-03-11'
                effective_date: '2025-10-01'
                exclusion_form_required: false
                license_number: E9182746
                license_state: CA
                name: Ethan Ramirez
                policy_id: POL-1000000001
                relationship: Child
                status: Rated
                uw_pending: false
              tool: policy_add_driver
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez and my customer id is CUST-TX-847291. I'd like to add my spouse, Carlos Rodriguez (DOB: 1990-06-22, TX license #TX99887766), as a driver to my policy POL-4729183856. He has one speeding ticket in the past five years and no DUIs. Can you tell me how this will affect my premium?
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 4526

        2) Answer to the security question - Buddy

        3) your email id - [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com)

        4) your date of birth - 1987-03-15

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-TX-847291
              id: BILL-TX-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '4526'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-TX-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-02-01'
              exclusion_form_required: false
              id: DRV-847291-001
              is_co_insured: false
              is_named_insured: true
              license_number: TX47829156
              license_state: TX
              name: Maria Rodriguez
              policy_id: POL-4729183856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-TX-847291
              effective_date: '2024-02-01'
              expiration_date: '2026-02-01'
              id: POL-4729183856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2026-02-01'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-02-01'
              effective_date: '2024-02-01'
              id: VEH-847291-001
              make: Honda
              model: Accord
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA123456
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-28T14:30:00Z'
              description: Customer asking about next payment due date and payment options
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '47291'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: null
              priority: normal
              request_category: Billing & Payments
              requester_id: '29847'
              status: open
              subject: Billing inquiry - payment due date question
              tags: []
              type: question
              updated_at: '2025-09-28T14:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '29847'
              name: Maria Rodriguez
              organization_id: '1'
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-TX-847291
                security_answer: Buddy
                ssn_last_4: '4526'
              tool: crm_verify_identity
            - parameters:
                customer_id: CUST-TX-847291
              tool: crm_get_customer_profile
            - parameters:
                policy_id: POL-4729183856
              tool: policy_get_policy_details
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requested to add spouse Carlos Rodriguez (DOB: 1990-06-22, TX license #TX99887766) as a driver. 1 speeding ticket in past 5 years, no DUI. Addition processed effective 2025-10-01. Informed customer premium may increase and will be reflected in next billing statement.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '29847'
                  status: open
                  subject: Add spouse Carlos Rodriguez as driver
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                date_of_birth: '1990-06-22'
                effective_date: '2025-10-01'
                exclusion_form_required: false
                license_number: TX99887766
                license_state: TX
                name: Carlos Rodriguez
                policy_id: POL-4729183856
                relationship: Spouse
                status: Rated
                uw_pending: false
              tool: policy_add_driver
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Elena Rodriguez. I need to add my nephew, Gabriel Alvarez, to my auto policy POL-3847291056. He just moved in with us. His date of birth is 2001-06-12, Florida license number A122456689243. He has had a couple tickets in the last five years but no DUIs. Can you add him as a driver starting today?
    user_context: |
        Your name is Maria Elena Rodriguez. Your e-mail is [maria.rodriguez@outlook.com](mailto:maria.rodriguez@outlook.com) and your date of birth is 1987-03-15. Your phone number is 813-492-7638. Your last 4 SSN are 7429 and your first name pet is Bella.

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-11-01'
              customer_id: CUS-00847291
              id: BILL-384729
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291056
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@outlook.com
              first_name: Maria Elena
              fraud_flag: false
              id: CUS-00847291
              last_name: Rodriguez
              phone: 813-492-7638
              security_answer: Bella
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Premium
          policy_drivers:
            - customer_id: null
              date_of_birth: '1987-03-15'
              effective_date: '2025-02-08'
              exclusion_form_required: false
              id: DRV-FL-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: R847291567125
              license_state: FL
              name: Maria Elena Rodriguez
              policy_id: POL-3847291056
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1985-07-22'
              effective_date: '2025-02-08'
              exclusion_form_required: false
              id: DRV-FL-847291-02
              is_co_insured: false
              is_named_insured: false
              license_number: R385729841479
              license_state: FL
              name: Carlos Miguel Rodriguez
              policy_id: POL-3847291056
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '2003-11-08'
              effective_date: '2025-03-20'
              exclusion_form_required: false
              id: DRV-FL-847291-03
              is_co_insured: false
              is_named_insured: false
              license_number: R203847592247
              license_state: FL
              name: Sofia Isabella Rodriguez
              policy_id: POL-3847291056
              relationship: Child
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-00847291
              effective_date: '2025-02-01'
              expiration_date: '2026-02-01'
              id: POL-3847291056
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-00847291
              renewal_date: '2026-02-01'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-02-08'
              effective_date: '2025-02-08'
              id: VEH-00847291
              make: Honda
              model: Accord
              policy_id: POL-3847291056
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F32KA012245
              year: 2019
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-03-20'
              effective_date: '2025-03-20'
              id: VEH-00846291
              make: Hyundai
              model: Elantra
              policy_id: POL-3847291056
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: KMHLM4AG1MU018745
              year: 2021
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-05-01T12:45:00Z'
              description: Customer Maria Elena Rodriguez (POL-3847291056) requested to remove Anghel Maria. Driver was successfully removed from policy
              due_at: null
              effective_date_of_change: '2025-05-01'
              escalation_level: Standard
              id: '6'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Policy Servicing
              requester_id: '847291'
              status: solved
              subject: Remove Driver from Policy POL-3847291056
              tags: []
              type: task
              updated_at: '2025-05-01T13:00:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-12T14:30:00Z'
              email: maria.rodriguez@outlook.com
              id: '847291'
              name: Maria Elena Rodriguez
              organization_id: null
              phone: 813-492-7638
              role: end-user
              updated_at: '2025-09-28T10:15:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUS-00847291
                security_answer: Bella
                ssn_last_4: '7429'
              tool: crm_verify_identity
            - parameters:
                customer_id: CUS-00847291
              tool: crm_get_customer_profile
            - parameters:
                policy_id: POL-3847291056
              tool: policy_get_policy_details
            - parameters:
                $filter: email eq 'maria.rodriguez@outlook.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '847291'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Named insurer requested addition of new driver to policy POL-3847291056
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Addition of driver to policy POL-3847291056
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                date_of_birth: '2001-06-12'
                effective_date: '2025-10-01'
                exclusion_form_required: false
                license_number: A122456689243
                license_state: FL
                name: Gabriel Alvarez
                policy_id: POL-3847291056
                relationship: Nephew
                status: Rated
                uw_pending: false
              tool: policy_add_driver
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Added driver Gabriel Alvarez to policy Addition of driver to policy POL-3847291056
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: solved
                  subject: Addition of driver to policy POL-3847291056
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi! I'm Rebecca Martinez. I have a pending ticket, I now have the information you need to move forward. I'd like to add my daughter, Sofia Martinez (DOB: 08/22/2001, CA license D9876543), as a driver to my policy with the policy ID POL-3847291056. She has four speeding tickets in the last five years but no DUIs. Can you tell me what the underwriting review means for how long this will take and what happens next?
    user_context: |
        Your name is Rebecca Martinez. Your e-mail address is [rebecca.martinez@gmail.com](mailto:rebecca.martinez@gmail.com) You are born on 1978-03-15. Your phone number is 415-892-3847. Your last 4 SSN numbers are 7394 and your first pet's name was Whiskers

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-3847291056
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291056
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: rebecca.martinez@gmail.com
              first_name: Rebecca
              fraud_flag: false
              id: CUST-847291
              last_name: Martinez
              phone: 415-892-3847
              security_answer: Whiskers
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Standard
          policy_drivers:
            - customer_id: null
              date_of_birth: '1978-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-3847291056-001
              is_co_insured: false
              is_named_insured: true
              license_number: D1224557
              license_state: CA
              name: Rebecca Martinez
              policy_id: POL-3847291056
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-06-15'
              expiration_date: '2025-12-15'
              id: POL-3847291056
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-12-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-3847291056-001
              make: Honda
              model: Accord
              policy_id: POL-3847291056
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263KA122446
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-10-01T13:00:00Z'
              description: Customer Rebecca Martinez (Policy POL-3847291056) requesting to add her adult daughter Sofia Martinez. She did not have the necessary information at hand so ticket is pending until named insurer contatcs us again with available information
              due_at: null
              effective_date_of_change: '2025-10-01'
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Pending – User Action
              priority: normal
              request_category: Policy Servicing
              requester_id: '2847'
              status: pending
              subject: Add Driver – Waiting for Named Insured to provide details of daughter
              tags: []
              type: task
              updated_at: '2025-10-01T13:00:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: rebecca.martinez@gmail.com
              id: '2847'
              name: Rebecca Martinez
              organization_id: null
              phone: 415-892-3847
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-847291
                security_answer: Whiskers
                ssn_last_4: '7394'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-3847291056
              tool: policy_get_policy_details
            - parameters:
                $filter: email eq 'rebecca.martinez@gmail.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '2847'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                id: '12847'
                table: tickets
              tool: zendesk_get_item
            - parameters:
                date_of_birth: '2001-08-22'
                effective_date: '2025-10-01'
                exclusion_form_required: false
                license_number: D9876543
                license_state: CA
                name: Sofia Martinez
                policy_id: POL-3847291056
                relationship: Daughter
                status: Rated
                uw_pending: true
              tool: policy_add_driver
            - parameters:
                id: '12847'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: User provided the necessary information to fill in the details of daughter as driver to policy POL-3847291056. Pending until UW check is completed
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '2847'
                  status: hold
                  subject: Addition of driver to policy POL-3847291056
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, My name is Maria Rodriguez.
        I want to add my brother, Juan Rodriguez (DOB: 1990-04-10, TX license: TX-99041023), as a driver to my active policy POL-4729183756 effective today. He has a DUI from 3 years ago and one other ticket. Can you add him? My email address is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com).
    user_context: |
        Rules:

        Your Date of Birth is 1985-03-15.

        Your ssn last four is "7394".

        Your security answer is "Buddy".

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-10-15'
              customer_id: CUS-1847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183756
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUS-1847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What is your pet's name?
              ssn_last_4: '7394'
              tier: Preferred
          policy_drivers:
            - customer_id: null
              date_of_birth: '1985-03-15'
              effective_date: '2025-06-15'
              exclusion_form_required: false
              id: DRV-84729101
              is_co_insured: false
              is_named_insured: true
              license_number: TX-84729156
              license_state: TX
              name: Maria Rodriguez
              policy_id: POL-4729183756
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1983-08-22'
              effective_date: '2025-06-15'
              exclusion_form_required: false
              id: DRV-84729102
              is_co_insured: false
              is_named_insured: false
              license_number: TX-83729847
              license_state: TX
              name: Carlos Rodriguez
              policy_id: POL-4729183756
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 14
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-1847291
              effective_date: '2025-06-15'
              expiration_date: '2026-06-15'
              id: POL-4729183756
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-1847291
              renewal_date: '2026-06-15'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-06-15'
              effective_date: '2025-06-15'
              id: VEH-84729101
              make: Honda
              model: Accord
              policy_id: POL-4729183756
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263JA122476
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-08-01'
              effective_date: '2025-08-01'
              id: VEH-84729102
              make: Ford
              model: F-150
              policy_id: POL-4729183756
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1FTFW1ET5DFC12265
              year: 2013
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-08-01T09:15:00Z'
              description: Customer requested to add 2013 Ford F-150 to policy POL-4729183756. Vehicle acquired 2025-07-28, VIN 1FTFW1ET5DFC12265. Added successfully with effective date 2025-08-01.
              due_at: null
              effective_date_of_change: '2025-08-15'
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Policy Servicing
              requester_id: '847291'
              status: solved
              subject: Add Vehicle - 2013 Ford F-150
              tags: []
              type: task
              updated_at: '2025-08-01T10:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-06-15T10:00:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-15T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: A Preferred tier customer in Texas with an active policy (2 vehicles, 2 existing drivers) wants to add their brother who has a DUI conviction from 3 years ago
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Preferred tier customer in Texas wants to add the brother on the policy
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                date_of_birth: '1990-04-10'
                effective_date: '2025-10-01'
                exclusion_form_required: false
                license_number: TX-99041023
                license_state: TX
                name: Juan Rodriguez
                policy_id: POL-4729183756
                relationship: Brother
                status: Rated
                uw_pending: true
              tool: policy_add_driver
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: A Preferred tier customer in Texas with an active policy (2 vehicles, 2 existing drivers) wants to add their brother who has a DUI conviction from 3 years ago
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: hold
                  subject: Preferred tier customer in Texas wants to add the brother on the policy
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_007(x: TestContext, judge: Judge):
    """!
    query: |
        Please add my spouse, Elena Rodriguez, to my auto policy (POL-3847291058). Her date of birth is 1987-07-22 and her Florida license number is R847291060. She had a DWI two years ago but no other violations. Also, will the DWI significantly increase premium.
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.



        If asked, provide following information

        Your full name: Michael Rodriguez

        Your email address: [michael.rodriguez@gmail.com](mailto:michael.rodriguez@gmail.com)

        Policy ID: POL-3847291058

        Last 4 digits of SSN: 7954

        Security answer: Bob

        Date of birth: 1985-03-15
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 237
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291058
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: Bob
              security_question: What is your dog name?
              ssn_last_4: '7954'
              tier: Premium
          policy_drivers:
            - customer_id: null
              date_of_birth: '1985-03-15'
              effective_date: '2024-12-01'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: R160384972
              license_state: FL
              name: Michael Rodriguez
              policy_id: POL-3847291058
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1987-07-22'
              effective_date: '2024-12-01'
              exclusion_form_required: false
              id: DRV-847291-02
              is_co_insured: false
              is_named_insured: false
              license_number: S928471650
              license_state: FL
              name: Anna Simones
              policy_id: POL-3847291058
              relationship: Listed Driver
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2024-12-01'
              expiration_date: '2025-12-01'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2025-12-01'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-12-01'
              effective_date: '2024-12-01'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCR2F3XJA248935
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-12-01'
              effective_date: '2024-12-01'
              id: VEH-847291-02
              make: Ford
              model: F-150
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1FTEW1E50LFA517824
              year: 2020
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-12-01'
              effective_date: '2024-12-01'
              id: VEH-847291-03
              make: Hyundai
              model: Elantra
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 5NPD74LF7HH873924
              year: 2017
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-08-15T10:30:00Z'
              email: michael.rodriguez@gmail.com
              id: '2847'
              name: Michael Rodriguez
              organization_id: '548'
              phone: (305) 847-2931
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: false
            - active: true
              created_at: '2022-08-15T10:30:00Z'
              email: anna.Simones@gmail.com
              id: '2848'
              name: Anna Simones
              organization_id: null
              phone: (305) 847-5792
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-FL-847291
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUST-FL-847291
                security_answer: null
                ssn_last_4: '7954'
              tool: crm_verify_identity
            - parameters:
                id: '2847'
                table: users
              tool: zendesk_get_item
            - parameters:
                policy_id: POL-3847291058
              tool: policy_get_policy_details
            - parameters:
                active_only: null
                policy_id: POL-3847291058
              tool: policy_get_policy_drivers
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests to add spouse Elena Rodriguez (DOB 1987-07-22, FL license R847291060) as a driver. DWI 2 years ago, no other violations. Premium tier, Florida. Addition flagged for Underwriting review. Customer asked about premium impact.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '2847'
                  status: open
                  subject: 'Add driver: Elena Rodriguez (DWI history) to policy POL-3847291058'
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                date_of_birth: '1987-07-22'
                effective_date: '2025-10-01'
                exclusion_form_required: false
                license_number: R847291060
                license_state: FL
                name: Elena Rodriguez
                policy_id: POL-3847291058
                relationship: Spouse
                status: Rated
                uw_pending: true
              tool: policy_add_driver
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests to add spouse Elena Rodriguez (DOB 1987-07-22, FL license R847291060) as a driver. DWI 2 years ago, no other violations. Premium tier, Florida. Addition flagged for Underwriting review. Customer asked about premium impact.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '2847'
                  status: hold
                  subject: Add Driver
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_008(x: TestContext, judge: Judge):
    """!
    query: |
        I want to add my cousin, Luis Martinez (DOB: 1992-07-10, NY license # M497631825), to my policy POL-3847291058. He just moved in with us and has a DUI from 4 years ago but no other tickets or accidents. I'm not sure whether my cousin's DUI history makes him ineligible to be added to my policy. I'm a Standard tier customer. My name is Maria Rodriguez and my email is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). For verification, my date of birth is 15 March 1985 and my SSN last 4 digits are 7429.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291058
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (718) 394-8271
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Standard
          policy_drivers:
            - customer_id: null
              date_of_birth: '1985-03-15'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: R835196247
              license_state: NY
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1987-08-22'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-847291002
              is_co_insured: false
              is_named_insured: false
              license_number: R719384625
              license_state: NY
              name: Carlos Rodriguez
              policy_id: POL-3847291058
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 7
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-04-15'
              expiration_date: '2026-04-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-04-15'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-84729101
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A123488
              year: 2003
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-04-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (718) 394-8271
              role: end-user
              updated_at: '2024-04-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer Maria Rodriguez (Standard tier, NY) requests to add cousin Luis Martinez (DOB: 1992-07-10, NY license # M497631825) to policy. Luis has a DUI from 4 years ago, otherwise clean record. Per policy, Standard tier cannot add driver with DUI/DWI in past 5 years.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Request to add driver Luis Martinez (DUI history) to policy POL-3847291058
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer Maria Rodriguez (Standard tier, NY) requests to add cousin Luis Martinez (DOB: 1992-07-10, NY license # M497631825) to policy. Luis has a DUI from 4 years ago, otherwise clean record. Per policy, Standard tier cannot add driver with DUI/DWI in past 5 years (request declined).'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: solved
                  subject: Request to add driver Luis Martinez (DUI history) to policy POL-3847291058
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to add my 17-year-old daughter, Sofia Rodriguez (DOB: 2008-09-10), to my policy (POL-3847291856). She only has her learner's permit right now, not a full license. What are my options for getting her covered? What I know is that since she's unlicensed, in California, we cannot rate nor exclude her. My name is Maria Rodriguez and my email is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). For verification, my date of birth is 15 March 1978 and my SSN last 4 digits is 5911.
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 288
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '5911'
              tier: Preferred
          policy_drivers:
            - customer_id: null
              date_of_birth: '1978-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291-001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1975-08-22'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291-002
              is_co_insured: false
              is_named_insured: false
              license_number: D7582946
              license_state: CA
              name: Carlos Rodriguez
              policy_id: POL-3847291856
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '2005-11-10'
              effective_date: '2024-08-20'
              exclusion_form_required: false
              id: DRV-847291-003
              is_co_insured: false
              is_named_insured: false
              license_number: D9384756
              license_state: CA
              name: Miguel Rodriguez
              policy_id: POL-3847291856
              relationship: Son
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-06-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-847291-001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A128856
              year: 2003
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-07-10'
              effective_date: '2024-07-10'
              id: VEH-847291-002
              make: Toyota
              model: Corolla
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2T1BURHE0JC987754
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-28T14:30:00Z'
              description: Customer asking about coverage details for potential claim
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: null
              priority: normal
              request_category: Claims
              requester_id: '847291'
              status: open
              subject: Claim coverage inquiry
              tags: []
              type: question
              updated_at: '2025-09-28T14:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-06-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-20T09:15:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests to add 17-year-old daughter Sofia Rodriguez (learner's permit only) to policy POL-3847291856. California regulations prohibit adding unlicensed drivers or excluding them. Customer informed of options.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Add unlicensed driver request - Sofia Rodriguez
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests to add 17-year-old daughter Sofia Rodriguez (learner's permit only) to policy POL-3847291856. California regulations prohibit adding unlicensed drivers or excluding them. Customer informed of options.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: solved
                  subject: Add unlicensed driver request - Sofia Rodriguez
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez, date of birth March 15, 1985. My policy number is POL-3847291856. I want to add my elderly parent, Carmen Rodriguez (DOB: 1948-06-22), to my auto policy. She lives with me, but her driver’s license was revoked last year due to a medical condition. She never drives, but I want her covered just in case. Can you add her as a driver or exclude her from the policy?


    user_context: |
        **Persona:**

        You are Maria Rodriguez, the Named Insured on a HorizonShield personal auto policy.

        Goal:

        You want to add your elderly parent, Carmen Rodriguez, to your auto policy and are asking whether she can be added as a driver or excluded.

        Rules:

        - Stay in character as the customer at all times.
        - Do not invent or provide information not listed below.
        - Provide verification information exactly as listed when asked.
        - Answer questions honestly and concisely.

        Identity Verification Information (provide when asked):

        - • Full name: Maria Rodriguez
        - • Date of birth: 1985-03-15
        - • Policy number: POL-3847291856
        - • SSN last 4: 4829

        Scenario Facts (repeat if asked):

        - Carmen Rodriguez is your elderly parent.
        - Her date of birth is 1948-06-22.
        - She lives in your household.
        - Her driver’s license was revoked last year due to a medical condition.
        - She does not drive.
        - You are asking whether she can be added as a driver or excluded from the policy.

        Conversation Behavior:

        - Respond clearly and directly to questions.
        - Provide confirmation when asked.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 186
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (212) 847-3928
              security_answer: null
              security_question: null
              ssn_last_4: '4829'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1985-03-15'
              effective_date: '2025-10-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: K28491753
              license_state: NY
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2025-10-01'
              expiration_date: '2026-10-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-10-01'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-10-01'
              effective_date: '2025-10-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F36JA087452
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (212) 847-3928
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer Maria Rodriguez requested to add her elderly parent, Carmen Rodriguez (DOB: 1948-06-22), to her auto policy. Parent''s license was revoked due to medical condition. Per New York state regulations, unlicensed drivers cannot be added and exclusions are not permitted. Request declined and customer informed.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Request to add or exclude unlicensed driver (Carmen Rodriguez) to policy POL-3847291856
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Michael Rodriguez and my email id is [michael.rodriguez@gmail.com](mailto:michael.rodriguez@gmail.com). I want to add my 16-year-old son, Daniel Rodriguez(DOB 2009-10-01), to my policy POL-4729183856 effective today. He only has a learner's permit right now i.e. unlicensed. Please add him as an excluded driver—I understand I'll need to sign the exclusion form. Can you process this today?
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 4278

        2) Answer to the security question - Buddy

        3) your date of birth - 1978-03-15

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-10-15'
              customer_id: CUST-TX-847291
              id: BILL-TX-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '4278'
              tier: Premium
            - date_of_birth: '1980-07-22'
              email: sofia.rodriguez@gmail.com
              first_name: Sofia
              fraud_flag: false
              id: CUST-TX-847292
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: null
              security_question: null
              ssn_last_4: '2578'
              tier: Premium
          policy_drivers:
            - customer_id: CUST-TX-847291
              date_of_birth: '1978-03-15'
              effective_date: '2024-08-15'
              exclusion_form_required: false
              id: DRV-TX-847291
              is_co_insured: false
              is_named_insured: true
              license_number: TX12345677
              license_state: TX
              name: Michael Rodriguez
              policy_id: POL-4729183856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: CUST-TX-847292
              date_of_birth: '1980-07-22'
              effective_date: '2024-08-15'
              exclusion_form_required: false
              id: DRV-TX-847292
              is_co_insured: true
              is_named_insured: false
              license_number: TX87674331
              license_state: TX
              name: Sofia Rodriguez
              policy_id: POL-4729183856
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: CUST-TX-847292
              customer_id: CUST-TX-847291
              effective_date: '2024-08-15'
              expiration_date: '2026-08-15'
              id: POL-4729183856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2026-08-15'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-15'
              effective_date: '2024-08-15'
              id: VEH-TX-294857
              make: Honda
              model: Accord
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA123455
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-06-01'
              effective_date: '2025-06-01'
              id: VEH-TX-294858
              make: Toyota
              model: Camry
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 4T1BF1FK0LU987754
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-06-01T09:15:00Z'
              description: Customer requested to add 2020 Toyota Camry to policy POL-4729183856. Vehicle acquired on 2025-06-01. Request completed successfully.
              due_at: null
              effective_date_of_change: '2025-06-01'
              escalation_level: Standard
              id: '18472'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Policy Servicing
              requester_id: '29847'
              status: solved
              subject: Add Vehicle - 2020 Toyota Camry
              tags: []
              type: task
              updated_at: '2025-06-01T09:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: michael.rodriguez@gmail.com
              id: '29847'
              name: Michael Rodriguez
              organization_id: '1'
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-15T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                email: michael.rodriguez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-TX-847291
              tool: crm_get_customer_profile
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requested to add 16-year-old son Daniel Rodriguez as an excluded driver to policy POL-4729183856. Learner''s permit only. Exclusion form required. Effective date: 2025-10-01.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '29847'
                  status: open
                  subject: Add Excluded Driver - Daniel Rodriguez
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                date_of_birth: '2009-10-01'
                effective_date: '2025-10-01'
                exclusion_form_required: true
                license_number: null
                name: Daniel Rodriguez
                policy_id: POL-4729183856
                relationship: Son
                status: Excluded
                uw_pending: false
              tool: policy_add_driver
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Pending – User Action
                  priority: null
                  request_category: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am Michael Torres, my date of birth is 1987-03-15, my email address is [michael.torres@gmail.com](mailto:michael.torres@gmail.com), and my policy number is POL-3847291658. I'd like to add my brother, Daniel Torres (DOB: 1990-05-10), to my policy POL-3847291658. His license is currently suspended for unpaid tickets, and he has no DUI history, please let me know what I need to do next.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-25'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 375
              payment_received: false
              policy_id: POL-3847291658
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: michael.torres@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Torres
              phone: (813) 492-7583
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: null
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-FL-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-08-15'
              exclusion_form_required: false
              id: DRV-FL-847291
              is_co_insured: false
              is_named_insured: true
              license_number: T847291583
              license_state: FL
              name: Michael Torres
              policy_id: POL-3847291658
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1989-11-22'
              effective_date: '2024-08-15'
              exclusion_form_required: false
              id: DRV-FL-847292
              is_co_insured: true
              is_named_insured: false
              license_number: T892847361
              license_state: FL
              name: Sofia Torres
              policy_id: POL-3847291658
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2024-08-15'
              expiration_date: '2025-10-15'
              id: POL-3847291658
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2025-10-15'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-15'
              effective_date: '2024-08-15'
              id: VEH-FL-928374
              make: Honda
              model: Accord
              policy_id: POL-3847291658
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F50JA206911
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-28T14:20:00Z'
              description: Customer requesting payment extension due to temporary financial hardship
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: TICK-847291-001
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Pending – User Action
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: pending
              subject: Payment Extension Request
              tags: []
              type: task
              updated_at: '2025-09-28T14:20:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: michael.torres@gmail.com
              id: '847291'
              name: Michael Torres
              organization_id: null
              phone: (813) 492-7583
              role: end-user
              updated_at: '2024-08-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests to add Daniel Torres as an excluded driver due to suspended license. Exclusion form required.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Add Excluded Driver - Daniel Torres
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Pending – User Action
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_013(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez and my email id is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). I would like to add my niece, Isabella Martinez (DOB: 1999-05-12, TX license: TX99123456), as a driver to my policy POL-4729183856. She has a valid Texas license and a clean record for the past 5 years, but I want to mention she had a DUI 6 years ago. Can you add her to my policy effective today? Hoping to get this solved today.
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 4256

        2) Answer to the security question - Buddy

        3) your date of birth - 1985-03-15

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-TX-847291
              id: BILL-TX-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '4256'
              tier: Standard
            - date_of_birth: '1983-07-22'
              email: carlos.rodriguez@gmail.com
              first_name: Carlos
              fraud_flag: false
              id: CUST-TX-847292
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Fluffy
              security_question: What is your pet's name?
              ssn_last_4: null
              tier: Standard
            - date_of_birth: '2006-11-08'
              email: sofia.rodriguez@gmail.com
              first_name: Sofia
              fraud_flag: false
              id: CUST-TX-847293
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: null
              security_question: null
              ssn_last_4: '2578'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-TX-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-10-01'
              exclusion_form_required: false
              id: DRV-TX-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: TX47291856
              license_state: TX
              name: Maria Rodriguez
              policy_id: POL-4729183856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: CUST-TX-847292
              date_of_birth: '1983-07-22'
              effective_date: '2024-10-01'
              exclusion_form_required: false
              id: DRV-TX-847291-02
              is_co_insured: true
              is_named_insured: false
              license_number: TX83729456
              license_state: TX
              name: Carlos Rodriguez
              policy_id: POL-4729183856
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: CUST-TX-847293
              date_of_birth: '2006-11-08'
              effective_date: '2025-01-15'
              exclusion_form_required: false
              id: DRV-TX-847291-03
              is_co_insured: false
              is_named_insured: false
              license_number: TX06847291
              license_state: TX
              name: Sofia Rodriguez
              policy_id: POL-4729183856
              relationship: Child
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: CUST-TX-847292
              customer_id: CUST-TX-847291
              effective_date: '2024-10-01'
              expiration_date: '2026-10-01'
              id: POL-4729183856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2025-10-01'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-10-01'
              effective_date: '2024-10-01'
              id: VEH-TX-847291-01
              make: Honda
              model: Accord
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA123456
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-10-01'
              effective_date: '2024-10-01'
              id: VEH-TX-847291-02
              make: Ford
              model: F-150
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1FTFW1ET5LFC84729
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: '1'
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-20T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Add driver: Isabella Martinez to policy POL-4729183856'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: 'Add driver: Isabella Martinez to policy POL-4729183856'
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                date_of_birth: '1999-05-12'
                effective_date: '2025-10-01'
                exclusion_form_required: false
                license_number: TX99123456
                license_state: TX
                name: Isabella Martinez
                policy_id: POL-4729183856
                relationship: Niece
                status: Rated
                uw_pending: false
              tool: policy_add_driver
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_014(x: TestContext, judge: Judge):
    """!
    query: |
        I'd like to add my spouse, David Martinez (DOB: 1984-07-22, NY license #M977634471), to my policy POL-3847291856. He has a valid license and about three tickets in the last five years, but no DUIs. My policy is currently in Grace Period because I'm 6 days past due on my payment. Will adding him now affect my ability to reinstate the policy if it gets cancelled for non-payment? My name is Sarah Martinez and my email is [sarah.martinez@gmail.com](mailto:sarah.martinez@gmail.com).
    user_context: |
        Rules:

        Your Date of Birth is 1985-03-15.

        Your ssn last four is "3729".

        Your security answer is "Buddy".

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-25'
              customer_id: CUS-1847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 15396
              new_due_date: null
              past_due_amount: 15396
              payment_received: false
              policy_id: POL-3847291856
              status: In Grace Period
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: sarah.martinez@gmail.com
              first_name: Sarah
              fraud_flag: false
              id: CUS-1847291
              last_name: Martinez
              phone: (212) 847-5692
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '3729'
              tier: Premium
          policy_drivers:
            - customer_id: CUS-1847291
              date_of_birth: '1985-03-15'
              effective_date: '2025-04-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: M127476799
              license_state: NY
              name: Sarah Martinez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-1847291
              effective_date: '2025-04-01'
              expiration_date: '2026-04-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-1847291
              renewal_date: '2026-04-01'
              state: NY
              status: In Grace Period
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-04-01'
              effective_date: '2025-04-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263JA122486
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-10T09:15:00Z'
              description: Customer received payment reminder notice and contacted to discuss payment options
              effective_date_of_change: '2025-09-10'
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: solved
              subject: Payment Reminder - Account Past Due
              type: incident
              updated_at: '2025-09-10T15:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-04-01T10:00:00Z'
              email: sarah.martinez@gmail.com
              id: '847291'
              name: Sarah Martinez
              organization_id: null
              phone: (212) 847-5692
              role: end-user
              updated_at: '2025-09-10T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requested to add spouse David Martinez (DOB: 1984-07-22, NY license #M977634471) to policy POL-3847291856. Driver has 3 violations in past 5 years, no DUI. Underwriting review required. Customer informed that driver addition does not affect reinstatement eligibility if overdue amount is paid within Premium tier window.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Add Driver - David Martinez (Underwriting Review)
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                date_of_birth: '1984-07-22'
                effective_date: '2025-10-01'
                exclusion_form_required: false
                license_number: M977634471
                license_state: NY
                name: David Martinez
                policy_id: POL-3847291856
                relationship: Spouse
                status: Rated
                uw_pending: true
              tool: policy_add_driver
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requested to add spouse David Martinez (DOB: 1984-07-22, NY license #M977634471) to policy POL-3847291856. Driver has 3 violations in past 5 years, no DUI. Underwriting review required. Customer informed that driver addition does not affect reinstatement eligibility if overdue amount is paid within Premium tier window.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: hold
                  subject: 'Add Driver - David Martinez '
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_015(x: TestContext, judge: Judge):
    """!
    query: |
        My name is Maria Rodriguez (DOB: March 15, 1987, email: [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com), SSN last 4: 7429).

        My policy POL-3847291856 was canceled for non-payment five days ago, and I’m working on resolving the payment issue.

        I initially wanted to add a new driver to that policy, but I realized that this may not be permitted while the policy is cancelled.

        Could you clarify what your policy rules say in this situation?

        I’m seeking clarification on eligibility only, not requesting any changes at this time. I am not in a rush.
    user_context: |
        Rules:

        - Do not invent or provide any data that is not present in the provided context.
        - Do not change your goal or switch topics.
        - If the agent asks again for the same information, provide it again.
        - Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-15'
              customer_id: CUST-847291
              id: BILL-847291856
              installment_amount: null
              installment_count: null
              monthly_payment: 186
              new_due_date: null
              past_due_amount: 372
              payment_received: false
              policy_id: POL-3847291856
              status: Cancelled
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: null
              security_question: null
              ssn_last_4: '7429'
              tier: Preferred
          policy_drivers:
            - customer_id: null
              date_of_birth: '1987-03-15'
              effective_date: '2025-01-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: E7412936
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: '2025-09-26'
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2025-01-15'
              expiration_date: '2026-01-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-01-15'
              state: CA
              status: Cancelled for Non-Payment
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-01-15'
              effective_date: '2025-01-15'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F3XJA042781
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-26T17:15:00Z'
              description: Customer policy POL-3847291856 was cancelled for non-payment on 2025-09-26. Customer contacted regarding payment arrangements and reinstatement options.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: TKT-847291001
              internal_review_type: null
              organization_id: null
              outcome_summary: Pending – User Action
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: pending
              subject: Policy Cancellation - Payment Issue
              tags: []
              type: incident
              updated_at: '2025-09-26T17:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-26T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer inquired whether a new driver can be added to policy POL-3847291856, which is currently cancelled for non-payment. Customer is not requesting a change, only clarification.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: low
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Eligibility to Add Driver on Cancelled Policy
                  tags: null
                  type: question
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_019(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez and my email id is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). I need to remove my nephew from my auto policy POL-3847291856 because he moved out of my household. His new address is 1224 New Town, San Diego, CA 92101. Can you process this change effective today?
    user_context: |
        Provide below verification details if asked by the agent

        1) your last 4 SSN - 7429

        2) your date of birth - 1978-03-15

        3) you are the named insured on the policy

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 237
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: null
              security_question: null
              ssn_last_4: '7429'
              tier: Standard
          policy_drivers:
            - customer_id: null
              date_of_birth: '1978-03-15'
              effective_date: '2024-06-01'
              exclusion_form_required: false
              id: DRV-847291-001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1975-11-22'
              effective_date: '2024-06-01'
              exclusion_form_required: false
              id: DRV-847291-002
              is_co_insured: false
              is_named_insured: false
              license_number: D7529184
              license_state: CA
              name: Carlos Rodriguez
              policy_id: POL-3847291856
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '2002-07-18'
              effective_date: '2024-08-15'
              exclusion_form_required: false
              id: DRV-847291-003
              is_co_insured: false
              is_named_insured: false
              license_number: D2847193
              license_state: CA
              name: Diego Martinez
              policy_id: POL-3847291856
              relationship: Nephew
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-06-01'
              expiration_date: '2026-06-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-06-01'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-01'
              effective_date: '2024-06-01'
              id: VEH-847291-001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA123446
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-01'
              effective_date: '2024-06-01'
              id: VEH-847291-002
              make: Toyota
              model: Corolla
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2T1BURHE0LC987654
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-20T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer Maria Rodriguez requests removal of nephew Diego Martinez (DOB: 2002-07-18, License: D2847193) from policy POL-3847291856 effective 2025-10-01. Reason: moved out of household. New address provided: 1224 New Town, San Diego, CA 92101. No open claims or tickets for this driver. Removal processed per CA regulations.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Remove nephew Diego Martinez from policy POL-3847291856 (moved out)
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                driver_id: DRV-847291-003
                effective_date: '2025-10-01'
                new_status: Removed
              tool: policy_update_driver_status
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_020(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I want to remove Michael Johnson from my policy POL-3847291058. My name is Robert Martinez and my email is [robert.martinez@gmail.com](mailto:robert.martinez@gmail.com). Let me know if you need more information about the driver I want removed because there are two drivers with similar names on my policy.
    user_context: |
        Your date of birth is 15 March 1978 and your SSN last 4 digits are 8981.

        If agent asks which Michael you want removed, clarify that it's junior by providing full name Michael Johnson Jr. and DOB: 2007-04-18



        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 237
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291058
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: robert.martinez@gmail.com
              first_name: Robert
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Martinez
              phone: (305) 847-2931
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '8981'
              tier: Premium
          policy_drivers:
            - customer_id: null
              date_of_birth: '1978-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-FL-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: M847291058
              license_state: FL
              name: Robert Martinez
              policy_id: POL-3847291058
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1982-07-22'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-FL-847291-02
              is_co_insured: false
              is_named_insured: false
              license_number: M847291059
              license_state: FL
              name: Sarah Martinez
              policy_id: POL-3847291058
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1985-11-08'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-FL-847291-03
              is_co_insured: false
              is_named_insured: false
              license_number: M847291060
              license_state: FL
              name: Michael Johnson
              policy_id: POL-3847291058
              relationship: Other
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '2007-04-18'
              effective_date: '2025-08-01'
              exclusion_form_required: false
              id: DRV-FL-847291-04
              is_co_insured: false
              is_named_insured: false
              license_number: M847291061
              license_state: FL
              name: Michael Johnson Jr.
              policy_id: POL-3847291058
              relationship: Other
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2026-06-15'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-FL-847291-01
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A128856
              year: 2003
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-FL-847291-02
              make: Toyota
              model: Corolla
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2T1BURHE5JC987654
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-FL-847291-03
              make: Ford
              model: F-150
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1FTFW1ET8DFC56789
              year: 2013
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-08-01T14:30:00Z'
              description: Customer requested to add new driver Michael Johnson Jr. (son, age 18) to policy POL-3847291058
              due_at: null
              effective_date_of_change: '2025-08-01'
              escalation_level: Standard
              id: '12847291'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Policy Servicing
              requester_id: '847291'
              status: solved
              subject: Add Driver - Michael Johnson Jr.
              tags: []
              type: task
              updated_at: '2025-08-01T15:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-06-15T10:00:00Z'
              email: robert.martinez@gmail.com
              id: '847291'
              name: Robert Martinez
              organization_id: null
              phone: (305) 847-2931
              role: end-user
              updated_at: '2024-06-15T10:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested removal of driver Michael Johnson.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Remove Driver - Michael Johnson
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                driver_id: DRV-FL-847291-04
                effective_date: '2025-10-01'
                new_status: Removed
              tool: policy_update_driver_status
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Clarification: Customer requested removal of driver Michael Johnson Jr. (DOB: 2007-04-18) from policy POL-3847291058. Driver removed effective 2025-10-01.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: solved
                  subject: Remove Driver - Michael Johnson
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_021(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I want my daughter Jessica Rodriguez removed from my policy. However, she was involved in an accident that is currently on an open claim undergoing investigation.  My policy ID is POL-4729183856. My name is Michael Rodriguez and my email is [michael.rodriguez@gmail.com](mailto:michael.rodriguez@gmail.com). For verification, my date of birth is 15 March 1978 and my SSN last 4 digits are 4899.
    user_context: |
        Tell agent your daughter moved out and that's why you want her removed from your policy immediately.

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-10-15'
              customer_id: CUS-78472915
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183856
              status: Current
          claims_claims:
            - claim_stage: Open – Investigation
              claim_type: Collision – Multi-Vehicle
              created_date: '2025-09-18'
              date_of_loss: '2025-09-18'
              driver_id: DRV-76128490
              has_bodily_injury: false
              id: CLM-847291-001
              loss_location: Austin, TX
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: ''
              police_report_required: false
              policy_id: POL-4729183856
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291-02
              vehicle_vin: 2T1BURHE0JC123789
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUS-78472915
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '4899'
              tier: Preferred
          policy_drivers:
            - customer_id: null
              date_of_birth: '1978-03-15'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-59382746
              is_co_insured: false
              is_named_insured: true
              license_number: '84739261'
              license_state: TX
              name: Michael Rodriguez
              policy_id: POL-4729183856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1980-07-22'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-10496832
              is_co_insured: false
              is_named_insured: false
              license_number: '29847351'
              license_state: TX
              name: Sarah Rodriguez
              policy_id: POL-4729183856
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '2005-11-08'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-76128490
              is_co_insured: false
              is_named_insured: false
              license_number: '68294517'
              license_state: TX
              name: Jessica Rodriguez
              policy_id: POL-4729183856
              relationship: Daughter
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-78472915
              effective_date: '2024-04-15'
              expiration_date: '2026-04-15'
              id: POL-4729183856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-78472915
              renewal_date: '2026-04-15'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A128756
              year: 2003
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-847291-02
              make: Toyota
              model: Corolla
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2T1BURHE0JC123789
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: FNOL – Collision
              created_at: '2025-09-18T15:45:00Z'
              description: Customer reported rear-end collision on 2025-09-18. Daughter Jessica was driving Toyota Corolla. Claim created and under investigation.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '29847'
              internal_review_type: Claims Adjuster
              organization_id: null
              outcome_summary: Pending – Internal Review
              priority: normal
              request_category: Claims
              requester_id: '847291'
              status: hold
              subject: Claim Investigation - Multi-Vehicle Collision
              tags: []
              type: incident
              updated_at: '2025-09-20T09:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-04-15T10:30:00Z'
              email: michael.rodriguez@gmail.com
              id: '847291'
              name: Michael Rodriguez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-18T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests immediate removal of daughter Jessica Rodriguez from policy POL-4729183856. Jessica is currently listed as driver at time of loss on open claim CLM-847291-001 (Investigation stage).
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Request to Remove Driver - Jessica Rodriguez
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Request declined: Jessica Rodriguez cannot be removed from policy POL-4729183856 at this time because she is listed as the driver at time of loss on open claim CLM-847291-001 (Investigation stage). Once the claim is closed, removal can be processed.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: solved
                  subject: Request to Remove Driver - Jessica Rodriguez (declined)
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_022(x: TestContext, judge: Judge):
    """!
    query: |
        I'd like to remove my roommate, Jessica Thompson, from my auto policy (POL-3847291856). She moved out, has her own coverage now, and was the driver in a claim that was paid out 2 weeks ago. Can you process her removal today? My name is Sarah Martinez and my email is [sarah.martinez@gmail.com](mailto:sarah.martinez@gmail.com)
    user_context: |
        Your date of birth is 15 March 1987 and your SSN last 4 digits are 5678



        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims:
            - claim_stage: Closed – Paid
              claim_type: Collision – Multi-Vehicle
              created_date: '2025-09-10T15:30:00Z'
              date_of_loss: '2025-09-09'
              driver_id: DRV-847291003
              has_bodily_injury: false
              id: CLM-847291001
              loss_location: Brooklyn, NY
              other_party_insurance: State Farm
              other_party_name: David Wilson
              other_party_phone: (718) 394-8271
              police_report_number: NYC2025091701
              police_report_required: true
              policy_id: POL-3847291856
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291001
              vehicle_vin: 1HGCM82633A128856
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: sarah.martinez@gmail.com
              first_name: Sarah
              fraud_flag: false
              id: CUST-847291
              last_name: Martinez
              phone: (212) 847-3928
              security_answer: Fluffy
              security_question: What is your pet's name?
              ssn_last_4: '5678'
              tier: Standard
          policy_drivers:
            - customer_id: null
              date_of_birth: '1987-03-15'
              effective_date: '2024-03-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: M847392561
              license_state: NY
              name: Sarah Martinez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1985-07-22'
              effective_date: '2024-03-01'
              exclusion_form_required: false
              id: DRV-847291002
              is_co_insured: false
              is_named_insured: false
              license_number: C462839175
              license_state: NY
              name: Michael Chen
              policy_id: POL-3847291856
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1990-11-08'
              effective_date: '2024-05-15'
              exclusion_form_required: false
              id: DRV-847291003
              is_co_insured: false
              is_named_insured: false
              license_number: T738492651
              license_state: NY
              name: Jessica Thompson
              policy_id: POL-3847291856
              relationship: Roommate
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-03-01'
              expiration_date: '2026-03-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-03-01'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-03-01'
              effective_date: '2024-03-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A128856
              year: 2003
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: FNOL – Collision
              created_at: '2025-09-10T15:30:00Z'
              description: 'Customer reported being rear-ended at traffic light in Brooklyn. Jessica Thompson was driving. Other party: David Wilson, State Farm insured. Police report filed.'
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '847291001'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Claims
              requester_id: '847291'
              status: solved
              subject: Collision claim - rear-ended at traffic light
              tags: []
              type: incident
              updated_at: '2025-09-17T10:15:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: sarah.martinez@gmail.com
              id: '847291'
              name: Sarah Martinez
              organization_id: null
              phone: (212) 847-3928
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests removal of roommate Jessica Thompson from policy POL-3847291856. Jessica was driver at time of loss on a claim that is now closed. Effective date is today.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Remove driver - Jessica Thompson
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                driver_id: DRV-847291003
                effective_date: '2025-10-01'
                new_status: Removed
              tool: policy_update_driver_status
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests removal of roommate Jessica Thompson from policy POL-3847291856. Jessica was driver at time of loss on a claim that is now closed. Effective date is today.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: solved
                  subject: Remove driver - Jessica Thompson
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_023(x: TestContext, judge: Judge):
    """!
    query: |
        Hi! My name is Maria Rodriguez, [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com) DOB 1985-03-15 last 4 SSN 2241. I want to add my domestic partner, Alex Martinez (DOB: 1990-04-12, CA license D1264767), as a Co-Insured on my policy POL-3847291856. Alex has two speeding tickets in the past 5 years, no DUIs. What is the difference between adding Alex as a Co-Insured versus just a listed driver? Can you at least add him as a listed driver today effective today? I do not yet have the domestic partnership documentation available.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 288
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: null
              security_question: null
              ssn_last_4: '2241'
              tier: Premium
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: CUST-847291
              date_of_birth: '1982-11-08'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291-02
              is_co_insured: false
              is_named_insured: false
              license_number: D9384726
              license_state: CA
              name: James Chen
              policy_id: POL-3847291856
              relationship: Brother
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-06-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-84729101
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A126416
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-22'
              effective_date: '2024-08-22'
              id: VEH-84729102
              make: Toyota
              model: Corolla
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2T1BURHE0JC981154
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-28T14:22:00Z'
              description: Customer Maria Rodriguez requesting to add domestic partner as Co-Insured. Requires proof of domestic partnership documentation per policy services requirements.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Pending – User Action
              priority: normal
              request_category: Policy Servicing
              requester_id: '847291'
              status: pending
              subject: Domestic Partnership Documentation Required
              tags: []
              type: task
              updated_at: '2025-09-28T14:22:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-02-14T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                date_of_birth: '1990-04-12'
                effective_date: '2025-10-01'
                exclusion_form_required: false
                license_number: D1264767
                license_state: CA
                name: Alex Martinez
                policy_id: POL-3847291856
                relationship: Domestic Partner
                status: Rated
                uw_pending: false
              tool: policy_add_driver
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Alex Martinez (DOB: 1990-04-12, CA license D1264767) added as listed driver effective 2025-10-01. Two violations (speeding tickets) in past 5 years, no DUI. No underwriting review required.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: 'Added Alex Martinez as listed driver '
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_101(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to add my daughter as a driver on my auto policy.

        My name is Maria Rodriguez (DOB: 1978-03-15), email: [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com), and my policy: POL-2847391652.

        My daughter is Sofia Rodriguez (DOB: 2007-09-12). She recently obtained her Texas license (TX license number: TX90712345). Relationship: child.

        Also, please inform me whether this change will affect my premium.

        Sofia has a clean record—no accidents, violations, or DUIs in the past 5 years. Can you add her effective today?
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.

        The user's answer to the security question is: Civic.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-47829
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-2847391652
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-47829
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Civic
              security_question: What was your first car?
              ssn_last_4: null
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-47829
              date_of_birth: '1978-03-15'
              effective_date: '2024-06-01'
              exclusion_form_required: false
              id: DRV-847291
              is_co_insured: false
              is_named_insured: true
              license_number: TX47829156
              license_state: TX
              name: Maria Rodriguez
              policy_id: POL-2847391652
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1975-11-22'
              effective_date: '2024-06-01'
              exclusion_form_required: false
              id: DRV-847292
              is_co_insured: false
              is_named_insured: false
              license_number: TX75829347
              license_state: TX
              name: Carlos Rodriguez
              policy_id: POL-2847391652
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-47829
              effective_date: '2024-06-01'
              expiration_date: '2026-06-01'
              id: POL-2847391652
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-47829
              renewal_date: '2026-06-01'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-01'
              effective_date: '2024-06-01'
              id: VEH-847291
              make: Honda
              model: Accord
              policy_id: POL-2847391652
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA045732
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-01'
              effective_date: '2024-06-01'
              id: VEH-847292
              make: Toyota
              model: Corolla
              policy_id: POL-2847391652
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2T1BURHE5LC384291
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '1847'
              name: Maria Rodriguez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                email: maria.rodriguez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-47829
                security_answer: Civic
                ssn_last_4: null
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-2847391652
              tool: policy_get_policy_details
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer (Maria Rodriguez, Named Insured) requests to add daughter Sofia Rodriguez (DOB: 2007-09-12, TX license TX90712345, clean record) as a driver. Policy is active, Preferred tier, Texas. No violations or DUI. Effective date: 2025-10-01.'
                  due_at: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '1847'
                  status: open
                  subject: 'Add driver: Sofia Rodriguez to policy POL-2847391652'
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                date_of_birth: '2007-09-12'
                effective_date: '2025-10-01'
                exclusion_form_required: false
                license_number: TX90712345
                license_state: TX
                name: Sofia Rodriguez
                policy_id: POL-2847391652
                relationship: Child
                status: Rated
                uw_pending: false
              tool: policy_add_driver
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer (Maria Rodriguez, Named Insured) requests to add daughter Sofia Rodriguez (DOB: 2007-09-12, TX license TX90712345, clean record) as a driver. Policy is active, Preferred tier, Texas. No violations or DUI. Effective date: 2025-10-01.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '1847'
                  status: solved
                  subject: 'Add driver: Sofia Rodriguez to policy POL-2847391652'
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_drv_106(x: TestContext, judge: Judge):
    """!
    query: |
        I want to add my son, Alejandro Rodriguez (DOB: 2002-08-10, FL license #R705184392662), to my policy POL-3847291056. He was caught driving drunk 4 years ago and has one other ticket. How long will the underwriting review take? Can you process the addition of my son to the policy today? is there going to be any issues adding him to the policy?
    user_context: |
        You are Maria Rodriguez, Your Date of Birth is 1978-03-15.

        Your ssn last four is "7394".

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-FL-78429
              id: BILL-FL-78429
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291056
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-78429
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: null
              security_question: null
              ssn_last_4: '7394'
              tier: Preferred
          policy_drivers:
            - customer_id: null
              date_of_birth: '1978-03-15'
              effective_date: '2024-02-15'
              exclusion_form_required: false
              id: DRV-FL-84729
              is_co_insured: false
              is_named_insured: true
              license_number: R483920615742
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291056
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '1975-11-22'
              effective_date: '2024-02-15'
              exclusion_form_required: false
              id: DRV-FL-84730
              is_co_insured: false
              is_named_insured: false
              license_number: R705184392661
              license_state: FL
              name: Carlos Rodriguez
              policy_id: POL-3847291056
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-78429
              effective_date: '2024-02-15'
              expiration_date: '2026-02-15'
              id: POL-3847291056
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-78429
              renewal_date: '2026-02-15'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-02-10'
              effective_date: '2024-02-15'
              id: VEH-FL-29384
              make: Honda
              model: Accord
              policy_id: POL-3847291056
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30KA472958
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-06-28T14:30:00Z'
              description: Customer requested to add son as driver to policy POL-3847291056. Driver has clean record, licensed in FL. Request completed successfully.
              due_at: null
              effective_date_of_change: '2025-06-28'
              escalation_level: Standard
              id: '29847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Policy Servicing
              requester_id: '78429'
              status: solved
              subject: Add Driver - Son
              tags: []
              type: task
              updated_at: '2025-06-28T15:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-12T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '78429'
              name: Maria Rodriguez
              organization_id: null
              phone: (305) 847-2931
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requests to add son Alejandro Rodriguez (DOB: 2002-08-10, FL license #R705184392662) to policy POL-3847291056. Driver has DUI (4 years ago) and 1 other violation.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '78429'
                  status: open
                  subject: Add Driver - Alejandro Rodriguez
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                date_of_birth: '2002-08-10'
                effective_date: '2025-10-01'
                exclusion_form_required: false
                license_number: R705184392662
                license_state: FL
                name: Alejandro Rodriguez
                policy_id: POL-3847291056
                relationship: Son
                status: Rated
                uw_pending: true
              tool: policy_add_driver
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: null
                  request_category: null
                  requester_id: null
                  status: hold
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_fnol_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Michael Rodriguez and my email is [michael.rodriguez@gmail.com](mailto:michael.rodriguez@gmail.com). My wife was rear-ended at a red light yesterday in Oakland, CA. The other driver was cited by the police, and we have the police report number. My wife got hurt with injury in the neck and went for urgent care. I want to file a claim for this accident under our policy POL-3847291856. The car involved is our 2019 Honda Accord (VIN: 1HGCV1F30KA123456). Here are the details of the other party - Name - John Snow, Phone Number -  415-230-3467, Insurance - Sunlife Insurance. This feels like a pretty serious accident, I'm anxious to get this resolved and want to make sure everything is handled correctly.
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 4589

        2) Answer to the security question - Buddy

        3) your date of birth - 1985-03-15

        Provide the policy report number CA-2025-00101 when the agent asks for it.

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 286
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims:
            - claim_stage: Closed – Paid
              claim_type: Comprehensive – Weather
              created_date: '2024-09-18'
              date_of_loss: '2024-09-18'
              driver_id: DRV-847291-01
              has_bodily_injury: false
              id: CLM-847291-001
              loss_location: Oakland, CA
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: null
              police_report_required: false
              policy_id: POL-3847291856
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291-01
              vehicle_vin: 1HGCV1F30KA123456
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '4589'
              tier: Preferred
            - date_of_birth: '1987-08-22'
              email: sofia.rodriguez@gmail.com
              first_name: Sofia
              fraud_flag: false
              id: CUST-847292
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '4792'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Michael Rodriguez
              policy_id: POL-3847291856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: CUST-847292
              date_of_birth: '1987-08-22'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291-02
              is_co_insured: true
              is_named_insured: false
              license_number: D9384726
              license_state: CA
              name: Sofia Rodriguez
              policy_id: POL-3847291856
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '2007-11-10'
              effective_date: '2024-11-15'
              exclusion_form_required: false
              id: DRV-847291-03
              is_co_insured: false
              is_named_insured: false
              license_number: D2847391
              license_state: CA
              name: Elena Rodriguez
              policy_id: POL-3847291856
              relationship: Child
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: CUST-847292
              customer_id: CUST-847291
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-06-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30KA123456
              year: 2019
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-20'
              effective_date: '2024-08-20'
              id: VEH-847291-02
              make: Hyundai
              model: Elantra
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 5NPD84LF9MH987654
              year: 2021
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-06-10T14:20:00Z'
              email: michael.rodriguez@gmail.com
              id: '847291'
              name: Michael Rodriguez
              organization_id: '1'
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-28T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                email: michael.rodriguez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-847291
                security_answer: Buddy
                ssn_last_4: '4589'
              tool: crm_verify_identity
            - parameters:
                customer_id: CUST-847291
              tool: crm_get_customer_profile
            - parameters:
                policy_id: POL-3847291856
              tool: policy_get_policy_details
            - parameters:
                active_only: true
                policy_id: POL-3847291856
              tool: policy_get_policy_vehicles
            - parameters:
                vehicle_id: VEH-847291-01
              tool: policy_get_vehicle_details
            - parameters:
                active_only: true
                policy_id: POL-3847291856
              tool: policy_get_policy_drivers
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: FNOL – Collision
                  description: 'Customer''s spouse was rear-ended at a red light in Oakland, CA on 2025-09-30. Minor neck injury, urgent care visit. Police report CA-2025-00101. Vehicle: 2019 Honda Accord (VIN: 1HGCV1F30KA123456).'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: high
                  request_category: Claims
                  requester_id: '847291'
                  status: open
                  subject: 'FNOL: Rear-ended accident – Sofia Rodriguez injured'
                  tags: null
                  type: incident
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                claim_type: Collision – Multi-Vehicle
                date_of_loss: '2025-09-30'
                driver_id: DRV-847291-02
                has_bodily_injury: true
                loss_location: Oakland, CA
                other_party_insurance: Sunlife Insurance
                other_party_name: John Snow
                other_party_phone: 415-230-3467
                police_report_number: CA-2025-00101
                police_report_required: true
                policy_id: POL-3847291856
                severity: Major
                siu_flag: None
                unlisted_driver_flag: false
                vehicle_id: VEH-847291-01
                vehicle_vin: 1HGCV1F30KA123456
              tool: claims_create_fnol
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: FNOL – Collision
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: high
                  request_category: Claims
                  requester_id: '847291'
                  status: solved
                  subject: null
                  tags: null
                  type: incident
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_fnol_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi I'm Marcus Rodriguez, I'm the named driver on the policy POL-4729183856. I was driving my 2018 Honda Accord (VIN: 1HGCV1F30JA782498) in Austin, Texas on 23 September 2025 and hit a deer, lost control, and went into a ditch. The car is badly damaged but no one was hurt. I have both collision and comprehensive coverage, but I'm not sure if I should file this as an animal strike or a collision. I don't have a police report. Can you help me file a claim? The vehicle was towed by horizon company and is at my home now and is currently not drivable. Can you please complete this claim today and provide me with the claim details?
    user_context: |
        You are Marcus Rodriguez, your date of birth is: 1985-03-15, Policy number is POL-4729183856 and security answer question is Buddy. Phone number is  (512) 847-3928, email is [marcus.rodriguez@gmail.com](mailto:marcus.rodriguez@gmail.com) and last 4 digits of SSN are 7398

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-TX-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 237
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: marcus.rodriguez@gmail.com
              first_name: Marcus
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7398'
              tier: Premium
          policy_drivers:
            - customer_id: null
              date_of_birth: '1985-03-15'
              effective_date: '2024-04-01'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: TX-84729183
              license_state: TX
              name: Marcus Rodriguez
              policy_id: POL-4729183856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 14
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-TX-847291
              effective_date: '2024-04-01'
              expiration_date: '2026-04-01'
              id: POL-4729183856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2025-04-01'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-01'
              effective_date: '2024-04-01'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA782498
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-01'
              effective_date: '2024-04-01'
              id: VEH-847291-02
              make: Toyota
              model: Corolla
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2T1BURHE0LC153729
              year: 2020
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-01'
              effective_date: '2024-04-01'
              id: VEH-847291-03
              make: Ford
              model: F-150
              policy_id: POL-4729183856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1FTFW1ET0KFC84729
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-28T09:15:00Z'
              description: Customer added BMW M5 to policy. Requires underwriting review per company guidelines for high-value luxury vehicles.
              due_at: null
              effective_date_of_change: '2025-09-28'
              escalation_level: Standard
              id: '12847'
              internal_review_type: Underwriting
              organization_id: null
              outcome_summary: Pending – Internal Review
              priority: normal
              request_category: Policy Servicing
              requester_id: '847291'
              status: hold
              subject: Underwriting Review - High Value Vehicle Addition
              tags: []
              type: task
              updated_at: '2025-09-28T14:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-02-14T10:30:00Z'
              email: marcus.rodriguez@gmail.com
              id: '847291'
              name: Marcus Rodriguez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-15T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer Marcus Rodriguez reports hitting a deer in Texas 8 days ago with 2018 Honda Accord (VIN: 1HGCV1F30JA782498). Significant vehicle damage, no injuries, no police report. Customer unsure if claim is animal strike or collision. Policy and vehicle confirmed active and covered.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Claims
                  requester_id: '847291'
                  status: open
                  subject: FNOL - Animal Strike (2018 Honda Accord, TX, 8 days ago)
                  tags: null
                  type: incident
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                claim_type: Comprehensive – Animal Strike
                date_of_loss: '2025-09-23'
                driver_id: DRV-847291-01
                has_bodily_injury: false
                loss_location: Austin, TX
                other_party_insurance: null
                other_party_name: null
                other_party_phone: null
                police_report_number: null
                police_report_required: false
                policy_id: POL-4729183856
                severity: Moderate
                siu_flag: null
                unlisted_driver_flag: false
                vehicle_id: VEH-847291-01
                vehicle_vin: 1HGCV1F30JA782498
              tool: claims_create_fnol
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: FNOL – Comprehensive
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Claims
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_fnol_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi! My name is Maria Rodriguez, [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com), date of birth 1985-03-15 last 4 SSN 7429. I am contacting you about my policy POL-3847291058. My 2009 Honda Accord, VIN 1HGCP26309A847291 was stolen from my driveway in Brooklyn two days ago. I have already filed a police report  (report number NY2025-093847)
        Could you clarify what documentation is needed and what is the expected timeline for resolution?

        I’m seeking clarification on eligibility only, not filing any claim at this time. I am not in a rush.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291058
              status: Current
          claims_claims:
            - claim_stage: Closed – Paid
              claim_type: Collision – Single Vehicle
              created_date: '2024-03-16T10:30:00Z'
              date_of_loss: '2024-03-15'
              driver_id: DRV-847291001
              has_bodily_injury: false
              id: CLM-847291001
              loss_location: Brooklyn, NY
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: NY2024-0315847
              police_report_required: false
              policy_id: POL-3847291058
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291001
              vehicle_vin: 1HGCP26309A847291
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (718) 394-8271
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Preferred
          policy_drivers:
            - customer_id: null
              date_of_birth: '1985-03-15'
              effective_date: '2023-02-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: R123847291
              license_state: NY
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2023-02-01'
              expiration_date: '2026-02-01'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-02-01'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2023-02-01'
              effective_date: '2023-02-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCP26309A847291
              year: 2009
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (718) 394-8271
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: FNOL – Comprehensive
                  description: Maria Rodriguez asks about FNOL documentation needed and timline for the theft of her vehicle
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: low
                  request_category: Claims
                  requester_id: '847291'
                  status: open
                  subject: FNOL Question – Theft of 2009 Honda Accord (SIU Review Required)
                  tags: null
                  type: question
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_fnol_013(x: TestContext, judge: Judge):
    """!
    query: |
        My Honda Accord was broken into and vandalized last night in San Francisco. The windows were smashed, the interior was damaged, and my stereo was stolen. I have comprehensive coverage, but I have not filed a police report yet. Should I file one, and what does the vandalism claim process involve? I would like to submit a claim. My policy ID is POL-3847291856. My name is Maria Rodriguez, and my email is [maria.rodriguez@gmail.com](). For verification purposes, my date of birth is 15 March 1987, and the last four digits of my SSN are 7394.
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims:
            - claim_stage: Closed – Paid
              claim_type: Comprehensive – Glass Only
              created_date: '2025-02-01'
              date_of_loss: '2025-01-28'
              driver_id: DRV-847291001
              has_bodily_injury: false
              id: CLM-847291001
              loss_location: San Francisco, CA
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: null
              police_report_required: false
              policy_id: POL-3847291856
              severity: Minor
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291001
              vehicle_vin: 1HGCM82633A847291
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Premium
          policy_drivers:
            - customer_id: null
              date_of_birth: '1987-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-06-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A847291
              year: 2003
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: FNOL – Comprehensive
              created_at: '2025-02-01T09:15:00Z'
              description: Customer reported windshield cracked by road debris on Highway 101. Comprehensive coverage confirmed. Claim created successfully.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '847291001'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Claims
              requester_id: '847291'
              status: solved
              subject: Glass claim - windshield replacement
              tags: []
              type: incident
              updated_at: '2025-02-01T14:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-06-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2024-06-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  description: 'Customer reports 2003 Honda Accord (VIN: 1HGCM82633A847291) was broken into and vandalized in San Francisco. Windows smashed, interior damaged, stereo stolen. Customer has comprehensive coverage. Police report not yet filed; advised customer to file report and provide report number to proceed with claim.'
                  due_at: null
                  effective_date_of_change: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  requester_id: '847291'
                  status: open
                  subject: Vandalism claim - Honda Accord broken into
                  tags: null
                  type: incident
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                claim_type: Comprehensive – Vandalism
                date_of_loss: '2025-09-30'
                driver_id: DRV-847291001
                loss_location: San Francisco, CA
                other_party_insurance: null
                other_party_name: null
                other_party_phone: null
                police_report_required: true
                policy_id: POL-3847291856
                severity: Moderate
                siu_flag: null
                unlisted_driver_flag: null
                vehicle_id: VEH-847291001
                vehicle_vin: 1HGCM82633A847291
              tool: claims_create_fnol
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: FNOL – Comprehensive
                  description: 'Customer reports 2003 Honda Accord (VIN: 1HGCM82633A847291) was broken into and vandalized in San Francisco. Windows smashed, interior damaged, stereo stolen. Customer has comprehensive coverage. Police report not yet filed; advised customer to file report and provide report number to proceed with claim.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Pending – User Action
                  priority: normal
                  request_category: Claims
                  requester_id: '847291'
                  status: pending
                  subject: Vandalism claim - Honda Accord broken into
                  tags: null
                  type: incident
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_fnol_018(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I’m Rebecca Martinez (DOB 1987-03-15) and I’m in Austin, Texas. My HorizonShield auto policy number is POL-4729183847. My email is [rebecca.martinez@gmail.com]() and my phone is (512) 847-3928. Overnight we had a big temperature swing and this morning I noticed a windshield crack on my 2018 Honda Accord. Nothing hit the glass, there was no accident, no other vehicles, and no injuries — it looks like a stress crack. I don’t have a police report. Please start a comprehensive glass claim for my windshield (not collision) for today, October 1, 2025, and tell me what my deductible/out-of-pocket would be. For verification, the last 4 of my SSN are 7394 (and my first pet’s name was Buddy).
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-TX-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 148
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183847
              status: Current
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Comprehensive – Glass Only
              created_date: '2025-02-14'
              date_of_loss: '2025-02-14'
              driver_id: null
              has_bodily_injury: false
              id: CLM-847291-001
              loss_location: Austin, TX
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: null
              police_report_required: false
              policy_id: POL-4729183847
              severity: Minor
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291-01
              vehicle_vin: null
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: rebecca.martinez@gmail.com
              first_name: Rebecca
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Martinez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Preferred
            - date_of_birth: '1987-03-15'
              email: rebecca.martinez@gmail.com
              first_name: Rebecca
              fraud_flag: false
              id: CUST-TX-847291-UPD
              last_name: Martinez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-TX-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: TX47829173
              license_state: TX
              name: Rebecca Martinez
              policy_id: POL-4729183847
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              comprehensive_deductible: 500
              customer_id: CUST-TX-847291
              effective_date: '2024-04-15'
              expiration_date: '2026-04-15'
              id: POL-4729183847
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2026-04-15'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-4729183847
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F14JA123456
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-04-15T10:30:00Z'
              email: rebecca.martinez@gmail.com
              id: '847291'
              name: Rebecca Martinez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2024-04-15T10:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: FNOL – Glass Only
                  description: 'Rebecca Martinez (DOB 1987-03-15, email rebecca.martinez@gmail.com, phone (512) 847-3928, SSN last 4 7394) reports windshield stress crack after overnight temperature change. No impact event, no accident, no police report. Policy POL-4729183847 Active (TX). Vehicle: 2018 Honda Accord (VEH-847291-01, VIN 1HGCV1F14JA123456). Prior glass claim within last 24 months: CLM-847291-001 (2025-02-14). Request: file FNOL (Comprehensive – Glass Only) and provide expected out-of-pocket (policy comprehensive deductible: $500).'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Claims
                  requester_id: '847291'
                  status: open
                  subject: 'FNOL: Windshield stress crack (TX) - POL-4729183847'
                  tags: null
                  type: incident
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                claim_type: Comprehensive – Glass Only
                date_of_loss: '2025-10-01'
                driver_id: DRV-847291-01
                has_bodily_injury: null
                loss_location: Austin, TX
                other_party_insurance: null
                other_party_name: null
                other_party_phone: null
                police_report_number: null
                police_report_required: null
                policy_id: POL-4729183847
                severity: Minor
                siu_flag: None
                unlisted_driver_flag: null
                vehicle_id: VEH-847291-01
                vehicle_vin: 1HGCV1F14JA123456
              tool: claims_create_fnol
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_fnol_020(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, My name is Maria Rodriguez and my email is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). My 2020 Hyundai Tucson was stolen last week, but my policy (POL-3847291058) was cancelled for non-payment just a few days before. I had comprehensive coverage when the policy was active and I filed a police report (number available). I didn't get any cancellation notice and I think the theft should be covered. Can I file a claim for this theft?
    user_context: |
        If asked provide the following:
        "date_of_birth": "1987-03-15"
        "ssn_last_4": "7429"
        "security_answer": "Buddy"

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-21'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 563
              payment_received: false
              policy_id: POL-3847291058
              status: Cancelled
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: true
              id: CUST-847291
              last_name: Rodriguez
              phone: (718) 394-8271
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-10-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: R38475621
              license_state: NY
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: '2025-09-21'
              cancellation_reason: Non-Payment
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-10-01'
              expiration_date: '2025-10-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-10-15'
              state: NY
              status: Cancelled for Non-Payment
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-10-01'
              effective_date: '2024-10-01'
              id: VEH-847291001
              make: Hyundai
              model: Tucson
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: KMHL14JA5LA129384
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-04-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (718) 394-8271
              role: end-user
              updated_at: '2025-09-25T14:20:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-847291
                security_answer: Buddy
                ssn_last_4: '7429'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-3847291058
              tool: policy_get_policy_details
            - parameters:
                item:
                  assignee_id: '585'
                  description: Customer Maria Rodriguez (POL-3847291058) requested to file a theft claim for her 2020 Hyundai Tucson. Theft occurred after policy was cancelled for non-payment on 2025-09-21. Customer had comprehensive coverage while active, provided police report, and stated no cancellation notice was received. Policy is in NY, customer is Preferred tier with fraud flag. Per company policy, coverage does not exist for losses after cancellation. Claim cannot be filed. SIU review noted due to fraud flag, but no claim created.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  organization_id: null
                  priority: normal
                  requester_id: '847291'
                  status: open
                  subject: Theft claim request for 2020 Hyundai Tucson after policy cancellation
                  tags: null
                  type: incident
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: FNOL – Comprehensive
                  description: Customer Maria Rodriguez (POL-3847291058) requested to file a theft claim for her 2020 Hyundai Tucson. Theft occurred after policy was cancelled for non-payment on 2025-09-21. Customer had comprehensive coverage while active, provided police report, and stated no cancellation notice was received. Policy is in NY, customer is Preferred tier with fraud flag. Per company policy, coverage does not exist for losses after cancellation. Claim cannot be filed. SIU review noted due to fraud flag, but no claim created.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: normal
                  request_category: Claims
                  requester_id: '847291'
                  status: solved
                  subject: Theft claim request for 2020 Hyundai Tucson after policy cancellation
                  tags: null
                  type: incident
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_fnol_021(x: TestContext, judge: Judge):
    """!
    query: |
        My son David Rodriguez was in a car accident yesterday in Austin, Texas. He was driving our 2018 Honda Accord and another driver hit him. David had to go to the emergency room by ambulance. I have the police report number: APD-2024-847291. I need to file a claim for this collision.
    user_context: |
        You are Michael Rodriguez, your date of birth is 1978-03-15, your last four digits of SSN are 2856. Policy id is POL-8472916583

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-23'
              customer_id: CUST-TX-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 186
              new_due_date: null
              past_due_amount: 186
              payment_received: false
              policy_id: POL-8472916583
              status: In Grace Period
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Collision – Multi-Vehicle
              created_date: '2023-11-16'
              date_of_loss: '2023-11-15'
              driver_id: null
              has_bodily_injury: false
              id: CLM-847291-2023
              loss_location: Austin, TX
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: APD-2023-847291
              police_report_required: false
              policy_id: POL-8472916583
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291-01
              vehicle_vin: null
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '2856'
              tier: Premium
          policy_drivers:
            - customer_id: null
              date_of_birth: '1978-03-15'
              effective_date: '2024-04-01'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: TX12847392
              license_state: TX
              name: Michael Rodriguez
              policy_id: POL-8472916583
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '2005-07-22'
              effective_date: '2024-04-01'
              exclusion_form_required: false
              id: DRV-847291-02
              is_co_insured: false
              is_named_insured: false
              license_number: TX98472851
              license_state: TX
              name: David Rodriguez
              policy_id: POL-8472916583
              relationship: Son
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-TX-847291
              effective_date: '2024-04-01'
              expiration_date: '2026-04-01'
              id: POL-8472916583
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2025-04-01'
              state: TX
              status: In Grace Period
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-01'
              effective_date: '2024-04-01'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-8472916583
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263JA847291
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2024-09-28T14:30:00Z'
              description: Customer requesting extension for overdue payment
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: null
              organization_id: null
              outcome_summary: Pending – User Action
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: pending
              subject: Payment Extension Request
              tags: []
              type: task
              updated_at: '2024-09-28T14:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-04-01T10:00:00Z'
              email: michael.rodriguez@gmail.com
              id: '847291'
              name: Michael Rodriguez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2024-04-01T10:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                claim_type: Collision – Multi-Vehicle
                date_of_loss: '2025-09-30'
                driver_id: DRV-847291-02
                has_bodily_injury: true
                loss_location: Austin, TX
                other_party_insurance: null
                other_party_name: null
                other_party_phone: null
                police_report_number: APD-2024-847291
                police_report_required: true
                policy_id: POL-8472916583
                severity: Major
                siu_flag: None
                unlisted_driver_flag: false
                vehicle_id: VEH-847291-01
                vehicle_vin: 1HGCM8263JA847291
              tool: claims_create_fnol
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: FNOL – Collision
                  description: 'Filed FNOL for multi-vehicle collision involving David Rodriguez (driver) in 2018 Honda Accord. Other driver at fault. Police report APD-2024-847291. Bodily injury: Yes (ambulance, ER). Location: Austin, TX. Policy: POL-8472916583.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: high
                  request_category: Claims
                  requester_id: '847291'
                  status: open
                  subject: 'FNOL – Collision: David Rodriguez, 2018 Honda Accord, 09/30/2025'
                  tags: null
                  type: incident
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: FNOL – Collision
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Claims
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_fnol_023(x: TestContext, judge: Judge):
    """!
    query: |
        Last week on 25th September, a tree fell on my 2018 Honda Accord during a storm here in Florida. The roof and hood are significantly damaged. I have comprehensive coverage and no prior claims. Can I file a claim for this damage, and am I eligible for a diminished value claim?
    user_context: |
        You are Maria Rodriguez, your date of birth is 1985-03-15, your last 4 digits of SSN are 2637. Policy id: POL-3847291658

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-FL-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291658
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (813) 492-7856
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '2637'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-FL-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-08-15'
              exclusion_form_required: false
              id: DRV-847291-001
              is_co_insured: false
              is_named_insured: true
              license_number: R847291856
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291658
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2024-08-15'
              expiration_date: '2026-08-15'
              id: POL-3847291658
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2025-08-15'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-15'
              effective_date: '2024-08-15'
              id: VEH-847291-001
              make: Honda
              model: Accord
              policy_id: POL-3847291658
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HG45X2K2JL836016
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-15'
              effective_date: '2024-08-15'
              id: VEH-847291-002
              make: Toyota
              model: Camry
              policy_id: POL-3847291658
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 4T1XGFKS3LR517784
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-06-01T14:20:00Z'
              description: Customer requested removal of 2016 Nissan Sentra from policy POL-3847291658
              due_at: null
              effective_date_of_change: '2025-06-01'
              escalation_level: Standard
              id: '384729'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Policy Servicing
              requester_id: '847291'
              status: solved
              subject: Remove Vehicle from Policy
              tags: []
              type: task
              updated_at: '2025-06-01T15:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-08-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: FNOL – Comprehensive
                  description: Customer reports a tree fell on 2018 Honda Accord during a storm in Florida. Roof and hood significantly damaged. No prior claims. Customer inquires about diminished value claim eligibility.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Claims
                  requester_id: '847291'
                  status: open
                  subject: 'FNOL: Storm Damage to 2018 Honda Accord'
                  tags: null
                  type: incident
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                claim_type: Comprehensive – Weather
                date_of_loss: '2025-09-25'
                driver_id: DRV-847291-001
                has_bodily_injury: false
                loss_location: Florida
                other_party_insurance: null
                other_party_name: null
                other_party_phone: null
                police_report_number: null
                police_report_required: false
                policy_id: POL-3847291658
                severity: Moderate
                siu_flag: None
                unlisted_driver_flag: null
                vehicle_id: VEH-847291-001
                vehicle_vin: 1HG45X2K2JL836016
              tool: claims_create_fnol
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_ldr_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Michael Chen. I'm a driver on my mom's policy. I was driving our 2018 Honda Accord yesterday in San Francisco, and I was rear-ended at a stoplight by another driver. There were no injuries and it's just a moderate dented bumper, but I'd like to file a claim for this accident. My date of birth is July 22, 2001. Can you help me start the claim? My email address is [michael.chen.student@gmail.com](mailto:michael.chen.student@gmail.com).
    user_context: |
        If asked for verification, provide the last 4 digit of your SSN "7194" or provide your policy number POL-3847291856.

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Collision – Single Vehicle
              created_date: '2024-05-15'
              date_of_loss: '2024-05-15'
              driver_id: null
              has_bodily_injury: false
              id: CLM-847291001
              loss_location: San Francisco, CA
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: null
              police_report_required: false
              policy_id: POL-3847291856
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291001
              vehicle_vin: null
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: patricia.chen@gmail.com
              first_name: Patricia
              fraud_flag: false
              id: CUST-847291
              last_name: Chen
              phone: (415) 892-3847
              security_answer: Whiskers
              security_question: What was the name of your first pet?
              ssn_last_4: '7194'
              tier: Preferred
          policy_drivers:
            - customer_id: null
              date_of_birth: '1978-03-15'
              effective_date: '2024-03-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: false
              license_number: D8472915
              license_state: CA
              name: Patricia Chen
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '2001-07-22'
              effective_date: '2024-03-01'
              exclusion_form_required: false
              id: DRV-847291002
              is_co_insured: false
              is_named_insured: false
              license_number: D2847291
              license_state: CA
              name: Michael Chen
              policy_id: POL-3847291856
              relationship: Child
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-03-01'
              expiration_date: '2026-03-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-03-01'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-03-01'
              effective_date: '2024-03-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633AJ47291
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: michael.chen.student@gmail.com
              id: '2847'
              name: Michael Chen
              organization_id: null
              phone: (415) 729-4851
              role: end-user
              updated_at: '2024-08-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: FNOL – Collision
                  description: Michael Chen (Listed Driver) rear-ended in 2018 Honda Accord, minor damage, no injuries, occurred 2025-09-30 in San Francisco, CA.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Claims
                  requester_id: '2847'
                  status: open
                  subject: FNOL Collision
                  tags: null
                  type: incident
                  user_type: Listed Driver
                table: tickets
              tool: zendesk_create_item
            - parameters:
                claim_type: Collision – Multi-Vehicle
                date_of_loss: '2025-09-30'
                driver_id: DRV-847291002
                has_bodily_injury: false
                loss_location: San Francisco, CA
                other_party_insurance: null
                other_party_name: null
                other_party_phone: null
                police_report_number: null
                police_report_required: false
                policy_id: POL-3847291856
                severity: Moderate
                siu_flag: None
                unlisted_driver_flag: false
                vehicle_id: VEH-847291001
                vehicle_vin: 1HGCM82633AJ47291
              tool: claims_create_fnol
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: FNOL – Collision
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Claims
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: Listed Driver
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_ldr_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is **Alex Martinez**. I’m a **listed driver** on my parents’ HorizonShield auto insurance policy. The policy number is **POL-4729183856**, my date of birth is **November 8, 1995**, and the email on the policy is **[alex.martinez@gmail.com](mailto:alex.martinez@gmail.com)**. I recently bought a new car and would like to add it to **my parents’ policy**. I understand I’m not the named insured, but I wanted to check if you can help me with adding the vehicle.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-TX-901721
              id: BILL-TX-901721
              monthly_payment: 154
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1967-03-15'
              email: robert.martinez@gmail.com
              first_name: Robert
              fraud_flag: false
              id: CUST-TX-901721
              last_name: Martinez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7419'
              tier: Preferred
            - date_of_birth: '1969-08-22'
              email: maria.martinez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-TX-901722
              last_name: Martinez
              phone: (512) 847-3929
              security_answer: Rodriguez
              security_question: What was your mother's maiden name?
              ssn_last_4: '5826'
              tier: Preferred
            - date_of_birth: '1995-11-08'
              email: alex.martinez@gmail.com
              first_name: Alex
              fraud_flag: false
              id: CUST-TX-901723
              last_name: Martinez
              phone: (512) 847-3930
              security_answer: Lincoln Elementary
              security_question: What was the name of your first school?
              ssn_last_4: '3094'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-TX-901721
              date_of_birth: '1967-03-15'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-TX-901721-01
              is_co_insured: false
              is_named_insured: true
              license_number: TX83492017
              license_state: TX
              name: Robert Martinez
              policy_id: POL-4729183856
              relationship: Named Insured
              status: Rated
              uw_pending: false
            - customer_id: CUST-TX-901722
              date_of_birth: '1969-08-22'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-TX-901721-02
              is_co_insured: true
              is_named_insured: false
              license_number: TX83492018
              license_state: TX
              name: Maria Martinez
              policy_id: POL-4729183856
              relationship: Co-Insured
              status: Rated
              uw_pending: false
            - customer_id: CUST-TX-901723
              date_of_birth: '1995-11-08'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-TX-901721-03
              is_co_insured: false
              is_named_insured: false
              license_number: TX83492019
              license_state: TX
              name: Alex Martinez
              policy_id: POL-4729183856
              relationship: Listed Driver
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: CUST-TX-901722
              customer_id: CUST-TX-901721
              effective_date: '2024-04-15'
              expiration_date: '2026-04-15'
              id: POL-4729183856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-901721
              renewal_date: '2026-04-15'
              state: TX
              status: Active
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-TX-901721-01
              make: Honda
              model: Accord
              policy_id: POL-4729183856
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F38JA045821
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-04-15T10:00:00Z'
              email: robert.martinez@gmail.com
              id: ZD-558201
              name: Robert Martinez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2024-04-15T10:00:00Z'
              verified: true
            - active: true
              created_at: '2024-04-15T10:00:00Z'
              email: maria.martinez@gmail.com
              id: ZD-558202
              name: Maria Martinez
              organization_id: null
              phone: (512) 847-3929
              role: end-user
              updated_at: '2024-04-15T10:00:00Z'
              verified: true
            - active: true
              created_at: '2024-04-15T10:00:00Z'
              email: alex.martinez@gmail.com
              id: ZD-558203
              name: Alex Martinez
              organization_id: null
              phone: (512) 847-3930
              role: end-user
              updated_at: '2024-04-15T10:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Listed Driver Alex Martinez requested to add a newly purchased vehicle to policy POL-4729183856. Request was declined because only the Named Insured or Co-Insured has authority to add vehicles.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: ZD-558203
                  status: open
                  subject: Add Vehicle Request - Insufficient Authority
                  tags: null
                  type: task
                  user_type: Listed Driver
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_ldr_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I am Sofia Martinez, I am a listed driver on the policy, my email address is [sofia.martinez@gmail.com](mailto:sofia.martinez@gmail.com), and my date of birth is 2005-08-22.  My father Robert Martinez is the policy owner, he is busy with work, so he asked me to contact you regarding the ticket (id 6) on the payment past due notice sent to the policy POL-3847291658. I want to request an extension for the overdue payment.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-22'
              customer_id: CUST-FL-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 376
              payment_received: false
              policy_id: POL-3847291658
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: robert.martinez@gmail.com
              first_name: Robert
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Martinez
              phone: (813) 492-7583
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: null
              tier: Premium
          policy_drivers:
            - customer_id: CUST-FL-847291
              date_of_birth: '1978-03-15'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: M847291583
              license_state: FL
              name: Robert Martinez
              policy_id: POL-3847291658
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: null
              date_of_birth: '2005-08-22'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-847291-02
              is_co_insured: false
              is_named_insured: false
              license_number: M205847392
              license_state: FL
              name: Sofia Martinez
              policy_id: POL-3847291658
              relationship: Daughter
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2024-04-15'
              expiration_date: '2025-10-22'
              id: POL-3847291658
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2025-10-22'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-3847291658
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F50JA206911
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-22T08:00:00Z'
              description: Automated past due notice sent to customer for overdue payment of $376.00. Payment was due on 2025-09-22. Policy is currently 9 days past due.
              due_at: null
              effective_date_of_change: null
              escalation_level: null
              id: '6'
              internal_review_type: null
              organization_id: null
              outcome_summary: null
              priority: normal
              request_category: null
              requester_id: '847291'
              status: open
              subject: Payment Past Due Notice - Policy POL-3847291658
              tags: []
              type: incident
              updated_at: '2025-09-22T08:00:00Z'
              user_type: null
          zendesk_users:
            - active: true
              created_at: '2024-04-15T10:30:00Z'
              email: robert.martinez@gmail.com
              id: '847291'
              name: Robert Martinez
              organization_id: null
              phone: (813) 492-7583
              role: end-user
              updated_at: '2025-09-15T14:20:00Z'
              verified: true
            - active: true
              created_at: '2024-04-15T10:30:00Z'
              email: sofia.martinez@gmail.com
              id: '847292'
              name: Sofia Martinez
              organization_id: null
              phone: (813) 492-7584
              role: end-user
              updated_at: '2025-09-20T16:45:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                id: '6'
                item:
                  claims_action_type: null
                  description: 'Sofia Martinez (listed driver) requested a payment extension for policy POL-3847291658. Request declined due to authority: only Named Insured or Co-Insured may request billing arrangements. Sofia was informed her father must contact HorizonShield directly.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: normal
                  request_category: Billing & Payments
                  status: solved
                  subject: Listed Driver Request for Payment Extension - Policy POL-3847291658
                  tags: null
                  type: task
                  user_type: Listed Driver
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_ldr_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Jessica Thompson. I'd like to add my friend as a driver to our policy(POL-8472916384) since they'll be staying with us and might need to borrow the car sometimes. My friend’s name is Alex Jordan Miller, their date of birth is 2000-06-18, and their driver’s license number is D7839172 issued in California (CA). My Mother said I cannot add my friend and only my step dad can add them, is this true?
    user_context: |
        Your date of birth is 2001-11-08, Last 4 digits of SSN: 3847.

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-8472916384
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (718) 394-8271
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Preferred
            - date_of_birth: '1982-07-22'
              email: sarah.martinez@outlook.com
              first_name: Sarah
              fraud_flag: false
              id: CUST-592847
              last_name: Martinez
              phone: (718) 592-8471
              security_answer: Garcia
              security_question: What was your mother's maiden name?
              ssn_last_4: '5928'
              tier: Preferred
            - date_of_birth: '2001-11-08'
              email: jessica.thompson@gmail.com
              first_name: Jessica
              fraud_flag: false
              id: CUST-384729
              last_name: Thompson
              phone: (718) 384-7291
              security_answer: Albany
              security_question: What city were you born in?
              ssn_last_4: '3847'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1978-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: R847291847
              license_state: NY
              name: Michael Rodriguez
              policy_id: POL-8472916384
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: CUST-592847
              date_of_birth: '1982-07-22'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-592847002
              is_co_insured: false
              is_named_insured: false
              license_number: M592847592
              license_state: NY
              name: Sarah Martinez
              policy_id: POL-8472916384
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: CUST-384729
              date_of_birth: '2001-11-08'
              effective_date: '2024-08-20'
              exclusion_form_required: false
              id: DRV-384729003
              is_co_insured: false
              is_named_insured: false
              license_number: T384729384
              license_state: NY
              name: Jessica Thompson
              policy_id: POL-8472916384
              relationship: Step-child
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 15
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-8472916384
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-06-15'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-8472916384
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82633A847291
              year: 2019
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-592847002
              make: Toyota
              model: Corolla
              policy_id: POL-8472916384
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2T1BURHE5JC592847
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-06-15T10:00:00Z'
              email: michael.rodriguez@gmail.com
              id: '847291'
              name: Michael Rodriguez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-06-15T10:00:00Z'
              verified: true
            - active: true
              created_at: '2024-06-15T10:00:00Z'
              email: sarah.martinez@outlook.com
              id: '592847'
              name: Sarah Martinez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-06-15T10:00:00Z'
              verified: true
            - active: true
              created_at: '2024-08-20T10:00:00Z'
              email: jessica.thompson@gmail.com
              id: '384729'
              name: Jessica Thompson
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2024-08-20T10:00:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Jessica Thompson (Listed Driver) requested to add her friend as a driver. Request declined: only Named Insured or Co-Insured may add drivers. Jessica advised to have Michael Rodriguez (Named Insured) or a Co-Insured contact us.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '384729'
                  status: open
                  subject: Driver addition request by listed driver declined
                  tags: null
                  type: task
                  user_type: Listed Driver
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_ldr_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I’m **David Rodriguez**. I’m a **listed driver** on my parents’ auto insurance policy. I want to **cancel the policy effective today**. The policy number is **POL-8472916384**. My email is **[david.rodriguez@utexas.edu]()**, and my date of birth is **November 8, 2003**. Please cancel the policy
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-11-01'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-8472916384
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1978-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Lopez
              security_question: Mother's maiden name
              ssn_last_4: '5817'
              tier: Standard
            - date_of_birth: '1980-07-22'
              email: patricia.rodriguez@gmail.com
              first_name: Patricia
              fraud_flag: false
              id: CUST-847292
              last_name: Rodriguez
              phone: (512) 847-3929
              security_answer: Buddy
              security_question: First pet's name
              ssn_last_4: '2946'
              tier: Standard
            - date_of_birth: '2003-11-08'
              email: david.rodriguez@utexas.edu
              first_name: David
              fraud_flag: false
              id: CUST-847293
              last_name: Rodriguez
              phone: (512) 394-8271
              security_answer: null
              security_question: null
              ssn_last_4: null
              tier: Standard
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1978-03-15'
              effective_date: '2023-03-01'
              exclusion_form_required: false
              id: DRV-847291
              is_co_insured: false
              is_named_insured: true
              license_number: TX87451293
              license_state: TX
              name: Michael Rodriguez
              policy_id: POL-8472916384
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: CUST-847292
              date_of_birth: '1980-07-22'
              effective_date: '2023-03-01'
              exclusion_form_required: false
              id: DRV-847292
              is_co_insured: true
              is_named_insured: false
              license_number: TX98347126
              license_state: TX
              name: Patricia Rodriguez
              policy_id: POL-8472916384
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: CUST-847293
              date_of_birth: '2003-11-08'
              effective_date: '2023-03-01'
              exclusion_form_required: false
              id: DRV-847293
              is_co_insured: false
              is_named_insured: false
              license_number: TX56382941
              license_state: TX
              name: David Rodriguez
              policy_id: POL-8472916384
              relationship: Son
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: CUST-847292
              customer_id: CUST-847291
              effective_date: '2023-03-01'
              expiration_date: '2026-03-01'
              id: POL-8472916384
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-03-01'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2023-03-01'
              effective_date: '2023-03-01'
              id: VEH-847291
              make: Honda
              model: Accord
              policy_id: POL-8472916384
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F34JA024683
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2023-03-01'
              effective_date: '2023-03-01'
              id: VEH-847292
              make: Toyota
              model: Corolla
              policy_id: POL-8472916384
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2T1BURHE0LC092517
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-04-01T14:30:00Z'
              description: Customer requested digital ID card for policy POL-8472916384
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: ZD-TCK-556812
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: low
              request_category: Documents
              requester_id: ZD-100847293
              status: solved
              subject: ID Card Request
              tags: []
              type: question
              updated_at: '2025-04-01T15:45:00Z'
              user_type: Listed Driver
          zendesk_users:
            - active: true
              created_at: '2023-02-18T10:30:00Z'
              email: michael.rodriguez@gmail.com
              id: ZD-100847291
              name: Michael Rodriguez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: true
            - active: true
              created_at: '2023-02-18T10:30:00Z'
              email: patricia.rodriguez@gmail.com
              id: ZD-100847292
              name: Patricia Rodriguez
              organization_id: null
              phone: (512) 847-3929
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: true
            - active: true
              created_at: '2023-02-18T10:30:00Z'
              email: david.rodriguez@utexas.edu
              id: ZD-100847293
              name: David Rodriguez
              organization_id: null
              phone: (512) 394-8271
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: David Rodriguez, a listed driver on policy POL-8472916384, requested cancellation effective today. Per company policy, listed drivers do not have authority to cancel policies. Customer was partially verified (name and DOB confirmed).
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: ZD-100847293
                  status: open
                  subject: Policy Cancellation Request - Unauthorized User
                  tags: null
                  type: task
                  user_type: Listed Driver
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Michael Rodriguez and my email id is [michael.rodriguez@gmail.com](mailto:michael.rodriguez@gmail.com). I'd like to cancel my auto insurance policy (POL-4729183847) effective today. I sold my Honda Accord and don't need insurance anymore. Will I get a refund for any unused premium?
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 4285

        2) Answer to the security question - Buddy

        3) your date of birth - 1987-03-15

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-11-01'
              customer_id: CUST-TX-847291
              id: BILL-TX-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183847
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '4285'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-TX-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-10-01'
              exclusion_form_required: false
              id: DRV-TX-847291
              is_co_insured: false
              is_named_insured: true
              license_number: TX12847392
              license_state: TX
              name: Michael Rodriguez
              policy_id: POL-4729183847
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-TX-847291
              effective_date: '2024-10-01'
              expiration_date: '2026-10-01'
              id: POL-4729183847
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2025-10-01'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-09-25'
              effective_date: '2024-10-01'
              id: VEH-TX-847291
              make: Honda
              model: Accord
              policy_id: POL-4729183847
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30JA847291
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-01-15T10:30:00Z'
              email: michael.rodriguez@gmail.com
              id: '2847'
              name: Michael Rodriguez
              organization_id: '1'
              phone: 214-325-4746
              role: end-user
              updated_at: '2024-01-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                email: michael.rodriguez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-TX-847291
              tool: crm_get_customer_profile
            - parameters:
                policy_id: POL-4729183847
              tool: policy_get_policy_details
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer Michael Rodriguez (Standard tier, TX) requested cancellation of policy POL-4729183847 effective 2025-10-01 due to sale of vehicle. Policy is paid through 2025-11-01, refund for unused premium will be processed per company policy.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: null
                  organization_id: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '2847'
                  status: open
                  subject: Policy cancellation request - POL-4729183847
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                cancellation_date: '2025-10-01'
                cancellation_reason: User Requested
                policy_id: POL-4729183847
              tool: policy_schedule_cancellation
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_002(x: TestContext, judge: Judge):
    """!
    query: |
        I want to cancel my auto policy (POL-3847291058) effective today (2025-10-01). I found a better rate with another company. Can you confirm the exact time my coverage will end today?
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.



        [You can provide this information if asked:]()

        1. Your full name -  Maria Rodriguez
        2. Your date of birth - 1987-03-15
        3. Your email address - [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com)
        4. Your phone number - (305) 847-2931
        5. Last 4 digits of Social Security number -   7394,
        6. Security Question -   What was the name of your first pet?,
        7. Security Answer - Buddy


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-10-15'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 18800
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291058
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-FL-847291
              date_of_birth: '1987-03-15'
              effective_date: '2025-06-15'
              exclusion_form_required: false
              id: DRV-FL-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: R847291583
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 14
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2025-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2026-06-15'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-06-15'
              effective_date: '2025-06-15'
              id: VEH-FL-847291-01
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F36KA123456
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-30T10:15:00Z'
              description: Customer inquired about upcoming payment due date and available payment methods
              due_at: null
              effective_date_of_change: null
              escalation_level: null
              id: TKT-847291-001
              internal_review_type: null
              organization_id: null
              outcome_summary: null
              priority: normal
              request_category: null
              requester_id: '847291'
              status: open
              subject: Billing inquiry - payment due date question
              tags: []
              type: question
              updated_at: '2025-09-30T10:15:00Z'
              user_type: null
          zendesk_users:
            - active: true
              created_at: '2023-08-15T14:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (305) 847-2931
              role: end-user
              updated_at: '2025-09-28T10:15:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-FL-847291
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUST-FL-847291
                security_answer: Buddy
                ssn_last_4: '7394'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-3847291058
              tool: policy_get_policy_details
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested cancellation effective today. Policy will be cancelled as of 11:59 PM local time on 2025-10-01. Written confirmation provided.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Policy cancellation confirmed for POL-3847291058 effective 2025-10-01 (coverage ends 11:59 PM local time)
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                cancellation_date: '2025-10-01'
                cancellation_reason: User Requested
                policy_id: POL-3847291058
              tool: policy_schedule_cancellation
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_003(x: TestContext, judge: Judge):
    """!
    query: |
        **Hi, my name is Rebecca Chen and my email is [rebecca.chen@gmail.com](mailto:rebecca.chen@gmail.com). My date of birth is March 15, 1987. I'd like to cancel my auto policy POL-3847291856 effective today. I'm moving out of California next week but want to end my coverage now. Why can't I cancel it immediately?**
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: rebecca.chen@gmail.com
              first_name: Rebecca
              fraud_flag: false
              id: CUST-847291
              last_name: Chen
              phone: (415) 892-7341
              security_answer: null
              security_question: null
              ssn_last_4: null
              tier: Premium
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-02-15'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Rebecca Chen
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-02-15'
              expiration_date: '2026-02-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-02-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-02-15'
              effective_date: '2024-02-15'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F35KA123456
              year: 2023
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2022-08-12T10:30:00Z'
              email: rebecca.chen@gmail.com
              id: '847291'
              name: Rebecca Chen
              organization_id: null
              phone: (415) 892-7341
              role: end-user
              updated_at: '2025-09-15T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested cancellation effective today due to moving out of state next week. California regulations require minimum 1-day notice for cancellation. Effective date adjusted to tomorrow.
                  due_at: null
                  effective_date_of_change: '2025-10-02'
                  escalation_level: Standard
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Policy Cancellation - Customer Request
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                cancellation_date: '2025-10-02'
                cancellation_reason: User Requested
                policy_id: POL-3847291856
              tool: policy_schedule_cancellation
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested cancellation effective today due to moving out of state next week. California regulations require minimum 1-day notice for cancellation. Effective date adjusted to tomorrow.
                  due_at: null
                  effective_date_of_change: '2025-10-02'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: solved
                  subject: Policy Cancellation - Customer Request
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I want to cancel my auto policy (POL-3847291056) effective today because I just bought a new policy that starts today. I don't want any overlap in coverage. Can you confirm if there will be a gap or overlap, and when my cancellation will actually take effect?

        For verification if needed: I’m Maria Rodriguez, DOB 1987-03-15, SSN last 4 is 7394, and my security answer is “Whiskers”.
    user_context: |
        You are Maria Rodriguez, a HorizonShield auto policyholder in New York. Reply naturally in 1-2 sentences. Do not mention tools or test cases.

        If asked for identity verification, provide:

        - Name: Maria Rodriguez
        - Policy number: POL-3847291056
        - Email: [maria.rodriguez@gmail.com]()
        - DOB: 1987-03-15
        - SSN last 4: 7394
        - Security question: What was the name of your first pet?
        - Security answer: Whiskers

        If asked whether you want to proceed with cancellation effective 2025-10-02, reply:
        “Yes, please proceed with cancellation effective 2025-10-02.”
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 18800
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291056
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (212) 847-5692
              security_answer: Whiskers
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-08-15'
              exclusion_form_required: false
              id: DRV-847291
              is_co_insured: false
              is_named_insured: true
              license_number: R123456789
              license_state: NY
              name: Maria Rodriguez
              policy_id: POL-3847291056
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 15
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-08-15'
              expiration_date: '2026-08-15'
              id: POL-3847291056
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-08-15'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-15'
              effective_date: '2024-08-15'
              id: VEH-847291
              make: Honda
              model: Accord
              policy_id: POL-3847291056
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F14KA123456
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-07-01T14:20:00Z'
              description: Customer requested proof of insurance document for vehicle registration renewal
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '47291'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: low
              request_category: Documents
              requester_id: '2847291'
              status: solved
              subject: Request for Proof of Insurance
              tags: []
              type: question
              updated_at: '2025-07-01T15:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '2847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (212) 847-5692
              role: end-user
              updated_at: '2024-08-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                policy_id: POL-3847291056
              tool: policy_get_policy_details
            - parameters:
                customer_id: CUST-847291
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUST-847291
                security_answer: Whiskers
                ssn_last_4: '7394'
              tool: crm_verify_identity
            - parameters:
                cancellation_date: '2025-10-02'
                cancellation_reason: User Requested
                policy_id: POL-3847291056
              tool: policy_schedule_cancellation
            - parameters:
                $filter: email eq 'maria.rodriguez@gmail.com'
                $orderby: null
                $select: id, name, email
                $skip: 0
                $top: 1
                table: users
              tool: zendesk_get_items
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer Maria Rodriguez requested cancellation effective 2025-10-01 due to new policy starting same day. Policy is NY; same-day cancellation not permitted. Earliest effective cancellation is 2025-10-02. This results in 1-day overlap (2025-10-01) and no gap. Cancellation scheduled effective 2025-10-02.
                  due_at: null
                  effective_date_of_change: '2025-10-02'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '2847291'
                  status: open
                  subject: Cancellation scheduled - POL-3847291056
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, My Name is Michael Rodriguez.  My email is [michael.rodriguez@techcorp.io](mailto:michael.rodriguez@techcorp.io) and date of birth is 1987-03-15. I'd like to cancel my auto policy (POL-4729183847) effective October 15, 2025, since I'm relocating for work and my new insurance starts then. Can you tell me how my prorated refund will be calculated? Although I'm asking about prorated refund calculations, I believe no refund is due because the next monthly premium payment date coincides with the cancellation date. I do expect the request to be completed today.
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.

        You can provide this information if asked:

        1. Your full name -  Michael Rodriguez
        2. Your date of birth - 1987-03-15
        3. Your Email - [michael.rodriguez@techcorp.io](mailto:michael.rodriguez@techcorp.io)
        4. Your Phone Number - (512) 847-3928
        5. Last 4 digits of Social Security number -   7394,
        6. Security Question -   What was the name of your first pet?,
        7. Security Answer - Buddy
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-TX-847291
              id: BILL-TX-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 15400
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183847
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: michael.rodriguez@techcorp.io
              first_name: Michael
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-TX-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-12-01'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: TX47291847
              license_state: TX
              name: Michael Rodriguez
              policy_id: POL-4729183847
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-TX-847291
              effective_date: '2024-12-01'
              expiration_date: '2025-12-01'
              id: POL-4729183847
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2025-12-01'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-12-01'
              effective_date: '2024-12-01'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-4729183847
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F34KA456789
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-02-18T10:30:00Z'
              email: michael.rodriguez@techcorp.io
              id: '2847291'
              name: Michael Rodriguez
              organization_id: '1'
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-15T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                email: michael.rodriguez@techcorp.io
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-TX-847291
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUST-TX-847291
                security_answer: Buddy
                ssn_last_4: '7394'
              tool: crm_verify_identity
            - parameters:
                $filter: email
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                id: '2847291'
                table: users
              tool: zendesk_get_item
            - parameters:
                policy_id: POL-4729183847
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-4729183847
              tool: billing_get_account_details
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested cancellation effective 2025-10-15 due to relocation. No refund ($0) as no prepayment was done for full year. Today is 2025-10-01.
                  due_at: null
                  effective_date_of_change: '2025-10-15'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '2847291'
                  status: open
                  subject: Policy cancellation request for POL-4729183847
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                cancellation_date: '2025-10-15'
                cancellation_reason: User Requested
                policy_id: POL-4729183847
              tool: policy_schedule_cancellation
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested cancellation effective 2025-10-15 due to relocation. No refund ($0) as no prepayment was done for full year. Today is 2025-10-01.
                  due_at: null
                  effective_date_of_change: '2025-10-15'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '2847291'
                  status: solved
                  subject: Policy cancellation request for POL-4729183847
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to cancel my auto policy (POL-3847291856) effective October 6, 2025. I've sold both my Honda Accord and Hyundai Sonata and am moving abroad, so I no longer need coverage. The vehicles have already been transferred. Please confirm the cancellation date and let me know if you need anything else from me.
    user_context: |
        Your name is Sarah Martinez and your email is [sarah.martinez@gmail.com](mailto:sarah.martinez@gmail.com)

        Your date of birth is 15 March 1987 and your SSN last 4 digits are 5911



        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 186
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: sarah.martinez@gmail.com
              first_name: Sarah
              fraud_flag: false
              id: CUST-847291
              last_name: Martinez
              phone: (212) 847-5692
              security_answer: Whiskers
              security_question: What was the name of your first pet?
              ssn_last_4: '5911'
              tier: Premium
          policy_drivers:
            - customer_id: null
              date_of_birth: '1987-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: M742918365
              license_state: NY
              name: Sarah Martinez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 7
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-06-15'
              state: NY
              status: Active
          policy_policy_documents:
            - created_at: '2025-09-28T14:35:00Z'
              document_type: proof_of_insurance
              expires_at: '2025-09-29T14:35:00Z'
              id: DOC-847291001
              policy_id: POL-3847291856
              ticket_id: '12847'
              url: https://docs.horizonshield.com/secure/proof-847291-xyz789
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGBH41JXMN109186
              year: 2021
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-847291002
              make: Hyundai
              model: Sonata
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 5NPE34AF4HH012877
              year: 2017
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-28T14:30:00Z'
              description: Customer requested proof of insurance documents for vehicle sale transaction. Documents needed to complete vehicle transfer process.
              due_at: null
              effective_date_of_change: null
              escalation_level: null
              id: '12847'
              internal_review_type: null
              organization_id: null
              outcome_summary: null
              priority: normal
              request_category: Documents
              requester_id: '847291'
              status: pending
              subject: Proof of Insurance Document Request
              tags: []
              type: task
              updated_at: '2025-09-28T14:30:00Z'
              user_type: null
          zendesk_users:
            - active: true
              created_at: '2023-02-14T10:30:00Z'
              email: sarah.martinez@gmail.com
              id: '847291'
              name: Sarah Martinez
              organization_id: null
              phone: (212) 847-5692
              role: end-user
              updated_at: '2025-09-28T16:45:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requests cancellation of auto policy POL-3847291856 effective 2025-10-06. Reason: Sold vehicles and moving abroad. NY minimum notice requirement met.'
                  due_at: null
                  effective_date_of_change: '2025-10-06'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Policy Cancellation Request - POL-3847291856
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                cancellation_date: '2025-10-06'
                cancellation_reason: User Requested
                policy_id: POL-3847291856
              tool: policy_schedule_cancellation
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requests cancellation of auto policy POL-3847291856 effective 2025-10-06. Reason: Sold vehicles and moving abroad. NY minimum notice requirement met.'
                  due_at: null
                  effective_date_of_change: '2025-10-06'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: solved
                  subject: Policy Cancellation Request - POL-3847291856
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez, and my date of birth is March 15, 1987. My policy number is POL-3847291582. I can’t afford the payments anymore, so I’d like to cancel my auto policy effective in 3 days. My account is currently in Grace Period and I have a past-due balance of $187.50. Will I still owe that past-due amount after the policy is cancelled?
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.

        If asked, you can confirm identity details, but you may ask one clarifying question before responding.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-25'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 18750
              new_due_date: null
              past_due_amount: 18750
              payment_received: false
              policy_id: POL-3847291582
              status: In Grace Period
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Standard
          policy_drivers:
            - customer_id: null
              date_of_birth: '1987-03-15'
              effective_date: '2024-04-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291582
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-04-01'
              expiration_date: '2026-04-01'
              id: POL-3847291582
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-04-01'
              state: CA
              status: In Grace Period
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-01'
              effective_date: '2024-04-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291582
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F36JA742913
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-26T09:00:00Z'
              description: Customer received payment overdue notice for policy POL-3847291582. Payment of $187.50 was due on 2025-09-25 and is now 6 days past due. Account is in Grace Period.
              due_at: null
              effective_date_of_change: null
              escalation_level: null
              id: '12847'
              internal_review_type: null
              organization_id: null
              outcome_summary: null
              priority: normal
              request_category: null
              requester_id: '847291'
              status: solved
              subject: Payment Overdue Notice
              tags: []
              type: incident
              updated_at: '2025-10-01T09:00:00Z'
              user_type: null
          zendesk_users:
            - active: true
              created_at: '2024-03-28T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-25T08:15:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                cancellation_date: '2025-10-04'
                cancellation_reason: User Requested
                policy_id: POL-3847291582
              tool: policy_schedule_cancellation
            - parameters:
                policy_id: POL-3847291582
              tool: billing_get_account_details
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests cancellation of auto policy POL-3847291582 effective 2025-10-04 due to inability to afford payments. Past-due amount of $187.50 remains owed after cancellation.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Policy Cancellation Request - POL-3847291582
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-04'
                  escalation_level: Standard
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez and my email id is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com).
        I recently made a payment for my policy that was cancelled for non-payment about 10 days ago (policy number POL-3847291856). Can you tell me when my coverage will resume?
    user_context: |
        Rules:

        If the agent asks for verification details please provide the below -

        your last 4 SSN - 4278

        your date of birth - 1987-03-15

        answer to the security question - Buddy

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-21'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: true
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '4278'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-06-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: '2025-09-21'
              cancellation_reason: Non-Payment
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-06-01'
              expiration_date: '2026-06-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: true
              lapse_start: '2025-09-21'
              named_insured_id: CUST-847291
              renewal_date: '2025-06-01'
              state: CA
              status: Cancelled for Non-Payment
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-01'
              effective_date: '2024-06-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM82683A582947
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-01-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '2847'
              name: Maria Rodriguez
              organization_id: '1'
              phone: (415) 892-3847
              role: end-user
              updated_at: '2024-01-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-847291
                security_answer: Buddy
                ssn_last_4: '4278'
              tool: crm_verify_identity
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer Maria Rodriguez requested reinstatement of policy POL-3847291856. Policy was cancelled for non-payment on 2025-09-21. Payment received and posted. Policy reinstated with lapse in coverage from 2025-09-21 to reinstatement date. Customer advised.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '2847'
                  status: open
                  subject: Policy Reinstatement - POL-3847291856
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                lapse_end: '2025-10-01'
                lapse_flag: true
                lapse_start: '2025-09-21'
                policy_id: POL-3847291856
              tool: policy_reinstate_policy
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez, customer ID CUS-84729186 and e-mail [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). I'd like to reinstate my auto policy POL-2847391652 that was cancelled for non-payment on September 6th. I already paid the full past-due amount. Can you help me get my coverage back?
    user_context: |
        You are born on 1987-03-15. Your  phone number is 415-892-3847. Your last 4 SSN digits are 7394, and your first pets name was Buddy

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-15'
              customer_id: CUS-84729186
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 21000
              new_due_date: null
              past_due_amount: 0
              payment_received: true
              policy_id: POL-2847391652
              status: Lapsed
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUS-84729186
              last_name: Rodriguez
              phone: 415-892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Preferred
          policy_drivers:
            - customer_id: CUS-84729186
              date_of_birth: '1987-03-15'
              effective_date: '2025-06-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472916
              license_state: TX
              name: Maria Rodriguez
              policy_id: POL-2847391652
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: '2025-09-06'
              cancellation_reason: Non-Payment
              co_insured_id: null
              customer_id: CUS-84729186
              effective_date: '2025-06-01'
              expiration_date: '2026-06-01'
              id: POL-2847391652
              lapse_end: null
              lapse_flag: true
              lapse_start: '2025-09-06'
              named_insured_id: CUS-84729186
              renewal_date: '2026-06-01'
              state: TX
              status: Cancelled for Non-Payment
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-06-01'
              effective_date: '2025-06-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-2847391652
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30KA126496
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-06T13:00:00Z'
              description: Customer policy was cancelled for non-payment. Customer has paid the past due ammount in full
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '18'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: solved
              subject: Policy cancellation - payment arrangement needed
              tags: []
              type: task
              updated_at: '2025-09-06T13:00:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: '1'
              phone: 415-892-3847
              role: end-user
              updated_at: '2025-09-23T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUS-84729186
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUS-84729186
                ssn_last_4: '7394'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-2847391652
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-2847391652
              tool: billing_get_account_details
            - parameters:
                $filter: email eq 'maria.rodriguez@gmail.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '847291'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested policy reinstatement. Customer is in the 30 day period (15 + 15 preferred account). Proceeding with policy reinstatement
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Policy reinstatement request
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                lapse_end: '2025-10-01'
                lapse_flag: true
                lapse_start: '2025-09-06'
                policy_id: POL-2847391652
              tool: policy_reinstate_policy
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Completed customer requested policy reinstatement. Customer is in the 30 day period (15 + 15 preferred account). Filling in correct ticket fields for policy reinstatement
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: solved
                  subject: Policy reinstatement request completed
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_013(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is **Maria Rodriguez**. My Florida auto policy **POL-3847291058** was **cancelled for non-payment about 40 days ago**, but I’ve now **paid the full balance** and want to **reinstate** it. For verification, my **DOB is 03/15/1985**, my email is **[maria.rodriguez@gmail.com]()**, and the **last 4 of my SSN is 7429**. Also—will this **lapse** affect my future premiums or renewal rate?
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-11-01'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 186
              new_due_date: null
              past_due_amount: 0
              payment_received: true
              policy_id: POL-3847291058
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: Bella
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Premium
          policy_drivers:
            - customer_id: CUST-FL-847291
              date_of_birth: '1985-03-15'
              effective_date: '2025-06-01'
              exclusion_form_required: false
              id: DRV-FL-847291
              is_co_insured: false
              is_named_insured: true
              license_number: R847291583
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: '2025-08-22'
              cancellation_reason: Non-Payment
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2025-06-01'
              expiration_date: '2026-06-01'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: true
              lapse_start: '2025-08-22'
              named_insured_id: CUST-FL-847291
              renewal_date: '2026-06-01'
              state: FL
              status: Cancelled for Non-Payment
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-06-01'
              effective_date: '2025-06-01'
              id: VEH-FL-847291
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F14JA123456
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-08-20T11:30:00Z'
              description: Policy POL-3847291058 was cancelled for non-payment effective 2025-08-22. Customer is requesting reinstatement and confirms full payment has been received. Customer also asks how the lapse may impact future premiums.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: TKT-847291-001
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: null
              priority: normal
              request_category: Policy Servicing
              requester_id: '847291'
              status: pending
              subject: Cancellation for Non-Payment - Reinstatement Request
              tags: []
              type: task
              updated_at: '2025-08-22T14:20:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-01-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (305) 847-2931
              role: end-user
              updated_at: '2025-08-22T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                lapse_end: '2025-10-01'
                lapse_flag: true
                lapse_start: '2025-08-22'
                policy_id: POL-3847291058
              tool: policy_reinstate_policy
            - parameters:
                id: TKT-847291-001
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: Full payment confirmed/posted and billing reset to Current. Reinstated policy POL-3847291058 (Premium tier) within the 45-day window. Lapse recorded from 2025-08-22 to 2025-10-01T13:00:00Z. Customer advised that a lapse may impact future premiums/renewal pricing per underwriting and state-approved rating factors (no specific premium change guaranteed).
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm James Peterson (DOB 06/12/1985). I'm really upset because I just saw my policy POL-9988776655 is still showing as cancelled even though I paid the full $250 balance a few days ago. I know I missed the deadline by just a couple of days, but I need my insurance back today! Can you please reinstate my New York policy?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUS-998877
              id: BILL-9988776655
              installment_amount: null
              installment_count: null
              last_payment_amount: 250
              last_payment_date: '2025-09-28'
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: true
              policy_id: POL-9988776655
              status: Cancelled
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-06-12'
              email: james.peterson@gmail.com
              first_name: James
              fraud_flag: false
              id: CUS-998877
              last_name: Peterson
              phone: (518) 472-8391
              security_answer: Buster
              security_question: First pet's name
              ssn_last_4: '7429'
              tier: Standard
          policy_drivers:
            - customer_id: CUS-998877
              date_of_birth: '1985-06-12'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-9988776655-001
              is_co_insured: false
              is_named_insured: true
              license_number: P984372106
              license_state: NY
              name: James Peterson
              policy_id: POL-9988776655
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: '2025-09-13'
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-998877
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-9988776655
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-998877
              renewal_date: '2026-06-15'
              state: NY
              status: Cancelled for Non-Payment
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-9988776655-001
              make: Honda
              model: Accord
              policy_id: POL-9988776655
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263JA000001
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-15T10:30:00Z'
              description: Customer requested policy reinstatement after cancellation for non-payment
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '10293'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Declined
              priority: normal
              request_category: Billing & Payments
              requester_id: '882'
              status: solved
              subject: Policy Reinstatement Request
              tags: []
              type: task
              updated_at: '2025-09-28T17:00:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-12T14:30:00Z'
              email: james.peterson@gmail.com
              id: '882'
              name: James Peterson
              organization_id: null
              phone: (518) 472-8391
              role: end-user
              updated_at: '2025-09-28T16:45:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUS-998877
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUS-998877
                security_answer: Buster
                ssn_last_4: '7429'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-9988776655
              tool: policy_get_policy_details
            - parameters:
                brand_id: null
                category: null
                label_names: null
                locale: null
                multibrand: null
                query: reinstatement window
                section: null
              tool: zendesk_search_articles
            - parameters:
                policy_id: POL-9988776655
              tool: billing_get_account_details
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested reinstatement 18 days after cancellation. NY Standard tier window is 15 days. Declined per ART-0008. Offered new application.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '882'
                  status: open
                  subject: Reinstatement Request - Declined
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_015(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Alex Diets, e-mail [alex.diets@gmail.com](mailto:alex.diets@gmail.com), customer ID CUS-47291830. I am contacting you about my auto policy (POL-8472951836) which was cancelled for non-payment about 35 days ago. I have paid the outstanding amount from my billing account today. I know I was late with my payment, but can I still get a reinstatement?
    user_context: |
        Your date of birth is 1987-06-14. Last 4 SSN are 7392 and first pet name is Bella.
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-11-01'
              customer_id: CUS-47291830
              id: BILL-84129418
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: true
              policy_id: POL-8472951836
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-06-14'
              email: alex.diets@gmail.com
              first_name: Alex
              fraud_flag: false
              id: CUS-47291830
              last_name: Diets
              phone: 415-729-3841
              security_answer: Bella
              security_question: What was the name of your first pet?
              ssn_last_4: '7392'
              tier: Preferred
          policy_drivers:
            - customer_id: CUS-47291830
              date_of_birth: '1987-06-14'
              effective_date: '2024-12-15'
              exclusion_form_required: false
              id: DRV-84729518
              is_co_insured: false
              is_named_insured: true
              license_number: D8472951
              license_state: CA
              name: Alex Diets
              policy_id: POL-8472951836
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: '2025-08-27'
              cancellation_reason: Non-Payment
              co_insured_id: null
              customer_id: CUS-47291830
              effective_date: '2024-12-15'
              expiration_date: '2025-12-15'
              id: POL-8472951836
              lapse_end: null
              lapse_flag: true
              lapse_start: '2025-08-27'
              named_insured_id: CUS-47291830
              renewal_date: '2025-12-15'
              state: CA
              status: Cancelled for Non-Payment
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-12-15'
              effective_date: '2024-12-15'
              id: VEH-8472951836
              make: Honda
              model: Accord
              policy_id: POL-8472951836
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F32KA012245
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-08-17T09:30:00Z'
              description: Customer requested payment extension due to temporary financial hardship. Extension granted for 10 days.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '2847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: '1847'
              status: solved
              subject: Payment Extension Request
              tags: []
              type: task
              updated_at: '2025-08-17T14:22:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-03-15T10:30:00Z'
              email: alex.diets@gmail.com
              id: '1847'
              name: Alex Diets
              organization_id: '1'
              phone: 415-729-3841
              role: end-user
              updated_at: '2025-08-17T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUS-47291830
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUS-47291830
                security_answer: Bella
                ssn_last_4: '7392'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-8472951836
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-8472951836
              tool: billing_get_account_details
            - parameters:
                $filter: requester_id eq '1847'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                $filter: email eq 'alex.diets@gmail.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests reinstatement of policy POL-8472951836 after payment. Policy cancelled 35 days ago.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '1847'
                  status: open
                  subject: Policy Reinstatement Request
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Declined
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_017(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to reinstate my auto policy POL-3847291058 that was cancelled for non-payment 8 days ago. How quickly can I pay the $385 past-due amount and get my coverage back?
    user_context: |
        You are Maria Rodriguez. Your email is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com), your phone number is (305) 847-2931, and your policy number is POL-3847291058. Your date of birth is April 15, 1987, and the last 4 digits of your SSN are 4729. You want to reinstate your policy that was cancelled for non-payment last month, and you want to understand how quickly you can pay and get your coverage back once you make the payment.

        **Rules**:

        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.

        You just want to understand the process and timeline for payment and getting reinstated but actually not going to pay now.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-15'
              customer_id: CUST-FL-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 385
              payment_received: false
              policy_id: POL-3847291058
              status: Cancelled
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-04-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: +1-305-847-2931
              security_answer: Santos
              security_question: What is your mother's maiden name?
              ssn_last_4: '4729'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-FL-847291
              date_of_birth: '1987-04-15'
              effective_date: '2023-02-15'
              exclusion_form_required: false
              id: DRV-847291-001
              is_co_insured: false
              is_named_insured: true
              license_number: R847291582
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: '2025-09-23'
              cancellation_reason: Non-Payment
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2023-02-15'
              expiration_date: '2026-02-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2026-02-15'
              state: FL
              status: Cancelled for Non-Payment
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2023-02-15'
              effective_date: '2023-02-15'
              id: VEH-847291-001
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263JA847291
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-02-14T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '2847291'
              name: Maria Rodriguez
              organization_id: null
              phone: +1-305-847-2931
              role: end-user
              updated_at: '2025-09-23T08:15:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-FL-847291
                security_answer: null
                ssn_last_4: '4729'
              tool: crm_verify_identity
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer Maria Rodriguez (POL-3847291058, Preferred tier) requests policy reinstatement. Policy cancelled for non-payment on 2025-09-23 (8 days ago). Customer is within Preferred tier 30-day reinstatement window per ART-0008. Past-due amount: $385. Payment not yet received. Customer informed that payment must be received before reinstatement can be processed.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '2847291'
                  status: open
                  subject: Policy Reinstatement Request - Payment Required
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Pending – User Action
                  priority: null
                  request_category: null
                  requester_id: null
                  status: pending
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_019(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I noticed my account is past due and I'm worried my policy POL-3847291856 was cancelled. My name is Elena Rodriguez. My email is [elena.rodriguez@gmail.com](mailto:elena.rodriguez@gmail.com). Can you please provide a status?
    user_context: |
        Rules:

        Your date of birth is 1985-03-15. The last 4 digits of your SSN are 7392.

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.

        Do not make further requests. End the conversation after receiving the current status of your policy. Do not attempt to change it or make payments.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 78
              payment_received: false
              policy_id: POL-3847291856
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: elena.rodriguez@gmail.com
              first_name: Elena
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (212) 847-3928
              security_answer: Whiskers
              security_question: What was the name of your first pet?
              ssn_last_4: '7392'
              tier: Premium
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: R155885291
              license_state: NY
              name: Elena Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-06-15'
              expiration_date: '2027-06-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-06-15'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8269KA123456
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-06-15T10:30:00Z'
              email: elena.rodriguez@gmail.com
              id: '847291'
              name: Elena Rodriguez
              organization_id: null
              phone: (212) 847-3928
              role: end-user
              updated_at: '2024-06-15T10:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                email: elena.rodriguez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-847291
              tool: crm_get_customer_profile
            - parameters:
                policy_id: POL-3847291856
              tool: policy_get_policy_details
            - parameters:
                customer_id: CUST-847291
                security_answer: null
                ssn_last_4: '7392'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-3847291856
              tool: billing_get_account_details
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Elena Rodriguez (POL-3847291856) contacted regarding past-due account status, worried policy was cancelled and asked about reinstatement. Policy is active, not cancelled. Explained past-due means payment is overdue but coverage remains active as long as payment is made by 2025-10-15. Offered payment options and reassured customer.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Billing & Payments
                  requester_id: '847291'
                  status: open
                  subject: Customer concerned about policy cancellation and reinstatement due to past-due status
                  tags: null
                  type: question
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_020(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Michael Rodriguez. My policy POL-4728163954 was cancelled for non-payment yesterday, but I just made the full payment today. Can you please reinstate my policy right away and confirm that my coverage is active again?
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.

        If asked info for verification, provide this info, name is Michael Rodriguez, email id is [michael.rodriguez@gmail.com](mailto:michael.rodriguez@gmail.com), DOB is 1987-03-15 and policy number is POL-4728163954


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-10-29'
              customer_id: CUST-4728163954
              id: BILL-4728163954
              installment_amount: null
              installment_count: null
              monthly_payment: 18750
              new_due_date: null
              past_due_amount: 0
              payment_received: true
              policy_id: POL-4728163954
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-4728163954
              last_name: Rodriguez
              phone: (512) 847-3921
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: null
              tier: Preferred
          policy_drivers:
            - customer_id: null
              date_of_birth: '1987-03-15'
              effective_date: '2024-09-30'
              exclusion_form_required: false
              id: DRV-4728163954-001
              is_co_insured: false
              is_named_insured: true
              license_number: TX12345678
              license_state: TX
              name: Michael Rodriguez
              policy_id: POL-4728163954
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: '2025-09-30'
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-4728163954
              effective_date: '2024-09-30'
              expiration_date: '2026-09-29'
              id: POL-4728163954
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-4728163954
              renewal_date: '2025-09-29'
              state: TX
              status: Cancelled for Non-Payment
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-09-30'
              effective_date: '2024-09-30'
              id: VEH-4728163954-001
              make: Honda
              model: Accord
              policy_id: POL-4728163954
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F50JA206911
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-15T09:00:00Z'
              description: Customer requested payment extension due to temporary financial hardship. Extension granted for 10 days.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: TKT-4728163954-001
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: ZD-4728163954
              status: solved
              subject: Payment Extension Request
              tags: []
              type: task
              updated_at: '2025-09-15T16:00:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-09-30T10:00:00Z'
              email: michael.rodriguez@gmail.com
              id: ZD-4728163954
              name: Michael Rodriguez
              organization_id: null
              phone: (512) 847-3921
              role: end-user
              updated_at: '2024-10-20T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                lapse_end: '2025-10-01'
                lapse_flag: true
                lapse_start: '2025-09-30'
                policy_id: POL-4728163954
              tool: policy_reinstate_policy
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requested reinstatement after cancellation for non-payment. Full payment received today. Policy reinstated with 1-day lapse (2025-09-30 to 2025-10-01). Coverage restored effective immediately.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: ZD-4728163954
                  status: open
                  subject: Policy Reinstatement Request
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: ZD-4728163954
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_lif_112(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Maria Rodriguez,[maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com) DOB 1985-03-15 last 4 SSN 2241. I am the co-insured person on my auto policy POL-4729381652 that was cancelled for non-payment on 2025-09-09. I have already paid the full past-due amount. Can you please process my reinstatement? Also, after reinstatement, can I add another vehicle to my policy in the same request? I do not want to add the vehicle now, maybe I will come back to you tomorrow on this.
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-09-09'
              customer_id: CUS-78421920
              id: BILL-7842912
              installment_amount: null
              installment_count: null
              monthly_payment: 186
              new_due_date: null
              past_due_amount: 0
              payment_received: true
              policy_id: POL-4729381652
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUS-78421920
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: null
              security_question: null
              ssn_last_4: '2241'
              tier: Preferred
            - date_of_birth: '1982-11-08'
              email: carlos.rodriguez@outlook.com
              first_name: Carlos
              fraud_flag: false
              id: CUS-78430861
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: null
              security_question: null
              ssn_last_4: '1142'
              tier: Preferred
          policy_drivers:
            - customer_id: CUS-78421920
              date_of_birth: '1985-03-15'
              effective_date: '2024-01-15'
              exclusion_form_required: false
              id: DRV-78429011
              is_co_insured: true
              is_named_insured: false
              license_number: F84729385141
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-4729381652
              relationship: Spouse
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: CUS-78430861
              date_of_birth: '1982-11-08'
              effective_date: '2024-01-15'
              exclusion_form_required: false
              id: DRV-78429012
              is_co_insured: false
              is_named_insured: true
              license_number: F58294736101
              license_state: FL
              name: Carlos Rodriguez
              policy_id: POL-4729381652
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 14
              cancellation_date: '2025-09-09'
              cancellation_reason: Non-Payment
              co_insured_id: CUS-78421920
              customer_id: CUS-78421920
              effective_date: '2024-01-15'
              expiration_date: '2026-01-15'
              id: POL-4729381652
              lapse_end: null
              lapse_flag: true
              lapse_start: '2025-09-09'
              named_insured_id: CUS-78430861
              renewal_date: '2026-01-15'
              state: FL
              status: Cancelled for Non-Payment
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-01-15'
              effective_date: '2024-01-15'
              id: VEH-FL-78429-01
              make: Honda
              model: Accord
              policy_id: POL-4729381652
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263JA121416
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-01T14:22:00Z'
              description: Customer notice of cancellation due to non-payment. Processed cancellation effective 2025-09-09 per Florida notice requirements.
              due_at: null
              effective_date_of_change: '2025-09-09'
              escalation_level: Standard
              id: '56'
              internal_review_type: null
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Policy Servicing
              requester_id: '78429'
              status: solved
              subject: Policy Cancellation Notice
              tags: []
              type: task
              updated_at: '2025-09-09T16:45:00Z'
              user_type: Co-Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '78429'
              name: Maria Rodriguez
              organization_id: null
              phone: (305) 847-2931
              role: end-user
              updated_at: '2025-09-09T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                lapse_end: '2025-10-01'
                lapse_flag: true
                lapse_start: '2025-09-09'
                policy_id: POL-4729381652
              tool: policy_reinstate_policy
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer (Maria Rodriguez, Co-Insured) requested reinstatement of policy POL-4729381652. Payment received. Policy reinstated with lapse from 2025-09-09 to 2025-10-01.
                  due_at: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '78429'
                  status: open
                  subject: Policy Reinstatement Request
                  tags: null
                  type: task
                  user_type: Co-Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_mul_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need help with two things: First, I was backing out of a parking spot yesterday in Texas City, Texas and accidentally bumped someone else who was backing out at the same time. No one was hurt, but there is a moderate amount of damage to the bumper and some of the paint on the back end. I have the other driver's info but no police report. Can I file a claim for this? It's for the 2020 Honda Accord (VIN: 1HGCV1F30LA671076). Second, I just bought a 2024 Honda CR-V five days ago (VIN: 5J6RS6H94RL322376) and want to add it to my policy (POL-3195137928).
    user_context: |
        You are Sarah Martinez. The last 4 digits of your SSN are 7394. Your email is [sarah.martinez@gmail.com](mailto:sarah.martinez@gmail.com). Your date of birth is 1985-03-15. The name of your first pet is Buddy.

        When asked, the name of the owner of the car you hit is George Wang. His phone number is (512) 847-6678. He is also covered by HorizonShield Insurance.

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-859438
              id: BILL-654674
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3195137928
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: sarah.martinez@gmail.com
              first_name: Sarah
              fraud_flag: false
              id: CUST-859438
              last_name: Martinez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Preferred
          policy_drivers:
            - customer_id: null
              date_of_birth: '1985-03-15'
              effective_date: '2024-08-15'
              exclusion_form_required: false
              id: DRV-978834887
              is_co_insured: false
              is_named_insured: true
              license_number: TX951622159
              license_state: TX
              name: Sarah Martinez
              policy_id: POL-3195137928
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 10
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-859438
              effective_date: '2024-08-15'
              expiration_date: '2026-08-15'
              id: POL-3195137928
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-859438
              renewal_date: '2026-08-15'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-15'
              effective_date: '2024-08-15'
              id: VEH-341402001
              make: Honda
              model: Accord
              policy_id: POL-3195137928
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30LA671076
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: sarah.martinez@gmail.com
              id: '847291'
              name: Sarah Martinez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2024-08-15T10:30:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                email: sarah.martinez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-859438
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUST-859438
                security_answer: null
                ssn_last_4: '7394'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-3195137928
              tool: policy_get_policy_details
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer was backing out and bumped another car, bumper damage, no injuries. Other party info obtained, no police report.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: null
                  requester_id: '847291'
                  status: open
                  subject: 'FNOL: Minor collision on 2025-09-30'
                  tags: null
                  type: incident
                  user_type: null
                table: tickets
              tool: zendesk_create_item
            - parameters:
                claim_type: Collision – Multi-Vehicle
                date_of_loss: '2025-09-30'
                driver_id: DRV-978834887
                has_bodily_injury: false
                loss_location: Texas City, TX
                other_party_insurance: HorizonShield Insurance
                other_party_name: George Wang
                other_party_phone: (512) 847-6678
                police_report_number: null
                police_report_required: false
                policy_id: POL-3195137928
                severity: Moderate
                siu_flag: None
                unlisted_driver_flag: null
                vehicle_id: VEH-341402001
                vehicle_vin: 1HGCV1F30LA671076
              tool: claims_create_fnol
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: FNOL – Collision
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Claims
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests to add 2024 Honda CR-V, purchased 2025-09-26, VIN provided, standard vehicle, eligible for addition.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: null
                  requester_id: '847291'
                  status: open
                  subject: 'Add Vehicle: 2024 Honda CR-V (VIN: 5J6RS6H94RL322376)'
                  tags: null
                  type: task
                  user_type: null
                table: tickets
              tool: zendesk_create_item
            - parameters:
                effective_date: '2025-09-26'
                make: Honda
                model: CR-V
                policy_id: POL-3195137928
                uw_pending: false
                vin: 5J6RS6H94RL322376
                year: 2024
              tool: policy_add_vehicle
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-09-26'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Elena Rodriguez, e-mail [maria.rodriguez@outlook.com](mailto:maria.rodriguez@outlook.com) customer ID CUS-00847291
        and policy ID POL-3847291056. I'd like to add my new 2024 Honda Civic (VIN: 2HGFE2F53RH126486) to my policy. I bought it 8 days ago and want the coverage to start from the purchase date. Can you backdate the addition to match when I bought it?
    user_context: |
        Your name is Maria Elena Rodriguez. Your e-mail is [maria.rodriguez@outlook.com](mailto:maria.rodriguez@outlook.com) and your date of birth is 1987-03-15. Your phone number is 813-492-7638. Your last 4 SSN are 7429 and your first name pet is Bella.

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-11-01'
              customer_id: CUS-00847291
              id: BILL-384729
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291056
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@outlook.com
              first_name: Maria Elena
              fraud_flag: false
              id: CUS-00847291
              last_name: Rodriguez
              phone: 813-492-7638
              security_answer: Bella
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Standard
          policy_drivers:
            - customer_id: null
              date_of_birth: '1987-03-15'
              effective_date: '2025-02-08'
              exclusion_form_required: false
              id: DRV-FL-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: R847291567125
              license_state: FL
              name: Maria Elena Rodriguez
              policy_id: POL-3847291056
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 10
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-00847291
              effective_date: '2025-02-01'
              expiration_date: '2026-02-01'
              id: POL-3847291056
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-00847291
              renewal_date: '2026-02-01'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-02-08'
              effective_date: '2025-02-08'
              id: VEH-00847291
              make: Honda
              model: Accord
              policy_id: POL-3847291056
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F32KA012245
              year: 2019
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-03-20'
              effective_date: '2025-03-20'
              id: VEH-00846291
              make: Hyundai
              model: Elantra
              policy_id: POL-3847291056
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: KMHLM4AG1MU018745
              year: 2021
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-12T14:30:00Z'
              email: maria.rodriguez@outlook.com
              id: '847291'
              name: Maria Elena Rodriguez
              organization_id: null
              phone: 813-492-7638
              role: end-user
              updated_at: '2025-09-28T10:15:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUS-00847291
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUS-00847291
                security_answer: Bella
                ssn_last_4: '7429'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-3847291056
              tool: policy_get_policy_details
            - parameters:
                vin: 2HGFE2F53RH126486
              tool: lookup_validate_vin
            - parameters:
                effective_date: '2025-09-23'
                make: Honda
                model: Civic
                policy_id: POL-3847291056
                vin: 2HGFE2F53RH126486
                year: 2024
              tool: policy_add_vehicle
            - parameters:
                $filter: email eq 'maria.rodriguez@outlook.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '847291'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requested addition of vehicle 2024 Honda Civic (VIN: 2HGFE2F53RH126486) to policy'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Addition of vehicle to policy ID POL-3847291056
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: 'Added following vehicle to policy 2024 Honda Civic (VIN: 2HGFE2F53RH126486)'
                  due_at: null
                  effective_date_of_change: '2025-09-23'
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: 'Added vehicle to policy '
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez. I'd like to add my new 2023 Toyota RAV4 to my policy POL-3847291582. I bought it 5 days ago (on 2025-09-26), and here is the VIN: JTMBWRFV2P1835721. Can you make the effective date the same as my purchase date?
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.

        If asked, provide the following details only when prompted:

        Date of birth: 1987-06-25

        Email address: [sarah.martinez@gmail.com](mailto:sarah.martinez@gmail.com)

        Phone number: (415) 892-3847

        Last four digits of social security number: 7429

        What was the name of your favorite pet: Buddy


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291582
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291582
              status: Current
          claims_claims:
            - claim_stage: Closed – Paid
              claim_type: Collision – Multi-Vehicle
              created_date: '2023-07-15'
              date_of_loss: '2023-07-15'
              driver_id: DRV-00015899
              has_bodily_injury: false
              id: CLM-847291001
              loss_location: San Francisco, CA
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: SF23-789456
              police_report_required: false
              policy_id: POL-3847291582
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291001
              vehicle_vin: 1HGCM82633A123457
          crm_customers:
            - date_of_birth: '1987-06-25'
              email: sarah.martinez@gmail.com
              first_name: Sarah
              fraud_flag: false
              id: CUST-847291
              last_name: Martinez
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Preferred
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1987-06-25'
              effective_date: '2022-03-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Sarah Martinez
              policy_id: POL-3847291582
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 1
              automatic_extension_days: 14
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2022-03-15'
              expiration_date: '2026-03-15'
              id: POL-3847291582
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-03-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2022-03-15'
              effective_date: '2022-03-15'
              id: VEH-847291001
              make: Honda
              model: Civic
              policy_id: POL-3847291582
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGBH41JXMN109186
              year: 2021
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-28T14:22:00Z'
              description: Customer asking about next payment due date and payment options
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: null
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: open
              subject: Billing inquiry - payment due date question
              tags: []
              type: question
              updated_at: '2025-09-28T14:22:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2022-02-14T10:30:00Z'
              email: sarah.martinez@gmail.com
              id: '847291'
              name: Sarah Martinez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requested to add 2023 Toyota RAV4 (VIN: JTMBWRFV2P1835721) to policy POL-3847291582. Purchase date: 2025-09-26. Per CA regulations, effective date is set to today (2025-10-01).'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Add 2023 Toyota RAV4 to policy
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                vin: JTMBWRFV2P1835721
              tool: lookup_validate_vin
            - parameters:
                effective_date: '2025-10-01'
                make: Toyota
                model: RAV4
                policy_id: POL-3847291582
                vin: JTMBWRFV2P1835721
                year: 2023
              tool: policy_add_vehicle
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Vehicle added successfully
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: solved
                  subject: Add 2023 Toyota RAV4 to policy
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_003(x: TestContext, judge: Judge):
    """!
    query: |
        I just bought a 2022 Chevrolet Corvette (VIN: 1G1YB2D40N5108R9T) three days ago and want to add it to my policy (POL-3847291058) with coverage starting from the purchase date. Can you backdate the effective date to three days ago?
    user_context: |
        You are Marcus Rodriguez, Date of Birth: 1985-03-15 and last 4 SSN: 7429



        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 186
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291058
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: marcus.rodriguez@gmail.com
              first_name: Marcus
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (813) 492-7583
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Standard
          policy_drivers:
            - customer_id: null
              date_of_birth: '1985-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-FL-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: R847291583
              license_state: FL
              name: Marcus Rodriguez
              policy_id: POL-3847291058
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 7
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2026-06-15'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-FL-847291-01
              make: Honda
              model: Civic
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 19XFC2F59JE8K472M
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-22'
              effective_date: '2024-08-22'
              id: VEH-FL-847291-02
              make: Ford
              model: F-150
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1FTFW1E50LFA9R6C2
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: marcus.rodriguez@gmail.com
              id: '847291'
              name: Marcus Rodriguez
              organization_id: null
              phone: (813) 492-7583
              role: end-user
              updated_at: '2025-09-20T14:22:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer Marcus Rodriguez requests to add a 2022 Chevrolet Corvette (VIN: 1G1YB2D40N5108R9T) to policy POL-3847291058, with coverage starting from 3 days ago (purchase date). Backdating requested. Vehicle is Sports Car class (high-risk for Standard tier).'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Add 2022 Chevrolet Corvette to policy POL-3847291058 (backdated)
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                effective_date: '2025-09-28'
                make: Chevrolet
                model: Corvette
                policy_id: POL-3847291058
                uw_pending: true
                vin: 1G1YB2D40N5108R9T
                year: 2022
              tool: policy_add_vehicle
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-09-28'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: hold
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Marcus Chen and my customer id is CUST-847291. I'd like to add my new 2024 Porsche 911 (VIN: WP0AA2A95RS123456) to my policy POL-3847291856. I bought it two days ago and want the coverage to start from the purchase date. Can you add it for me?
    user_context: |
        Rules:

        If the agent requests for the below details for verification purposes, please provide the same -

        1) last 4 digits of your SSN - 4526

        2) Answer to the security question - Buddy

        3) your email id - [marcus.chen@gmail.com](mailto:marcus.chen@gmail.com)

        4) your date of birth - 1985-03-15

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 48600
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims:
            - claim_stage: Closed – Paid
              claim_type: Collision – Single Vehicle
              created_date: '2023-05-20'
              date_of_loss: '2023-05-20'
              driver_id: DRV-847291001
              has_bodily_injury: false
              id: CLM-847291001
              loss_location: Brooklyn, NY
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: NYC-2023-052001
              police_report_required: false
              policy_id: POL-3847291856
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291001
              vehicle_vin: 1HGCV1F3XMA109186
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: marcus.chen@gmail.com
              first_name: Marcus
              fraud_flag: false
              id: CUST-847291
              last_name: Chen
              phone: (212) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '4526'
              tier: Premium
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: M123456789
              license_state: NY
              name: Marcus Chen
              policy_id: POL-3847291856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: '1'
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-06-15'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F3XMA109186
              year: 2021
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-20'
              effective_date: '2024-08-20'
              id: VEH-847291002
              make: Hyundai
              model: Elantra
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 5NPD74LF5HH012345
              year: 2017
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-04-01'
              effective_date: '2025-04-01'
              id: VEH-847291003
              make: Ford
              model: F-150
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1FTFW1ET5DFC10312
              year: 2013
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-04-01T09:15:00Z'
              description: Customer requested to add 2013 Ford F-150 to policy POL-3847291856
              due_at: null
              effective_date_of_change: '2025-04-01'
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Policy Servicing
              requester_id: '847291'
              status: solved
              subject: Add Vehicle - 2013 Ford F-150
              tags: []
              type: task
              updated_at: '2025-04-01T11:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-06-15T10:00:00Z'
              email: marcus.chen@gmail.com
              id: '847291'
              name: Marcus Chen
              organization_id: '1'
              phone: (212) 847-3928
              role: end-user
              updated_at: '2025-09-15T14:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUST-847291
                security_answer: Buddy
                ssn_last_4: '4526'
              tool: crm_verify_identity
            - parameters:
                customer_id: CUST-847291
              tool: crm_get_customer_profile
            - parameters:
                policy_id: POL-3847291856
              tool: policy_get_policy_details
            - parameters:
                vin: WP0AA2A95RS123456
              tool: lookup_validate_vin
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requested to add 2024 Porsche 911 (VIN: WP0AA2A95RS123456) to policy POL-3847291856. Effective date set to 2025-10-01 per NY regulations.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Add Vehicle - 2024 Porsche 911
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                effective_date: '2025-10-01'
                make: Porsche
                model: '911'
                policy_id: POL-3847291856
                uw_pending: false
                vin: WP0AA2A95RS123456
                year: 2024
              tool: policy_add_vehicle
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I’m Michael Rodriguez (michael.rodriguez@gmail.com). Please add my newly purchased 2020 Ford Mustang GT (VIN 1FA6P8CF2L5117834) to policy POL-4729183847.

        For verification: DOB 1987-03-15, SSN last 4 is 7392 (security answer: Buddy). I bought it 15 days ago, but if TX rules don’t allow backdating, please add it effective today.


    user_context: |
        **User Information:**

        - Your name is **Michael Rodriguez**.
        - Your email is **[michael.rodriguez@gmail.com]()**.
        - Your date of birth is **1987-03-15**.
        - Your policy number is **POL-4729183847**.

        **Rules:**

        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-TX-847291
              id: BILL-TX-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 0
              payment_received: true
              policy_id: POL-4729183847
              status: Current
          claims_claims:
            - claim_stage: Closed – Paid
              claim_type: Collision – Multi-Vehicle
              created_date: '2023-04-19T14:30:00Z'
              date_of_loss: '2023-04-18'
              driver_id: DRV-TX-847291
              has_bodily_injury: false
              id: CLM-TX-847291-1
              loss_location: Austin, TX
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: APD-2023-847291
              police_report_required: false
              policy_id: POL-4729183847
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-TX-847291-1
              vehicle_vin: 2HGFC2F59JH617348
            - claim_stage: Closed – Paid
              claim_type: Collision – Multi-Vehicle
              created_date: '2024-01-23T11:15:00Z'
              date_of_loss: '2024-01-22'
              driver_id: DRV-TX-847291
              has_bodily_injury: false
              id: CLM-TX-847291-2
              loss_location: Round Rock, TX
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: RRPD-2024-384752
              police_report_required: false
              policy_id: POL-4729183847
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-TX-847291-1
              vehicle_vin: 2HGFC2F59JH617348
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7392'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-TX-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-08-15'
              exclusion_form_required: false
              id: DRV-TX-847291
              is_co_insured: false
              is_named_insured: true
              license_number: TX-84729183
              license_state: TX
              name: Michael Rodriguez
              policy_id: POL-4729183847
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 2
              automatic_extension_days: 10
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-TX-847291
              effective_date: '2024-08-15'
              expiration_date: '2026-08-15'
              id: POL-4729183847
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2026-08-15'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-15'
              effective_date: '2024-08-15'
              id: VEH-TX-847291-1
              make: Honda
              model: Civic
              policy_id: POL-4729183847
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2HGFC2F59JH617348
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-28T14:30:00Z'
              description: Customer requesting proof of insurance document for vehicle registration renewal
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Pending – User Action
              priority: normal
              request_category: Documents
              requester_id: '847291'
              status: pending
              subject: Request for Proof of Insurance Document
              tags: []
              type: task
              updated_at: '2025-09-28T14:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:00:00Z'
              email: michael.rodriguez@gmail.com
              id: '847291'
              name: Michael Rodriguez
              organization_id: null
              phone: (512) 847-3928
              role: end-user
              updated_at: '2024-08-15T10:00:00Z'
              verified: true
            - active: true
              created_at: '2022-06-03T09:15:00Z'
              email: alicia.nguyen@insureco.com
              id: '585'
              name: Alicia Nguyen
              organization_id: null
              phone: (512) 438-2719
              role: agent
              updated_at: '2025-11-18T16:40:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests to add a newly purchased 2020 Ford Mustang GT to auto policy POL-4729183847. Vehicle was purchased 15 days ago, which is outside the 10-day automatic extension window in Texas, so coverage cannot be backdated to the purchase date. Effective date set to 2025-10-01. Underwriting review required due to high-risk vehicle class and claims history.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Add vehicle to auto policy
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                effective_date: '2025-10-01'
                make: Ford
                model: Mustang GT
                policy_id: POL-4729183847
                uw_pending: true
                vin: 1FA6P8CF2L5117834
                year: 2020
              tool: policy_add_vehicle
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: null
                  request_category: null
                  requester_id: null
                  status: hold
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Marcus Thompson and my email id is [marcus.thompson@gmail.com](mailto:marcus.thompson@gmail.com). I just bought a 2021 Dodge Challenger Hellcat four days ago and want to add it to my policy (POL-3847291582). Here is the VIN: [2C3CDZC98MH123466]. Please add it to my policy. My friend who purchased the same model a few months back wasn't allowed to add it to his insurance coverage. Hence if this vehicle can't be added to my policy, I would like to know why.  Please help me with the final status of this request.
    user_context: |
        Rules:

        If the agent asks for verification details please provide the below -

        your last 4 SSN - 7429

        your date of birth - 1987-03-15

        answer to the security question - Buddy

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 186
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291582
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: marcus.thompson@gmail.com
              first_name: Marcus
              fraud_flag: false
              id: CUST-847291
              last_name: Thompson
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-08-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D1235567
              license_state: CA
              name: Marcus Thompson
              policy_id: POL-3847291582
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 7
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-08-15'
              expiration_date: '2026-08-15'
              id: POL-3847291582
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-08-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-15'
              effective_date: '2024-08-15'
              id: VEH-847291001
              make: Honda
              model: Civic
              policy_id: POL-3847291582
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGFC2F59JH122456
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-07-01T14:20:00Z'
              description: Customer requested removal of 2016 Ford Focus VIN 1FADP3F21GL123456 from policy POL-3847291582. Vehicle was sold.
              due_at: null
              effective_date_of_change: '2025-07-01'
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Policy Servicing
              requester_id: '847291'
              status: solved
              subject: Remove 2016 Ford Focus from Policy
              tags: []
              type: task
              updated_at: '2025-07-01T15:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: marcus.thompson@gmail.com
              id: '847291'
              name: Marcus Thompson
              organization_id: '1'
              phone: (415) 892-3847
              role: end-user
              updated_at: '2024-08-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requests to add 2021 Dodge Challenger Hellcat (VIN: 2C3CDZC98MH123466) to policy POL-3847291582.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Add 2021 Dodge Challenger Hellcat to Policy
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Declined
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_008(x: TestContext, judge: Judge):
    """!
    query: |
        I'd like to add my recently purchased 2019 BMW 5-Series (VIN:WBA7E2C54KBH73842) with a salvage title to my policy. I bought it 10 days ago from a salvage auction. Is there any way I can get insurance coverage for this vehicle?
    user_context: |
        Your name is Michael Rodriguez and my Date of Birth is 1985-03-15, last 4 digits of ssn 7394 and policy number is POL-3847291856. Your email is [michael.rodriguez@gmail.com](mailto:michael.rodriguez@gmail.com)

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 286
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (212) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Premium
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-06-15'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: R122456689
              license_state: NY
              name: Michael Rodriguez
              policy_id: POL-3847291856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-06-15'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-15'
              effective_date: '2024-06-15'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F39MA437628
              year: 2021
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-10'
              effective_date: '2024-08-10'
              id: VEH-847291-02
              make: BMW
              model: X3
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 5UXTY5C06L9D63829
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-28T14:20:00Z'
              description: Customer asking about coverage details for recent minor fender bender incident
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: null
              priority: normal
              request_category: Claims
              requester_id: '847291'
              status: open
              subject: Claim inquiry - coverage question
              tags: []
              type: question
              updated_at: '2025-09-28T14:20:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-06-15T10:30:00Z'
              email: michael.rodriguez@gmail.com
              id: '847291'
              name: Michael Rodriguez
              organization_id: '1'
              phone: (212) 847-3928
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requests to add a 2019 BMW 5-Series with salvage title (VIN: WBA7E2C54KBH73842) purchased 10 days ago from salvage auction. Wants to know if insurance coverage is possible.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: 'Request to add salvage title vehicle - BMW 5-Series (VIN: WBA7E2C54KBH73842)'
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: Request declined due to policy not allowing salvage vehicle
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi! My name is Marcus Rodriguez, e-mail [marcus.rodriguez@gmail.com](mailto:marcus.rodriguez@gmail.com) customer ID CUS-84729186. I am contacting you about my personal policy POL-3847291058. I'd like to add my new 2022 Toyota Camry (VIN: 4T1BF1FK6NU122486) to my policy. I use it for Uber driving on weekends, doing rideshare. What are my options for rideshare coverage?
    user_context: |
        You are born on 1985-03-15. Your  phone number is 512-847-3928. Your last 4 SSN digits are 7394, and your first pets name was Buddy
        If the agent is telling you that he can add this vehicle to your personal policy but you are not covered for ridesharing, kindly decline and ask him not to add the vehicle.

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-10-15'
              customer_id: CUS-84729186
              id: BILL-842291
              installment_amount: null
              installment_count: null
              monthly_payment: 148
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291058
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: marcus.rodriguez@gmail.com
              first_name: Marcus
              fraud_flag: false
              id: CUS-84729186
              last_name: Rodriguez
              phone: 512-847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Preferred
          policy_drivers:
            - customer_id: null
              date_of_birth: '1985-03-15'
              effective_date: '2025-02-15'
              exclusion_form_required: false
              id: DRV-84729114
              is_co_insured: false
              is_named_insured: true
              license_number: TX47829156
              license_state: TX
              name: Marcus Rodriguez
              policy_id: POL-3847291058
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUS-84729186
              effective_date: '2025-02-15'
              expiration_date: '2026-02-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-84729186
              renewal_date: '2026-02-15'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-02-15'
              effective_date: '2025-02-15'
              id: VEH-84729114
              make: Honda
              model: Accord
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCM8263JA113566
              year: 2018
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: marcus.rodriguez@gmail.com
              id: '2847'
              name: Marcus Rodriguez
              organization_id: '1'
              phone: 512-847-3928
              role: end-user
              updated_at: '2025-09-28T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUS-84729186
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUS-84729186
                security_answer: Buddy
                ssn_last_4: '7394'
              tool: crm_verify_identity
            - parameters:
                brand_id: null
                category: null
                label_names: null
                locale: en-us
                multibrand: null
                query: Vehicles We Cannot Insure
                section: null
              tool: zendesk_search_articles
            - parameters:
                $filter: email eq 'marcus.rodriguez@gmail.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '2847'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Client requested addition of rideshare vehicle to policy. Request cannot be completed because rideshare vehicles are excluded from personal insurance policies as per ART-0002
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '2847'
                  status: open
                  subject: Request to add rideshare vehicle to policy
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '6'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Client requested addition of rideshare vehicle to policy. Request cannot be completed because rideshare vehicles are excluded from personal insurance policies as per ART-0002. Closing ticket as declined.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Declined
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '2847'
                  status: solved
                  subject: Request to add rideshare vehicle to policy
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Maria Rodriguez, customer ID CUS-84729186 and e-mail [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com). I am contacting you about my policy POL-2847391652. I just bought a 2024 Kia Sportage three days ago (VIN: KNDPX3A54R7125856) and want to add it to my policy. Can you help me add this new car? Is anything pending on my side for this to be resolved today?
    user_context: |
        You are born on 1987-03-15. Your  phone number is 415-892-3847. Your last 4 SSN digits are 7394, and your first pets name was Buddy
        If agent offers to help you with the payment of the due amount kindly refuse saying that you will do it at a later date. You want to have your ticket updated before closing the conversation.

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-15'
              customer_id: CUS-84729186
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 21000
              new_due_date: null
              past_due_amount: 21000
              payment_received: false
              policy_id: POL-2847391652
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUS-84729186
              last_name: Rodriguez
              phone: 415-892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Preferred
          policy_drivers:
            - customer_id: CUS-84729186
              date_of_birth: '1987-03-15'
              effective_date: '2025-06-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472916
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-2847391652
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: '2025-09-23'
              cancellation_reason: Non-Payment
              co_insured_id: null
              customer_id: CUS-84729186
              effective_date: '2025-06-01'
              expiration_date: '2026-06-01'
              id: POL-2847391652
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUS-84729186
              renewal_date: '2026-06-01'
              state: CA
              status: Cancelled for Non-Payment
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-06-01'
              effective_date: '2025-06-01'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-2847391652
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30KA126496
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-27T13:00:00Z'
              description: Customer policy was cancelled for non-payment 8 days ago. Customer needs assistance with payment arrangement to potentially reinstate policy.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '18'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Pending - User Action
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: pending
              subject: Policy cancellation - payment arrangement needed
              tags: []
              type: task
              updated_at: '2025-09-27T13:00:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: '1'
              phone: 415-892-3847
              role: end-user
              updated_at: '2025-09-23T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                customer_id: CUS-84729186
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUS-84729186
                security_answer: Buddy
                ssn_last_4: '7394'
              tool: crm_verify_identity
            - parameters:
                policy_id: POL-2847391652
              tool: policy_get_policy_details
            - parameters:
                policy_id: POL-2847391652
              tool: billing_get_account_details
            - parameters:
                $filter: email eq 'maria.rodriguez@gmail.com'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: users
              tool: zendesk_get_items
            - parameters:
                $filter: requester_id eq '847291'
                $orderby: null
                $select: null
                $skip: null
                $top: null
                table: tickets
              tool: zendesk_get_items
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Opening ticket with status = open. Vehicle addition cannot proceed until policy is reinstated. Policy cannot be reinstated because user past due amount on her billing account. User must pay in full before policy is reinstated
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Named insured requests addition of new vehicle
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Moving ticket to status=pending. Opening ticket with status = open. Vehicle addition cannot proceed until policy is reinstated. Policy cannot be reinstated because user past due amount on her billing account. User must pay in full before policy is reinstated
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Pending – User Action
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: pending
                  subject: Request to add new vehicle
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Michael Rodriguez and my email id is [michael.rodriguez@gmail.com](mailto:michael.rodriguez@gmail.com). I'd like to add my new 2023 Mercedes-Benz AMG C63 to my policy. I bought it yesterday and the VIN is W1K5J6BB0PF123456. Can you add it to my policy POL-3847291058?
    user_context: |
        Rules:

        If the agent asks for verification details please provide the below -

        your last 4 SSN - 7429

        your date of birth - 1987-03-15

        answer to the security question - Buddy

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 1
              current_due_date: '2025-09-26'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 286
              new_due_date: null
              past_due_amount: 286
              payment_received: false
              policy_id: POL-3847291058
              status: In Grace Period
          claims_claims:
            - claim_stage: Closed – Paid
              claim_type: Collision – Single Vehicle
              created_date: '2024-07-15'
              date_of_loss: '2024-07-15'
              driver_id: DRV-847291001
              has_bodily_injury: false
              id: CLM-847291001
              loss_location: Brooklyn, NY
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: null
              police_report_required: false
              policy_id: POL-3847291058
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291001
              vehicle_vin: 19XFC2F59LE123444
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (718) 394-8271
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7429'
              tier: Standard
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1987-03-15'
              effective_date: '2024-04-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: R123847291
              license_state: NY
              name: Michael Rodriguez
              policy_id: POL-3847291058
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 1
              automatic_extension_days: 7
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2024-04-15'
              expiration_date: '2026-04-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2025-04-15'
              state: NY
              status: In Grace Period
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-15'
              effective_date: '2024-04-15'
              id: VEH-847291001
              make: Honda
              model: Civic
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 19XFC2F59LE123444
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-08-01T14:20:00Z'
              description: Customer requested 10-day extension on payment due to temporary financial hardship
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847291'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Billing & Payments
              requester_id: '847291'
              status: solved
              subject: Billing Extension Request
              tags: []
              type: task
              updated_at: '2025-08-01T15:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-04-15T10:30:00Z'
              email: michael.rodriguez@gmail.com
              id: '847291'
              name: Michael Rodriguez
              organization_id: '1'
              phone: (718) 394-8271
              role: end-user
              updated_at: '2025-08-01T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                vin: W1K5J6BB0PF123456
              tool: lookup_validate_vin
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requested to add 2023 Mercedes-Benz AMG C63 (VIN: W1K5J6BB0PF123456) to policy POL-3847291058. Vehicle is high-value AMG model, triggers underwriting review. Effective date set to 2025-10-01 per NY rules.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Add 2023 Mercedes-Benz AMG C63 to policy
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                effective_date: '2025-10-01'
                make: Mercedes-Benz
                model: AMG C63
                policy_id: POL-3847291058
                uw_pending: true
                vin: W1K5J6BB0PF123456
                year: 2023
              tool: policy_add_vehicle
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: null
                  request_category: null
                  requester_id: null
                  status: hold
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_013(x: TestContext, judge: Judge):
    """!
    query: |
        I want to remove the Honda Accord from my policy. My policy number is POL-4729183847
    user_context: |
        You are Michael Rodriguez and your date of birth is 1985-03-15. Your policy number is POL-4729183847.

        If the Agent asks which model needs to be removed, respond 2020 model with VIN 1HGCV1F39LA213476



        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-TX-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 237
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183847
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: michael.rodriguez@gmail.com
              first_name: Michael
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: null
              tier: Premium
          policy_drivers:
            - customer_id: CUST-TX-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-01-15'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: TX12847392
              license_state: TX
              name: Michael Rodriguez
              policy_id: POL-4729183847
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-TX-847291
              effective_date: '2024-01-15'
              expiration_date: '2026-01-15'
              id: POL-4729183847
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2026-01-15'
              state: TX
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-01-15'
              effective_date: '2024-01-15'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-4729183847
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F39LA213476
              year: 2020
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-03-20'
              effective_date: '2024-03-20'
              id: VEH-847291-02
              make: Honda
              model: Accord
              policy_id: POL-4729183847
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F39MA789012
              year: 2021
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-10'
              effective_date: '2024-06-10'
              id: VEH-847291-03
              make: Toyota
              model: Camry
              policy_id: POL-4729183847
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 4T1C11AK5NU345678
              year: 2022
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2024-01-10T14:20:00Z'
              email: michael.rodriguez@gmail.com
              id: '847291'
              name: Michael Rodriguez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer requests removal of Honda Accord. Two Honda Accords (2020, 2021) present on policy. Clarification needed.
                  due_at: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Request to remove Honda Accord from policy POL-4729183847
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                effective_date: '2025-10-01'
                new_status: Removed
                vehicle_id: VEH-847291-01
              tool: policy_update_vehicle_status
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: Vehicle removal completed as requested.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Maria Rodriguez, my date of birth is 1985-03-15. I sold my 2019 Chevrolet Malibu and would like to remove it from my policy(POL-4729183847) effective today. Can you tell me if I'll get a refund for the unused premium?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-01'
              customer_id: CUST-FL-847291
              id: BILL-4729183847
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183847
              status: Current
          claims_claims:
            - claim_stage: Open – Initial Review
              claim_type: Collision – Multi-Vehicle
              created_date: '2025-09-25'
              date_of_loss: '2025-09-25'
              driver_id: null
              has_bodily_injury: false
              id: CLM-847291-001
              loss_location: Tampa, FL
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: null
              police_report_required: false
              policy_id: POL-4729183847
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291-01
              vehicle_vin: null
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (813) 492-7583
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: null
              tier: Preferred
          policy_drivers:
            - customer_id: null
              date_of_birth: '1985-03-15'
              effective_date: '2024-04-01'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: R847291583
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-4729183847
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2024-04-01'
              expiration_date: '2026-04-01'
              id: POL-4729183847
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2026-04-01'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-01'
              effective_date: '2024-04-01'
              id: VEH-847291-01
              make: Ford
              model: F-150
              policy_id: POL-4729183847
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1FTFW1ET5MKF47291
              year: 2021
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-04-01'
              effective_date: '2024-04-01'
              id: VEH-847291-02
              make: Chevrolet
              model: Malibu
              policy_id: POL-4729183847
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1G1ZD5ST5KF847291
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-25T14:30:00Z'
              description: Customer reported being rear-ended at traffic light on 9/25/25. Creating claim for investigation.
              due_at: null
              effective_date_of_change: null
              escalation_level: null
              id: '47291'
              internal_review_type: null
              organization_id: null
              outcome_summary: null
              priority: normal
              request_category: null
              requester_id: '2847'
              status: open
              subject: Claim for 2021 Ford F-150 - Rear-end collision
              tags: []
              type: incident
              updated_at: '2025-09-25T14:30:00Z'
              user_type: null
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '2847'
              name: Maria Rodriguez
              organization_id: null
              phone: (813) 492-7583
              role: end-user
              updated_at: '2024-08-15T10:30:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer sold 2019 Chevrolet Malibu and requests removal effective today. No open claims on this vehicle. Inform customer about refund for unused premium.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: null
                  requester_id: '2847'
                  status: open
                  subject: Remove 2019 Chevrolet Malibu from policy
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                open_only: true
                vehicle_id: VEH-847291-02
              tool: claims_get_vehicle_claims
            - parameters:
                effective_date: '2025-10-01'
                new_status: Removed
                vehicle_id: VEH-847291-02
              tool: policy_update_vehicle_status
            - parameters:
                policy_id: POL-4729183847
              tool: billing_get_account_details
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: Vehicle removed, Refund will be processed according to guidelines
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_015(x: TestContext, judge: Judge):
    """!
    query: |
        I sold my 2020 Nissan Altima (VIN 1N4BL4BV8LC278941) and want to remove it from my policy POL-3847291856. Can you help me with this?
    user_context: |
        Your name is Maria Rodriguez. Your date of birth is 1987-03-15. Your email is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@hotmail.com). Your relationship to the policy is Named Insured. The last 4 digits of your SSN are 7394. The answer to the security question "What was the name of your first pet?" is "Buddy". Before the agent proceeds with vehicle removal, ask if there is any problem if it's the only car on the policy. Proceed with cancellation if offered.

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 128
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '7394'
              tier: Standard
          policy_drivers:
            - customer_id: null
              date_of_birth: '1987-03-15'
              effective_date: '2025-06-01'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2025-06-01'
              expiration_date: '2026-06-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-06-01'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2025-06-01'
              effective_date: '2025-06-01'
              id: VEH-847291001
              make: Nissan
              model: Altima
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1N4BL4BV8LC278941
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-06-01T14:15:00Z'
              description: Customer requested to add 2020 Nissan Altima VIN 1N4BL4BV8LC278941 to policy POL-3847291856. Vehicle acquired on 2025-05-28. Added successfully with effective date 2025-06-01.
              due_at: null
              effective_date_of_change: '2025-06-01'
              escalation_level: Standard
              id: '12847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Policy Servicing
              requester_id: '847291'
              status: solved
              subject: Add Vehicle - 2020 Nissan Altima
              tags: []
              type: task
              updated_at: '2025-06-01T14:25:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2025-06-01T14:15:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-06-01T14:22:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                policy_id: POL-3847291856
              tool: policy_get_policy_details
            - parameters:
                active_only: true
                policy_id: POL-3847291856
              tool: policy_get_policy_vehicles
            - parameters:
                email: maria.rodriguez@gmail.com
              tool: crm_get_customer_by_email
            - parameters:
                customer_id: CUST-847291
              tool: crm_get_customer_profile
            - parameters:
                customer_id: CUST-847291
                security_answer: Buddy
                ssn_last_4: '7394'
              tool: crm_verify_identity
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requests cancellation of policy POL-3847291856 since they could not remove only active vehicle. Cancellation date set as per California notice requirements (minimum 1 day in future).  '
                  due_at: null
                  effective_date_of_change: '2025-10-02'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Customer-requested cancellation of policy POL-3847291856
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                cancellation_date: '2025-10-02'
                cancellation_reason: User Requested
                policy_id: POL-3847291856
              tool: policy_schedule_cancellation
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: null
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: null
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_018(x: TestContext, judge: Judge):
    """!
    query: |
        Hi my name is Maria Rodriguez. I'd like to remove my 2019 Honda Civic (VIN: **2HGFC2F69KH153796**) from my policy now that the claim on it is closed. Can you process this removal today? My policy number is POL-3847291058.
    user_context: |
        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.

        When asked for verification purposes, your email is [maria.rodriguez@gmail.com](mailto:maria.rodriguez@gmail.com), phone number: (305) 847-2931 and last 4 digits of SSN are: 3674, date of birth is 1985-03-15.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-FL-847291
              id: BILL-FL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 154
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291058
              status: Current
          claims_claims:
            - claim_stage: Closed – Paid
              claim_type: Collision – Multi-Vehicle
              created_date: '2025-09-16T08:30:00Z'
              date_of_loss: '2025-09-15'
              driver_id: null
              has_bodily_injury: false
              id: CLM-FL-847291-001
              loss_location: Miami, FL
              other_party_insurance: State Farm
              other_party_name: James Thompson
              other_party_phone: (305) 729-4851
              police_report_number: MPD-2025-091501
              police_report_required: false
              policy_id: POL-3847291058
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-FL-847291-01
              vehicle_vin: 2HGFC2F69KH153796
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-FL-847291
              last_name: Rodriguez
              phone: (305) 847-2931
              security_answer: Salem
              security_question: What is the name of your cat?
              ssn_last_4: '3674'
              tier: Standard
          policy_drivers:
            - customer_id: null
              date_of_birth: '1985-03-15'
              effective_date: '2024-01-15'
              exclusion_form_required: false
              id: DRV-FL-847291-01
              is_co_insured: false
              is_named_insured: false
              license_number: R847291582
              license_state: FL
              name: Maria Rodriguez
              policy_id: POL-3847291058
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-FL-847291
              effective_date: '2024-01-15'
              expiration_date: '2026-01-15'
              id: POL-3847291058
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-FL-847291
              renewal_date: '2026-01-15'
              state: FL
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-01-15'
              effective_date: '2024-01-15'
              id: VEH-FL-847291-01
              make: Honda
              model: Civic
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2HGFC2F69KH153796
              year: 2019
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-01-15'
              effective_date: '2024-01-15'
              id: VEH-FL-847291-02
              make: Toyota
              model: Corolla
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 2T1BURHE0JC123456
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-03-08'
              effective_date: '2024-03-08'
              id: VEH-FL-847291-03
              make: Ford
              model: F-150
              policy_id: POL-3847291058
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1FTFW1ET5DFC78901
              year: 2020
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: FNOL – Collision
              created_at: '2025-09-16T08:30:00Z'
              description: Customer reported rear-end collision on Coral Way. Multi-vehicle accident with other party information collected. Police report filed.
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '12847291'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Claims
              requester_id: '847291'
              status: solved
              subject: Claim Filed - Rear-End Collision
              tags: []
              type: incident
              updated_at: '2025-09-21T16:45:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2023-02-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '847291'
              name: Maria Rodriguez
              organization_id: null
              phone: (305) 847-2931
              role: end-user
              updated_at: '2025-09-20T14:22:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                active_only: null
                policy_id: POL-3847291058
              tool: policy_get_policy_vehicles
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Removed 2019 Honda Civic (VIN: 2HGFC2F69KH153796) from policy POL-3847291058 effective 2025-10-01 at customer request. Claim on vehicle is closed.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: 'Vehicle Removed - 2019 Honda Civic (VIN: 2HGFC2F69KH153796)'
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                effective_date: '2025-10-01'
                new_status: Removed
                vehicle_id: VEH-FL-847291-01
              tool: policy_update_vehicle_status
            - parameters:
                id: '7'
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Removed 2019 Honda Civic (VIN: 2HGFC2F69KH153796) from policy POL-3847291058 effective 2025-10-01 at customer request. Claim on vehicle is closed.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: solved
                  subject: 'Vehicle Removed - 2019 Honda Civic (VIN: 2HGFC2F69KH153796)'
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_019(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Sarah Martinez and my email id is [sarah.martinez@gmail.com](mailto:sarah.martinez@gmail.com). I'd like to remove my 2022 Mazda CX-5 from my policy. I recently moved and no longer need the third vehicle. My policy number is POL-3847291856.
    user_context: |
        Provide below verification details if asked by the agent

        1) your last 4 SSN - 4736

        2) your date of birth - 1987-03-15

        3) you are the named insured on the policy



        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-09-24'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 153
              new_due_date: null
              past_due_amount: 184
              payment_received: false
              policy_id: POL-3847291856
              status: Past Due
          claims_claims: []
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: sarah.martinez@gmail.com
              first_name: Sarah
              fraud_flag: false
              id: CUST-847291
              last_name: Martinez
              phone: (415) 892-3847
              security_answer: null
              security_question: null
              ssn_last_4: '4736'
              tier: Premium
          policy_drivers:
            - customer_id: null
              date_of_birth: '1987-03-15'
              effective_date: '2023-02-01'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: D1847291
              license_state: CA
              name: Sarah Martinez
              policy_id: POL-3847291856
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2023-02-01'
              expiration_date: '2026-02-01'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-02-01'
              state: CA
              status: In Grace Period
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2023-02-01'
              effective_date: '2023-02-01'
              id: VEH-847291-01
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F30LA125456
              year: 2020
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2023-03-15'
              effective_date: '2023-03-15'
              id: VEH-847291-02
              make: Toyota
              model: Camry
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 4T1BF1FK5JU113456
              year: 2018
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-10'
              effective_date: '2024-06-10'
              id: VEH-847291-03
              make: Mazda
              model: CX-5
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: JM3KFBDM6N0847291
              year: 2022
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-01T10:15:00Z'
              description: Customer requested removal of son Michael Martinez from policy POL-3847291856. Driver moved out of household for college. Effective date 2025-09-01.
              due_at: null
              effective_date_of_change: '2025-09-01'
              escalation_level: Standard
              id: '12847291'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Completed
              priority: normal
              request_category: Policy Servicing
              requester_id: '847291'
              status: solved
              subject: Remove Driver - Michael Martinez
              tags: []
              type: task
              updated_at: '2025-09-01T11:30:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2022-08-15T10:30:00Z'
              email: sarah.martinez@gmail.com
              id: '847291'
              name: Sarah Martinez
              organization_id: null
              phone: (415) 892-3847
              role: end-user
              updated_at: '2025-09-24T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: Customer Sarah Martinez (Named Insured) requested removal of 2022 Mazda CX-5 (VIN JM3KFBDM6N0847291) from policy POL-3847291856. No open claims on vehicle. Effective date 2025-10-01.
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Remove Vehicle - 2022 Mazda CX-5
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                effective_date: '2025-10-01'
                new_status: Removed
                vehicle_id: VEH-847291-03
              tool: policy_update_vehicle_status
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_020(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I’m **Sarah Chen**. I’m calling from **New York** and I need to **add a new vehicle** to my HorizonShield auto policy.

        My **policy number is POL-3847291856**, my **date of birth is 03/15/1985**, and the **last 4 digits of my SSN are 4821**.

        I bought a **2024 Tesla Model S Plaid** about **6 days ago** and want to add it to my policy. Here’s the **VIN:** 5YJSA1E58RF839214.

        Can you add it and tell me **when coverage will start** and if you need anything else from me?
    user_context: |


        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.


    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 286
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims:
            - claim_stage: Closed – Paid
              claim_type: Collision – Multi-Vehicle
              created_date: '2023-09-16T08:30:00Z'
              date_of_loss: '2023-09-15'
              driver_id: null
              has_bodily_injury: false
              id: CLM-847291001
              loss_location: Brooklyn, NY
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: NYC-2023-091578
              police_report_required: false
              policy_id: POL-3847291856
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291001
              vehicle_vin: null
            - claim_stage: Closed – Paid
              claim_type: Collision – Parked Vehicle
              created_date: '2024-03-01T10:15:00Z'
              date_of_loss: '2024-02-28'
              driver_id: null
              has_bodily_injury: false
              id: CLM-847291002
              loss_location: Manhattan, NY
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: null
              police_report_required: false
              policy_id: POL-3847291856
              severity: Minor
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-847291002
              vehicle_vin: null
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: sarah.chen@gmail.com
              first_name: Sarah
              fraud_flag: false
              id: CUST-847291
              last_name: Chen
              phone: (212) 847-3928
              security_answer: null
              security_question: null
              ssn_last_4: null
              tier: Preferred
          policy_drivers:
            - customer_id: null
              date_of_birth: '1985-03-15'
              effective_date: '2023-06-15'
              exclusion_form_required: false
              id: DRV-847291001
              is_co_insured: false
              is_named_insured: true
              license_number: '123847291'
              license_state: NY
              name: Sarah Chen
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 2
              automatic_extension_days: 10
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-847291
              effective_date: '2023-06-15'
              expiration_date: '2026-06-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-06-15'
              state: NY
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2023-06-15'
              effective_date: '2023-06-15'
              id: VEH-847291001
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F35LA074392
              year: 2020
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2023-08-20'
              effective_date: '2023-08-20'
              id: VEH-847291002
              make: Tesla
              model: Model 3
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 5YJ3E1EA9KF472801
              year: 2019
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-12T14:30:00Z'
              email: sarah.chen@gmail.com
              id: '847291'
              name: Sarah Chen
              organization_id: null
              phone: (212) 847-3928
              role: end-user
              updated_at: '2025-09-28T10:15:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Named insured Sarah Chen requests to add a newly purchased 2024 Tesla Model S Plaid. Purchase was 6 days ago (2025-09-25). NY prohibits backdating, so effective date set to 2025-10-01. Preferred tier does not require UW review for high-value vehicle alone; however policy has 2 at-fault claims in past 3 years → UW review required regardless of tier. VIN provided: 5YJSA1E58RF839214.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: 'Policy Servicing – Add Vehicle: 2024 Tesla Model S Plaid (NY) – UW Review (Claims History)'
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                effective_date: '2025-10-01'
                make: Tesla
                model: Model S Plaid
                policy_id: POL-3847291856
                uw_pending: true
                vin: 5YJSA1E58RF839214
                year: 2024
              tool: policy_add_vehicle
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: Vehicle added effective 2025-10-01 (NY prohibits backdating; purchase date 2025-09-25). UW review required due to 2 at-fault claims in past 3 years (tier-independent trigger). Vehicle marked UW pending. Customer advised coverage starts today and premium will update per billing cycle.
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: null
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: null
                  request_category: null
                  requester_id: null
                  status: hold
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_021(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, my name is Marcus Rodriguez and my email id is [marcus.rodriguez@gmail.com](mailto:marcus.rodriguez@gmail.com). I just bought a new sports car 2023 Subaru WRX STI on 19th September 2025 and want to add it to my policy POL-4729183847. Here is the VIN: JF1VBAF65P9802525. Can you backdate the coverage to the date I bought the car? Can this be resolved today? Also, I learnt from my friend that sports car addition requires underwriting review as it happened for him. Let me know if this is the case here as well.
    user_context: |
        Rules:

        If the agent asks for verification information, please provide the below details -

        your date of birth - 1987-03-15

        your last 4 SSN - 5378

        your security answer - Buddy

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-TX-847291
              id: BILL-TX-847291
              installment_amount: null
              installment_count: null
              monthly_payment: 188
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-4729183847
              status: Current
          claims_claims:
            - claim_stage: Closed – Paid
              claim_type: Collision – Single Vehicle
              created_date: '2024-08-18'
              date_of_loss: '2024-08-18'
              driver_id: DRV-TX-847291
              has_bodily_injury: false
              id: CLM-TX-847291-2023
              loss_location: Austin, TX
              other_party_insurance: null
              other_party_name: null
              other_party_phone: null
              police_report_number: null
              police_report_required: false
              policy_id: POL-4729183847
              severity: Moderate
              siu_flag: None
              unlisted_driver_flag: false
              vehicle_id: VEH-TX-847291-1
              vehicle_vin: 1HGBH41JXMN109186
          crm_customers:
            - date_of_birth: '1987-03-15'
              email: marcus.rodriguez@gmail.com
              first_name: Marcus
              fraud_flag: false
              id: CUST-TX-847291
              last_name: Rodriguez
              phone: (512) 847-3928
              security_answer: Buddy
              security_question: What was the name of your first pet?
              ssn_last_4: '5378'
              tier: Standard
          policy_drivers:
            - customer_id: null
              date_of_birth: '1987-03-15'
              effective_date: '2024-08-15'
              exclusion_form_required: false
              id: DRV-TX-847291
              is_co_insured: false
              is_named_insured: true
              license_number: TX47291847
              license_state: TX
              name: Marcus Rodriguez
              policy_id: POL-4729183847
              relationship: Self
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 1
              automatic_extension_days: 14
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: null
              customer_id: CUST-TX-847291
              effective_date: '2024-08-15'
              expiration_date: '2026-08-15'
              id: POL-4729183847
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-TX-847291
              renewal_date: '2025-08-15'
              state: TX
              status: Active
          policy_policy_documents:
            - created_at: '2025-09-28T14:25:00Z'
              document_type: declarations_page
              expires_at: '2025-09-29T14:25:00Z'
              id: DOC-POL-4729183847-DECL
              policy_id: POL-4729183847
              ticket_id: '29847'
              url: https://docs.horizonshield.com/declarations/POL-4729183847-2024.pdf
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-08-15'
              effective_date: '2024-08-15'
              id: VEH-TX-847291-1
              make: Honda
              model: Civic
              policy_id: POL-4729183847
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGBH41JXMN109186
              year: 2021
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets:
            - assignee_id: '585'
              claims_action_type: null
              created_at: '2025-09-28T14:20:00Z'
              description: Customer requested proof of insurance document for policy POL-4729183847
              due_at: null
              effective_date_of_change: null
              escalation_level: Standard
              id: '29847'
              internal_review_type: Not Required
              organization_id: null
              outcome_summary: Pending – User Action
              priority: normal
              request_category: Documents
              requester_id: '847291'
              status: pending
              subject: Proof of Insurance Document Request
              tags: []
              type: task
              updated_at: '2025-09-28T14:25:00Z'
              user_type: Named Insured
          zendesk_users:
            - active: true
              created_at: '2024-08-15T10:30:00Z'
              email: marcus.rodriguez@gmail.com
              id: '847291'
              name: Marcus Rodriguez
              organization_id: '1'
              phone: (512) 847-3928
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: true
        golden_test_case:
          tool_interactions:
            - parameters:
                vin: JF1VBAF65P9802525
              tool: lookup_validate_vin
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requests addition of 2023 Subaru WRX STI (VIN: JF1VBAF65P9802525) to policy POL-4729183847, effective 2025-09-19. Sports car triggers underwriting review.'
                  due_at: null
                  effective_date_of_change: '2025-09-19'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '847291'
                  status: open
                  subject: Add 2023 Subaru WRX STI to policy POL-4729183847
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                effective_date: '2025-09-19'
                make: Subaru
                model: WRX STI
                policy_id: POL-4729183847
                uw_pending: true
                vin: JF1VBAF65P9802525
                year: 2023
              tool: policy_add_vehicle
            - parameters:
                id: '7'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: null
                  due_at: null
                  effective_date_of_change: '2025-09-19'
                  escalation_level: Standard
                  internal_review_type: Underwriting
                  organization_id: null
                  outcome_summary: Pending – Internal Review
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: null
                  status: hold
                  subject: null
                  tags: null
                  type: task
                  user_type: Named Insured
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)


def test_veh_113(x: TestContext, judge: Judge):
    """!
    query: |
        I want to remove the Toyota Camry from my policy. Can you do this for me today?
    user_context: |
        You are David Rodriguez and your date of birth is 1983-07-22. Last 4 digits of SSN: 2856. Your policy number is POL-3847291856.

        If the Agent asks which model needs to be removed, respond 2019 model with VIN 4T1B11HK5KU392847

        Rules:

        Do not invent or provide any data not present in the provided context.

        Do not change your goal or switch topics.

        If asked for the same info, provide it again.

        Remain focused, clear, and patient.
    init:
      sandbox_auto_insurance:
        data_patch:
          billing_billing_accounts:
            - arrangement_type: None
              arrangements_12_months: 0
              current_due_date: '2025-10-15'
              customer_id: CUST-847291
              id: BILL-847291856
              installment_amount: null
              installment_count: null
              monthly_payment: 237
              new_due_date: null
              past_due_amount: 0
              payment_received: false
              policy_id: POL-3847291856
              status: Current
          claims_claims: []
          crm_customers:
            - date_of_birth: '1985-03-15'
              email: maria.rodriguez@gmail.com
              first_name: Maria
              fraud_flag: false
              id: CUST-847291
              last_name: Rodriguez
              phone: (415) 892-3847
              security_answer: null
              security_question: null
              ssn_last_4: null
              tier: Premium
            - date_of_birth: '1983-07-22'
              email: david.rodriguez@gmail.com
              first_name: David
              fraud_flag: false
              id: CUST-847292
              last_name: Rodriguez
              phone: (415) 892-3848
              security_answer: null
              security_question: null
              ssn_last_4: '2856'
              tier: Premium
          policy_drivers:
            - customer_id: CUST-847291
              date_of_birth: '1985-03-15'
              effective_date: '2024-01-15'
              exclusion_form_required: false
              id: DRV-847291-01
              is_co_insured: false
              is_named_insured: true
              license_number: D8472915
              license_state: CA
              name: Maria Rodriguez
              policy_id: POL-3847291856
              relationship: Named Insured
              removal_date: null
              status: Rated
              uw_pending: false
            - customer_id: CUST-847292
              date_of_birth: '1983-07-22'
              effective_date: '2024-01-15'
              exclusion_form_required: false
              id: DRV-847292-01
              is_co_insured: true
              is_named_insured: false
              license_number: D8472916
              license_state: CA
              name: David Rodriguez
              policy_id: POL-3847291856
              relationship: Co-Insured
              removal_date: null
              status: Rated
              uw_pending: false
          policy_policies:
            - at_fault_claims_3_years: 0
              automatic_extension_days: 30
              cancellation_date: null
              cancellation_reason: null
              co_insured_id: CUST-847292
              customer_id: CUST-847291
              effective_date: '2024-01-15'
              expiration_date: '2026-01-15'
              id: POL-3847291856
              lapse_end: null
              lapse_flag: false
              lapse_start: null
              named_insured_id: CUST-847291
              renewal_date: '2026-01-15'
              state: CA
              status: Active
          policy_policy_documents: []
          policy_vehicles:
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-01-15'
              effective_date: '2024-01-15'
              id: VEH-847291-01
              make: Toyota
              model: Camry
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 4T1B11HK5KU392847
              year: 2019
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-03-22'
              effective_date: '2024-03-22'
              id: VEH-847291-02
              make: Toyota
              model: Camry
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 4T1B11HK6LU584163
              year: 2020
            - collision_coverage: true
              comprehensive_coverage: true
              date_added_to_policy: '2024-06-17'
              effective_date: '2024-06-17'
              id: VEH-847291-03
              make: Honda
              model: Accord
              policy_id: POL-3847291856
              removal_date: null
              rental_coverage: false
              status: Active
              uw_pending: false
              vin: 1HGCV1F14MA203578
              year: 2021
          zendesk_articles: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_ticket_status_violations: []
          zendesk_tickets: []
          zendesk_users:
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: maria.rodriguez@gmail.com
              id: '2847291'
              name: Maria Rodriguez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: false
            - active: true
              created_at: '2023-08-15T10:30:00Z'
              email: david.rodriguez@gmail.com
              id: '2847292'
              name: David Rodriguez
              organization_id: null
              phone: null
              role: end-user
              updated_at: '2025-09-28T14:20:00Z'
              verified: false
        golden_test_case:
          tool_interactions:
            - parameters:
                item:
                  assignee_id: '585'
                  claims_action_type: null
                  description: 'Customer requests to remove a Toyota Camry from policy POL-3847291856. Ambiguity detected: two Toyota Camry''s (2020, 2019) present. Clarification needed.'
                  due_at: null
                  effective_date_of_change: null
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: null
                  priority: normal
                  request_category: Policy Servicing
                  requester_id: '2847292'
                  status: open
                  subject: Remove Toyota Camry from policy POL-3847291856
                  tags: null
                  type: task
                  user_type: Co-Insured
                table: tickets
              tool: zendesk_create_item
            - parameters:
                effective_date: '2025-10-01'
                new_status: Removed
                vehicle_id: VEH-847291-01
              tool: policy_update_vehicle_status
            - parameters:
                id: '6'
                item:
                  assignee_id: null
                  claims_action_type: null
                  description: 'Vehicle VEH-847291-01 (2019 Toyota Camry, VIN: 4T1B11HK5KU392847) removed from policy as requested.'
                  due_at: null
                  effective_date_of_change: '2025-10-01'
                  escalation_level: Standard
                  internal_review_type: Not Required
                  organization_id: null
                  outcome_summary: Completed
                  priority: null
                  request_category: Policy Servicing
                  requester_id: null
                  status: solved
                  subject: null
                  tags: null
                  type: null
                  user_type: null
                table: tickets
              tool: zendesk_update_item
    """

    validate_database(x)
