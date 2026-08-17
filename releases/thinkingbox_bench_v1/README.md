# ThinkingBox-Bench v1.0

## Repository

Use the following `thinkingbox-data` tag for a stable version of the benchmark,
tool servers, and supporting data:

| | |
| - | - |
| Tag | [`thinkingbox-bench-v1.0`](https://github.com/microsoft/thinkingbox-data/releases/tag/thinkingbox-bench-v1.0) |

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

ThinkingBox-Bench requires:

- Python 3.12 and [`uv`](https://docs.astral.sh/uv/)
- a Linux or WSL environment
- ThinkingBox and `thinkingbox-data` cloned side-by-side
- Typesense 30.1, installed by the ThinkingBox installation script

On Ubuntu or WSL Ubuntu, install the required system tools:

```bash
sudo apt-get update
sudo apt-get install -y git curl tar coreutils procps
```

Install `uv` if it is not already available:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
```

It does **not** require the embeddings server, downloaded Hugging Face models,
or pre-indexed Typesense snapshots. Each benchmark scenario initializes its
own Typesense collections from the sources in its scenario definition.

Clone and install ThinkingBox:

```bash
git clone https://github.com/microsoft/thinkingbox.git
git clone https://github.com/microsoft/thinkingbox-data.git

cd thinkingbox-data
git checkout thinkingbox-bench-v1.0
cd ../thinkingbox

uv venv --python 3.12
uv sync --group dev
source .venv/bin/activate
```

Install the benchmark's MCP server package into the same environment:

```bash
uv pip install --config-settings editable-mode=compat \
    -e ../thinkingbox-data/servers/tb_business_ops_servers_202606
```

Install Typesense into the active ThinkingBox virtual environment:

```bash
./scripts/install_typesense.sh
typesense-server --version
```

Configure an LLM endpoint in `config/config_o4mini.yaml` or another ThinkingBox
configuration file. See the
[ThinkingBox LLM configuration guide](https://github.com/microsoft/thinkingbox/blob/main/docs/llm_endpoint_config.md)
for the supported providers and fields.

From `thinkingbox/`, start Typesense and the MCP Session Proxy in one terminal:

```bash
export THINKINGBOX_DATA="../thinkingbox-data"
export TB_MCP_START_SERVERS_FILE="../thinkingbox-data/servers/servers.yaml"
./scripts/background_tasks.sh
```

Wait for the script to print `All processes are running`. It uses the
`TYPESENSE_API_KEY=Fake` default expected by the benchmark server
configuration. Keep this terminal running.

In another terminal, enter `thinkingbox/`, activate the same environment, and
run all 507 tasks:

```bash
source .venv/bin/activate

uv run tb infer -c config/config_o4mini.yaml \
    --dataset ../thinkingbox-data/dataset --agent think \
    --test-list ../thinkingbox-data/releases/thinkingbox_bench_v1/testlist_thinkingbox_bench_v1.yaml \
    --repeat 20 --batch-size 20 \
    --output output_thinkingbox_bench_v1.jsonl
```

## Analyze the results

The `tb infer` command writes one JSON object per trial to
`output_thinkingbox_bench_v1.jsonl`. Use `tb agg` to compute the aggregate
metrics:

```bash
uv run tb agg output_thinkingbox_bench_v1.jsonl
```

For a JSONL containing 20 attempts for every task, the aggregate output includes
pass@1, pass@20, and pass^20. pass@20 measures whether at least one of 20
attempts succeeds; pass^20 estimates whether all 20 attempts succeed. These
metrics are omitted if tasks have unequal attempt counts.

Press Ctrl+C in the background-services terminal to stop Typesense and the MCP
Session Proxy.

For a reproducible published result, record the exact `thinkingbox` and
`thinkingbox-data` commits, ThinkingBox configuration, model deployment,
inference parameters, user-simulator model, and judge model used for the run.
