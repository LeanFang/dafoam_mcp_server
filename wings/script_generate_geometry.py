from pygeo import pyGeo
import argparse
import numpy as np
import gmsh

parser = argparse.ArgumentParser()
parser.add_argument("-airfoil_profile", help="name of the airfoil profile", type=str, default="naca0012")
parser.add_argument("-mesh_cells", help="number of mesh cells", type=int, default=50000)
parser.add_argument("-y_plus", help="yPlus, the normalized near wall mesh size", type=float, default=3.0)
parser.add_argument("-n_ffd_points", help="The number of FFD control points", type=int, default=10)
parser.add_argument(
    "-mach_number", help="The reference Mach number to estimate the near wall mesh size", type=float, default=0.1
)
args = parser.parse_args()

nSections = 2
airfoil_list = ["profiles/naca0012.dat", "profiles/naca0012.dat"]
chord = [1.0, 1.0]
x = [0, 0]
y = [0, 0]
z = [0, 3]
rot_x = [0, 0, 0]
rot_y = [0, 0, 0]
rot_z = [0, 0, 0]
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

gmsh.model.addPhysicalGroup(2, [1, 2], tag=1, name="wing")  # Main wing surfaces
gmsh.model.addPhysicalGroup(2, [3], tag=2, name="te")  # TE surface
gmsh.model.addPhysicalGroup(2, [4, 5], tag=3, name="tip")  # TE surface
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
