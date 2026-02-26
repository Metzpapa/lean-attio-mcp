"""Attio MCP Server — lean, purpose-built CRM tools."""

import logging
import traceback
from collections.abc import Sequence
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from . import tools_records, tools_lists, tools_schema, tools_notes, tools_tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("attio-mcp")

app = Server("attio-mcp")

# Collect all tools from all modules
ALL_TOOLS: list[dict] = (
    tools_records.TOOLS
    + tools_lists.TOOLS
    + tools_schema.TOOLS
    + tools_notes.TOOLS
    + tools_tasks.TOOLS
)

# Map tool names to their handler modules
HANDLERS = {}
for tool_def in tools_records.TOOLS:
    HANDLERS[tool_def["name"]] = tools_records.handle
for tool_def in tools_lists.TOOLS:
    HANDLERS[tool_def["name"]] = tools_lists.handle
for tool_def in tools_schema.TOOLS:
    HANDLERS[tool_def["name"]] = tools_schema.handle
for tool_def in tools_notes.TOOLS:
    HANDLERS[tool_def["name"]] = tools_notes.handle
for tool_def in tools_tasks.TOOLS:
    HANDLERS[tool_def["name"]] = tools_tasks.handle


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name=t["name"],
            description=t["description"],
            inputSchema=t["inputSchema"],
        )
        for t in ALL_TOOLS
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    try:
        if not isinstance(arguments, dict):
            arguments = {}

        handler = HANDLERS.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        result = handler(name, arguments)
        return [TextContent(type="text", text=result)]

    except Exception as e:
        logger.error(traceback.format_exc())
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    logger.info("Starting Attio MCP server")
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )
