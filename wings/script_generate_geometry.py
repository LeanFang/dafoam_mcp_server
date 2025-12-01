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
rot_z = args.spanwise_twists
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

wing.writeTecplot("wing.dat")
wing.writeIGES("wing.igs")


gmsh.initialize()
gmsh.option.setNumber("Geometry.OCCScaling", 0.001)
gmsh.merge("wing.igs")

# Synchronize to make entities available
gmsh.model.occ.synchronize()

# List all surfaces to see what you have
surfaces = gmsh.model.getEntities(dim=2)
print("Surfaces found:", surfaces)

for surf in surfaces:
    bbox = gmsh.model.getBoundingBox(surf[0], surf[1])
    print(
        f"Surface {surf[1]}: xmin={bbox[0]:.4f}, xmax={bbox[3]:.4f}, "
        f"ymin={bbox[1]:.4f}, ymax={bbox[4]:.4f}, zmin={bbox[2]:.4f}, zmax={bbox[5]:.4f}"
    )

gmsh.model.addPhysicalGroup(2, [1], tag=1, name="wing_upper")  # Main wing surfaces
gmsh.model.addPhysicalGroup(2, [2], tag=2, name="wing_lower")  # Main wing surfaces
gmsh.model.addPhysicalGroup(2, [3], tag=3, name="te")  # TE surface
gmsh.model.addPhysicalGroup(2, [4, 5], tag=4, name="tip")  # TE surface
gmsh.option.setNumber("Geometry.Tolerance", 1e-8)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 100)
gmsh.option.setNumber("Mesh.MeshSizeMin", 0.005)
gmsh.option.setNumber("Mesh.MeshSizeMax", 0.05)
gmsh.option.setNumber("Mesh.MinimumCirclePoints", 100)
gmsh.option.setNumber("Mesh.Algorithm", 5)
gmsh.model.mesh.generate(2)
# Save physical groups in STL
gmsh.option.setNumber("Mesh.StlOneSolidPerSurface", 2)  # One solid per physical group
gmsh.write("wing.stl")
gmsh.finalize()
