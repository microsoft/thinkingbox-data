# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# /// script
# dependencies = [
#   "pyarrow>=18.0.0",
#   "PyYAML>=6.0.2",
# ]
# ///

"""Generate Hugging Face Dataset Viewer tables for ThinkingBox-Bench v1.0."""

from __future__ import annotations

import argparse
import ast
import json
import shutil
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

RELEASE_TAG = "thinkingbox-bench-v1.0"
REPOSITORY_URL = "https://github.com/microsoft/thinkingbox-data"
EXPECTED_ROW_COUNTS = {"tasks": 507, "scenarios": 5, "agents": 1}
ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "releases" / "thinkingbox_bench_v1"
TEST_LIST = RELEASE_DIR / "testlist_thinkingbox_bench_v1.yaml"
BUNDLE_DIR = RELEASE_DIR / "huggingface"
DATA_DIR = BUNDLE_DIR / "data"
LICENSE_SOURCE = ROOT / "LICENSE.txt"
LICENSE_DESTINATION = BUNDLE_DIR / "LICENSE.txt"
DATASET_CARD = BUNDLE_DIR / "README.md"
EXPECTED_BUNDLE_FILES = {
    Path("LICENSE.txt"),
    Path("README.md"),
    Path("data/agents.parquet"),
    Path("data/scenarios.parquet"),
    Path("data/tasks.parquet"),
}
EXPECTED_CONFIGS = [
    {
        "config_name": "tasks",
        "default": True,
        "data_files": [{"split": "test", "path": "data/tasks.parquet"}],
    },
    {
        "config_name": "scenarios",
        "data_files": [{"split": "test", "path": "data/scenarios.parquet"}],
    },
    {
        "config_name": "agents",
        "data_files": [{"split": "test", "path": "data/agents.parquet"}],
    },
]

DOMAIN_BY_SCENARIO = {
    "sandbox_external_retail": "retail_and_ecommerce",
    "external_booking_v1": "travel_and_hospitality",
    "sandbox_auto_insurance": "auto_insurance",
    "sandbox_neobank_support_v1": "neobank_support",
    "sandbox_consulting": "consulting_it_and_hr",
}

TASK_SCHEMA = pa.schema(
    [
        ("task_ref", pa.string()),
        ("domain", pa.string()),
        ("scenario_id", pa.string()),
        ("query", pa.string()),
        ("user_context", pa.string()),
        ("initial_state_patch_json", pa.string()),
        ("expected_tool_interactions_json", pa.string()),
        ("rubrics_json", pa.string()),
        ("source_url", pa.string()),
        ("release_tag", pa.string()),
    ]
)
SCENARIO_SCHEMA = pa.schema(
    [
        ("scenario_id", pa.string()),
        ("domain", pa.string()),
        ("world_state_json", pa.string()),
        ("available_tools", pa.list_(pa.string())),
        ("source_url", pa.string()),
        ("release_tag", pa.string()),
    ]
)
AGENT_SCHEMA = pa.schema(
    [
        ("agent_id", pa.string()),
        ("system_instructions", pa.string()),
        ("parallel_tool_calls", pa.bool_()),
        ("builtin_tools_json", pa.string()),
        ("source_url", pa.string()),
        ("release_tag", pa.string()),
    ]
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that committed exports and license match the current sources.",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def source_url(path: Path) -> str:
    relative_path = path.relative_to(ROOT).as_posix()
    return f"{REPOSITORY_URL}/blob/{RELEASE_TAG}/{relative_path}"


def find_test_files() -> dict[str, Path]:
    files_by_name: dict[str, Path] = {}
    for path in sorted((ROOT / "dataset" / "test_case").rglob("*.py")):
        if path.name in files_by_name:
            raise ValueError(f"Test filename is ambiguous: {path.name}")
        files_by_name[path.name] = path
    return files_by_name


def load_task_document(
    task_ref: str, files_by_name: dict[str, Path]
) -> tuple[dict[str, Any], Path]:
    try:
        filename, function_name = task_ref.split(":", 1)
        path = files_by_name[filename]
    except (KeyError, ValueError) as error:
        raise ValueError(f"Invalid task reference: {task_ref}") from error

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    function = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == function_name
        ),
        None,
    )
    if function is None:
        raise ValueError(f"Function not found for task reference: {task_ref}")

    docstring = ast.get_docstring(function, clean=False)
    if not docstring or not docstring.startswith("!"):
        raise ValueError(f"Task does not contain a YAML docstring: {task_ref}")

    document = yaml.safe_load(docstring[1:])
    if not isinstance(document, dict):
        raise ValueError(f"Task YAML is not a mapping: {task_ref}")
    return document, path


def build_task_row(
    task_ref: str, files_by_name: dict[str, Path]
) -> dict[str, Any]:
    document, path = load_task_document(task_ref, files_by_name)
    initial_state = document.get("init")
    if not isinstance(initial_state, dict) or len(initial_state) != 1:
        raise ValueError(f"Task must initialize exactly one scenario: {task_ref}")

    scenario_id, scenario_state = next(iter(initial_state.items()))
    if scenario_id not in DOMAIN_BY_SCENARIO or not isinstance(scenario_state, dict):
        raise ValueError(f"Unsupported scenario in task: {task_ref}")

    golden_test_case = scenario_state.get("golden_test_case")
    if not isinstance(golden_test_case, dict) or not isinstance(
        golden_test_case.get("tool_interactions"), list
    ):
        raise ValueError(f"Task has no golden tool interactions: {task_ref}")

    return {
        "task_ref": task_ref,
        "domain": DOMAIN_BY_SCENARIO[scenario_id],
        "scenario_id": scenario_id,
        "query": document.get("query", ""),
        "user_context": document.get("user_context", ""),
        "initial_state_patch_json": to_json(scenario_state.get("data_patch") or {}),
        "expected_tool_interactions_json": to_json(
            golden_test_case["tool_interactions"]
        ),
        "rubrics_json": to_json(
            scenario_state.get("rubrics_yesno")
            or scenario_state.get("rubrics")
            or []
        ),
        "source_url": source_url(path),
        "release_tag": RELEASE_TAG,
    }


def build_tasks() -> pa.Table:
    task_refs = load_yaml(TEST_LIST)
    if (
        not isinstance(task_refs, list)
        or len(task_refs) != EXPECTED_ROW_COUNTS["tasks"]
        or len(set(task_refs)) != EXPECTED_ROW_COUNTS["tasks"]
    ):
        raise ValueError(
            f"Expected {EXPECTED_ROW_COUNTS['tasks']} unique canonical task references"
        )

    files_by_name = find_test_files()
    rows = [build_task_row(task_ref, files_by_name) for task_ref in task_refs]
    return pa.Table.from_pylist(rows, schema=TASK_SCHEMA)


def build_scenarios() -> pa.Table:
    rows = []
    for scenario_id, domain in DOMAIN_BY_SCENARIO.items():
        path = ROOT / "dataset" / "scenario" / f"{scenario_id}.yaml"
        document = load_yaml(path)
        world_state = document.get("world_state")
        tools = document.get("tools")
        if not isinstance(world_state, dict) or not isinstance(tools, list):
            raise ValueError(f"Invalid scenario document: {path}")

        tool_names = [tool.get("name") for tool in tools]
        if not all(isinstance(name, str) for name in tool_names):
            raise ValueError(f"Scenario contains an unnamed tool: {path}")

        rows.append(
            {
                "scenario_id": scenario_id,
                "domain": domain,
                "world_state_json": to_json(world_state),
                "available_tools": tool_names,
                "source_url": source_url(path),
                "release_tag": RELEASE_TAG,
            }
        )

    return pa.Table.from_pylist(rows, schema=SCENARIO_SCHEMA)


def build_agents() -> pa.Table:
    path = ROOT / "dataset" / "agent" / "think.yaml"
    document = load_yaml(path)
    row = {
        "agent_id": "think",
        "system_instructions": document.get("system_instructions", ""),
        "parallel_tool_calls": document.get("parallel_tool_calls", False),
        "builtin_tools_json": to_json(document.get("builtin_tools") or []),
        "source_url": source_url(path),
        "release_tag": RELEASE_TAG,
    }
    return pa.Table.from_pylist([row], schema=AGENT_SCHEMA)


def build_tables() -> dict[str, pa.Table]:
    tables = {
        "tasks": build_tasks(),
        "scenarios": build_scenarios(),
        "agents": build_agents(),
    }
    for name, expected_count in EXPECTED_ROW_COUNTS.items():
        actual_count = tables[name].num_rows
        if actual_count != expected_count:
            raise ValueError(
                f"Expected {expected_count} exported {name}, found {actual_count}"
            )

    scenario_rows = {
        row["scenario_id"]: row["domain"] for row in tables["scenarios"].to_pylist()
    }
    for task in tables["tasks"].to_pylist():
        if scenario_rows.get(task["scenario_id"]) != task["domain"]:
            raise ValueError(
                f"Task {task['task_ref']} has an invalid scenario or domain"
            )
    return tables


def load_dataset_card_metadata() -> dict[str, Any]:
    content = DATASET_CARD.read_text(encoding="utf-8")
    sections = content.split("---", 2)
    if len(sections) != 3 or sections[0].strip():
        raise ValueError("Dataset card must start with YAML front matter")
    metadata = yaml.safe_load(sections[1])
    if not isinstance(metadata, dict):
        raise ValueError("Dataset card metadata must be a mapping")
    return metadata


def check_tables(tables: dict[str, pa.Table]) -> None:
    errors = []
    for name, expected in tables.items():
        path = DATA_DIR / f"{name}.parquet"
        if not path.exists():
            errors.append(f"Missing {path.relative_to(ROOT)}")
            continue
        actual = pq.read_table(path)
        if not actual.equals(expected):
            errors.append(f"Outdated {path.relative_to(ROOT)}")
    if (
        not LICENSE_DESTINATION.exists()
        or LICENSE_DESTINATION.read_bytes() != LICENSE_SOURCE.read_bytes()
    ):
        errors.append(f"Outdated {LICENSE_DESTINATION.relative_to(ROOT)}")
    actual_files = {
        path.relative_to(BUNDLE_DIR)
        for path in BUNDLE_DIR.rglob("*")
        if path.is_file()
    }
    if actual_files != EXPECTED_BUNDLE_FILES:
        errors.append(
            "Unexpected Hugging Face bundle files: "
            f"{sorted(str(path) for path in actual_files ^ EXPECTED_BUNDLE_FILES)}"
        )
    try:
        metadata = load_dataset_card_metadata()
        if metadata.get("configs") != EXPECTED_CONFIGS:
            errors.append("Dataset card configs do not match the exported tables")
    except (OSError, ValueError, yaml.YAMLError) as error:
        errors.append(f"Invalid dataset card: {error}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Verified the Hugging Face publishing bundle ({len(tables)} tables).")


def write_tables(tables: dict[str, pa.Table]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        path = DATA_DIR / f"{name}.parquet"
        pq.write_table(table, path, compression="zstd")
        print(f"Wrote {path.relative_to(ROOT)} ({table.num_rows} rows).")
    shutil.copyfile(LICENSE_SOURCE, LICENSE_DESTINATION)
    print(f"Copied {LICENSE_DESTINATION.relative_to(ROOT)}.")


def main() -> None:
    args = parse_args()
    tables = build_tables()
    if args.check:
        check_tables(tables)
    else:
        write_tables(tables)


if __name__ == "__main__":
    main()
