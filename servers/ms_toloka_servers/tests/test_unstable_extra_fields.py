# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for UnstableExtraFields marker and hash exclusion of dynamic fields."""

from typing import ClassVar

import pytest
from ms_toloka_servers.utils.db_utils import (
    calculate_database_hash,
    get_stable_database_state,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    UnstableExtraFields,
)
from pydantic import BaseModel, ConfigDict, Field


class DynamicItem(BaseModel):
    """Test model with extra='allow' and unstable_extra_fields marker."""

    model_config = ConfigDict(extra="allow")
    unstable_extra_fields: ClassVar[bool] = True

    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")

    def get_id(self) -> str:
        return self.id


class StrictItem(BaseModel):
    """Test model without extra fields — no unstable_extra_fields marker."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")

    def get_id(self) -> str:
        return self.id


class TestUnstableExtraFieldsMarker:
    """Tests for the UnstableExtraFields class methods."""

    def test_has_unstable_extras_true(self):
        """Test that has_unstable_extras returns True for marked models."""
        assert UnstableExtraFields.has_unstable_extras(DynamicItem) is True

    def test_has_unstable_extras_false(self):
        """Test that has_unstable_extras returns False for unmarked models."""
        assert UnstableExtraFields.has_unstable_extras(StrictItem) is False

    def test_get_extra_field_names_with_extras(self):
        """Test extraction of extra field names from an instance dict."""
        instance_dict = {
            "id": "1",
            "name": "Test",
            "Status": "Active",
            "Priority": "High",
        }
        extra_names = UnstableExtraFields.get_extra_field_names(
            DynamicItem, instance_dict
        )
        assert sorted(extra_names) == ["Priority", "Status"]

    def test_get_extra_field_names_no_extras(self):
        """Test that no extra names are returned when there are no extra fields."""
        instance_dict = {"id": "1", "name": "Test"}
        extra_names = UnstableExtraFields.get_extra_field_names(
            DynamicItem, instance_dict
        )
        assert extra_names == []

    def test_get_extra_field_names_unmarked_model(self):
        """Test that unmarked models return no extra field names even with extra keys."""
        instance_dict = {"id": "1", "name": "Test", "Bonus": "field"}
        extra_names = UnstableExtraFields.get_extra_field_names(
            StrictItem, instance_dict
        )
        assert extra_names == []


class TestUnstableExtraFieldsHash:
    """Tests for hash and state calculation with UnstableExtraFields."""

    @pytest.fixture
    def db_with_dynamic_items(self):
        """Database with dynamic items containing extra fields."""
        db = InMemoryDatabase()
        items = [
            DynamicItem(id="I1", name="Item 1", Status="Active", Priority="High"),
            DynamicItem(id="I2", name="Item 2", Status="Completed", Priority="Low"),
        ]
        db._model_cls_to_stem[DynamicItem] = "dynamic_items"
        db._store[DynamicItem] = items
        return db

    def test_hash_excluding_extra_fields(self, db_with_dynamic_items):
        """Test that hash is stable when extra fields differ but are excluded."""
        hash1 = calculate_database_hash(
            db_with_dynamic_items, exclude_unstable_fields=True
        )

        # Create a second DB with different extra field values but same schema fields
        db2 = InMemoryDatabase()
        items2 = [
            DynamicItem(id="I1", name="Item 1", Status="Pending", Priority="Medium"),
            DynamicItem(
                id="I2", name="Item 2", Status="Cancelled", Priority="Critical"
            ),
        ]
        db2._model_cls_to_stem[DynamicItem] = "dynamic_items"
        db2._store[DynamicItem] = items2

        hash2 = calculate_database_hash(db2, exclude_unstable_fields=True)
        assert hash1 == hash2, "Hashes should match when extra fields are excluded"

    def test_hash_including_extra_fields(self, db_with_dynamic_items):
        """Test that hash differs when extra fields differ and are included."""
        hash1 = calculate_database_hash(
            db_with_dynamic_items, exclude_unstable_fields=False
        )

        # Create a second DB with different extra field values
        db2 = InMemoryDatabase()
        items2 = [
            DynamicItem(id="I1", name="Item 1", Status="Pending", Priority="Medium"),
            DynamicItem(
                id="I2", name="Item 2", Status="Cancelled", Priority="Critical"
            ),
        ]
        db2._model_cls_to_stem[DynamicItem] = "dynamic_items"
        db2._store[DynamicItem] = items2

        hash2 = calculate_database_hash(db2, exclude_unstable_fields=False)
        assert hash1 != hash2, "Hashes should differ when extra fields are included"

    def test_get_stable_state_excludes_extra_fields(self, db_with_dynamic_items):
        """Test that get_stable_database_state strips extra fields from marked models."""
        state_with = get_stable_database_state(
            db_with_dynamic_items, exclude_unstable_fields=False
        )
        state_without = get_stable_database_state(
            db_with_dynamic_items, exclude_unstable_fields=True
        )

        # Extra fields should be present when not excluding
        assert "Status" in state_with["dynamic_items"][0]
        assert "Priority" in state_with["dynamic_items"][0]

        # Extra fields should be absent when excluding
        assert "Status" not in state_without["dynamic_items"][0]
        assert "Priority" not in state_without["dynamic_items"][0]

        # Schema fields should be present in both
        assert state_with["dynamic_items"][0]["id"] == "I1"
        assert state_without["dynamic_items"][0]["id"] == "I1"
        assert state_with["dynamic_items"][0]["name"] == "Item 1"
        assert state_without["dynamic_items"][0]["name"] == "Item 1"

    def test_get_stable_state_preserves_unstable_field_annotations(self):
        """Test that per-field UnstableField and model-level UnstableExtraFields
        work together correctly."""
        from typing import Annotated

        from ms_toloka_servers.utils.sandbox_tools_system import UnstableField

        class CombinedModel(BaseModel):
            """Model with both per-field UnstableField and extra='allow'."""

            model_config = ConfigDict(extra="allow")
            unstable_extra_fields: ClassVar[bool] = True

            id: str = Field(..., description="Item ID")
            name: str = Field(..., description="Item name")
            notes: Annotated[str, UnstableField()] = Field(
                ..., description="Notes (unstable)"
            )

            def get_id(self) -> str:
                return self.id

        db = InMemoryDatabase()
        items = [
            CombinedModel(
                id="C1",
                name="Combined 1",
                notes="Some note",
                DynField="dynamic_value",
            ),
        ]
        db._model_cls_to_stem[CombinedModel] = "combined_items"
        db._store[CombinedModel] = items

        state = get_stable_database_state(db, exclude_unstable_fields=True)

        # Per-field unstable field should be excluded
        assert "notes" not in state["combined_items"][0]
        # Extra field should be excluded
        assert "DynField" not in state["combined_items"][0]
        # Schema stable fields should remain
        assert state["combined_items"][0]["id"] == "C1"
        assert state["combined_items"][0]["name"] == "Combined 1"
