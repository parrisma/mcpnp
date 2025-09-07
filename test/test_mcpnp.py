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
from mcpncp_responses import McpNpResponses

TEST_BEARER_TOKEN = "sk-test-123"

class MCPNPTestClient:
    """MCP Client for testing MCPNP"""
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()
        self._streams_context = None
        self._session_context = None
        self._excpected_tools = ["add"]

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

    async def test_tool_list(self):
            print("\n1. Testing tool listing...")
            tools_response: ListToolsResult = await self.list_tools()
            actual_tools: list[str] = [tool.name for tool in tools_response.tools]
            for expected_tool in self._excpected_tools:
                print(f"Expected tool: {expected_tool}")
                assert expected_tool in actual_tools
            print("✓ All expected tools found")       
            
    async def test_add(self):
            # Test 2: Call add
            print("\n2. Testing add tool, good_cases...")
            # Test 2: Call add with a list of numbers
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
                print(f"Adding numbers: {numbers}")
                add_result = await self.call_tool("add", {"numbers": numbers})
                print(f"Add result: {add_result.content}")
                # Extract and validate result
                add_text = str(add_result.content[0].text) if hasattr(add_result.content[0], 'text') else str(add_result.content[0])
                response = json.loads(add_text)
                self._check_response_format(response)
                assert float(response[str(McpNpResponses.RESULT)]) == expected_sum, f"Expected {expected_sum}, got {response['result']}"

            print("\n2. Testing add tool, bad_cases...")
            # Test 2: Call add with a list of numbers
            test_cases_bad = [[[1, "NotANNumber"],0]]
            for numbers, expected_sum in test_cases_bad:
                print(f"Adding numbers: {numbers}")
                add_result = await self.call_tool("add", {"numbers": numbers})
                print(f"Add result: {add_result.content}")
                # Extract and validate result
                add_text = str(add_result.content[0].text) if hasattr(add_result.content[0], 'text') else str(add_result.content[0])
                assert type(add_text) is str, "Incorrect error response format"
                assert bool(re.search(r"error", add_text, re.IGNORECASE)), f"Expected error message, got {add_text}"
            print("✓ add tests passed")
                        
    async def run_tests(self):
        print("\nRunning MCP NumpyAddServer client tests...")
        try:
            await self.test_tool_list()
            await self.test_add()
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
