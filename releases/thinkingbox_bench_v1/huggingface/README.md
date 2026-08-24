---
pretty_name: ThinkingBox-Bench
license: cdla-permissive-2.0
language:
  - en
task_categories:
  - reinforcement-learning
tags:
  - agent
  - tool-use
  - benchmark
  - evaluation
configs:
  - config_name: tasks
    default: true
    data_files:
      - split: test
        path: data/tasks.parquet
  - config_name: scenarios
    data_files:
      - split: test
        path: data/scenarios.parquet
  - config_name: agents
    data_files:
      - split: test
        path: data/agents.parquet
---

# ThinkingBox-Bench

ThinkingBox-Bench is an executable benchmark for evaluating whether tool-using
LLM agents can reliably complete stateful business workflows. Version 1.0
contains 507 tool-agent-user tasks across retail and e-commerce, travel and
hospitality, auto insurance, neobank support, and consulting IT/HR support.

This dataset repository provides a browsable representation of the benchmark.
The executable benchmark, tool servers, and supporting fixtures are maintained
in the
[`microsoft/thinkingbox-data`](https://github.com/microsoft/thinkingbox-data)
GitHub repository.

## Dataset structure

| Subset | Rows | Contents |
| - | -: | - |
| `tasks` | 507 | User goal, initial-state patch, expected tool interactions, and rubrics |
| `scenarios` | 5 | Shared world state and available tools, linked by `scenario_id` |
| `agents` | 1 | Agent instructions and built-in tools |

Select a subset using the Dataset Viewer dropdown. Each task references its
shared scenario through `scenario_id`. Nested task state and expected
interactions are serialized as JSON strings so they remain readable and
portable in the Viewer.

### Task fields

| Field | Description |
| - | - |
| `task_ref` | Canonical `file.py:function_name` identifier from the release test list |
| `domain` | Human-readable benchmark domain |
| `scenario_id` | Key linking the task to its shared row in the `scenarios` subset |
| `query` | Initial request sent by the simulated user |
| `user_context` | Instructions and facts available to the simulated user |
| `initial_state_patch_json` | JSON object applied to the scenario's base world state before the task starts |
| `expected_tool_interactions_json` | Ordered golden tool calls that define the expected state changes |
| `rubrics_json` | Additional response requirements evaluated for applicable tasks |
| `source_url` | Tagged GitHub source containing the executable test definition |
| `release_tag` | Immutable `thinkingbox-data` release used to generate the row |

The dataset does not store a precomputed expected end state. During evaluation,
the scenario's MCP server creates a fresh database, applies
`initial_state_patch_json`, and replays `expected_tool_interactions_json` to
materialize the `golden_db_state`. It then compares the stable hash of that
state with the hash of the database modified by the evaluated agent. This
runtime process ensures the expected state uses the same tool implementation
and database semantics as the agent's attempt.

## Intended use

ThinkingBox-Bench v1.0 is intended exclusively for evaluation. Do not use its
task content, expected outcomes, golden state, or tool trajectories for prompt
optimization, fine-tuning, reinforcement learning, reward-model training, or
other model optimization.

## Run the benchmark

The Parquet tables are for browsing and analysis; they are not the executable
runtime. Follow the
[ThinkingBox-Bench v1.0 instructions](https://github.com/microsoft/thinkingbox-data/blob/thinkingbox-bench-v1.0/releases/thinkingbox_bench_v1/README.md#run-the-benchmark)
to install ThinkingBox, start the required services, and run all 507 tasks.

For reproducibility, use the
[`thinkingbox-bench-v1.0`](https://github.com/microsoft/thinkingbox-data/releases/tag/thinkingbox-bench-v1.0)
release.

## License

The dataset is licensed under the Community Data License Agreement -
Permissive - Version 2.0 (`CDLA-Permissive-2.0`). See `LICENSE.txt`.
