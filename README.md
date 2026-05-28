# thinkingbox-data

Curated datasets, MCP tool server packages, and supporting data files for use
with [ThinkingBox](https://github.com/microsoft/thinkingbox). See the
framework's [README](https://github.com/microsoft/thinkingbox#readme) for
installation, configuration, and the `tb` CLI overview.

## Contents

- **`dataset/`** — scenarios, agents, and test cases.
- **`servers/`** — MCP tool server packages (`thinkingbox_tools`,
  `sandbox_servers`) and the master `servers.yaml` consumed by
  `tb mcp-start`.
- **`support/`** — large data files used by some tools (embeddings, knowledge
  bases). Set `THINKINGBOX_DATA=<path-to-this-repo>` so tools can locate them.
- **`releases/`** — per-release dataset snapshots pinned to git tags.

## Layout

The commands below assume both repos are cloned side-by-side and you are
running them from the **`thinkingbox/`** directory, so that `uv run` picks up
the framework's project and `../thinkingbox-data` resolves to this repo:

```
parent/
├── thinkingbox/        # framework (CLI, Session Proxy, agent loop) ← cwd
└── thinkingbox-data/   # this repo (datasets, server packages, support files)
```

## Setup

Install the framework first (see the [thinkingbox
README](https://github.com/microsoft/thinkingbox#readme)). Then, still from
`thinkingbox/`, install the server packages from this repo into the same env:

```bash
uv pip install --config-settings editable-mode=compat -e ../thinkingbox-data/servers/thinkingbox_tools
uv pip install --config-settings editable-mode=compat -e ../thinkingbox-data/servers/sandbox_servers
```

Some tools also need extra services (e.g. Typesense, embeddings server) — see
[`tools_with_additional_setup.md`](https://github.com/microsoft/thinkingbox/blob/main/docs/tools_with_additional_setup.md)
in the framework repo.

## Verify your setup

Before running larger scenarios, sanity-check that the framework, the
`thinkingbox_tools` server package, and your LLM config are wired up
correctly. The four test cases below need only the in-process MCP servers
bundled here — no Typesense, no embeddings, no `support/` data files.

In one terminal (from `thinkingbox/`), start the Session Proxy:

```bash
THINKINGBOX_DATA="../thinkingbox-data" \
    uv run tb mcp-start --servers ../thinkingbox-data/servers/servers.yaml
```

In another terminal (also from `thinkingbox/`), try running a single test
case — output is a single YAML file:

```bash
# Banking: agent looks up an account balance
uv run tb infer -c config/config_o4mini.yaml \
    --dataset ../thinkingbox-data/dataset --agent think \
    --name banking.py:test_get_balance_savings \
    --output output.yaml

# MCS defaults: agent answers a store-info question
uv run tb infer -c config/config_o4mini.yaml \
    --dataset ../thinkingbox-data/dataset --agent think \
    --name mcs_defaults.py:test_mcs_defaults_easy \
    --output output.yaml
```

Pretty-print the conversation and verify the assertions passed:

```bash
uv run tb pp output.yaml
```

Or run a whole test file with multiple repetitions — output is a JSONL with
one row per (test, repetition):

```bash
# Banking + email: full file (1 test) × 5 repetitions
uv run tb infer -c config/config_o4mini.yaml \
    --dataset ../thinkingbox-data/dataset --agent think \
    --inputs ../thinkingbox-data/dataset/test_case/banking_email.py \
    --repeat 5 --batch-size 5 --output output.jsonl

# Email org: full file (3 tests) × 5 repetitions
uv run tb infer -c config/config_o4mini.yaml \
    --dataset ../thinkingbox-data/dataset --agent think \
    --inputs ../thinkingbox-data/dataset/test_case/email_system_org.py \
    --repeat 5 --batch-size 5 --output output.jsonl
```

Aggregate the JSONL into a summary table (pass-rate per test, etc.):

```bash
uv run tb agg output.jsonl
```

If `tb pp` shows a successful conversation or `tb agg` reports passing
assertions, the framework, server packages, and LLM endpoint are all wired
up.

## Run larger scenarios

To run dataset_2602_external_retail and dataset_2603_sandbox_rl_zendesk, 
you need to also start typesense server. 

All commands below assume you are in the `thinkingbox/` directory.

```
export THINKINGBOX_DATA="../thinkingbox-data/dataset"
export TB_MCP_START_SERVERS_FILE=../thinkingbox-data/servers/servers.yaml
./scripts/background_tasks.sh
```

```bash
uv run tb infer -c config/config_o4mini.yaml \
    --dataset ../thinkingbox-data/dataset --agent think \
    --test-list ../thinkingbox-data/releases/dataset_2602_external_retail/testlist_2602_external_retail_full100.yaml \
    --repeat 10 --batch-size 40 \
    --output output_sandbox_external_retail_10reps.jsonl
```

### Re-run assertions on a saved test context

After decoding once, re-run just the test assertions (no LLM calls):

```bash
# write to a new file
uv run tb run-test -c config/config_o4mini.yaml \
    --dataset ../thinkingbox-data/dataset \
    --resultfile output.yaml \
    --name banking.py:test_transfer_and_balance \
    --output test_result.yaml

# OR update output.yaml in place
uv run tb run-test -c config/config_o4mini.yaml \
    --dataset ../thinkingbox-data/dataset \
    --resultfile output.yaml --update
```

### Interactive TUI

Chat with a scenario:

```bash
uv run tb tui -c config/config_o4mini.yaml \
    --dataset ../thinkingbox-data/dataset --agent think \
    --scenario retail_banking --query "What's my checking account balance?"
```

Chat with a specific test case (loads the test's `user_context` so the
simulated user can answer follow-ups):

```bash
uv run tb tui -c config/config_o4mini.yaml \
    --dataset ../thinkingbox-data/dataset --agent think \
    --name banking.py:test_transfer_and_balance --query ""
```

For interactive-mode hotkeys (ESC+ENTER to submit) and slash commands, see
[Interactive TUI](https://github.com/microsoft/thinkingbox#interactive-tui)
in the framework README.

## Third-party code

This repository does not vendor third-party source code. The MCP server packages under `servers/` declare their dependencies in their respective `pyproject.toml` files and install them from public package indexes (PyPI). Each dependency retains its own license.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft trademarks or logos is subject to and must follow [Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general). Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship. Any use of third-party trademarks or logos are subject to those third-party's policies.
