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
async def airfoil_run_cfd_simulation(cpu_cores: int, angle_of_attack: float):
    """
    Airfoil module: Run CFD simulation to compute airfoil flow fields such as velocity, pressure, and temperature.

    Args:
        cpu_cores: The number of CPU cores to use. >1 means running the simulation in parallel. Default: 1
        angle_of_attack: The angle of attack boundary condition at the far field for the airfoil. Default: 3.0
    """

    # Run DAFoam commands directly in this container with mpirun
    base_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd /home/dafoamuser/mount/airfoils && "
        f"mpirun -np {cpu_cores} python run_script.py -task=run_model -angle_of_attack={angle_of_attack} > log-cfd-simulation.txt"
    )

    # Add reconstructPar and cleanup only if parallel (cpu_cores > 1)
    if cpu_cores > 1:
        bash_command = f"{base_command} && reconstructPar && rm -rf processor* && pvpython plot_flow_field.py && pvpython plot_pressure_profile.py"
    else:
        bash_command = f"{base_command} && pvpython plot_flow_field.py && pvpython plot_pressure_profile.py"

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path1 = "/home/dafoamuser/mount/airfoils/flow_field.jpeg"
    image_path2 = "/home/dafoamuser/mount/airfoils/pressure_profile.jpeg"

    return [display_image(image_path1), display_image(image_path2)]


@mcp.tool()
async def airfoil_view_flow_field_details(x_location: float, y_location: float, zoom_in_scale: float, variable: str):
    """
    Airfoil module: Allow users to view the details of a selected flow field variable. The airfoil CFD simulation must have been done.

    Args:
        x_location: where to zoom in to view the airfoil mesh details in the x direction. Leading edge: x_location=0, mid chord: x_location=0.5, and trailing edge: x_location=1. Default: 0.5
        y_location: where to zoom in to view the airfoil mesh details in the y direction. Upper surface: y_location>0 (about 0.1), lower surface: y_location<0 (about -0.1). Default: 0
        zoom_in_scale: how much to zoom in to visualize the mesh. Set a smaller zoom_in_scale if users need zoom in more. Set a larger zoom_in_scale if users need to zoom out more. Default: 0.5
        variable: which flow field variable to visualize. Options are "U": velocity, "T": temperature, "p": pressure, "nut": turbulence viscosity (turbulence variable). Default: "p"
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd /home/dafoamuser/mount/airfoils && "
        f"pvpython plot_flow_field.py -x_location={x_location} -y_location={y_location} -zoom_in_scale={zoom_in_scale} -variable={variable}"
    )

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path = "/home/dafoamuser/mount/airfoils/flow_field.jpeg"

    if not os.path.exists(image_path):
        return TextContent(
            type="text",
            text=f"Image not found!\n\nStdout:\n{result.stdout}\n\nStderr:\n{result.stderr}",
        )

    return display_image(image_path)


@mcp.tool()
async def airfoil_view_mesh_details(x_location: float, y_location: float, zoom_in_scale: float):
    """
    Airfoil module: Allow users to view detail airfoil meshes. The mesh must have been generated in airfoils

    Args:
        x_location: where to zoom in to view the airfoil mesh details in the x direction. Leading edge: x_location=0, mid chord: x_location=0.5, and trailing edge: x_location=1. Default: 0.5
        y_location: where to zoom in to view the airfoil mesh details in the y direction. Upper surface: y_location>0 (about 0.1), lower surface: y_location<0 (about -0.1). Default: 0
        zoom_in_scale: how much to zoom in to visualize the mesh. Set a smaller zoom_in_scale if users need zoom in more. Set a larger zoom_in_scale if users need to zoom out more. Default: 0.5
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd /home/dafoamuser/mount/airfoils && "
        f"pvpython plot_mesh.py -x_location={x_location} -y_location={y_location} -zoom_in_scale={zoom_in_scale}"
    )

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path = "/home/dafoamuser/mount/airfoils/airfoil_mesh.jpeg"

    if not os.path.exists(image_path):
        return TextContent(
            type="text",
            text=f"Image not found!\n\nStdout:\n{result.stdout}\n\nStderr:\n{result.stderr}",
        )

    return display_image(image_path)


@mcp.tool()
async def airfoil_generate_mesh(
    airfoil_profile: str, mesh_cells: int, y_plus: float, n_ffd_points: int, mach_ref: float
):
    """
    Airfoil module: Generate the airfoil mesh and output the mesh image called airfoil_mesh.jpeg

    Args:
        airfoil_profile: The name of the airfoil profile, such as rae2822 or naca0012 (no spaces and all lower case letters). Default: naca0012
        mesh_cells: The number of mesh cells to generate. Default: 5000
        y_plus: the normalized near wall mesh size to capture boundary layer. Default: 50
        n_ffd_points: the Number of FFD control points to change the airfoil geometry. Default: 10
        mach_ref: the reference Mach number to estimate the near wall mesh size. Default: 0.1
    """
    # Run DAFoam commands directly in this container with mpirun
    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd /home/dafoamuser/mount/airfoils && "
        f"./Allclean.sh && "
        f"python generate_mesh.py -airfoil_profile={airfoil_profile} -mesh_cells={mesh_cells} -y_plus={y_plus} -n_ffd_points={n_ffd_points} -mach_ref={mach_ref} > log-mesh.txt && "
        f"plot3dToFoam -noBlank volumeMesh.xyz >> log-mesh.txt && "
        f"autoPatch 30 -overwrite >> log-mesh.txt && "
        f"createPatch -overwrite >> log-mesh.txt && "
        f"renumberMesh -overwrite >> log-mesh.txt && "
        f"cp -r 0_orig 0 && "
        f'transformPoints -scale "(1 1 0.01)" >> log-mesh.txt && '
        f"dafoam_plot3dtransform.py scale FFD.xyz FFD.xyz 1 1 0.01 >> log-mesh.txt && "
        f"dafoam_plot3d2tecplot.py FFD.xyz FFD.dat >> log-mesh.txt && "
        f'sed -i "/Zone T=\\"embedding_vol\\"/,\\$d" FFD.dat && '
        f"pvpython plot_mesh.py"
    )

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path = "/home/dafoamuser/mount/airfoils/airfoil_mesh.jpeg"

    return display_image(image_path)


if __name__ == "__main__":
    mcp.run(transport="stdio")
