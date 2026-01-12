"""FastMCP server setup for LedgerOne.

Based on research.md from 007-api-for-mcp feature.
"""

from mcp.server.fastmcp import FastMCP

# Create the MCP server instance
mcp = FastMCP(
    name="LedgerOne Accounting",
    json_response=True,
)


def get_mcp_server() -> FastMCP:
    """Get the FastMCP server instance.

    This function is used to register tools from other modules
    and to mount the MCP server to the FastAPI app.
    """
    return mcp
