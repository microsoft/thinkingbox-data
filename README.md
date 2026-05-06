# thinkingbox-data

Curated datasets, MCP tool server packages, and supporting data files for use
with [ThinkingBox](https://github.com/microsoft/thinkingbox). See the
framework's [README](https://github.com/microsoft/thinkingbox#readme) for
installation, configuration, and the `tb` CLI overview.

## Contents

- **`dataset/`** — scenarios, agents, and test cases.
- **`servers/`** — MCP tool server packages (`thinkingbox_tools`,
  `ms_toloka_servers`, `ms_telus_servers`) and the master `servers.yaml`
  consumed by `tb mcp-start`.
- **`support/`** — large data files used by some tools (embeddings, knowledge
  bases). Set `THINKINGBOX_DATA=<path-to-this-repo>` so tools can locate them.
- **`releases/`** — per-release dataset snapshots pinned to git tags.

## Layout

The commands below assume both repos are cloned side-by-side and you are in
their **parent directory**:

```
parent/
├── thinkingbox/        # framework (CLI, Session Proxy, agent loop)
└── thinkingbox-data/   # this repo (datasets, server packages, support files)
```

## Setup

Install the framework first (see the [thinkingbox
README](https://github.com/microsoft/thinkingbox#readme)). Then, in the same
virtualenv, install the server packages from this repo:

```bash
uv pip install --config-settings editable-mode=compat -e thinkingbox-data/servers/thinkingbox_tools
uv pip install --config-settings editable-mode=compat -e thinkingbox-data/servers/ms_toloka_servers
uv pip install --config-settings editable-mode=compat -e thinkingbox-data/servers/ms_telus_servers
```

Some tools also need extra services (e.g. Typesense, embeddings server) — see
[`tools_with_additional_setup.md`](https://github.com/microsoft/thinkingbox/blob/main/docs/tools_with_additional_setup.md)
in the framework repo.

## Run

Start the Session Proxy with `THINKINGBOX_DATA` pointing at this repo:

```bash
THINKINGBOX_DATA="thinkingbox-data" \
    tb mcp-start --servers thinkingbox-data/servers/servers.yaml
```

Run a single test:

```bash
tb infer -c thinkingbox/config/config_o4mini.yaml \
    --dataset thinkingbox-data/dataset --agent think \
    --name sandbox_external_retail_group1.py:test_case_ST002_001 \
    --repeat 1 --batch-size 1 --dump testcontext --output output.yaml
tb pp output.yaml
```

Run a full directory, 10 repetitions each:

```bash
tb infer -c thinkingbox/config/config_o4mini.yaml \
    --dataset thinkingbox-data/dataset --agent think \
    --inputs thinkingbox-data/dataset/test_case/sandbox_external_retail \
    --repeat 10 --batch-size 40 \
    --output output_sandbox_external_retail_10reps.jsonl
```

## Third-party code

This repository does not vendor third-party source code. The MCP server packages under `servers/` declare their dependencies in their respective `pyproject.toml` files and install them from public package indexes (PyPI). Each dependency retains its own license.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft trademarks or logos is subject to and must follow [Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general). Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship. Any use of third-party trademarks or logos are subject to those third-party's policies.
