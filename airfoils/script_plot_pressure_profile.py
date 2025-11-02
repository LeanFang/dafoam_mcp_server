# trace generated using paraview version 5.9.1

#### import the simple module from the paraview
from paraview.simple import *
import argparse, os

parser = argparse.ArgumentParser()
parser.add_argument("-mach_number", help="mach number", type=float, default=0.3)
parser.add_argument("-frame", help="which frame to visualize", type=int, default=-1)
args = parser.parse_args()

C0 = 347.2
U0 = args.mach_number * C0
rho0 = 1.1768
coeff = 0.5 * rho0 * U0 * U0

#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# create a new 'OpenFOAMReader'
paraviewfoam = OpenFOAMReader(registrationName="paraview.foam", FileName="./paraview.foam")

# if it is a parallel run, choose Decomposed Case
if os.path.exists("processor0"):
    paraviewfoam.CaseType = "Decomposed Case"

# get animation scene
animationScene1 = GetAnimationScene()

# update animation scene based on data timesteps
animationScene1.UpdateAnimationUsingDataTimeSteps()

# go to the specific frame
if args.frame == -1:
    animationScene1.GoToLast()
else:
    animationScene1.AnimationTime = args.frame * 0.0001

# get active view
renderView1 = GetActiveViewOrCreate("RenderView")

# show data in view
paraviewfoamDisplay = Show(paraviewfoam, renderView1, "UnstructuredGridRepresentation")

# trace defaults for the display properties.
paraviewfoamDisplay.Representation = "Surface"

# Properties modified on renderView1
renderView1.CameraParallelProjection = 1

# Properties modified on paraviewfoam
paraviewfoam.MeshRegions = ["wing"]

# create a new 'Calculator'
calculator1 = Calculator(registrationName="Calculator1", Input=paraviewfoam)

# Properties modified on calculator1
calculator1.ResultArrayName = "Cp"
calculator1.Function = "(p-101325)/%f" % coeff

# show data in view
calculator1Display = Show(calculator1, renderView1, "GeometryRepresentation")

# hide data in view
Hide(paraviewfoam, renderView1)

# create a new 'Slice'
slice1 = Slice(registrationName="Slice1", Input=calculator1)

# Properties modified on slice1.SliceType
slice1.SliceType.Normal = [0.0, 0.0, 1.0]

# create a new 'Plot On Sorted Lines'
plotOnSortedLines1 = PlotOnSortedLines(registrationName="PlotOnSortedLines1", Input=slice1)

# Create a new 'Line Chart View'
lineChartView1 = CreateView("XYChartView")

# show data in view
plotOnSortedLines1Display = Show(plotOnSortedLines1, lineChartView1, "XYChartRepresentation")

# Properties modified on plotOnSortedLines1Display
plotOnSortedLines1Display.XArrayName = "Points_X"

# Properties modified on plotOnSortedLines1Display
plotOnSortedLines1Display.SeriesVisibility = ["Cp (3)"]

# Properties modified on plotOnSortedLines1Display
plotOnSortedLines1Display.SeriesLineThickness = ["Cp (3)", "3"]

# Properties modified on plotOnSortedLines1Display
plotOnSortedLines1Display.SeriesColor = ["Cp (3)", "0", "0", "0"]

# Properties modified on lineChartView1
lineChartView1.ShowLegend = 0

# Properties modified on lineChartView1
lineChartView1.LeftAxisTitle = "Cp"

# Properties modified on lineChartView1
lineChartView1.BottomAxisTitle = "x/c"

# Properties modified on lineChartView1
lineChartView1.LeftAxisTitleFontSize = 15

# Properties modified on lineChartView1
lineChartView1.LeftAxisLabelFontSize = 15

# Properties modified on lineChartView1
lineChartView1.BottomAxisTitleFontSize = 15

# Properties modified on lineChartView1
lineChartView1.BottomAxisLabelFontSize = 15

# Properties modified on lineChartView1
lineChartView1.BottomAxisUseCustomLabels = 1

# Properties modified on lineChartView1
lineChartView1.BottomAxisLabels = ["0", "", "0.2", "", "0.4", "", "0.6", "", "0.8", "", "1.0", ""]

# Properties modified on lineChartView1
lineChartView1.BottomAxisUseCustomRange = 1

# Properties modified on lineChartView1
lineChartView1.BottomAxisRangeMaximum = 1.05
lineChartView1.BottomAxisRangeMinimum = -0.05

# Properties modified on lineChartView1
lineChartView1.LeftAxisUseCustomRange = 1

# Properties modified on lineChartView1
lineChartView1.LeftAxisRangeMinimum = 2.0

# Properties modified on lineChartView1
lineChartView1.LeftAxisRangeMaximum = -2.0

# save screenshot
SaveScreenshot("plots/airfoil_pressure_profile.png", lineChartView1, ImageResolution=[800, 600])

# save data
# SaveData('/slide_data.csv', proxy=plotOnSortedLines1, PointDataArrays=['U', 'nut', 'p'],
#    FieldDataArrays=['CasePath'],
#    Precision=8)
