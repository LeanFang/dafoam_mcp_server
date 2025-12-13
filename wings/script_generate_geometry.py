from pygeo import pyGeo
import argparse
import numpy as np
import gmsh


parser = argparse.ArgumentParser()
parser.add_argument(
    "-spanwise_airfoil_profiles",
    help="airfoil profiles for each spanwise section",
    nargs="+",
    type=str,
    default=["naca0012", "naca0012"],
)
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
    "-spanwise_y",
    help="airfoil y coordination for each spanwise section",
    nargs="+",
    type=float,
    default=[0.0, 0.0],
)
parser.add_argument(
    "-spanwise_z",
    help="airfoil z coordination for each spanwise section",
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

nSections = len(args.spanwise_airfoil_profiles)
# Prepend 'profiles/' folder to each airfoil name
airfoil_list = [f"profiles/{airfoil}.dat" for airfoil in args.spanwise_airfoil_profiles]
chord = args.spanwise_chords
x = args.spanwise_x
y = args.spanwise_y
z = args.spanwise_z
rot_x = np.zeros(nSections)
rot_y = np.zeros(nSections)
# NOTE: we treat nose up as positive twist
rot_z = -np.array(args.spanwise_twists)
offset = np.zeros((nSections, 2))

wing = pyGeo(
    "liftingSurface",
    xsections=airfoil_list,
    scale=chord,
    offset=offset,
    x=x,
    y=y,
    z=z,
    rotX=rot_x,
    rotY=rot_y,
    rotZ=rot_z,
    bluntTe=True,
    teHeightScaled=0.01,
    kSpan=2,
    tip="rounded",
)

# wing.writeTecplot("wing.dat")
wing.writeIGES("wing_mm.iges")
