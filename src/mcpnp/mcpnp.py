
import logging
from multiprocessing import Value
import numpy as np
import scipy.constants as sc
import json
from pydantic import Field
from typing import Any, Dict
from fastmcp import FastMCP
from typing import Annotated, Dict, Any
from mcpncp_responses import McpNpResponses
from mcpnp_constants import McpNpConstant

class McpNp:
    """MCP server exposing numpy capabilities."""

    MCPNP_CONSTANT_VALUES = {
        McpNpConstant.PI.value: np.pi,
        McpNpConstant.E.value: np.e,
        McpNpConstant.SPEED_OF_LIGHT.value: sc.speed_of_light,
        McpNpConstant.PLANCK.value: sc.Planck,
        McpNpConstant.ELEMENTARY_CHARGE.value: sc.elementary_charge,
        McpNpConstant.GRAVITATIONAL_CONSTANT.value: sc.gravitational_constant,
        McpNpConstant.ELECTRON_MASS.value: sc.electron_mass,
        McpNpConstant.PROTON_MASS.value: sc.proton_mass,
    }
    
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
            name="stddev",
            description="Calculate the standard deviation of a list of real numbers using numpy.std. Returns the result as a float."
        )
        async def mcpnp_stddev(
            numbers: Annotated[list[float], Field(description="List of real numbers (float or integer) to calculate standard deviation")]
        ) -> Dict[str, Any]:
            self.logger.debug(f"mcpnp stddev called with numbers={numbers}")
            try:
                arr = np.array(numbers, dtype=float)
                result = float(np.std(arr))
                self.logger.debug(f"mcpnp stddev result: {result}")
            except Exception as e:
                msg = f"McpNp stddev failed with error: {e}"
                self.logger.error(msg)
                return self._json_response(
                    result_value=str(McpNpResponses.NAN),status=False,
                    message=msg
                )
            return self._json_response(
                result_value=str(result),
                status=True,
                message="McpNp stddev successful"
            )
            
        @self.mcp.tool(
            name="constant",
            description="Return the value and description of a requested mathematical or physical constant. Supported names: PI, E, SPEED_OF_LIGHT, PLANCK, ELEMENTARY_CHARGE, GRAVITATIONAL_CONSTANT, ELECTRON_MASS, PROTON_MASS."
        )
        async def mcpnp_constant(
            name: Annotated[str, Field(description="Name of the constant to retrieve. Must match enum McpNpConstant.")]
        ) -> Dict[str, Any]:
            if name not in self.MCPNP_CONSTANT_VALUES:
                return self._json_response(
                    result_value="",
                    status=False,
                    message=f"Constant '{name}' is not supported."
                )
            value = self.MCPNP_CONSTANT_VALUES[name]
            result = {"name": name, "value": float(value) if value is not None else None}
            return self._json_response(
                result_value=json.dumps(result, indent=2),
                status=True,
                message=f"Constant '{name}' returned."
            )
            
        @self.mcp.tool(
            name="results_explanation",
            description="Explains the JSON structure of MCPNP results and the meaning of each response string."
        )
        async def mcpnp_results_explanation() -> Dict[str, Any]:
            from mcpncp_responses import McpNpResponses
            explanation = {
                "json_structure": {
                    str(McpNpResponses.RESULT): "The main result value, e.g., a number, list, or error string.",
                    str(McpNpResponses.STATUS): "Indicates if the operation was successful ('ok') or failed ('error').",
                    str(McpNpResponses.MESSAGE): "A human-readable message describing the result or error."
                },
                "response_strings": {
                    str(McpNpResponses.RESULT): "Key for the result value.",
                    str(McpNpResponses.STATUS): "Key for the status of the operation.",
                    str(McpNpResponses.OK): "Indicates success.",
                    str(McpNpResponses.ERROR): "Indicates failure.",
                    str(McpNpResponses.MESSAGE): "Key for the message field."
                }
            }
            return self._json_response(
                result_value=json.dumps(explanation, indent=2),
                status=True,
                message="Explanation of MCPNP result JSON structure and response strings."
            )
            
        @self.mcp.tool(
            name="elementwise_operators",
            description="List all supported elementwise operators and their descriptions."
        )
        async def mcpnp_list_operators() -> Dict[str, Any]:
            from mcpnp_operator import McpNpOperator
            operator_info = {
                McpNpOperator.ADD.value: "Elementwise addition of two lists of real numbers.",
                McpNpOperator.SUBTRACT.value: "Elementwise subtraction of two lists of real numbers.",
                McpNpOperator.MULTIPLY.value: "Elementwise multiplication of two lists of real numbers.",
                McpNpOperator.DIVIDE.value: "Elementwise division of two lists of real numbers (division by zero returns NaN)."
            }
            return self._json_response(
                result_value=json.dumps(operator_info),
                status=True,
                message="Supported operators listed."
            )
            
        @self.mcp.tool(
            name="elementwise",
            description="Perform element-wise operations (add, subtract, multiply, divide) on two lists of real numbers. The operation is specified by the 'operator' argument, which must be one of: add, subtract, multiply, divide. Lists must be of equal length. Returns a list of results as floats."
        )
        async def mcpnp_elementwise_op(
            list_a: Annotated[list[float], Field(description="First list of real numbers (float or integer)")],
            list_b: Annotated[list[float], Field(description="Second list of real numbers (float or integer)")],
            operator: Annotated[str, Field(description="Element-wise operation to perform: add, subtract, multiply, divide")]
        ) -> Dict[str, Any]:
            self.logger.debug(f"mcpnp elementwise_op called with list_a={list_a}, list_b={list_b}, operator={operator}")
            from mcpnp_operator import McpNpOperator
            try:
                arr_a = np.array(list_a, dtype=float)
                arr_b = np.array(list_b, dtype=float)
                if arr_a.shape != arr_b.shape:
                    raise ValueError("Input lists must be of equal length.")
                op = McpNpOperator(operator)
                result = None
                error_detected = False
                error_message = ""
                if op == McpNpOperator.ADD:
                    result = np.add(arr_a, arr_b)
                elif op == McpNpOperator.SUBTRACT:
                    result = np.subtract(arr_a, arr_b)
                elif op == McpNpOperator.MULTIPLY:
                    result = np.multiply(arr_a, arr_b)
                elif op == McpNpOperator.DIVIDE:
                    # Elementwise division, catch division by zero
                    result = []
                    for idx, (a, b) in enumerate(zip(arr_a, arr_b)):
                        try:
                            if b == 0:
                                result.append(float('nan'))
                                error_detected = True
                                error_message = f"Division by zero at index {idx}. "
                            else:
                                result.append(float(a) / float(b))
                        except Exception:
                            result.append(float('nan'))
                            error_detected = True
                            error_message = f"Invalid division at index {idx}. "
                    result = np.array(result)
                else:
                    raise ValueError(f"Unsupported operator: {operator}")
                self.logger.debug(f"mcpnp elementwise_op result: {result}")
            except Exception as e:
                msg = f"McpNp elementwise_op failed with error: {e}"
                self.logger.error(msg)
                return self._json_response(
                    result_value="",
                    status=False,
                    message=msg
                )
            # Check for NaN in result
            result_list = [float(x) if not np.isnan(x) else str(McpNpResponses.NAN) for x in result]
            if error_detected or any(x == str(McpNpResponses.NAN) for x in result_list):
                return self._json_response(
                    result_value=str(result_list),
                    status=False,
                    message=f"McpNp elementwise_op failed: {error_message if error_message else 'One or more results are NaN.'}"
                )
            return self._json_response(
                result_value=str(result_list),
                status=True,
                message="McpNp elementwise_op successful"
            )
            
        @self.mcp.tool(
            name="sum",
            description="Numerically sum a given list of real numbers (float or integer), use this for mathematical summation of arbitrary lenght list of real numbers, returns the sum as a float. A zero length list returns 0.0"
        )        
        async def mcpnp_sum(
            numbers: Annotated[list[float], Field(description="List of real numbers to sum (float or integer)")]
        ) -> Dict[str, Any]:
            self.logger.debug(f"mcpnp sum called with numbers={numbers}")
            try:
                arr = np.array(numbers, dtype=float)
                result = np.sum(arr)
                self.logger.debug(f"mcpnp sum result: {result}")
            except Exception as e:
                msg = f"McpNp sum failed with error: {e}"
                self.logger.error(msg)
                return self._json_response(
                    result_value="",
                    status=False,
                    message=msg
                )
            return self._json_response(
                result_value=str(float(result)),
                status=True,
                message="McpNp sum successful"
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


