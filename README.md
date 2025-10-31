# dafoam_mcp_server

## MacOS

Build an MCP server (airfoils)

- Download and install the Docker Desktop from https://docs.docker.com/desktop/setup/install/mac-install. Open Docker Desktop and keep it open.
- Open a terminal and download the DAFoam Docker image:
  <pre>
  docker pull dafoam/opt-packages:latest
  </pre>
- Download the zip file of the dafoam_mcp_server repo from GitHub https://github.com/iDesign-Lab/dafoam_mcp_server/archive/refs/heads/main.zip and unzip it. Windows users can't use the git clone command because it will change the file format for the bash script.
  
- Open a terminal and and cd into dafoam_mcp_server/airfoils, then run the following to build the dafoam_mcp_server docker image
  <pre>
  docker build -t dafoam_mcp_server . 
  </pre>

Connect the DAFoam MCP server to a client (Claude).

- Download and install Claude app from https://www.claude.com/download. Open the Claude app (you may need to sign up for an account).
- In Claude's app, locate to the bottom left and click: "Your Account->Settings->Developer". Then, click "Edit Config", this will open a directory where Claude saves your claude_desktop_config.json file. 
- Open claude_desktop_config.json and add these into it. Here `abs_path_to_your_dafoam_mcp_server` is the absolute path of the dafoam_mcp_server repo on your local MacOS system, e.g., `/Users/phe/Desktop/dafoam_mcp_server` for MacOS or `C:\\Users\phe\dafoam_mcp_server` for Windows. NOTE: the DAFoam MCP will make modifications ONLY in this dafoam_mcp_server folder. Also note that the dafoam_mcp_server.py should be in your /abs_path_to_your_dafoam_mcp_server directory.

  <pre>
  {
    "mcpServers": {
      "dafoam_mcp_server": {
        "command": "docker",
        "args": [
          "run", 
          "-i", 
          "--rm",
          "-p",
          "8001:8001",
          "-v", 
          "/abs_path_to_your_dafoam_mcp_server:/home/dafoamuser/mount",
          "dafoam_mcp_server"
        ]
      }
    }
  }
  </pre>

- IMPORTANT! You need to close and re-open the Claude app to make the new MCP effective.

- You can ask questions such as "Generate a mesh for the NACA0012 airfoil". Once Claude generates the mesh, you can view it by expanding the "Generate Mesh" tab in the chat window. You can also ask it to zoom in to view mesh details, like "Zoom in to the trailing edge" or "Zoom in more".

NOTE: If you see an error, the logs file are in ~/Library/Logs/Claude/mcp-server-dafoam_mcp_server.log 


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


