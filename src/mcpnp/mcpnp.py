
import logging
from cyclopts import convert
import numpy as np
from pydantic import Field
from typing import Any, Dict
from fastmcp import FastMCP
from typing import Annotated, Dict, Any
from mcpncp_responses import McpNpResponses

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

    def _json_response(self,
                       result_value:str,
                       status:bool,
                       message:str) -> Dict[str, Any]:
        if status:
            status_value = str(McpNpResponses.OK)
        else:
            status_value = str(McpNpResponses.ERROR)
        return {
            str(McpNpResponses.RESULT): result_value,
            str(McpNpResponses.STATUS): status_value,
            str(McpNpResponses.MESSAGE): message
        }

    def _register_tools(self) -> None:
        @self.mcp.tool(
            name="add",
            description="Numerically add a list of numbers (float or int). Use this for mathematical addition of any number of real numbers, including decimals and integers. Returns the sum as a float. Input should be a list of numbers."
        )
        async def mcpnp_add(
            numbers: Annotated[list[float], Field(description="List of numbers to add (float or int)")]
        ) -> Dict[str, Any]:
            self.logger.debug(f"mcpnp add called with numbers={numbers}")
            try:
                arr = np.array(numbers, dtype=float)
                result = np.sum(arr)
                self.logger.debug(f"mcpnp add result: {result}")
            except Exception as e:
                msg = f"McpNp add failed with error in mcpnp add: {e}"
                self.logger.error(msg)
                return self._json_response(
                    result_value="",
                    status=False,
                    message=msg
                )
            return self._json_response(
                result_value=str(float(result)),
                status=True,
                message="McpNp add successful"
            )

    def run(self, log_level: str = "debug") -> None:
        self.logger.debug("Starting MCPNP numerical server based on Numpy...")
        self.mcp.run(
            transport="streamable-http",
            host=self._host,
            port=self._port,
            log_level=log_level,
        )
        self.logger.debug("McpNp stopped")


