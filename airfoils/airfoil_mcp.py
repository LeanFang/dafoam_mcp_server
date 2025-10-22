from typing import Any
import httpx
import os
from mcp.server.fastmcp import FastMCP
import base64
from pathlib import Path
from mcp.types import ImageContent, TextContent

# Initialize FastMCP server
mcp = FastMCP("airfoil_mcp")


@mcp.tool()
async def download_dafoam_tutorials(working_dir: str):
    """
    Download the DAFoam tutorial. We need to force Users to set the working_dir. If not, ask users to set it.

    Args:
        working_dir: Users need to provide the absolute path for the working directory, where we will download the tutorial files from github
    """
    os.chdir(working_dir)
    os.system("wget https://github.com/DAFoam/tutorials/archive/refs/heads/main.tar.gz")


@mcp.tool()
def display_image(image_path: str):
    """
    Display an image from the filesystem

    Args:
        image_path: Path to the image file. Ask users to set the absolute path.
    """
    path = Path(image_path).expanduser()

    if not path.exists():
        return TextContent(type="text", text=f"Error: File not found: {path}")

    if not path.is_file():
        return TextContent(type="text", text=f"Error: Not a file: {path}")

    # Read and encode image
    with open(path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Determine MIME type
    suffix = path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(suffix, "image/png")

    # Return as ImageContent
    return ImageContent(type="image", data=image_data, mimeType=mime_type)


if __name__ == "__main__":
    mcp.run(transport="stdio")
