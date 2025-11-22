# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Approach for New Features and Changes

**CRITICAL: Always start simple and plan before coding.**

When the user requests new features or changes:

1. **Start Simple**: Begin with the simplest possible approach. Avoid over-engineering.

2. **Multiple Options**: If there are multiple ways to implement something, write a very basic list of options (2-4 bullet points each) and ask the user which approach they prefer. Do NOT assume.

3. **Proposal First, Code Later**:
   - Always write a proposal using only English requirements and descriptions
   - NO code in the proposal - only describe what needs to be done
   - Break down into clear phases

4. **Implementation Plan Structure**:
   - Each phase should have a numbered todo list
   - Last item in the plan must be: "Code review and testing"
   - Keep phases small and achievable

5. **Think Deeply**: Take extra time to think through the implications, edge cases, and simplest path forward.

6. **Afternoon-Sized Changes**: Greatly simplify proposals so they can be completed in an afternoon. This is NOT production-scale work - keep it really basic and focused.

## Repository Overview

This is a monorepo containing multiple Model Context Protocol (MCP) servers for Neo4j graph database integration. Each server provides different capabilities for interacting with Neo4j databases and the Neo4j Aura cloud platform through LLM-powered assistants like Claude Desktop.

## Architecture

### Server Structure

The repository contains four independent Python MCP servers under `servers/`:

1. **mcp-neo4j-cypher** - Natural language to Cypher query translation
   - Executes read/write Cypher queries on Neo4j databases
   - Schema inspection with configurable sampling
   - Query timeout and token limit controls
   - Location: `servers/mcp-neo4j-cypher/`

2. **mcp-neo4j-memory** - Knowledge graph memory storage
   - Persistent entity and relationship storage
   - Multi-session memory across conversations
   - Entity/observation management
   - Location: `servers/mcp-neo4j-memory/`

3. **mcp-neo4j-cloud-aura-api** - Neo4j Aura cloud instance management
   - Create, update, delete Aura instances
   - Instance scaling and configuration
   - Tenant/project management
   - Location: `servers/mcp-neo4j-cloud-aura-api/`

4. **mcp-neo4j-data-modeling** - Interactive graph data model design
   - Create and validate graph schemas
   - Visualize with Mermaid diagrams
   - Import/export from Arrows.app
   - Generate Cypher ingest queries
   - Location: `servers/mcp-neo4j-data-modeling/`

### Transport Modes

All servers support three transport protocols:
- **STDIO** (default): For local development and Claude Desktop integration
- **HTTP**: For cloud deployments, microservices, and remote access
- **SSE**: Legacy support for Server-Sent Events web clients

### Common Patterns

Each server follows a similar structure:
- `src/mcp_neo4j_*/server.py` - Main MCP server implementation using FastMCP
- `src/mcp_neo4j_*/utils.py` - Utility functions
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests (stdio, http, sse transport tests)
- `pyproject.toml` - Dependencies and build configuration
- `Dockerfile` - Container image for cloud deployment
- `Makefile` - Common development commands

## Development Commands

### Setup Development Environment

Each server is an independent Python project using `uv` for dependency management:

```bash
# Install uv if not already installed
pip install uv
# OR
brew install uv

# Navigate to a server directory
cd servers/mcp-neo4j-cypher

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate     # On Windows

# Install with dev dependencies
uv sync
# OR
uv pip install -e ".[dev]"
```

### Testing

Each server has a Makefile with standard targets:

```bash
# Run unit tests only
make test-unit
# OR
uv run pytest tests/unit/ -v

# Run integration tests only
make test-integration
# OR
uv run pytest tests/integration/ -v

# Run all tests
make test-all
# OR
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/integration/test_http_transport_IT.py -v
```

### Code Formatting

```bash
# Format and lint code
make format
# This runs:
# - ruff check --select I . --fix  (import sorting)
# - ruff check --fix .             (linting)
# - ruff format .                   (formatting)
```

### Docker Development

```bash
# Build Docker image locally
docker build -t mcp-neo4j-cypher:dev-latest .

# Run Docker container with HTTP transport
docker run -p 8000:8000 \
  -e NEO4J_URI="bolt://host.docker.internal:7687" \
  -e NEO4J_USERNAME="neo4j" \
  -e NEO4J_PASSWORD="password" \
  -e NEO4J_TRANSPORT="http" \
  mcp-neo4j-cypher:dev-latest

# For stdio transport (Claude Desktop integration)
docker run -i --rm \
  -e NEO4J_URI="bolt://host.docker.internal:7687" \
  -e NEO4J_USERNAME="neo4j" \
  -e NEO4J_PASSWORD="password" \
  -e NEO4J_TRANSPORT="stdio" \
  mcp-neo4j-cypher:dev-latest
```

## Key Technical Details

### MCP Framework

All servers use **FastMCP** (from `fastmcp` package), which provides:
- Decorator-based tool registration: `@mcp.tool()`
- Multiple transport support (stdio, http, sse)
- Built-in security middleware (CORS, TrustedHost)
- Stateless HTTP mode for cloud deployment
- Pydantic integration for type validation

### Neo4j Integration

Servers use the official `neo4j` Python driver:
- Async driver pattern: `AsyncGraphDatabase.driver()`
- Environment variable configuration: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`
- Query execution with timeout controls
- Schema inspection via APOC procedures (e.g., `apoc.meta.schema()`)

### Namespacing

All servers support namespacing to run multiple instances:
- CLI flag: `--namespace myapp`
- Environment variable: `NEO4J_NAMESPACE=myapp`
- Result: Tools prefixed as `myapp-tool_name`

### Security Middleware

HTTP transport includes security protections:
- **DNS Rebinding Protection**: TrustedHostMiddleware validates Host headers (default: localhost only)
- **CORS Protection**: CORSMiddleware controls cross-origin requests (default: no origins allowed)
- Configuration via `--allowed-hosts` / `--allow-origins` flags or environment variables
- Production deployments should explicitly configure allowed hosts and origins

## Testing Strategy

### Integration Tests

Integration tests use **testcontainers** to spin up Neo4j instances:
- Tests run against real Neo4j database containers
- Located in `tests/integration/`
- Test all transport modes: stdio, http, sse
- Clean up automatically after tests

### Unit Tests

Unit tests mock external dependencies:
- Located in `tests/unit/`
- Test individual functions and utilities
- Fast execution without external dependencies

## Common Workflows

### Adding a New Tool

When adding a new tool to any server:

1. Add the tool function in `server.py` using `@mcp.tool()` decorator
2. Include proper type hints and docstrings
3. Add namespace prefix: `name=namespace_prefix + "tool_name"`
4. Include ToolAnnotations for hints (readOnly, destructive, idempotent)
5. Add unit tests in `tests/unit/test_server.py`
6. Add integration tests in `tests/integration/test_server_tools_IT.py`
7. Update the server's README.md with tool documentation

### Modifying Transport Configuration

Transport configuration is handled in `__init__.py`:
- Parse CLI arguments with argparse
- Read environment variables as fallbacks
- Create Neo4j driver with connection settings
- Call `create_mcp_server()` with config
- Run appropriate transport: `mcp.run()`, `mcp.run_sse()`, or `mcp.run_http()`

### Publishing Updates

Each server is published independently to PyPI:
- Version specified in `pyproject.toml`
- GitHub Actions workflows automate publishing: `.github/workflows/publish-*.yml`
- Docker images published to Docker Hub
- Update CHANGELOG.md for each server when releasing

## Environment Variables Reference

Common across all servers:
- `NEO4J_URI` - Neo4j connection URI (bolt:// or neo4j+s://)
- `NEO4J_USERNAME` - Database username
- `NEO4J_PASSWORD` - Database password
- `NEO4J_DATABASE` - Database name (default: "neo4j")
- `NEO4J_TRANSPORT` - Transport mode: stdio, http, or sse
- `NEO4J_NAMESPACE` - Tool name prefix for multi-instance setups
- `NEO4J_MCP_SERVER_HOST` - HTTP/SSE bind host (default: 127.0.0.1)
- `NEO4J_MCP_SERVER_PORT` - HTTP/SSE port (default: 8000)
- `NEO4J_MCP_SERVER_PATH` - HTTP/SSE URL path (default: /api/mcp/ or /mcp/)
- `NEO4J_MCP_SERVER_ALLOWED_HOSTS` - Comma-separated allowed Host headers
- `NEO4J_MCP_SERVER_ALLOW_ORIGINS` - Comma-separated CORS origins

Cypher server specific:
- `NEO4J_READ_TIMEOUT` - Query timeout in seconds (default: 30)
- `NEO4J_RESPONSE_TOKEN_LIMIT` - Max response tokens for read queries
- `NEO4J_READ_ONLY` - Disable write queries (true/false)
- `NEO4J_SCHEMA_SAMPLE_SIZE` - Node sample size for schema inspection (default: 1000)

Aura manager specific:
- `NEO4J_AURA_CLIENT_ID` - Aura API client ID
- `NEO4J_AURA_CLIENT_SECRET` - Aura API client secret

## Project Dependencies

All servers require Python 3.10+:
- **fastmcp** - MCP server framework with multi-transport support
- **neo4j** - Official Neo4j Python driver (most servers)
- **pydantic** - Data validation and settings management
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **ruff** - Fast Python linter and formatter
- **pyright** - Static type checker
- **testcontainers** - Docker container integration tests

Data modeling server also uses:
- **rdflib** - OWL/RDF parsing for ontology import/export

## Claude Desktop Configuration

For local development with Claude Desktop:

```json
{
  "mcpServers": {
    "neo4j-cypher-dev": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-neo4j/servers/mcp-neo4j-cypher",
        "run",
        "mcp-neo4j-cypher",
        "--transport",
        "stdio"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password",
        "NEO4J_DATABASE": "neo4j"
      }
    }
  }
}
```

Replace `/path/to/mcp-neo4j` with your actual repository path.

## Cloud Deployment

All servers are containerized and ready for cloud deployment:
- AWS ECS Fargate
- Azure Container Apps
- Google Cloud Run
- See README-Cloud.md for detailed deployment guides
- Use HTTP transport for cloud deployments
- Configure security middleware (CORS, TrustedHost) appropriately
- Use `mcp-remote` or similar proxy to connect Claude Desktop to remote servers
