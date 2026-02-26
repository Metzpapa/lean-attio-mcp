# lean-attio-mcp

A lean Attio CRM server for the [Model Context Protocol](https://modelcontextprotocol.io). 1,400 lines. No abstractions. Just tools.

Built because the existing options are either 98,000 lines of strategy patterns and factory abstractions, or hosted servers that return raw JSON blobs that eat your context window.

This server gives AI agents clean, formatted access to Attio's full REST API. Every response is compressed text, not raw JSON.

## What's in the box

**19 tools** across 5 categories:

| Category | Tools | What they do |
|----------|-------|-------------|
| **Records** | `search_records`, `get_record`, `create_or_update_record`, `update_record`, `list_record_entries` | Find, read, and write companies, people, and deals |
| **Pipelines** | `list_lists`, `create_list`, `query_list_entries`, `create_or_update_entry`, `delete_entry` | Manage sales pipelines and any custom list |
| **Schema** | `list_attributes`, `create_attribute`, `list_select_options`, `create_select_option` | Add fields, pipeline stages, and dropdown options |
| **Notes** | `create_note`, `list_notes` | Attach notes to any record |
| **Tasks** | `create_task`, `list_tasks`, `update_task` | Follow-up reminders with deadlines and linked records |

## Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- An [Attio API key](https://app.attio.com/settings/api-keys) with appropriate scopes

### Install

```bash
git clone https://github.com/Metzpapa/lean-attio-mcp.git
cd lean-attio-mcp
uv sync
```

### Connect to Claude Code

Add to your `.mcp.json` (project-level or `~/.claude/.mcp.json` for global):

```json
{
  "mcpServers": {
    "attio": {
      "command": "uv",
      "args": ["--directory", "/path/to/lean-attio-mcp", "run", "attio-mcp"],
      "env": {
        "ATTIO_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Connect to Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "attio": {
      "command": "uv",
      "args": ["--directory", "/path/to/lean-attio-mcp", "run", "attio-mcp"],
      "env": {
        "ATTIO_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Example responses

What the agent actually sees (not raw JSON):

```
# Search
Found 3 companies:
1. OwnerRez (ownerrez.com) — ID: ed9b4608-...
2. Breezeway (breezeway.io) — ID: a1b2c3d4-...
3. Guesty (guesty.com) — ID: e5f6a7b8-...

# Record detail
Company: OwnerRez (ID: ed9b4608-...)
  Domains: ownerrez.com
  Description: Property management software for vacation rentals
  Categories: Travel & Leisure, B2B, Technology, SAAS
  Foundation Date: 2009-01-01

# Pipeline entries
Sales pipeline (5 entries):
1. OwnerRez — Stage: Negotiation — Next Step: Waiting on Paul
2. Breezeway — Stage: Negotiation — Next Step: Waiting on Peter
3. Guesty — Stage: Proposal — Next Step: Partnership form pending
```

## Adding a tool

The whole point of this server is that it's easy to extend. Here's the pattern:

### 1. Add the handler to the right `tools_*.py` file

```python
# In tools_records.py (or whichever category fits)

# Add the tool definition to TOOLS list
TOOLS = [
    # ... existing tools ...
    {
        "name": "my_new_tool",
        "description": "What it does",
        "inputSchema": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "..."},
            },
            "required": ["param1"],
        },
    },
]

# Add the handler in the handle() function
def handle(name: str, args: dict) -> str:
    # ... existing handlers ...
    elif name == "my_new_tool":
        return _my_new_tool(args)

# Write the implementation
def _my_new_tool(args: dict) -> str:
    data = client.get("/some/attio/endpoint", params={...})
    # Format the response as clean text
    return f"Result: {data}"
```

### 2. That's it

The server auto-discovers tools from the `TOOLS` list in each module. No registration, no config, no strategy patterns.

## Project structure

```
src/attio_mcp/
  server.py        # MCP server setup, tool dispatch (80 lines)
  client.py        # Attio API client with httpx (75 lines)
  formatting.py    # Value extraction + response formatting (185 lines)
  tools_records.py # Company/people/deal CRUD (260 lines)
  tools_lists.py   # Pipeline management (262 lines)
  tools_schema.py  # Attributes and select options (249 lines)
  tools_notes.py   # Notes (101 lines)
  tools_tasks.py   # Tasks with deadlines (173 lines)
```

## Why this exists

The Attio API returns deeply nested JSON where every field value is an array of objects with metadata. A single company record can be 200+ lines of JSON. This server unwraps all of that into clean text that fits in an LLM's context window.

The [existing community MCP server](https://github.com/kesslerio/attio-mcp-server) does this too, but through 98,000 lines of TypeScript with strategy patterns, factory abstractions, and a 280-line dispatcher switch statement. It's well-engineered for a general-purpose product. This is not that. This is a tool.

Attio's [official hosted MCP](https://docs.attio.com/mcp/overview) is solid but can't create lists, add attributes, or configure pipeline stages. It also requires OAuth (not API keys) and runs on Attio's servers.

This server runs locally, uses a simple API key, and covers the full REST API surface including schema configuration.

## Required API scopes

Your Attio API key needs these scopes:
- `record_permission:read-write`
- `object_configuration:read-write`
- `list_configuration:read-write`
- `list_entry:read-write`
- `note:read-write`
- `task:read-write`
- `comment:read-write`
- `user_management:read`

## License

MIT
