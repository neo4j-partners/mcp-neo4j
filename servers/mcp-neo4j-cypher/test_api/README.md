# API Authentication Demo

Simple demonstration of API key authentication for the mcp-neo4j-cypher server.

## Setup

1. **Install dependencies**
   ```bash
   cd /path/to/mcp-neo4j/servers/mcp-neo4j-cypher
   uv sync
   ```

2. **Configure environment**
   ```bash
   cd test_api
   cp .env.sample .env
   # Edit .env and add your Neo4j credentials
   ```

## Running

**Terminal 1 - Start the server:**
```bash
cd test_api
uv run python start_server.py
```

**Terminal 2 - Run the sample client:**
```bash
cd test_api
uv run python test_auth.py
```

## Files

- `start_server.py` - Generates API key and starts the MCP server with HTTP transport
- `test_auth.py` - Sample FastMCP client demonstrating authentication and tool usage
- `.env.sample` - Environment variable template
- `.env` - Your configuration (auto-generated, not in git)

## How It Works

1. `start_server.py` generates a secure random API key and saves it to `.env`
2. The server starts with HTTP transport and Bearer token authentication
3. `test_auth.py` loads the API key from `.env` and connects to the server
4. The client lists available tools and calls `get_neo4j_schema` to retrieve the database schema

## Troubleshooting

**Server won't start:**
- Check port 8001 is available: `lsof -i :8001`
- Verify Neo4j credentials in `.env`

**Client gets 401 Unauthorized:**
- Ensure `start_server.py` is running
- Check `.env` has `NEO4J_API_KEY` set

**Client can't connect:**
- Verify server is running on http://127.0.0.1:8001/mcp/
- Check firewall settings
