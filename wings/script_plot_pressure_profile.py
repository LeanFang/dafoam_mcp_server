# trace generated using paraview version 5.9.1

#### import the simple module from the paraview
from paraview.simple import *
import argparse, os
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument("-mach_number", help="mach number", type=float, default=0.1)
parser.add_argument("-frame", help="which frame to visualize", type=int, default=-1)
parser.add_argument("-span", help="total span length", type=float, default=1.0)
parser.add_argument(
    "-spanwise_chords",
    help="chord lengths at 10, 50, and 90 percent of the span",
    nargs="+",
    type=float,
    default=[1.0, 1.0, 1.0],
)
args = parser.parse_args()

# Parse spanwise_chords
chords = args.spanwise_chords
span_locations = [0.1 * args.span, 0.5 * args.span, 0.9 * args.span]
span_labels = ["10_percent_span", "50_percent_span", "90_percent_span"]

C0 = 347.2
U0 = args.mach_number * C0
rho0 = 1.1768
coeff = 0.5 * rho0 * U0 * U0

#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# create a new 'OpenFOAMReader'
paraviewfoam = OpenFOAMReader(registrationName="paraview.foam", FileName="./paraview.foam")

# if it is a parallel run, choose Decomposed Case
if os.path.exists("processor0"):
    paraviewfoam.CaseType = "Decomposed Case"

# get animation scene
animationScene1 = GetAnimationScene()

# update animation scene based on data timesteps
animationScene1.UpdateAnimationUsingDataTimeSteps()

# get active view
renderView1 = GetActiveViewOrCreate("RenderView")

# show data in view
paraviewfoamDisplay = Show(paraviewfoam, renderView1, "UnstructuredGridRepresentation")

# trace defaults for the display properties.
paraviewfoamDisplay.Representation = "Surface"

# Properties modified on renderView1
renderView1.CameraParallelProjection = 1

# Properties modified on paraviewfoam
# In ParaView 5.13, the mesh region is 'patch/wing' not 'wing'
paraviewfoam.MeshRegions = ["patch/wing"]

# Enable the pressure array for ParaView 5.13
paraviewfoam.CellArrays = ['p']

# go to the specific frame
if args.frame == -1:
    # Get all available time steps
    animationScene1 = GetAnimationScene()
    time_steps = animationScene1.TimeKeeper.TimestepValues

    # Loop through all time steps from last to first
    for idx, time_value in enumerate(reversed(time_steps)):
        animationScene1.AnimationTime = time_value
        UpdatePipeline(time_value)

        if time_value < 1.0:
            iterI = "%04d" % int(time_value * 10000)
        else:
            iterI = "Final"

        # Loop through each spanwise location
        for span_loc, chord, label in zip(span_locations, chords, span_labels):
            # create a new 'Slice'
            slice1 = Slice(registrationName="Slice1", Input=paraviewfoam)

            # Properties modified on slice1.SliceType
            slice1.SliceType.Origin = [0.0, 0.0, span_loc]
            slice1.SliceType.Normal = [0.0, 0.0, 1.0]

            # create a new 'Plot On Sorted Lines'
            plotOnSortedLines1 = PlotOnSortedLines(registrationName="PlotOnSortedLines1", Input=slice1)

            # Fetch the data to the client
            multi_block_data = servermanager.Fetch(plotOnSortedLines1)

            # Navigate through the nested structure (ParaView 5.13)
            patches = multi_block_data.GetBlock(0)
            wing = patches.GetBlock(0)
            data = wing

            # Now you can get the point data
            point_data = data.GetPointData()

            # Get number of points
            n_points = data.GetNumberOfPoints()

            # Get coordinates (x, y, z)
            points = np.array([data.GetPoint(i) for i in range(n_points)])
            x = points[:, 0]
            y = points[:, 1]
            z = points[:, 2]

            # Normalize by chord
            x = x / chord
            y = y / chord

            # Get pressure (p)
            p_array = point_data.GetArray("p")
            p = np.array([p_array.GetValue(i) for i in range(p_array.GetNumberOfTuples())])
            cp = (p - 101325.0) / coeff

            # Create figure with two subplots, share x-axis
            fig, (ax1, ax2) = plt.subplots(
                2,
                1,
                figsize=(10, 8),
                gridspec_kw={"height_ratios": [2, 1], "hspace": 0.05},
            )

            # Top plot: Cp vs x/c (complete distribution)
            ax1.set_title(
                f"Pressure profile on the airfoil. Iteration = {iterI}. Mach = {args.mach_number}. Span = {label}",
                fontsize=18,
                fontweight="bold",
            )
            ax1.plot(x, cp, "-k", linewidth=2)
            ax1.set_ylim([-2, 2])
            ax1.invert_yaxis()  # Invert y-axis for Cp plot (standard in aerodynamics)
            ax1.set_ylabel("$C_p$", fontsize=16, fontweight="bold")
            ax1.tick_params(axis="x", labelsize=15)
            ax1.tick_params(axis="y", labelsize=15)
            # Completely remove x-axis for top plot
            ax1.spines["bottom"].set_visible(False)
            ax1.set_xticks([])
            # Remove top and right spines
            ax1.spines["top"].set_visible(False)
            ax1.spines["right"].set_visible(False)

            # Bottom plot: Airfoil profile
            ax2.plot(x, y, "-k", linewidth=2)
            ax2.set_xlabel("x/c", fontsize=16, fontweight="bold")
            ax2.set_ylabel("y/c", fontsize=16, fontweight="bold")
            ax2.tick_params(axis="x", labelsize=15)
            ax2.tick_params(axis="y", labelsize=15)
            ax2.set_aspect("equal", adjustable="datalim")
            ax2.set_xlim([-0.05, 1.05])
            # Remove top and right spines
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_visible(False)

            # Use frame index in filename to ensure unique names
            plt.savefig(
                f"plots/wing_pressure_profile_{iterI}_{label}.png",
                dpi=200,
                bbox_inches="tight",
            )
            plt.close()

            # Clean up
            Delete(plotOnSortedLines1)
            Delete(slice1)

else:
    time_value = args.frame * 0.0001
    if time_value < 1.0:
        iterI = "%04d" % int(time_value * 10000)
    else:
        iterI = "Final"
    animationScene1.AnimationTime = time_value
    UpdatePipeline()

    # Loop through each spanwise location
    for span_loc, chord, label in zip(span_locations, chords, span_labels):
        # create a new 'Slice'
        slice1 = Slice(registrationName="Slice1", Input=paraviewfoam)

        # Properties modified on slice1.SliceType
        slice1.SliceType.Origin = [0.0, 0.0, span_loc]
        slice1.SliceType.Normal = [0.0, 0.0, 1.0]

        # create a new 'Plot On Sorted Lines'
        plotOnSortedLines1 = PlotOnSortedLines(registrationName="PlotOnSortedLines1", Input=slice1)

        # Fetch and plot for specific frame (same code as in loop)
        multi_block_data = servermanager.Fetch(plotOnSortedLines1)
        patches = multi_block_data.GetBlock(0)
        wing = patches.GetBlock(0)
        data = wing
        point_data = data.GetPointData()
        n_points = data.GetNumberOfPoints()
        points = np.array([data.GetPoint(i) for i in range(n_points)])
        x = points[:, 0]
        y = points[:, 1]

        # Normalize by chord
        x = x / chord
        y = y / chord

        p_array = point_data.GetArray("p")
        p = np.array([p_array.GetValue(i) for i in range(p_array.GetNumberOfTuples())])
        cp = (p - 101325.0) / coeff

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={"height_ratios": [2, 1], "hspace": 0.05})
        ax1.set_title(
            f"Pressure profile on the airfoil. Iteration = {iterI}. Mach = {args.mach_number}. Span = {label}",
            fontsize=18,
            fontweight="bold",
        )
        ax1.plot(x, cp, "-k", linewidth=2)
        ax1.set_ylim([-2, 2])
        ax1.invert_yaxis()
        ax1.set_ylabel("$C_p$", fontsize=16, fontweight="bold")
        ax1.tick_params(axis="x", labelsize=15)
        ax1.tick_params(axis="y", labelsize=15)
        ax1.spines["bottom"].set_visible(False)
        ax1.set_xticks([])
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
        ax2.plot(x, y, "-k", linewidth=2)
        ax2.set_xlabel("x/c", fontsize=16, fontweight="bold")
        ax2.set_ylabel("y/c", fontsize=16, fontweight="bold")
        ax2.tick_params(axis="x", labelsize=15)
        ax2.tick_params(axis="y", labelsize=15)
        ax2.set_aspect("equal", adjustable="datalim")
        ax2.set_xlim([-0.05, 1.05])
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        plt.savefig(
            f"plots/airfoil_pressure_profile_{iterI}_{label}.png",
            dpi=200,
            bbox_inches="tight",
        )
        plt.close()

        # Clean up
        Delete(plotOnSortedLines1)
        Delete(slice1)
