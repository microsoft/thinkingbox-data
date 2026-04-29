# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Database utilities for hashing, diff calculation, and golden test case application."""

import hashlib
import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

from pydantic import BaseModel

if TYPE_CHECKING:
    from .sandbox_tools_system import InMemoryDatabase

from .sandbox_tools_system import UnstableExtraFields, UnstableField

logger = logging.getLogger(__name__)


class DiffItem(BaseModel):
    """Represents a single difference between result and golden database states."""

    path: str
    type: str
    result: Any | None = None
    golden: Any | None = None


def _convert_datetime_to_str(data: Any) -> Any:
    """
    Recursively convert datetime objects to ISO format strings for JSON serialization.

    Args:
        data: Data structure that may contain datetime objects

    Returns:
        Data structure with datetime objects converted to strings
    """
    if isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: _convert_datetime_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_convert_datetime_to_str(item) for item in data]
    else:
        return data


def _sort_lists_recursively(data: Any) -> Any:
    """
    Recursively sort all lists of primitives (strings, ints) in a data structure.

    This ensures that list order doesn't affect hash comparison for fields like
    procedure_codes, diagnosis_codes, document_ids, etc. where order is semantically
    irrelevant.

    Args:
        data: Data structure that may contain lists

    Returns:
        Data structure with lists of primitives sorted
    """
    if isinstance(data, dict):
        return {key: _sort_lists_recursively(value) for key, value in data.items()}
    elif isinstance(data, list):
        # If it's a list of primitives (str, int, float, bool), sort it
        if data and all(isinstance(item, (str, int, float, bool)) for item in data):
            return sorted(data)
        # Otherwise, recursively process each item (for lists of dicts, etc.)
        return [_sort_lists_recursively(item) for item in data]
    else:
        return data


def get_stable_database_state(
    db: "InMemoryDatabase", exclude_unstable_fields: bool = True
) -> Dict[str, Any]:
    """
    Creates a dictionary representing the database state with optional filtering of unstable fields.

    Args:
        db: The InMemoryDatabase instance
        exclude_unstable_fields: Whether to exclude fields marked with UnstableField

    Returns:
        Dictionary representing the stable database state
    """
    database_state = {}
    for model_cls in db._model_cls_to_stem.keys():
        stem = db._model_cls_to_stem[model_cls]
        raw_items = []

        # Get unstable fields for this model class if needed
        unstable_fields = (
            UnstableField.extract_names(model_cls) if exclude_unstable_fields else []
        )

        # Get all items for this model class
        items = db.get_all(model_cls)
        for item in items:
            try:
                raw_dict = item.model_dump(mode="json")
            except AttributeError:
                raw_dict = item.dict()

            # Remove per-field unstable fields
            for field in unstable_fields:
                if field in raw_dict:
                    del raw_dict[field]

            # Remove extra fields if model has unstable_extra_fields marker
            if exclude_unstable_fields:
                extra_fields = UnstableExtraFields.get_extra_field_names(
                    model_cls, raw_dict
                )
                for field in extra_fields:
                    del raw_dict[field]

            # Sort lists of primitives to ensure order doesn't affect hash
            raw_dict = _sort_lists_recursively(raw_dict)

            raw_items.append(raw_dict)

        # Sort items by their 'id' field to ensure deterministic ordering
        # This prevents hash differences caused by items being added in different orders
        raw_items.sort(key=lambda x: str(x.get("id", "")))

        database_state[stem] = raw_items

    # Convert any datetime objects to strings before returning
    return _convert_datetime_to_str(database_state)


def calculate_database_hash(
    db: "InMemoryDatabase", exclude_unstable_fields: bool = True
) -> str:
    """
    Calculate a SHA-256 hash of the database state.

    Args:
        db: The InMemoryDatabase instance
        exclude_unstable_fields: Whether to exclude fields marked with UnstableField from the hash

    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    stable_state = get_stable_database_state(db, exclude_unstable_fields)
    json_str = json.dumps(stable_state, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def calculate_deep_diff(
    obj1: Any, obj2: Any, path: str = "root"
) -> List[Dict[str, Any]]:
    """
    Calculate deep diff between two objects.
    Returns list of diff items.

    Args:
        obj1: First object (usually result)
        obj2: Second object (usually golden)
        path: Current path in the object tree

    Returns:
        List of diff items describing differences
    """
    differences: List[Dict[str, Any]] = []

    # Handle None cases
    if obj1 is None and obj2 is None:
        return differences
    if obj1 is None:
        differences.append(
            {
                "path": path,
                "type": "result is None, golden is not",
                "result": obj1,
                "golden": type(obj2).__name__,
            }
        )
        return differences
    if obj2 is None:
        differences.append(
            {
                "path": path,
                "type": "result is not None, golden is None",
                "result": type(obj1).__name__,
                "golden": obj2,
            }
        )
        return differences

    # Handle type mismatch
    if type(obj1) is not type(obj2):
        differences.append(
            {
                "path": path,
                "type": "type mismatch",
                "result": type(obj1).__name__,
                "golden": type(obj2).__name__,
            }
        )
        return differences

    # Handle dictionaries
    if isinstance(obj1, dict):
        all_keys = set(obj1.keys()) | set(obj2.keys())

        for key in sorted(all_keys):
            key_path = f"{path}.{key}" if path != "root" else key

            if key not in obj1:
                differences.append(
                    {"path": key_path, "type": "missing in result (present in golden)"}
                )
            elif key not in obj2:
                differences.append(
                    {"path": key_path, "type": "present in result (missing in golden)"}
                )
            else:
                differences.extend(calculate_deep_diff(obj1[key], obj2[key], key_path))

    # Handle lists
    elif isinstance(obj1, list):
        if len(obj1) != len(obj2):
            differences.append(
                {
                    "path": path,
                    "type": "length mismatch",
                    "result": len(obj1),
                    "golden": len(obj2),
                }
            )

        max_len = max(len(obj1), len(obj2))
        for i in range(max_len):
            item_path = f"{path}[{i}]"

            if i >= len(obj1):
                differences.append(
                    {"path": item_path, "type": "missing in result (present in golden)"}
                )
            elif i >= len(obj2):
                differences.append(
                    {"path": item_path, "type": "present in result (missing in golden)"}
                )
            else:
                differences.extend(calculate_deep_diff(obj1[i], obj2[i], item_path))

    # Handle primitive types
    else:
        if obj1 != obj2:
            differences.append(
                {"path": path, "type": "value mismatch", "result": obj1, "golden": obj2}
            )

    return differences


async def apply_golden_set_to_database(
    system, test_case: Dict[str, Any]
) -> "InMemoryDatabase":
    """
    Apply golden test case to a fresh database copy.

    Args:
        system: SandboxToolsSystem instance
        test_case: Golden test case with tool_interactions

    Returns:
        Updated InMemoryDatabase instance
    """
    tool_interactions = test_case.get("tool_interactions", [])

    logger.info(
        f"Applying {len(tool_interactions)} tool interactions from golden test case"
    )

    for interaction in tool_interactions:
        tool_name = interaction.get("tool")
        parameters = interaction.get("parameters", {})

        if not tool_name:
            continue

        try:
            await system.call_tool(tool_name, parameters)
        except Exception as e:
            logger.error(f"Error running tool {tool_name}: {e}")

    return system.db
