from trame.app import get_server
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vtk, vuetify3
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkActor,
    vtkDataSetMapper,
)
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa
import vtkmodules.vtkRenderingOpenGL2  # noqa
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-mesh_file", help="mesh file to load", type=str, default="VTK/wings_0/boundary.vtp")
args = parser.parse_args()

mesh_file = args.mesh_file
port = 8002

# VTK Pipeline
reader = vtkXMLPolyDataReader()
reader.SetFileName(mesh_file)
reader.Update()
mapper = vtkDataSetMapper()
mapper.SetInputConnection(reader.GetOutputPort())
actor = vtkActor()
actor.SetMapper(mapper)
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
renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
renderer.ResetCamera()
camera = renderer.GetActiveCamera()
camera.Azimuth(-45)
camera.Elevation(30)
camera.Zoom(10)
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
            view = vtk.VtkRemoteView(renderWindow)
            ctrl.view_update = view.update
            ctrl.view_reset_camera = view.reset_camera


server.start(host="0.0.0.0", port=port)
