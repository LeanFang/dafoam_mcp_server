from typing import Any
import httpx
import os
from mcp.server.fastmcp import FastMCP
import base64
from pathlib import Path
from mcp.types import ImageContent, TextContent
import subprocess

# Initialize FastMCP server
mcp = FastMCP("dafoam_mcp_server")


# helper functions
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
async def airfoil_generate_mesh(airfoil_profile: str, mesh_cells: int, y_plus: float, n_ffds: int):
    """
    Airfoil module: Generate the airfoil mesh and output the mesh image called airfoil_mesh.jpeg

    Args:
        airfoil_profile: The name of the airfoil profile, such as rae2822 or naca0012 (no spaces and all lower case letters). Default: naca0012
        mesh_cells: The number of mesh cells to generate. Default: 5000
        y_plus: the normalized near wall mesh size to capture boundary layer. Default: 50
        n_ffds: the Number of FFD control points to change the airfoil geometry. Default: 10
    """
    # Run DAFoam commands directly in this container with mpirun
    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd /home/dafoamuser/mount/airfoils && "
        f"python generate_mesh.py -airfoil_profile={airfoil_profile} -mesh_cells={mesh_cells} -y_plus={y_plus} -n_ffds={n_ffds} && "
        f"plot3dToFoam -noBlank volumeMesh.xyz && "
        f"autoPatch 30 -overwrite && "
        f"createPatch -overwrite && "
        f"renumberMesh -overwrite && "
        f'transformPoints -scale "(1 1 0.01)" && '
        f"dafoam_plot3d2tecplot.py FFD.xyz FFD.dat && "
        f'sed -i "/Zone T=\\"embedding_vol\\"/,\\$d" FFD.dat && '
        f"pvpython plot_mesh.py"
    )

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path = "/home/dafoamuser/mount/airfoils/airfoil_mesh.jpeg"

    if not os.path.exists(image_path):
        return TextContent(
            type="text",
            text=f"Mesh generation completed but image not found.\n\nStdout:\n{result.stdout}\n\nStderr:\n{result.stderr}",
        )

    return display_image(image_path)


if __name__ == "__main__":
    mcp.run(transport="stdio")
