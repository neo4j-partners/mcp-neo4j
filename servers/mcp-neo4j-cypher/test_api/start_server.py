"""
Start the MCP Neo4j Cypher server with API key authentication.

This script:
1. Loads Neo4j connection info from .env
2. Generates a secure random API key
3. Updates .env with the API key
4. Starts the server with HTTP transport

Usage:
  python start_server.py           # Run server locally with uv
  python start_server.py --docker  # Run server in Docker container
"""

import argparse
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


def update_env_with_api_key(api_key: str, env_path: Path) -> None:
    """Update .env file with generated API key while preserving Neo4j connection info."""
    if not env_path.exists():
        print(f"✗ .env file not found at {env_path}")
        print(f"Please copy .env.sample to .env and add your Neo4j credentials")
        sys.exit(1)

    # Load existing .env to preserve Neo4j connection info
    load_dotenv(env_path)

    # Get Neo4j connection info from existing .env
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

    if not all([neo4j_uri, neo4j_username, neo4j_password]):
        print("✗ Missing Neo4j connection info in .env file")
        print("Please ensure NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD are set")
        sys.exit(1)

    # Create updated .env with all configuration
    env_content = f"""# Neo4j Connection (from your cloud instance)
NEO4J_URI={neo4j_uri}
NEO4J_USERNAME={neo4j_username}
NEO4J_PASSWORD={neo4j_password}
NEO4J_DATABASE={neo4j_database}

# Server Configuration (for testing)
NEO4J_TRANSPORT=http
NEO4J_MCP_SERVER_HOST=127.0.0.1
NEO4J_MCP_SERVER_PORT=8001
NEO4J_MCP_SERVER_PATH=/mcp/

# API Key (generated for this server session)
NEO4J_API_KEY={api_key}
"""
    env_path.write_text(env_content)
    print(f"✓ Updated .env file with API key")


def start_server(api_key: str) -> None:
    """Start the MCP server using uv."""
    print("Starting MCP Neo4j Cypher server...")

    # Load environment variables from .env file
    project_dir = Path(__file__).parent.parent
    load_dotenv(Path(__file__).parent / ".env")

    # Create environment dict with values from .env
    env = os.environ.copy()
    env_updates = {
        "NEO4J_URI": os.getenv("NEO4J_URI"),
        "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
        "NEO4J_DATABASE": os.getenv("NEO4J_DATABASE"),
        "NEO4J_TRANSPORT": os.getenv("NEO4J_TRANSPORT"),
        "NEO4J_MCP_SERVER_HOST": os.getenv("NEO4J_MCP_SERVER_HOST"),
        "NEO4J_MCP_SERVER_PORT": os.getenv("NEO4J_MCP_SERVER_PORT"),
        "NEO4J_MCP_SERVER_PATH": os.getenv("NEO4J_MCP_SERVER_PATH"),
        "NEO4J_API_KEY": api_key,  # Use the generated API key directly
    }

    # Filter out None values and update env
    env.update({k: v for k, v in env_updates.items() if v is not None})

    print(f"Server URL: http://{env.get('NEO4J_MCP_SERVER_HOST')}:{env.get('NEO4J_MCP_SERVER_PORT')}{env.get('NEO4J_MCP_SERVER_PATH')}")
    print(f"API Key: {api_key}")
    print("\nPress Ctrl+C to stop the server\n")

    # Start server process (foreground)
    try:
        subprocess.run(
            ["uv", "run", "mcp-neo4j-cypher"],
            cwd=project_dir,
            env=env,
        )
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")


def start_server_docker(api_key: str) -> None:
    """Start the MCP server in a Docker container."""
    print("Starting MCP Neo4j Cypher server in Docker...")
    print()

    # Load environment variables from .env file
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)

    # Get project directory (parent of test_api)
    project_dir = Path(__file__).parent.parent

    # Build Docker image
    image_name = "mcp-neo4j-cypher:dev-latest"
    print(f"Building Docker image: {image_name}")
    print(f"Building from: {project_dir}")
    print()

    try:
        subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            cwd=project_dir,
            check=True,
        )
        print(f"✓ Docker image built successfully")
        print()
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to build Docker image (exit code {e.returncode})")
        sys.exit(1)
    except FileNotFoundError:
        print("✗ Docker not found")
        print("Please install Docker: https://docs.docker.com/get-docker/")
        sys.exit(1)

    # Prepare environment variables for container
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

    # For Docker on Mac/Windows, need to use special hostname to access host
    # Replace localhost/127.0.0.1 with host.docker.internal
    if neo4j_uri and ("localhost" in neo4j_uri or "127.0.0.1" in neo4j_uri):
        neo4j_uri = neo4j_uri.replace("localhost", "host.docker.internal")
        neo4j_uri = neo4j_uri.replace("127.0.0.1", "host.docker.internal")
        print(f"⚠️  Modified Neo4j URI for Docker: {neo4j_uri}")
        print()

    server_host = "0.0.0.0"  # Bind to all interfaces in container
    server_port = os.getenv("NEO4J_MCP_SERVER_PORT", "8001")
    server_path = os.getenv("NEO4J_MCP_SERVER_PATH", "/mcp/")

    print(f"Server URL: http://127.0.0.1:{server_port}{server_path}")
    print(f"API Key: {api_key}")
    print("\nPress Ctrl+C to stop the server\n")

    # Run Docker container
    docker_run_cmd = [
        "docker",
        "run",
        "--rm",
        "-p",
        f"{server_port}:{server_port}",  # Map port to host
        "-e",
        f"NEO4J_URI={neo4j_uri}",
        "-e",
        f"NEO4J_USERNAME={neo4j_username}",
        "-e",
        f"NEO4J_PASSWORD={neo4j_password}",
        "-e",
        f"NEO4J_DATABASE={neo4j_database}",
        "-e",
        "NEO4J_TRANSPORT=http",
        "-e",
        f"NEO4J_MCP_SERVER_HOST={server_host}",
        "-e",
        f"NEO4J_MCP_SERVER_PORT={server_port}",
        "-e",
        f"NEO4J_MCP_SERVER_PATH={server_path}",
        "-e",
        f"NEO4J_API_KEY={api_key}",
        image_name,
    ]

    try:
        subprocess.run(docker_run_cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Start MCP Neo4j Cypher server with API authentication"
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Run the server in a Docker container instead of locally",
    )
    return parser.parse_args()


def main() -> None:
    """Main server startup."""
    args = parse_args()

    print("=" * 60)
    print("MCP Neo4j Cypher Server - HTTP Mode with Authentication")
    print("=" * 60)
    print()

    # Setup paths
    env_path = Path(__file__).parent / ".env"

    # Generate and save API key
    api_key = generate_api_key()
    update_env_with_api_key(api_key, env_path)

    # Start server
    if args.docker:
        start_server_docker(api_key)
    else:
        start_server(api_key)


if __name__ == "__main__":
    main()
