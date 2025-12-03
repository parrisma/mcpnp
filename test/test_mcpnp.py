#!/usr/bin/env python3
"""
MCP Streamable HTTP Client for NumpyAddServer
"""
import argparse
import asyncio
import json
import sys
import re
import numpy as np
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, ListToolsResult
from mcp.client.streamable_http import streamablehttp_client
from mcpnp import McpNpResponses
from mcpnp import McpNpConstant

TEST_BEARER_TOKEN = "sk-test-123"

"""MCP Client for testing MCPNP"""
    
class MCPNPTestClient:

    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()
        self._streams_context = None
        self._session_context = None
        self._excpected_tools = ["sum"]

    async def connect_to_streamable_http_server(self, server_url: str, headers: Optional[dict] = None):
        self._streams_context = streamablehttp_client(
            url=server_url,
            headers=headers or {},
        )
        read_stream, write_stream, _ = await self._streams_context.__aenter__()
        self._session_context = ClientSession(read_stream, write_stream)
        self.session = await self._session_context.__aenter__()
        await self.session.initialize()

    def _to_np_float(self, value):
        """Convert a value to a numpy float."""
        try:
            arr = np.array([value])
            return (arr.astype(float))[0]
        except Exception as e:
            raise ValueError(f"Cannot convert {value} to float: {e}")

    def _check_response_format(self, response_data):
        """Check if the response data has the expected format."""
        if not isinstance(response_data, dict):
            raise ValueError(f"Response data is not a dictionary: {response_data}")
        required_keys = {str(McpNpResponses.RESULT), str(McpNpResponses.STATUS), str(McpNpResponses.MESSAGE)}
        if not required_keys.issubset(response_data.keys()):
            raise ValueError(f"Response data missing required keys: {response_data}")
        return True
    
    async def list_tools(self):
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        response = await self.session.list_tools()
        return response

    async def call_tool(self, tool_name: str, arguments: dict):
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        result = await self.session.call_tool(tool_name, arguments)
        return result

    async def test_results_explanation(self):
        print("\n5. Testing results_explanation tool...")
        result = await self.call_tool("results_explanation", {})
        print(f"results_explanation result: {result.content}")
        result_text = str(result.content[0].text) if hasattr(result.content[0], 'text') else str(result.content[0])
        response = json.loads(result_text)
        self._check_response_format(response)
        assert response[str(McpNpResponses.STATUS)] == str(McpNpResponses.OK), f"Expected status {str(McpNpResponses.OK)}, got {response[str(McpNpResponses.STATUS)]}"
        print("✓ results_explanation test passed")

    async def test_tool_list(self):
            print("\n1. Testing tool listing...")
            tools_response: ListToolsResult = await self.list_tools()
            actual_tools: list[str] = [tool.name for tool in tools_response.tools]
            for expected_tool in self._excpected_tools:
                print(f"Expected tool: {expected_tool}")
                assert expected_tool in actual_tools
            print("✓ All expected tools found")       
        
    async def test_elementwise_operators(self):
        print("\n4. Testing elementwise_operators tool...")
        result = await self.call_tool("elementwise_operators", {})
        print(f"elementwise_operators result: {result.content}")
        result_text = str(result.content[0].text) if hasattr(result.content[0], 'text') else str(result.content[0])
        response = json.loads(result_text)
        self._check_response_format(response)
        operators = json.loads(response[str(McpNpResponses.RESULT)])
        expected_ops = {"add", "subtract", "multiply", "divide"}
        assert set(operators.keys()) == expected_ops, f"Expected operators {expected_ops}, got {set(operators.keys())}"
        for op, desc in operators.items():
            assert isinstance(desc, str) and len(desc) > 0, f"Operator {op} missing description"
        print("✓ elementwise_operators test passed")

    async def test_elementwise(self):
        print("\n3. Testing elementwise tool, good_cases...")
        test_cases_good = [
            # Format: (list_a, list_b, operator, expected_result)
            ([1, 2, 3], [4, 5, 6], "add", [5.0, 7.0, 9.0]),
            ([10, 20, 30], [1, 2, 3], "subtract", [9.0, 18.0, 27.0]),
            ([2, 4, 6], [3, 2, 1], "multiply", [6.0, 8.0, 6.0]),
            ([8, 6, 4], [2, 3, 4], "divide", [4.0, 2.0, 1.0]),
            ([np.pi, np.e], [np.e, np.pi], "add", [np.pi + np.e, np.e + np.pi]),
            ([0, 0, 0], [0, 0, 0], "add", [0.0, 0.0, 0.0]),
            ([1e10, 2e10], [3e10, 4e10], "add", [4e10, 6e10]),
            # Negative numbers and negative results
            ([-1, -2, -3], [-4, -5, -6], "add", [-5.0, -7.0, -9.0]),
            ([-10, -20, -30], [-1, -2, -3], "subtract", [-9.0, -18.0, -27.0]),
            ([2, -4, 6], [-3, 2, -1], "multiply", [-6.0, -8.0, -6.0]),
            ([-8, 6, -4], [2, -3, 4], "divide", [-4.0, -2.0, -1.0]),
            ([0, -1, 1], [-1, 1, 0], "add", [-1.0, 0.0, 1.0]),
        ]
        for list_a, list_b, operator, expected in test_cases_good:
            print(f"elementwise {operator} of {list_a} and {list_b}")
            result = await self.call_tool("elementwise", {"list_a": list_a, "list_b": list_b, "operator": operator})
            print(f"elementwise result: {result.content}")
            result_text = str(result.content[0].text) if hasattr(result.content[0], 'text') else str(result.content[0])
            response = json.loads(result_text)
            self._check_response_format(response)
            # Parse result_value as a list of floats
            result_list = json.loads(response[str(McpNpResponses.RESULT)])
            assert all(np.isclose(result_list[i], expected[i]) for i in range(len(expected))), f"Expected {expected}, got {result_list}"

        print("\n3. Testing elementwise tool, bad_cases...")
        test_cases_bad = [
            # Unequal length
            ([1, 2], [1], "add"),
            # Invalid operator
            ([1, 2], [3, 4], "invalid_op"),
            # Non-numeric input
            ([1, "a"], [2, 3], "add"),
            # Divide by zero
            ([1, 2], [0, 0], "divide"),
        ]
        for list_a, list_b, operator in test_cases_bad:
            print(f"elementwise {operator} of {list_a} and {list_b}")
            result = await self.call_tool("elementwise", {"list_a": list_a, "list_b": list_b, "operator": operator})
            print(f"elementwise result: {result.content}")
            result_text = str(result.content[0].text) if hasattr(result.content[0], 'text') else str(result.content[0])
            assert type(result_text) is str, "Incorrect error response format"
            assert bool(re.search(r"error|fail|unsupported|length", result_text, re.IGNORECASE)), f"Expected error message, got {result_text}"
        print("✓ elementwise tests passed")
        
    async def test_sum(self):
            # Test 2: Call sum
            print("\n2. Testing sum tool, good_cases...")
            # Test 2: Call sum with a list of numbers
            test_cases_good = [[[],0],
                                           [[1],1],
                                           [[-1],-1],
                                           [[2, 3, 4.5], 9.5],
                                           [[-1, 1], 0],
                                           [[-1, -1], -2],
                                           [[1.5, 2.5, 3.5], 7.5],
                                           [[0, 0, 0], 0],
                                           [[-1.5, -2.5, -3.5], -7.5],
                                           [[1e10, 2e10], 3e10],
                                           [[np.pi, -np.pi], np.sum([np.pi, -np.pi])],
                                           [[np.e, np.e, np.e], np.multiply(np.e, 3)]
                                          ]
            for numbers, expected_sum in test_cases_good:
                print(f"suming numbers: {numbers}")
                sum_result = await self.call_tool("sum", {"numbers": numbers})
                print(f"sum result: {sum_result.content}")
                # Extract and validate result
                sum_text = str(sum_result.content[0].text) if hasattr(sum_result.content[0], 'text') else str(sum_result.content[0])
                response = json.loads(sum_text)
                self._check_response_format(response)
                assert float(response[str(McpNpResponses.RESULT)]) == expected_sum, f"Expected {expected_sum}, got {response['result']}"

            print("\n2. Testing sum tool, bad_cases...")
            # Test 2: Call sum with a list of numbers
            test_cases_bad = [[[1, "NotANNumber"],0]]
            for numbers, expected_sum in test_cases_bad:
                print(f"suming numbers: {numbers}")
                sum_result = await self.call_tool("sum", {"numbers": numbers})
                print(f"sum result: {sum_result.content}")
                # Extract and validate result
                sum_text = str(sum_result.content[0].text) if hasattr(sum_result.content[0], 'text') else str(sum_result.content[0])
                assert type(sum_text) is str, "Incorrect error response format"
                assert bool(re.search(r"error", sum_text, re.IGNORECASE)), f"Expected error message, got {sum_text}"
            print("✓ sum tests passed")

    async def test_constant(self):
        print("\n6. Testing constant tool...")
        # Supported constant names
        supported = [c.value for c in McpNpConstant]
        for name in supported:
            print(f"Requesting constant: {name}")
            result = await self.call_tool("constant", {"name": name})
            print(f"constant result: {result.content}")
            result_text = str(result.content[0].text) if hasattr(result.content[0], 'text') else str(result.content[0])
            assert result_text and len(result_text) > 0, f"No result for constant {name}"
            response = json.loads(result_text)
            self._check_response_format(response)
            value = json.loads(response[str(McpNpResponses.RESULT)])['value']
            assert value is not None, f"Value for constant {name} is None"
        # Test unsupported constant
        result = await self.call_tool("constant", {"name": "NOT_A_CONSTANT"})
        result_text = str(result.content[0].text) if hasattr(result.content[0], 'text') else str(result.content[0])
        response = json.loads(result_text)
        self._check_response_format(response)
        assert response[str(McpNpResponses.STATUS)] == str(McpNpResponses.ERROR), "Expected error status for unsupported constant"
        print("✓ constant tool test passed")

    async def test_stddev(self):
        print("\n7. Testing stddev tool...")
        test_cases = [
            ([1, 2, 3, 4, 5], np.std([1, 2, 3, 4, 5])),
            ([0, 0, 0, 0], 0.0),
            ([10, 10, 10, 20], np.std([10, 10, 10, 20])),
            ([1.5, 2.5, 3.5], np.std([1.5, 2.5, 3.5])),
            ([-1, -2, -3], np.std([-1, -2, -3])),
            ([], np.nan),  
            ([42], np.nan),  
        ]
        for numbers, expected in test_cases:
            print(f"Calculating stddev for: {numbers}")
            result = await self.call_tool("stddev", {"numbers": numbers})
            print(f"stddev result: {result.content}")
            result_text = str(result.content[0].text) if hasattr(result.content[0], 'text') else str(result.content[0])
            assert result_text and len(result_text) > 0, "No result returned from stddev tool"
            response = json.loads(result_text)
            self._check_response_format(response)
            try:
                value = float(response[str(McpNpResponses.RESULT)])
            except (ValueError, TypeError):
                value = response[str(McpNpResponses.RESULT)]
            assert np.isclose(value, expected), f"Expected {expected}, got {value}"
        # Test error case
        result = await self.call_tool("stddev", {"numbers": [1, "not_a_number"]})
        result_text = str(result.content[0].text) if hasattr(result.content[0], 'text') else str(result.content[0])
        try:# pydantic catches issue so no call to tool and no json response
            response = json.loads(result_text) 
            self._check_response_format(response)
            assert response[str(McpNpResponses.STATUS)] == str(McpNpResponses.ERROR), "Expected error status for invalid input"
        except Exception as e:
            assert result_text == "Input validation error: 'not_a_number' is not of type 'number'", f"Unexpected error message: {result_text}"
        print("✓ stddev tool test passed")
                        
    async def run_tests(self):
        print("\nRunning MCP NumpysumServer client tests...")
        try:
            await self.test_tool_list()
            await self.test_sum()
            await self.test_elementwise()
            await self.test_elementwise_operators()
            await self.test_results_explanation()
            await self.test_constant()
            await self.test_stddev()
            print("\nAll tests passed successfully!")
        except AssertionError as e:
            print(f"\nTest failed: {e}")
            raise
        except Exception as e:
            print(f"\nTest error: {e}")
            raise

    async def cleanup(self):
        if hasattr(self, '_session_context') and self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if hasattr(self, '_streams_context') and self._streams_context:
            await self._streams_context.__aexit__(None, None, None)

async def main():
    parser = argparse.ArgumentParser(description="MCPNP Test Client")
    parser.add_argument("--host", "-H", default="0.0.0.0", help="Host/IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", "-P", type=int, default=9124, help="Port to bind (default: 9124)")
    args = parser.parse_args()
    mcpnp_url = f"http://{args.host}:{args.port}/mcp"
    client = MCPNPTestClient()
    try:
        print(f"Connecting to MCPNP server at {mcpnp_url}...")
        headers = {"Authorization": f"Bearer {TEST_BEARER_TOKEN}"} if TEST_BEARER_TOKEN else {}
        await client.connect_to_streamable_http_server(mcpnp_url, headers=headers)
        print("Connected successfully!")
        await client.run_tests()
        sys.exit(0)
    except Exception as e:
        print(f"Error running MCPNP Tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("Exited MCPNP Test Client...")
        await client.cleanup()

if __name__ == "__main__":
    print("Starting MCPNP Test Client...")
    asyncio.run(main())
