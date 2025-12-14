from pygeo.geo_utils import createFittedWingFFD
import argparse
import numpy as np
from stl.mesh import Mesh

parser = argparse.ArgumentParser()
parser.add_argument(
    "-spanwise_chords",
    help="airfoil chords for each spanwise section",
    nargs="+",
    type=float,
    default=[1.0, 1.0],
)
parser.add_argument(
    "-spanwise_x",
    help="airfoil x coordination for each spanwise section",
    nargs="+",
    type=float,
    default=[0.0, 0.0],
)
parser.add_argument(
    "-spanwise_z",
    help="airfoil x coordination for each spanwise section",
    nargs="+",
    type=float,
    default=[0.0, 3.0],
)
parser.add_argument(
    "-spanwise_twists",
    help="airfoil profile twist for each spanwise section",
    nargs="+",
    type=float,
    default=[0.0, 0.0],
)
args = parser.parse_args()

# Scale all dimensions from millimeters to meters so that the tolerances match a regular use case
nSections = len(args.spanwise_chords)
leList = np.zeros((nSections, 3))
teList = np.zeros((nSections, 3))
chord = args.spanwise_chords
x = args.spanwise_x
z = args.spanwise_z
twist = args.spanwise_twists

for i in range(nSections):
    leList[i, 0] = x[i] + 0.01
    leList[i, 1] = -100.0
    leList[i, 2] = max(z[i], 0.01)
    teList[i, 0] = x[i] + chord[i] * float(np.cos(np.radians(twist[i]))) - 0.01
    teList[i, 1] = -100.0
    teList[i, 2] = max(z[i], 0.01)

# Get the surface definition from the STL file
stlMesh = Mesh.from_file("constant/triSurface/wing.stl")
p0 = stlMesh.vectors[:, 0, :]
p1 = stlMesh.vectors[:, 1, :]
p2 = stlMesh.vectors[:, 2, :]
surf = [p0, p1, p2]
surfFormat = "point-point"
# Set the other FFD generation inputs
outFile = "FFD/FFD.xyz"
nSpan = 5
nChord = 8
relMargins = [0.02, 0.01, 0.2]
absMargins = [0.04, 0.02, 0.02]
liftIndex = 2
createFittedWingFFD(surf, surfFormat, outFile, leList, teList, nSpan, nChord, absMargins, relMargins, liftIndex)
