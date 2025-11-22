"""
Sample FastMCP client for mcp-neo4j-cypher server with API key authentication.

This script demonstrates:
1. Loading API key from .env
2. Connecting to HTTP MCP server with Bearer auth
3. Listing available tools
4. Calling the get_neo4j_schema tool

Prerequisites:
- Server must be running (use start_server.py)
- .env file must contain NEO4J_API_KEY

Usage:
  python test_auth.py           # Run client locally
  python test_auth.py --docker  # Run client in Docker container
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def main() -> None:
    """Connect to MCP server and demonstrate tool usage."""
    print("=" * 60)
    print("MCP Neo4j Cypher Client - Authentication Demo")
    print("=" * 60)
    print()

    # Load API key from .env
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("✗ .env file not found")
        print("Please run start_server.py first to generate API key")
        return

    load_dotenv(env_path)
    api_key = os.getenv("NEO4J_API_KEY")

    if not api_key:
        print("✗ NEO4J_API_KEY not found in .env")
        print("Please run start_server.py first to generate API key")
        return

    print(f"✓ Loaded API key from .env: {api_key[:16]}...")
    print()

    # Configure transport with authentication
    server_url = "http://127.0.0.1:8001/mcp/"
    transport = StreamableHttpTransport(server_url, auth=api_key)
    print(f"✓ Configured transport: {server_url}")
    print()

    try:
        async with Client(transport) as client:
            # Test connection
            print("Testing connection...")
            await client.ping()
            print("✓ Connection successful")
            print()

            # List available tools
            print("Available Tools:")
            print("-" * 60)
            tools = await client.list_tools()
            for i, tool in enumerate(tools, 1):
                print(f"{i}. {tool.name}")
                if hasattr(tool, "description") and tool.description:
                    # Print first line of description
                    desc_first_line = tool.description.split("\n")[0]
                    print(f"   {desc_first_line}")
            print()

            # Call get_neo4j_schema tool
            print("Calling get_neo4j_schema tool...")
            print("-" * 60)
            result = await client.call_tool("get_neo4j_schema", {})

            # Display result
            print(f"✓ Tool call successful")
            print(f"  Result type: {result.content[0].type}")
            print()

            # Parse and display schema (pretty print JSON)
            if result.content and len(result.content) > 0:
                schema_text = result.content[0].text
                schema_data = json.loads(schema_text)

                print("Neo4j Schema Summary:")
                print("-" * 60)

                # Count nodes and relationships
                node_types = [
                    k for k, v in schema_data.items() if v.get("type") == "node"
                ]
                rel_types = [
                    k
                    for k, v in schema_data.items()
                    if v.get("type") == "relationship"
                ]

                print(f"Node types: {len(node_types)}")
                print(f"Relationship types: {len(rel_types)}")
                print()

                # Show node types with property counts
                if node_types:
                    print("Node Types:")
                    for node_type in node_types:
                        node_info = schema_data[node_type]
                        prop_count = len(node_info.get("properties", {}))
                        count = node_info.get("count", "?")
                        print(f"  - {node_type}: {prop_count} properties, {count} nodes")
                    print()

                # Show relationship types
                if rel_types:
                    print("Relationship Types:")
                    for rel_type in rel_types:
                        rel_info = schema_data[rel_type]
                        prop_count = len(rel_info.get("properties", {}))
                        count = rel_info.get("count", "?")
                        print(
                            f"  - {rel_type}: {prop_count} properties, {count} relationships"
                        )
                    print()

                # Optionally show full schema (commented out to avoid clutter)
                # print("Full Schema (JSON):")
                # print(json.dumps(schema_data, indent=2))

            print("=" * 60)
            print("✓ Client demo completed successfully")
            print("=" * 60)

    except Exception as e:
        print(f"✗ Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Ensure start_server.py is running in another terminal")
        print("2. Check that server is listening on http://127.0.0.1:8001/mcp/")
        print("3. Verify API key matches between .env and running server")
        raise


def run_in_docker() -> None:
    """Run the test client inside a Docker container."""
    print("=" * 60)
    print("Running MCP Client in Docker Container")
    print("=" * 60)
    print()

    # Check if .env file exists
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("✗ .env file not found")
        print("Please run start_server.py first to generate API key")
        sys.exit(1)

    # Load environment variables from .env
    load_dotenv(env_path)
    api_key = os.getenv("NEO4J_API_KEY")

    if not api_key:
        print("✗ NEO4J_API_KEY not found in .env")
        print("Please run start_server.py first to generate API key")
        sys.exit(1)

    print(f"✓ Loaded API key from .env: {api_key[:16]}...")
    print()

    # Build Docker command to run the test client
    # Use Python official image with network=host to access localhost:8001
    script_dir = Path(__file__).parent.absolute()
    script_name = Path(__file__).name

    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "-i",
        "--network=host",  # Use host network to access localhost:8001
        "-v",
        f"{script_dir}:/app",  # Mount the test_api directory
        "-w",
        "/app",
        "-e",
        f"NEO4J_API_KEY={api_key}",  # Pass API key to container
        "python:3.11-slim",
        "sh",
        "-c",
        f"pip install -q fastmcp python-dotenv && python {script_name}",
    ]

    print("Starting Docker container...")
    print(f"Command: {' '.join(docker_cmd[:8])} ... python:3.11-slim ...")
    print()

    try:
        # Run Docker container
        result = subprocess.run(
            docker_cmd, check=True, text=True, capture_output=False
        )
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Docker execution failed with exit code {e.returncode}")
        print("\nTroubleshooting:")
        print("1. Ensure Docker is installed and running")
        print("2. Ensure the MCP server is running (start_server.py)")
        print("3. Check that the .env file contains a valid API key")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("✗ Docker not found")
        print("Please install Docker: https://docs.docker.com/get-docker/")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Test MCP Neo4j Cypher client with API authentication"
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Run the client in a Docker container instead of locally",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.docker:
        # Run in Docker container
        run_in_docker()
    else:
        # Run locally
        asyncio.run(main())
