# External Retail 26-02

## Repository

Use the following tag of `thinkingbox-data` to use a stable version of this dataset and tools.

|  |  |
| - | - |
| Tag | [ds-external-retail-2026-02-v1.0](https://github.com/microsoft/thinkingbox-data/releases/tag/ds-external-retail-2026-02-v1.0) |


## Overview

**Dataset name**: External Retail 26-02

**Test cases**: 100

System: Zendesk

Domain: Retail & E-commerce

Business function: Customer Support & Service

Agent name: B2C Ecommerce Electronics Support Agent (External)

The agent operates as a customer service representative for **TechHome Direct**, a fictitious online electronics and appliances retailer. It handles consumer inquiries about orders, deliveries, returns, warranty claims, installation services, payment disputes, order modifications, and membership management through a Zendesk-based ticketing system.

## Intended use

This dataset is designed **exclusively for evaluation** of LLM agent capabilities. It provides an unbiased benchmark for measuring how well agents handle realistic, multi-step customer service workflows with tool use.

**This dataset MUST NOT be used for:**
- Prompt tuning or prompt optimization
- Fine-tuning or training language models
- Reinforcement learning or reward model training
- Any form of optimization that uses test case content, expected outcomes, or golden tool interactions as a training signal

Using this dataset for training or tuning would compromise its value as an independent evaluation benchmark. The dataset is intended to represent an unbiased assessment of agent performance; any model optimized against it would produce inflated scores that do not reflect genuine capability improvements.

## What the dataset covers

The 100 test cases simulate realistic B2C customer support interactions across the full lifecycle of an e-commerce customer relationship. Each test case provides a customer query, a simulated user persona with context, a pre-populated database state, and a golden expected outcome (the sequence of tool calls and their parameters that constitute a correct resolution).

### Topic distribution

| Category | Stories | Cases | What it tests |
|---|---|---|---|
| **Returns** | ST006, ST008, ST009, ST010 | 40 | Return eligibility by tier/window/product category, fee calculations (restocking, shipping, removal), RMA creation, returns with installation cancellation, ineligible return handling, pre-delivery return attempts |
| **Defects & Warranty** | ST007, ST012, ST013, ST014 | 14 | Warranty claim filing, routing between return and warranty paths, protection plan vs manufacturer warranty, minor defect partial refunds with score-based compensation |
| **Installation Services** | ST015, ST016, ST017, ST018 | 10 | Customer-requested rescheduling, weather delay rescheduling with compensation, workmanship warranty issues, installation cancellation with shipping cost charge |
| **Order Tracking & Delivery** | ST002, ST003 | 7 | Delayed shipment compensation (score-based), delivery exception handling, ticket reuse for follow-ups |
| **Undelivered Packages** | ST004, ST005 | 9 | Missing package investigation, courtesy replacements (tier/score-based), carrier investigation, returned-to-sender reship with fault determination |
| **Order Modifications** | ST025, ST026, ST028, ST029 | 11 | Order cancellation (with and without installation), shipping address changes within modification window, promo code after purchase |
| **Membership Management** | ST030, ST031 | 5 | Plus membership upgrades and cancellations |
| **Exchanges** | ST011 | 4 | Same-SKU exchanges for defective items, inventory availability checks |

### Complexity dimensions

The test cases vary along several dimensions that affect difficulty:

- **Customer tiers** (Standard, Plus, VIP) determine return windows, fee waivers, shipping speeds, and ticket priority
- **Customer scores** (Regular, Opportunist, Bonus Hunter) determine compensation amounts and fee waivers, and must never be disclosed to the customer
- **Policy lookups**: the agent's system prompt references policies but does not contain specific fee amounts, return windows, or warranty periods. The agent must search the knowledge base at runtime to retrieve these values and apply them correctly.
- **Multi-step workflows**: most cases require multiple tool calls in sequence (e.g., look up customer profile, find or create a Zendesk ticket, retrieve order details, search policies, calculate fees, create an RMA, update ticket status)
- **Ticket management**: the agent must decide whether to create a new ticket, reopen a recently solved one, or reuse an existing open ticket, and must set the correct status, priority, and type based on the customer's tier and issue
- **User interaction**: 35 of the 100 test cases do not include all required information in the initial query. The agent must ask the customer for missing details (email, order ID, preferences) before proceeding. A simulated user with the required context is provided for each test case.
- **Edge cases**: first-time customer courtesy waivers, product category-specific return windows (computing, gaming, and wearables have reduced windows for Standard customers), installed appliance removal fees

### Evaluation method

Each test case is evaluated by comparing the final database state after the agent's execution against a golden expected state. This is a deterministic, hash-based comparison: the agent either produced exactly the correct set of side effects (created the right tickets, RMAs, refunds, etc. with the correct parameters) or it did not. There is no partial credit.

## Scenario

All test cases refer to scenario `dataset/scenario/sandbox_external_retail.yaml`, which provides the agent with:
- System instructions, defining the agent's role
- Knowledge base articles: 10 policy documents searchable at runtime

The agent has access to 33 tools spanning several systems.

## Test cases

The dataset is made of 100 test cases, found in `dataset/test_case/sandbox_external_retail/`.

Some interaction with the user is expected in most test cases, to retrieve missing information that is critical for the completion of the task. A prompt for a simulated user, including the required additional context, is provided for each test case.

Two splits are provided as YAML files in this directory:

| Split | File | Cases | Description |
|---|---|---|---|
| **full100** | `testlist_2602_external_retail_full100.yaml` | 100 | All test cases |
| **quick20** | `testlist_2602_external_retail_quick20.yaml` | 20 | A subset of 20 test cases |

The quick20 split is designed to track the full100 performance, and to be used as proxy for faster iteration.

## Evaluation results

All results are pass@k over 20 repetitions.

Agent:
- Temperature: 1.0
- No seed
- Reasoning effort (reasoning models only): medium

User simulator: GPT-5 Chat

### full100

| Model | Orchestrator | pass@1 | pass@5 |
|---|---|---|---|
| Opus4.6 | ThinkingBox | 0.73 | 0.86 |
| BIC RL FT GPT-5 mini Medium Reasoning | ThinkingBox | 0.70 | 0.89 |
| GPT 5.2 reasoning medium | ThinkingBox | 0.69 | 0.85 |
| Sonnet4.6 | ThinkingBox | 0.68 | 0.84 |
| Opus4.7 | ThinkingBox | 0.61 | 0.76 |
| GPT 5 reasoning medium | ThinkingBox | 0.58 | 0.83 |
| Sonnet4.5 | ThinkingBox | 0.52 | 0.82 |
| GPT 5.2 reasoning medium | MCS | 0.47 | 0.73 |
| GPT-5 mini reasoning medium | ThinkingBox | 0.37 | 0.77 |
| GPT-4.1 | ThinkingBox | 0.16 | 0.42 |
| GPT-5-Chat | ThinkingBox | 0.03 | 0.11 |
| GPT-4.1 | MCS | 0.01 | 0.06 |

### quick20

| Model | Orchestrator | pass@1 | pass@5 |
|---|---|---|---|
| GPT 5.2 reasoning medium | ThinkingBox | 0.69 | 0.86 |
| GPT-4.1 | ThinkingBox | 0.20 | 0.51 |
| GPT-5 mini reasoning medium | ThinkingBox | 0.39 | 0.82 |
| t11_24_25_5mini_rm medium (FT) | ThinkingBox | 0.74 | 0.92 |
| GPT-4.1 | MCS | 0.02 | 0.08 |
| GPT-5.2 reasoning medium | MCS | 0.38 | 0.72 |

### Notes

Results on `t11_24_25_5mini_rm` refer to a run on an internal deployment of the fine-tuned model. There is often a small difference when re-evaluating on the public deployment after publishing, which we cannot quantify at this time.

MCS tests were run with the following parameters:

- GPT-4.1:
    - useModelKnowledge: false
    - model: CurrentModels/GPT41, routed to AOAI GPT4.1, with overrides (temperature=1.0, seed=None)
- GPT-5.2 reasoning
    - useModelKnowledge: false
    - model: ReasoningExperimentalModels/GPT5Reasoning, routed to AOAI GPT-5.2, with overrides (temperature=1.0, reasoning=medium)

## Running

Check `thinkingbox/README.md` for installing ThinkingBox

```bash
# Install the servers in the ThinkingBox virtual environment
uv pip install --config-settings editable-mode=compat -e servers/tb_business_ops_servers_202606

# Start typesense (default port, key: Fake)
mkdir -p /tmp/typesense/data && typesense-server --data-dir="/tmp/typesense/data" --api-key="Fake" --enable-cors

# Start session proxy
THINKINGBOX_DATA=thinkingbox-data tb mcp-start --servers servers.yaml

# Decode (full100, 20 repetitions)
tb infer -c config.yaml -d thinkingbox-data/dataset -a think \
    --inputs thinkingbox-data/dataset/test_case/sandbox_external_retail/ \
    --repeat 20 --batch-size 40 -o output_zendesk_external_retail_full100.jsonl

# Decode (quick20, 5 repetitions)
tb infer -c config.yaml -d thinkingbox-data/dataset -a think \
    --test-list thinkingbox-data/releases/dataset_2602_external_retail/testlist_2602_external_retail_quick20.yaml \
    --repeat 5 --batch-size 40 -o output_zendesk_external_retail_quick20.jsonl
```
