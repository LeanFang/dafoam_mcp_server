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

airfoil_path = "/home/dafoamuser/mount/airfoils/"


# helper functions
def display_image(image_path: str):
    """
    Display an image from the filesystem

    Inputs:
        image_path: Path to the image file. Ask users to set the absolute path.
    Outputs:
        The image
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
async def airfoil_run_optimization(
    cpu_cores: int, angle_of_attack: float, mach_number: float, reynolds_number: float, lift_constraint: float
):
    """
    Airfoil module: Run CFD-based aerodynamic optimization.
    Objective: drag coefficient.
    Design variables: airfoil shape and angle of attack.
    Constraints: lift, thickness, volume, and leading edge radius

    Inputs:
        cpu_cores: The number of CPU cores to use. >1 means running the simulation in parallel. Default: 1
        angle_of_attack: The angle of attack (aoa) boundary condition at the far field for the airfoil. Default: 3.0
        mach_number: The Mach number (Ma). mach_number > 0.6: transonic conditions, mach_number < 0.6 subsonic conditions. We should use the same mach number set in the airfoil_generate_mesh call.
        reynolds_number: The Reynolds number, users can also use Re to denote the Reynolds number.
        lift_constraint: The lift constraint. Default: 0.5
    Outputs:
        1. The image of flow field for the optimized design
        2. The image of pressure profile for the optimized design
        3. A dictionary for the airfoil optimization. {CD_optimized (optimized drag coefficient), CL_optimized (optimized lift coefficient), CM_optimized (optimized moment coefficient)}
    """

    if mach_number < 0.6:
        os.system(f"cp -r {airfoil_path}/system/fvSolution_subsonic {airfoil_path}/system/fvSolution")
    else:
        os.system(f"cp -r {airfoil_path}/system/fvSolution_transonic {airfoil_path}/system/fvSolution")

    # Run DAFoam commands directly in this container with mpirun
    base_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"mpirun -np {cpu_cores} python run_script.py "
        f"-task=run_driver "
        f"-angle_of_attack={angle_of_attack} "
        f"-mach_number={mach_number} "
        f"-reynolds_number={reynolds_number} "
        f"-lift_constraint={lift_constraint} > log-optimization.txt"
    )

    # Add reconstructPar and cleanup only if parallel (cpu_cores > 1)
    if cpu_cores > 1:
        bash_command = f"{base_command} && reconstructPar && rm -rf processor* && pvpython plot_flow_field.py && pvpython plot_pressure_profile.py -mach_number={mach_number}"
    else:
        bash_command = f"{base_command} && pvpython plot_flow_field.py && pvpython plot_pressure_profile.py -mach_number={mach_number}"

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path1 = f"{airfoil_path}/flow_field.jpeg"
    image_path2 = f"{airfoil_path}/pressure_profile.jpeg"

    # read CD, CL, and CM
    with open(f"{airfoil_path}/log-optimization.txt") as f:
        lines = f.readlines()
        CD = [line.split()[1] for line in lines if "CD:" in line][-1]
        CL = [line.split()[1] for line in lines if "CL:" in line][-1]
        CM = [line.split()[1] for line in lines if "CM:" in line][-1]

    return [
        display_image(image_path1),
        display_image(image_path2),
        {"CD_optimized": CD, "CL_optimized": CL, "CM_optimized": CM},
    ]


@mcp.tool()
async def airfoil_run_cfd_simulation(
    cpu_cores: int, angle_of_attack: float, mach_number: float, reynolds_number: float
):
    """
    Airfoil module: Run CFD simulation to compute airfoil flow fields such as velocity, pressure, and temperature.

    Inputs:
        cpu_cores: The number of CPU cores to use. >1 means running the simulation in parallel. Default: 1
        angle_of_attack: The angle of attack (aoa) boundary condition at the far field for the airfoil. Default: 3.0
        mach_number: The Mach number (Ma). mach_number > 0.6: transonic conditions, mach_number < 0.6 subsonic conditions. We should use the same mach number set in the airfoil_generate_mesh call.
        reynolds_number: The Reynolds number, users can also use Re to denote the Reynolds number.
    Outputs:
        1. The image of flow field
        2. The image of pressure profile
        3. A dictionary for the airfoil aerodynamics. {CD (drag coefficient), CL (lift coefficient), CM (moment coefficient)}
    """

    if mach_number < 0.6:
        os.system(f"cp -r {airfoil_path}/system/fvSolution_subsonic {airfoil_path}/system/fvSolution")
    else:
        os.system(f"cp -r {airfoil_path}/system/fvSolution_transonic {airfoil_path}/system/fvSolution")

    # Run DAFoam commands directly in this container with mpirun
    base_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"mpirun -np {cpu_cores} python run_script.py "
        f"-task=run_model "
        f"-angle_of_attack={angle_of_attack} "
        f"-mach_number={mach_number} "
        f"-reynolds_number={reynolds_number} > log-cfd-simulation.txt"
    )

    # Add reconstructPar and cleanup only if parallel (cpu_cores > 1)
    if cpu_cores > 1:
        bash_command = f"{base_command} && reconstructPar && rm -rf processor* && pvpython plot_flow_field.py && pvpython plot_pressure_profile.py -mach_number={mach_number}"
    else:
        bash_command = f"{base_command} && pvpython plot_flow_field.py && pvpython plot_pressure_profile.py -mach_number={mach_number}"

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path1 = f"{airfoil_path}/flow_field.jpeg"
    image_path2 = f"{airfoil_path}/pressure_profile.jpeg"

    # read CD, CL, and CM
    with open(f"{airfoil_path}/log-cfd-simulation.txt") as f:
        lines = f.readlines()
        CD = [line.split()[1] for line in lines if "CD:" in line][-1]
        CL = [line.split()[1] for line in lines if "CL:" in line][-1]
        CM = [line.split()[1] for line in lines if "CM:" in line][-1]

    return [display_image(image_path1), display_image(image_path2), {"CD": CD, "CL": CL, "CM": CM}]


@mcp.tool()
async def airfoil_view_flow_field_details(x_location: float, y_location: float, zoom_in_scale: float, variable: str):
    """
    Airfoil module: Allow users to view the details of a selected flow field variable. The airfoil CFD simulation must have been done.

    Inputs:
        x_location: where to zoom in to view the airfoil mesh details in the x direction. Leading edge: x_location=0, mid chord: x_location=0.5, and trailing edge: x_location=1. Default: 0.5
        y_location: where to zoom in to view the airfoil mesh details in the y direction. Upper surface: y_location>0 (about 0.1), lower surface: y_location<0 (about -0.1). Default: 0
        zoom_in_scale: how much to zoom in to visualize the mesh. Set a smaller zoom_in_scale if users need zoom in more. Set a larger zoom_in_scale if users need to zoom out more. Default: 0.5
        variable: which flow field variable to visualize. Options are "U": velocity, "T": temperature, "p": pressure, "nut": turbulence viscosity (turbulence variable). Default: "p"
    Outputs:
        The image of flow field
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"pvpython plot_flow_field.py -x_location={x_location} -y_location={y_location} -zoom_in_scale={zoom_in_scale} -variable={variable}"
    )

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path = f"{airfoil_path}/flow_field.jpeg"

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

    Inputs:
        x_location: where to zoom in to view the airfoil mesh details in the x direction. Leading edge: x_location=0, mid chord: x_location=0.5, and trailing edge: x_location=1. Default: 0.5
        y_location: where to zoom in to view the airfoil mesh details in the y direction. Upper surface: y_location>0 (about 0.1), lower surface: y_location<0 (about -0.1). Default: 0
        zoom_in_scale: how much to zoom in to visualize the mesh. Set a smaller zoom_in_scale if users need zoom in more. Set a larger zoom_in_scale if users need to zoom out more. Default: 0.5
    Outputs:
        The image of the airfoil mesh
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"pvpython plot_mesh.py -x_location={x_location} -y_location={y_location} -zoom_in_scale={zoom_in_scale}"
    )

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path = f"{airfoil_path}/airfoil_mesh.jpeg"

    if not os.path.exists(image_path):
        return TextContent(
            type="text",
            text=f"Image not found!\n\nStdout:\n{result.stdout}\n\nStderr:\n{result.stderr}",
        )

    return display_image(image_path)


@mcp.tool()
async def airfoil_generate_mesh(
    airfoil_profile: str, mesh_cells: int, y_plus: float, n_ffd_points: int, mach_number: float
):
    """
    Airfoil module: Generate the airfoil mesh and output the mesh image called airfoil_mesh.jpeg

    Inputs:
        airfoil_profile: The name of the airfoil profile, such as rae2822 or naca0012 (no spaces and all lower case letters). Default: naca0012
        mesh_cells: The number of mesh cells to generate. Default: 5000
        y_plus: the normalized near wall mesh size to capture boundary layer. Default: 50
        n_ffd_points: the Number of FFD control points to change the airfoil geometry. Default: 10
        mach_number: the reference Mach number to estimate the near wall mesh size. Default: 0.1
    Outputs:
        The image of the airfoil mesh
    """
    # Run DAFoam commands directly in this container with mpirun
    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"./Allclean.sh && "
        f"python generate_mesh.py -airfoil_profile={airfoil_profile} -mesh_cells={mesh_cells} -y_plus={y_plus} -n_ffd_points={n_ffd_points} -mach_number={mach_number} > log-mesh.txt && "
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
    image_path = f"{airfoil_path}/airfoil_mesh.jpeg"

    return display_image(image_path)


if __name__ == "__main__":
    mcp.run(transport="stdio")
