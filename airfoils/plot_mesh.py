# trace generated using paraview version 5.9.1

#### import the simple module from the paraview
from paraview.simple import *
import argparse

#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

parser = argparse.ArgumentParser()
parser.add_argument("-x_location", help="the camera x_location in the x direction", type=float, default=0.5)
parser.add_argument("-y_location", help="the camera y_location in the y direction", type=float, default=0.0)
parser.add_argument("-zoom_in_scale", help="zoom in level", type=float, default=0.5)
args = parser.parse_args()

# create a new 'OpenFOAMReader'
paraviewfoam = OpenFOAMReader(registrationName="paraview.foam", FileName="./paraview.foam")

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

# change representation type
paraviewfoamDisplay.SetRepresentationType("Surface With Edges")

fFDdat = TecplotReader(registrationName="FFD.dat", FileNames=["./FFD.dat"])

# show data in view
fFDdatDisplay = Show(fFDdat, renderView1, "StructuredGridRepresentation")

# change representation type
fFDdatDisplay.SetRepresentationType("Points")

# Properties modified on fFDdatDisplay
fFDdatDisplay.PointSize = 5.0

# change solid color
fFDdatDisplay.AmbientColor = [0.6666666666666666, 0.0, 0.0]
fFDdatDisplay.DiffuseColor = [0.6666666666666666, 0.0, 0.0]

# save screenshot
SaveScreenshot("./airfoil_mesh.jpeg", renderView1, ImageResolution=[600, 360])
