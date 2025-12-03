from mcp.server.fastmcp import FastMCP
import base64
from pathlib import Path
import subprocess
import asyncio
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import logging
import time
import urllib.request
import os
import glob

# Suppress all logging to stdout/stderr before MCP starts
logging.basicConfig(level=logging.CRITICAL)

# Initialize FastMCP server
mcp = FastMCP("dafoam_mcp_server")

airfoil_path = "/home/dafoamuser/mount/airfoils/"
wing_path = "/home/dafoamuser/mount/wings/"


@mcp.tool()
async def mcp_check_run_status(module: str):
    """
    Check whether the cfd simulation or optimization finished

    Inputs:
        module: either "airfoil" or "wing"
    Outputs:
        finished:
            1 = the run finishes.
            0 = the run does not finish
    """

    return check_run_status(module)


@mcp.tool()
async def airfoil_generate_mesh(
    airfoil_profile: str = "naca0012",
    mesh_cells: int = 5000,
    y_plus: float = 50.0,
    n_ffd_points: int = 10,
    mach_number: float = 0.1,
):
    """
    Airfoil module:
        Generate the airfoil mesh. Call airfoil_view_mesh after airfoil_generate_mesh
        to plot the mesh image image_airfoil_mesh.png

    Inputs:
        airfoil_profile:
            The name of the airfoil profile, such as rae2822 or naca0012 (no spaces and all lower case letters).
        mesh_cells:
            The number of mesh cells to generate.
        y_plus:
            the normalized near wall mesh size to capture boundary layer.
        n_ffd_points:
            the Number of FFD control points to change the airfoil geometry.
        mach_number:
            the reference Mach number to estimate the near wall mesh size.
    Outputs:
        Message indicating the status with HTML link. Must show the link in bold to users.
        Mesh statistics. Must show them to users. Keep only one digit for non-orthogonality and skewness
    """

    # first check if the airfoil exists in the profiles folder
    # if not, we need to download it from the UIUC airfoil database
    profile_file_name = os.path.join(airfoil_path, "profiles", airfoil_profile.lower() + ".dat")
    download_message = ""
    if not os.path.exists(profile_file_name):
        logging.info(f"Downloading the {airfoil_profile} airfoil profile from the UIUC database!")
        download_status = download_airfoil_from_uiuc(airfoil_profile, profile_file_name)
        if download_status:
            logging.info("Download completed!")
            download_message = (
                f"The {airfoil_profile} airfoil profile is not found in the profiles folder "
                "and has been downloaded from the UIUC database! \n"
            )
        else:
            return (
                f"Error: the {airfoil_profile} airfoil profile is not found in the profiles folder "
                "and it could not be downloaded from the UIUC database either! \n"
            )

    # Run DAFoam commands directly in this container with mpirun
    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"./Allclean.sh && "
        f"python script_generate_mesh.py -airfoil_profile={airfoil_profile} -mesh_cells={mesh_cells} "
        f"-y_plus={y_plus} -n_ffd_points={n_ffd_points} -mach_number={mach_number} > log_mesh.txt && "
        f"plot3dToFoam -noBlank volumeMesh.xyz >> log_mesh.txt && "
        f"autoPatch 30 -overwrite >> log_mesh.txt && "
        f"createPatch -overwrite >> log_mesh.txt && "
        f"renumberMesh -overwrite >> log_mesh.txt && "
        f"checkMesh >> log_mesh.txt && "
        f"cp -r 0_orig 0 && "
        f'transformPoints -scale "(1 1 0.01)" >> log_mesh.txt && '
        f"mv FFD.xyz FFD/ && "
        f"dafoam_plot3dtransform.py scale FFD/FFD.xyz FFD/FFD.xyz 1 1 0.01 >> log_mesh.txt && "
        f"dafoam_plot3d2tecplot.py FFD/FFD.xyz FFD/FFD.dat >> log_mesh.txt && "
        f'sed -i "/Zone T=\\"embedding_vol\\"/,\\$d" FFD/FFD.dat && '
        f"rm volumeMesh.xyz surfMesh.xyz && "
        f"pvpython script_plot_mesh.py -plot_all_views=1 "
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Parse mesh statistics from log_mesh.txt
        log_file_path = f"{airfoil_path}/log_mesh.txt"
        mesh_stats = parse_mesh_statistics(log_file_path)

        # Create HTML wrapper using multi-image function
        html_filename = "airfoil_mesh_all_views.html"
        create_image_html(
            airfoil_path,
            ["plots/airfoil_mesh_overview.png", "plots/airfoil_mesh_le.png", "plots/airfoil_mesh_te.png"],
            html_filename,
        )

        return (
            download_message,
            "Mesh successfully generated for {airfoil_profile}!\n\n"
            f"Mesh Statistics:\n"
            f"  - Number of mesh cells: {mesh_stats['cells']}\n"
            f"  - Mesh max non-orthogonality: {mesh_stats['max_non_orthogonality']:.2f}°\n"
            f"  - Mesh max skewness: {mesh_stats['max_skewness']:.2f}\n\n"
            f"View the mesh: http://localhost:{FILE_HTTP_PORT}/airfoil/{html_filename}",
        )

    except subprocess.CalledProcessError as e:
        return f"Error occurred!\n\nStderr:\n{e.stderr}"


@mcp.tool()
async def airfoil_run_cfd_simulation(
    cpu_cores: int = 1, angle_of_attack: float = 3.0, mach_number: float = 0.1, reynolds_number: float = 1000000.0
):
    """
    Airfoil module:
        Run CFD simulation/analysis to compute airfoil flow fields,
        such as velocity, pressure, and temperature.

    Inputs:
        cpu_cores:
            The number of CPU cores to use. We should use 1 core for < 10,000 mesh cells,
            and use one more core for every 10,000 more cells. DO NOT use more than 4 cores
        angle_of_attack:
            The angle of attack (aoa) boundary condition at the far field for the airfoil.
        mach_number:
            The Mach number (Ma). mach_number > 0.6: transonic conditions, mach_number < 0.6 subsonic conditions.
            We should use the same mach number set in the airfoil_generate_mesh call.
        reynolds_number:
            The Reynolds number, users can also use Re to denote the Reynolds number.
    Outputs:
        A message saying that the cfd simulation is running in the background
        and the progress is written to log_cfd_simulation.txt
    """

    if mach_number < 0.6:
        os.system(f"cp -r {airfoil_path}/system/fvSolution_subsonic {airfoil_path}/system/fvSolution")
    else:
        os.system(f"cp -r {airfoil_path}/system/fvSolution_transonic {airfoil_path}/system/fvSolution")

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"rm -rf .dafoam_run_finished && "
        f"mpirun --oversubscribe -np {cpu_cores} python script_run_dafoam.py "
        f"-angle_of_attack={angle_of_attack} "
        f"-mach_number={mach_number} "
        f"-reynolds_number={reynolds_number} > log_cfd_simulation.txt 2>&1"
    )

    try:
        # Run in non-blocking background mode
        subprocess.Popen(
            ["bash", "-c", bash_command],
            stdout=subprocess.DEVNULL,  # Don't let child write to our stdout
            stderr=subprocess.DEVNULL,  # Don't let child write to our stderr
            stdin=subprocess.DEVNULL,  # Don't let child read from our stdin
        )
        return (
            "CFD simulation started in the background. "
            "Progress is being written to log_cfd_simulation.txt. "
            "Use mcp_check_run_status to check if it's finished."
        )

    except Exception as e:
        return f"Error starting CFD simulation: {str(e)}"


@mcp.tool()
async def airfoil_run_optimization(
    cpu_cores: int = 1,
    angle_of_attack: float = 3.0,
    mach_number: float = 0.1,
    reynolds_number: float = 1000000.0,
    lift_constraint: float = 0.5,
):
    """
    Airfoil module:
        Run CFD-based aerodynamic optimization.
        Objective: drag coefficient.
        Design variables: airfoil shape and angle of attack.
        Constraints: lift, thickness, volume, and leading edge radius
        NOTE: other optimization formulations are not supported at this moment!

    Inputs:
        cpu_cores:
            The number of CPU cores to use. We should use 1 core for < 10,000 mesh cells,
            and use one more core for every 10,000 more cells. DO NOT use more than 4 cores
        angle_of_attack:
            The angle of attack (aoa) boundary condition at the far field for the airfoil.
        mach_number:
            The Mach number (Ma). mach_number > 0.6: transonic conditions, mach_number < 0.6 subsonic conditions.
            We should use the same mach number set in the airfoil_generate_mesh call.
        reynolds_number:
            The Reynolds number, users can also use Re to denote the Reynolds number.
        lift_constraint:
            The lift constraint.
    Outputs:
        A message saying that the optimization is running in the background
        and the progress is written to log_optimization.txt
    """

    if mach_number < 0.6:
        os.system(f"cp -r {airfoil_path}/system/fvSolution_subsonic {airfoil_path}/system/fvSolution")
    else:
        os.system(f"cp -r {airfoil_path}/system/fvSolution_transonic {airfoil_path}/system/fvSolution")

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"rm -rf .dafoam_run_finished && "
        f"mpirun --oversubscribe -np {cpu_cores} python script_run_dafoam.py -task=run_driver "
        f"-angle_of_attack={angle_of_attack} -mach_number={mach_number} -reynolds_number={reynolds_number} "
        f"-lift_constraint={lift_constraint} > log_optimization.txt 2>&1"
    )

    try:
        # Run in non-blocking background mode
        subprocess.Popen(
            ["bash", "-c", bash_command],
            stdout=subprocess.DEVNULL,  # Don't let child write to our stdout
            stderr=subprocess.DEVNULL,  # Don't let child write to our stderr
            stdin=subprocess.DEVNULL,  # Don't let child read from our stdin
        )
        return (
            "Optimization started in the background. "
            "Progress is being written to log_optimization.txt."
            "Use mcp_check_run_status to check if it's finished."
        )
    except Exception as e:
        return f"Error starting optimization: {str(e)}"


@mcp.tool()
async def airfoil_view_flow_field(
    x_location: float = 0.5, y_location: float = 0.0, zoom_in_scale: float = 0.5, variable: str = "p", frame: int = -1
):
    """
    Airfoil module:
        Allow users to view the details of a selected flow field variable.
        The airfoil CFD simulation must have been done.

    Inputs:
        x_location:
            where to zoom in to view the airfoil mesh details in the x direction.
            Leading edge: x_location=0, mid chord: x_location=0.5, and trailing edge: x_location=1.
        y_location:
            where to zoom in to view the airfoil mesh details in the y direction.
            Upper surface: y_location>0 (about 0.1), lower surface: y_location<0 (about -0.1).
        zoom_in_scale:
            how much to zoom in to visualize the mesh. Set a smaller zoom_in_scale if users need zoom in more.
            Set a larger zoom_in_scale if users need to zoom out more.
        variable:
            which flow field variable to visualize. Options are "U": velocity, "T": temperature,
            "p": pressure, "nut": turbulence viscosity (turbulence variable).
        frame:
            which frame to view. The frame is the time-step for cfd simulation or
            optimization iteration for optimization. frame=-1 means all frames
    Outputs:
        Message indicating the status with HTML link. Must show the link in bold to users.
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"pvpython script_plot_flow_field.py -x_location={x_location} -y_location={y_location} "
        f"-zoom_in_scale={zoom_in_scale} -variable={variable} -frame={frame}"
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Create a single HTML with both images
        html_filename = "airfoil_flow_field.html"
        image_names = glob.glob(f"{airfoil_path}/plots/airfoil_flow_field*.png")
        create_image_html(airfoil_path, sorted(image_names, reverse=True), html_filename)

        return (
            "Flow field plots successfully generated!\n\n"
            f"View convergence: http://localhost:{FILE_HTTP_PORT}/airfoil/{html_filename}"
        )

    except subprocess.CalledProcessError as e:
        return f"Error occurred!\n\nStderr:\n{e.stderr}"


@mcp.tool()
async def airfoil_view_optimization_history():
    """
    Airfoil Module:
        Plot the optimization history

    Inputs:
        None
    Outputs:
        Message indicating the status with HTML links. Must show the link in bold to users.
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"python script_plot_optimization_history.py"
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Create a single HTML with both images
        html_filename = "airfoil_optimization_history.html"
        image_files = [
            "plots/airfoil_opt_hst_cd.png",
            "plots/airfoil_opt_hst_cl.png",
            "plots/airfoil_opt_hst_aoa.png",
            "plots/airfoil_opt_hst_shape.png",
            "plots/airfoil_opt_hst_optimality.png",
            "plots/airfoil_opt_hst_feasibility.png",
        ]
        create_image_html(airfoil_path, image_files, html_filename)

        return (
            "Optimization history plots successfully generated!\n\n"
            f"View convergence: http://localhost:{FILE_HTTP_PORT}/airfoil/{html_filename}"
        )

    except subprocess.CalledProcessError as e:
        return f"Error occurred!\n\nStderr:\n{e.stderr}"


@mcp.tool()
async def view_cfd_convergence(
    module: str = "airfoil",
    log_file: str = "log_cfd_simulation.txt",
    start_time_cfd: int = 0,
    end_time_cfd: int = -1,
    start_time_adjoint: int = 0,
    end_time_adjoint: int = -1,
):
    """
    Airfoil or Wing Module:
        Plot the cfd and adjoint (optional) residuals and function (such as CD, CL, and CM) convergence history
        by parsing the information from the log_file

    Inputs:
        module:
            The module can be either "airfoil" or "wing"
        log_file:
            log_file=log_cfd_simulation.txt for CFD simulation. log_file=log_optimization.txt for optimization
        start_time_cfd:
            the cfd start time index to plot.
        end_time_cfd:
            the cfd end time index to plot. end_time_cfd=-1 means the last time step
        start_time_adjoint:
            the adjoint start time index to plot.
        end_time_adjoint:
            the adjoint end time index to plot. end_time_adjoint=-1 means the last time step
    Outputs:
        Message indicating the status with HTML links. Must show the link in bold to users.
    """

    if module == "airfoil":
        case_path = airfoil_path
    elif module == "wing":
        case_path = wing_path

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {case_path} && "
        f"pvpython script_plot_residual.py "
        f"-log_file={log_file} -start_time_cfd={start_time_cfd} -end_time_cfd={end_time_cfd} "
        f"-start_time_adjoint={start_time_adjoint} -end_time_adjoint={end_time_adjoint} && "
        f"pvpython script_plot_function.py -log_file={log_file} -start_time={start_time_cfd} -end_time={end_time_cfd}"
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Create a single HTML with both images
        html_filename = "airfoil_convergence.html"
        image_files = [
            "plots/airfoil_function_cd.png",
            "plots/airfoil_function_cl.png",
            "plots/airfoil_function_cm.png",
            "plots/airfoil_residual_cfd.png",
        ]
        if log_file == "log_optimization.txt":
            image_files.append("plots/airfoil_residual_adjoint.png")
        create_image_html(case_path, image_files, html_filename)

        return (
            "Residual and function plots successfully generated!\n\n"
            f"View convergence: http://localhost:{FILE_HTTP_PORT}/{module}/{html_filename}"
        )

    except subprocess.CalledProcessError as e:
        return f"Error occurred!\n\nStderr:\n{e.stderr}"


@mcp.tool()
async def airfoil_view_pressure_profile(mach_number: float = 0.1, frame: int = -1):
    """
    Airfoil module:
        Plot the pressure profile (distribution) on the airfoil surface

    Inputs:
        mach_number:
            The Mach number (Ma). We should use the same mach number set in the
            airfoil_generate_mesh and airfoil_run_cfd_simulation calls.
        frame:
            which frame to view. The frame is the time-step for cfd simulation or
            optimization iteration for optimization. frame=-1 means all frames
    Outputs:
        Message indicating the status with HTML link. Must show the link in bold to users.
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"pvpython script_plot_pressure_profile.py -mach_number={mach_number} -frame={frame}"
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Create HTML wrapper using multi-image function
        html_filename = "airfoil_pressure_profile.html"
        image_names = glob.glob(f"{airfoil_path}/plots/airfoil_pressure_profile*.png")
        create_image_html(airfoil_path, sorted(image_names, reverse=True), html_filename)

        return (
            "Pressure profile successfully generated!\n\n"
            f"View the result: http://localhost:{FILE_HTTP_PORT}/airfoil/{html_filename}"
        )

    except subprocess.CalledProcessError as e:
        return f"Error occurred!\n\nStderr:\n{e.stderr}"


@mcp.tool()
async def airfoil_view_mesh(x_location: float = 0.5, y_location: float = 0.0, zoom_in_scale: float = 0.5):
    """
    Airfoil module:
        Allow users to view detail airfoil meshes. The mesh must have been generated in airfoils

    Inputs:
        x_location:
            where to zoom in to view the airfoil mesh details in the x direction.
            Leading edge: x_location=0, mid chord: x_location=0.5, and trailing edge: x_location=1.
        y_location:
            where to zoom in to view the airfoil mesh details in the y direction.
            Upper surface: y_location>0 (about 0.1), lower surface: y_location<0 (about -0.1).
        zoom_in_scale:
            how much to zoom in to visualize the mesh. Set a smaller zoom_in_scale if users need zoom in more.
            Set a larger zoom_in_scale if users need to zoom out more.
    Outputs:
        Message indicating the status with HTML link. Must show the link in bold to users.
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"pvpython script_plot_mesh.py -x_location={x_location} -y_location={y_location} -zoom_in_scale={zoom_in_scale}"
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Create HTML wrapper using multi-image function
        html_filename = "airfoil_mesh.html"
        create_image_html(airfoil_path, ["plots/airfoil_mesh.png"], html_filename)

        return (
            "Mesh visualization successfully generated!\n\n"
            f"View the result: http://localhost:{FILE_HTTP_PORT}/airfoil/{html_filename}"
        )

    except subprocess.CalledProcessError as e:
        return f"Error occurred!\n\nStderr:\n{e.stderr}"


@mcp.tool()
async def wing_generate_geometry(
    spanwise_airfoil_profiles: list[str] = ["naca0012", "naca0012"],
    spanwise_chords: list[float] = [1.0, 1.0],
    spanwise_x: list[float] = [0.0, 0.0],
    spanwise_y: list[float] = [0.0, 0.0],
    spanwise_z: list[float] = [0.0, 3.0],
    spanwise_twists: list[float] = [0.0, 0.0],
) -> str:
    """
    Wing module:
        Generate wing geometry using pyGeo and gmsh. Here we assume x is the flow direction, y is the airfoil vertical direction,
        and z is the wing spanwise direction.

    Args:
        spanwise_airfoil_profiles:
            Airfoil profiles for each spanwise section (e.g., ["naca0012", "naca0012"])
        spanwise_chords:
            Airfoil chords for each spanwise section.
        spanwise_x:
            X coordinates for each spanwise section
        spanwise_y:
            Y coordinates for each spanwise section
        spanwise_z:
            Z coordinates for each spanwise section
        spanwise_twists:
            Twist angles for each spanwise section

    Returns:
        Status message and list of generated files. Must show the link in bold to users.
    """

    # Build command line arguments
    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {wing_path} && "
        f"./Allclean.sh && "
        f"python script_generate_geometry.py "
        f"-spanwise_airfoil_profiles {' '.join(map(str, spanwise_airfoil_profiles))} "
        f"-spanwise_chords {' '.join(map(str, spanwise_chords))} "
        f"-spanwise_x {' '.join(map(str, spanwise_x))} "
        f"-spanwise_y {' '.join(map(str, spanwise_y))} "
        f"-spanwise_z {' '.join(map(str, spanwise_z))} "
        f"-spanwise_twists {' '.join(map(str, spanwise_twists))} && "
        f"pvpython script_plot_geometry.py "
        f"-spanwise_z {' '.join(map(str, spanwise_z))} "
        f"-spanwise_chords {' '.join(map(str, spanwise_chords))} "
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Create HTML wrapper using multi-image function
        html_filename = "wing_geometry_all_views.html"
        create_image_html(
            wing_path,
            [
                "plots/wing_geometry_view_3d.png",
                "plots/wing_geometry_view_y.png",
                "plots/wing_geometry_view_x.png",
                "plots/wing_geometry_view_z.png",
            ],
            html_filename,
        )

        return (
            "Wing geometry is successfully generated!\n\n"
            f"View the geometry at: http://localhost:{FILE_HTTP_PORT}/wing/{html_filename}"
        )

    except subprocess.CalledProcessError as e:
        return f"Error occurred!\n\nStderr:\n{e.stderr}"


@mcp.tool()
async def wing_generate_mesh(
    max_cell_size: float = 1.0,
    mesh_refinement_level: int = 5,
    n_boundary_layers: int = 10,
    mean_chord: float = 1.0,
    span: float = 3.0,
    leading_edge_root: list[float] = [0.0, 0.0, 0.0],
    leading_edge_tip: list[float] = [0.0, 0.0, 3.0],
) -> str:
    """
    Wing module:
        Generate wing mesh using cfMesh. Here we assume x is the flow direction, y is the airfoil vertical direction,
        and z is the wing spanwise direction.

    Args:
        max_cell_size:
            The maximial cell size in the far field
        mesh_refinement_level:
            How many levels to refine the mesh. The higher the refinement the higher the mesh cells
        n_boundary_layers:
            How many mesh layer to capture the boundary layer
        mean_chord:
            The average chord for the wing. NOTE: this value must be consistent with the averaged chords
            from the spanwise_chords args from the wing_generate_geometry function!
        span:
            The span for the wing. NOTE: this value must be consistent with the spanwise_z args
            from the wing_generate_geometry function! span = spanwise_z[-1] - spanwise_z[0]
        leading_edge_root:
            The coordinates for the leading edge at the wing root. It will be calculated based on spanwise_x,
            spanwise_y, and spanwise_z from the wing_generate_geometry function. Here the size of spanwise_x
            is the number of spanwise sections, if there are more than two sections prescribed, we will use
            the first one (root section) and the last one (tip section).
        leading_edge_tip:
            The coordinates for the leading edge at the wing tip. It will be calculated based on spanwise_x,
            spanwise_y, and spanwise_z from the wing_generate_geometry function. Here the size of spanwise_x
            is the number of spanwise sections, if there are more than two sections prescribed, we will use
            the first one (root section) and the last one (tip section).

    Returns:
        Status message and list of generated files. Must show the link in bold to users.
        Mesh statistics. Must show them to users. Keep only one digit for non-orthogonality and skewness
    """

    # Build command line arguments
    domain = mean_chord * 20.0
    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {wing_path} && "
        f"sed -i 's/^maxCellSize.*/maxCellSize {max_cell_size};/' system/meshDict && "
        f"sed -i 's/^refinementLevel.*/refinementLevel {mesh_refinement_level};/' system/meshDict && "
        f"sed -i 's/^nBoundaryLayers.*/nBoundaryLayers {n_boundary_layers};/' system/meshDict && "
        f"sed -i 's/^le_p0.*/le_p0 ({leading_edge_root[0]} {leading_edge_root[1]} {leading_edge_root[2]});/' system/meshDict && "
        f"sed -i 's/^le_p1.*/le_p1 ({leading_edge_tip[0]} {leading_edge_tip[1]} {leading_edge_tip[2]});/' system/meshDict && "
        f"surfaceGenerateBoundingBox wing.stl domain.stl {domain} {domain} {domain} {domain} 0 {domain} > log_mesh.txt && "
        f"cartesianMesh >> log_mesh.txt && "
        f"renumberMesh -overwrite >> log_mesh.txt && "
        f"checkMesh >> log_mesh.txt && "
        f"cp -r 0_orig 0 && "
        f"pvpython script_plot_mesh.py "
        f"-mean_chord={mean_chord} "
        f"-span={span} "
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Parse mesh statistics from log_mesh.txt
        log_file_path = f"{wing_path}/log_mesh.txt"
        mesh_stats = parse_mesh_statistics(log_file_path)

        # Create HTML wrapper using multi-image function
        html_filename = "wing_mesh_all_views.html"
        create_image_html(
            wing_path,
            [
                "plots/wing_mesh_view_3d.png",
                "plots/wing_mesh_view_y.png",
                "plots/wing_mesh_view_x.png",
                "plots/wing_mesh_view_z.png",
            ],
            html_filename,
        )

        return (
            "Wing mesh is successfully generated!\n\n"
            f"Mesh Statistics:\n"
            f"  - Number of mesh cells: {mesh_stats['cells']}\n"
            f"  - Mesh max non-orthogonality: {mesh_stats['max_non_orthogonality']:.2f}°\n"
            f"  - Mesh max skewness: {mesh_stats['max_skewness']:.2f}\n\n"
            f"View the mesh at: http://localhost:8001/wing/{html_filename}"
        )

    except subprocess.CalledProcessError as e:
        return f"Error occurred!\n\nStderr:\n{e.stderr}"


@mcp.tool()
async def wing_run_cfd_simulation(
    cpu_cores: int = 1,
    angle_of_attack: float = 2,
    mach_number: float = 0.1,
    reynolds_number: float = 1000000,
    reference_area: float = 1.0,
):
    """
    Wing module:
        Run CFD simulation/analysis to compute flow fields,
        such as velocity, pressure, and temperature.

    Args:
        cpu_cores:
            The number of CPU cores to use. We should use 1 core for < 100,000 mesh cells,
            and use one more core for every 100,000 more cells. DO NOT use more than 4 cores
        angle_of_attack:
            The angle of attack (aoa) boundary condition at the far field.
        mach_number:
            The Mach number (Ma). mach_number > 0.6: transonic conditions, mach_number < 0.6 subsonic conditions.
        reynolds_number:
            The Reynolds number, users can also use Re to denote the Reynolds number.
        reference_area:
            The reference area for normalizing forces. If users do not prescribe it, approximate it as ref_area = mean_chord * span
    Returns:
        A message saying that the cfd simulation is running in the background
        and the progress is written to log_cfd_simulation.txt
    """

    if mach_number < 0.6:
        os.system(f"cp -r {wing_path}/system/fvSolution_subsonic {wing_path}/system/fvSolution")
    else:
        os.system(f"cp -r {wing_path}/system/fvSolution_transonic {wing_path}/system/fvSolution")

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {wing_path} && "
        f"rm -rf .dafoam_run_finished && "
        f"mpirun --oversubscribe -np {cpu_cores} python script_run_dafoam.py "
        f"-angle_of_attack={angle_of_attack} "
        f"-mach_number={mach_number} "
        f"-reference_area={reference_area} "
        f"-reynolds_number={reynolds_number} > log_cfd_simulation.txt 2>&1"
    )

    try:
        # Run in non-blocking background mode
        subprocess.Popen(
            ["bash", "-c", bash_command],
            stdout=subprocess.DEVNULL,  # Don't let child write to our stdout
            stderr=subprocess.DEVNULL,  # Don't let child write to our stderr
            stdin=subprocess.DEVNULL,  # Don't let child read from our stdin
        )
        return (
            "CFD simulation started in the background. "
            "Progress is being written to log_cfd_simulation.txt. "
            "Use check_run_status to check if it's finished."
        )

    except Exception as e:
        return f"Error starting CFD simulation: {str(e)}"


@mcp.tool()
async def wing_view_pressure_profile(
    mach_number: float = 0.1, frame: int = -1, span: float = 3.0, spanwise_chords: list[float] = [1.0, 1.0, 1.0]
):
    """
    Wing module:
        Plot the pressure profile (distribution) at the 10%, 50%, and 90% of the wing span

    Inputs:
        mach_number:
            The Mach number (Ma). We should use the same mach number set in the
            airfoil_generate_mesh and airfoil_run_cfd_simulation calls.
        frame:
            which frame to view. The frame is the time-step for cfd simulation or
            optimization iteration for optimization. Default: -1 (all frames)
        span:
            The span for the wing. NOTE: this value must be consistent with the spanwise_z args
            from the wing_generate_geometry function! span = spanwise_z[-1] - spanwise_z[0]
        spanwise_chords:
            Airfoil chords for the 10%, 50%, and 90% of the spanwise location. Here spanwise_chords MUST be a 3D array.
            NOTE: the array's value must be consistent with the spanwise_chords args from the wing_generate_geometry
            function! If only the root and tip chords are set in wing_generate_geometry's spanwise_chords, we need to
            use linear  interpolation to get the chord at 10%, 50%, and 90% of the span. We MUST recompute these
            values instead of using the default.
    Outputs:
        Message indicating the status with HTML link. Must show the link in bold to users.
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {wing_path} && "
        f"pvpython script_plot_pressure_profile.py -mach_number={mach_number} -frame={frame} -span={span} "
        f"-spanwise_chords {' '.join(map(str, spanwise_chords))} "
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Create HTML wrapper using multi-image function
        html_filename = "wing_pressure_profile.html"
        image_names = glob.glob(f"{wing_path}/plots/wing_pressure_profile*.png")
        create_image_html(wing_path, sorted(image_names, reverse=True), html_filename)

        return (
            "Pressure profile successfully generated!\n\n"
            f"View the result: http://localhost:{FILE_HTTP_PORT}/wing/{html_filename}"
        )

    except subprocess.CalledProcessError as e:
        return f"Error occurred!\n\nStderr:\n{e.stderr}"


@mcp.tool()
async def wing_view_flow_field(mean_chord: float = 1.0, span: float = 3.0, variable: str = "p"):
    """
    Wing module:
        Allow users to view the details of a selected flow field variable.
        The wing CFD simulation must have been done.

    Inputs:
        mean_chord:
            The average chord for the wing. NOTE: this value must be consistent with the averaged chords
            from the spanwise_chords args from the wing_generate_geometry function!
        span:
            The span for the wing. NOTE: this value must be consistent with the spanwise_z args
            from the wing_generate_geometry function! span = spanwise_z[-1] - spanwise_z[0]
        variable:
            which flow field variable to visualize. Options are "U": velocity, "T": temperature,
            "p": pressure, "nut": turbulence viscosity (turbulence variable). Default: "p"

    Outputs:
        Message indicating the status with HTML link. Must show the link in bold to users.
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {wing_path} && "
        f"pvpython script_plot_flow_field.py -mean_chord={mean_chord} -span={span} -variable={variable}"
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Create a single HTML with both images
        html_filename = "wing_flow_field.html"
        image_names = glob.glob(f"{wing_path}/plots/wing_flow_field*.png")
        create_image_html(wing_path, sorted(image_names, reverse=True), html_filename)

        return (
            "Flow field plots successfully generated!\n\n"
            f"View convergence: http://localhost:{FILE_HTTP_PORT}/wing/{html_filename}"
        )

    except subprocess.CalledProcessError as e:
        return f"Error occurred!\n\nStderr:\n{e.stderr}"


# helper functions
def check_run_status(module: str = "airfoil"):
    """
    Check whether the cfd simulation or optimization finished

    Inputs:
        module: either "airfoil" or "wing"
    Outputs:
        finished: 1 = the run finishes. 0 = the run does not finish
    """

    if module == "airfoil":
        case_path = airfoil_path
    elif module == "wing":
        case_path = wing_path

    file_path = f"{case_path}/.dafoam_run_finished"
    path = Path(file_path).expanduser()

    if path.exists():
        return 1
    else:
        return 0


def parse_mesh_statistics(log_file_path: str) -> dict:
    """
    Parse mesh statistics from the log_mesh.txt file.

    Args:
        log_file_path: Path to the log_mesh.txt file

    Returns:
        Dictionary containing:
            - cells: number of mesh cells
            - max_non_orthogonality: maximum non-orthogonality angle
            - max_skewness: maximum skewness value
    """

    mesh_stats = {"cells": 0, "max_non_orthogonality": 0.0, "max_skewness": 0.0}

    try:
        with open(log_file_path, "r") as f:
            lines = f.readlines()

        search_started = 0
        for line in lines:
            if "checkMesh" in line:
                search_started = 1
            if search_started == 1:
                if "cells:" in line:
                    mesh_stats["cells"] = int(line.split()[1])
                if "Mesh non-orthogonality Max:" in line:
                    mesh_stats["max_non_orthogonality"] = float(line.split()[3])
                if "skewness" in line:
                    mesh_stats["max_skewness"] = float(line.split()[3].rstrip(","))

    except FileNotFoundError:
        print(f"Warning: Log file not found at {log_file_path}")
    except Exception as e:
        print(f"Warning: Error parsing log file: {str(e)}")

    return mesh_stats


class CustomHTTPHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler to serve files from both airfoil_path and wing_path"""

    def translate_path(self, path):
        """Translate URL path to local file path, using prefixes to distinguish directories"""
        import urllib.parse
        import os

        # Remove query parameters and normalize
        path = path.split("?", 1)[0]
        path = path.split("#", 1)[0]
        path = urllib.parse.unquote(path)

        # Remove leading slash
        if path.startswith("/"):
            path = path[1:]

        # Check for wing/ prefix
        if path.startswith("wing/"):
            relative_path = path[5:]  # Remove 'wing/' prefix
            return os.path.join(wing_path, "plots", relative_path)

        # Check for airfoil/ prefix
        elif path.startswith("airfoil/"):
            relative_path = path[8:]  # Remove 'airfoil/' prefix
            return os.path.join(airfoil_path, "plots", relative_path)

        # Default to airfoil directory for backward compatibility
        else:
            return os.path.join(airfoil_path, "plots", path)

    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass


def start_http_server():
    """Start HTTP server in background thread"""
    global http_server, server_started
    try:
        # Try binding to 0.0.0.0 first, fallback to 127.0.0.1
        try:
            http_server = HTTPServer(("0.0.0.0", FILE_HTTP_PORT), CustomHTTPHandler)
        except OSError:
            # If 0.0.0.0 fails (common on some Windows configurations), try 127.0.0.1
            http_server = HTTPServer(("127.0.0.1", FILE_HTTP_PORT), CustomHTTPHandler)

        server_started = True
        http_server.serve_forever()
    except Exception as e:
        # Log error to a file for debugging
        with open(f"{airfoil_path}/plots/http_server_error.txt", "w") as f:
            f.write(f"HTTP Server failed to start: {str(e)}\n")
        server_started = False


def create_image_html(case_path: str, image_files: list, html_filename: str) -> str:
    """
    Create an HTML wrapper for multiple images displayed side by side with embedded base64 images

    Inputs:
        case_path: airfoils for the Airfoil Module and wings for the Wing Module. Default: airfoils
        image_files: List of image filenames (e.g., ['image1.png', 'image2.png'])
        html_filename: name of the generated html file
    """

    # Read all images and convert to base64
    image_data_list = []
    for i, image_filename in enumerate(image_files):
        image_path = Path(case_path) / image_filename
        if not image_path.exists():
            continue

        with open(image_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode("utf-8")

        # Determine image type
        img_extension = image_path.suffix.lower()
        mime_type = "image/png" if img_extension == ".png" else "image/jpeg"

        image_data_list.append({"data": img_data, "mime": mime_type, "filename": image_filename})

    if not image_data_list:
        return None

    # Create image sections HTML
    image_sections = ""
    for img_info in image_data_list:
        image_sections += f"""
        <div class="image-section">
            <div class="image-container">
                <img src="data:{img_info['mime']};base64,{img_info['data']}">
            </div>
            <div class="image-info">
                <p>Image: {img_info['filename']}</p>
            </div>
        </div>
        """

    # Create HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .main-container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 40px;
            font-size: 28px;
        }}
        h2 {{
            color: #444;
            text-align: center;
            margin-bottom: 20px;
            font-size: 20px;
        }}
        h3 {{
            color: #555;
            font-size: 16px;
            margin-top: 20px;
        }}
        .image-section {{
            margin-bottom: 50px;
            padding-bottom: 30px;
            border-bottom: 2px solid #eee;
        }}
        .image-section:last-child {{
            border-bottom: none;
        }}
        .image-container {{
            text-align: center;
            margin: 20px 0;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .image-info {{
            text-align: center;
            color: #666;
            margin-top: 20px;
            font-size: 14px;
        }}
        .download-btn {{
            display: inline-block;
            margin-top: 10px;
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            transition: background-color 0.3s;
        }}
        .download-btn:hover {{
            background-color: #45a049;
        }}
        .server-info {{
            background-color: #f0f8ff;
            padding: 20px;
            border-radius: 8px;
            margin-top: 30px;
            border-left: 4px solid #4CAF50;
        }}
        .server-info ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        .server-info li {{
            margin: 8px 0;
        }}
        .server-info a {{
            color: #0066cc;
            text-decoration: none;
        }}
        .server-info a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="main-container">
        {image_sections}
    </div>
</body>
</html>"""

    html_path = Path(case_path) / "plots" / html_filename

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def download_airfoil_from_uiuc(airfoil_name, save_path):
    """
    Download airfoil coordinates from UIUC Airfoil Database

    Inputs:
        airfoil_name:
            Name of the airfoil (e.g., 'naca4412')
        save_path:
            Path where to save the downloaded file

    Returns:
        True if download successful, False otherwise
    """
    base_url = "https://m-selig.ae.illinois.edu/ads/coord/"
    url = f"{base_url}{airfoil_name.lower()}.dat"

    try:
        # Download the file
        with urllib.request.urlopen(url, timeout=10) as response:
            content = response.read()

        # Save to file
        with open(save_path, "wb") as f:
            f.write(content)
        return True

    except Exception:
        return False


# HTTP server configuration for file serving
FILE_HTTP_PORT = 8001  # Changed to 8001 to avoid conflict with MCP HTTP port
http_server = None
server_started = False


# Start HTTP server in daemon thread when module loads
server_thread = threading.Thread(target=start_http_server, daemon=True)
server_thread.start()

# Give the server a moment to start
time.sleep(0.5)

if __name__ == "__main__":
    # Use stdio mode only - FastMCP doesn't directly support SSE
    # For HTTP support, you'd need to use the low-level MCP SDK
    mcp.run(transport="stdio")
