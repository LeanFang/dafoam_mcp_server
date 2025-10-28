# trace generated using paraview version 5.9.1

#### import the simple module from the paraview
from paraview.simple import *
import argparse, os

#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

parser = argparse.ArgumentParser()
parser.add_argument("-x_location", help="the camera x_location in the x direction", type=float, default=0.5)
parser.add_argument("-y_location", help="the camera y_location in the y direction", type=float, default=0.0)
parser.add_argument("-zoom_in_scale", help="zoom in level", type=float, default=0.5)
parser.add_argument("-variable", help="flow field variable to plot", type=str, default="p")
args = parser.parse_args()

# create a new 'OpenFOAMReader'
paraviewfoam = OpenFOAMReader(registrationName="paraview.foam", FileName="./paraview.foam")

# if it is a parallel run, choose Decomposed Case
if os.path.exists("processor0"):
    paraviewfoam.CaseType = "Decomposed Case"

# get animation scene
animationScene1 = GetAnimationScene()

# update animation scene based on data timesteps
animationScene1.UpdateAnimationUsingDataTimeSteps()

# get active view
renderView1 = GetActiveViewOrCreate("RenderView")

# show data in view
paraviewfoamDisplay = Show(paraviewfoam, renderView1, "UnstructuredGridRepresentation")

# trace defaults for the display properties.
paraviewfoamDisplay.Representation = "Surface"

# Properties modified on renderView1
renderView1.CameraParallelProjection = 1

# current camera placement for renderView1
renderView1.CameraPosition = [args.x_location, args.y_location, 10.0]
renderView1.CameraFocalPoint = [args.x_location, args.y_location, 0.0]
renderView1.CameraParallelScale = args.zoom_in_scale

# white background
renderView1.Background = [1.0, 1.0, 1.0]

# set scalar coloring
ColorBy(paraviewfoamDisplay, ('POINTS', args.variable))

# show color bar/color legend
paraviewfoamDisplay.SetScalarBarVisibility(renderView1, True)

# get color transfer function/color map for 'p'
pLUT = GetColorTransferFunction(args.variable)

# get color legend/bar for pLUT in view renderView1
pLUTColorBar = GetScalarBar(pLUT, renderView1)

# change scalar bar placement
pLUTColorBar.Orientation = 'Horizontal'
pLUTColorBar.Position = [0.0, 0.5]
pLUTColorBar.ScalarBarLength = 0.8

pLUTColorBar.TitleFontSize = 10
pLUTColorBar.LabelFontSize = 10
pLUTColorBar.LabelFormat = '%g'
pLUTColorBar.RangeLabelFormat = '%.3e'
pLUTColorBar.ScalarBarThickness = 8

# save screenshot
SaveScreenshot("./image_airfoil_flow_field.png", renderView1, ImageResolution=[1200, 1000])
