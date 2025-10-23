from typing import Any
import httpx
import os
from mcp.server.fastmcp import FastMCP
import base64
from pathlib import Path
from mcp.types import ImageContent, TextContent
import subprocess

# Initialize FastMCP server
mcp = FastMCP("airfoil_mcp")


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


@mcp.tool()
async def generate_mesh(
    working_dir: str, airfoil_profile: str, mesh_cells: int, y_plus: float, mach: float, n_ffds: int
):
    """
    Generate the airfoil mesh and output the mesh image called airfoil_mesh.png

    Args:
        working_dir: !mandatory! Users need to provide the absolute path for the working directory. If not, ask users to set it.
        airfoil_profile: The name of the airfoil profile, such as rae2822 or naca0012 (no spaces and all lower case letters). Default: naca0012
        mesh_cells: The number of mesh cells to generate. Default: 5000
        y_plus: the normalized near wall mesh size to capture boundary layer. Default: 50
        mach: Mach number to estimate the near wall mesh size value. Default: 0.1
        n_ffds: the Number of FFD control points to change the airfoil geometry. Default: 10
    """
    os.chdir(working_dir)
    cmd = [
        "docker",
        "run",
        "--rm",
        "-u",
        "dafoamuser",
        "-v",
        f"{os.getcwd()}:/home/dafoamuser/mount",
        "-w",
        "/home/dafoamuser/mount",
        "dafoam/opt-packages:claude",
        "bash",
        "-lc",
        '. /home/dafoamuser/dafoam/loadDAFoam.sh && python generate_mesh.py -airfoil_profile=%s -mesh_cells=%i -y_plus=%f -mach=%f -n_ffds=%i && plot3dToFoam -noBlank volumeMesh.xyz && autoPatch 30 -overwrite && createPatch -overwrite  && renumberMesh -overwrite && transformPoints -scale "(1 1 0.01)" && pvpython plot_mesh.py'
        % (airfoil_profile, mesh_cells, y_plus, mach, n_ffds),
    ]
    subprocess.run(cmd, check=False)

    image_path = working_dir + "/airfoil_mesh.png"

    return display_image(image_path)


@mcp.tool()
async def download_dafoam_tutorials(working_dir: str):
    """
    Download the DAFoam tutorial. We need to force Users to set the working_dir. If not, ask users to set it.

    Args:
        working_dir: Users need to provide the absolute path for the working directory, where we will download the tutorial files from github
    """
    os.chdir(working_dir)
    os.system("wget https://github.com/DAFoam/tutorials/archive/refs/heads/main.tar.gz")


if __name__ == "__main__":
    mcp.run(transport="stdio")
