# trace generated using paraview version 5.9.1

# import the simple module from the paraview
from paraview.simple import *
import argparse

# disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

parser = argparse.ArgumentParser()
parser.add_argument(
    "-spanwise_chords",
    help="airfoil chords for each spanwise section",
    nargs="+",
    type=float,
    default=[1.0, 1.0],
)
parser.add_argument(
    "-spanwise_z",
    help="airfoil z coordination for each spanwise section",
    nargs="+",
    type=float,
    default=[0.0, 3.0],
)
args = parser.parse_args()

# 0.4 scale = 1.0 m span
span = args.spanwise_z[-1] - args.spanwise_z[0]
zoom_in_scale = span * 0.4
mean_chord = sum(args.spanwise_chords) / len(args.spanwise_chords)
mean_span = span / 2.0

# create a new 'STL Reader'
wingstl = STLReader(registrationName="wing.stl", FileNames=["wing.stl"])

# get active view
renderView1 = GetActiveViewOrCreate("RenderView")

# show data in view
wingstlDisplay = Show(wingstl, renderView1, "GeometryRepresentation")

# trace defaults for the display properties.
wingstlDisplay.Representation = "Surface"

# turn off scalar coloring
ColorBy(wingstlDisplay, None)

# get color transfer function/color map for 'STLSolidLabeling'
sTLSolidLabelingLUT = GetColorTransferFunction("STLSolidLabeling")

# Hide the scalar bar for this color map if no visible data is colored by it.
HideScalarBarIfNotNeeded(sTLSolidLabelingLUT, renderView1)

# Properties modified on renderView1
renderView1.CameraParallelProjection = 1

# Properties modified on renderView1
# renderView1.Background = [1.0, 1.0, 1.0]

text1 = Text(registrationName="Wing Geometry: Z view")
text1.Text = f"Wing Geometry: Z view"
text1Display = Show(text1, renderView1, "TextSourceRepresentation")
renderView1.Update()
text1Display.FontSize = 50
text1Display.WindowLocation = "UpperCenter"
text1Display.Bold = 1
text1Display.FontFamily = "Arial"
text1Display.Color = [0.0, 0.0, 0.0]

# current camera placement for renderView1
renderView1.CameraPosition = [mean_chord, 0.0, 10]
renderView1.CameraFocalPoint = [mean_chord, 0.0, 0]
renderView1.CameraParallelScale = zoom_in_scale * 0.5
renderView1.CameraViewUp = [0.0, 1.0, 0.0]

# save screenshot
SaveScreenshot("plots/wing_geometry_view_z.png", renderView1, ImageResolution=[1923, 1158])

text1.Text = f"Wing Geometry: Y view"
renderView1.Update()

# current camera placement for renderView1
renderView1.CameraPosition = [mean_chord, 10.0, mean_span]
renderView1.CameraFocalPoint = [mean_chord, 0.0, mean_span]
renderView1.CameraParallelScale = zoom_in_scale
renderView1.CameraViewUp = [1.0, 0.0, 0.0]

# save screenshot
SaveScreenshot("plots/wing_geometry_view_y.png", renderView1, ImageResolution=[1923, 1158])

# current camera placement for renderView1
renderView1.CameraPosition = [-10.0, 0.0, mean_span]
renderView1.CameraFocalPoint = [0, 0.0, mean_span]
renderView1.CameraParallelScale = zoom_in_scale
renderView1.CameraViewUp = [0.0, 1.0, 0.0]

text1.Text = f"Wing Geometry: X view"
renderView1.Update()

# save screenshot
SaveScreenshot("plots/wing_geometry_view_x.png", renderView1, ImageResolution=[1923, 1158])

text1.Text = f"Wing Geometry: 3D view"
renderView1.Update()

# current camera placement for renderView1
renderView1.CameraPosition = [mean_chord - 10.0, 10.0, mean_span + 10.0]
renderView1.CameraFocalPoint = [mean_chord, 0.0, mean_span]
renderView1.CameraParallelScale = zoom_in_scale
renderView1.CameraViewUp = [1.0, 1.0, -1.0]

# save screenshot
SaveScreenshot("plots/wing_geometry_view_3d.png", renderView1, ImageResolution=[1923, 1158])
