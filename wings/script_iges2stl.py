# trace generated using paraview version 5.13.3
# import paraview
# paraview.compatibility.major = 5
# paraview.compatibility.minor = 13

#### import the simple module from the paraview
from paraview.simple import *

#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# create a new 'IGES Reader'
wingiges = IGESReader(registrationName="wing_mm.iges", FileNames=["wing_mm.iges"])
wingiges.LinearDeflection = 0.05
wingiges.AngularDeflection = 0.2
wingiges.RelativeDeflection = 0
wingiges.ReadWire = 0

# Apply scaling transform
transform1 = Transform(registrationName="Transform1", Input=wingiges)
transform1.Transform = "Transform"

# scale the iges from mm to m
scale_factor = 0.001
transform1.Transform.Scale = [scale_factor, scale_factor, scale_factor]

# save data
SaveData(
    "./wing.stl",
    proxy=transform1,
    ChooseArraysToWrite=0,
    PointDataArrays=["Normal", "UV"],
    CellDataArrays=["Colors"],
    FieldDataArrays=[],
    VertexDataArrays=[],
    EdgeDataArrays=[],
    RowDataArrays=[],
    WriteTimeSteps=0,
    Filenamesuffix="_%d",
    NumberOfIORanks=1,
    RankAssignmentMode="Contiguous",
    FileType="Ascii",
)
