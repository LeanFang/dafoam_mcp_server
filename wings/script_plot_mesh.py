# trace generated using paraview version 5.9.1

# import the simple module from the paraview
from paraview.simple import *
import argparse

# disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

parser = argparse.ArgumentParser()
parser.add_argument(
    "-mean_chord",
    help="mean chord along the span",
    type=float,
    default=1.0,
)
parser.add_argument(
    "-span",
    help="span",
    type=float,
    default=3.0,
)
args = parser.parse_args()

span = args.span
zoom_in_scale = span * 0.4
mean_chord = args.mean_chord
mean_span = span / 2.0

# create a new 'OpenFOAMReader'
paraviewfoam = OpenFOAMReader(registrationName='paraview.foam', FileName='paraview.foam')

# get active view
renderView1 = GetActiveViewOrCreate('RenderView')

# show data in view
paraviewfoamDisplay = Show(paraviewfoam, renderView1, 'UnstructuredGridRepresentation')

# trace defaults for the display properties.
paraviewfoamDisplay.Representation = 'Surface'

# change representation type
paraviewfoamDisplay.SetRepresentationType('Surface With Edges')


# Properties modified on renderView1
renderView1.CameraParallelProjection = 1

# Properties modified on paraviewfoam
paraviewfoam.MeshRegions = ['symmetry', 'wing']

# update the view to ensure updated data information
renderView1.Update()

# current camera placement for renderView1
renderView1.CameraPosition = [mean_chord, 0.0, 10]
renderView1.CameraFocalPoint = [mean_chord, 0.0, 0]
renderView1.CameraParallelScale = zoom_in_scale * 0.5
renderView1.CameraViewUp = [0.0, 1.0, 0.0]

# save screenshot
SaveScreenshot("plots/wing_mesh_view_z.png", renderView1, ImageResolution=[1923, 1158])

# current camera placement for renderView1
renderView1.CameraPosition = [mean_chord, 10.0, mean_span]
renderView1.CameraFocalPoint = [mean_chord, 0.0, mean_span]
renderView1.CameraParallelScale = zoom_in_scale
renderView1.CameraViewUp = [1.0, 0.0, 0.0]

# save screenshot
SaveScreenshot("plots/wing_mesh_view_y.png", renderView1, ImageResolution=[1923, 1158])

# current camera placement for renderView1
renderView1.CameraPosition = [-10.0, 0.0, mean_span]
renderView1.CameraFocalPoint = [0, 0.0, mean_span]
renderView1.CameraParallelScale = zoom_in_scale
renderView1.CameraViewUp = [0.0, 1.0, 0.0]

# save screenshot
SaveScreenshot("plots/wing_mesh_view_x.png", renderView1, ImageResolution=[1923, 1158])

# current camera placement for renderView1
renderView1.CameraPosition = [mean_chord - 10.0, 10.0, mean_span + 10.0]
renderView1.CameraFocalPoint = [mean_chord, 0.0, mean_span]
renderView1.CameraParallelScale = zoom_in_scale
renderView1.CameraViewUp = [1.0, 1.0, -1.0]

# save screenshot
SaveScreenshot("plots/wing_mesh_view_3d.png", renderView1, ImageResolution=[1923, 1158])
