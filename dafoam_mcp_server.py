from mcp.server.fastmcp import FastMCP
import base64
from pathlib import Path
from mcp.types import TextContent
import subprocess
import asyncio
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import logging
import socket
import time

# Suppress all logging to stdout/stderr before MCP starts
logging.basicConfig(level=logging.CRITICAL)

# Initialize FastMCP server
mcp = FastMCP("dafoam_mcp_server")

airfoil_path = "/home/dafoamuser/mount/airfoils/"


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
async def airfoil_run_optimization(
    cpu_cores: int, angle_of_attack: float, mach_number: float, reynolds_number: float, lift_constraint: float
):
    """
    Airfoil module: Run CFD-based aerodynamic optimization.
    Objective: drag coefficient.
    Design variables: airfoil shape and angle of attack.
    Constraints: lift, thickness, volume, and leading edge radius

    Inputs:
        cpu_cores: The number of CPU cores to use. We should use 1 core for < 10,000 mesh cells, and use one more core for every 10,000 more cells. Default: 1
        angle_of_attack: The angle of attack (aoa) boundary condition at the far field for the airfoil. Default: 3.0
        mach_number: The Mach number (Ma). mach_number > 0.6: transonic conditions, mach_number < 0.6 subsonic conditions. We should use the same mach number set in the airfoil_generate_mesh call. Default: 0.1
        reynolds_number: The Reynolds number, users can also use Re to denote the Reynolds number. Default: 1000000
        lift_constraint: The lift constraint. Default: 0.5
    Outputs:
        A message saying that the optimization is running in the background and the progress is written to log_optimization.txt
    """

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
        return TextContent(
            type="text",
            text="Optimization started in the background. Progress is being written to log_optimization.txt. Use airfoil_check_run_status to check if it's finished.",
        )
    except Exception as e:
        return TextContent(
            type="text",
            text=f"Error starting optimization: {str(e)}",
        )


@mcp.tool()
async def airfoil_run_cfd_simulation(
    cpu_cores: int, angle_of_attack: float, mach_number: float, reynolds_number: float
):
    """
    Airfoil module: Run CFD simulation/analysis to compute airfoil flow fields such as velocity, pressure, and temperature.

    Inputs:
        cpu_cores: The number of CPU cores to use. We should use 1 core for < 10,000 mesh cells, and use one more core for every 10,000 more cells. Default: 1
        angle_of_attack: The angle of attack (aoa) boundary condition at the far field for the airfoil. Default: 3.0
        mach_number: The Mach number (Ma). mach_number > 0.6: transonic conditions, mach_number < 0.6 subsonic conditions. We should use the same mach number set in the airfoil_generate_mesh call. Default: 0.1
        reynolds_number: The Reynolds number, users can also use Re to denote the Reynolds number. Default: 1000000
    Outputs:
        A message saying that the cfd simulation is running in the background and the progress is written to log_cfd_simulation.txt
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"rm -rf .dafoam_run_finished && "
        f"mpirun --oversubscribe -np {cpu_cores} python script_run_dafoam.py "
        f"-angle_of_attack={angle_of_attack} -mach_number={mach_number} -reynolds_number={reynolds_number} > log_cfd_simulation.txt 2>&1"
    )

    try:
        # Run in non-blocking background mode
        subprocess.Popen(
            ["bash", "-c", bash_command],
            stdout=subprocess.DEVNULL,  # Don't let child write to our stdout
            stderr=subprocess.DEVNULL,  # Don't let child write to our stderr
            stdin=subprocess.DEVNULL,  # Don't let child read from our stdin
        )
        return TextContent(
            type="text",
            text="CFD simulation started in the background. Progress is being written to log_cfd_simulation.txt. Use airfoil_check_run_status to check if it's finished.",
        )
    except Exception as e:
        return TextContent(
            type="text",
            text=f"Error starting CFD simulation: {str(e)}",
        )


@mcp.tool()
async def airfoil_view_flow_field(
    x_location: float, y_location: float, zoom_in_scale: float, variable: str, frame: int
):
    """
    Airfoil module: Allow users to view the details of a selected flow field variable. The airfoil CFD simulation must have been done.

    Inputs:
        x_location: where to zoom in to view the airfoil mesh details in the x direction. Leading edge: x_location=0, mid chord: x_location=0.5, and trailing edge: x_location=1. Default: 0.5
        y_location: where to zoom in to view the airfoil mesh details in the y direction. Upper surface: y_location>0 (about 0.1), lower surface: y_location<0 (about -0.1). Default: 0
        zoom_in_scale: how much to zoom in to visualize the mesh. Set a smaller zoom_in_scale if users need zoom in more. Set a larger zoom_in_scale if users need to zoom out more. Default: 0.5
        variable: which flow field variable to visualize. Options are "U": velocity, "T": temperature, "p": pressure, "nut": turbulence viscosity (turbulence variable). Default: "p"
        frame: which frame to view. The frame is the time-step for cfd simulation or optimization iteration for optimization. Default: -1 (the last frame)
    Outputs:
        Message indicating the status with HTML link. Must show the link in bold to users.
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"pvpython script_plot_flow_field.py -x_location={x_location} -y_location={y_location} -zoom_in_scale={zoom_in_scale} -variable={variable} -frame={frame}"
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Create a single HTML with both images
        image_files = [
            "plots/airfoil_flow_field.png",
        ]
        image_titles = [f"{variable } Field"]
        combined_html = create_image_html(image_files, image_titles, "Airfoil Flow Field")

        if combined_html:
            return TextContent(
                type="text",
                text=f"Flow field plots successfully generated!\n\nView convergence: http://localhost:{FILE_HTTP_PORT}/{combined_html}",
            )
        else:
            return TextContent(
                type="text",
                text="Plots generated but HTML wrapper creation failed.",
            )
    except subprocess.CalledProcessError as e:
        return TextContent(
            type="text",
            text=f"Error occurred!\n\nStderr:\n{e.stderr}",
        )


@mcp.tool()
async def airfoil_view_residual(
    log_file: str, start_time_cfd: int, end_time_cfd: int, start_time_adjoint: int, end_time_adjoint: int
):
    """
    Plot the residual and function convergence based on the information from the log_file

    Inputs:
        log_file: log_file=log_cfd_simulation.txt for CFD simulation. log_file=log_optimization.txt for optimization
        start_time_cfd: the cfd start time index to plot. Default: 0
        end_time_cfd: the cfd end time index to plot. Default: -1 (last time step)
        start_time_adjoint: the adjoint start time index to plot. Default: 0
        end_time_adjoint: the adjoint end time index to plot. Default: -1 (last time step)
    Outputs:
        Message indicating the status with HTML links. Must show the link in bold to users.
    """

    bash_command = (
        f". /home/dafoamuser/dafoam/loadDAFoam.sh && "
        f"cd {airfoil_path} && "
        f"pvpython script_plot_residual.py -log_file={log_file} -start_time_cfd={start_time_cfd} -end_time_cfd={end_time_cfd} "
        f"-start_time_adjoint={start_time_adjoint} -end_time_adjoint={end_time_adjoint} && "
        f"pvpython script_plot_function.py -log_file={log_file} -start_time={start_time_cfd} -end_time={end_time_cfd} "
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Create a single HTML with both images
        image_files = [
            "plots/airfoil_function_cd.png",
            "plots/airfoil_function_cl.png",
            "plots/airfoil_function_cm.png",
            "plots/airfoil_residual_cfd.png",
        ]
        image_titles = ["CD Convergence", "CL Convergence", "CM Convergence", "CFD Residual Convergence"]
        if log_file == "log_optimization.txt":
            image_files.append("plots/airfoil_residual_adjoint.png")
            image_titles.append("Adjoint Residual Convergence")
        combined_html = create_image_html(image_files, image_titles, "Airfoil Convergence Analysis")

        if combined_html:
            return TextContent(
                type="text",
                text=f"Residual and function plots successfully generated!\n\nView convergence: http://localhost:{FILE_HTTP_PORT}/{combined_html}",
            )
        else:
            return TextContent(
                type="text",
                text="Plots generated but HTML wrapper creation failed.",
            )

    except subprocess.CalledProcessError as e:
        return TextContent(
            type="text",
            text=f"Error occurred!\n\nStderr:\n{e.stderr}",
        )


@mcp.tool()
async def airfoil_view_pressure_profile(mach_number: float, frame: int):
    """
    Airfoil module: Plot the pressure profile (distribution) on the airfoil surface

    Inputs:
        mach_number: The Mach number (Ma). We should use the same mach number set in the airfoil_generate_mesh and airfoil_run_cfd_simulation calls.
        frame: which frame to view. The frame is the time-step for cfd simulation or optimization iteration for optimization. Default: -1 (the last frame)
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
        html_file = create_image_html(
            ["plots/airfoil_pressure_profile.png"], ["Airfoil Pressure Profile"], "Airfoil Pressure Distribution"
        )

        if html_file:
            return TextContent(
                type="text",
                text=f"Pressure profile successfully generated!\n\nView the result: http://localhost:{FILE_HTTP_PORT}/{html_file}",
            )
        else:
            return TextContent(
                type="text",
                text="Image generated but HTML wrapper creation failed.",
            )
    except subprocess.CalledProcessError as e:
        return TextContent(
            type="text",
            text=f"Error occurred!\n\nStderr:\n{e.stderr}",
        )


@mcp.tool()
async def airfoil_view_mesh(x_location: float, y_location: float, zoom_in_scale: float):
    """
    Airfoil module: Allow users to view detail airfoil meshes. The mesh must have been generated in airfoils

    Inputs:
        x_location: where to zoom in to view the airfoil mesh details in the x direction. Leading edge: x_location=0, mid chord: x_location=0.5, and trailing edge: x_location=1. Default: 0.5
        y_location: where to zoom in to view the airfoil mesh details in the y direction. Upper surface: y_location>0 (about 0.1), lower surface: y_location<0 (about -0.1). Default: 0
        zoom_in_scale: how much to zoom in to visualize the mesh. Set a smaller zoom_in_scale if users need zoom in more. Set a larger zoom_in_scale if users need to zoom out more. Default: 0.5
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
        html_file = create_image_html(["plots/airfoil_mesh.png"], ["Airfoil Mesh Visualization"], "Airfoil Mesh")

        if html_file:
            return TextContent(
                type="text",
                text=f"Mesh visualization successfully generated!\n\nView the result: http://localhost:{FILE_HTTP_PORT}/{html_file}",
            )
        else:
            return TextContent(
                type="text",
                text="Image generated but HTML wrapper creation failed.",
            )
    except subprocess.CalledProcessError as e:
        return TextContent(
            type="text",
            text=f"Error occurred!\n\nStderr:\n{e.stderr}",
        )


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
        Message indicating the status with HTML link. Must show the link in bold to users.
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
        f"pvpython script_plot_mesh.py && "
        f"mv plots/airfoil_mesh.png plots/airfoil_mesh_all.png && "
        f"pvpython script_plot_mesh.py -x_location=0 -zoom_in_scale=0.25 && "
        f"mv plots/airfoil_mesh.png plots/airfoil_mesh_le.png && "
        f"pvpython script_plot_mesh.py -x_location=1 -zoom_in_scale=0.25 && "
        f"mv plots/airfoil_mesh.png plots/airfoil_mesh_te.png"
    )

    try:
        # run in non-blocking mode
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: subprocess.run(["bash", "-c", bash_command], capture_output=True, text=True, check=True)
        )

        # Create HTML wrapper using multi-image function
        html_file = create_image_html(
            ["plots/airfoil_mesh_all.png", "plots/airfoil_mesh_le.png", "plots/airfoil_mesh_te.png"],
            [
                f"Airfoil Mesh - {airfoil_profile.upper()} All",
                f"Airfoil Mesh - {airfoil_profile.upper()} Leading Edge",
                f"Airfoil Mesh - {airfoil_profile.upper()} Trailing Edge",
            ],
            f"Mesh Generation: {airfoil_profile.upper()}",
        )

        if html_file:
            return TextContent(
                type="text",
                text=f"Mesh successfully generated for {airfoil_profile}!\n\nView the mesh: http://localhost:{FILE_HTTP_PORT}/{html_file}",
            )
        else:
            return TextContent(
                type="text",
                text="Mesh generated but HTML wrapper creation failed.",
            )
    except subprocess.CalledProcessError as e:
        return TextContent(
            type="text",
            text=f"Error occurred!\n\nStderr:\n{e.stderr}",
        )


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


class CustomHTTPHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler to serve files from airfoil_path"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=airfoil_path + "/plots/", **kwargs)

    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass


def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        # Create a socket to get the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


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


def get_server_url():
    """Get the appropriate server URL based on what's available"""
    local_ip = get_local_ip()

    # Return multiple URL options for user to try
    urls = [
        f"http://localhost:{FILE_HTTP_PORT}",
        f"http://127.0.0.1:{FILE_HTTP_PORT}",
        f"http://{local_ip}:{FILE_HTTP_PORT}",
    ]
    return urls


def create_image_html(image_files: list, titles: list, main_title: str = "Airfoil Visualization") -> str:
    """
    Create an HTML wrapper for multiple images displayed side by side with embedded base64 images

    Inputs:
        image_files: List of image filenames (e.g., ['image1.png', 'image2.png'])
        titles: List of titles for each image
        main_title: Main title for the HTML page
    Outputs:
        html_filename: Name of the created HTML file
    """
    if len(image_files) != len(titles):
        return None

    # Read all images and convert to base64
    image_data_list = []
    for i, image_filename in enumerate(image_files):
        image_path = Path(airfoil_path) / image_filename
        if not image_path.exists():
            continue

        with open(image_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode("utf-8")

        # Determine image type
        img_extension = image_path.suffix.lower()
        mime_type = "image/png" if img_extension == ".png" else "image/jpeg"

        image_data_list.append({"data": img_data, "mime": mime_type, "filename": image_filename, "title": titles[i]})

    if not image_data_list:
        return None

    # Create image sections HTML
    image_sections = ""
    for img_info in image_data_list:
        image_sections += f"""
        <div class="image-section">
            <h2>{img_info['title']}</h2>
            <div class="image-container">
                <img src="data:{img_info['mime']};base64,{img_info['data']}" alt="{img_info['title']}">
            </div>
            <div class="image-info">
                <p>Image: {img_info['filename']}</p>
                <a href="data:{img_info['mime']};base64,{img_info['data']}" download="{img_info['filename']}" class="download-btn">
                    Download Image
                </a>
            </div>
        </div>
        """

    # Add server status information
    server_status = ""
    if server_started:
        urls = get_server_url()
        server_status = f"""
        <div class="server-info">
            <h3>Alternative Access URLs:</h3>
            <p>If the main link doesn't work, try these:</p>
            <ul>
                {''.join([f'<li><a href="{url}" target="_blank">{url}</a></li>' for url in urls])}
            </ul>
            <p style="font-size: 12px; color: #666; margin-top: 10px;">
                Note: Images are embedded in this HTML file and don't require server access.
                You can save this HTML file and open it offline.
            </p>
        </div>
        """

    # Create HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{main_title}</title>
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
        <h1>{main_title}</h1>
        {image_sections}
        {server_status}
    </div>
</body>
</html>"""

    # Save HTML file - use first image name or generic name
    html_filename = "airfoil_plots.html"

    html_path = Path(airfoil_path) / "plots" / html_filename

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_filename


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
