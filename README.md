# dafoam_mcp_server

## MacOS/Linux

Build an MCP server

- Install Python 3.10+ and install relevant python packages `pip3 install mcp httpx`
- Install uv by running: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Download the dafoam_mcp_server and cd into a subfolder, e.g., airfoils
- Run the following commands to initialize some environments:
  <pre>
  uv init .
  uv venv
  source .venv/bin/activate
  uv add "mcp[cli]" httpx
  </pre> 
- Start the server by running: `uv run airfoil_mcp.py`

Connect the MCP server to a client (Claude)

Open Claude's configuration file using VSCode:  `code ~/Library/Application\ Support/Claude/claude_desktop_config.json`

Add these into the .json file. Here `absolute_path_to_dafoam_mcp_server` is the absolute path of the dafoam_mcp_server repo and `/Users/phe/.local/bin/uv` is the absolute path of the uv command (you can get it from `which uv`). Claude may not have access to your system's PATH variable, so we may need to use the absolute paths.

<pre>
{
  "mcpServers": {
    "airfoil_mcp": {
      "command": "/Users/phe/.local/bin/uv",
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

You need to re-open Claude to make the new MCP effective.

The logs file are in ~/Library/Logs/Claude


## Windows 11

Build an MCP server

- Install uv for Python. Open any terminal such as a Command Prompt, and run `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` Restart the terminal so that uv command can be used
- Make sure your Python is at least 3.10+. You can check your Python version using uv by `uv python list`, and install by `uv python install` If you are using a Anaconda PowerShell Prompt, you can check by `python --version`, and this requirement is usually already satisfied
- Download the dafoam_mcp_server and cd into the subfolder airfoils
- Run the following commands to initialize some environments:
  <pre>
  uv init .
  uv venv
  .venv\Scripts\activate
  uv add mcp[cli] httpx
  </pre> 
- Start the server by running: `uv run airfoil_mcp.py`
- Do not close this terminal as it would close the MCP server

Connect the MCP server to a client (Claude)

Open Claude's configuration file using VSCode (run in any terminal):  `code $env:AppData\Claude\claude_desktop_config.json`

Add these into the .json file. Here `absolute_path_to_dafoam_mcp_server` is the absolute path of the dafoam_mcp_server repo and `C:\\Users\\your_user_name\\.local\\bin\\uv.exe` is the absolute path of the uv command (you can get it from `where uv` in a Command Prompt). Claude may not have access to your system's PATH variable, so we may need to use the absolute paths. Remember to use double backslashes `\\` in the JSON path for Windows 

<pre>
{
  "mcpServers": {
    "airfoil_mcp": {
      "command": "C:\\Users\\your_user_name\\.local\\bin\\uv.exe",
      "args": [
        "--directory",
        "C:\\absolute_path_to_dafoam_mcp_server\\airfoils",
        "run",
        "airfoil_mcp.py"
      ]
    }
  }
}
</pre>

You need to re-open Claude to make the new MCP effective.

The logs file are in %APPDATA%\Claude\logs


[WiP]


