"""MCP Client for connecting to the GIGR DuckDB MCP Server."""

from typing import Dict, List, Optional

from langchain_core.tools import Tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from loguru import logger


class MCPToolsManager:
    """Manager for MCP tools integration."""

    def __init__(self, mcp_server_path: Optional[str] = None):
        """Initialize MCP tools manager.

        Args:
            mcp_server_path: Path to the MCP server. If None, uses default.
        """
        from fastapi_langraph.core.config import settings

        self.mcp_server_path = mcp_server_path or settings.MCP_SERVER_PATH
        self.client: Optional[MultiServerMCPClient] = None
        self.tools: List[Tool] = []

    async def initialize(self) -> None:
        """Initialize connection to MCP server and retrieve tools."""
        try:
            # Use poetry to run the MCP server as recommended
            config = {
                "gigr_db": {
                    "command": "poetry",
                    "args": ["run", "gigr-mcp-server"],
                    "cwd": self.mcp_server_path,
                    "transport": "stdio",
                }
            }

            logger.info(f"Initializing MCP client with path: {self.mcp_server_path}")

            # Initialize the MCP client
            self.client = MultiServerMCPClient(config)

            # Retrieve tools from the MCP server
            self.tools = await self.client.get_tools()

            logger.info(
                f"Successfully connected to MCP server. Retrieved {len(self.tools)} tools"
            )
            for tool in self.tools:
                logger.info(f"  - Tool available: {tool.name}")

        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            # Continue without MCP tools if connection fails
            self.tools = []

    async def cleanup(self) -> None:
        """Clean up MCP client connection."""
        # As of langchain-mcp-adapters 0.1.0, cleanup is handled automatically
        if self.client:
            logger.info("MCP client cleanup completed")

    def get_tools(self) -> List[Tool]:
        """Get the list of available MCP tools.

        Returns:
            List of LangChain-compatible tools from MCP server.
        """
        return self.tools

    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all available tools.

        Returns:
            Dictionary mapping tool names to descriptions.
        """
        return {tool.name: tool.description for tool in self.tools}


# Global instance for easy access
_mcp_manager: Optional[MCPToolsManager] = None


async def get_mcp_tools_manager() -> MCPToolsManager:
    """Get or create the global MCP tools manager.

    Returns:
        The initialized MCP tools manager.
    """
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPToolsManager()
        await _mcp_manager.initialize()
    return _mcp_manager
