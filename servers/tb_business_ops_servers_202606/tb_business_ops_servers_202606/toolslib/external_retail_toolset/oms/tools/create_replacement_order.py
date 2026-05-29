# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for creating a replacement order."""

from datetime import datetime, timezone
from typing import Any, Dict, Type

from tb_business_ops_servers_202606 import InMemoryDatabase, Tool, get_schema_without_refs
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.netsuite.models import (
    InventoryRecord,
)
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.oms.models import (
    FulfillmentType,
    Order,
    OrderLineItem,
    OrderStatus,
    ShippingSpeed,
)
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.shopify_pim.models import (
    ProductDetails,
)
from pydantic import BaseModel, ConfigDict, Field

# Fixed time for testing purposes
FIXED_DATETIME = datetime(2025, 10, 1, 13, 0, 5, tzinfo=timezone.utc)


class CreateReplacementOrderInput(BaseModel):
    """Input for create_replacement_order tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    original_order_id: str = Field(
        ...,
        description="Original order identifier for reference",
        examples=["ORD-00012345"],
    )
    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    sku: str = Field(
        ..., description="Product SKU to replace", examples=["SKU-00012345"]
    )
    quantity: int = Field(..., description="Quantity to replace", examples=[1])
    shipping_speed: ShippingSpeed = Field(
        ...,
        description="Shipping speed: standard, expedited, or next_day.",
        examples=["standard"],
    )
    shipping_address_line1: str = Field(
        ..., description="Shipping address line 1", examples=["123 Main St"]
    )
    shipping_address_city: str = Field(
        ..., description="Shipping address city", examples=["Memphis"]
    )
    shipping_address_state: str = Field(
        ..., description="Shipping address state", examples=["TN"]
    )
    shipping_address_zip: str = Field(
        ..., description="Shipping address ZIP code", examples=["38103"]
    )


class CreateReplacementOrderOutput(BaseModel):
    """Output for create_replacement_order tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    replacement_order_id: str = Field(
        ...,
        description="Generated replacement order identifier",
        examples=["ORD-00098765"],
    )
    status: str = Field(..., description="Order status", examples=["processing"])
    total_amount: float = Field(
        ...,
        description="Total amount (should be 0.00 for warranty replacements)",
        examples=[0.00],
    )


class CreateReplacementOrderTool(Tool):
    """Tool implementation for creating a replacement order."""

    @property
    def name(self) -> str:
        return "create_replacement_order"

    @property
    def description(self) -> str:
        return "Create a replacement order."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CreateReplacementOrderInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CreateReplacementOrderOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return CreateReplacementOrderInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CreateReplacementOrderOutput

    async def run(
        self, db: InMemoryDatabase, request: CreateReplacementOrderInput
    ) -> CreateReplacementOrderOutput:
        """Create a replacement order for a product."""
        try:
            # Check inventory availability (hard guard)
            all_inventory = db.get_all(InventoryRecord)
            inventory_record = None
            for inv in all_inventory:
                if inv.sku == request.sku:
                    inventory_record = inv
                    break

            if not inventory_record or inventory_record.available_quantity == 0:
                raise Tool.ExecutionError(
                    f"Product out of stock - cannot create replacement order for SKU {request.sku}. "
                    "Available quantity is 0."
                )

            # Decrement inventory (optimistic - don't reserve, just reduce)
            inventory_record.available_quantity -= request.quantity
            db.update(inventory_record)

            # Get product details for name
            all_products = db.get_all(ProductDetails)
            product = None
            for prod in all_products:
                if prod.sku == request.sku:
                    product = prod
                    break

            if not product:
                raise Tool.ExecutionError(f"Product SKU not found: {request.sku}")

            # Generate deterministic order ID with prefix ORD-2 to distinguish from original orders
            all_orders = db.get_all(Order)
            existing_ids = [order.id for order in all_orders]
            counter = 1
            while True:
                new_order_id = f"ORD-2{counter:07d}"
                if new_order_id not in existing_ids:
                    break
                counter += 1

            # Generate line item ID
            all_line_items = db.get_all(OrderLineItem)
            existing_line_ids = [item.id for item in all_line_items]
            line_counter = 1
            while True:
                new_line_id = f"LIN-2{line_counter:07d}"
                if new_line_id not in existing_line_ids:
                    break
                line_counter += 1

            # Create new replacement order
            new_order = Order(
                id=new_order_id,
                customer_id=request.customer_id,
                order_date=FIXED_DATETIME,
                status=OrderStatus.PROCESSING,
                subtotal_amount=0.00,  # No charge for replacements
                discount_amount=0.00,
                points_used=0,
                points_value=0.00,
                shipping_cost=0.00,  # No shipping charge for replacements
                total_amount=0.00,
                shipping_address_line1=request.shipping_address_line1,
                shipping_address_city=request.shipping_address_city,
                shipping_address_state=request.shipping_address_state,
                shipping_address_zip=request.shipping_address_zip,
                shipping_speed=request.shipping_speed,
                fulfillment_type=FulfillmentType.WAREHOUSE,  # Always warehouse
                installation_service_id=None,  # No installation for replacements
            )

            # Create order line item
            new_line_item = OrderLineItem(
                id=new_line_id,
                order_id=new_order_id,
                sku=request.sku,
                product_name=product.name,
                quantity=request.quantity,
                base_price=0.00,  # No charge
                discount_amount=0.00,
                final_price=0.00,
            )

            # Save to database
            db.create(new_order)
            db.create(new_line_item)

            # Return replacement order details
            return CreateReplacementOrderOutput(
                replacement_order_id=new_order_id,
                status=OrderStatus.PROCESSING.value,
                total_amount=0.00,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to create replacement order: {str(e)}"
            raise Tool.ExecutionError(error_message)
