# ThinkingBox-Bench v1.0

## Repository

Use the following `thinkingbox-data` tag for a stable version of the benchmark,
tool servers, and supporting data:

| | |
| - | - |
| Tag | [`thinkingbox-bench-v1.0`](https://github.com/microsoft/thinkingbox-data/tree/thinkingbox-bench-v1.0) |

ThinkingBox-Bench is an executable benchmark for evaluating whether tool-using
LLM agents can reliably complete stateful business workflows. Version 1.0
contains 507 tool-agent-user tasks across five domains.

Each task provides an initial backend state, a user goal and simulated-user
context, domain tools, policy constraints, and executable checks. An attempt
passes only when all required checks over the final state, side effects, and
designated dialogue properties pass.

## Release contents

| Domain | Canonical definitions | Tasks |
| - | - | -: |
| Retail and e-commerce | `sandbox_external_retail_group1.py` | 98 |
| Travel and hospitality | `external_booking_v1_group1.py` (89) and `external_booking_v1_group1_rubrics_yesno.py` (15) | 104 |
| Auto insurance | `sandbox_auto_insurance_group1.py` | 100 |
| Neobank support | `sandbox_neobank_support_v1_group1.py` (89) and `sandbox_neobank_support_v1_group1_rubrics_yesno.py` (15) | 104 |
| Consulting IT/HR support | `sandbox_consulting_group1.py` | 101 |
| **Total** | | **507** |

The canonical task set is
[`testlist_thinkingbox_bench_v1.yaml`](testlist_thinkingbox_bench_v1.yaml).
The test list, rather than every test definition under `dataset/test_case/`,
defines the release. It selects rubric-enhanced alternatives for 15 travel
tasks and 15 neobank tasks in place of their corresponding base definitions,
so these alternatives do not increase the task count.

Other datasets and tests in this repository are not part of ThinkingBox-Bench
v1.0.

## Evaluation method

Each task compares the final backend state with its golden expected state using
deterministic, hash-based checks. Thirty tasks additionally use simple yes/no
rubrics evaluated by an LLM judge. A task passes only when its final state is
correct and every applicable rubric returns the expected result; there is no
partial credit.

## Intended use

ThinkingBox-Bench v1.0 is intended exclusively for evaluation. Do not use its
task content, expected outcomes, golden state, or tool trajectories for prompt
optimization, fine-tuning, reinforcement learning, reward-model training, or
other model optimization.

## Run the benchmark

The commands below assume `thinkingbox/` and `thinkingbox-data/` are cloned
side-by-side and are run from the `thinkingbox/` directory.

Install the benchmark's server package in the ThinkingBox environment:

```bash
uv pip install --config-settings editable-mode=compat \
    -e ../thinkingbox-data/servers/tb_business_ops_servers_202606
```

Install the additional service prerequisites described in
[`tools_with_additional_setup.md`](https://github.com/microsoft/thinkingbox/blob/main/docs/tools_with_additional_setup.md).
ThinkingBox-Bench requires Typesense.

In one terminal, start the required background services:

```bash
export THINKINGBOX_DATA="../thinkingbox-data"
export TB_MCP_START_SERVERS_FILE="../thinkingbox-data/servers/servers.yaml"
./scripts/background_tasks.sh
```

In another terminal, run all 507 tasks:

```bash
uv run tb infer -c config/config_o4mini.yaml \
    --dataset ../thinkingbox-data/dataset --agent think \
    --test-list ../thinkingbox-data/releases/thinkingbox_bench_v1/testlist_thinkingbox_bench_v1.yaml \
    --repeat 5 --batch-size 40 \
    --output output_thinkingbox_bench_v1.jsonl
```

Aggregate pass rates:

```bash
uv run tb agg output_thinkingbox_bench_v1.jsonl
```

For a reproducible published result, record the exact `thinkingbox-data` commit
and the ThinkingBox configuration, model deployment, inference parameters,
user-simulator model, and judge model used for the run.
