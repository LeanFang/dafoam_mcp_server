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
def check_run_status():
    """
    Check whether the cfd simulation or optimization finished

    Inputs:
        None
    Outputs:
        finished: 1 = the run finishes. 0 = the run does not finish
    """

    file_path = f"{airfoil_path}/.dafoam_run_finished"
    path = Path(file_path).expanduser()

    if path.exists():
        return 1
    else:
        return 0


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
        A message saying that the optimization is running in the background and the progress is written to log_optimization.txt
    """

    if mach_number < 0.6:
        os.system(f"cp -r {airfoil_path}/system/fvSolution_subsonic {airfoil_path}/system/fvSolution")
    else:
        os.system(f"cp -r {airfoil_path}/system/fvSolution_transonic {airfoil_path}/system/fvSolution")

    # Run DAFoam commands directly in this container with mpirun
    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"rm -rf .dafoam_run_finished && "
        f"mpirun -np {cpu_cores} python script_run_dafoam.py "
        f"-task=run_driver "
        f"-angle_of_attack={angle_of_attack} "
        f"-mach_number={mach_number} "
        f"-reynolds_number={reynolds_number} "
        f"-lift_constraint={lift_constraint} > log_optimization.txt 2>&1"
    )

    subprocess.Popen(
        ["bash", "-c", bash_command],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # Detach from parent process
    )

    return "The optimization is running. Check log_optimization.txt for progress."


@mcp.tool()
async def airfoil_check_run_status():
    """
    Check whether the cfd simulation or optimization finished

    Inputs:
        None
    Outputs:
        finished: 1 = the run finishes. 0 = the run does not finish
    """

    return check_run_status()


@mcp.tool()
async def airfoil_run_cfd_simulation(
    cpu_cores: int, angle_of_attack: float, mach_number: float, reynolds_number: float
):
    """
    Airfoil module: Run CFD simulation/analysis to compute airfoil flow fields such as velocity, pressure, and temperature.

    Inputs:
        cpu_cores: The number of CPU cores to use. >1 means running the simulation in parallel. Default: 1
        angle_of_attack: The angle of attack (aoa) boundary condition at the far field for the airfoil. Default: 3.0
        mach_number: The Mach number (Ma). mach_number > 0.6: transonic conditions, mach_number < 0.6 subsonic conditions. We should use the same mach number set in the airfoil_generate_mesh call.
        reynolds_number: The Reynolds number, users can also use Re to denote the Reynolds number.
    Outputs:
        A message saying that the cfd simulation is running in the background and the progress is written to log_cfd_simulation.txt
    """

    if mach_number < 0.6:
        os.system(f"cp -r {airfoil_path}/system/fvSolution_subsonic {airfoil_path}/system/fvSolution")
    else:
        os.system(f"cp -r {airfoil_path}/system/fvSolution_transonic {airfoil_path}/system/fvSolution")

    # Run DAFoam commands directly in this container with mpirun
    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"rm -rf .dafoam_run_finished && "
        f"mpirun -np {cpu_cores} python script_run_dafoam.py "
        f"-task=run_model "
        f"-angle_of_attack={angle_of_attack} "
        f"-mach_number={mach_number} "
        f"-reynolds_number={reynolds_number} > log_cfd_simulation.txt 2>&1"
    )

    subprocess.Popen(
        ["bash", "-c", bash_command],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # Detach from parent process
    )

    return "The cfd simulation is running. Check log_cfd_simulation.txt for progress."


@mcp.tool()
async def airfoil_view_flow_field(x_location: float, y_location: float, zoom_in_scale: float, variable: str):
    """
    Airfoil module: Allow users to view the details of a selected flow field variable. The airfoil CFD simulation must have been done.

    Inputs:
        x_location: where to zoom in to view the airfoil mesh details in the x direction. Leading edge: x_location=0, mid chord: x_location=0.5, and trailing edge: x_location=1. Default: 0.5
        y_location: where to zoom in to view the airfoil mesh details in the y direction. Upper surface: y_location>0 (about 0.1), lower surface: y_location<0 (about -0.1). Default: 0
        zoom_in_scale: how much to zoom in to visualize the mesh. Set a smaller zoom_in_scale if users need zoom in more. Set a larger zoom_in_scale if users need to zoom out more. Default: 0.5
        variable: which flow field variable to visualize. Options are "U": velocity, "T": temperature, "p": pressure, "nut": turbulence viscosity (turbulence variable). Default: "p"
    Outputs:
        A message about the status of the flow field image
    """

    finished = check_run_status()
    if finished == 0:
        return "The CFD simulation is not finished. No flow field plot is generated. Please wait."

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"pvpython script_plot_flow_field.py -x_location={x_location} -y_location={y_location} -zoom_in_scale={zoom_in_scale} -variable={variable}"
    )

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path = f"{airfoil_path}/image_airfoil_flow_field.png"

    if not os.path.exists(image_path):
        return TextContent(
            type="text",
            text=f"Image not found!\n\nStdout:\n{result.stdout}\n\nStderr:\n{result.stderr}",
        )

    return "The flow field is plotted as image_airfoil_flow_field.png"


@mcp.tool()
async def airfoil_view_residual(log_file: str):
    """
    Plot the residual based on the information from the log_file

    Inputs:
        log_file: log_file=log_cfd_simulation.txt for CFD simulation. log_file=log_optimization.txt for optimization
    Outputs:
        A message about the residual image
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"cp {log_file} .temp_{log_file} && "
        f"pvpython script_plot_residual.py -log_file=.temp_{log_file} && "
        f"rm .temp_{log_file}"
    )

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path = f"{airfoil_path}/image_airfoil_residual.png"

    if not os.path.exists(image_path):
        return TextContent(
            type="text",
            text=f"Image not found!\n\nStdout:\n{result.stdout}\n\nStderr:\n{result.stderr}",
        )

    return "The flow field is plotted as image_airfoil_residual.png"


@mcp.tool()
async def airfoil_view_pressure_profile(mach_number: float):
    """
    Airfoil module: Plot the pressure profile (distribution) on the airfoil surface

    Inputs:
        mach_number: The Mach number (Ma). We should use the same mach number set in the airfoil_generate_mesh and airfoil_run_cfd_simulation calls.
    Outputs:
        A message about the pressure profile image
    """

    finished = check_run_status()
    if finished == 0:
        return "The CFD simulation is not finished. No pressure profile plot is generated. Please wait."

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"pvpython script_plot_pressure_profile.py -mach_number={mach_number}"
    )

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path = f"{airfoil_path}/image_airfoil_pressure_profile.png"

    if not os.path.exists(image_path):
        return TextContent(
            type="text",
            text=f"Image not found!\n\nStdout:\n{result.stdout}\n\nStderr:\n{result.stderr}",
        )

    return "The pressure profile is plotted as image_airfoil_pressure_profile.png"


@mcp.tool()
async def airfoil_view_mesh(x_location: float, y_location: float, zoom_in_scale: float):
    """
    Airfoil module: Allow users to view detail airfoil meshes. The mesh must have been generated in airfoils

    Inputs:
        x_location: where to zoom in to view the airfoil mesh details in the x direction. Leading edge: x_location=0, mid chord: x_location=0.5, and trailing edge: x_location=1. Default: 0.5
        y_location: where to zoom in to view the airfoil mesh details in the y direction. Upper surface: y_location>0 (about 0.1), lower surface: y_location<0 (about -0.1). Default: 0
        zoom_in_scale: how much to zoom in to visualize the mesh. Set a smaller zoom_in_scale if users need zoom in more. Set a larger zoom_in_scale if users need to zoom out more. Default: 0.5
    Outputs:
        A message about mesh image
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"pvpython script_plot_mesh.py -x_location={x_location} -y_location={y_location} -zoom_in_scale={zoom_in_scale}"
    )

    result = subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    # Read and display the generated image
    image_path = f"{airfoil_path}/image_airfoil_mesh.png"

    if not os.path.exists(image_path):
        return TextContent(
            type="text",
            text=f"Image not found!\n\nStdout:\n{result.stdout}\n\nStderr:\n{result.stderr}",
        )

    return "The mesh is plotted as image_airfoil_mesh"


@mcp.tool()
async def airfoil_generate_mesh(
    airfoil_profile: str, mesh_cells: int, y_plus: float, n_ffd_points: int, mach_number: float
):
    """
    Airfoil module: Generate the airfoil mesh. Call airfoil_view_mesh after airfoil_generate_mesh to plot the mesh image image_airfoil_mesh.png

    Inputs:
        airfoil_profile: The name of the airfoil profile, such as rae2822 or naca0012 (no spaces and all lower case letters). Default: naca0012
        mesh_cells: The number of mesh cells to generate. Default: 5000
        y_plus: the normalized near wall mesh size to capture boundary layer. Default: 50
        n_ffd_points: the Number of FFD control points to change the airfoil geometry. Default: 10
        mach_number: the reference Mach number to estimate the near wall mesh size. Default: 0.1
    Outputs:
        A message saying that the mesh is generated, the mesh image is saved as image_airfoil_mesh.png, and the log file is in log_mesh.txt
    """
    # Run DAFoam commands directly in this container with mpirun
    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"./Allclean.sh && "
        f"python script_generate_mesh.py -airfoil_profile={airfoil_profile} -mesh_cells={mesh_cells} -y_plus={y_plus} -n_ffd_points={n_ffd_points} -mach_number={mach_number} > log_mesh.txt && "
        f"plot3dToFoam -noBlank volumeMesh.xyz >> log_mesh.txt && "
        f"autoPatch 30 -overwrite >> log_mesh.txt && "
        f"createPatch -overwrite >> log_mesh.txt && "
        f"renumberMesh -overwrite >> log_mesh.txt && "
        f"cp -r 0_orig 0 && "
        f'transformPoints -scale "(1 1 0.01)" >> log_mesh.txt && '
        f"mv FFD.xyz FFD/ && "
        f"dafoam_plot3dtransform.py scale FFD/FFD.xyz FFD/FFD.xyz 1 1 0.01 >> log_mesh.txt && "
        f"dafoam_plot3d2tecplot.py FFD/FFD.xyz FFD/FFD.dat >> log_mesh.txt && "
        f'sed -i "/Zone T=\\"embedding_vol\\"/,\\$d" FFD/FFD.dat && '
        f"rm volumeMesh.xyz surfMesh.xyz && "
        f"pvpython script_plot_mesh.py"
    )

    subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True)

    return "The mesh is image is in image_airfoil_mesh.png and the log file is in log_mesh.txt"


if __name__ == "__main__":
    mcp.run(transport="stdio")
