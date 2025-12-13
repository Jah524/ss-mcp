"""Template MCP server implementation."""

from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("template-server")


@server.list_tools()
async def list_tools():
    """List available tools."""
    return []


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
