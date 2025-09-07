import logging
import argparse
from mcpnp import McpNp

# Configure basic logging at DEBUG level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="McpNp MCP server")
    parser.add_argument("--host", "-H", default="0.0.0.0", help="Host/IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", "-P", type=int, default=9124, help="Port to bind (default: 9124)")
    args = parser.parse_args()

    app = McpNp(host=args.host, 
                port=args.port)
    app.run()