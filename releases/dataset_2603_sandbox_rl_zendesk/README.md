# Sandbox RL Zendesk 26-03

## Repository

Use the following tag of `thinkingbox-data` to use a stable version of this dataset and tools.

|  |  |
| - | - |
| Tag | [ds-sandbox-rl-zendesk-2026-03-v1.0](https://github.com/microsoft/thinkingbox-data/releases/tag/ds-sandbox-rl-zendesk-2026-03-v1.0) |


## Overview

**Dataset name**: Sandbox RL Zendesk 26-03

**Test cases**: 516

**Agents**: 5

| Agent | System | Domain | Business function |
| - | - | - | - |
| a01 | Zendesk | Retail & E-commerce | Customer Support & Service |
| a02r | Zendesk | Travel & Hospitality | Customer Support & Service |
| a03 | Zendesk | Insurance | Customer Support & Service |
| a04r | Zendesk | Banking & Finance | IT & Technical Support |
| a05 | Zendesk | Consulting Services | IT & Technical Support |

### Agent descriptions

**a01**

- Name: B2C Ecommerce Electronics Support Agent (External)
- Num Tests: 100
- Description: Handles consumer inquiries about orders, deliveries, returns, and warranty

**a02r**

- Name: Hotel Booking Support & Reservation Management Agent (External)
- Num Tests: 104
- Description: Assists guests with reservations, modifications, cancellations, and billing

**a03**

- Name: Car Insurance Policy & Claims Service Agent (External)
- Num Tests: 101
- Description: Supports policy changes, FNOL intake, claim status inquiries, and documentation

**a04r**

- Name: Internal Neobank IT Support Desk (IT Service Agent)
- Num Tests: 104
- Description: Handles internal employee how-to requests, access and end-user hardware providing, and system issues

**a05**

- Name: Internal Consulting Helpdesk Agent (IT, HR, Expense Support)
- Num Tests: 107
- Description: Supports consultants with equipment issues, system access, travel/expense inquiries


## Intended use

This dataset is designed **exclusively for evaluation** of LLM agent capabilities. It provides an unbiased benchmark for measuring how well agents handle realistic, multi-step customer service workflows with tool use.

**This dataset MUST NOT be used for:**
- Prompt tuning or prompt optimization
- Fine-tuning or training language models
- Reinforcement learning or reward model training
- Any form of optimization that uses test case content, expected outcomes, or golden tool interactions as a training signal

Using this dataset for training or tuning would compromise its value as an independent evaluation benchmark. The dataset is intended to represent an unbiased assessment of agent performance; any model optimized against it would produce inflated scores that do not reflect genuine capability improvements.

### Evaluation method

Each test case is evaluated by comparing the final database state after the agent's execution against a golden expected state. This is a deterministic, hash-based comparison: the agent either produced exactly the correct set of side effects or it did not.

In addition, 30 out of 516 test cases have simple rubrics evaluated by a LLM judge, in the form of yes/no questions.

Tests pass if the final state is correct and all rubrics evaluate to the expected result. There is no partial credit.

## Evaluation results

All results are pass@k over 20 repetitions.

Agent:
- Temperature: 1.0
- No seed
- Reasoning effort (reasoning models only): medium

User simulator and Judge: GPT-5 Chat

### ds-sandbox-rl-zendesk-2026-03-v1.0

| Model | Orchestrator | pass@1 | pass@5 |
|---|---|---|---|
| GPT o4-mini reasoning medium | ThinkingBox | 0.09 | 0.28 |
| t11_24_25_varset_3_rm (o4-mini FT) reasoning medium | ThinkingBox | 0.37 | 0.71 |
| GPT 5-mini reasoning medium | ThinkingBox | 0.19 | 0.41 |
| GPT 5.2 reasoning medium | ThinkingBox | 0.46 | 0.71 |
| GPT 5.4 reasoning medium | ThinkingBox | 0.64 | 0.83 |
| Claude Sonnet 4.6 reasoning medium | ThinkingBox | 0.57 | 0.78 |
| Claude Opus 4.6 reasoning medium | ThinkingBox | 0.38 | 0.57 |

### Notes

Results on `t11_24_25_varset_3_rm` refer to a run on the PPE CAPI deployment of the fine-tuned model.

## Running

Check `thinkingbox/README.md` for installing ThinkingBox

```bash
# Install the Sandbox RL servers in the ThinkingBox virtual environment
uv pip install --config-settings editable-mode=compat -e servers/tb_business_ops_servers_202606

# Start typesense (default port, key: Fake)
mkdir -p /tmp/typesense/data && typesense-server --data-dir="/tmp/typesense/data" --api-key="Fake" --enable-cors

# Start session proxy
THINKINGBOX_DATA=thinkingbox-data tb mcp-start --servers thinkingbox-data/servers/servers.yaml

# Decode (full dataset, 5 repetitions)
tb infer -c config.yaml -d thinkingbox-data/dataset -a think \
    --test-list thinkingbox-data/releases/dataset_2603_sandbox_rl_zendesk/testlist_2603_sandbox_rl_zendesk.yaml \
    --repeat 5 --batch-size 40 -o output_2603_sandbox_rl_zendesk.jsonl
```
