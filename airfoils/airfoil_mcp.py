from typing import Any
import httpx
import os
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("airfoil_mcp")


@mcp.tool()
async def download_dafoam_tutorials(working_dir: str):
    """
    Download the DAFoam tutorial

    Args:
        working_dir: Users need to provide the absolute path for the working directory, where we will download the tutorial files from github
    """
    os.chdir(working_dir)
    os.system("wget https://github.com/DAFoam/tutorials/archive/refs/heads/main.tar.gz")


if __name__ == "__main__":
    mcp.run(transport="stdio")
