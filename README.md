# thinkingbox-data

This repo contains datasets to use with thinkingbox.

## Clone this branch

```bash
git clone https://github.com/microsoft/thinkingbox-data.git
# OR using GitHub CLI
gh repo clone microsoft/thinkingbox-data
```

## Install servers

Create a virtualenv for ThinkingBox (follow instructions in the thinkingbox README) and activate it

Also install typesense (instructions in `thinkingbox/docs/tools_with_additional_setup.md`)

Install server packages in this repo

```bash
# For thinkingbox_tools Servers
uv pip install --config-settings editable-mode=compat -e servers/thinkingbox_tools
# For Toloka Sandbox Servers
uv pip install --config-settings editable-mode=compat -e servers/ms_toloka_servers
# For Telus Scenario Servers
uv pip install --config-settings editable-mode=compat -e servers/ms_telus_servers
```

## Start Session Proxy

Start the MCP Session Proxy with environment variable THINKINGBOX_DATA pointing to the root of this repo.

```bash
THINKINGBOX_DATA="thinkingbox-data" tb mcp-start --servers thinkingbox-data/servers/servers.yaml
```

Start typesense

```bash
mkdir -p /tmp/typesense/data && typesense-server --data-dir="/tmp/typesense/data" --api-key="Fake" --enable-cors
```

Run a test

```bash
# Run one
tb infer -c config.yaml --dataset thinkingbox-data/dataset --agent think --name sandbox_external_retail_group1.py:test_case_ST002_001 --repeat 1 --batch-size 1 --dump testcontext --output output.yaml

# Check output
tb pp output.yaml
```

Run all sandbox_external_retail, 10 repetitions

```bash
tb infer -c config.yaml --dataset thinkingbox-data/dataset --agent think --inputs thinkingbox-data/dataset/test_case/sandbox_external_retail --repeat 10 --batch-size 40 --output output_sandbox_external_retail_10reps.jsonl
```

## Third-party code

This repository does not vendor third-party source code. The MCP server packages under `servers/` declare their dependencies in their respective `pyproject.toml` files and install them from public package indexes (PyPI). Each dependency retains its own license.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft trademarks or logos is subject to and must follow [Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general). Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship. Any use of third-party trademarks or logos are subject to those third-party's policies.
