"""
Sample usage script showing some use cases, and how the API should work.
"""

from prefoil import Airfoil, sampling
from prefoil.utils import readCoordFile
import matplotlib.pyplot as plt
from pyhyp import pyHyp
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("-airfoil_profile", help="name of the airfoil profile", type=str, default="naca0012")
parser.add_argument("-mesh_cells", help="number of mesh cells", type=int, default=50000)
parser.add_argument("-y_plus", help="yPlus, the normalized near wall mesh size", type=float, default=3.0)
parser.add_argument("-n_ffd_points", help="The number of FFD control points", type=int, default=10)
parser.add_argument(
    "-mach_ref", help="The reference Mach number to estimate the near wall mesh size", type=float, default=0.1
)
args = parser.parse_args()


# users need to prescribe the airfoil profile name (no spaces)
airfoil_profile = args.airfoil_profile
# the ratio between the surface points and extruded points
mesh_ratio = 1.8
n_surf_points = int(np.sqrt(args.mesh_cells) * mesh_ratio)
n_extrude = int(np.sqrt(args.mesh_cells) / mesh_ratio)
n_ffd_points = args.n_ffd_points
distribution_coeff = 1.0
# estimate the trailing mesh points
n_trailing_points = int(args.mesh_cells / 20000) + 3
# estimate y0_wall based on yPlus. y0=1e-5 is yPlus=1 at Mach=0.2
y0_wall = args.y_plus * (0.2 / args.mach_ref) * 1e-5

"""
Here we read an airfoil coordinate file from a database, perform geometric
cleanup, and then sample it with a particular distribution.
"""
# Read the Coordinate file
filename = "./profiles/" + airfoil_profile.lower() + ".dat"
coords = readCoordFile(filename)
airfoil = Airfoil(coords)
airfoil.makeBluntTE(xCut=0.99)
coords = airfoil.getSampledPts(
    n_surf_points, spacingFunc=sampling.conical, nTEPts=n_trailing_points, func_args={"coeff": distribution_coeff}
)

# Write surface mesh
airfoil.writeCoords("surfMesh", file_format="plot3d")

# Write a fitted FFD with n_ffd_points chordwise points
airfoil.generateFFD(n_ffd_points, "FFD", xmargin=0.025, ymarginu=0.05, ymarginl=0.05)

# extrude volume mesh
options = {
    # ---------------------------
    #        Input Parameters
    # ---------------------------
    "inputFile": "surfMesh.xyz",
    "unattachedEdgesAreSymmetry": False,
    "outerFaceBC": "farfield",
    "autoConnect": True,
    "BC": {1: {"jLow": "zSymm", "jHigh": "zSymm"}},
    "families": "wall",
    # ---------------------------
    #        Grid Parameters
    # ---------------------------
    "N": n_extrude,
    "s0": y0_wall,
    "marchDist": 30.0,
    # ---------------------------
    #   Pseudo Grid Parameters
    # ---------------------------
    "ps0": -1.0,
    "pGridRatio": -1.0,
    "cMax": 1.0,
    # ---------------------------
    #   Smoothing parameters
    # ---------------------------
    "epsE": 2.0,
    "epsI": 4.0,
    "theta": 2.0,
    "volCoef": 0.20,
    "volBlend": 0.0005,
    "volSmoothIter": 20,
}


hyp = pyHyp(options=options)
hyp.run()
hyp.writePlot3D("volumeMesh.xyz")
