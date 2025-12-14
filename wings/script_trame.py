from trame.app import get_server
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vtk, vuetify3
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
from vtkmodules.vtkIOGeometry import vtkSTLReader
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkActor,
    vtkDataSetMapper,
)
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
import vtkmodules.vtkRenderingOpenGL2  # noqa
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("-mesh_file", help="mesh file to load (.stl or .vtp)", type=str, default="VTK/wings_0/boundary.vtp")
parser.add_argument("-focal_x", help="x for focal point", type=float, default=0.5)
parser.add_argument("-focal_z", help="z for focal point", type=float, default=1.5)
args = parser.parse_args()

mesh_file = args.mesh_file
focal_x = args.focal_x
focal_y = 0.0
focal_z = args.focal_z
port = 8002

# VTK Pipeline - detect file type and use appropriate reader
file_ext = os.path.splitext(mesh_file)[1].lower()
if file_ext == ".stl":
    reader = vtkSTLReader()
    reader.SetFileName(mesh_file)
elif file_ext == ".vtp":
    reader = vtkXMLPolyDataReader()
    reader.SetFileName(mesh_file)
else:
    raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: .stl, .vtp")

reader.Update()
mapper = vtkDataSetMapper()
mapper.SetInputConnection(reader.GetOutputPort())
actor = vtkActor()
actor.SetMapper(mapper)

# For STL, show surface only; for VTP mesh, show edges
if file_ext == ".stl":
    actor.GetProperty().EdgeVisibilityOff()
else:
    actor.GetProperty().EdgeVisibilityOn()

renderer = vtkRenderer()
renderer.AddActor(actor)
renderer.GetActiveCamera().ParallelProjectionOn()
renderer.SetBackground(1.0, 1.0, 1.0)
renderWindow = vtkRenderWindow()
renderWindow.AddRenderer(renderer)
renderWindow.OffScreenRenderingOn()
renderWindowInteractor = vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

# Set interaction style to trackball camera for rotation
interactorStyle = vtkInteractorStyleTrackballCamera()
renderWindowInteractor.SetInteractorStyle(interactorStyle)

# Set up camera for isometric view
renderer.ResetCamera()
camera = renderer.GetActiveCamera()

# Set focal point based on mean_chord and span
camera.SetFocalPoint(focal_x, focal_y, focal_z)

# Set up isometric view (45 degrees from x and y, 35.264 degrees elevation for true isometric)
camera.Azimuth(-45)
camera.Elevation(35.264)

renderWindow.Render()
camera.SetClippingRange(0.1, 1000.0)

# Trame GUI
server = get_server()
ctrl = server.controller

with SinglePageLayout(server) as layout:
    layout.title.set_text("DAFoam Mesh Viewer")

    with layout.toolbar:
        vuetify3.VBtn("Reset View", click=ctrl.view_reset_camera)

    with layout.content:
        with vuetify3.VContainer(fluid=True, classes="pa-0 fill-height"):
            view = vtk.VtkLocalView(renderWindow)
            ctrl.view_update = view.update
            ctrl.view_reset_camera = view.reset_camera


server.start(host="0.0.0.0", port=port)
