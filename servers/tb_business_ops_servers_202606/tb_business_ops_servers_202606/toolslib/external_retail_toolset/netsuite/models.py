# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for NetSuite Inventory Module toolset."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InventoryRecord(BaseModel):
    """Inventory record model from NetSuite."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    sku: str = Field(..., description="Product SKU identifier")
    available_quantity: int = Field(..., description="Available quantity in stock")
    reserved_quantity: int = Field(
        ..., description="Reserved quantity for pending orders"
    )
    warehouse_location: Optional[str] = Field(
        None, description="Warehouse location code"
    )
    restock_date: Optional[datetime] = Field(
        None, description="Expected restock date if out of stock"
    )
    expected_restock_quantity: Optional[int] = Field(
        None, description="Expected quantity on restock"
    )

    def get_id(self) -> str:
        """Return the SKU as ID."""
        return self.sku
