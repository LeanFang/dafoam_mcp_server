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
    "-wing_span",
    help="span",
    type=float,
    default=3.0,
)
args = parser.parse_args()

wing_span = args.wing_span
zoom_in_scale = wing_span * 0.4
focal_x = args.mean_chord / 2.0
focal_z = wing_span / 2.0

# create a new 'OpenFOAMReader'
paraviewfoam = OpenFOAMReader(registrationName="paraview.foam", FileName="paraview.foam")

# get active view
renderView1 = GetActiveViewOrCreate("RenderView")

# show data in view
paraviewfoamDisplay = Show(paraviewfoam, renderView1, "UnstructuredGridRepresentation")

# trace defaults for the display properties.
paraviewfoamDisplay.Representation = "Surface"

# change representation type
paraviewfoamDisplay.SetRepresentationType("Surface With Edges")

fFDdat = TecplotReader(registrationName="FFD.dat", FileNames=["./FFD/FFD.dat"])

# show data in view
fFDdatDisplay = Show(fFDdat, renderView1, "StructuredGridRepresentation")

# change representation type
fFDdatDisplay.SetRepresentationType("Points")

# Properties modified on fFDdatDisplay
fFDdatDisplay.PointSize = 10.0

# change solid color
fFDdatDisplay.AmbientColor = [0.6666666666666666, 0.0, 0.0]
fFDdatDisplay.DiffuseColor = [0.6666666666666666, 0.0, 0.0]


# Properties modified on renderView1
renderView1.CameraParallelProjection = 1

# Properties modified on paraviewfoam
paraviewfoam.MeshRegions = ["patch/sym", "patch/wing"]

# update the view to ensure updated data information
renderView1.Update()

text1 = Text(registrationName="Wing Mesh: Z view")
text1.Text = f"Wing Mesh: Z view"
text1Display = Show(text1, renderView1, "TextSourceRepresentation")
renderView1.Update()
text1Display.FontSize = 15
text1Display.WindowLocation = "Upper Center"
text1Display.Bold = 1
text1Display.FontFamily = "Arial"
text1Display.Color = [0.0, 0.0, 0.0]

# current camera placement for renderView1
renderView1.CameraPosition = [focal_x, 0.0, 10]
renderView1.CameraFocalPoint = [focal_x, 0.0, 0]
renderView1.CameraParallelScale = zoom_in_scale * 0.5
renderView1.CameraViewUp = [0.0, 1.0, 0.0]

# save screenshot
SaveScreenshot("plots/wing_mesh_view_z.png", renderView1, ImageResolution=[1923, 1158])

text1.Text = f"Wing Mesh: Y view"
renderView1.Update()

# current camera placement for renderView1
renderView1.CameraPosition = [focal_x, 10.0, focal_z]
renderView1.CameraFocalPoint = [focal_x, 0.0, focal_z]
renderView1.CameraParallelScale = zoom_in_scale
renderView1.CameraViewUp = [1.0, 0.0, 0.0]

# save screenshot
SaveScreenshot("plots/wing_mesh_view_y.png", renderView1, ImageResolution=[1923, 1158])

text1.Text = f"Wing Mesh: X view"
renderView1.Update()

# current camera placement for renderView1
renderView1.CameraPosition = [-10.0, 0.0, focal_z]
renderView1.CameraFocalPoint = [0, 0.0, focal_z]
renderView1.CameraParallelScale = zoom_in_scale
renderView1.CameraViewUp = [0.0, 1.0, 0.0]

# save screenshot
SaveScreenshot("plots/wing_mesh_view_x.png", renderView1, ImageResolution=[1923, 1158])

text1.Text = f"Wing Mesh: 3D view"
renderView1.Update()

# current camera placement for renderView1
renderView1.CameraPosition = [focal_x - 10.0, 10.0, focal_z + 10.0]
renderView1.CameraFocalPoint = [focal_x, 0.0, focal_z]
renderView1.CameraParallelScale = zoom_in_scale
renderView1.CameraViewUp = [1.0, 1.0, -1.0]

# save screenshot
SaveScreenshot("plots/wing_mesh_view_3d.png", renderView1, ImageResolution=[1923, 1158])
