#!/bin/bash

python script_generate_geometry.py
surfaceGenerateBoundingBox wing.stl constant/triSurface/domain.stl 20 20 20 20 0 20
cartesianMesh
renumberMesh -overwrite

# copy initial and boundary condition files
cp -r 0_orig 0