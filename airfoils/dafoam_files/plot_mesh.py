# trace generated using paraview version 5.9.1

#### import the simple module from the paraview
from paraview.simple import *
import argparse

#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

parser = argparse.ArgumentParser()
parser.add_argument("-working_dir", help="absolute path for the working directory", type=str, default="./")
args = parser.parse_args()

working_dir = args.working_dir

# create a new 'OpenFOAMReader'
paraviewfoam = OpenFOAMReader(registrationName="paraview.foam", FileName=working_dir + "/paraview.foam")

# get active view
renderView1 = GetActiveViewOrCreate("RenderView")

# show data in view
paraviewfoamDisplay = Show(paraviewfoam, renderView1, "UnstructuredGridRepresentation")

# trace defaults for the display properties.
paraviewfoamDisplay.Representation = "Surface"

# reset view to fit data
renderView1.ResetCamera()

# get the material library
materialLibrary1 = GetMaterialLibrary()

# update the view to ensure updated data information
renderView1.Update()

# Properties modified on renderView1
renderView1.CameraParallelProjection = 1

# reset view to fit data
renderView1.ResetCamera()

# change representation type
paraviewfoamDisplay.SetRepresentationType("Surface With Edges")

# get layout
layout1 = GetLayout()

# layout/tab size in pixels
layout1.SetSize(1925, 1158)

# current camera placement for renderView1
renderView1.CameraPosition = [0.5123891830444336, -0.0026445388793945312, 1.5313394223807257]
renderView1.CameraFocalPoint = [0.5123891830444336, -0.0026445388793945312, 0.004999999888241291]
renderView1.CameraParallelScale = 0.3950457118318379
renderView1.CameraParallelProjection = 1

# save screenshot
SaveScreenshot(working_dir + "/airfoil_mesh.jpeg", renderView1, ImageResolution=[600, 360])

# ================================================================
# addendum: following script captures some of the application
# state to faithfully reproduce the visualization during playback
# ================================================================

# --------------------------------
# saving layout sizes for layouts
# --------------------------------------------
# uncomment the following to render all views
# RenderAllViews()
# alternatively, if you want to write images, you can use SaveScreenshot(...).
