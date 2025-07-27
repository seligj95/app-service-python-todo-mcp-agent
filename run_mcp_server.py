"""
Standalone MCP server runner.
This runs the FastMCP server on its own port.
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path setup to avoid linting issues
from src.app import create_app  # noqa: E402
from src.mcp_server import create_mcp_server  # noqa: E402


async def main():
    """Run the MCP server."""
    # Create Flask app for context
    flask_app = create_app()
    
    # Create MCP server
    mcp_server = create_mcp_server(flask_app)
    
    # Run the FastMCP server
    print("Starting MCP server on port 3001...")
    print("Connect with MCP Inspector using HTTP transport at:")
    print("http://localhost:3001")
    
    # Start the server
    await mcp_server.server.run(transport="http", port=3001)


if __name__ == '__main__':
    asyncio.run(main())
