# Airline Tau-Bench 26-04

## Repository

Use the following tag of `thinkingbox-data` to use a stable version of this dataset and tools.

|  |  |
| - | - |
| Tag | [`ds-airline-tau-bench-2026-04-v1.0`](https://github.com/microsoft/thinkingbox-data/releases/tag/ds-airline-tau-bench-2026-04-v1.0) |


## Overview

**Dataset name**: Airline Tau-Bench 26-04

**Test cases**: 21

System: Tau-Bench airline environment

Domain: Travel & Hospitality

Business function: Customer Support & Service

Agent name: Airline Customer Service Agent

The agent operates as a customer service representative for a fictitious airline. It handles customer inquiries about flight bookings, cancellations, reservation changes (flights, passengers, baggage, cabin class), travel insurance, certificate and gift card payments, delay compensation, and transfers to human agents when a request is outside policy.

## Intended use

This dataset is designed **exclusively for evaluation** of LLM agent capabilities. It is a Microsoft-adapted version of the publicly available tau-bench airline environment, with test assertions rewritten to check the final database state and agent behavior against reference solutions.

**This dataset MUST NOT be used for:**
- Prompt tuning or prompt optimization
- Fine-tuning or training language models
- Reinforcement learning or reward model training
- Any form of optimization that uses test case content, expected outcomes, or golden tool interactions as a training signal

Using this dataset for training or tuning would compromise its value as an independent evaluation benchmark.

## What the dataset covers

The 21 test cases cover the end-to-end airline customer-service workflow, including:

| Category | What it tests |
|---|---|
| **Booking** | One-way economy booking with certificates and credit card, booking the same flights for a friend |
| **Reservation changes** | Changing return flights, downgrading cabin class, upgrading to business within budget, changing to nonstop, pushing back dates |
| **Baggage & passengers** | Adding checked bags, changing passenger details, removing passengers, baggage refunds |
| **Cancellations & refunds** | Cancelling basic economy (refusal cases), partial refunds, insurance-based refunds, certificate re-issuance |
| **Payment handling** | Certificate + gift card balance calculation, correct credit-card fallback when certificates/gift cards are exhausted |
| **Policy & refusal** | Refusing out-of-policy changes (basic economy modifications, budget-exceeding changes, persistent refund demands) |
| **Compensation** | Delayed-flight compensation via travel vouchers |

Each test case carries:
- A customer query
- A user-persona context used by the simulated user
- An assertion block that verifies the database state and/or tool-call trace against the reference solution

### Evaluation method

Each test case is evaluated by inspecting the final airline database state (reservations, users, payment methods) and the agent's tool-call trace after the agent's execution. Some test cases also use a LLM-judge rubric for natural-language checks (e.g. did the agent's response look like a refusal).

Tests pass if all assertions pass. There is no partial credit.

## Scenario

All test cases refer to scenario `dataset/scenario/airline_tau_bench_full.yaml`, which provides the agent with:
- System instructions (airline policy)
- 16 tools (flight search, booking, reservation updates, certificate issuance, transfer-to-human, think, calculate, etc.)
- Initial world state loaded from `support/tau_bench/airline_data/{flights,reservations,users}.json`

## Test cases

The dataset consists of 21 test cases in `dataset/test_case/airline_tau_bench.py`, listed in `testlist_2604_airline_tau_bench.yaml` in this directory.

Some interaction with the user is expected in most test cases, to retrieve missing information or to consent to a modification. A prompt for a simulated user, including the required additional context, is provided for each test case.

## Running

Check `thinkingbox/README.md` for installing ThinkingBox.
The commands below assume `thinkingbox/` and `thinkingbox-data/` are cloned
side-by-side and are run from the `thinkingbox/` directory.

```bash
# Install the airline tau-bench server in the ThinkingBox virtual environment
uv pip install --config-settings editable-mode=compat \
    -e ../thinkingbox-data/servers/thinkingbox_tools

# Start session proxy
THINKINGBOX_DATA=../thinkingbox-data \
    tb mcp-start --servers ../thinkingbox-data/servers/servers.yaml

# Decode (full dataset, 5 repetitions)
tb infer -c config.yaml -d ../thinkingbox-data/dataset -a think \
    --test-list ../thinkingbox-data/releases/dataset_2604_airline_tau_bench/testlist_2604_airline_tau_bench.yaml \
    --repeat 5 --batch-size 40 -o output_2604_airline_tau_bench.jsonl
```
