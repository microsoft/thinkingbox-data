import json
from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from pydantic_core import to_jsonable_python

mcp = FastMCP("ms_store")


class SuccessResponse(BaseModel):
    status: Literal["ok"]


def success_response(**kwargs) -> str:
    obj = {
        "status": "ok",
        **to_jsonable_python(kwargs),
    }
    return json.dumps(obj)


@mcp.tool(name="__reserved__init")
async def initialize(config: dict):

    return json.dumps({"status": "ok"})


@mcp.tool(name="__reserved__geteffects")
async def geteffects():

    return json.dumps({"effects": []})


@mcp.tool(
    name="shovels_at_ms_store",
    description="Get a description of all the shovels available at MS Store",
)
async def shovels_at_ms_store() -> str:
    return success_response(response=SHOVELS_AT_MS_STORE)


@mcp.tool(name="ms_store_hours", description="Get MS Store opening hours")
async def ms_store_hours() -> str:
    return success_response(response=MS_STORE_HOURS)


@mcp.tool(name="ms_store_location", description="Get MS Store location")
async def ms_store_location() -> str:
    return success_response(response=MS_STORE_LOCATION)


SHOVELS_AT_MS_STORE = """\
Welcome to MS Store! We are thrilled to offer a wide range of high-quality tools and equipment for
all your DIY needs. Whether you're working on a garden project, building a new patio, or just need
a reliable tool for digging, our selection of shovels is sure to meet your needs.

Explore our top picks below:

XP Pro-Dig Shovel
    Brand: XP
    Description: The XP Pro-Dig Shovel is engineered for heavy-duty tasks. With its reinforced
    steel blade and ergonomic handle, it's perfect for both professional landscapers and
    enthusiastic gardeners.
ME Tough Terrain Spade
    Brand: ME
    Description: Designed for rugged use, the ME Tough Terrain Spade features a carbon steel head
    and a shock-absorbing grip. Ideal for breaking through tough soil and roots with ease.
DOS Garden Companion
    Brand: DOS
    Description: The DOS Garden Companion is lightweight yet durable, making it the perfect choice
    for everyday gardening. Its rust-resistant coating ensures longevity.
Vista Power Shovel
    Brand: Vista Tools
    Description: The Vista Power Shovel combines innovative design with superior strength. Its
    serrated edges make cutting through sod and clay a breeze.
Techno Earth Digger
    Brand: Techno Tools
    Description: Built for efficiency, the Techno Earth Digger offers a fiberglass handle and a
    tempered steel blade, providing durability and comfort for extended use.
Quantum Heavy Load Shovel
    Brand: Quantum Gear
    Description: Perfect for moving large amounts of soil, the Quantum Heavy Load Shovel features
    an oversized blade and a reinforced shaft for maximum performance.

Explore these options and more at MS Store, where quality and customer satisfaction are our top
priorities. For more information or to place an order, visit our website or contact our sales team
today!
"""

MS_STORE_HOURS = """\
MS Store opening hours are:
- Monday to Friday: 9:00 - 18:00
- Saturday: 10:00 - 16:00
- Sunday: Closed
"""

MS_STORE_LOCATION = """\
The store locations are:
Redmond Store   12312 Redmond Street
Seattle Store   9844 Seattle Way
"""

if __name__ == "__main__":
    mcp.run(transport="stdio")
