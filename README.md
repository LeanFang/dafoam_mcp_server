# dafoam_mcp_server

## MacOS/Linux

Build an MCP server

- Install Python 3.10+.
- Install uv by running: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Download the dafoam_mcp_server and cd into a subfolder, e.g., airfoils
- Run the following commands to initialize some environments:
  <pre>
  uv venv
  source .venv/bin/activate
  uv add "mcp[cli]" httpx
  </pre> 
- Start the server by running: `uv run airfoil_mcp.py`

Connect the MCP server to a client (Claude)

Open Claude's configuration file using VSCode:  `code ~/Library/Application\ Support/Claude/claude_desktop_config.json`

Add these into the .json file

<pre>
{
  "mcpServers": {
    "airfoil_mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute_path_to_dafoam_mcp_server/airfoils",
        "run",
        "airfoil_mcp.py"
      ]
    }
  }
}
</pre>