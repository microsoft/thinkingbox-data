# thinkingbox-data

Curated datasets, MCP tool server packages, and supporting data files for use
with [ThinkingBox](https://github.com/microsoft/thinkingbox). See the
framework's [README](https://github.com/microsoft/thinkingbox#readme) for
installation, configuration, and the `tb` CLI overview.

## ThinkingBox-Bench

[ThinkingBox-Bench](releases/thinkingbox_bench_v1/README.md) is the primary
evaluation release in this repository. Version 1.0 contains 507 executable
tool-agent-user tasks across retail and e-commerce, travel and hospitality,
auto insurance, neobank support, and consulting IT/HR support.

Each task runs in an isolated, stateful tool environment and is evaluated with
executable checks over the final backend state and side effects. Some tasks
also check required properties of the final response.

If your goal is to run the published benchmark, follow the complete
[ThinkingBox-Bench v1.0 installation and run instructions](releases/thinkingbox_bench_v1/README.md#run-the-benchmark)
directly. The remaining setup and examples in this README are intended for
customized ThinkingBox development, individual scenarios, and smoke testing.

| Version | Tasks | Domains | Release |
| - | -: | -: | - |
| ThinkingBox-Bench v1.0 | 507 | 5 | [Documentation and usage](releases/thinkingbox_bench_v1/README.md) |

The rest of this repository also contains individual datasets and development
fixtures that are not part of ThinkingBox-Bench. The benchmark's canonical task
set is defined by the test list linked from its release documentation.

## Contents

- **`dataset/`** — scenarios, agents, and test cases.
- **`servers/`** — MCP tool server packages (`thinkingbox_tools`,
  `tb_business_ops_servers_202606`) and the master `servers.yaml` consumed by
  `tb mcp-start`.
- **`support/`** — large data files used by some tools (embeddings, knowledge
  bases). Set `THINKINGBOX_DATA=<path-to-this-repo>` so tools can locate them.
- **[`releases/`](releases/README.md)** — supported benchmark releases and
  their canonical test lists.

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
README](https://github.com/microsoft/thinkingbox#readme)). For the smoke tests
below, install the `thinkingbox_tools` package into the same environment:

```bash
uv pip install --config-settings editable-mode=compat -e ../thinkingbox-data/servers/thinkingbox_tools
```

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

## Run ThinkingBox-Bench

Use the canonical
[ThinkingBox-Bench v1.0 installation and run instructions](releases/thinkingbox_bench_v1/README.md#run-the-benchmark).

## Re-run assertions on a saved test context

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

## Interactive TUI

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
