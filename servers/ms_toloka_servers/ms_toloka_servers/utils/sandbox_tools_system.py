# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""SandboxToolsSystem - standalone system for managing tools and database.

This module provides a self-contained system that:
1. Manages an in-memory database with models from toolsets
2. Discovers and registers tools from toolset modules
3. Provides list_tools() and call_tool() interfaces
4. Handles data patches and golden test cases

Similar to airline_tau_bench_system.py, this is a business-logic engine
that integrates with mcp_core for tool and database management.
"""

from __future__ import annotations

import importlib
import inspect
import json
import logging
import os
import pkgutil
import time
import uuid
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from fastmcp.server.tasks.config import TaskConfig
from fastmcp.tools.function_tool import FunctionTool
from pydantic import BaseModel, ValidationError

# Try to import TypesenseIndex, make it optional
from .typesense_helpers import TypesenseIndex

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Stub domain used when domain-scoped features are not needed.
# Using this explicitly indicates the caller does not require:
# - Typesense search
# - Other domain-scoped service lookups
#
# Usage:
#   from ms_toloka_servers.utils.sandbox_tools_system import STUB_DOMAIN
#   db = InMemoryDatabase(domain=STUB_DOMAIN)
STUB_DOMAIN = "__stub__"


# ═══════════════════════════════════════════════════════════════════════════
# Typesense Index
# ═══════════════════════════════════════════════════════════════════════════

_g_typesense: TypesenseIndex | None = None


def initialize_typesense(sources: List[Dict[str, Any]]) -> None:
    """Initialize the global Typesense index with sources.

    Args:
        collection_name: Name of the Typesense collection
        sources: List of source documents with 'name' and 'snippets' fields

    Raises:
        Exception: If Typesense initialization fails
    """
    global _g_typesense

    if TypesenseIndex is None:
        logger.warning(
            "TypesenseIndex not available, skipping Typesense initialization"
        )
        return

    collection_name = str(uuid.uuid4())
    logger.info(f"Initializing Typesense with collection: {collection_name}")

    _g_typesense = TypesenseIndex(
        collection_name=collection_name,
        read_only=False,
        delete_on_exit=True,
    )

    for source in sources:
        logger.info(f"Adding source: {source.get('name')}")
        _g_typesense.add_source(source)

    logger.info(f"Successfully initialized Typesense with {len(sources)} sources")


def get_typesense() -> TypesenseIndex | None:
    """Get the global Typesense index instance.

    Returns:
        TypesenseIndex instance or None if not initialized
    """
    return _g_typesense


# ═══════════════════════════════════════════════════════════════════════════
# Error Classes
# ═══════════════════════════════════════════════════════════════════════════


class SandboxToolsSystemError(Exception):
    """Base exception for SandboxToolsSystem errors."""

    pass


# ═══════════════════════════════════════════════════════════════════════════
# Schema Utilities
# ═══════════════════════════════════════════════════════════════════════════


class UnstableField:
    """Marker to label a field as an unstable field that should be excluded from hash calculations."""

    def __repr__(self):
        return "UnstableField()"

    @classmethod
    def extract_names(cls, model_cls: Type[BaseModel]) -> List[str]:
        """
        Returns a list of field names that are marked as unstable in a Pydantic model.

        Args:
            model_cls: The Pydantic model class to analyze

        Returns:
            List of field names that are marked with UnstableField
        """
        if not hasattr(model_cls, "model_fields"):
            return []

        return [
            name
            for name, f in model_cls.model_fields.items()
            if any(isinstance(m, cls) for m in getattr(f, "metadata", ()))
        ]


class UnstableExtraFields:
    """Marker class variable to indicate that extra (non-schema) fields on this model
    should be treated as unstable and excluded from hash calculations.

    Usage on a model:
        class MyModel(BaseModel):
            model_config = ConfigDict(extra="allow")
            unstable_extra_fields: ClassVar[bool] = True

            name: str = Field(...)  # stable, included in hash
            # Any extra field set at runtime is excluded from hash
    """

    @classmethod
    def has_unstable_extras(cls, model_cls: type) -> bool:
        """Check if a model class has unstable extra fields marking."""
        return getattr(model_cls, "unstable_extra_fields", False) is True

    @classmethod
    def get_extra_field_names(cls, model_cls: type, instance_dict: dict) -> list[str]:
        """Get names of extra fields (not in model schema) from an instance dict."""
        if not cls.has_unstable_extras(model_cls):
            return []
        schema_fields = (
            set(model_cls.model_fields.keys())
            if hasattr(model_cls, "model_fields")
            else set()
        )
        return [k for k in instance_dict if k not in schema_fields]


def get_schema_without_refs(model_class: Type[BaseModel]) -> Dict[str, Any]:
    """Get JSON schema without $ref references.

    Generates the Pydantic JSON schema then:
    1. Preserves field-level ``examples`` metadata.
    2. Recursively inlines all ``$ref`` references so the returned dict
       is fully self-contained (no ``$defs`` section).
    3. Converts any remaining Pydantic objects to plain dicts.
    """
    schema = model_class.model_json_schema(mode="serialization")
    schema = _preserve_field_examples(schema, model_class)
    schema = _inline_refs(schema, schema.get("$defs", {}))
    if "$defs" in schema:
        del schema["$defs"]
    schema = _serialize_pydantic_objects(schema)
    return schema


def _preserve_field_examples(
    schema: Dict[str, Any], model_class: Type[BaseModel]
) -> Dict[str, Any]:
    """Copy ``examples`` from ``model_fields`` into the JSON schema."""
    if "properties" not in schema:
        return schema
    for field_name, field_info in model_class.model_fields.items():
        if field_name in schema["properties"]:
            if hasattr(field_info, "examples") and field_info.examples is not None:
                examples = []
                for example in field_info.examples:
                    if hasattr(example, "model_dump"):
                        examples.append(example.model_dump(mode="json"))
                    else:
                        examples.append(example)
                schema["properties"][field_name]["examples"] = examples
    return schema


def _inline_refs(obj: Any, defs: Dict[str, Any]) -> Any:
    """Recursively replace ``$ref`` pointers with the referenced definition."""
    if isinstance(obj, dict):
        if "$ref" in obj:
            ref_path = obj["$ref"]
            if ref_path.startswith("#/$defs/"):
                def_name = ref_path.split("/")[-1]
                if def_name in defs:
                    inlined_def = _inline_refs(defs[def_name], defs)
                    result = (
                        inlined_def.copy()
                        if isinstance(inlined_def, dict)
                        else inlined_def
                    )
                    if isinstance(result, dict):
                        for key, value in obj.items():
                            if key != "$ref":
                                if key not in result or key in [
                                    "examples",
                                    "title",
                                    "description",
                                ]:
                                    result[key] = value
                    return result
            return obj
        result = {}
        for key, value in obj.items():
            if key != "$defs":
                result[key] = _inline_refs(value, defs)
        return result
    elif isinstance(obj, list):
        return [_inline_refs(item, defs) for item in obj]
    else:
        return obj


def _serialize_pydantic_objects(obj: Any) -> Any:
    """Convert any lingering Pydantic objects to plain dicts."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    elif isinstance(obj, dict):
        return {key: _serialize_pydantic_objects(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_pydantic_objects(item) for item in obj]
    else:
        return obj


# ═══════════════════════════════════════════════════════════════════════════
# Tool Base Class
# ═══════════════════════════════════════════════════════════════════════════


class Tool(ABC):
    """Base class for all tools."""

    class ExecutionError(Exception):
        """Exception raised when tool execution fails."""

        def __init__(self, message: str, details: Optional[List[str]] = None):
            if details:
                message += f": {'; '.join(details)}"
            super().__init__(message)

        @staticmethod
        def from_error(message: str, error: Exception) -> "Tool.ExecutionError":
            return Tool.ExecutionError(message, [str(error)])

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (without namespace prefix)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass

    @property
    def input_schema(self) -> Dict[str, Any]:
        """JSON schema for input validation."""
        return get_schema_without_refs(self.request_model)

    @property
    def output_schema(self) -> Dict[str, Any]:
        """JSON schema for output format."""
        return get_schema_without_refs(self.output_model)

    @property
    @abstractmethod
    def request_model(self) -> Type[BaseModel]:
        """Input schema as Pydantic model."""
        pass

    @property
    @abstractmethod
    def output_model(self) -> Type[BaseModel]:
        """Output schema as Pydantic model."""
        pass

    @abstractmethod
    async def run(self, db: "InMemoryDatabase", request: BaseModel) -> BaseModel:
        """Execute the tool and return a result."""
        pass

    def _validate_input(
        self, arguments: Dict[str, Any]
    ) -> Tuple[Optional[BaseModel], Optional[ExecutionError]]:
        """Validate input arguments against request_model."""
        try:
            validated_request = self.request_model.model_validate(arguments)
            return validated_request, None
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field = (
                    ".".join(str(loc) for loc in error["loc"])
                    if error["loc"]
                    else "unknown"
                )
                message = error["msg"]
                error_details.append(f"{field}: {message}")
            return None, self.ExecutionError("Input validation failed", error_details)

    async def run_with_validation(
        self, db: "InMemoryDatabase", arguments: Dict[str, Any] | BaseModel
    ) -> Dict[str, Any]:
        """Run tool with input/output validation."""
        if isinstance(arguments, self.request_model):
            validated_request = arguments
        elif isinstance(arguments, BaseModel):
            raise ValueError(
                f"Arguments must be a dictionary or a '{self.request_model.__name__}' object"
            )
        else:
            validated_request, input_error = self._validate_input(arguments)
            if input_error is not None:
                raise input_error

        result_model = await self.run(db, validated_request)

        # Return JSON-serializable dict (mode='json' handles datetime serialization)
        try:
            return result_model.model_dump(mode="json", exclude_none=True)
        except AttributeError:
            return result_model.dict(exclude_none=True)


# ═══════════════════════════════════════════════════════════════════════════
# In-Memory Database
# ═══════════════════════════════════════════════════════════════════════════


class InMemoryDatabase:
    """
    Generic in-memory database seeded from JSON files on init.
    Supports additional_sources for namespace-based tool sets.
    """

    def __init__(
        self,
        domain: str = STUB_DOMAIN,
        data_dir: Optional[str] = None,
        additional_sources: Optional[Dict[str, Tuple[str, str]]] = None,
        domain_version: Optional[str] = None,
    ):
        """
        Initialize the database.

        Args:
            domain: Domain identifier for this database instance. Defaults to
                    STUB_DOMAIN when domain-scoped features are not needed.
            data_dir: Optional primary data directory (for src.db.* models).
                     If not provided, only additional_sources will be loaded.
            additional_sources: Dict mapping namespace -> (data_dir, module_prefix)
                Example: {"excel": ("/path/to/excel/data", "thinkingbox.tools.toolslib.sandbox.excel.models")}
            domain_version: Version of the domain configuration
        """
        self.data_dir = data_dir or ""
        self.created_at_epoch_seconds: float = time.time()
        self._additional_sources = additional_sources or {}
        self.domain = domain
        self.domain_version = domain_version

        self._stem_to_model_cls: Dict[str, Type[BaseModel]] = {}
        self._model_cls_to_stem: Dict[Type[BaseModel], str] = {}
        self._store: Dict[Type[BaseModel], List[BaseModel]] = {}

        # Only discover and load from data_dir if it's provided
        if data_dir:
            self._discover_models()
            self._load_and_validate_all()

        # Discover and load models from additional sources (namespaces)
        for namespace, (ns_data_dir, module_prefix) in self._additional_sources.items():
            self._discover_namespace_models(namespace, ns_data_dir, module_prefix)

    @classmethod
    def from_state_dict(
        cls,
        state_dict: Dict[str, Any],
        domain: str = STUB_DOMAIN,
        domain_version: Optional[str] = None,
    ) -> "InMemoryDatabase":
        """Create a new InMemoryDatabase instance from a state dictionary."""
        db = cls.__new__(cls)
        db.data_dir = ""
        db.created_at_epoch_seconds = time.time()
        db.domain = domain
        db.domain_version = domain_version
        db._additional_sources = {}
        db._stem_to_model_cls = {}
        db._model_cls_to_stem = {}
        db._store = {}
        db._discover_models_from_stems(list(state_dict.keys()))
        for stem, raw_items in state_dict.items():
            if stem in db._stem_to_model_cls:
                model_cls = db._stem_to_model_cls[stem]
                validated_items = [
                    db._validate_dict(model_cls, item) for item in raw_items
                ]
                db._store[model_cls] = validated_items
            else:
                logger.warning(f"No model class found for stem '{stem}', skipping data")
        return db

    def validate(self, model_cls: Type[T]) -> Tuple[int, int]:
        """Validate all items of a model class."""
        raw_items = [self._to_raw(item) for item in self._store.get(model_cls, [])]
        validated = [self._validate_dict(model_cls, obj) for obj in raw_items]
        self._store[model_cls] = validated
        return (len(validated), len(raw_items))

    def get_all(self, model_cls: Type[T]) -> List[T]:
        """Get all items of a specific model type from the database."""
        items = self._store.get(model_cls, [])
        return list(items)

    def get_by_id(self, model_cls: Type[T], value: Any) -> Optional[T]:
        """Get a single item by its ID from the database."""
        items = self._store.get(model_cls, [])
        for item in items:
            if hasattr(item, "get_id") and item.get_id() == value:
                return item
        return None

    def create(self, obj: object) -> T:
        """Create a new object in the database."""
        if not hasattr(obj, "__class__"):
            raise ValueError("Object must have a class")

        model_cls = obj.__class__
        if not issubclass(model_cls, BaseModel):
            raise ValueError("Object must be a Pydantic BaseModel")

        if model_cls not in self._model_cls_to_stem:
            raise ValueError("Attempted to create object for an unknown model class")

        if isinstance(obj, BaseModel):
            validated = self._revalidate_instance(model_cls, obj)
        elif isinstance(obj, dict):
            validated = self._validate_dict(model_cls, obj)
        else:
            raise ValueError("Object must be a Pydantic model or dict")

        if hasattr(validated, "get_id"):
            existing = self.get_by_id(model_cls, validated.get_id())
            if existing is not None:
                raise ValueError(f"Object with ID {validated.get_id()} already exists")

        existing_items = self._store.get(model_cls, [])
        new_items = list(existing_items) + [validated]
        self._store[model_cls] = new_items

        return validated

    def bulk_create(self, objects: List[object]) -> List[T]:
        """Create multiple objects in the database."""
        if not objects:
            return []

        first_obj = objects[0]
        if not hasattr(first_obj, "__class__"):
            raise ValueError("Objects must have a class")

        model_cls = first_obj.__class__
        if not issubclass(model_cls, BaseModel):
            raise ValueError("Objects must be Pydantic BaseModels")

        if model_cls not in self._model_cls_to_stem:
            raise ValueError("Attempted to create objects for an unknown model class")

        validated_objects = []
        new_ids = set()

        for obj in objects:
            if obj.__class__ != model_cls:
                raise ValueError("All objects must be of the same model class")

            if isinstance(obj, BaseModel):
                validated = self._revalidate_instance(model_cls, obj)
            elif isinstance(obj, dict):
                validated = self._validate_dict(model_cls, obj)
            else:
                raise ValueError("Objects must be Pydantic models or dicts")

            if hasattr(validated, "get_id"):
                obj_id = validated.get_id()
                if obj_id in new_ids:
                    raise ValueError(f"Duplicate ID {obj_id} in bulk create batch")
                new_ids.add(obj_id)

                existing = self.get_by_id(model_cls, obj_id)
                if existing is not None:
                    raise ValueError(f"Object with ID {obj_id} already exists")

            validated_objects.append(validated)

        existing_items = self._store.get(model_cls, [])
        new_items = list(existing_items) + validated_objects
        self._store[model_cls] = new_items

        return validated_objects

    def update(self, obj: object) -> T:
        """Update an existing object in the database."""
        if not hasattr(obj, "__class__"):
            raise ValueError("Object must have a class")

        model_cls = obj.__class__
        if not issubclass(model_cls, BaseModel):
            raise ValueError("Object must be a Pydantic BaseModel")

        if model_cls not in self._model_cls_to_stem:
            raise ValueError("Attempted to update object for an unknown model class")

        if isinstance(obj, BaseModel):
            validated = self._revalidate_instance(model_cls, obj)
        elif isinstance(obj, dict):
            validated = self._validate_dict(model_cls, obj)
        else:
            raise ValueError("Object must be a Pydantic model or dict")

        if not hasattr(validated, "get_id"):
            raise ValueError("Object must have a get_id() method for updates")

        obj_id = validated.get_id()
        existing_items = self._store.get(model_cls, [])

        updated_items = []
        found = False

        for item in existing_items:
            if hasattr(item, "get_id") and item.get_id() == obj_id:
                updated_items.append(validated)
                found = True
            else:
                updated_items.append(item)

        if not found:
            raise ValueError(f"Object with ID {obj_id} does not exist")

        self._store[model_cls] = updated_items

        return validated

    def delete(self, obj: object) -> None:
        """Delete an existing object from the database."""
        if not hasattr(obj, "__class__"):
            raise ValueError("Object must have a class")

        model_cls = obj.__class__
        if not issubclass(model_cls, BaseModel):
            raise ValueError("Object must be a Pydantic BaseModel")

        if model_cls not in self._model_cls_to_stem:
            raise ValueError("Attempted to delete object for an unknown model class")

        if not hasattr(obj, "get_id"):
            raise ValueError("Object must have a get_id() method for deletion")

        obj_id = obj.get_id()
        existing_items = self._store.get(model_cls, [])

        updated_items = []
        found = False

        for item in existing_items:
            if hasattr(item, "get_id") and item.get_id() == obj_id:
                found = True
            else:
                updated_items.append(item)

        if not found:
            raise ValueError(f"Object with ID {obj_id} does not exist")

        self._store[model_cls] = updated_items

    def delete_by_id(self, model_cls: Type[T], obj_id: Any) -> None:
        """Delete an existing object from the database by its ID."""
        if model_cls not in self._model_cls_to_stem:
            raise ValueError("Attempted to delete object for an unknown model class")

        existing_items = self._store.get(model_cls, [])

        updated_items = []
        found = False

        for item in existing_items:
            if hasattr(item, "get_id") and item.get_id() == obj_id:
                found = True
            else:
                updated_items.append(item)

        if not found:
            raise ValueError(f"Object with ID {obj_id} does not exist")

        self._store[model_cls] = updated_items

    def bulk_delete(self, objects: List[object]) -> None:
        """Delete multiple objects from the database."""
        if not objects:
            return

        first_obj = objects[0]
        if not hasattr(first_obj, "__class__"):
            raise ValueError("Objects must have a class")

        model_cls = first_obj.__class__
        if not issubclass(model_cls, BaseModel):
            raise ValueError("Objects must be Pydantic BaseModels")

        if model_cls not in self._model_cls_to_stem:
            raise ValueError("Attempted to delete objects for an unknown model class")

        ids_to_delete = set()
        for obj in objects:
            if obj.__class__ != model_cls:
                raise ValueError("All objects must be of the same model class")

            if not hasattr(obj, "get_id"):
                raise ValueError("Objects must have a get_id() method for deletion")

            ids_to_delete.add(obj.get_id())

        existing_items = self._store.get(model_cls, [])

        updated_items = [
            item
            for item in existing_items
            if not (hasattr(item, "get_id") and item.get_id() in ids_to_delete)
        ]

        deleted_count = len(existing_items) - len(updated_items)
        if deleted_count != len(ids_to_delete):
            raise ValueError("Some objects to delete were not found in the database")

        self._store[model_cls] = updated_items

    def to_state_dict(self) -> Dict[str, Any]:
        """Get database state as a dictionary."""
        database_state = {}

        for model_cls in self._model_cls_to_stem.keys():
            stem = self._model_cls_to_stem[model_cls]
            items = self.get_all(model_cls)

            raw_items = []
            for item in items:
                try:
                    raw_dict = item.model_dump(mode="json")
                except AttributeError:
                    raw_dict = item.dict()
                raw_items.append(raw_dict)

            database_state[stem] = raw_items

        return database_state

    def copy(self) -> "InMemoryDatabase":
        """Create a deep copy of the database."""
        new_obj = self.__class__.__new__(self.__class__)
        new_obj.data_dir = self.data_dir
        new_obj.domain = self.domain
        new_obj.domain_version = self.domain_version
        new_obj.created_at_epoch_seconds = time.time()
        new_obj._additional_sources = deepcopy(self._additional_sources)
        new_obj._stem_to_model_cls = deepcopy(self._stem_to_model_cls)
        new_obj._model_cls_to_stem = deepcopy(self._model_cls_to_stem)
        new_obj._store = deepcopy(self._store)
        return new_obj

    def _discover_models(self) -> None:
        """Discover models from primary data directory."""
        if not os.path.exists(self.data_dir):
            return

        for filename in os.listdir(self.data_dir):
            if not filename.endswith(".json"):
                continue
            stem = filename[:-5]
            module_name = f"src.db.{stem}"
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError:
                continue

            model_cls = self._resolve_primary_model_class(stem, module)
            if model_cls is None:
                continue

            self._stem_to_model_cls[stem] = model_cls
            self._model_cls_to_stem[model_cls] = stem

    def _discover_models_from_stems(self, stems: List[str]) -> None:
        """Discover model classes based on provided stem names."""
        for stem in stems:
            module_name = f"src.db.{stem}"
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError:
                logger.warning(f"No module found for stem '{stem}' at {module_name}")
                continue

            model_cls = self._resolve_primary_model_class(stem, module)
            if model_cls is None:
                logger.warning(f"No valid model class found in module {module_name}")
                continue

            self._stem_to_model_cls[stem] = model_cls
            self._model_cls_to_stem[model_cls] = stem

    def _discover_namespace_models(
        self, namespace: str, data_dir: str, module_prefix: str
    ) -> None:
        """Discover and load models from a namespace."""
        if not os.path.exists(data_dir):
            logger.debug(
                f"Namespace '{namespace}' data directory does not exist: {data_dir}"
            )
            return

        try:
            models_module = importlib.import_module(module_prefix)
        except ModuleNotFoundError:
            logger.warning(
                f"Cannot import models module '{module_prefix}' for namespace '{namespace}'"
            )
            return

        for filename in os.listdir(data_dir):
            if not filename.endswith(".json"):
                continue

            base_stem = filename[:-5]
            prefixed_stem = f"{namespace}_{base_stem}" if namespace else base_stem

            model_cls = self._resolve_primary_model_class(base_stem, models_module)
            if model_cls is None:
                logger.warning(
                    f"No model class found for '{base_stem}' in '{module_prefix}'"
                )
                continue

            self._stem_to_model_cls[prefixed_stem] = model_cls
            self._model_cls_to_stem[model_cls] = prefixed_stem

            json_path = os.path.join(data_dir, filename)
            raw_list = self._safe_read_json_array(json_path)
            validated_list = [self._validate_dict(model_cls, obj) for obj in raw_list]

            if model_cls in self._store:
                self._store[model_cls].extend(validated_list)
            else:
                self._store[model_cls] = validated_list

    def _load_and_validate_all(self) -> None:
        """Load and validate all data from primary data directory."""
        for stem, model_cls in self._stem_to_model_cls.items():
            json_path = os.path.join(self.data_dir, f"{stem}.json")
            raw_list = self._safe_read_json_array(json_path)
            validated_list = [self._validate_dict(model_cls, obj) for obj in raw_list]
            self._store[model_cls] = validated_list

    def _safe_read_json_array(self, path: str) -> List[Dict[str, Any]]:
        """Safely read JSON array from file."""
        try:
            with open(path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except FileNotFoundError:
            return []

    def _pluralize_to_singular(self, plural: str) -> str:
        """Convert plural form to singular using English grammar rules.

        Handles various pluralization patterns:
        - Regular plurals: items -> item
        - -ies endings: entries -> entry
        - -es endings after s/x/z/ch/sh: boxes -> box, classes -> class
        - -ves endings: shelves -> shelf
        - Irregular double consonants: Access patterns (accesses -> access)
        """
        # Words ending in -ies (but not -eies like species)
        if plural.endswith("ies") and len(plural) > 3 and plural[-4] not in "aeiou":
            # entries -> entry, policies -> policy
            return plural[:-3] + "y"

        # Words ending in -sses, -xes, -zes (after s, x, z)
        if plural.endswith("sses"):
            # classes -> class, accesses -> access
            return plural[:-2]
        elif plural.endswith("xes") or plural.endswith("zes"):
            # boxes -> box, quizzes -> quiz
            return plural[:-2]

        # Words ending in -ches or -shes
        if plural.endswith("ches") or plural.endswith("shes"):
            # matches -> match, dishes -> dish
            return plural[:-2]

        # Words ending in -ves
        if plural.endswith("ves") and len(plural) > 3:
            # shelves -> shelf, knives -> knife
            return plural[:-3] + "f"

        # Words ending in -oes
        if plural.endswith("oes") and len(plural) > 3:
            # tomatoes -> tomato, heroes -> hero
            return plural[:-2]

        # Standard -s ending
        if plural.endswith("s") and len(plural) > 1:
            # items -> item, records -> record
            return plural[:-1]

        # Already singular or unknown pattern
        return plural

    def _resolve_primary_model_class(
        self, stem: str, module: Any
    ) -> Optional[Type[BaseModel]]:
        """Resolve primary model class from module based on stem.

        Tries multiple strategies:
        1. Try exact case-sensitive match (for CamelCase names like "IssueLink")
        2. Convert plural stem to singular using grammar rules
        3. Try exact match with stem (title case)
        4. Search all models in module with matching table_name attribute
        5. Fall back to first available model
        """
        # Strategy 1: Try exact case-sensitive match (for CamelCase names like "IssueLink")
        exact_case_match = getattr(module, stem, None)
        if (
            isinstance(exact_case_match, type)
            and issubclass(exact_case_match, BaseModel)
            and exact_case_match is not BaseModel
        ):
            return exact_case_match

        # Strategy 2: Try singularized form
        singular = self._pluralize_to_singular(stem)
        preferred_name = singular.title().replace("_", "")
        preferred = getattr(module, preferred_name, None)
        if (
            isinstance(preferred, type)
            and issubclass(preferred, BaseModel)
            and preferred is not BaseModel
        ):
            return preferred

        # Strategy 2: Try exact stem match (in case it's already singular)
        if singular != stem:
            exact_name = stem.title().replace("_", "")
            exact_match = getattr(module, exact_name, None)
            if (
                isinstance(exact_match, type)
                and issubclass(exact_match, BaseModel)
                and exact_match is not BaseModel
            ):
                return exact_match

        # Strategy 3: Search for model with matching table_name attribute
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseModel)
                and attr is not BaseModel
            ):
                # Check if model has table_name attribute matching our stem
                table_name = getattr(attr, "table_name", None)
                if table_name == stem:
                    return attr

        # Strategy 4: Fallback to first available model (legacy behavior)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseModel)
                and attr is not BaseModel
            ):
                return attr

        return None

    def _validate_dict(self, model_cls: Type[T], obj: Dict[str, Any]) -> T:
        """Validate dict against model class."""
        try:
            return model_cls.model_validate(obj)
        except AttributeError:
            return model_cls.parse_obj(obj)

    def _revalidate_instance(self, model_cls: Type[T], instance: T) -> T:
        """Revalidate an existing instance."""
        raw = self._to_raw(instance)
        return self._validate_dict(model_cls, raw)

    def _to_raw(self, instance: BaseModel) -> Dict[str, Any]:
        """Convert instance to raw dict."""
        try:
            return instance.model_dump(mode="json")
        except AttributeError:
            return instance.dict()


# ═══════════════════════════════════════════════════════════════════════════
# ToolSet Configuration
# ═══════════════════════════════════════════════════════════════════════════


class ToolSet:
    """Configuration for a tool set that can be mounted."""

    def __init__(
        self,
        path: str,
        namespace: Optional[str] = None,
        db_namespace: Optional[str] = None,
    ):
        """
        Initialize ToolSet configuration.

        Args:
            path: Python import path to the tool set module
                  (e.g., 'toolslib.sandbox.zendesk')
            namespace: Optional namespace prefix for tools. If provided, all tools
                      will be prefixed with '{namespace}_'. If None, tools are
                      mounted at root without prefix.
            db_namespace: Optional prefix for database table names. If provided,
                         table names will be prefixed with '{db_namespace}_'.
                         If None, uses namespace or generates from module path.
        """
        self.path = path
        self.namespace = namespace
        self.db_namespace = db_namespace

    def __repr__(self) -> str:
        parts = [f"path={self.path!r}"]
        if self.namespace:
            parts.append(f"namespace={self.namespace!r}")
        if self.db_namespace:
            parts.append(f"db_namespace={self.db_namespace!r}")
        return f"ToolSet({', '.join(parts)})"


# ═══════════════════════════════════════════════════════════════════════════
# Main System Class
# ═══════════════════════════════════════════════════════════════════════════


class SandboxToolsSystem:
    """
    Standalone system for managing tools and database.

    This system:
    - Manages an in-memory database with models from toolsets
    - Discovers and registers tools from toolset modules
    - Provides list_tools() and call_tool() interfaces
    - Handles data patches
    """

    def __init__(self, toolsets: List[ToolSet]):
        """
        Initialize the SandboxToolsSystem.

        Args:
            toolsets: List of ToolSet configurations to load
        """
        self.toolsets = toolsets
        self._tool_map: Dict[str, Tool] = {}
        self._tool_namespace_map: Dict[str, str] = {}
        self.db: Optional[InMemoryDatabase] = None

        # Resolve toolset configurations
        self._resolved_toolsets: List[
            Tuple[Optional[str], Optional[str], Dict[str, str]]
        ] = []
        self._resolve_toolsets()

        # Initialize database
        self._initialize_database()

        # Discover and register tools
        self._discover_tools()

    def _resolve_toolsets(self) -> None:
        """Resolve toolset configurations from module paths."""
        for toolset in self.toolsets:
            namespace_display = toolset.namespace if toolset.namespace else "root"
            try:
                module = importlib.import_module(toolset.path)
                if not hasattr(module, "__file__") or module.__file__ is None:
                    raise ValueError(
                        f"Module '{toolset.path}' has no __file__ attribute"
                    )

                module_dir = os.path.dirname(os.path.abspath(module.__file__))

                config = {
                    "tools_path": os.path.join(module_dir, "tools"),
                    "tools_import": f"{toolset.path}.tools",
                    "data_dir": os.path.join(module_dir, "initial_data"),
                    "models_module": f"{toolset.path}.models",
                }

                self._resolved_toolsets.append(
                    (toolset.namespace, toolset.db_namespace, config)
                )

            except ImportError as e:
                raise ValueError(
                    f"Tool set '{namespace_display}': cannot import module '{toolset.path}'. "
                    f"Make sure the module is installed and accessible. Error: {e}"
                )
            except Exception as e:
                raise ValueError(
                    f"Tool set '{namespace_display}': error resolving configuration "
                    f"from '{toolset.path}': {e}"
                )

    def _initialize_database(self) -> None:
        """Initialize the in-memory database with all toolset data."""
        # Prepare additional_sources for database
        additional_sources = {}

        for namespace, db_namespace, config in self._resolved_toolsets:
            # Generate source key for database table names
            # Priority: db_namespace > namespace > generated from module path
            # Note: empty string ("") means "no prefix" - tables registered by plain name
            if db_namespace is not None:
                # db_namespace explicitly set (even "" = no prefix)
                source_key = db_namespace
            elif namespace is not None:
                # namespace explicitly set (even "" = no prefix)
                source_key = namespace
            else:
                # Both None - generate stable key from models module path
                # Remove 'sandbox_external_retail.' prefix to match data_patch format
                models_module = config["models_module"]

                # Remove 'sandbox_external_retail.' prefix if present
                if models_module.startswith("sandbox_external_retail."):
                    relevant_part = models_module[len("sandbox_external_retail.") :]
                    source_key = relevant_part.replace(".", "_")
                # Remove 'sandbox.' prefix if present (fallback for other formats)
                elif models_module.startswith("sandbox."):
                    relevant_part = models_module[len("sandbox.") :]
                    source_key = relevant_part.replace(".", "_")
                else:
                    # Fallback to full path replacement
                    source_key = models_module.replace(".", "_")

            additional_sources[source_key] = (
                config["data_dir"],
                config["models_module"],
            )

        # Create database with no primary data_dir, only additional sources
        self.db = InMemoryDatabase(
            domain=STUB_DOMAIN, data_dir=None, additional_sources=additional_sources
        )

    def _discover_tools(self) -> None:
        """Discover and register tools from all toolsets."""
        for namespace, db_namespace, config in self._resolved_toolsets:
            tools_package_path = config["tools_path"]
            tools_package_import = config["tools_import"]

            # Discover tools from this toolset
            toolset_tools = self._discover_tools_from_package(
                tools_package_path, tools_package_import
            )

            # Determine the effective namespace (empty string for root)
            effective_namespace = namespace if namespace else ""

            # Register tools with or without namespace prefix
            for tool_name, tool_instance in toolset_tools.items():
                # Determine the final name (with or without prefix)
                if effective_namespace:
                    final_name = f"{effective_namespace}_{tool_name}"
                else:
                    final_name = tool_name

                # Check for conflicts
                if final_name in self._tool_map:
                    existing_namespace = self._tool_namespace_map.get(final_name, "")
                    existing_location = (
                        f"namespace '{existing_namespace}'"
                        if existing_namespace
                        else "root"
                    )
                    new_location = (
                        f"namespace '{effective_namespace}'"
                        if effective_namespace
                        else "root"
                    )
                    raise ValueError(
                        f"Tool name conflict: '{final_name}' is already registered in "
                        f"{existing_location}. Cannot register it again in {new_location}. "
                        f"Tool names must be unique across all namespaces and root."
                    )

                # Register the tool
                self._tool_map[final_name] = tool_instance
                self._tool_namespace_map[final_name] = effective_namespace

    def _discover_tools_from_package(
        self, package_dir: str, package_name: str
    ) -> Dict[str, Tool]:
        """Discover tools from a package directory."""
        discovered: Dict[str, Tool] = {}

        if not os.path.exists(package_dir):
            logger.warning(f"Tools directory does not exist: {package_dir}")
            return discovered

        for module_info in pkgutil.iter_modules([package_dir]):
            module_name = module_info.name
            if module_name in {"__init__"}:
                continue

            try:
                module = importlib.import_module(f"{package_name}.{module_name}")
            except Exception as e:
                logger.warning(
                    f"Failed to import tool module {package_name}.{module_name}: {e}"
                )
                continue

            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Tool)
                    and obj != Tool
                    and not inspect.isabstract(obj)
                ):
                    tool_instance = obj()
                    discovered[tool_instance.name] = tool_instance

        return discovered

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools.

        Returns:
            List of tool definitions with name and description
        """
        tools = []
        for tool_name, tool in self._tool_map.items():
            tools.append(
                {
                    "name": tool_name,
                    "description": tool.description,
                    "input_schema": get_schema_without_refs(tool.request_model),
                }
            )
        return tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool by name with given arguments.

        Args:
            name: Tool name (including namespace prefix if applicable)
            arguments: Tool arguments as dictionary

        Returns:
            Tool execution result as dictionary

        Raises:
            SandboxToolsSystemError: If tool not found or execution fails
        """
        if self.db is None:
            raise SandboxToolsSystemError("Database not initialized")

        tool = self._tool_map.get(name)
        if tool is None:
            raise SandboxToolsSystemError(f"Unknown tool: {name}")

        try:
            result = await tool.run_with_validation(self.db, arguments)
            return result
        except Tool.ExecutionError as e:
            raise SandboxToolsSystemError(f"Tool execution failed: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error executing tool {name}")
            raise SandboxToolsSystemError(f"Tool execution failed: {str(e)}")

    def apply_data_patch(self, patch: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Apply a data patch to the database.

        Args:
            patch: Dictionary mapping table names to lists of items

        Raises:
            SandboxToolsSystemError: If validation fails
        """
        if self.db is None:
            raise SandboxToolsSystemError("Database not initialized")

        validation_errors = []
        for table_name, items in patch.items():
            if not isinstance(items, list):
                validation_errors.append(
                    f"Table '{table_name}' must contain a list of items"
                )
                continue

            model_cls = None
            for cls, stem in self.db._model_cls_to_stem.items():
                if stem == table_name:
                    model_cls = cls
                    break

            if model_cls is None:
                validation_errors.append(f"Unknown table '{table_name}'")
                continue

            try:
                if items:
                    for item in items:
                        validated_obj = model_cls.model_validate(item)
                        # Use upsert logic: update if exists, create if not
                        obj_id = validated_obj.get_id()
                        existing = self.db.get_by_id(model_cls, obj_id)
                        if existing is not None:
                            self.db.update(validated_obj)
                        else:
                            self.db.create(validated_obj)
            except (ValueError, Exception) as e:
                validation_errors.append(
                    f"Validation error for table '{table_name}': {str(e)}"
                )

        if validation_errors:
            raise SandboxToolsSystemError(
                f"Data patch validation failed: {'; '.join(validation_errors)}"
            )

    def get_database_state(self) -> Dict[str, Any]:
        """
        Get current database state as dictionary.

        Returns:
            Database state dictionary
        """
        if self.db is None:
            raise SandboxToolsSystemError("Database not initialized")
        return self.db.to_state_dict()


def make_function_tool(fn, name: str, description: str, parameters: dict):
    """Create a FastMCP FunctionTool."""
    return FunctionTool(
        fn=fn,
        name=name,
        description=description,
        parameters=parameters,
        tags=set(),
        task_config=TaskConfig(),
    )
