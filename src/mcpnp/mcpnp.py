
import logging
import numpy as np
from pydantic import Field
from typing import Any, Dict
from fastmcp import FastMCP
from typing import Annotated, Dict, Any

class McpNp:
    """MCP server exposing numpy capabilities."""

    def __init__(self, 
                 host: str, 
                 port: int) -> None:
        self.logger = logging.getLogger(__name__)
        self._host = host
        self._port = port
        self.mcp = FastMCP(name="McpNp", version="1.0.0")
        self._register_tools()

    def _register_tools(self) -> None:
        @self.mcp.tool(name="add", description="Add two numbers")
        async def mcpnp_add(
            a: Annotated[float, Field(description="First number")],
            b: Annotated[float, Field(description="Second number")]
        ) -> Dict[str, Any]:
            self.logger.debug(f"mcpnp add called with a={a}, b={b}")
            result = np.add(a, b)
            self.logger.debug(f"mcpnp add result: {result}")
            return {"result": float(result)}

    def run(self, log_level: str = "debug") -> None:
        self.logger.debug("Starting MCPNP numerical server based on Numpy...")
        self.mcp.run(
            transport="streamable-http",
            host=self._host,
            port=self._port,
            log_level=log_level,
        )
        self.logger.debug("McpNp stopped")


