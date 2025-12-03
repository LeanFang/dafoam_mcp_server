# trace generated using paraview version 5.9.1

# import the simple module from the paraview
from paraview.simple import *
import argparse, os

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
parser.add_argument("-variable", help="flow field variable to plot", type=str, default="p")
args = parser.parse_args()

span = args.span
zoom_in_scale = span * 0.4
mean_chord = args.mean_chord
mean_span = span / 2.0

# create a new 'OpenFOAMReader'
paraviewfoam = OpenFOAMReader(registrationName='paraview.foam', FileName='paraview.foam')

# if it is a parallel run, choose Decomposed Case
if os.path.exists("processor0"):
    paraviewfoam.CaseType = "Decomposed Case"

# get active view
renderView1 = GetActiveViewOrCreate('RenderView')

# show data in view
paraviewfoamDisplay = Show(paraviewfoam, renderView1, 'UnstructuredGridRepresentation')

# trace defaults for the display properties.
paraviewfoamDisplay.Representation = 'Surface'

# Properties modified on renderView1
renderView1.CameraParallelProjection = 1

# Properties modified on paraviewfoam
paraviewfoam.MeshRegions = ['symmetry', 'wing']

# white background
#renderView1.Background = [1.0, 1.0, 1.0]

# update the view to ensure updated data information
renderView1.Update()

# set scalar coloring
ColorBy(paraviewfoamDisplay, ("POINTS", args.variable))

# show color bar/color legend
paraviewfoamDisplay.SetScalarBarVisibility(renderView1, True)

# get color transfer function/color map for 'p'
pLUT = GetColorTransferFunction(args.variable)

# get color legend/bar for pLUT in view renderView1
pLUTColorBar = GetScalarBar(pLUT, renderView1)

# change scalar bar placement
pLUTColorBar.Orientation = "Vertical"
pLUTColorBar.Position = [0.1, 0.9]
pLUTColorBar.ScalarBarLength = 0.8

pLUTColorBar.TitleFontSize = 8
pLUTColorBar.LabelFontSize = 8
pLUTColorBar.LabelFormat = "%g"
pLUTColorBar.RangeLabelFormat = "%.3e"
pLUTColorBar.ScalarBarThickness = 8
pLUTColorBar.TitleColor = [0, 0, 0]
pLUTColorBar.LabelColor = [0, 0, 0]

text1 = Text(registrationName=f"Flow Field: {args.variable}")
text1.Text = f"Flow Field: {args.variable}"
text1Display = Show(text1, renderView1, "TextSourceRepresentation")
renderView1.Update()
text1Display.FontSize = 35
text1Display.WindowLocation = "UpperCenter"
text1Display.Bold = 1
text1Display.FontFamily = "Arial"
text1Display.Color = [0.0, 0.0, 0.0]

# current camera placement for renderView1
renderView1.CameraPosition = [mean_chord - 10.0, 10.0, mean_span + 10.0]
renderView1.CameraFocalPoint = [mean_chord, 0.0, mean_span]
renderView1.CameraParallelScale = zoom_in_scale
renderView1.CameraViewUp = [1.0, 1.0, -1.0]

# save screenshot
SaveScreenshot(f"plots/wing_flow_field_{args.variable}_3d.png", renderView1, ImageResolution=[1923, 1158])
